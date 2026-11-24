"""Command-line interface (`sloptoon`) for the WOW Forever Sloptoon pipeline."""

from __future__ import annotations

import argparse
import functools
import http.server
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
    DEFAULT_ARCHIVE_BASE_URL,
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
    layout: str = "classic",
    bg: str | None = None,
) -> EpisodeRecord | EpisodeScript:
    records = load_episode_records(settings.episodes_json)
    ep_num = episode_number or _next_episode_number(records)
    ep_id = f"ep{ep_num:03d}"
    layout_choice = (layout or "classic").strip().lower()
    if layout_choice not in {"classic", "v4"}:
        raise ValueError(f"Unsupported layout '{layout}'. Choose 'classic' or 'v4'.")

    if bg is None:
        bg_choice = "full_bleed" if layout_choice == "v4" else "clean_white"
    else:
        bg_choice = bg.strip().lower()
        if bg_choice not in {"full_bleed", "clean_white"}:
            raise ValueError(
                f"Unsupported background style '{bg}'. Choose 'full_bleed' or 'clean_white'."
            )

    if dry_run:
        if layout_choice == "v4":
            from wow_sloptoon import writer as _writer

            script = _writer.build_dry_run_v4_script(
                post,
                episode_number=ep_num,
                background_style=bg_choice,  # type: ignore[arg-type]
            )
            print(
                f"[DRY-RUN] Generated V4 5-act preview script for {ep_id} "
                f"(source #{post.post_no}, {len(script.cuts)} cuts, bg={bg_choice}):"
            )
        else:
            script = build_dry_run_script(post, episode_number=ep_num)
            if script.background_style != bg_choice:
                script = script.model_copy(update={"background_style": bg_choice})
            print(f"[DRY-RUN] Generated preview script for {ep_id} (source #{post.post_no}):")
        print(script_to_pretty_json(script))
        return script

    resolved_image_model = resolve_image_model(image_model, settings)
    resolved_text_model = text_model or settings.text_model or DEFAULT_TEXT_MODEL
    ep_dir = settings.episodes_dir / ep_id

    if layout_choice == "v4":
        from wow_sloptoon import artist as _artist
        from wow_sloptoon import composer as _composer
        from wow_sloptoon import writer as _writer

        print(
            f"[1/4] Writing V4 5-act script for {ep_id} from #{post.post_no} "
            f"(model={resolved_text_model}, bg={bg_choice})..."
        )
        script = _writer.generate_v4_episode_script(
            post,
            episode_number=ep_num,
            settings=settings,
            model=resolved_text_model,
            background_style=bg_choice,  # type: ignore[arg-type]
        )
        if script.background_style != bg_choice:
            script = script.model_copy(update={"background_style": bg_choice})

        raw_pages_dir = settings.data_dir / "raw_pages" / ep_id
        act_count = len(script.acts) if script.acts else 5
        bg_label = "full-bleed boxed" if bg_choice == "full_bleed" else "pure-#FFFFFF"
        print(
            f"[2/4] Generating {act_count} {bg_label} V4 2K act pages "
            f"({len(script.cuts)} cuts total, model={resolved_image_model})..."
        )
        raw_page_paths = _artist.generate_v4_episode_pages(
            script,
            raw_pages_dir,
            settings=settings,
            model=resolved_image_model,
        )

        print(f"[3/4] Composing V4 variable-layout pages & watermark CTA into {ep_dir}...")
        composed = _composer.compose_v4_episode(
            script,
            raw_page_paths,
            ep_dir,
            watermark_url=settings.archive_base_url,
        )
    else:
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

        print(f"[3/4] Composing speech bubbles & watermark CTA into {ep_dir}...")
        composed = composer.compose_episode(
            script,
            raw_cut_paths,
            ep_dir,
            watermark_url=settings.archive_base_url,
        )

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
        layout=getattr(args, "layout", "classic"),
        bg=getattr(args, "bg", None),
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

    if getattr(args, "open_folder", False):
        opened_folder = dc_packager.open_pack_folder(pack.pack_dir)
        print(f"  Pack folder      : {'opened' if opened_folder else 'skipped (headless/unavailable)'}")

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
        layout=getattr(args, "layout", "classic"),
        bg=getattr(args, "bg", None),
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


