"""Static web archive builder for wow-forever-sloptoon.

Generates a pure-white (#FFFFFF) Korean 2~2.5-head SD gag-sloptoon web archive
deployable to GitHub Pages (slopwow.github.io), local HTTP servers, or direct `file://`.
"""

from __future__ import annotations

import hashlib
import html
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from wow_sloptoon.cast import CAST_BIBLE, CAST_BY_NAME, CastMember, resolve_cast_member
from wow_sloptoon.composer import clean_white_bg, extract_art_bbox
from wow_sloptoon.config import DEFAULT_ARCHIVE_BASE_URL, DEFAULT_GALLERY_ID
from wow_sloptoon.models import EpisodeRecord

SITE_NAME = "와우 포에버 슬롭툰"
SITE_TAGLINE = "디시 WOW 포에버 마이너 갤러리 개념글 상황극 아카이브"
SITE_DESCRIPTION = (
    "디시인사이드 WOW 포에버 마이너 갤러리 개념글을 2~2.5등신 귀염뽀짝 SD 고정 9인 캐스트와 "
    "동행 펫(아기 곰·공허방랑자)의 상황극 웹툰으로 아카이빙합니다."
)
LEGAL_NOTICE = (
    "본 사이트는 World of Warcraft 및 디시인사이드 WOW 포에버 마이너 갤러리 기반의 비공식 팬메이드 패러디 아카이브입니다. "
    "모든 에피소드에 원글 출처를 표기하며, 원작자 삭제 요청 시 즉시 비공개 처리합니다."
)

DC_GALLERY_RECOMMEND_URL = (
    f"https://gall.dcinside.com/mgallery/board/lists/?id={DEFAULT_GALLERY_ID}&exception_mode=recommend"
)

# Fallback normalized (x0, y0, x1, y1) crop boxes on `cast_sheet_c.jpg` when a turnaround is absent.
_CAST_PORTRAIT_BOXES: dict[str, tuple[float, float, float, float]] = {
    "orc_warrior": (0.025, 0.015, 0.200, 0.495),
    "undead_paladin": (0.215, 0.015, 0.395, 0.495),
    "gnome_rogue": (0.400, 0.035, 0.598, 0.495),
    "dwarf_hunter": (0.598, 0.015, 0.790, 0.495),
    "troll_shaman": (0.798, 0.015, 0.975, 0.495),
    "tauren_druid": (0.078, 0.505, 0.265, 0.988),
    "nightelf_priest": (0.288, 0.505, 0.495, 0.988),
    "human_warlock": (0.505, 0.505, 0.725, 0.988),
    "skyborne_mage": (0.740, 0.505, 0.922, 0.988),
}


