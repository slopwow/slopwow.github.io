"""Command-line interface (`sloptoon`) for the WOW Forever Sloptoon pipeline."""

from __future__ import annotations

import argparse
import functools
import http.server
import json
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
    key = episode_id.strip().lower()
    if key.isdigit():
        key = f"ep{int(key):03d}"
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


def _generate_for_post(
    post: GalleryPost,
    *,
    settings: Settings,
    episode_number: int | None = None,
    dry_run: bool = False,
    text_model: str | None = None,
    image_model: str | None = None,
    skip_site: bool = False,
) -> EpisodeRecord | EpisodeScript:
    records = load_episode_records(settings.episodes_json)
    ep_num = episode_number or _next_episode_number(records)
    ep_id = f"ep{ep_num:03d}"

    if dry_run:
        script = build_dry_run_script(post, episode_number=ep_num)
        print(f"[DRY-RUN] Generated preview script for {ep_id} (source #{post.post_no}):")
        print(script_to_pretty_json(script))
        return script

    resolved_image_model = resolve_image_model(image_model, settings)
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

    raw_cuts_dir = settings.data_dir / "raw_cuts" / ep_id
    print(
        f"[2/4] Generating {len(script.cuts)} pure-#FFFFFF Draft C cuts "
        f"(model={resolved_image_model})..."
    )
    raw_cut_paths = generate_episode_cuts(
        script,
        raw_cuts_dir,
        settings=settings,
        model=resolved_image_model,
    )

    from wow_sloptoon import composer

    ep_dir = settings.episodes_dir / ep_id
    print(f"[3/4] Composing speech bubbles & layout into {ep_dir}...")
    composed = composer.compose_episode(script, raw_cut_paths, ep_dir)

    # Save script alongside composed assets for reproducibility
    (ep_dir / "script.json").write_text(script_to_pretty_json(script), encoding="utf-8")

    now_iso = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    record = EpisodeRecord(
        episode_id=ep_id,
        episode_number=ep_num,
        title=script.source_title,
        subtitle=script.subtitle,
        source_post_no=script.source_post_no,
        source_url=script.source_url,
        created_at=now_iso,
        cut_count=len(script.cuts),
        cast_used=_collect_cast_used(script),
        full_image_rel=_to_project_rel(composed.full_image_path, settings.project_root),
        thumb_image_rel=_to_project_rel(composed.thumb_image_path if hasattr(composed, "thumb_image_path") else composed.thumb_path, settings.project_root),
        page_images_rel=[
            _to_project_rel(p, settings.project_root) for p in composed.page_paths
        ],
    )

    updated = [r for r in records if r.episode_id != record.episode_id]
    updated.append(record)
    save_episode_records(settings.episodes_json, updated)

    if not skip_site:
        print("[4/4] Rebuilding static web archive...")
        built = _run_build_site(settings)
        print(f"Archive rebuilt at: {built}")
    else:
        print("[4/4] Skipped static site rebuild (--skip-site).")

    print(f"Done! Created {record.episode_id}: {record.title}")
    print(f"  Full image : {record.full_image_rel}")
    print(f"  Thumbnail  : {record.thumb_image_rel}")
    return record


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
        skip_site=args.skip_site,
    )
    return 0


def cmd_build_site(args: argparse.Namespace, settings: Settings) -> int:
    built = _run_build_site(settings)
    print(f"Built static web archive: {built}")
    return 0


def cmd_pack_dc(args: argparse.Namespace, settings: Settings) -> int:
    from wow_sloptoon import dc_packager

    records = load_episode_records(settings.episodes_json)
    record = _find_episode_record(records, args.episode_id)
    if record is None:
        available = ", ".join(r.episode_id for r in records) or "(none)"
        print(
            f"Episode '{args.episode_id}' not found in {settings.episodes_json}. "
            f"Available: {available}",
            file=sys.stderr,
        )
        return 1

    full_image_path = _resolve_episode_asset(record.full_image_rel, settings)
    if not full_image_path.exists():
        print(
            f"Full episode image not found for {record.episode_id}: {full_image_path}",
            file=sys.stderr,
        )
        return 1

    out_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else (settings.upload_pack_dir / record.episode_id)
    )
    archive_url = args.archive_url if args.archive_url is not None else settings.archive_base_url

    pack = dc_packager.create_dc_upload_pack(
        record,
        full_image_path,
        out_dir,
        archive_base_url=archive_url,
    )

    print(f"DC upload pack created: {pack.pack_dir}")
    print(f"  Title     : {pack.title_text}")
    print(f"  Write URL : {pack.write_url}")
    print("  Images    :")
    for img_path in pack.image_paths:
        print(f"    - {img_path}")

    if args.copy_title:
        copied = dc_packager.copy_to_clipboard(pack.title_text)
        print(f"  Clipboard (title): {'copied' if copied else 'unavailable'}")
    elif args.copy_body:
        copied = dc_packager.copy_to_clipboard(pack.body_text)
        print(f"  Clipboard (body) : {'copied' if copied else 'unavailable'}")

    if args.open_browser:
        url = dc_packager.open_dc_write_page(settings.gallery_id)
        print(f"Opened official DCInside write page in browser: {url}")
        print("(Please log in, paste title/body, attach images, solve CAPTCHA, and submit manually.)")

    return 0