def _has_real_gemini_api_key(settings: Settings) -> bool:
    key = (settings.gemini_api_key or "").strip()
    if not key:
        return False
    return key.lower() not in {"your-gemini-api-key-here", "changeme", "placeholder"}


def cmd_watermark_all(args: argparse.Namespace, settings: Settings) -> int:
    from wow_sloptoon import composer, dc_packager

    records = load_episode_records(settings.episodes_json)
    if not records:
        print(f"No episodes found in {settings.episodes_json}.")
        return 0

    site_url = (args.site_url or settings.archive_base_url or composer.DEFAULT_WATERMARK_URL).strip()
    watermarked_count = 0
    repacked_count = 0

    for record in records:
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

        pack_dir = settings.upload_pack_dir / record.episode_id
        if args.repack or pack_dir.exists():
            dc_packager.create_dc_upload_pack(
                record,
                stamped,
                pack_dir,
                archive_base_url=settings.archive_base_url,
            )
            repacked_count += 1
            print(f"     Re-packed upload pack: {pack_dir}")

    print(
        f"Done! Watermarked {watermarked_count}/{len(records)} episode(s) "
        f"(banner URL: {site_url}, repacked: {repacked_count})."
    )
    return 0


def cmd_queue(args: argparse.Namespace, settings: Settings) -> int:
    from wow_sloptoon import scheduler

    queue_path = scheduler.default_queue_path(settings)
    items = scheduler.sync_publish_queue(
        episodes_json=settings.episodes_json,
        queue_path=queue_path,
    )

    if args.json:
        payload = [item.model_dump(mode="json") for item in items]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if not items:
        print("Publish queue is empty (no episodes in data/episodes.json).")
        return 0

    print(f"DCInside Publish Queue ({queue_path}):")
    print(f"{'ID':<8} {'EP':<5} {'STATUS':<10} {'UPDATED':<20} {'TITLE'}")
    print("-" * 82)
    for item in items:
        ts = item.published_at or item.packed_at or item.queued_at
        ts_short = ts[:19].replace("T", " ") if ts else "-"
        title_line = item.title if len(item.title) <= 44 else (item.title[:41] + "...")
        print(
            f"{item.episode_id:<8} EP.{item.episode_number:<2} "
            f"{item.status:<10} {ts_short:<20} {title_line}"
        )
        if item.dc_post_url:
            print(f"{'':<25} DC URL: {item.dc_post_url}")

    n_pub = sum(1 for i in items if i.status == "published")
    n_packed = sum(1 for i in items if i.status == "packed")
    n_pend = sum(1 for i in items if i.status == "pending")
    print("-" * 82)
    print(f"Total: {len(items)} | published: {n_pub} | packed: {n_packed} | pending: {n_pend}")

    nxt = scheduler.get_next_unpublished(queue_path=queue_path)
    if nxt is not None:
        print(
            f"Next unpublished: {nxt.episode_id} (EP.{nxt.episode_number} - {nxt.title})\n"
            "Run: python -m wow_sloptoon.cli publish-next --open-folder --open-browser --copy-body"
        )
    else:
        print("All episodes are published on DCInside!")
    return 0