def _safe_json_for_script(obj: Any) -> str:
    """Serialize data to JSON safe for embedding inside an HTML <script> tag."""
    return (
        json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        .replace("</", "<\\/")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _copy_if_different(src: Path, dst: Path) -> None:
    """Copy `src` to `dst` unless they resolve to the exact same file."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        if dst.exists() and src.resolve() == dst.resolve():
            return
    except OSError:
        pass
    shutil.copy2(src, dst)


def _file_cache_suffix(path: Path) -> str:
    """Return a deterministic `?v=<8-char-sha256>` cache-busting query suffix for synced images."""
    try:
        if path.exists() and path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()[:8]
            return f"?v={digest}"
    except OSError:
        pass
    return ""


def load_episodes(episodes_json: Path) -> list[EpisodeRecord]:
    """Load and validate episodes from `data/episodes.json`.

    Supports both a top-level JSON array `[EpisodeRecord, ...]` and an object
    `{"episodes": [...]}`. Returns records sorted by `episode_number` ascending.
    """
    if not episodes_json.exists():
        return []
    raw_text = episodes_json.read_text(encoding="utf-8").strip()
    if not raw_text:
        return []
    payload = json.loads(raw_text)
    if isinstance(payload, dict):
        items = payload.get("episodes", [])
    elif isinstance(payload, list):
        items = payload
    else:
        raise ValueError(f"Unsupported episodes.json root type: {type(payload).__name__}")

    records = [EpisodeRecord.model_validate(item) for item in items]
    records.sort(key=lambda r: (r.episode_number, r.episode_id))
    return records


def _resolve_media_path(
    rel_or_abs: str,
    episodes_json: Path,
    assets_dir: Path,
    site_dir: Path,
) -> Path | None:
    """Resolve an episode media path flexibly across project/data/assets/site roots."""
    if not rel_or_abs:
        return None
    p = Path(rel_or_abs)
    if p.is_absolute() and p.exists():
        return p

    candidates = [
        episodes_json.parent.parent / p,
        episodes_json.parent / p,
        assets_dir.parent / p,
        assets_dir / p,
        site_dir / p,
        Path.cwd() / p,
    ]
    for cand in candidates:
        if cand.exists() and cand.is_file():
            return cand
    return None


def generate_episode_thumbnail(
    source_image: Path,
    dest_thumb: Path,
    size: tuple[int, int] = (800, 500),
    padding: int = 20,
) -> Path:
    """Create a crisp pure-white (#FFFFFF) card thumbnail cropped from key panel art."""
    dest_thumb.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source_image) as im:
        rgb = im.convert("RGB")
        w, h = rgb.size
        arr = np.array(rgb)

        ink_mask = (arr < 242).any(axis=2)
        crop_box: tuple[int, int, int, int]

        if w >= 600 and 1000 <= h <= 1650:
            y_search_top = int(h * 0.16)
            y_search_bot = int(h * 0.642)
            slice_arr = arr[y_search_top:y_search_bot, :].copy()
            slice_ink = (slice_arr < 242).any(axis=2)
            sh, sw = slice_ink.shape
            visited = np.zeros_like(slice_ink, dtype=bool)
            for seed_x in range(sw):
                if slice_ink[0, seed_x] and not visited[0, seed_x]:
                    stack = [(0, seed_x)]
                    visited[0, seed_x] = True
                    while stack:
                        cy, cx = stack.pop()
                        slice_arr[cy, cx] = 255
                        slice_ink[cy, cx] = False
                        for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                            if 0 <= ny < sh and 0 <= nx < sw and slice_ink[ny, nx] and not visited[ny, nx]:
                                visited[ny, nx] = True
                                stack.append((ny, nx))

            ys = np.where(slice_ink.any(axis=1))[0]
            xs = np.where(slice_ink.any(axis=0))[0]
            if len(ys) > 40 and len(xs) > 40:
                ry0 = max(0, int(ys[0]) - 8)
                ry1 = min(sh, int(ys[-1]) + 8)
                rx0 = max(0, int(xs[0]) - 16)
                rx1 = min(sw, int(xs[-1]) + 16)
                region = Image.fromarray(slice_arr[ry0:ry1, rx0:rx1], mode="RGB")
            else:
                region = Image.fromarray(slice_arr, mode="RGB")
        elif h > w * 2.2:
            start_y = min(int(h * 0.14), 560)
            band_h = min(int(w * 0.62), h - start_y)
            region = rgb.crop((0, start_y, w, min(h, start_y + max(band_h, 100))))
        else:
            ys = np.where(ink_mask.any(axis=1))[0]
            xs = np.where(ink_mask.any(axis=0))[0]
            if len(ys) > 10 and len(xs) > 10:
                crop_box = (
                    max(0, int(xs[0]) - 10),
                    max(0, int(ys[0]) - 10),
                    min(w, int(xs[-1]) + 10),
                    min(h, int(ys[-1]) + 10),
                )
            else:
                crop_box = (0, 0, w, h)
            region = rgb.crop(crop_box)

        reg_arr = np.array(region)
        near_white = (reg_arr[:, :, 0] >= 248) & (reg_arr[:, :, 1] >= 248) & (reg_arr[:, :, 2] >= 248)
        reg_arr[near_white] = 255
        region = Image.fromarray(reg_arr, mode="RGB")

        target_w, target_h = size
        inner_w = max(1, target_w - padding * 2)
        inner_h = max(1, target_h - padding * 2)
        rw, rh = region.size
        scale = min(inner_w / max(rw, 1), inner_h / max(rh, 1))
        new_w = max(1, int(round(rw * scale)))
        new_h = max(1, int(round(rh * scale)))
        resized = region.resize((new_w, new_h), Image.Resampling.LANCZOS)

        canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
        paste_x = (target_w - new_w) // 2
        paste_y = target_h - new_h - max(4, padding // 2) if (target_h - new_h) < padding * 3 else (target_h - new_h) // 2
        paste_y = max(padding // 2, min(paste_y, target_h - new_h))
        canvas.paste(resized, (paste_x, paste_y))
        canvas.save(dest_thumb, format="JPEG", quality=93, optimize=True)

    return dest_thumb


def _erase_disconnected_edge_fragments(arr: np.ndarray, *, edges: tuple[int, ...]) -> np.ndarray:
    """Erase disconnected non-white fragments touching specified vertical borders (neighbor bleed)."""
    ink = (arr < 245).any(axis=2)
    ch, cw = ink.shape
    visited = np.zeros_like(ink, dtype=bool)
    for edge_x in edges:
        if edge_x < 0 or edge_x >= cw:
            continue
        for seed_y in range(ch):
            if ink[seed_y, edge_x] and not visited[seed_y, edge_x]:
                stack = [(seed_y, edge_x)]
                visited[seed_y, edge_x] = True
                comp: list[tuple[int, int]] = []
                min_cx = max_cx = edge_x
                while stack:
                    cy, cx = stack.pop()
                    comp.append((cy, cx))
                    if cx < min_cx:
                        min_cx = cx
                    if cx > max_cx:
                        max_cx = cx
                    for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                        if 0 <= ny < ch and 0 <= nx < cw and ink[ny, nx] and not visited[ny, nx]:
                            visited[ny, nx] = True
                            stack.append((ny, nx))
                touches_center = not (max_cx < int(cw * 0.24) or min_cx > int(cw * 0.76))
                if not touches_center:
                    for cy, cx in comp:
                        arr[cy, cx] = 255
    return arr


def _fit_square_portrait(cropped: Image.Image, size: int = 360) -> Image.Image:
    """Clean, tight-crop via `extract_art_bbox`, and center with balanced pure-white padding."""
    cleaned = clean_white_bg(cropped)
    bb = extract_art_bbox(cleaned, threshold=248)
    if bb is not None:
        ax0, ay0, ax1, ay1 = bb
        trimmed = cleaned.crop((ax0, ay0, ax1 + 1, ay1 + 1))
    else:
        trimmed = cleaned

    pad = max(14, int(round(size * 0.055)))
    inner = max(16, size - pad * 2)
    tw, th = trimmed.size
    scale = min(inner / max(tw, 1), inner / max(th, 1))
    nw = max(1, int(round(tw * scale)))
    nh = max(1, int(round(th * scale)))
    resized = clean_white_bg(trimmed.resize((nw, nh), Image.Resampling.LANCZOS))

    canvas = Image.new("RGB", (size, size), (255, 255, 255))
    px = (size - nw) // 2
    py = max(pad // 2, min(size - nh - 6, (size - nh) // 2 + 2))
    canvas.paste(resized, (px, py))
    return canvas


def _extract_front_portrait_from_turnaround(turnaround_path: Path, size: int = 360) -> Image.Image | None:
    """Crop the front-facing 2.5-head SD view (left 1/3) from a 3-view turnaround sheet."""
    with Image.open(turnaround_path) as im:
        cleaned = clean_white_bg(im)
        w, h = cleaned.size
        if w < 180 or h < 90:
            return None

        # Detect the pure-white vertical valley separating Front (left 1/3) from Side (middle 1/3).
        # Search generously up to 45% width and accept even 1px pure-white valleys (e.g. wide daggers).
        arr = np.asarray(cleaned)
        col_ink_counts = (arr < 245).any(axis=2).sum(axis=0)
        col_ink = col_ink_counts > 0
        lo_x = max(1, int(w * 0.28))
        hi_x = min(w - 1, int(w * 0.45))

        best_gap_start = -1
        best_gap_len = 0
        cur_start = -1
        for x in range(lo_x, hi_x):
            if not col_ink[x]:
                if cur_start < 0:
                    cur_start = x
            else:
                if cur_start >= 0:
                    gap_len = x - cur_start
                    if gap_len > best_gap_len:
                        best_gap_len = gap_len
                        best_gap_start = cur_start
                    cur_start = -1
        if cur_start >= 0:
            gap_len = hi_x - cur_start
            if gap_len > best_gap_len:
                best_gap_len = gap_len
                best_gap_start = cur_start

        if best_gap_len >= 1:
            # Ensure at least 1 pure-white column stays inside the right edge of `front_crop`
            split_x = min(w, best_gap_start + max(1, best_gap_len // 2))
        else:
            # Fallback to the sparsest vertical column between 30% and 44% width
            min_lo = max(1, int(w * 0.30))
            min_hi = min(w - 1, int(w * 0.44))
            split_x = min_lo + int(np.argmin(col_ink_counts[min_lo:min_hi]))

        front_crop = cleaned.crop((0, 0, max(20, split_x), h))
        front_arr = np.array(front_crop)
        front_arr = _erase_disconnected_edge_fragments(front_arr, edges=(front_arr.shape[1] - 1,))
        return _fit_square_portrait(Image.fromarray(front_arr, mode="RGB"), size=size)


def extract_cast_portraits(
    cast_sheet_clean: Path | None,
    dest_cast_dir: Path,
    size: int = 360,
    *,
    turnarounds_dir: Path | None = None,
) -> dict[str, str]:
    """Generate 9 individual 1:1 square SD portraits from turnarounds (with `cast_sheet_c.jpg` fallback).

    Priority 1: Left 1/3 front view of `assets/turnarounds/<cast_id>.jpg`, tight-cropped via
    `extract_art_bbox` with balanced pure-white margin.
    Priority 2: Normalized crop fallback from `cast_sheet_c.jpg` when a turnaround file is absent.
    """
    dest_cast_dir.mkdir(parents=True, exist_ok=True)
    generated: dict[str, str] = {}

    sheet_rgb: Image.Image | None = None
    if cast_sheet_clean is not None and cast_sheet_clean.exists():
        with Image.open(cast_sheet_clean) as sheet_im:
            if sheet_im.width >= 200 and sheet_im.height >= 120:
                sheet_rgb = sheet_im.convert("RGB")

    for member in CAST_BIBLE:
        portrait_im: Image.Image | None = None

        # Priority 1: Individual 2.5-head SD turnaround front view (left 1/3)
        if turnarounds_dir is not None:
            t_path = turnarounds_dir / member.turnaround_filename
            if t_path.exists() and t_path.is_file():
                portrait_im = _extract_front_portrait_from_turnaround(t_path, size=size)

        # Priority 2: Fallback crop from master cast sheet when turnaround is unavailable
        if portrait_im is None and sheet_rgb is not None:
            box_ratio = _CAST_PORTRAIT_BOXES.get(member.id)
            if box_ratio is not None:
                w, h = sheet_rgb.size
                x0 = max(0, int(round(w * box_ratio[0])))
                y0 = max(0, int(round(h * box_ratio[1])))
                x1 = min(w, int(round(w * box_ratio[2])))
                y1 = min(h, int(round(h * box_ratio[3])))
                if x1 > x0 + 10 and y1 > y0 + 10:
                    crop = sheet_rgb.crop((x0, y0, x1, y1))
                    arr = np.array(clean_white_bg(crop))
                    arr = _erase_disconnected_edge_fragments(arr, edges=(0, arr.shape[1] - 1))
                    portrait_im = _fit_square_portrait(Image.fromarray(arr, mode="RGB"), size=size)

        if portrait_im is not None:
            out_path = dest_cast_dir / f"{member.id}.jpg"
            portrait_im.save(out_path, format="JPEG", quality=93, optimize=True)
            generated[member.id] = f"assets/cast/{member.id}.jpg"

    return generated


def _normalize_base_url(archive_base_url: str | None) -> str:
    return (archive_base_url or "").strip().rstrip("/")


def _format_date_short(created_at: str) -> str:
    if not created_at:
        return ""
    return created_at.split("T", 1)[0].strip()


_FACTION_BADGE_KO: dict[str, str] = {
    "Alliance": "얼라이언스",
    "Horde": "호드",
    "Neutral-Skyborne": "스카이본",
}


def _cast_member_payload(
    member: CastMember,
    portrait_rel: str | None,
    ep_counts: dict[str, int],
    turnaround_rel: str | None = None,
    companion_turnaround_rel: str | None = None,
) -> dict[str, Any]:
    return {
        "id": member.id,
        "name": member.name,
        "race": member.race,
        "wow_class": member.wow_class,
        "faction": member.faction,
        "faction_label": _FACTION_BADGE_KO.get(member.faction, member.faction),
        "role_tag": member.role_tag,
        "color_hex": member.color_hex,
        "accent_hex": member.accent_hex,
        "personality": member.personality,
        "aliases": list(member.aliases[:5]),
        "portrait": portrait_rel or "",
        "turnaround": turnaround_rel or "",
        "companion_id": member.companion_id,
        "companion_name": member.companion_name,
        "companion_turnaround": companion_turnaround_rel or "",
        "episode_count": ep_counts.get(member.name, 0),
    }


def _render_social_meta(
    *,
    title: str,
    description: str,
    og_type: str,
    path_from_root: str,
    relative_url: str,
    image_rel_from_root: str,
    base_url: str,
    root_prefix: str = "",
) -> str:
    """Render complete Open Graph + Twitter Card meta tags with absolute or relative fallback."""
    clean_path = path_from_root.lstrip("/")
    if base_url:
        og_url = f"{base_url}/{clean_path}" if clean_path else f"{base_url}/"
    else:
        og_url = relative_url

    clean_img = image_rel_from_root.lstrip("/")
    if clean_img:
        og_image = f"{base_url}/{clean_img}" if base_url else f"{root_prefix}{clean_img}"
    else:
        og_image = ""

    lines = [
        f'  <meta name="description" content="{html.escape(description)}">',
        f'  <meta property="og:site_name" content="{html.escape(SITE_NAME)}">',
        f'  <meta property="og:type" content="{html.escape(og_type)}">',
        '  <meta property="og:locale" content="ko_KR">',
        f'  <meta property="og:title" content="{html.escape(title)}">',
        f'  <meta property="og:description" content="{html.escape(description)}">',
        f'  <meta property="og:url" content="{html.escape(og_url)}">',
    ]
    if og_image:
        lines.append(f'  <meta property="og:image" content="{html.escape(og_image)}">')
    lines.extend([
        '  <meta name="twitter:card" content="summary_large_image">',
        f'  <meta name="twitter:title" content="{html.escape(title)}">',
        f'  <meta name="twitter:description" content="{html.escape(description)}">',
    ])
    if og_image:
        lines.append(f'  <meta name="twitter:image" content="{html.escape(og_image)}">')
    if base_url:
        lines.append(f'  <link rel="canonical" href="{html.escape(og_url)}">')
    return "\n".join(lines)


def _select_recommended_episodes(
    site_episodes: list[dict[str, Any]],
    current_id: str,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Select up to `limit` other episodes for binge recommendations (non-adjacent preferred)."""
    idx = next((i for i, item in enumerate(site_episodes) if item["episode_id"] == current_id), -1)
    adjacent_ids: set[str] = set()
    if idx > 0:
        adjacent_ids.add(site_episodes[idx - 1]["episode_id"])
    if 0 <= idx < len(site_episodes) - 1:
        adjacent_ids.add(site_episodes[idx + 1]["episode_id"])

    newest_others = [e for e in reversed(site_episodes) if e["episode_id"] != current_id]
    non_adjacent = [e for e in newest_others if e["episode_id"] not in adjacent_ids]
    adjacent = [e for e in newest_others if e["episode_id"] in adjacent_ids]
    return (non_adjacent + adjacent)[:limit]


def _render_sitemap_xml(site_episodes: list[dict[str, Any]], base_url: str) -> str:
    clean_base = _normalize_base_url(base_url) or DEFAULT_ARCHIVE_BASE_URL
    latest_date = site_episodes[-1]["date_short"] if site_episodes else ""

    def _entry(loc: str, lastmod: str = "", changefreq: str = "weekly", priority: str = "0.8") -> str:
        parts = ["  <url>", f"    <loc>{html.escape(loc)}</loc>"]
        if lastmod and len(lastmod) == 10 and lastmod[4] == "-" and lastmod[7] == "-":
            parts.append(f"    <lastmod>{html.escape(lastmod)}</lastmod>")
        parts.append(f"    <changefreq>{changefreq}</changefreq>")
        parts.append(f"    <priority>{priority}</priority>")
        parts.append("  </url>")
        return "\n".join(parts)

    entries = [
        _entry(f"{clean_base}/", lastmod=latest_date, changefreq="daily", priority="1.0"),
        _entry(f"{clean_base}/cast.html", lastmod=latest_date, changefreq="weekly", priority="0.7"),
    ]
    for ep in site_episodes:
        entries.append(
            _entry(
                f"{clean_base}/episodes/{ep['episode_id']}.html",
                lastmod=ep.get("date_short", ""),
                changefreq="monthly",
                priority="0.9",
            )
        )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )


def _render_robots_txt(base_url: str) -> str:
    clean_base = _normalize_base_url(base_url) or DEFAULT_ARCHIVE_BASE_URL
    return f"User-agent: *\nAllow: /\n\nSitemap: {clean_base}/sitemap.xml\n"


_FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
  <rect width="64" height="64" rx="14" fill="#111318"/>
  <rect x="12" y="13" width="40" height="17" rx="4" fill="#ffffff"/>
  <rect x="12" y="34" width="23" height="17" rx="4" fill="#ffffff"/>
  <rect x="39" y="34" width="13" height="17" rx="4" fill="#0ea5e9"/>
</svg>
"""

_BRAND_MARK_SVG = (
    '<svg class="brand-mark" width="28" height="28" viewBox="0 0 64 64" fill="none" aria-hidden="true">'
    '<rect width="64" height="64" rx="14" fill="#111318"/>'
    '<rect x="12" y="13" width="40" height="17" rx="4" fill="#ffffff"/>'
    '<rect x="12" y="34" width="23" height="17" rx="4" fill="#ffffff"/>'
    '<rect x="39" y="34" width="13" height="17" rx="4" fill="#0ea5e9"/>'
    "</svg>"
)


def _render_head_assets(root_prefix: str = "", css_suffix: str = "") -> str:
    return "\n".join([
        '  <meta name="theme-color" content="#ffffff">',
        f'  <link rel="icon" href="{root_prefix}assets/favicon.svg" type="image/svg+xml">',
        '  <link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>',
        '  <link rel="preconnect" href="https://fonts.googleapis.com">',
        '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        '  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard-dynamic-subset.min.css">',
        '  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600&display=swap">',
        f'  <link rel="stylesheet" href="{root_prefix}assets/style.css{css_suffix}">',
    ])


def _render_nav(active: str, root_prefix: str = "") -> str:
    def _nav_attrs(key: str) -> str:
        if active == key:
            return 'class="nav-link is-active" aria-current="page"'
        if active == "episode" and key == "home":
            return 'class="nav-link is-active"'
        return 'class="nav-link"'

    return f"""
    <header class="site-header">
      <div class="container header-inner">
        <a class="brand" href="{root_prefix}index.html" aria-label="와우 포에버 슬롭툰 홈">
          {_BRAND_MARK_SVG}
          <span class="brand-text">
            <span class="brand-name">와우 포에버 슬롭툰</span>
            <span class="brand-tag">ARCHIVE</span>
          </span>
        </a>
        <nav class="site-nav" aria-label="주요 메뉴">
          <a {_nav_attrs('home')} href="{root_prefix}index.html">에피소드</a>
          <a {_nav_attrs('cast')} href="{root_prefix}cast.html">SD 캐스트 도감</a>
          <button type="button" class="nav-pill-random js-random-ep" title="무작위 다른 에피소드로 이동">🎲 랜덤 화 보기</button>
          <a class="nav-link nav-ext" href="{DC_GALLERY_RECOMMEND_URL}" target="_blank" rel="noopener noreferrer">포에버갤 개념글 ↗</a>
        </nav>
      </div>
    </header>
    """.strip()


def _render_footer(total_episodes: int, root_prefix: str = "") -> str:
    return f"""
    <footer class="site-footer">
      <div class="container footer-inner">
        <div class="footer-brand">
          <div class="footer-eyebrow"><span class="dot-sky" aria-hidden="true"></span>{SITE_TAGLINE}</div>
          <p class="footer-desc">
            포에버갤 개념글의 명장면을 2~2.5등신 귀염뽀짝 SD 고정 9인 캐스트와 동행 펫(아기 곰·공허방랑자)의 순백 상황극 웹툰으로 아카이빙합니다.
            현재 총 <strong>{total_episodes}화</strong>가 아카이브에 보관되어 있습니다.
          </p>
        </div>
        <div class="footer-links">
          <a href="{root_prefix}index.html">전체 에피소드</a>
          <a href="{root_prefix}cast.html">SD 캐스트 도감</a>
          <a href="{DC_GALLERY_RECOMMEND_URL}" target="_blank" rel="noopener noreferrer">디시 WOW 포에버 갤러리 ↗</a>
        </div>
      </div>
      <div class="container footer-legal">
        <p class="legal-notice">{LEGAL_NOTICE}</p>
      </div>
    </footer>
    <button type="button" id="backToTopBtn" class="back-to-top" aria-label="맨 위로 이동" hidden>↑ 맨 위로</button>
    <div id="toast" class="toast" role="status" aria-live="polite" hidden></div>
    """.strip()


def _render_cast_chip_html(cast_name: str, root_prefix: str = "") -> str:
    member = resolve_cast_member(cast_name)
    color = member.color_hex if member else "#111318"
    label = html.escape(member.name if member else cast_name)
    target = f"{root_prefix}cast.html#{html.escape(member.id)}" if member else f"{root_prefix}cast.html"
    return (
        f'<a class="cast-chip" href="{target}">'
        f'<span class="cast-dot" style="background:{html.escape(color)};"></span>'
        f"{label}</a>"
    )


def _render_episode_card(
    ep: dict[str, Any],
    *,
    root_prefix: str = "",
    include_filter_attrs: bool = False,
) -> str:
    chips = "".join(
        f'<span class="mini-chip"><span class="cast-dot" style="background:{html.escape((CAST_BY_NAME[c].color_hex if c in CAST_BY_NAME else "#111318"))};"></span>{html.escape(c)}</span>'
        for c in ep["cast_used"]
    )
    id_attr = f'\n              data-id="{html.escape(ep["episode_id"])}"'
    filter_attrs = id_attr
    if include_filter_attrs:
        filter_attrs = (
            f"{id_attr}"
            f'\n              data-num="{ep["episode_number"]}"'
            f'\n              data-title="{html.escape(ep["title"].lower())}"'
            f'\n              data-sub="{html.escape(ep["subtitle"].lower())}"'
            f'\n              data-post="{html.escape(ep["source_post_no"].lower())}"'
            f'\n              data-cast="{html.escape("|".join(ep["cast_used"]))}"'
        )
    ep_href = f"{root_prefix}episodes/{html.escape(ep['episode_id'])}.html"
    return f"""
            <article class="ep-card"{filter_attrs}>
              <a class="ep-card-link" href="{ep_href}">
                <div class="ep-thumb-wrap">
                  <img src="{root_prefix}{html.escape(ep['thumb_image'])}" alt="EP.{ep['episode_number']} {html.escape(ep['title'])}" class="ep-thumb" width="800" height="500" loading="lazy" decoding="async">
                  <span class="thumb-cuts">{ep['cut_count']}컷</span>
                </div>
                <div class="ep-card-body">
                  <div class="meta-row">
                    <span class="ep-index">EP.{ep['episode_number']}</span>
                    <span class="meta-sep" aria-hidden="true">·</span>
                    <span class="post-no">#{html.escape(ep['source_post_no'])}</span>
                    <span class="meta-date">{html.escape(ep['date_short'])}</span>
                    <span class="ep-read-mark" hidden>✓ 읽음</span>
                  </div>
                  <h3 class="ep-card-title">{html.escape(ep['title'])}</h3>
                  <p class="ep-card-sub">{html.escape(ep['subtitle'])}</p>
                  <div class="mini-chip-row">{chips}</div>
                </div>
              </a>
            </article>
            """


def _render_index_html(
    site_episodes: list[dict[str, Any]],
    cast_payload: list[dict[str, Any]],
    total_episodes: int,
    *,
    base_url: str = DEFAULT_ARCHIVE_BASE_URL,
    fallback_og_image: str = "",
    css_suffix: str = "",
    js_suffix: str = "",
) -> str:
    newest_first = list(reversed(site_episodes))
    latest = newest_first[0] if newest_first else None
    og_image_rel = (latest["thumb_image"] if latest else fallback_og_image).split("?", 1)[0]
    page_title = f"{SITE_NAME} — {SITE_TAGLINE}"
    social_meta = _render_social_meta(
        title=page_title,
        description=SITE_DESCRIPTION,
        og_type="website",
        path_from_root="",
        relative_url="index.html",
        image_rel_from_root=og_image_rel,
        base_url=base_url,
        root_prefix="",
    )

    if latest:
        latest_href = f"episodes/{html.escape(latest['episode_id'])}.html"
        latest_chips = "".join(_render_cast_chip_html(c) for c in latest["cast_used"])
        hero_html = f"""
        <section class="hero-section" aria-label="최신 에피소드" data-enter="2">
          <div class="hero-card">
            <a class="hero-thumb-link" href="{latest_href}" aria-label="최신 화 EP.{latest['episode_number']} {html.escape(latest['title'])} 바로 보기">
              <img src="{html.escape(latest['thumb_image'])}" alt="EP.{latest['episode_number']} {html.escape(latest['title'])} 썸네일" class="hero-thumb" width="800" height="500" loading="eager" decoding="async" fetchpriority="high">
              <span class="thumb-cuts">{latest['cut_count']}컷</span>
            </a>
            <div class="hero-body">
              <div class="meta-row hero-meta-top">
                <span class="hero-kicker">LATEST</span>
                <span class="ep-index">EP.{latest['episode_number']}</span>
                <span class="meta-sep" aria-hidden="true">·</span>
                <span class="post-no">#{html.escape(latest['source_post_no'])}</span>
                <span class="meta-date">{html.escape(latest['date_short'])}</span>
              </div>
              <h2 class="hero-title">
                <a href="{latest_href}">{html.escape(latest['title'])}</a>
              </h2>
              <p class="hero-sub">{html.escape(latest['subtitle'])}</p>
              <div class="chip-row">{latest_chips}</div>
              <div class="hero-actions">
                <a class="btn btn-primary" href="{latest_href}">지금 바로 감상하기 →</a>
                <a class="btn btn-outline" href="{html.escape(latest['source_url'])}" target="_blank" rel="noopener noreferrer">원본 개념글 ↗</a>
              </div>
            </div>
          </div>
        </section>
        """
    else:
        hero_html = """
        <section class="empty-hero" data-enter="2">
          <p>아직 등록된 에피소드가 없습니다. <code>sloptoon generate --auto</code>로 첫 화를 생성해 보세요!</p>
        </section>
        """

    filter_buttons = [
        f'<button type="button" class="filter-chip is-active" data-cast="" aria-pressed="true">'
        f'전체 <span class="filter-count">{total_episodes}</span></button>'
    ]
    for c in cast_payload:
        if c.get("portrait"):
            avatar_markup = (
                f'<img class="filter-avatar" src="{html.escape(c["portrait"])}" '
                f'alt="" width="24" height="24" loading="lazy" decoding="async">'
            )
        else:
            avatar_markup = (
                f'<span class="cast-dot" style="background:{html.escape(c["color_hex"])};"></span>'
            )
        filter_buttons.append(
            f'<button type="button" class="filter-chip" data-cast="{html.escape(c["name"])}" aria-pressed="false">'
            f"{avatar_markup}"
            f'<span class="filter-name">{html.escape(c["name"])}</span>'
            f'<span class="filter-count">{c["episode_count"]}</span>'
            f"</button>"
        )

    cards_html_parts = [
        _render_episode_card(ep, root_prefix="", include_filter_attrs=True)
        for ep in newest_first
    ]

    embedded_data = _safe_json_for_script({
        "episodes": site_episodes,
        "cast": cast_payload,
        "rootPrefix": "",
    })

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(page_title)}</title>
{social_meta}
{_render_head_assets("", css_suffix)}
</head>
<body data-page="home">
  <a class="skip-link" href="#main-content">본문으로 바로가기</a>
  {_render_nav('home')}

  <main id="main-content" class="container main-content">
    <section class="masthead" data-enter="1">
      <div class="masthead-main">
        <p class="masthead-eyebrow"><span class="dot-sky" aria-hidden="true"></span>{SITE_TAGLINE}</p>
        <h1 class="masthead-title">{SITE_NAME}</h1>
        <p class="masthead-sub">포에버갤 레전드 개념글을 2~2.5등신 귀염뽀짝 SD 고정 9인 캐스트와 아기 곰·공허방랑자 파트너의 상황극으로 연재하는 순백 웹 아카이브</p>
      </div>
      <div class="masthead-stats" aria-label="아카이브 지표">
        <span class="stat-item">총 <strong>{total_episodes}</strong>화 아카이브</span>
        <span class="stat-item">2~2.5등신 귀염뽀짝 SD</span>
        <span class="stat-item">고정 9인 · 펫 2종</span>
      </div>
    </section>

    {hero_html}

    <section class="archive-section" aria-label="전체 에피소드 목록">
      <div class="section-head">
        <div>
          <h2 class="section-title">전체 에피소드</h2>
          <p class="section-meta" id="resultCount">총 {total_episodes}개의 에피소드</p>
        </div>
        <div class="controls-right">
          <div class="search-box">
            <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <input type="search" id="searchInput" class="search-input" placeholder="제목, EP.12, #92059, 캐릭터" aria-label="에피소드 검색" autocomplete="off">
            <kbd class="search-kbd" aria-hidden="true">/</kbd>
          </div>
          <button type="button" id="sortToggle" class="btn btn-outline" data-order="desc" title="정렬 순서 전환">최신순 ↓</button>
        </div>
      </div>

      <div class="cast-filter-bar" id="castFilterBar" role="group" aria-label="캐릭터별 필터">
        {''.join(filter_buttons)}
      </div>

      <div class="episode-grid" id="episodeGrid">
        {''.join(cards_html_parts)}
      </div>

      <div class="archive-load-more" id="loadMoreWrap" hidden>
        <button type="button" id="loadMoreBtn" class="btn btn-outline">더 보기</button>
        <button type="button" id="showAllBtn" class="btn btn-outline">전체 펼치기</button>
      </div>

      <div class="empty-filter" id="emptyFilter" hidden>
        <p class="empty-filter-title">조건에 맞는 에피소드가 아직 없어요.</p>
        <p class="empty-filter-sub">다른 검색어나 캐릭터를 선택해 보세요.</p>
        <button type="button" id="resetFiltersBtn" class="btn btn-outline">필터 초기화</button>
      </div>
    </section>

    <aside class="slop-sponsor-slot" data-slot="home-feed-bottom" aria-label="스폰서 영역"></aside>
  </main>

  {_render_footer(total_episodes)}

  <script>window.__SLOPTOON_DATA__ = {embedded_data};</script>
  <script src="assets/app.js{js_suffix}"></script>
</body>
</html>
"""


def _render_episode_reader_html(
    site_episodes: list[dict[str, Any]],
    default_episode: dict[str, Any] | None,
    root_prefix: str = "",
    pinned_episode_id: str | None = None,
    *,
    base_url: str = DEFAULT_ARCHIVE_BASE_URL,
    fallback_og_image: str = "",
    css_suffix: str = "",
    js_suffix: str = "",
) -> str:
    """Render `episode.html` (dynamic `?id=...`) or a static `episodes/<id>.html` page."""
    ep = default_episode
    total_episodes = len(site_episodes)
    if pinned_episode_id:
        embedded_episodes = [
            item
            if item["episode_id"] == pinned_episode_id
            else {k: v for k, v in item.items() if k != "page_images"}
            for item in site_episodes
        ]
    else:
        embedded_episodes = site_episodes

    embedded_data = _safe_json_for_script({
        "episodes": embedded_episodes,
        "rootPrefix": root_prefix,
        "pinnedEpisodeId": pinned_episode_id or "",
        "archiveBaseUrl": base_url or DEFAULT_ARCHIVE_BASE_URL,
    })

    page_title = (
        f"EP.{ep['episode_number']} {ep['title']} — {SITE_NAME}"
        if ep
        else f"에피소드 리더 — {SITE_NAME}"
    )
    og_desc = ep["subtitle"] if ep else "와우 포에버 슬롭툰 웹툰 뷰어"
    og_img_rel = (ep["thumb_image"] if ep else fallback_og_image).split("?", 1)[0]
    if pinned_episode_id and ep:
        path_from_root = f"episodes/{ep['episode_id']}.html"
        relative_url = f"{ep['episode_id']}.html"
    elif ep:
        path_from_root = f"episodes/{ep['episode_id']}.html"
        relative_url = "episode.html"
    else:
        path_from_root = "episode.html"
        relative_url = "episode.html"

    social_meta = _render_social_meta(
        title=page_title,
        description=og_desc,
        og_type="article",
        path_from_root=path_from_root,
        relative_url=relative_url,
        image_rel_from_root=og_img_rel,
        base_url=base_url,
        root_prefix=root_prefix,
    )

    if ep:
        idx = next((i for i, item in enumerate(site_episodes) if item["episode_id"] == ep["episode_id"]), 0)
        prev_ep = site_episodes[idx - 1] if idx > 0 else None
        next_ep = site_episodes[idx + 1] if idx + 1 < len(site_episodes) else None
        recommended = _select_recommended_episodes(site_episodes, ep["episode_id"], limit=3)
        cast_chips = "".join(_render_cast_chip_html(c, root_prefix=root_prefix) for c in ep["cast_used"])
        total_pages = len(ep["page_images"])
        pages_imgs_html = "".join(
            f'<figure class="reader-page-item">'
            f'<figcaption class="reader-page-label">PAGE {pi:02d} / {total_pages:02d}</figcaption>'
            f'<img src="{root_prefix}{html.escape(p)}" alt="EP.{ep["episode_number"]} 페이지 {pi}" class="reader-page-img" loading="lazy" decoding="async">'
            f"</figure>"
            for pi, p in enumerate(ep["page_images"], start=1)
        )
        canonical_url = html.escape(ep["canonical_url"])

        prev_link_html = (
            f'<a class="nav-ep-card" href="{root_prefix}episodes/{html.escape(prev_ep["episode_id"])}.html">'
            f'<div class="nav-ep-thumb-wrap">'
            f'<img src="{root_prefix}{html.escape(prev_ep["thumb_image"])}" alt="EP.{prev_ep["episode_number"]} {html.escape(prev_ep["title"])}" class="nav-ep-thumb" width="800" height="500" loading="lazy" decoding="async">'
            f"</div>"
            f'<div class="nav-ep-info">'
            f'<span class="nav-ep-dir"><kbd class="key-hint" aria-hidden="true">←</kbd> 이전 화 정주행</span>'
            f'<strong class="nav-ep-title">EP.{prev_ep["episode_number"]} {html.escape(prev_ep["title"])}</strong>'
            f'<span class="nav-ep-sub">{html.escape(prev_ep["subtitle"])}</span>'
            f"</div>"
            f"</a>"
            if prev_ep
            else '<div class="nav-ep-card is-disabled"><div class="nav-ep-info"><span class="nav-ep-dir">← 이전 화</span><span class="nav-ep-title">첫 번째 에피소드입니다</span><span class="nav-ep-sub">지금 1화부터 정주행 중입니다.</span></div></div>'
        )
        next_link_html = (
            f'<a class="nav-ep-card nav-ep-next" href="{root_prefix}episodes/{html.escape(next_ep["episode_id"])}.html">'
            f'<div class="nav-ep-info">'
            f'<span class="nav-ep-dir nav-ep-dir-accent">다음 화 바로 보기 <kbd class="key-hint" aria-hidden="true">→</kbd></span>'
            f'<strong class="nav-ep-title">EP.{next_ep["episode_number"]} {html.escape(next_ep["title"])}</strong>'
            f'<span class="nav-ep-sub">{html.escape(next_ep["subtitle"])}</span>'
            f"</div>"
            f'<div class="nav-ep-thumb-wrap">'
            f'<img src="{root_prefix}{html.escape(next_ep["thumb_image"])}" alt="EP.{next_ep["episode_number"]} {html.escape(next_ep["title"])}" class="nav-ep-thumb" width="800" height="500" loading="lazy" decoding="async">'
            f"</div>"
            f"</a>"
            if next_ep
            else '<div class="nav-ep-card nav-ep-next is-disabled"><div class="nav-ep-info"><span class="nav-ep-dir">다음 화 →</span><span class="nav-ep-title">가장 최신 에피소드입니다</span><span class="nav-ep-sub">랜덤 화 보기로 다른 명장면도 감상해 보세요.</span></div></div>'
        )

        rec_cards_html = "".join(
            _render_episode_card(rec, root_prefix=root_prefix, include_filter_attrs=False)
            for rec in recommended
        )
        rec_hidden_attr = "" if recommended else " hidden"

        jump_select_html = ""
        if len(site_episodes) > 1:
            jump_options = "".join(
                f'<option value="{html.escape(item["episode_id"])}"'
                f'{" selected" if item["episode_id"] == ep["episode_id"] else ""}>'
                f'EP.{item["episode_number"]} {html.escape(item["title"][:32])}'
                f'{"…" if len(item["title"]) > 32 else ""}</option>'
                for item in reversed(site_episodes)
            )
            jump_select_html = (
                f'<select id="epJumpSelect" class="ep-jump-select" aria-label="에피소드 바로가기">'
                f"{jump_options}</select>"
            )

        reader_initial_html = f"""
        <div class="reader-top-bar">
          <a class="back-link" href="{root_prefix}index.html">← 전체 목록</a>
          <div class="reader-mode-toggle" role="group" aria-label="보기 방식">
            <button type="button" class="mode-btn is-active" data-mode="full" aria-pressed="true">통합 스크롤</button>
            <button type="button" class="mode-btn" data-mode="pages" aria-pressed="false">페이지별 보기</button>
          </div>
          <div class="reader-top-actions">
            {jump_select_html}
            <button type="button" class="btn btn-outline btn-sm js-share-url" data-share-url="{canonical_url}">🔗 링크 복사</button>
          </div>
        </div>

        <header class="episode-header" data-enter="1">
          <div class="meta-row">
            <span class="ep-index" id="epBadge">EP.{ep['episode_number']} · #{html.escape(ep['source_post_no'])}</span>
            <span class="meta-sep" aria-hidden="true">·</span>
            <span class="meta-date" id="epDate">{html.escape(ep['date_short'])}</span>
            <span class="meta-sep" aria-hidden="true">·</span>
            <span class="meta-cuts" id="epCuts">{ep['cut_count']}컷 상황극</span>
          </div>
          <h1 class="episode-title" id="epTitle">{html.escape(ep['title'])}</h1>
          <p class="episode-sub" id="epSub">{html.escape(ep['subtitle'])}</p>
          <div class="episode-header-foot">
            <div class="chip-row" id="epCastRow">{cast_chips}</div>
            <a id="epSourceLink" class="source-link" href="{html.escape(ep['source_url'])}" target="_blank" rel="noopener noreferrer">
              원본 포에버갤 개념글 (#{html.escape(ep['source_post_no'])}) ↗
            </a>
          </div>
        </header>

        <section class="comic-stage" aria-label="웹툰 본문">
          <div id="readerFullView" class="reader-full-view">
            <img id="epFullImg" src="{root_prefix}{html.escape(ep['full_image'])}" alt="와우 포에버 슬롭툰 EP.{ep['episode_number']} {html.escape(ep['title'])} 통합본" class="reader-full-img" loading="eager" decoding="async" fetchpriority="high">
          </div>
          <div id="readerPagesView" class="reader-pages-view" hidden>
            {pages_imgs_html}
          </div>
        </section>

        <aside class="slop-sponsor-slot" data-slot="episode-strip-bottom" aria-label="스폰서 영역"></aside>

        <section class="episode-action-strip" aria-label="공유 및 다음 정주행">
          <div class="action-strip-copy">
            <strong>이 념글 상황극, 재밌게 보셨나요?</strong>
            <span>링크를 복사해 공유하거나 랜덤 화로 바로 이어서 정주행해 보세요.</span>
          </div>
          <div class="action-strip-btns">
            <button type="button" id="shareCopyBtn" class="btn btn-outline btn-sm js-share-url" data-share-url="{canonical_url}">🔗 링크 복사</button>
            <button type="button" id="bottomRandomBtn" class="btn btn-primary btn-sm js-random-ep">🎲 랜덤 화 보기</button>
            <a id="epBottomSourceLink" class="btn btn-outline btn-sm" href="{html.escape(ep['source_url'])}" target="_blank" rel="noopener noreferrer">원본 개념글 ↗</a>
          </div>
        </section>

        <nav class="episode-pager" id="epPager" aria-label="이전화 다음화 이동">
          {prev_link_html}
          {next_link_html}
        </nav>

        <section class="recommend-section" id="epRecommendSection" aria-label="다른 레전드 념글 만화"{rec_hidden_attr}>
          <div class="section-head">
            <div>
              <h2 class="section-title">다른 레전드 념글 만화</h2>
              <p class="section-meta">놓치면 아까운 포에버갤 개념글 상황극을 이어서 정주행해 보세요.</p>
            </div>
            <a class="btn btn-outline btn-sm" href="{root_prefix}index.html">전체 아카이브 →</a>
          </div>
          <div class="recommend-grid" id="epRecommendGrid">
            {rec_cards_html}
          </div>
        </section>
        """
    else:
        reader_initial_html = f"""
        <section class="empty-hero">
          <p>표시할 에피소드가 없습니다.</p>
          <a class="btn btn-primary" href="{root_prefix}index.html">목록으로 돌아가기</a>
        </section>
        """

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(page_title)}</title>
{social_meta}
{_render_head_assets(root_prefix, css_suffix)}
</head>
<body data-page="episode">
  <a class="skip-link" href="#main-content">본문으로 바로가기</a>
  <div class="read-progress" aria-hidden="true"><div class="read-progress-bar" id="readProgressBar"></div></div>
  {_render_nav('episode', root_prefix=root_prefix)}

  <main id="main-content" class="container reader-container">
    <div id="episodeRoot">
      {reader_initial_html}
    </div>
  </main>

  {_render_footer(total_episodes, root_prefix=root_prefix)}

  <script>window.__SLOPTOON_DATA__ = {embedded_data};</script>
  <script src="{root_prefix}assets/app.js{js_suffix}"></script>
</body>
</html>
"""


def _render_cast_html(
    cast_payload: list[dict[str, Any]],
    site_episodes: list[dict[str, Any]],
    has_clean_sheet: bool,
    *,
    base_url: str = DEFAULT_ARCHIVE_BASE_URL,
    css_suffix: str = "",
    js_suffix: str = "",
) -> str:
    total_episodes = len(site_episodes)
    page_title = f"SD 9인 캐스트 도감 — {SITE_NAME}"
    page_desc = (
        "와우 포에버 슬롭툰 공식 2~2.5등신 귀염뽀짝 SD 고정 9인 캐스트 및 "
        "고정 동행 펫(아기 곰·공허방랑자) 도감"
    )

    ep_by_cast: dict[str, list[dict[str, Any]]] = {c["name"]: [] for c in cast_payload}
    for ep in reversed(site_episodes):
        for name in ep["cast_used"]:
            ep_by_cast.setdefault(name, []).append(ep)

    horde_count = sum(1 for c in cast_payload if c.get("faction") == "Horde")
    alliance_count = sum(1 for c in cast_payload if c.get("faction") == "Alliance")
    skyborne_count = sum(1 for c in cast_payload if c.get("faction") == "Neutral-Skyborne")

    sheet_src = "assets/cast/cast_sheet_c.jpg" if has_clean_sheet else ""
    og_image_rel = (sheet_src or (site_episodes[-1]["thumb_image"] if site_episodes else "")).split("?", 1)[0]
    social_meta = _render_social_meta(
        title=page_title,
        description=page_desc,
        og_type="website",
        path_from_root="cast.html",
        relative_url="cast.html",
        image_rel_from_root=og_image_rel,
        base_url=base_url,
        root_prefix="",
    )

    sheet_section = (
        f"""
        <section class="cast-sheet-section" aria-label="공식 2.5등신 SD 전체 캐스트 시트" data-enter="2">
          <div class="section-head">
            <div>
              <h2 class="section-title">공식 2.5등신 SD 전체 캐스트 시트</h2>
              <p class="section-meta">이미지를 클릭하면 원본 고해상도로 확대해서 감상할 수 있습니다.</p>
            </div>
          </div>
          <button type="button" class="cast-sheet-frame" id="castSheetBtn" data-lightbox-src="{html.escape(sheet_src)}" aria-label="공식 2.5등신 SD 전체 캐스트 시트 원본 확대">
            <img id="castSheetImg" src="{html.escape(sheet_src)}" alt="와우 포에버 슬롭툰 공식 2.5등신 귀염뽀짝 SD 고정 9인 캐스트 시트" class="cast-sheet-img" loading="eager" decoding="async">
            <span class="cast-sheet-caption">원본 고해상도 확대 보기 ↗</span>
          </button>
        </section>
        """
        if sheet_src
        else ""
    )

    cards_parts: list[str] = []
    for idx, c in enumerate(cast_payload, start=1):
        appearances = ep_by_cast.get(c["name"], [])
        if appearances:
            shown_appearances = appearances[:5]
            ep_links = "".join(
                f'<a class="ep-mini-link" href="episodes/{html.escape(ep["episode_id"])}.html">EP.{ep["episode_number"]} {html.escape(ep["title"])}</a>'
                for ep in shown_appearances
            )
            extra_count = len(appearances) - len(shown_appearances)
            more_badge = (
                f'<span class="cast-ep-more">+ 외 {extra_count}화 더 있음</span>'
                if extra_count > 0
                else ""
            )
            appearances_html = f'<div class="cast-ep-list">{ep_links}{more_badge}</div>'
        else:
            appearances_html = '<p class="cast-ep-empty">곧 새로운 개념글 상황극으로 등판 예정입니다.</p>'

        if c["portrait"]:
            avatar_html = f'<img src="{html.escape(c["portrait"])}" alt="{html.escape(c["name"])} 포트레이트" class="cast-avatar" width="360" height="360" loading="lazy" decoding="async">'
        else:
            avatar_html = (
                f'<div class="cast-avatar-fallback" style="background:{html.escape(c["color_hex"])};">'
                f'{html.escape(c["name"][:2])}</div>'
            )

        alias_tags = "".join(f'<span class="alias-tag">#{html.escape(a)}</span>' for a in c["aliases"])
        faction_label = c.get("faction_label", "")
        faction_suffix = f" · {html.escape(faction_label)}" if faction_label else ""
        turnaround_html = ""
        if c.get("turnaround"):
            t_src = html.escape(c["turnaround"])
            turnaround_html = (
                f'<div class="cast-turnaround-wrap">'
                f'<button type="button" class="cast-turnaround-btn" data-lightbox-src="{t_src}" '
                f'aria-label="{html.escape(c["name"])} 정면·측면·후면 3면 턴어라운드 확대 보기">'
                f'<span class="cast-turnaround-stage">'
                f'<img src="{t_src}" alt="{html.escape(c["name"])} 정면 측면 후면 3면 턴어라운드 도면" '
                f'class="cast-turnaround-img" loading="lazy" decoding="async">'
                f"</span>"
                f'<span class="cast-turnaround-caption">2.5등신 SD 3면 턴어라운드 · 확대 ↗</span>'
                f"</button>"
                f"</div>"
            )

        companion_html = ""
        if c.get("companion_name") and c.get("companion_turnaround"):
            ct_src = html.escape(c["companion_turnaround"])
            c_name = html.escape(c["companion_name"])
            companion_html = (
                f'<div class="cast-turnaround-wrap">'
                f'<button type="button" class="cast-turnaround-btn" data-lightbox-src="{ct_src}" '
                f'aria-label="{html.escape(c["name"])} 고정 동행 펫 {c_name} 3면 턴어라운드 확대 보기">'
                f'<span class="cast-turnaround-stage">'
                f'<img src="{ct_src}" alt="{html.escape(c["name"])} 고정 동행 펫 {c_name} 3면 턴어라운드 도면" '
                f'class="cast-turnaround-img" loading="lazy" decoding="async">'
                f"</span>"
                f'<span class="cast-turnaround-caption">고정 동행 펫 · {c_name} 3면 도면 · 확대 ↗</span>'
                f"</button>"
                f"</div>"
            )

        cards_parts.append(
            f"""
            <article class="cast-card" id="{html.escape(c['id'])}" data-faction="{html.escape(c['faction'])}">
              <div class="cast-card-accent" style="background:{html.escape(c['color_hex'])};"></div>
              <div class="cast-card-top">
                <div class="cast-avatar-wrap">
                  {avatar_html}
                </div>
                <div class="cast-identity">
                  <div class="cast-index-row">
                    <span class="cast-num">0{idx}</span>
                    <span class="cast-race-label">
                      <span class="cast-dot" style="background:{html.escape(c['color_hex'])};"></span>
                      {html.escape(c['race'])} · {html.escape(c['wow_class'])}{faction_suffix}
                    </span>
                  </div>
                  <h3 class="cast-name">{html.escape(c['name'])}</h3>
                  <p class="cast-role">{html.escape(c['role_tag'])}</p>
                </div>
              </div>
              <p class="cast-bio">{html.escape(c['personality'])}</p>
              {turnaround_html}
              {companion_html}
              <div class="alias-row">{alias_tags}</div>
              <div class="cast-card-foot">
                <div class="cast-foot-label">출연 에피소드 ({len(appearances)}화)</div>
                {appearances_html}
                <a class="cast-filter-link" href="index.html?cast={html.escape(c['name'])}">아카이브에서 모아보기 →</a>
              </div>
            </article>
            """
        )

    embedded_data = _safe_json_for_script({
        "episodes": [
            {"episode_id": ep["episode_id"], "episode_number": ep["episode_number"], "title": ep["title"]}
            for ep in site_episodes
        ],
        "rootPrefix": "",
    })

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(page_title)}</title>
{social_meta}
{_render_head_assets("", css_suffix)}
</head>
<body data-page="cast">
  <a class="skip-link" href="#main-content">본문으로 바로가기</a>
  {_render_nav('cast')}

  <main id="main-content" class="container main-content">
    <section class="masthead" data-enter="1">
      <div class="masthead-main">
        <p class="masthead-eyebrow"><span class="dot-sky" aria-hidden="true"></span>2~2.5등신 귀염뽀짝 SD 정본 · 고정 9인 + 동행 펫 2종</p>
        <h1 class="masthead-title">SD 9인 캐스트 도감</h1>
        <p class="masthead-sub">오크·언데드·노움·드워프·트롤·타우렌·나이트엘프·인간·스카이본 — 포에버갤 상황극을 책임지는 2~2.5등신 SD 고정 9인과 동행 펫(아기 곰·공허방랑자)을 소개합니다.</p>
      </div>
      <div class="masthead-stats" aria-label="캐스트 구성">
        <span class="stat-item">고정 <strong>{len(cast_payload)}</strong>인 캐스트</span>
        <span class="stat-item">동행 펫 <strong>2</strong>종</span>
        <span class="stat-item">3면 턴어라운드 정본</span>
      </div>
    </section>

    {sheet_section}

    <section class="cast-grid-section" aria-label="9명 캐릭터 프로필">
      <div class="section-head">
        <div>
          <h2 class="section-title">캐릭터별 프로필 ({len(cast_payload)}명)</h2>
          <p class="section-meta" id="castCountMeta">진영별 필터와 3면 턴어라운드 확대, 출연 화 모아보기를 지원합니다.</p>
        </div>
        <div class="faction-filter-bar" id="castFactionFilter" role="group" aria-label="진영별 필터">
          <button type="button" class="filter-chip is-active" data-faction="" aria-pressed="true">전체 {len(cast_payload)}인</button>
          <button type="button" class="filter-chip" data-faction="Horde" aria-pressed="false">호드 <span class="filter-count">{horde_count}</span></button>
          <button type="button" class="filter-chip" data-faction="Alliance" aria-pressed="false">얼라이언스 <span class="filter-count">{alliance_count}</span></button>
          <button type="button" class="filter-chip" data-faction="Neutral-Skyborne" aria-pressed="false">스카이본 <span class="filter-count">{skyborne_count}</span></button>
        </div>
      </div>
      <div class="cast-grid" id="castGrid">
        {''.join(cards_parts)}
      </div>
    </section>
  </main>

  <div id="lightbox" class="lightbox" hidden aria-modal="true" role="dialog" aria-label="이미지 확대 보기">
    <button type="button" id="lightboxClose" class="lightbox-close" aria-label="닫기">✕</button>
    <figure class="lightbox-figure">
      <img id="lightboxImg" alt="확대 이미지" class="lightbox-img">
      <figcaption id="lightboxCaption" class="lightbox-caption"></figcaption>
    </figure>
  </div>

  {_render_footer(total_episodes)}

  <script>window.__SLOPTOON_DATA__ = {embedded_data};</script>
  <script src="assets/app.js{js_suffix}"></script>
</body>
</html>
"""


_STYLE_CSS = """/* 와우 포에버 슬롭툰 — 순백(#FFFFFF) 에디토리얼 정적 웹 아카이브 */
:root {
  --bg: #ffffff;
  --surface: #f7f8fa;
  --surface-2: #eff2f6;
  --ink: #111318;
  --ink-muted: #4b5262;
  --ink-soft: #636b7c;
  --border: rgba(17, 19, 24, 0.11);
  --border-strong: rgba(17, 19, 24, 0.22);
  --border-hover: rgba(17, 19, 24, 0.28);
  --sky: #0ea5e9;
  --sky-dark: #0284c7;
  --sky-ink: #0369a1;
  --sky-soft: #f0f9ff;
  --sky-border: #bae6fd;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 14px;
  --shadow-hover: 0 12px 28px -10px rgba(17, 19, 24, 0.11), 0 2px 6px -1px rgba(17, 19, 24, 0.05);
  --shadow-float: 0 10px 26px -6px rgba(17, 19, 24, 0.14), 0 2px 8px -2px rgba(17, 19, 24, 0.06);
  --ease-out: cubic-bezier(0.22, 1, 0.36, 1);
  --font-sans: "Pretendard", "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

*, *::before, *::after { box-sizing: border-box; }
html {
  scroll-behavior: smooth;
  background: var(--bg);
  max-width: 100%;
  overflow-x: clip;
  -webkit-text-size-adjust: 100%;
}
body {
  margin: 0;
  max-width: 100%;
  overflow-x: clip;
  background: var(--bg);
  color: var(--ink);
  font-family: var(--font-sans);
  font-size: 16px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}
a { color: inherit; text-decoration: none; }
img { display: block; max-width: 100%; height: auto; }
button, input, select { font-family: inherit; }

:focus-visible {
  outline: 2px solid var(--sky);
  outline-offset: 2px;
}

/* Skip link for keyboard accessibility */
.skip-link {
  position: fixed;
  top: 10px;
  left: 12px;
  z-index: 120;
  padding: 10px 16px;
  border-radius: var(--radius-sm);
  background: var(--ink);
  color: #ffffff;
  font-size: 0.875rem;
  font-weight: 700;
  transform: translateY(-160%);
}
.skip-link:focus-visible {
  transform: translateY(0);
}

/* Quiet entrance animation — hero & masthead first load only */
@keyframes quietEnter {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
[data-enter] {
  animation: quietEnter 420ms var(--ease-out) both;
}
[data-enter="2"] {
  animation-delay: 70ms;
}

/* Equal-edges container */
.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

/* Fixed reading progress bar on episode pages */
.read-progress {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 2.5px;
  z-index: 65;
  pointer-events: none;
  background: transparent;
}
.read-progress-bar {
  width: 0%;
  height: 100%;
  background: var(--sky);
}

/* Opaque pure-white sticky header */
.site-header {
  position: sticky;
  top: 0;
  z-index: 50;
  background: #ffffff;
  border-bottom: 1px solid var(--border);
}
.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 64px;
}
.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-height: 44px;
  min-width: 0;
  max-width: 100%;
  flex-shrink: 0;
}
.brand-mark {
  flex-shrink: 0;
  display: block;
}
.brand-text {
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
  min-width: 0;
}
.brand-name {
  font-size: 1.0625rem;
  font-weight: 800;
  letter-spacing: -0.025em;
  color: var(--ink);
  white-space: nowrap;
}
.brand-tag {
  font-family: var(--font-mono);
  font-size: 0.8125rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  color: var(--ink-soft);
}
.site-nav {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}
.nav-link {
  position: relative;
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  padding: 0 12px;
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--ink-muted);
  border-radius: var(--radius-sm);
  transition: color 150ms ease, background-color 150ms ease;
}
.nav-link:hover {
  color: var(--ink);
  background: var(--surface);
}
.nav-link.is-active {
  color: var(--ink);
  font-weight: 700;
}
.nav-link.is-active::after {
  content: "";
  position: absolute;
  left: 12px;
  right: 12px;
  bottom: 0;
  height: 2px;
  background: var(--sky);
  border-radius: 2px 2px 0 0;
}
.nav-ext {
  color: var(--ink-soft);
}
.nav-pill-random {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 44px;
  padding: 0 14px;
  margin-left: 4px;
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--ink);
  background: #ffffff;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background-color 150ms ease, border-color 150ms ease, color 150ms ease, transform 90ms ease;
}
.nav-pill-random:hover {
  background: var(--sky-soft);
  border-color: var(--sky-border);
  color: var(--sky-ink);
}
.nav-pill-random:active {
  transform: scale(0.985);
}

/* Main layout & compact left-aligned editorial masthead */
.main-content {
  padding-top: 28px;
  padding-bottom: 72px;
}
.masthead {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px 32px;
  padding-bottom: 22px;
  margin-bottom: 28px;
  border-bottom: 1px solid var(--border);
}
.masthead-main {
  flex: 1 1 320px;
  min-width: 0;
  max-width: 100%;
}
.masthead-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 8px;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--ink-soft);
  letter-spacing: -0.01em;
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.dot-sky {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: var(--sky);
  display: inline-block;
  flex-shrink: 0;
}
.masthead-title {
  margin: 0 0 6px;
  font-size: clamp(1.85rem, 3.2vw, 2.55rem);
  font-weight: 850;
  letter-spacing: -0.035em;
  line-height: 1.16;
  color: var(--ink);
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.masthead-sub {
  margin: 0;
  max-width: 680px;
  font-size: 0.9375rem;
  line-height: 1.55;
  color: var(--ink-muted);
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.masthead-stats {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 16px;
  max-width: 100%;
  min-width: 0;
}
.stat-item {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--ink-soft);
  padding-left: 16px;
  border-left: 1px solid var(--border);
  white-space: nowrap;
}
.stat-item:first-child {
  padding-left: 0;
  border-left: 0;
}
.stat-item strong {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  color: var(--ink);
}

/* Shared editorial metadata & unified buttons */
.meta-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 8px;
  min-width: 0;
}
.ep-index {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--ink);
  letter-spacing: -0.01em;
}
.meta-sep {
  color: var(--border-strong);
  font-size: 0.8125rem;
}
.post-no, .meta-date, .meta-cuts {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--ink-soft);
}
.ep-read-mark {
  margin-left: auto;
  font-family: var(--font-mono);
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--sky-ink);
  background: var(--sky-soft);
  border: 1px solid var(--sky-border);
  border-radius: 5px;
  padding: 1px 7px;
  line-height: 1.4;
}
.ep-read-mark[hidden] { display: none; }

