"""Command-line interface (`sloptoon`) for the WOW Forever Sloptoon pipeline.

Clean site-only archive pipeline supporting 6 commands:
- `scout`: rank unproduced wowforever recommend posts
- `generate`: script -> quality audit -> cut art -> compose -> record sync -> build-site
- `compose`: re-compose an existing episode from `script.json` + `raw_cuts`
- `build-site`: build the pure-white static web archive into `site/`
- `watermark` (alias `watermark-all`): idempotently stamp the bottom archive CTA banner
- `autopilot`: end-to-end scout -> generate -> build-site -> optional deploy
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from wow_sloptoon.artist import generate_episode_cuts, resolve_image_model
from wow_sloptoon.cast import canonical_cast_name
from wow_sloptoon.config import (
    DEFAULT_TEXT_MODEL,
    SUPPORTED_IMAGE_MODELS,
    Settings,
    load_settings,
)
from wow_sloptoon.models import EpisodeRecord, EpisodeScript, GalleryPost
from wow_sloptoon.scout import GalleryAccessBlockedError, GalleryScout, build_post_url
from wow_sloptoon.writer import (
    audit_script_quality,
    build_dry_run_script,
    generate_episode_script,
    script_to_pretty_json,
)


def _configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def load_episode_records(episodes_json: Path) -> list[EpisodeRecord]:
    """Load `EpisodeRecord` entries from `data/episodes.json` (array or `{"episodes": [...]}`)."""
    if not episodes_json.exists():
        return []
    raw = json.loads(episodes_json.read_text(encoding="utf-8"))
    items = raw.get("episodes", []) if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        return []
    return [EpisodeRecord.model_validate(item) for item in items]


def save_episode_records(episodes_json: Path, records: list[EpisodeRecord]) -> None:
    """Persist `EpisodeRecord` entries as a top-level UTF-8 JSON array."""
    episodes_json.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(records, key=lambda r: r.episode_number)
    payload = [record.model_dump(mode="json") for record in ordered]
    episodes_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _normalize_episode_id(raw_id: str) -> str:
    key = raw_id.strip().lower()
    if key.isdigit():
        return f"ep{int(key):03d}"
    return key


def _next_episode_number(records: Sequence[EpisodeRecord]) -> int:
    if not records:
        return 1
    return max(r.episode_number for r in records) + 1


def _to_project_rel(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _resolve_episode_asset(rel_path: str, settings: Settings) -> Path:
    raw = Path(rel_path)
    if raw.is_absolute() and raw.exists():
        return raw
    for base in (settings.project_root, settings.data_dir, settings.site_dir):
        candidate = base / raw
        if candidate.exists():
            return candidate
    return settings.project_root / raw


def _find_episode_record(records: Sequence[EpisodeRecord], episode_id: str) -> EpisodeRecord | None:
    key = _normalize_episode_id(episode_id)
    for record in records:
        if record.episode_id.strip().lower() == key:
            return record
    return None


def _collect_cast_used(script: EpisodeScript) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for cut in script.cuts:
        for name in cut.characters:
            canon = canonical_cast_name(name)
            if canon not in seen:
                seen.add(canon)
                ordered.append(canon)
    return ordered


def _run_build_site(settings: Settings) -> Path:
    from wow_sloptoon import site_builder

    return site_builder.build_static_site(
        settings.episodes_json,
        settings.site_dir,
        settings.assets_dir,
        archive_base_url=settings.archive_base_url,
    )


def _persist_episode_metadata(
    script: EpisodeScript,
    composed: object,
    *,
    ep_id: str,
    ep_dir: Path,
    settings: Settings,
    preserve_created_at: str | None = None,
) -> EpisodeRecord:
    """Write `script.json`, `record.json`, and `data/episodes.json` with 100% identical metadata."""
    ep_dir.mkdir(parents=True, exist_ok=True)
    (ep_dir / "script.json").write_text(script_to_pretty_json(script) + "\n", encoding="utf-8")

    created_at = (
        preserve_created_at
        or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    )
    thumb_path = getattr(composed, "thumb_path")
    full_path = getattr(composed, "full_image_path")
    page_paths = getattr(composed, "page_paths")

    record = EpisodeRecord(
        episode_id=ep_id,
        episode_number=script.episode_number,
        title=script.source_title,
        subtitle=script.subtitle,
        source_post_no=script.source_post_no,
        source_url=script.source_url,
        created_at=created_at,
        cut_count=len(script.cuts),
        cast_used=_collect_cast_used(script),
        full_image_rel=_to_project_rel(full_path, settings.project_root),
        thumb_image_rel=_to_project_rel(thumb_path, settings.project_root),
        page_images_rel=[
            _to_project_rel(p, settings.project_root) for p in page_paths
        ],
    )

    # Save identical record payload to both `ep_dir/record.json` and `data/episodes.json`
    (ep_dir / "record.json").write_text(
        json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    records = load_episode_records(settings.episodes_json)
    updated = [r for r in records if r.episode_id != record.episode_id]
    updated.append(record)
    save_episode_records(settings.episodes_json, updated)
    return record


def _check_script_quality_gate(script: EpisodeScript) -> dict[str, object]:
    """Run `audit_script_quality` and surface warnings/errors before image generation."""
    audit = audit_script_quality(script)
    for warn in audit.get("warnings", []):
        print(f"  [SCRIPT WARN] {warn}", file=sys.stderr)
    if not audit.get("passed", False):
        print("[SCRIPT GATE FAILED] Quality audit errors:", file=sys.stderr)
        for err in audit.get("errors", []):
            print(f"  - {err}", file=sys.stderr)
    return audit


def _discover_raw_cut_paths(script: EpisodeScript, raw_dir: Path) -> dict[int, Path]:
    """Locate raw cut image files inside `raw_dir` for all cuts in `script`."""
    found: dict[int, Path] = {}
    exts = (".png", ".jpg", ".jpeg", ".webp")
    ordered_cuts = sorted(script.cuts, key=lambda c: c.cut_index)
    for pos, cut in enumerate(ordered_cuts, start=1):
        matched: Path | None = None
        for idx_val in dict.fromkeys((cut.cut_index, pos)):
            stems = (f"cut_{idx_val:02d}", f"cut_{idx_val}", f"raw_cut_{idx_val:02d}", f"raw_cut_{idx_val}")
            for stem in stems:
                for ext in exts:
                    cand = raw_dir / f"{stem}{ext}"
                    if cand.exists() and cand.is_file():
                        matched = cand
                        break
                if matched is not None:
                    break
            if matched is not None:
                break
        if matched is None:
            raise FileNotFoundError(
                f"Missing raw cut image for cut {cut.cut_index} in {raw_dir} "
                f"(expected cut_{cut.cut_index:02d}.png/.jpg)"
            )
        found[cut.cut_index] = matched
    return found


def _render_and_compose_script(
    script: EpisodeScript,
    *,
    settings: Settings,
    image_model: str | None = None,
    max_workers: int = 3,
    skip_site: bool = False,
) -> EpisodeRecord:
    from wow_sloptoon import composer

    ep_id = f"ep{script.episode_number:03d}"
    ep_dir = settings.episodes_dir / ep_id
    raw_cuts_dir = settings.data_dir / "raw_cuts" / ep_id
    resolved_image_model = resolve_image_model(image_model, settings)

    print(
        f"[2/4] Generating {len(script.cuts)} 2~2.5-head SD cuts "
        f"(model={resolved_image_model}, workers={max_workers})..."
    )
    raw_cut_paths = generate_episode_cuts(
        script,
        raw_cuts_dir,
        settings=settings,
        model=resolved_image_model,
        max_workers=max(1, int(max_workers)),
    )

    print(f"[3/4] Composing speech bubbles, tooltips & watermark CTA into {ep_dir}...")
    composed = composer.compose_episode(
        script,
        raw_cut_paths,
        ep_dir,
        watermark_url=settings.archive_base_url,
    )

    audit = composed.audit_report
    ratios = [c.get("art_height_ratio", 0.0) for c in audit.get("cuts", [])]
    min_ratio = min(ratios) if ratios else 0.0
    print(
        f"  Compose audit: passed={audit['passed']}, overlap_px={audit['total_overlap_px']}, "
        f"tooltip_overlap_px={audit.get('total_tooltip_overlap_px', 0)}, "
        f"min_art_height_ratio={min_ratio:.2%}"
    )

    existing = _find_episode_record(load_episode_records(settings.episodes_json), ep_id)
    record = _persist_episode_metadata(
        script,
        composed,
        ep_id=ep_id,
        ep_dir=ep_dir,
        settings=settings,
        preserve_created_at=existing.created_at if existing else None,
    )

    if not skip_site:
        print("[4/4] Rebuilding static web archive...")
        built = _run_build_site(settings)
        print(f"Archive rebuilt at: {built}")
    else:
        print("[4/4] Skipped static site rebuild (--skip-site).")

    print(f"Done! Created {record.episode_id}: {record.title}")
    print(f"  Full image : {record.full_image_rel}")
    print(f"  Thumbnail  : {record.thumb_image_rel}")
    print(f"  Pages      : {len(record.page_images_rel)} ({record.cut_count} cuts)")
    return record


def _generate_for_post(
    post: GalleryPost,
    *,
    settings: Settings,
    episode_number: int | None = None,
    dry_run: bool = False,
    text_model: str | None = None,
    image_model: str | None = None,
    max_workers: int = 3,
    skip_site: bool = False,
) -> EpisodeRecord | EpisodeScript:
    records = load_episode_records(settings.episodes_json)
    ep_num = episode_number or _next_episode_number(records)
    ep_id = f"ep{ep_num:03d}"

    if dry_run:
        script = build_dry_run_script(post, episode_number=ep_num)
        audit = _check_script_quality_gate(script)
        print(
            f"[DRY-RUN] Preview script for {ep_id} (source #{post.post_no}, "
            f"{len(script.cuts)} cuts, audit_passed={audit.get('passed')}):"
        )
        print(script_to_pretty_json(script))
        return script

    resolved_text_model = text_model or settings.text_model or DEFAULT_TEXT_MODEL
    print(
        f"[1/4] Writing script for {ep_id} from #{post.post_no} "
        f"(model={resolved_text_model})..."
    )
    script = generate_episode_script(
        post,
        episode_number=ep_num,
        settings=settings,
        model=resolved_text_model,
    )
    audit = _check_script_quality_gate(script)
    if not audit.get("passed", False):
        raise RuntimeError(
            f"Script quality gate failed for {ep_id} (#{post.post_no}): "
            + "; ".join(str(e) for e in audit.get("errors", []))
        )

    return _render_and_compose_script(
        script,
        settings=settings,
        image_model=image_model,
        max_workers=max_workers,
        skip_site=skip_site,
    )


def _has_real_gemini_api_key(settings: Settings) -> bool:
    key = (settings.gemini_api_key or "").strip()
    if not key:
        return False
    return key.lower() not in {"your-gemini-api-key-here", "changeme", "placeholder"}


def _run_deploy_pages_script(settings: Settings) -> int:
    deploy_script = settings.project_root / "deploy-pages.ps1"
    if not deploy_script.exists():
        print(f"[WARN] deploy-pages.ps1 not found at {deploy_script}; skipping deploy.", file=sys.stderr)
        return 1

    ps_exe = shutil.which("pwsh") or shutil.which("powershell")
    if not ps_exe:
        print("[ERROR] PowerShell executable (pwsh/powershell) not found for --deploy.", file=sys.stderr)
        return 1

    print(f"[autopilot] Deploying static archive via {deploy_script} -SkipBuild ...")
    proc = subprocess.run(
        [ps_exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(deploy_script), "-SkipBuild"],
        cwd=str(settings.project_root),
        check=False,
    )
    return int(proc.returncode)


def cmd_scout(args: argparse.Namespace, settings: Settings) -> int:
    existing = {r.source_post_no for r in load_episode_records(settings.episodes_json)}
    scout = GalleryScout(gallery_id=settings.gallery_id)
    candidates = scout.scout_candidates(
        existing_post_nos=existing,
        pages=args.pages,
        limit=args.limit,
        fetch_bodies_for_top=0 if args.no_body else min(5, args.limit),
    )

    if args.json:
        payload = [
            {"score": score, "post": post.model_dump(mode="json")}
            for post, score in candidates
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if not candidates:
        print("No unproduced recommend posts found.")
        return 0

    print(f"Top {len(candidates)} unproduced recommend candidates ({settings.gallery_id}):")
    for rank, (post, score) in enumerate(candidates, start=1):
        print(
            f"  {rank:2d}. [score={score:6.2f}] #{post.post_no} "
            f"(추천 {post.recommends} / 댓글 {post.comments_count}) {post.title}"
        )
        print(f"      {post.url}")
    return 0


def cmd_generate(args: argparse.Namespace, settings: Settings) -> int:
    if args.from_script:
        script_path = Path(args.from_script).expanduser().resolve()
        if not script_path.exists():
            print(f"[ERROR] Script JSON not found: {script_path}", file=sys.stderr)
            return 1
        script = EpisodeScript.model_validate_json(script_path.read_text(encoding="utf-8"))
        if args.episode_number is not None:
            script = script.model_copy(update={"episode_number": args.episode_number})
        audit = _check_script_quality_gate(script)
        if args.dry_run:
            print(
                f"[DRY-RUN] Loaded script from {script_path} "
                f"(ep{script.episode_number:03d}, {len(script.cuts)} cuts, audit_passed={audit.get('passed')}):"
            )
            print(script_to_pretty_json(script))
            return 0 if audit.get("passed", False) else 1
        if not audit.get("passed", False):
            return 1
        _render_and_compose_script(
            script,
            settings=settings,
            image_model=args.image_model,
            max_workers=args.max_workers,
            skip_site=args.skip_site,
        )
        return 0

    scout = GalleryScout(gallery_id=settings.gallery_id)
    if args.post_no:
        post_no = str(args.post_no).strip()
        try:
            post = scout.fetch_post_detail(post_no)
        except Exception as exc:
            if args.dry_run:
                print(
                    f"[WARN] Could not fetch #{post_no} live ({exc}); "
                    "using offline placeholder post for --dry-run.",
                    file=sys.stderr,
                )
                post = GalleryPost(
                    post_no=post_no,
                    title=f"포에버갤 개념글 #{post_no}",
                    url=build_post_url(post_no, gallery_id=settings.gallery_id),
                    author="포에버갤러",
                    date_str=datetime.now().strftime("%Y-%m-%d"),
                    body="던전 파티 상황극 드라이런 프리뷰 테스트입니다.",
                )
            else:
                raise
    else:
        existing = {r.source_post_no for r in load_episode_records(settings.episodes_json)}
        candidates = scout.scout_candidates(
            existing_post_nos=existing,
            pages=args.pages,
            limit=5,
            fetch_bodies_for_top=5,
        )
        if not candidates:
            print("No unproduced recommend candidates available to generate.")
            return 1
        post, score = candidates[0]
        if not post.body:
            post = scout.fetch_post_detail(post.post_no, base_post=post)
        print(f"Selected top candidate #{post.post_no} (score={score:.2f}): {post.title}")

    _generate_for_post(
        post,
        settings=settings,
        episode_number=args.episode_number,
        dry_run=args.dry_run,
        text_model=args.text_model,
        image_model=args.image_model,
        max_workers=args.max_workers,
        skip_site=args.skip_site,
    )
    return 0


def cmd_compose(args: argparse.Namespace, settings: Settings) -> int:
    from wow_sloptoon import composer

    ep_id = _normalize_episode_id(args.episode_id)
    ep_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else (settings.episodes_dir / ep_id)
    )
    script_path = (
        Path(args.script).expanduser().resolve()
        if args.script
        else (ep_dir / "script.json")
    )
    raw_dir = (
        Path(args.raw_dir).expanduser().resolve()
        if args.raw_dir
        else (settings.data_dir / "raw_cuts" / ep_id)
    )

    if not script_path.exists():
        print(f"[ERROR] script.json not found for {ep_id}: {script_path}", file=sys.stderr)
        return 1
    if not raw_dir.exists():
        print(f"[ERROR] raw_cuts directory not found for {ep_id}: {raw_dir}", file=sys.stderr)
        return 1

    script = EpisodeScript.model_validate_json(script_path.read_text(encoding="utf-8"))
    raw_cut_paths = _discover_raw_cut_paths(script, raw_dir)

    wm_url = None if args.no_watermark else settings.archive_base_url
    composed = composer.compose_episode(
        script,
        raw_cut_paths,
        ep_dir,
        watermark_url=wm_url,
    )

    existing = _find_episode_record(load_episode_records(settings.episodes_json), ep_id)
    record = _persist_episode_metadata(
        script,
        composed,
        ep_id=ep_id,
        ep_dir=ep_dir,
        settings=settings,
        preserve_created_at=existing.created_at if existing else None,
    )

    audit = composed.audit_report
    ratios = [c.get("art_height_ratio", 0.0) for c in audit.get("cuts", [])]
    min_ratio = min(ratios) if ratios else 0.0
    print(
        f"[OK] Composed {record.episode_id} ({record.cut_count} cuts, {len(record.page_images_rel)} pages): "
        f"passed={audit['passed']}, overlap_px={audit['total_overlap_px']}, "
        f"tooltip_overlap_px={audit.get('total_tooltip_overlap_px', 0)}, "
        f"min_art_height_ratio={min_ratio:.2%}"
    )

    if not args.skip_site:
        built = _run_build_site(settings)
        print(f"Archive rebuilt at: {built}")

    return 0 if audit["passed"] else 1


def cmd_build_site(args: argparse.Namespace, settings: Settings) -> int:
    built = _run_build_site(settings)
    print(f"Built static web archive: {built}")
    return 0


def cmd_watermark(args: argparse.Namespace, settings: Settings) -> int:
    from wow_sloptoon import composer

    records = load_episode_records(settings.episodes_json)
    if not records:
        print(f"No episodes found in {settings.episodes_json}.")
        return 0

    if args.episode_id:
        target = _find_episode_record(records, args.episode_id)
        if target is None:
            print(f"[ERROR] Episode '{args.episode_id}' not found in {settings.episodes_json}.", file=sys.stderr)
            return 1
        targets = [target]
    else:
        targets = records

    site_url = (args.site_url or settings.archive_base_url or composer.DEFAULT_WATERMARK_URL).strip()
    watermarked_count = 0

    for record in targets:
        full_img = _resolve_episode_asset(record.full_image_rel, settings)
        if not full_img.exists():
            print(f"[SKIP] {record.episode_id}: missing {full_img}", file=sys.stderr)
            continue

        stamped = composer.retrofit_episode_watermark(
            full_img.parent,
            site_url=site_url,
            filename=full_img.name,
        )
        watermarked_count += 1
        print(f"[OK] Watermarked {record.episode_id}: {stamped}")

    print(
        f"Done! Watermarked {watermarked_count}/{len(targets)} episode(s) "
        f"(banner URL: {site_url})."
    )
    return 0


def cmd_autopilot(args: argparse.Namespace, settings: Settings) -> int:
    existing_records = load_episode_records(settings.episodes_json)
    existing_post_nos = {r.source_post_no for r in existing_records}

    print(f"[autopilot 1/4] Scouting unproduced recommend posts from '{settings.gallery_id}'...")
    scout = GalleryScout(gallery_id=settings.gallery_id)
    candidates = scout.scout_candidates(
        existing_post_nos=existing_post_nos,
        pages=args.pages,
        limit=5,
        fetch_bodies_for_top=5,
    )

    if args.dry_run:
        if candidates:
            post, score = candidates[0]
            if not post.body:
                post = scout.fetch_post_detail(post.post_no, base_post=post)
            print(f"[autopilot DRY-RUN] Top candidate #{post.post_no} (score={score:.2f}): {post.title}")
            _generate_for_post(
                post,
                settings=settings,
                dry_run=True,
                text_model=args.text_model,
                image_model=args.image_model,
                max_workers=args.max_workers,
                skip_site=True,
            )
        else:
            print("[autopilot DRY-RUN] No new unproduced recommend candidates found.")
        print(
            "[autopilot DRY-RUN] Would run: generate (if GEMINI_API_KEY set) -> build-site"
            + (" -> deploy-pages.ps1" if args.deploy else "")
            + "."
        )
        return 0

    if candidates and _has_real_gemini_api_key(settings):
        post, score = candidates[0]
        if not post.body:
            post = scout.fetch_post_detail(post.post_no, base_post=post)
        print(f"[autopilot 2/4] Generating episode from #{post.post_no} (score={score:.2f}): {post.title}")
        _generate_for_post(
            post,
            settings=settings,
            dry_run=False,
            text_model=args.text_model,
            image_model=args.image_model,
            max_workers=args.max_workers,
            skip_site=True,
        )
    elif not candidates:
        print("[autopilot 2/4] No new unproduced recommend posts found; refreshing static archive.")
    else:
        print("[autopilot 2/4] GEMINI_API_KEY not set; skipping episode generation.")

    print("[autopilot 3/4] Building static web archive (site/)...")
    built = _run_build_site(settings)
    print(f"  Archive built: {built}")

    if args.deploy:
        rc = _run_deploy_pages_script(settings)
        if rc != 0:
            print(f"[autopilot ERROR] deploy-pages.ps1 exited with code {rc}", file=sys.stderr)
            return rc
    else:
        print("[autopilot 4/4] Local run complete (pass --deploy to push to slopwow.github.io).")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sloptoon",
        description="WOW Forever Sloptoon — Automated 2~2.5-head SD 4~7 cut gag webtoon pipeline for slopwow.github.io.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Override wow-forever-sloptoon project root directory.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # scout
    p_scout = subparsers.add_parser(
        "scout",
        help="Fetch and rank unproduced recommend posts from DCInside wowforever gallery.",
    )
    p_scout.add_argument("--pages", type=int, default=1, help="Number of recommend list pages to scan.")
    p_scout.add_argument("--limit", type=int, default=10, help="Maximum ranked candidates to display.")
    p_scout.add_argument("--no-body", action="store_true", help="Rank from list metadata only without fetching post bodies.")
    p_scout.add_argument("--json", action="store_true", help="Output candidates as JSON.")
    p_scout.set_defaults(func=cmd_scout)

    # generate
    p_gen = subparsers.add_parser(
        "generate",
        help="Generate a 4~7 cut SD sloptoon episode from a post, top scout candidate, or existing script.json.",
    )
    target_group = p_gen.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--post-no", type=str, help="Specific DCInside wowforever post number.")
    target_group.add_argument("--auto", action="store_true", help="Automatically select the top unproduced recommend post.")
    target_group.add_argument("--from-script", type=Path, help="Render and compose from an existing script.json file.")
    p_gen.add_argument("--dry-run", action="store_true", help="Build/validate preview script without calling Gemini API or modifying data/episodes.json.")
    p_gen.add_argument("--text-model", type=str, default=None, help=f"Override Gemini text model (default: {DEFAULT_TEXT_MODEL}).")
    p_gen.add_argument(
        "--model",
        "--image-model",
        dest="image_model",
        type=str,
        default=None,
        choices=list(SUPPORTED_IMAGE_MODELS),
        help="Select Gemini image model.",
    )
    p_gen.add_argument("--max-workers", type=int, default=3, help="Concurrent image-generation workers (default: 3).")
    p_gen.add_argument("--episode-number", type=int, default=None, help="Override sequential episode number.")
    p_gen.add_argument("--pages", type=int, default=1, help="Pages to scan when using --auto.")
    p_gen.add_argument("--skip-site", action="store_true", help="Skip rebuilding static site after generation.")
    p_gen.set_defaults(func=cmd_generate)

    # compose
    p_comp = subparsers.add_parser(
        "compose",
        help="Re-compose an existing episode from script.json + raw_cuts without regenerating images.",
    )
    p_comp.add_argument("episode_id", type=str, help="Episode ID (e.g. ep001 or 1).")
    p_comp.add_argument("--script", type=Path, default=None, help="Optional path to script.json.")
    p_comp.add_argument("--raw-dir", type=Path, default=None, help="Optional path to raw_cuts directory.")
    p_comp.add_argument("--output-dir", type=Path, default=None, help="Optional output episode directory.")
    p_comp.add_argument("--no-watermark", action="store_true", help="Skip bottom archive CTA watermark banner.")
    p_comp.add_argument("--skip-site", action="store_true", help="Skip rebuilding static site after compose.")
    p_comp.set_defaults(func=cmd_compose)

    # build-site
    p_site = subparsers.add_parser(
        "build-site",
        help="Build the static #FFFFFF webtoon archive into site/.",
    )
    p_site.set_defaults(func=cmd_build_site)

    # watermark (alias: watermark-all)
    p_wm = subparsers.add_parser(
        "watermark",
        aliases=["watermark-all"],
        help="Idempotently apply the Sloptoon bottom watermark CTA banner to episodes in data/episodes.json.",
    )
    p_wm.add_argument(
        "--site-url",
        type=str,
        default="slopwow.github.io",
        help="Archive domain shown in the bottom watermark banner (default: slopwow.github.io).",
    )
    p_wm.add_argument(
        "--episode-id",
        type=str,
        default=None,
        help="Optional single episode ID to watermark (default: all episodes).",
    )
    p_wm.set_defaults(func=cmd_watermark)

    # autopilot
    p_auto = subparsers.add_parser(
        "autopilot",
        help="End-to-end static archive pipeline: scout -> generate -> build-site -> optional deploy.",
    )
    p_auto.add_argument("--deploy", action="store_true", help="Run deploy-pages.ps1 to publish site/ to slopwow.github.io.")
    p_auto.add_argument("--dry-run", action="store_true", help="Preview scout + dry-run script without API calls or deploy.")
    p_auto.add_argument("--text-model", type=str, default=None, help=f"Override Gemini text model (default: {DEFAULT_TEXT_MODEL}).")
    p_auto.add_argument(
        "--model",
        "--image-model",
        dest="image_model",
        type=str,
        default=None,
        choices=list(SUPPORTED_IMAGE_MODELS),
        help="Select Gemini image model.",
    )
    p_auto.add_argument("--max-workers", type=int, default=3, help="Concurrent image-generation workers (default: 3).")
    p_auto.add_argument("--pages", type=int, default=1, help="Recommend list pages to scan.")
    p_auto.set_defaults(func=cmd_autopilot)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    _configure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = load_settings(project_root=args.project_root)

    try:
        return int(args.func(args, settings))
    except GalleryAccessBlockedError as exc:
        print(f"[BLOCKED] {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