def cmd_publish_next(args: argparse.Namespace, settings: Settings) -> int:
    from wow_sloptoon import composer, dc_packager, scheduler

    queue_path = scheduler.default_queue_path(settings)
    scheduler.sync_publish_queue(episodes_json=settings.episodes_json, queue_path=queue_path)
    records = load_episode_records(settings.episodes_json)

    if args.episode_id:
        record = _find_episode_record(records, args.episode_id)
        if record is None:
            print(f"Episode '{args.episode_id}' not found in {settings.episodes_json}.", file=sys.stderr)
            return 1
    else:
        next_item = scheduler.get_next_unpublished(queue_path=queue_path)
        if next_item is None:
            print("All episodes are already published on DCInside! Nothing pending in queue.")
            return 0
        record = _find_episode_record(records, next_item.episode_id)
        if record is None:
            print(
                f"Queued episode '{next_item.episode_id}' missing from {settings.episodes_json}.",
                file=sys.stderr,
            )
            return 1

    full_img = _resolve_episode_asset(record.full_image_rel, settings)
    if not full_img.exists():
        print(
            f"Full episode image not found for {record.episode_id}: {full_img}",
            file=sys.stderr,
        )
        return 1

    archive_url = (
        args.archive_url
        if args.archive_url is not None
        else (settings.archive_base_url or DEFAULT_ARCHIVE_BASE_URL)
    )

    # Ensure episode_full.jpg carries the bottom watermark CTA banner idempotently
    stamped_img = composer.retrofit_episode_watermark(
        full_img.parent,
        site_url=archive_url,
        filename=full_img.name,
    )

    pack_dir = settings.upload_pack_dir / record.episode_id
    pack = dc_packager.create_dc_upload_pack(
        record,
        stamped_img,
        pack_dir,
        archive_base_url=archive_url,
        gallery_id=settings.gallery_id,
    )

    scheduler.mark_episode_packed(
        record.episode_id,
        pack_dir=pack.pack_dir,
        queue_path=queue_path,
    )

    print(f"[publish-next] Ready for manual DCInside upload: {record.episode_id} (EP.{record.episode_number})")
    print(f"  Title     : {pack.title_text}")
    print(f"  Pack Dir  : {pack.pack_dir}")
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

    if args.open_folder:
        opened = dc_packager.open_pack_folder(pack.pack_dir)
        print(f"  Explorer folder  : {'opened' if opened else 'skipped (headless/unavailable)'}")

    if args.open_browser:
        url = dc_packager.open_dc_write_page(settings.gallery_id)
        print(f"  Browser opened   : {url}")
        print("  (Please log in, attach the watermarked JPGs, complete CAPTCHA, and submit manually.)")

    print(
        f"\nAfter posting on DCInside, mark it done with:\n"
        f"  python -m wow_sloptoon.cli mark-published {record.episode_id} --dc-url <POST_URL>"
    )
    return 0


def cmd_mark_published(args: argparse.Namespace, settings: Settings) -> int:
    from wow_sloptoon import scheduler

    queue_path = scheduler.default_queue_path(settings)
    try:
        updated = scheduler.mark_episode_published(
            args.episode_id,
            dc_post_url=args.dc_url or "",
            queue_path=queue_path,
            episodes_json=settings.episodes_json,
        )
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"[OK] Marked {updated.episode_id} (EP.{updated.episode_number}) as published.")
    if updated.dc_post_url:
        print(f"  DC Post URL  : {updated.dc_post_url}")
    print(f"  Published At : {updated.published_at}")

    nxt = scheduler.get_next_unpublished(queue_path=queue_path)
    if nxt is not None:
        print(f"  Next in queue: {nxt.episode_id} (EP.{nxt.episode_number} - {nxt.title})")
    else:
        print("  All episodes are now published!")
    return 0


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