/* Unified 2-variant button system: Solid Primary + Clean Outline Secondary */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-height: 44px;
  padding: 0 18px;
  border-radius: var(--radius-sm);
  font-size: 0.9375rem;
  font-weight: 700;
  line-height: 1.2;
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 150ms ease, border-color 150ms ease, color 150ms ease, transform 90ms ease;
}
.btn:active {
  transform: scale(0.985);
}
.btn-primary {
  background: var(--ink);
  color: #ffffff;
  border: 1px solid var(--ink);
}
.btn-primary:hover {
  background: #232833;
  border-color: #232833;
}
.btn-outline {
  background: #ffffff;
  color: var(--ink);
  border: 1px solid var(--border-strong);
}
.btn-outline:hover {
  background: var(--surface);
  border-color: var(--ink);
}
.btn-sm {
  min-height: 44px;
  padding: 0 14px;
  font-size: 0.875rem;
}

/* Collapsible sponsor slot — zero height & invisible when empty */
.slop-sponsor-slot {
  width: 100%;
  max-width: 960px;
  margin: 28px auto;
  padding: 16px;
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  text-align: center;
}
.slop-sponsor-slot:empty {
  display: none;
  margin: 0;
  padding: 0;
  border: 0;
}

/* Featured latest hero — balanced 2-column showcase fitting above 1440x900 fold */
.hero-section {
  margin-bottom: 48px;
}
.hero-card {
  display: grid;
  grid-template-columns: minmax(0, 1.18fr) minmax(0, 1fr);
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: border-color 180ms ease, box-shadow 180ms var(--ease-out);
}
.hero-card:hover {
  border-color: var(--border-hover);
  box-shadow: var(--shadow-hover);
}
.hero-thumb-link {
  position: relative;
  display: block;
  aspect-ratio: 16 / 10;
  background: #ffffff;
  border-right: 1px solid var(--border);
  overflow: hidden;
}
.hero-thumb {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #ffffff;
  transition: transform 500ms var(--ease-out);
}
.hero-thumb-link:hover .hero-thumb {
  transform: scale(1.025);
}
.thumb-cuts {
  position: absolute;
  bottom: 12px;
  right: 12px;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--ink-muted);
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 2px 9px;
  line-height: 1.45;
}
.hero-body {
  padding: 32px 34px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 14px;
  min-width: 0;
}
.hero-kicker {
  font-family: var(--font-mono);
  font-size: 0.8125rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  color: var(--sky-ink);
  background: var(--sky-soft);
  border: 1px solid var(--sky-border);
  border-radius: 5px;
  padding: 1px 8px;
}
.hero-title {
  margin: 0;
  font-size: clamp(1.5rem, 2.3vw, 2.05rem);
  font-weight: 850;
  letter-spacing: -0.03em;
  line-height: 1.24;
  color: var(--ink);
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.hero-title a {
  background-image: linear-gradient(currentColor, currentColor);
  background-position: 0% 100%;
  background-repeat: no-repeat;
  background-size: 0% 2px;
  transition: background-size 220ms var(--ease-out);
}
.hero-title a:hover {
  background-size: 100% 2px;
}
.hero-sub {
  margin: 0;
  color: var(--ink-muted);
  font-size: 1rem;
  line-height: 1.55;
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 6px;
}

/* Cast chips */
.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.cast-chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 36px;
  padding: 4px 12px;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--ink-muted);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  transition: border-color 150ms ease, color 150ms ease, background-color 150ms ease;
}
.cast-chip:hover {
  border-color: var(--border-hover);
  color: var(--ink);
  background: #ffffff;
}
.cast-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  display: inline-block;
  flex-shrink: 0;
}