def cmd_serve(args: argparse.Namespace, settings: Settings) -> int:
    if args.rebuild or not (settings.site_dir / "index.html").exists():
        _run_build_site(settings)

    handler_cls = functools.partial(
        http.server.SimpleHTTPRequestHandler,
        directory=str(settings.site_dir),
    )
    server = http.server.ThreadingHTTPServer((args.host, args.port), handler_cls)
    print(f"Serving WOW Forever Sloptoon archive from {settings.site_dir}")
    print(f"Open: http://{args.host}:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()
    return 0


def cmd_run_once(args: argparse.Namespace, settings: Settings) -> int:
    existing = {r.source_post_no for r in load_episode_records(settings.episodes_json)}
    scout = GalleryScout(gallery_id=settings.gallery_id)
    candidates = scout.scout_candidates(
        existing_post_nos=existing,
        pages=args.pages,
        limit=5,
        fetch_bodies_for_top=5,
    )
    if not candidates:
        print("No new unproduced recommend posts found.")
        if settings.episodes_json.exists() and not args.dry_run:
            built = _run_build_site(settings)
            print(f"Rebuilt archive with existing episodes: {built}")
        return 0

    post, score = candidates[0]
    if not post.body:
        post = scout.fetch_post_detail(post.post_no, base_post=post)
    print(f"[run-once] Selected #{post.post_no} (score={score:.2f}): {post.title}")

    result = _generate_for_post(
        post,
        settings=settings,
        dry_run=args.dry_run,
        text_model=args.text_model,
        image_model=args.image_model,
        skip_site=False,
    )

    if isinstance(result, EpisodeRecord) and args.pack_dc:
        from wow_sloptoon import dc_packager

        full_img = _resolve_episode_asset(result.full_image_rel, settings)
        pack_dir = settings.upload_pack_dir / result.episode_id
        pack = dc_packager.create_dc_upload_pack(
            result,
            full_img,
            pack_dir,
            archive_base_url=settings.archive_base_url,
        )
        print(f"[run-once] DC upload pack ready at: {pack.pack_dir}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sloptoon",
        description="WOW Forever Sloptoon — Automated 4~6 cut gag webtoon pipeline for DCInside wowforever gallery.",
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
        help="Generate a 4~6 cut sloptoon episode from a specific post or top auto-scouted post.",
    )
    target_group = p_gen.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--post-no", type=str, help="Specific DCInside wowforever post number.")
    target_group.add_argument("--auto", action="store_true", help="Automatically select the top unproduced recommend post.")
    p_gen.add_argument("--dry-run", action="store_true", help="Build and print a preview script without calling Gemini API or modifying data/episodes.json.")
    p_gen.add_argument("--text-model", type=str, default=None, help=f"Override Gemini text model (default: {DEFAULT_TEXT_MODEL}).")
    p_gen.add_argument(
        "--image-model",
        type=str,
        default=None,
        choices=list(SUPPORTED_IMAGE_MODELS),
        help="Select Gemini image model.",
    )
    p_gen.add_argument("--episode-number", type=int, default=None, help="Override sequential episode number.")
    p_gen.add_argument("--pages", type=int, default=1, help="Pages to scan when using --auto.")
    p_gen.add_argument("--skip-site", action="store_true", help="Skip rebuilding static site after generation.")
    p_gen.set_defaults(func=cmd_generate)

    # build-site
    p_site = subparsers.add_parser(
        "build-site",
        help="Build the static #FFFFFF webtoon archive into site/.",
    )
    p_site.set_defaults(func=cmd_build_site)

    # pack-dc
    p_pack = subparsers.add_parser(
        "pack-dc",
        help="Create a policy-compliant manual DCInside upload pack (images + title/body text).",
    )
    p_pack.add_argument("episode_id", type=str, help="Episode ID (e.g. ep001, ep002).")
    p_pack.add_argument("--open-browser", action="store_true", help="Open official wowforever gallery write page in default browser.")
    p_pack.add_argument("--output-dir", type=str, default=None, help="Custom output directory (default: upload_pack/<episode_id>).")
    p_pack.add_argument("--archive-url", type=str, default=None, help="Public web archive base URL for body link.")
    clip_group = p_pack.add_mutually_exclusive_group()
    clip_group.add_argument("--copy-title", action="store_true", help="Copy formatted post title to clipboard.")
    clip_group.add_argument("--copy-body", action="store_true", help="Copy formatted post body to clipboard.")
    p_pack.set_defaults(func=cmd_pack_dc)

    # serve
    p_serve = subparsers.add_parser(
        "serve",
        help="Serve the static webtoon archive locally over HTTP.",
    )
    p_serve.add_argument("--port", type=int, default=8765, help="Port to listen on (default: 8765).")
    p_serve.add_argument("--host", type=str, default="127.0.0.1", help="Host interface (default: 127.0.0.1).")
    p_serve.add_argument("--rebuild", action="store_true", help="Rebuild static site before starting server.")
    p_serve.set_defaults(func=cmd_serve)

    # run-once
    p_once = subparsers.add_parser(
        "run-once",
        help="Run one complete cycle: scout -> generate -> compose -> update index -> build-site.",
    )
    p_once.add_argument("--dry-run", action="store_true", help="Preview top candidate and dry-run script without API calls.")
    p_once.add_argument("--text-model", type=str, default=None, help=f"Override Gemini text model (default: {DEFAULT_TEXT_MODEL}).")
    p_once.add_argument(
        "--image-model",
        type=str,
        default=None,
        choices=list(SUPPORTED_IMAGE_MODELS),
        help="Select Gemini image model.",
    )
    p_once.add_argument("--pages", type=int, default=1, help="Recommend list pages to scan.")
    p_once.add_argument("--pack-dc", action="store_true", help="Also generate a DCInside manual upload pack.")
    p_once.set_defaults(func=cmd_run_once)

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