def cmd_autopilot(args: argparse.Namespace, settings: Settings) -> int:
    from wow_sloptoon import dc_packager, scheduler

    queue_path = scheduler.default_queue_path(settings)
    existing_records = load_episode_records(settings.episodes_json)
    existing_post_nos = {r.source_post_no for r in existing_records}

    print(f"[autopilot 1/6] Scouting unproduced recommend posts from '{settings.gallery_id}'...")
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
                skip_site=True,
                layout=getattr(args, "layout", "classic"),
                bg=getattr(args, "bg", None),
            )
        else:
            print("[autopilot DRY-RUN] No new unproduced recommend candidates found.")
        print(
            "[autopilot DRY-RUN] Would run: generate (if GEMINI_API_KEY set) -> build-site -> "
            "pack-dc -> sync_publish_queue"
            + (" -> deploy-pages.ps1" if args.deploy else "")
            + " -> notify user (manual DCInside upload only; never auto-POSTs)."
        )
        return 0

    created_record: EpisodeRecord | None = None
    if candidates and _has_real_gemini_api_key(settings):
        post, score = candidates[0]
        if not post.body:
            post = scout.fetch_post_detail(post.post_no, base_post=post)
        print(f"[autopilot 2/6] Generating episode from #{post.post_no} (score={score:.2f}): {post.title}")
        res = _generate_for_post(
            post,
            settings=settings,
            dry_run=False,
            text_model=args.text_model,
            image_model=args.image_model,
            skip_site=True,
            layout=getattr(args, "layout", "classic"),
            bg=getattr(args, "bg", None),
        )
        if isinstance(res, EpisodeRecord):
            created_record = res
    elif not candidates:
        print("[autopilot 2/6] No new unproduced recommend posts found; refreshing archive & queue.")
    else:
        print("[autopilot 2/6] GEMINI_API_KEY not set; skipping episode generation.")

    print("[autopilot 3/6] Building static web archive (site/)...")
    built = _run_build_site(settings)
    print(f"  Archive built: {built}")

    print("[autopilot 4/6] Syncing DCInside publish queue...")
    scheduler.sync_publish_queue(episodes_json=settings.episodes_json, queue_path=queue_path)

    target_record: EpisodeRecord | None = created_record
    if target_record is None:
        all_records = load_episode_records(settings.episodes_json)
        nxt_item = scheduler.get_next_unpublished(queue_path=queue_path)
        if nxt_item is not None:
            target_record = _find_episode_record(all_records, nxt_item.episode_id)

    packed_dir: Path | None = None
    if target_record is not None:
        full_img = _resolve_episode_asset(target_record.full_image_rel, settings)
        if full_img.exists():
            pack_dir = settings.upload_pack_dir / target_record.episode_id
            print(f"[autopilot 5/6] Packing DCInside manual upload pack for {target_record.episode_id}...")
            pack = dc_packager.create_dc_upload_pack(
                target_record,
                full_img,
                pack_dir,
                archive_base_url=settings.archive_base_url,
                gallery_id=settings.gallery_id,
            )
            packed_dir = pack.pack_dir
            scheduler.mark_episode_packed(
                target_record.episode_id,
                pack_dir=pack.pack_dir,
                queue_path=queue_path,
            )
            print(f"  Upload pack ready: {pack.pack_dir}")
        else:
            print(f"[autopilot 5/6] Skipping pack-dc: missing image {full_img}", file=sys.stderr)
    else:
        print("[autopilot 5/6] All episodes already published; no upload pack needed.")

    if args.deploy:
        rc = _run_deploy_pages_script(settings)
        if rc != 0:
            print(f"[autopilot ERROR] deploy-pages.ps1 exited with code {rc}", file=sys.stderr)
            return rc
    else:
        print("[autopilot 6/6] Local run complete (pass --deploy to push to slopwow.github.io).")

    if target_record is not None:
        scheduler.notify_new_episode_ready(
            target_record.episode_id,
            target_record.title,
            site_url=settings.archive_base_url,
            pack_dir=packed_dir,
            use_toast=not args.no_notify,
        )

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
    p_gen.add_argument(
        "--layout",
        type=str,
        choices=["classic", "v4"],
        default="classic",
        help="Episode layout mode: 'classic' (4~6 cut 2-tier) or 'v4' (5-act 10~14 cut variable layout).",
    )
    p_gen.add_argument(
        "--bg",
        type=str,
        choices=["full_bleed", "clean_white"],
        default=None,
        help="Panel background mode ('full_bleed' default for --layout v4, 'clean_white' default for --layout classic).",
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
    p_pack.add_argument("--open-folder", action="store_true", help="Open local upload_pack folder in Explorer.")
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
    p_once.add_argument(
        "--layout",
        type=str,
        choices=["classic", "v4"],
        default="classic",
        help="Episode layout mode: 'classic' (4~6 cut 2-tier) or 'v4' (5-act 10~14 cut variable layout).",
    )
    p_once.add_argument(
        "--bg",
        type=str,
        choices=["full_bleed", "clean_white"],
        default=None,
        help="Panel background mode ('full_bleed' default for --layout v4, 'clean_white' default for --layout classic).",
    )
    p_once.add_argument("--pages", type=int, default=1, help="Recommend list pages to scan.")
    p_once.add_argument("--pack-dc", action="store_true", help="Also generate a DCInside manual upload pack.")
    p_once.set_defaults(func=cmd_run_once)

    # watermark-all
    p_wm = subparsers.add_parser(
        "watermark-all",
        help="Idempotently apply the Sloptoon bottom watermark CTA banner to all episodes in data/episodes.json.",
    )
    p_wm.add_argument(
        "--site-url",
        type=str,
        default="slopwow.github.io",
        help="Archive domain shown in the bottom watermark banner (default: slopwow.github.io).",
    )
    p_wm.add_argument(
        "--repack",
        action="store_true",
        help="Create or refresh upload_pack/<ep_id>/ for all episodes even if not packed yet.",
    )
    p_wm.set_defaults(func=cmd_watermark_all)

    # queue
    p_queue = subparsers.add_parser(
        "queue",
        help="Sync and display the DCInside manual publish queue (pending / packed / published).",
    )
    p_queue.add_argument("--json", action="store_true", help="Output publish queue as JSON.")
    p_queue.set_defaults(func=cmd_queue)

    # publish-next
    p_pub = subparsers.add_parser(
        "publish-next",
        help="Prepare watermarked upload pack for the next unpublished episode and assist manual DCInside posting.",
    )
    p_pub.add_argument("--episode-id", type=str, default=None, help="Optionally target a specific episode ID.")
    p_pub.add_argument("--archive-url", type=str, default=None, help="Override archive base URL in post body & watermark.")
    p_pub.add_argument("--open-folder", action="store_true", help="Open upload_pack/<ep_id>/ in Explorer for drag-and-drop.")
    p_pub.add_argument("--open-browser", action="store_true", help="Open official wowforever gallery write page in browser.")
    pub_clip_group = p_pub.add_mutually_exclusive_group()
    pub_clip_group.add_argument("--copy-body", action="store_true", help="Copy formatted post body to clipboard.")
    pub_clip_group.add_argument("--copy-title", action="store_true", help="Copy formatted post title to clipboard.")
    p_pub.set_defaults(func=cmd_publish_next)

    # mark-published
    p_mark = subparsers.add_parser(
        "mark-published",
        help="Record an episode as manually published on DCInside in data/publish_queue.json.",
    )
    p_mark.add_argument("episode_id", type=str, help="Episode ID to mark published (e.g. ep001).")
    p_mark.add_argument("--dc-url", type=str, default="", help="Optional published DCInside post URL.")
    p_mark.set_defaults(func=cmd_mark_published)

    # autopilot
    p_auto = subparsers.add_parser(
        "autopilot",
        help="Policy-compliant end-to-end pipeline: scout -> generate -> build-site -> pack-dc -> queue -> optional deploy -> notify.",
    )
    p_auto.add_argument("--deploy", action="store_true", help="Run deploy-pages.ps1 to publish site/ to slopwow.github.io.")
    p_auto.add_argument("--dry-run", action="store_true", help="Preview scout + dry-run script without API calls or deploy.")
    p_auto.add_argument("--text-model", type=str, default=None, help=f"Override Gemini text model (default: {DEFAULT_TEXT_MODEL}).")
    p_auto.add_argument(
        "--image-model",
        type=str,
        default=None,
        choices=list(SUPPORTED_IMAGE_MODELS),
        help="Select Gemini image model.",
    )
    p_auto.add_argument(
        "--layout",
        type=str,
        choices=["classic", "v4"],
        default="classic",
        help="Episode layout mode: 'classic' (4~6 cut 2-tier) or 'v4' (5-act 10~14 cut variable layout).",
    )
    p_auto.add_argument(
        "--bg",
        type=str,
        choices=["full_bleed", "clean_white"],
        default=None,
        help="Panel background mode ('full_bleed' default for --layout v4, 'clean_white' default for --layout classic).",
    )
    p_auto.add_argument("--pages", type=int, default=1, help="Recommend list pages to scan.")
    p_auto.add_argument("--no-notify", action="store_true", help="Suppress Windows toast notification (console output only).")
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