/* Section header, search & sort controls */
.section-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 18px;
}
.section-title {
  margin: 0;
  font-size: 1.375rem;
  font-weight: 800;
  letter-spacing: -0.025em;
  line-height: 1.25;
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.section-meta {
  margin: 4px 0 0;
  font-size: 0.875rem;
  color: var(--ink-soft);
  font-variant-numeric: tabular-nums;
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.controls-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  max-width: 100%;
  min-width: 0;
}
.search-box {
  position: relative;
  max-width: 100%;
  min-width: 0;
}
.search-icon {
  position: absolute;
  left: 13px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--ink-soft);
  pointer-events: none;
}
.search-input {
  width: 320px;
  max-width: 100%;
  min-height: 44px;
  padding: 0 38px 0 38px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  font-size: 0.9375rem;
  background: #ffffff;
  color: var(--ink);
  transition: border-color 150ms ease;
}
.search-input::placeholder {
  color: var(--ink-soft);
}
.search-input:hover {
  border-color: var(--border-hover);
}
.search-input:focus {
  border-color: var(--sky);
}
.search-kbd {
  position: absolute;
  right: 11px;
  top: 50%;
  transform: translateY(-50%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 5px;
  font-family: var(--font-mono);
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--ink-soft);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 5px;
  pointer-events: none;
}
.search-box:focus-within .search-kbd {
  opacity: 0;
}

/* Character avatar filter bar & faction filter bar */
.cast-filter-bar, .faction-filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 24px;
}
.faction-filter-bar {
  margin-bottom: 0;
}
.filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 44px;
  padding: 5px 13px;
  background: #ffffff;
  color: var(--ink-muted);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 150ms ease, background-color 150ms ease, color 150ms ease, transform 90ms ease;
}
.filter-chip:hover {
  border-color: var(--border-hover);
  color: var(--ink);
  background: var(--surface);
}
.filter-chip:active {
  transform: scale(0.985);
}
.filter-chip.is-active {
  background: var(--ink);
  border-color: var(--ink);
  color: #ffffff;
}
.filter-avatar {
  width: 24px;
  height: 24px;
  border-radius: 999px;
  object-fit: cover;
  object-position: 50% 15%;
  background: #ffffff;
  border: 1px solid var(--border);
  flex-shrink: 0;
}
.filter-chip.is-active .filter-avatar {
  border-color: rgba(255, 255, 255, 0.65);
}
.filter-count {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 0.8125rem;
  font-weight: 500;
  opacity: 0.72;
}

/* Episode card grid */
.episode-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(310px, 100%), 1fr));
  gap: 24px;
}
.ep-card {
  min-width: 0;
  max-width: 100%;
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
  transition: transform 180ms var(--ease-out), box-shadow 180ms var(--ease-out), border-color 180ms ease;
}
.ep-card:hover {
  transform: translateY(-2px);
  border-color: var(--border-hover);
  box-shadow: var(--shadow-hover);
}
.ep-card-link {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.ep-thumb-wrap {
  position: relative;
  aspect-ratio: 16 / 10;
  background: #ffffff;
  border-bottom: 1px solid var(--border);
  overflow: hidden;
}
.ep-thumb {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #ffffff;
  transition: transform 500ms var(--ease-out), opacity 180ms ease;
}
.ep-card.is-read .ep-thumb {
  opacity: 0.92;
}
.ep-card:hover .ep-thumb {
  transform: scale(1.025);
  opacity: 1;
}
.ep-card-body {
  padding: 16px 18px 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  min-width: 0;
}
.ep-card-title {
  margin: 2px 0 0;
  font-size: 1.0625rem;
  font-weight: 750;
  letter-spacing: -0.02em;
  line-height: 1.38;
  color: var(--ink);
  word-break: keep-all;
  overflow-wrap: anywhere;
  text-decoration: underline;
  text-decoration-color: transparent;
  text-underline-offset: 4px;
  transition: text-decoration-color 180ms ease;
}
.ep-card:hover .ep-card-title {
  text-decoration-color: var(--ink);
}
.ep-card-sub {
  margin: 0;
  font-size: 0.9375rem;
  line-height: 1.5;
  color: var(--ink-muted);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.mini-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: auto;
  padding-top: 8px;
}
.mini-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--ink-muted);
  background: var(--surface);
  border-radius: 6px;
  padding: 2px 8px;
}

.empty-filter, .empty-hero {
  text-align: center;
  padding: 52px 24px;
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius-md);
  background: var(--surface);
}
.empty-filter-title {
  margin: 0 0 6px;
  font-weight: 750;
  font-size: 1.0625rem;
}
.empty-filter-sub {
  margin: 0 0 18px;
  color: var(--ink-muted);
  font-size: 0.9375rem;
}

.archive-load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 32px;
}
.archive-load-more[hidden] { display: none; }

/* Back to top floating button */
.back-to-top {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 60;
  min-height: 44px;
  padding: 0 16px;
  background: #ffffff;
  color: var(--ink);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: var(--shadow-float);
  transition: transform 150ms var(--ease-out), border-color 150ms ease, background-color 150ms ease;
}
.back-to-top:hover {
  background: var(--surface);
  border-color: var(--ink);
  transform: translateY(-2px);
}
.back-to-top:active {
  transform: scale(0.985);
}
.back-to-top[hidden] { display: none; }

/* ---------------- EPISODE READER PAGE ---------------- */
.reader-container {
  max-width: 960px;
  padding-top: 20px;
  padding-bottom: 72px;
}
.reader-top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px 14px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}
.back-link {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  padding: 0 4px;
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--ink-muted);
  transition: color 150ms ease;
}
.back-link:hover {
  color: var(--ink);
}
.reader-mode-toggle {
  display: inline-flex;
  align-items: center;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 3px;
  gap: 3px;
}
.mode-btn {
  min-height: 44px;
  padding: 0 14px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: var(--ink-muted);
  font-size: 0.875rem;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 150ms ease, color 150ms ease, box-shadow 150ms ease;
}
.mode-btn:hover {
  color: var(--ink);
}
.mode-btn.is-active {
  background: #ffffff;
  color: var(--ink);
  box-shadow: 0 1px 3px rgba(17, 19, 24, 0.10);
}
.reader-top-actions {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  max-width: 100%;
  min-width: 0;
}
.ep-jump-select {
  max-width: 240px;
  min-width: 0;
  min-height: 44px;
  padding: 0 12px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  background: #ffffff;
  color: var(--ink);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 150ms ease;
}
.ep-jump-select:hover {
  border-color: var(--ink);
}

.episode-header {
  padding: 28px 0 24px;
  border-bottom: 1px solid var(--border);
}
.episode-title {
  margin: 10px 0 8px;
  font-size: clamp(1.6rem, 3.4vw, 2.3rem);
  font-weight: 850;
  letter-spacing: -0.03em;
  line-height: 1.24;
  color: var(--ink);
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.episode-sub {
  margin: 0 0 18px;
  color: var(--ink-muted);
  font-size: 1rem;
  line-height: 1.55;
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.episode-header-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px 16px;
}
.source-link {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  padding: 0 12px;
  max-width: 100%;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--sky-ink);
  background: var(--sky-soft);
  border: 1px solid var(--sky-border);
  border-radius: var(--radius-sm);
  line-height: 1.4;
  word-break: keep-all;
  overflow-wrap: anywhere;
  transition: background-color 150ms ease, border-color 150ms ease;
}
.source-link:hover {
  background: #e0f2fe;
  border-color: var(--sky);
}

/* Borderless pure-white comic stage */
.comic-stage {
  background: #ffffff;
  margin: 24px auto 36px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.reader-full-view, .reader-pages-view {
  width: 100%;
  max-width: 900px;
  background: #ffffff;
}
.reader-full-img, .reader-page-img {
  width: 100%;
  height: auto;
  margin: 0 auto;
  background: #ffffff;
}
.reader-pages-view {
  display: flex;
  flex-direction: column;
  gap: 32px;
}
.reader-pages-view[hidden], .reader-full-view[hidden] {
  display: none;
}
.reader-page-item {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.reader-page-label {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 0.8125rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  color: var(--ink-soft);
}
.reader-page-img {
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
}

/* Post-comic Share & Random Strip */
.episode-action-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  padding: 20px 24px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  margin-bottom: 24px;
}
.action-strip-copy {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}
.action-strip-copy strong {
  font-size: 1rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--ink);
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.action-strip-copy span {
  font-size: 0.875rem;
  color: var(--ink-muted);
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.action-strip-btns {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  max-width: 100%;
}

/* Prev / Next Episode Pager */
.episode-pager {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 48px;
}
.nav-ep-card {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  padding: 14px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: #ffffff;
  transition: transform 180ms var(--ease-out), box-shadow 180ms var(--ease-out), border-color 180ms ease;
}
.nav-ep-card:not(.is-disabled):hover {
  transform: translateY(-2px);
  border-color: var(--border-hover);
  box-shadow: var(--shadow-hover);
}
.nav-ep-card.is-disabled {
  background: var(--surface);
  color: var(--ink-soft);
}
.nav-ep-next {
  justify-content: flex-end;
  text-align: right;
}
.nav-ep-thumb-wrap {
  width: 108px;
  height: 68px;
  flex-shrink: 0;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
  background: #ffffff;
}
.nav-ep-thumb {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #ffffff;
  transition: transform 500ms var(--ease-out);
}
.nav-ep-card:not(.is-disabled):hover .nav-ep-thumb {
  transform: scale(1.03);
}
.nav-ep-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
  max-width: 100%;
  flex: 1;
  overflow: hidden;
}
.nav-ep-dir {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--ink-soft);
}
.nav-ep-next .nav-ep-dir {
  justify-content: flex-end;
}
.nav-ep-dir-accent {
  color: var(--sky-dark);
}
.key-hint {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 5px;
  font-family: var(--font-mono);
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--ink-soft);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 4px;
}
.nav-ep-title {
  font-size: 0.9375rem;
  font-weight: 750;
  line-height: 1.32;
  color: var(--ink);
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.nav-ep-card.is-disabled .nav-ep-title {
  color: var(--ink-muted);
}
.nav-ep-sub {
  display: block;
  max-width: 100%;
  font-size: 0.8125rem;
  color: var(--ink-soft);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Recommended Episodes Grid */
.recommend-section {
  margin-bottom: 42px;
}
.recommend-section[hidden] { display: none; }
.recommend-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(260px, 100%), 1fr));
  gap: 20px;
}

/* ---------------- CAST PAGE ---------------- */
.cast-sheet-section {
  margin-bottom: 52px;
}
.cast-sheet-frame {
  display: block;
  width: 100%;
  padding: 0;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: #ffffff;
  cursor: zoom-in;
  text-align: left;
  transition: border-color 180ms ease, box-shadow 180ms var(--ease-out);
}
.cast-sheet-frame:hover {
  border-color: var(--border-hover);
  box-shadow: var(--shadow-hover);
}
.cast-sheet-img {
  width: 100%;
  height: auto;
  background: #ffffff;
  transition: transform 500ms var(--ease-out);
}
.cast-sheet-frame:hover .cast-sheet-img {
  transform: scale(1.015);
}
.cast-sheet-caption {
  display: block;
  padding: 12px 18px;
  border-top: 1px solid var(--border);
  background: var(--surface);
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--ink-muted);
  text-align: right;
}

.cast-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(310px, 100%), 1fr));
  gap: 24px;
}
.cast-card {
  min-width: 0;
  max-width: 100%;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: #ffffff;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: transform 180ms var(--ease-out), box-shadow 180ms var(--ease-out), border-color 180ms ease;
}
.cast-card:hover {
  transform: translateY(-2px);
  border-color: var(--border-hover);
  box-shadow: var(--shadow-hover);
}
.cast-card[hidden] { display: none; }
.cast-card-accent {
  height: 3px;
  width: 100%;
}
.cast-card-top {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 20px 12px;
}
.cast-avatar-wrap {
  width: 104px;
  height: 104px;
  flex-shrink: 0;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: #ffffff;
}
.cast-avatar {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #ffffff;
}
.cast-avatar-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-weight: 800;
  font-size: 1.4rem;
}
.cast-identity {
  min-width: 0;
  flex: 1;
}
.cast-index-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 8px;
}
.cast-num {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--ink-soft);
}
.cast-race-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--ink-muted);
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.cast-name {
  margin: 6px 0 2px;
  font-size: 1.2rem;
  font-weight: 800;
  letter-spacing: -0.025em;
  line-height: 1.25;
  color: var(--ink);
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.cast-role {
  margin: 0;
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--sky-ink);
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.cast-bio {
  margin: 0;
  padding: 4px 20px 14px;
  font-size: 0.9375rem;
  line-height: 1.55;
  color: var(--ink-muted);
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.cast-turnaround-wrap {
  padding: 0 20px 12px;
}
.cast-turnaround-btn {
  display: block;
  width: 100%;
  padding: 8px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: #ffffff;
  cursor: zoom-in;
  text-align: center;
  transition: border-color 150ms ease, background-color 150ms ease;
}
.cast-turnaround-btn:hover {
  border-color: var(--border-hover);
  background: var(--surface);
}
.cast-turnaround-stage {
  display: block;
  overflow: hidden;
  border-radius: 6px;
  background: #ffffff;
}
.cast-turnaround-img {
  display: block;
  width: 100%;
  height: auto;
  background: #ffffff;
  transition: transform 500ms var(--ease-out);
}
.cast-turnaround-btn:hover .cast-turnaround-img {
  transform: scale(1.025);
}
.cast-turnaround-caption {
  display: block;
  margin-top: 7px;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--ink-soft);
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.alias-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 0 20px 16px;
}
.alias-tag {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--ink-soft);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 2px 8px;
}
.cast-card-foot {
  margin-top: auto;
  padding: 14px 20px 16px;
  border-top: 1px solid var(--border);
  background: var(--surface);
  min-width: 0;
  max-width: 100%;
}
.cast-foot-label {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--ink-soft);
  margin-bottom: 8px;
}
.cast-ep-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 10px;
  min-width: 0;
  max-width: 100%;
}
.ep-mini-link {
  display: block;
  max-width: 100%;
  padding: 3px 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ep-mini-link:hover {
  color: var(--sky-dark);
  text-decoration: underline;
  text-underline-offset: 3px;
}
.cast-ep-more {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--ink-soft);
  padding-top: 2px;
}
.cast-ep-empty {
  margin: 0 0 8px;
  font-size: 0.875rem;
  color: var(--ink-soft);
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.cast-filter-link {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--sky-dark);
}
.cast-filter-link:hover {
  text-decoration: underline;
  text-underline-offset: 4px;
}

/* Lightbox modal */
.lightbox {
  position: fixed;
  inset: 0;
  z-index: 90;
  background: rgba(17, 19, 24, 0.88);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.lightbox[hidden] { display: none; }
.lightbox-figure {
  margin: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  max-width: 96vw;
  max-height: 92vh;
}
.lightbox-img {
  max-width: 96vw;
  max-height: 84vh;
  border-radius: var(--radius-md);
  background: #ffffff;
  box-shadow: 0 20px 48px rgba(0, 0, 0, 0.35);
}
.lightbox-caption {
  font-size: 0.875rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  text-align: center;
  word-break: keep-all;
}
.lightbox-close {
  position: fixed;
  top: 18px;
  right: 22px;
  width: 44px;
  height: 44px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: #ffffff;
  color: var(--ink);
  font-size: 1.1rem;
  font-weight: 800;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: transform 90ms ease, background-color 150ms ease;
}
.lightbox-close:hover {
  background: var(--surface-2);
}
.lightbox-close:active {
  transform: scale(0.95);
}

/* Editorial Pure-White Footer, Legal Notice & Toast */
.site-footer {
  border-top: 1px solid var(--border);
  background: #ffffff;
  padding: 38px 0 42px;
}
.footer-inner {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 20px 32px;
}
.footer-brand {
  min-width: 0;
  max-width: 600px;
}
.footer-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--ink);
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.footer-desc {
  margin: 8px 0 0;
  font-size: 0.875rem;
  line-height: 1.6;
  color: var(--ink-muted);
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.footer-links {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 18px;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--ink-muted);
}
.footer-links a {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  transition: color 150ms ease;
}
.footer-links a:hover {
  color: var(--ink);
}
.footer-legal {
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid var(--border);
}
.legal-notice {
  margin: 0;
  font-size: 0.8125rem;
  line-height: 1.65;
  color: var(--ink-soft);
  word-break: keep-all;
  overflow-wrap: anywhere;
}

.toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  background: var(--ink);
  color: #ffffff;
  font-size: 0.875rem;
  font-weight: 600;
  padding: 12px 20px;
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-float);
  max-width: calc(100vw - 32px);
  text-align: center;
  overflow-wrap: anywhere;
}

/* ---------------- RESPONSIVE BREAKPOINTS ---------------- */
@media (max-width: 820px) {
  .header-inner {
    flex-wrap: wrap;
    padding-top: 8px;
    padding-bottom: 8px;
    gap: 6px 14px;
  }
  .brand-tag { display: none; }
  .masthead {
    align-items: flex-start;
    gap: 14px;
  }
  .masthead-main {
    flex: 1 1 100%;
  }
  .masthead-stats {
    width: 100%;
    gap: 6px 14px;
  }
  .hero-card {
    grid-template-columns: minmax(0, 1fr);
  }
  .hero-thumb-link {
    border-right: 0;
    border-bottom: 1px solid var(--border);
  }
  .hero-body {
    padding: 22px 24px;
  }
  .episode-pager { grid-template-columns: minmax(0, 1fr); }
  .nav-ep-next {
    text-align: left;
    flex-direction: row-reverse;
    justify-content: flex-start;
  }
  .nav-ep-next .nav-ep-dir {
    justify-content: flex-start;
  }
  .nav-ep-thumb-wrap {
    width: 92px;
    height: 58px;
  }
  .key-hint, .search-kbd { display: none; }
  .search-input {
    width: 100%;
    padding-right: 14px;
  }
  .ep-jump-select {
    max-width: 190px;
  }
  .back-to-top {
    right: 16px;
    bottom: 16px;
  }
}

@media (max-width: 640px) {
  .container { padding: 0 16px; }
  .main-content {
    padding-top: 20px;
    padding-bottom: 56px;
  }
  .header-inner {
    min-height: 44px;
    padding-top: 4px;
    padding-bottom: 4px;
    gap: 2px 10px;
  }
  .brand {
    min-height: 36px;
  }
  .site-nav {
    width: 100%;
    flex-wrap: nowrap;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
    gap: 8px;
    padding-bottom: 2px;
  }
  .site-nav::-webkit-scrollbar { display: none; }
  .site-nav > * {
    flex-shrink: 0;
    white-space: nowrap;
  }
  .nav-link {
    padding: 0 10px;
    font-size: 0.875rem;
  }
  .nav-link.is-active::after {
    left: 10px;
    right: 10px;
  }
  .nav-pill-random {
    margin-left: 0;
    padding: 0 12px;
    font-size: 0.8125rem;
  }
  .masthead {
    padding-bottom: 18px;
    margin-bottom: 22px;
  }
  .masthead-title {
    font-size: clamp(1.65rem, 7.2vw, 2.15rem);
  }
  .masthead-stats {
    gap: 4px 12px;
  }
  .stat-item {
    padding-left: 0;
    border-left: 0;
    white-space: normal;
    word-break: keep-all;
    overflow-wrap: anywhere;
  }
  .hero-section { margin-bottom: 36px; }
  .hero-body {
    padding: 18px;
    gap: 12px;
  }
  .hero-title { font-size: 1.375rem; }
  .hero-sub { font-size: 0.9375rem; }
  .hero-actions .btn { flex: 1 1 140px; }
  .section-head {
    gap: 12px;
    margin-bottom: 16px;
  }
  .controls-right {
    width: 100%;
    flex-wrap: nowrap;
  }
  .search-box {
    flex: 1 1 auto;
    min-width: 0;
  }
  .search-input {
    width: 100%;
    font-size: 16px;
    padding: 0 12px 0 36px;
  }
  .controls-right .btn {
    flex-shrink: 0;
    padding: 0 12px;
    font-size: 0.875rem;
  }
  .cast-filter-bar {
    gap: 6px;
    margin-bottom: 18px;
  }
  .filter-chip {
    padding: 4px 11px;
    font-size: 0.8125rem;
  }
  .episode-grid, .cast-grid, .recommend-grid {
    grid-template-columns: minmax(0, 1fr);
    gap: 16px;
  }
  .reader-container {
    padding-top: 14px;
    padding-bottom: 56px;
  }
  .reader-top-bar {
    gap: 8px;
    padding-bottom: 14px;
  }
  .reader-top-actions {
    width: 100%;
    display: flex;
    flex-wrap: nowrap;
  }
  .ep-jump-select {
    flex: 1 1 0;
    min-width: 0;
    max-width: 100%;
    font-size: 16px;
  }
  .reader-top-actions .btn {
    flex-shrink: 0;
  }
  .episode-header {
    padding: 20px 0 18px;
  }
  .episode-title {
    font-size: clamp(1.375rem, 6vw, 1.8rem);
  }
  .episode-action-strip {
    padding: 16px 18px;
  }
  .action-strip-btns {
    width: 100%;
  }
  .action-strip-btns .btn {
    flex: 1 1 120px;
  }
  .episode-pager {
    gap: 12px;
    margin-bottom: 34px;
  }
  .nav-ep-card {
    padding: 12px;
    gap: 12px;
  }
  .nav-ep-thumb-wrap {
    width: 78px;
    height: 50px;
  }
  .cast-card-top {
    padding: 16px 16px 10px;
    gap: 14px;
  }
  .cast-avatar-wrap {
    width: 84px;
    height: 84px;
  }
  .cast-bio { padding: 4px 16px 12px; }
  .cast-turnaround-wrap { padding: 0 16px 12px; }
  .alias-row { padding: 0 16px 14px; }
  .cast-card-foot { padding: 14px 16px 16px; }
}

@media (max-width: 380px) {
  .container { padding: 0 12px; }
  .nav-link {
    font-size: 0.8125rem;
    padding: 0 8px;
  }
  .nav-pill-random {
    font-size: 0.8125rem;
    padding: 0 10px;
  }
  .mode-btn {
    font-size: 0.8125rem;
    padding: 0 10px;
  }
  .controls-right {
    gap: 6px;
  }
  .controls-right .btn {
    padding: 0 10px;
    font-size: 0.8125rem;
  }
  .nav-ep-thumb-wrap {
    width: 66px;
    height: 44px;
  }
  .cast-avatar-wrap {
    width: 74px;
    height: 74px;
  }
}

/* Reduced motion accessibility */
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  .ep-card:hover,
  .cast-card:hover,
  .nav-ep-card:not(.is-disabled):hover,
  .back-to-top:hover,
  .ep-card:hover .ep-thumb,
  .hero-thumb-link:hover .hero-thumb,
  .cast-sheet-frame:hover .cast-sheet-img,
  .cast-turnaround-btn:hover .cast-turnaround-img,
  .btn:active,
  .filter-chip:active,
  .nav-pill-random:active {
    transform: none;
  }
}
"""


_APP_JS = """/* 와우 포에버 슬롭툰 — 정적 웹 아카이브 인터랙션 */
(function () {
  "use strict";

  var HOME_PAGE_SIZE = 24;
  var READ_STORAGE_KEY = "sloptoon_read_eps";

  function getReadEpisodeMap() {
    var map = {};
    try {
      var raw = window.localStorage.getItem(READ_STORAGE_KEY);
      if (!raw) return map;
      var list = JSON.parse(raw);
      if (Array.isArray(list)) {
        list.forEach(function (id) {
          if (typeof id === "string" && id) map[id] = true;
        });
      }
    } catch (_err) {
      /* ignore storage errors */
    }
    return map;
  }

  function markEpisodeRead(episodeId) {
    if (!episodeId) return;
    try {
      var map = getReadEpisodeMap();
      if (map[episodeId]) return;
      var list = Object.keys(map);
      list.push(episodeId);
      if (list.length > 500) list = list.slice(list.length - 500);
      window.localStorage.setItem(READ_STORAGE_KEY, JSON.stringify(list));
    } catch (_err) {
      /* ignore storage errors */
    }
  }

  function applyReadMarks(container) {
    if (!container) return;
    var readMap = getReadEpisodeMap();
    var cards = container.querySelectorAll(".ep-card[data-id]");
    cards.forEach(function (card) {
      var epId = card.getAttribute("data-id") || "";
      var isRead = Boolean(epId && readMap[epId]);
      card.classList.toggle("is-read", isRead);
      var mark = card.querySelector(".ep-read-mark");
      if (mark) mark.hidden = !isRead;
    });
  }

  function prefersReducedMotion() {
    return Boolean(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }

  function showToast(msg) {
    var toast = document.getElementById("toast");
    if (!toast) return;
    toast.textContent = msg;
    toast.hidden = false;
    clearTimeout(showToast._timer);
    showToast._timer = setTimeout(function () {
      toast.hidden = true;
    }, 3200);
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).catch(function () {
        return fallbackCopy(text);
      });
    }
    return Promise.resolve(fallbackCopy(text));
  }

  function fallbackCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand("copy");
    } catch (_err) {
      /* ignore */
    }
    document.body.removeChild(ta);
  }

  function episodeHref(rootPrefix, episodeId) {
    return (rootPrefix || "") + "episodes/" + encodeURIComponent(episodeId) + ".html";
  }

  /* ---------------- GLOBAL RANDOM EPISODE NAVIGATION ---------------- */
  function initRandomButtons() {
    var buttons = document.querySelectorAll(".js-random-ep");
    if (!buttons.length) return;

    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var data = window.__SLOPTOON_DATA__ || {};
        var episodes = Array.isArray(data.episodes) ? data.episodes : [];
        var rootPrefix = data.rootPrefix || "";
        if (episodes.length === 0) {
          showToast("아직 등록된 에피소드가 없습니다.");
          return;
        }
        var currentId = window.__SLOPTOON_CURRENT_EP__ || "";
        var pool = episodes.filter(function (item) {
          return item.episode_id !== currentId;
        });
        if (pool.length === 0) {
          if (currentId) {
            showToast("현재 1화만 등록되어 있습니다. 곧 새로운 념글 만화가 추가됩니다.");
            return;
          }
          pool = episodes;
        }
        var picked = pool[Math.floor(Math.random() * pool.length)];
        window.location.href = episodeHref(rootPrefix, picked.episode_id);
      });
    });
  }

  /* ---------------- HOME PAGE (SEARCH / FILTER / SORT / PAGINATION / READ MARKS) ---------------- */
  function initHomePage() {
    var grid = document.getElementById("episodeGrid");
    var searchInput = document.getElementById("searchInput");
    var filterBar = document.getElementById("castFilterBar");
    var sortToggle = document.getElementById("sortToggle");
    var resultCount = document.getElementById("resultCount");
    var emptyFilter = document.getElementById("emptyFilter");
    var resetBtn = document.getElementById("resetFiltersBtn");
    var loadMoreWrap = document.getElementById("loadMoreWrap");
    var loadMoreBtn = document.getElementById("loadMoreBtn");
    var showAllBtn = document.getElementById("showAllBtn");
    if (!grid) return;

    applyReadMarks(grid);

    var cards = Array.prototype.slice.call(grid.querySelectorAll(".ep-card"));
    var totalAll = cards.length;
    var activeCast = "";
    var sortOrder = "desc";
    var renderedOrder = "desc";
    var visibleLimit = HOME_PAGE_SIZE;

    var params = new URLSearchParams(window.location.search);
    var initCast = params.get("cast");
    if (initCast && filterBar) {
      activeCast = initCast;
      var btns = filterBar.querySelectorAll(".filter-chip");
      btns.forEach(function (btn) {
        var active = btn.getAttribute("data-cast") === activeCast;
        btn.classList.toggle("is-active", active);
        btn.setAttribute("aria-pressed", active ? "true" : "false");
      });
    }

    function reorderDomIfNeeded() {
      if (renderedOrder === sortOrder) return;
      cards.sort(function (a, b) {
        var na = parseInt(a.getAttribute("data-num") || "0", 10);
        var nb = parseInt(b.getAttribute("data-num") || "0", 10);
        return sortOrder === "desc" ? nb - na : na - nb;
      });
      var frag = document.createDocumentFragment();
      cards.forEach(function (card) {
        frag.appendChild(card);
      });
      grid.appendChild(frag);
      renderedOrder = sortOrder;
    }

    function applyFilters() {
      var q = (searchInput ? searchInput.value : "").trim().toLowerCase();
      var qNoHash = q.replace(/^#/, "");
      var matched = [];

      reorderDomIfNeeded();

      cards.forEach(function (card) {
        var epId = (card.getAttribute("data-id") || "").toLowerCase();
        var epNum = (card.getAttribute("data-num") || "").toLowerCase();
        var title = card.getAttribute("data-title") || "";
        var sub = card.getAttribute("data-sub") || "";
        var post = card.getAttribute("data-post") || "";
        var castStr = card.getAttribute("data-cast") || "";
        var castList = castStr ? castStr.split("|") : [];

        var matchesCast = !activeCast || castList.indexOf(activeCast) !== -1;
        var matchesQuery =
          !q ||
          title.indexOf(q) !== -1 ||
          sub.indexOf(q) !== -1 ||
          post.indexOf(qNoHash) !== -1 ||
          epId.indexOf(q) !== -1 ||
          ("ep." + epNum).indexOf(q) !== -1 ||
          (epNum + "화").indexOf(q) !== -1 ||
          castStr.toLowerCase().indexOf(q) !== -1;

        if (matchesCast && matchesQuery) {
          matched.push(card);
        } else {
          card.hidden = true;
        }
      });

      var totalMatched = matched.length;
      var shownCount = 0;
      for (var i = 0; i < totalMatched; i++) {
        var showCard = i < visibleLimit;
        matched[i].hidden = !showCard;
        if (showCard) shownCount += 1;
      }

      if (resultCount) {
        if (q || activeCast) {
          resultCount.textContent = "검색 결과 " + totalMatched + "화 (전체 " + totalAll + "화)";
        } else if (shownCount < totalMatched) {
          resultCount.textContent = "총 " + totalMatched + "개의 에피소드 중 " + shownCount + "화 표시 중";
        } else {
          resultCount.textContent = "총 " + totalMatched + "개의 에피소드";
        }
      }
      if (emptyFilter) {
        emptyFilter.hidden = totalMatched > 0;
      }
      if (loadMoreWrap) {
        var remaining = totalMatched - shownCount;
        loadMoreWrap.hidden = remaining <= 0;
        if (loadMoreBtn && remaining > 0) {
          loadMoreBtn.textContent = "더 보기 (남은 " + remaining + "화)";
        }
      }
    }

    if (searchInput) {
      searchInput.addEventListener("input", function () {
        visibleLimit = HOME_PAGE_SIZE;
        applyFilters();
      });
      searchInput.addEventListener("keydown", function (ev) {
        if (ev.key === "Escape") {
          if (searchInput.value) {
            searchInput.value = "";
            visibleLimit = HOME_PAGE_SIZE;
            applyFilters();
          } else {
            searchInput.blur();
          }
        }
      });
      document.addEventListener("keydown", function (ev) {
        if (ev.key !== "/" || ev.ctrlKey || ev.metaKey || ev.altKey) return;
        var tag = ev.target ? ev.target.tagName : "";
        if (/INPUT|TEXTAREA|SELECT/.test(tag) || (ev.target && ev.target.isContentEditable)) return;
        ev.preventDefault();
        searchInput.focus();
        searchInput.select();
      });
    }
    if (filterBar) {
      filterBar.addEventListener("click", function (ev) {
        var btn = ev.target.closest(".filter-chip");
        if (!btn) return;
        activeCast = btn.getAttribute("data-cast") || "";
        visibleLimit = HOME_PAGE_SIZE;
        filterBar.querySelectorAll(".filter-chip").forEach(function (b) {
          var isMatch = b === btn;
          b.classList.toggle("is-active", isMatch);
          b.setAttribute("aria-pressed", isMatch ? "true" : "false");
        });
        applyFilters();
      });
    }
    if (sortToggle) {
      sortToggle.addEventListener("click", function () {
        sortOrder = sortOrder === "desc" ? "asc" : "desc";
        sortToggle.setAttribute("data-order", sortOrder);
        sortToggle.textContent = sortOrder === "desc" ? "최신순 ↓" : "1화부터 ↑";
        visibleLimit = HOME_PAGE_SIZE;
        applyFilters();
      });
    }
    if (loadMoreBtn) {
      loadMoreBtn.addEventListener("click", function () {
        visibleLimit += HOME_PAGE_SIZE;
        applyFilters();
      });
    }
    if (showAllBtn) {
      showAllBtn.addEventListener("click", function () {
        visibleLimit = Math.max(totalAll, HOME_PAGE_SIZE);
        applyFilters();
      });
    }
    if (resetBtn) {
      resetBtn.addEventListener("click", function () {
        activeCast = "";
        visibleLimit = HOME_PAGE_SIZE;
        if (searchInput) searchInput.value = "";
        if (filterBar) {
          filterBar.querySelectorAll(".filter-chip").forEach(function (b) {
            var isAll = (b.getAttribute("data-cast") || "") === "";
            b.classList.toggle("is-active", isAll);
            b.setAttribute("aria-pressed", isAll ? "true" : "false");
          });
        }
        applyFilters();
      });
    }

    applyFilters();
  }

  /* ---------------- EPISODE READER, PROGRESS, SHARE & BINGE NAVIGATION ---------------- */
  function selectRecommended(episodes, currentIndex, limit) {
    var currentId = episodes[currentIndex].episode_id;
    var adjacent = {};
    if (currentIndex > 0) adjacent[episodes[currentIndex - 1].episode_id] = true;
    if (currentIndex + 1 < episodes.length) adjacent[episodes[currentIndex + 1].episode_id] = true;

    var nonAdjacent = [];
    var adjList = [];
    for (var i = episodes.length - 1; i >= 0; i--) {
      var item = episodes[i];
      if (item.episode_id === currentId) continue;
      if (adjacent[item.episode_id]) {
        adjList.push(item);
      } else {
        nonAdjacent.push(item);
      }
    }
    return nonAdjacent.concat(adjList).slice(0, limit);
  }

  function buildRecommendCardEl(rec, rootPrefix) {
    var article = document.createElement("article");
    article.className = "ep-card";
    article.setAttribute("data-id", rec.episode_id);

    var link = document.createElement("a");
    link.className = "ep-card-link";
    link.href = episodeHref(rootPrefix, rec.episode_id);

    var thumbWrap = document.createElement("div");
    thumbWrap.className = "ep-thumb-wrap";
    var img = document.createElement("img");
    img.src = rootPrefix + rec.thumb_image;
    img.alt = "EP." + rec.episode_number + " " + rec.title;
    img.className = "ep-thumb";
    img.width = 800;
    img.height = 500;
    img.loading = "lazy";
    img.decoding = "async";
    var cuts = document.createElement("span");
    cuts.className = "thumb-cuts";
    cuts.textContent = rec.cut_count + "컷";
    thumbWrap.appendChild(img);
    thumbWrap.appendChild(cuts);

    var body = document.createElement("div");
    body.className = "ep-card-body";
    var metaRow = document.createElement("div");
    metaRow.className = "meta-row";
    var idxSpan = document.createElement("span");
    idxSpan.className = "ep-index";
    idxSpan.textContent = "EP." + rec.episode_number;
    var sep = document.createElement("span");
    sep.className = "meta-sep";
    sep.setAttribute("aria-hidden", "true");
    sep.textContent = "·";
    var postNo = document.createElement("span");
    postNo.className = "post-no";
    postNo.textContent = "#" + rec.source_post_no;
    var dt = document.createElement("span");
    dt.className = "meta-date";
    dt.textContent = rec.date_short || "";
    var readMark = document.createElement("span");
    readMark.className = "ep-read-mark";
    readMark.hidden = true;
    readMark.textContent = "✓ 읽음";
    metaRow.appendChild(idxSpan);
    metaRow.appendChild(sep);
    metaRow.appendChild(postNo);
    metaRow.appendChild(dt);
    metaRow.appendChild(readMark);

    var h3 = document.createElement("h3");
    h3.className = "ep-card-title";
    h3.textContent = rec.title;

    var sub = document.createElement("p");
    sub.className = "ep-card-sub";
    sub.textContent = rec.subtitle || "";

    var chipRow = document.createElement("div");
    chipRow.className = "mini-chip-row";
    (rec.cast_chips || []).forEach(function (chip) {
      var sp = document.createElement("span");
      sp.className = "mini-chip";
      var dot = document.createElement("span");
      dot.className = "cast-dot";
      dot.style.background = chip.color || "#111318";
      sp.appendChild(dot);
      sp.appendChild(document.createTextNode(chip.name));
      chipRow.appendChild(sp);
    });

    body.appendChild(metaRow);
    body.appendChild(h3);
    body.appendChild(sub);
    body.appendChild(chipRow);
    link.appendChild(thumbWrap);
    link.appendChild(body);
    article.appendChild(link);
    return article;
  }

  function buildBingeCardEl(targetEp, isNext, rootPrefix) {
    if (!targetEp) {
      var disabled = document.createElement("div");
      disabled.className = isNext ? "nav-ep-card nav-ep-next is-disabled" : "nav-ep-card is-disabled";
      var info = document.createElement("div");
      info.className = "nav-ep-info";
      var dir = document.createElement("span");
      dir.className = "nav-ep-dir";
      dir.textContent = isNext ? "다음 화 →" : "← 이전 화";
      var ttl = document.createElement("span");
      ttl.className = "nav-ep-title";
      ttl.textContent = isNext ? "가장 최신 에피소드입니다" : "첫 번째 에피소드입니다";
      var hint = document.createElement("span");
      hint.className = "nav-ep-sub";
      hint.textContent = isNext ? "랜덤 화 보기로 다른 명장면도 감상해 보세요." : "지금 1화부터 정주행 중입니다.";
      info.appendChild(dir);
      info.appendChild(ttl);
      info.appendChild(hint);
      disabled.appendChild(info);
      return disabled;
    }

    var a = document.createElement("a");
    a.className = isNext ? "nav-ep-card nav-ep-next" : "nav-ep-card";
    a.href = episodeHref(rootPrefix, targetEp.episode_id);

    var thumbWrap = document.createElement("div");
    thumbWrap.className = "nav-ep-thumb-wrap";
    var img = document.createElement("img");
    img.src = rootPrefix + targetEp.thumb_image;
    img.alt = "EP." + targetEp.episode_number + " " + targetEp.title;
    img.className = "nav-ep-thumb";
    img.width = 800;
    img.height = 500;
    img.loading = "lazy";
    img.decoding = "async";
    thumbWrap.appendChild(img);

    var infoBox = document.createElement("div");
    infoBox.className = "nav-ep-info";
    var dirSpan = document.createElement("span");
    dirSpan.className = isNext ? "nav-ep-dir nav-ep-dir-accent" : "nav-ep-dir";
    var kbd = document.createElement("kbd");
    kbd.className = "key-hint";
    kbd.setAttribute("aria-hidden", "true");
    kbd.textContent = isNext ? "→" : "←";
    if (isNext) {
      dirSpan.appendChild(document.createTextNode("다음 화 바로 보기 "));
      dirSpan.appendChild(kbd);
    } else {
      dirSpan.appendChild(kbd);
      dirSpan.appendChild(document.createTextNode(" 이전 화 정주행"));
    }

    var titleStrong = document.createElement("strong");
    titleStrong.className = "nav-ep-title";
    titleStrong.textContent = "EP." + targetEp.episode_number + " " + targetEp.title;
    var subSpan = document.createElement("span");
    subSpan.className = "nav-ep-sub";
    subSpan.textContent = targetEp.subtitle || "";
    infoBox.appendChild(dirSpan);
    infoBox.appendChild(titleStrong);
    infoBox.appendChild(subSpan);

    if (isNext) {
      a.appendChild(infoBox);
      a.appendChild(thumbWrap);
    } else {
      a.appendChild(thumbWrap);
      a.appendChild(infoBox);
    }
    return a;
  }

  function initReadProgressBar() {
    var bar = document.getElementById("readProgressBar");
    if (!bar) return null;
    var rafPending = false;
    function update() {
      rafPending = false;
      var docEl = document.documentElement;
      var maxScroll = Math.max(0, docEl.scrollHeight - window.innerHeight);
      var pct = maxScroll > 0 ? Math.min(100, Math.max(0, (window.scrollY / maxScroll) * 100)) : 0;
      bar.style.width = pct.toFixed(2) + "%";
    }
    function schedule() {
      if (rafPending) return;
      rafPending = true;
      window.requestAnimationFrame(update);
    }
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule, { passive: true });
    update();
    return update;
  }

  function initEpisodePage() {
    var data = window.__SLOPTOON_DATA__;
    if (!data || !Array.isArray(data.episodes) || data.episodes.length === 0) return;

    var episodes = data.episodes;
    var rootPrefix = data.rootPrefix || "";

    var params = new URLSearchParams(window.location.search);
    var requestedId = data.pinnedEpisodeId || params.get("id") || "";
    var currentIndex = episodes.length - 1;
    if (requestedId) {
      for (var i = 0; i < episodes.length; i++) {
        if (episodes[i].episode_id === requestedId || String(episodes[i].episode_number) === requestedId) {
          currentIndex = i;
          break;
        }
      }
    }
    var ep = episodes[currentIndex];
    window.__SLOPTOON_CURRENT_EP__ = ep.episode_id;
    markEpisodeRead(ep.episode_id);

    var prevEp = currentIndex > 0 ? episodes[currentIndex - 1] : null;
    var nextEp = currentIndex + 1 < episodes.length ? episodes[currentIndex + 1] : null;
    var canonicalShareUrl =
      ep.canonical_url || ((data.archiveBaseUrl || "https://slopwow.github.io").replace(/\\/+$/, "") + "/episodes/" + ep.episode_id + ".html");

    document.title = "EP." + ep.episode_number + " " + ep.title + " — 와우 포에버 슬롭툰";
    var badgeEl = document.getElementById("epBadge");
    if (badgeEl) badgeEl.textContent = "EP." + ep.episode_number + " · #" + ep.source_post_no;
    var dateEl = document.getElementById("epDate");
    if (dateEl) dateEl.textContent = ep.date_short || "";
    var cutsEl = document.getElementById("epCuts");
    if (cutsEl) cutsEl.textContent = ep.cut_count + "컷 상황극";
    var titleEl = document.getElementById("epTitle");
    if (titleEl) titleEl.textContent = ep.title;
    var subEl = document.getElementById("epSub");
    if (subEl) subEl.textContent = ep.subtitle;

    var sourceEl = document.getElementById("epSourceLink");
    if (sourceEl) {
      sourceEl.href = ep.source_url;
      sourceEl.textContent = "원본 포에버갤 개념글 (#" + ep.source_post_no + ") ↗";
    }
    var bottomSourceEl = document.getElementById("epBottomSourceLink");
    if (bottomSourceEl) {
      bottomSourceEl.href = ep.source_url;
    }

    var castRow = document.getElementById("epCastRow");
    if (castRow && Array.isArray(ep.cast_chips)) {
      castRow.innerHTML = "";
      ep.cast_chips.forEach(function (chip) {
        var a = document.createElement("a");
        a.className = "cast-chip";
        a.href = rootPrefix + "cast.html#" + encodeURIComponent(chip.id || "");
        var dot = document.createElement("span");
        dot.className = "cast-dot";
        dot.style.background = chip.color || "#111318";
        a.appendChild(dot);
        a.appendChild(document.createTextNode(chip.name));
        castRow.appendChild(a);
      });
    }

    var fullImg = document.getElementById("epFullImg");
    var fullSrc = rootPrefix + ep.full_image;
    if (fullImg) {
      fullImg.src = fullSrc;
      fullImg.alt = "와우 포에버 슬롭툰 EP." + ep.episode_number + " " + ep.title + " 통합본";
    }

    var pagesView = document.getElementById("readerPagesView");
    if (pagesView && Array.isArray(ep.page_images)) {
      pagesView.innerHTML = "";
      var totalPages = ep.page_images.length;
      ep.page_images.forEach(function (rel, idx) {
        var fig = document.createElement("figure");
        fig.className = "reader-page-item";
        var cap = document.createElement("figcaption");
        cap.className = "reader-page-label";
        var pNum = String(idx + 1).padStart(2, "0");
        var pTot = String(totalPages).padStart(2, "0");
        cap.textContent = "PAGE " + pNum + " / " + pTot;
        var img = document.createElement("img");
        img.src = rootPrefix + rel;
        img.alt = "EP." + ep.episode_number + " 페이지 " + (idx + 1);
        img.className = "reader-page-img";
        img.loading = "lazy";
        img.decoding = "async";
        fig.appendChild(cap);
        fig.appendChild(img);
        pagesView.appendChild(fig);
      });
    }

    document.querySelectorAll(".js-share-url").forEach(function (btn) {
      btn.setAttribute("data-share-url", canonicalShareUrl);
      btn.addEventListener("click", function () {
        var origText = btn.textContent;
        copyText(canonicalShareUrl).then(function () {
          showToast("링크가 복사되었습니다! " + canonicalShareUrl);
          btn.textContent = "✓ 링크 복사됨";
          clearTimeout(btn._copyTimer);
          btn._copyTimer = setTimeout(function () {
            btn.textContent = origText;
          }, 1800);
        });
      });
    });

    var pager = document.getElementById("epPager");
    if (pager) {
      pager.innerHTML = "";
      pager.appendChild(buildBingeCardEl(prevEp, false, rootPrefix));
      pager.appendChild(buildBingeCardEl(nextEp, true, rootPrefix));
    }

    var recSection = document.getElementById("epRecommendSection");
    var recGrid = document.getElementById("epRecommendGrid");
    if (recSection && recGrid) {
      var recs = selectRecommended(episodes, currentIndex, 3);
      recGrid.innerHTML = "";
      if (recs.length > 0) {
        recs.forEach(function (rec) {
          recGrid.appendChild(buildRecommendCardEl(rec, rootPrefix));
        });
        applyReadMarks(recGrid);
        recSection.hidden = false;
      } else {
        recSection.hidden = true;
      }
    }

    var updateProgress = initReadProgressBar();

    var fullView = document.getElementById("readerFullView");
    document.querySelectorAll(".mode-btn[data-mode]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var mode = btn.getAttribute("data-mode");
        document.querySelectorAll(".mode-btn[data-mode]").forEach(function (b) {
          var active = b === btn;
          b.classList.toggle("is-active", active);
          b.setAttribute("aria-pressed", active ? "true" : "false");
        });
        if (fullView) fullView.hidden = mode !== "full";
        if (pagesView) pagesView.hidden = mode !== "pages";
        if (updateProgress) window.requestAnimationFrame(updateProgress);
      });
    });

    var jumpSelect = document.getElementById("epJumpSelect");
    if (jumpSelect) {
      jumpSelect.value = ep.episode_id;
      jumpSelect.addEventListener("change", function () {
        if (jumpSelect.value && jumpSelect.value !== ep.episode_id) {
          window.location.href = episodeHref(rootPrefix, jumpSelect.value);
        }
      });
    }

    document.addEventListener("keydown", function (ev) {
      if (ev.target && /INPUT|TEXTAREA|SELECT/.test(ev.target.tagName)) return;
      if (ev.key === "ArrowLeft" && prevEp) {
        window.location.href = episodeHref(rootPrefix, prevEp.episode_id);
      } else if (ev.key === "ArrowRight" && nextEp) {
        window.location.href = episodeHref(rootPrefix, nextEp.episode_id);
      }
    });
  }

  /* ---------------- GLOBAL BACK TO TOP ---------------- */
  function initBackToTop() {
    var btn = document.getElementById("backToTopBtn");
    if (!btn) return;
    function toggleBtn() {
      btn.hidden = window.scrollY < 420;
    }
    window.addEventListener("scroll", toggleBtn, { passive: true });
    btn.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: prefersReducedMotion() ? "auto" : "smooth" });
    });
    toggleBtn();
  }

  /* ---------------- CAST PAGE (FACTION FILTER & ACCESSIBLE LIGHTBOX) ---------------- */
  function initCastPage() {
    var factionFilter = document.getElementById("castFactionFilter");
    var castGrid = document.getElementById("castGrid");
    var castCountMeta = document.getElementById("castCountMeta");
    var factionNames = {
      Horde: "호드",
      Alliance: "얼라이언스",
      "Neutral-Skyborne": "스카이본"
    };

    if (factionFilter && castGrid) {
      var castCards = Array.prototype.slice.call(castGrid.querySelectorAll(".cast-card"));
      var totalCast = castCards.length;
      var defaultMetaText = castCountMeta ? castCountMeta.textContent : "";

      factionFilter.addEventListener("click", function (ev) {
        var btn = ev.target.closest(".filter-chip");
        if (!btn) return;
        var faction = btn.getAttribute("data-faction") || "";
        factionFilter.querySelectorAll(".filter-chip").forEach(function (b) {
          var isMatch = b === btn;
          b.classList.toggle("is-active", isMatch);
          b.setAttribute("aria-pressed", isMatch ? "true" : "false");
        });
        var visibleCount = 0;
        castCards.forEach(function (card) {
          var show = !faction || card.getAttribute("data-faction") === faction;
          card.hidden = !show;
          if (show) visibleCount += 1;
        });
        if (castCountMeta) {
          if (!faction) {
            castCountMeta.textContent = defaultMetaText;
          } else {
            castCountMeta.textContent = (factionNames[faction] || faction) + " " + visibleCount + "명 표시 중 (전체 " + totalCast + "명)";
          }
        }
      });
    }

    var lightbox = document.getElementById("lightbox");
    var lightboxImg = document.getElementById("lightboxImg");
    var lightboxCaption = document.getElementById("lightboxCaption");
    var lightboxClose = document.getElementById("lightboxClose");

    if (lightbox && lightboxImg) {
      var lastTrigger = null;

      var openLightbox = function (src, alt, triggerEl) {
        if (!src) return;
        lastTrigger = triggerEl || document.activeElement;
        lightboxImg.src = src;
        lightboxImg.alt = alt || "확대 이미지";
        if (lightboxCaption) lightboxCaption.textContent = alt || "";
        lightbox.hidden = false;
        document.body.style.overflow = "hidden";
        if (lightboxClose) lightboxClose.focus();
      };

      var closeLightbox = function () {
        if (lightbox.hidden) return;
        lightbox.hidden = true;
        lightboxImg.removeAttribute("src");
        if (lightboxCaption) lightboxCaption.textContent = "";
        document.body.style.overflow = "";
        if (lastTrigger && typeof lastTrigger.focus === "function") {
          lastTrigger.focus();
        }
        lastTrigger = null;
      };

      document.querySelectorAll("[data-lightbox-src]").forEach(function (el) {
        el.addEventListener("click", function () {
          var src = el.getAttribute("data-lightbox-src");
          var img = el.querySelector("img");
          openLightbox(src, img ? img.alt : "", el);
        });
      });

      if (lightboxClose) lightboxClose.addEventListener("click", closeLightbox);
      lightbox.addEventListener("click", function (ev) {
        if (ev.target === lightbox) closeLightbox();
      });
      document.addEventListener("keydown", function (ev) {
        if (ev.key === "Escape" && !lightbox.hidden) closeLightbox();
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    var page = document.body.getAttribute("data-page");
    if (page === "home") initHomePage();
    if (page === "episode") initEpisodePage();
    if (page === "cast") initCastPage();
    initRandomButtons();
    initBackToTop();
  });
})();
"""


def build_static_site(
    episodes_json: Path,
    site_dir: Path,
    assets_dir: Path,
    archive_base_url: str = DEFAULT_ARCHIVE_BASE_URL,
) -> Path:
    """Build the complete static pure-white web archive into `site_dir`.

    Copies the SD cast sheet & turnarounds, generates individual 1:1 portraits from each
    character's front-facing turnaround (falling back to `cast_sheet_c.jpg`), syncs episode
    images while automatically cleaning orphan `page_*` files/dirs, auto-generates missing
    thumbnails, and emits `index.html`, `episode.html`, static `episodes/<id>.html`,
    `cast.html`, `sitemap.xml`, `robots.txt`, `assets/style.css`, `assets/app.js`, and
    `data/episodes.json`.

    Returns:
        Path to the generated `site_dir / "index.html"`.
    """
    episodes_json = Path(episodes_json)
    site_dir = Path(site_dir)
    assets_dir = Path(assets_dir)

    clean_base = _normalize_base_url(archive_base_url)
    canonical_base = clean_base or DEFAULT_ARCHIVE_BASE_URL

    site_dir.mkdir(parents=True, exist_ok=True)
    site_assets_dir = site_dir / "assets"
    site_cast_dir = site_assets_dir / "cast"
    site_episodes_assets_dir = site_assets_dir / "episodes"
    site_episodes_html_dir = site_dir / "episodes"
    site_data_dir = site_dir / "data"

    for d in (
        site_assets_dir,
        site_cast_dir,
        site_episodes_assets_dir,
        site_episodes_html_dir,
        site_data_dir,
    ):
        d.mkdir(parents=True, exist_ok=True)

    # 1. Sync cast sheet & turnaround assets, and extract 2.5-head SD portraits from turnarounds
    # Clean legacy labeled sheet if left behind in site/assets/cast/
    (site_cast_dir / "cast_sheet_c_labeled.png").unlink(missing_ok=True)

    clean_src = assets_dir / "cast_sheet_c.jpg"
    has_clean = False
    if clean_src.exists():
        _copy_if_different(clean_src, site_cast_dir / "cast_sheet_c.jpg")
        has_clean = True

    turnarounds_src_dir = assets_dir / "turnarounds"
    portraits = extract_cast_portraits(
        clean_src if has_clean else None,
        site_cast_dir,
        turnarounds_dir=turnarounds_src_dir if turnarounds_src_dir.exists() else None,
    )

    site_turnarounds_dir = site_cast_dir / "turnarounds"
    turnarounds: dict[str, str] = {}
    companion_turnarounds: dict[str, str] = {}
    if turnarounds_src_dir.exists():
        site_turnarounds_dir.mkdir(parents=True, exist_ok=True)
        for member in CAST_BIBLE:
            t_src = turnarounds_src_dir / member.turnaround_filename
            if t_src.exists() and t_src.is_file():
                _copy_if_different(t_src, site_turnarounds_dir / member.turnaround_filename)
                turnarounds[member.id] = f"assets/cast/turnarounds/{member.turnaround_filename}"
            if member.companion_turnaround_filename:
                ct_src = turnarounds_src_dir / member.companion_turnaround_filename
                if ct_src.exists() and ct_src.is_file():
                    _copy_if_different(ct_src, site_turnarounds_dir / member.companion_turnaround_filename)
                    companion_turnarounds[member.id] = (
                        f"assets/cast/turnarounds/{member.companion_turnaround_filename}"
                    )
    fallback_og_image = "assets/cast/cast_sheet_c.jpg" if has_clean else ""

    # 2. Load episodes, sync media assets into site/assets/episodes/<id>/, and clean orphan files
    records = load_episodes(episodes_json)
    site_episodes: list[dict[str, Any]] = []
    ep_counts: dict[str, int] = {}

    valid_episode_ids = {r.episode_id for r in records}
    for stale_ep_dir in site_episodes_assets_dir.iterdir():
        if stale_ep_dir.is_dir() and stale_ep_dir.name not in valid_episode_ids:
            shutil.rmtree(stale_ep_dir, ignore_errors=True)

    for record in records:
        ep_out_dir = site_episodes_assets_dir / record.episode_id
        ep_out_dir.mkdir(parents=True, exist_ok=True)
        expected_ep_files: set[str] = set()

        # Resolve and copy full image
        full_src = _resolve_media_path(record.full_image_rel, episodes_json, assets_dir, site_dir)
        full_dst = ep_out_dir / "episode_full.jpg"
        if full_src is not None:
            _copy_if_different(full_src, full_dst)
            expected_ep_files.add(full_dst.name)

        # Resolve and copy current page images
        page_web_paths: list[str] = []
        resolved_pages: list[Path] = []
        for idx, page_rel in enumerate(record.page_images_rel, start=1):
            p_src = _resolve_media_path(page_rel, episodes_json, assets_dir, site_dir)
            if p_src is not None:
                ext = p_src.suffix.lower() or ".png"
                p_name = f"page_{idx}{ext}"
                p_dst = ep_out_dir / p_name
                _copy_if_different(p_src, p_dst)
                expected_ep_files.add(p_name)
                page_web_paths.append(
                    f"assets/episodes/{record.episode_id}/{p_name}{_file_cache_suffix(p_dst)}"
                )
                resolved_pages.append(p_src)

        # Resolve, copy, or auto-generate thumbnail
        thumb_src = _resolve_media_path(record.thumb_image_rel, episodes_json, assets_dir, site_dir)
        thumb_dst = ep_out_dir / "thumb.jpg"
        if thumb_src is not None:
            _copy_if_different(thumb_src, thumb_dst)
            expected_ep_files.add(thumb_dst.name)
        else:
            thumb_basis = resolved_pages[0] if resolved_pages else full_src
            if thumb_basis is not None and thumb_basis.exists():
                generate_episode_thumbnail(thumb_basis, thumb_dst)
                expected_ep_files.add(thumb_dst.name)
                declared_data_thumb = episodes_json.parent.parent / record.thumb_image_rel
                if declared_data_thumb.parent.exists() and not declared_data_thumb.exists():
                    _copy_if_different(thumb_dst, declared_data_thumb)

        # Clean any orphan files (such as leftover page_4.png / page_5.png from earlier builds)
        for existing_file in ep_out_dir.iterdir():
            if existing_file.is_file() and existing_file.name not in expected_ep_files:
                existing_file.unlink(missing_ok=True)

        # Normalize cast list and tally appearances
        cast_chips: list[dict[str, str]] = []
        normalized_cast: list[str] = []
        for raw_name in record.cast_used:
            member = resolve_cast_member(raw_name)
            canon = member.name if member else raw_name
            if canon not in normalized_cast:
                normalized_cast.append(canon)
                ep_counts[canon] = ep_counts.get(canon, 0) + 1
                cast_chips.append({
                    "id": member.id if member else "",
                    "name": canon,
                    "color": member.color_hex if member else "#111111",
                })

        canonical_ep_url = f"{canonical_base}/episodes/{record.episode_id}.html"
        site_episodes.append({
            "episode_id": record.episode_id,
            "episode_number": record.episode_number,
            "title": record.title,
            "subtitle": record.subtitle,
            "source_post_no": record.source_post_no,
            "source_url": record.source_url,
            "created_at": record.created_at,
            "date_short": _format_date_short(record.created_at),
            "cut_count": record.cut_count,
            "cast_used": normalized_cast,
            "cast_chips": cast_chips,
            "full_image": f"assets/episodes/{record.episode_id}/episode_full.jpg{_file_cache_suffix(full_dst)}",
            "thumb_image": f"assets/episodes/{record.episode_id}/thumb.jpg{_file_cache_suffix(thumb_dst)}",
            "page_images": page_web_paths,
            "canonical_url": canonical_ep_url,
        })

    # 3. Build cast metadata payload
    cast_payload = [
        _cast_member_payload(
            member,
            portraits.get(member.id),
            ep_counts,
            turnaround_rel=turnarounds.get(member.id),
            companion_turnaround_rel=companion_turnarounds.get(member.id),
        )
        for member in CAST_BIBLE
    ]

    # 4. Write shared static assets, favicon, site JSON, and crawler metadata
    style_css_path = site_assets_dir / "style.css"
    app_js_path = site_assets_dir / "app.js"
    favicon_path = site_assets_dir / "favicon.svg"
    style_css_path.write_text(_STYLE_CSS, encoding="utf-8")
    app_js_path.write_text(_APP_JS, encoding="utf-8")
    favicon_path.write_text(_FAVICON_SVG, encoding="utf-8")
    css_suffix = _file_cache_suffix(style_css_path)
    js_suffix = _file_cache_suffix(app_js_path)
    (site_data_dir / "episodes.json").write_text(
        json.dumps(site_episodes, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (site_dir / ".nojekyll").write_text("", encoding="utf-8")
    (site_dir / "sitemap.xml").write_text(
        _render_sitemap_xml(site_episodes, canonical_base),
        encoding="utf-8",
    )
    (site_dir / "robots.txt").write_text(
        _render_robots_txt(canonical_base),
        encoding="utf-8",
    )

    # 5. Write HTML pages
    index_path = site_dir / "index.html"
    index_path.write_text(
        _render_index_html(
            site_episodes,
            cast_payload,
            len(site_episodes),
            base_url=clean_base,
            fallback_og_image=fallback_og_image,
            css_suffix=css_suffix,
            js_suffix=js_suffix,
        ),
        encoding="utf-8",
    )

    latest_ep = site_episodes[-1] if site_episodes else None
    (site_dir / "episode.html").write_text(
        _render_episode_reader_html(
            site_episodes,
            latest_ep,
            root_prefix="",
            base_url=clean_base,
            fallback_og_image=fallback_og_image,
            css_suffix=css_suffix,
            js_suffix=js_suffix,
        ),
        encoding="utf-8",
    )

    valid_episode_html_names = {f"{ep['episode_id']}.html" for ep in site_episodes}
    for stale_html in site_episodes_html_dir.glob("*.html"):
        if stale_html.name not in valid_episode_html_names:
            stale_html.unlink(missing_ok=True)

    for ep in site_episodes:
        (site_episodes_html_dir / f"{ep['episode_id']}.html").write_text(
            _render_episode_reader_html(
                site_episodes,
                ep,
                root_prefix="../",
                pinned_episode_id=ep["episode_id"],
                base_url=clean_base,
                fallback_og_image=fallback_og_image,
                css_suffix=css_suffix,
                js_suffix=js_suffix,
            ),
            encoding="utf-8",
        )

    (site_dir / "cast.html").write_text(
        _render_cast_html(
            cast_payload,
            site_episodes,
            has_clean,
            base_url=clean_base,
            css_suffix=css_suffix,
            js_suffix=js_suffix,
        ),
        encoding="utf-8",
    )

    # Never expose creator upload helper pages publicly on the reader archive
    (site_dir / "publish.html").unlink(missing_ok=True)

    return index_path
