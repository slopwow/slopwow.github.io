"""Static web archive builder for wow-forever-sloptoon.

Generates a pure-white (#FFFFFF) Korean gag-sloptoon web archive deployable to
GitHub Pages, Vercel, Cloudflare Pages, local `http.server`, or direct `file://`.
"""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from wow_sloptoon.cast import CAST_BIBLE, CAST_BY_NAME, CastMember, resolve_cast_member
from wow_sloptoon.config import DEFAULT_ARCHIVE_BASE_URL, DEFAULT_GALLERY_ID
from wow_sloptoon.models import EpisodeRecord

SITE_NAME = "와우 포에버 슬롭툰"
SITE_TAGLINE = "디시 WOW 포에버 마이너 갤러리 개념글 상황극 봇"
SITE_DESCRIPTION = (
    "디시인사이드 WOW 포에버 마이너 갤러리 개념글을 시안 C 귀염뽀짝 9×9 미소녀 4~6컷 상황극 웹툰으로 아카이빙합니다."
)
LEGAL_NOTICE = (
    "본 사이트는 World of Warcraft 및 디시인사이드 WOW 포에버 마이너 갤러리 기반의 비공식 팬메이드 패러디 아카이브입니다. "
    "모든 에피소드에 원글 출처를 표기하며, 원작자 삭제 요청 시 즉시 비공개 처리합니다."
)

DC_GALLERY_RECOMMEND_URL = (
    f"https://gall.dcinside.com/mgallery/board/lists/?id={DEFAULT_GALLERY_ID}&exception_mode=recommend"
)
DC_GALLERY_WRITE_URL = (
    f"https://gall.dcinside.com/mgallery/board/write/?id={DEFAULT_GALLERY_ID}"
)

# Normalized (x0, y0, x1, y1) portrait crop boxes on the 1600x900 clean Draft C full-body cast sheet.
_CAST_PORTRAIT_BOXES: dict[str, tuple[float, float, float, float]] = {
    "orc_warrior": (0.025, 0.015, 0.200, 0.495),
    "undead_paladin": (0.215, 0.015, 0.395, 0.495),
    "gnome_rogue": (0.400, 0.035, 0.598, 0.495),
    "dwarf_hunter": (0.605, 0.015, 0.785, 0.495),
    "troll_shaman": (0.798, 0.015, 0.975, 0.495),
    "tauren_druid": (0.078, 0.505, 0.265, 0.988),
    "nightelf_priest": (0.288, 0.505, 0.495, 0.988),
    "human_warlock": (0.518, 0.505, 0.705, 0.988),
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
        episodes_json.parent.parent / p,  # project root (e.g. data/episodes/ep001/...)
        episodes_json.parent / p,  # data/ dir (e.g. episodes/ep001/...)
        assets_dir.parent / p,  # project root inferred from assets_dir
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
    """Create a crisp pure-white (#FFFFFF) card thumbnail cropped from key panel art.

    For standard 2-tier sloptoon pages (e.g. 900x1320), isolates the top cut's clean
    character illustration band below the speech bubble and above the bottom boxed cut.
    For full stitched strips or arbitrary images, crops cleanly near the top hero art
    without clipping heads or showing awkward borders.
    """
    dest_thumb.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source_image) as im:
        rgb = im.convert("RGB")
        w, h = rgb.size
        arr = np.array(rgb)

        # Normalize near-white speckles to pure white for clean ink detection.
        ink_mask = (arr < 242).any(axis=2)
        crop_box: tuple[int, int, int, int]

        if w >= 600 and 1000 <= h <= 1650:
            # Standard 2-tier page: speech bubble (+ tail) on top, open character art in middle,
            # boxed panel at bottom (~64%+ height). Erase any connected component touching the
            # top edge of the middle slice (which is always the speech bubble / tail) so the
            # character illustration is 100% pure with zero stray V-tail artifacts.
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
            # Full stitched vertical strip: skip header (~244px) and first speech bubble (~290px).
            start_y = min(int(h * 0.14), 560)
            band_h = min(int(w * 0.62), h - start_y)
            region = rgb.crop((0, start_y, w, min(h, start_y + max(band_h, 100))))
        else:
            # General / square / single-panel image: trim outer pure white border cleanly.
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

        # Clean near-white background to #FFFFFF inside the thumbnail.
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
        # Anchor characters gently toward bottom edge for open-bottom comic look.
        paste_y = target_h - new_h - max(4, padding // 2) if (target_h - new_h) < padding * 3 else (target_h - new_h) // 2
        paste_y = max(padding // 2, min(paste_y, target_h - new_h))
        canvas.paste(resized, (paste_x, paste_y))
        canvas.save(dest_thumb, format="JPEG", quality=93, optimize=True)

    return dest_thumb


def extract_cast_portraits(cast_sheet_clean: Path, dest_cast_dir: Path, size: int = 360) -> dict[str, str]:
    """Crop 9 individual square Draft C character portraits from `cast_sheet_c.jpg`."""
    if not cast_sheet_clean.exists():
        return {}

    dest_cast_dir.mkdir(parents=True, exist_ok=True)
    generated: dict[str, str] = {}

    with Image.open(cast_sheet_clean) as im:
        rgb = im.convert("RGB")
        w, h = rgb.size
        if w < 200 or h < 120:
            return {}

        for member in CAST_BIBLE:
            box_ratio = _CAST_PORTRAIT_BOXES.get(member.id)
            if not box_ratio:
                continue
            x0 = max(0, int(round(w * box_ratio[0])))
            y0 = max(0, int(round(h * box_ratio[1])))
            x1 = min(w, int(round(w * box_ratio[2])))
            y1 = min(h, int(round(h * box_ratio[3])))
            if x1 <= x0 + 10 or y1 <= y0 + 10:
                continue

            crop = rgb.crop((x0, y0, x1, y1))
            arr = np.array(crop)
            near_white = (arr[:, :, 0] >= 246) & (arr[:, :, 1] >= 246) & (arr[:, :, 2] >= 246)
            arr[near_white] = 255

            # Remove disconnected neighbor fragments touching the far left/right crop edges
            # (e.g., adjacent weapon blade tips intruding into the paladin portrait margin).
            ink = (arr < 245).any(axis=2)
            ch, cw = ink.shape
            visited = np.zeros_like(ink, dtype=bool)
            for edge_x in (0, cw - 1):
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
                        # If a component touches left/right edge and never reaches the center band,
                        # it belongs to a neighboring character -> erase to pure white.
                        touches_center = not (max_cx < int(cw * 0.24) or min_cx > int(cw * 0.76))
                        if not touches_center:
                            for cy, cx in comp:
                                arr[cy, cx] = 255

            # Tight trim inside portrait cell
            ink = (arr < 245).any(axis=2)
            ys = np.where(ink.any(axis=1))[0]
            xs = np.where(ink.any(axis=0))[0]
            if len(ys) > 8 and len(xs) > 8:
                arr = arr[int(ys[0]):int(ys[-1]) + 1, int(xs[0]):int(xs[-1]) + 1]
            trimmed = Image.fromarray(arr, mode="RGB")

            pad = 14
            inner = size - pad * 2
            tw, th = trimmed.size
            scale = min(inner / max(tw, 1), inner / max(th, 1))
            nw = max(1, int(round(tw * scale)))
            nh = max(1, int(round(th * scale)))
            resized = trimmed.resize((nw, nh), Image.Resampling.LANCZOS)

            canvas = Image.new("RGB", (size, size), (255, 255, 255))
            px = (size - nw) // 2
            py = size - nh - 4
            canvas.paste(resized, (px, max(pad // 2, py)))
            out_path = dest_cast_dir / f"{member.id}.jpg"
            canvas.save(out_path, format="JPEG", quality=92, optimize=True)
            generated[member.id] = f"assets/cast/{member.id}.jpg"

    return generated


def _normalize_base_url(archive_base_url: str | None) -> str:
    return (archive_base_url or "").strip().rstrip("/")


def _build_dc_post_title(ep: EpisodeRecord) -> str:
    return f"[와포슬롭툰]{ep.title.strip()}"


def _build_dc_post_body(
    ep: EpisodeRecord,
    archive_base_url: str = DEFAULT_ARCHIVE_BASE_URL,
) -> str:
    clean_base = _normalize_base_url(archive_base_url) or DEFAULT_ARCHIVE_BASE_URL
    canonical_ep_url = f"{clean_base}/episodes/{ep.episode_id}.html"
    lines = [
        f"와우 포에버 슬롭툰 EP.{ep.episode_number} — {ep.title}",
        ep.subtitle,
        "",
        f"원본 포에버갤 개념글 (#{ep.source_post_no}):",
        ep.source_url,
        "",
        f"전편 정주행 아카이브: {canonical_ep_url}",
        f"전체 정주행: {clean_base}",
        "",
        "※ 시안 C 귀염뽀짝 9×9 미소녀 상황극 봇 (순수 팬메이드 패러디)",
    ]
    return "\n".join(lines)


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
        parts = [f"  <url>", f"    <loc>{html.escape(loc)}</loc>"]
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


def _render_nav(active: str, root_prefix: str = "") -> str:
    def _cls(key: str) -> str:
        return "nav-link is-active" if active == key else "nav-link"

    return f"""
    <header class="site-header">
      <div class="container header-inner">
        <a class="brand" href="{root_prefix}index.html" aria-label="와우 포에버 슬롭툰 홈">
          <span class="brand-dot" aria-hidden="true"></span>
          <span class="brand-name">와우 포에버 슬롭툰</span>
          <span class="brand-tag">ARCHIVE</span>
        </a>
        <nav class="site-nav" aria-label="주요 메뉴">
          <a class="{_cls('home')}" href="{root_prefix}index.html">에피소드</a>
          <a class="{_cls('cast')}" href="{root_prefix}cast.html">9×9 캐스트 도감</a>
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
          <span class="pill-badge pill-sm"><span class="dot-sky"></span>{SITE_TAGLINE}</span>
          <p class="footer-desc">
            포에버갤 개념글의 명장면을 시안 C 귀염뽀짝 9종족×9직업 미소녀 4~6컷 순수 상황극 웹툰으로 아카이빙합니다.
            현재 총 <strong>{total_episodes}화</strong>가 아카이브에 보관되어 있습니다.
          </p>
        </div>
        <div class="footer-links">
          <a href="{root_prefix}index.html">전체 에피소드</a>
          <a href="{root_prefix}cast.html">시안 C 캐스트 도감</a>
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
    color = member.color_hex if member else "#111111"
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
        f'<span class="mini-chip"><span class="cast-dot" style="background:{html.escape((CAST_BY_NAME[c].color_hex if c in CAST_BY_NAME else "#111111"))};"></span>{html.escape(c)}</span>'
        for c in ep["cast_used"]
    )
    filter_attrs = ""
    if include_filter_attrs:
        filter_attrs = (
            f'\n              data-id="{html.escape(ep["episode_id"])}"'
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
                    <span class="ep-pill ep-pill-sm">EP.{ep['episode_number']}</span>
                    <span class="post-no">#{html.escape(ep['source_post_no'])}</span>
                    <span class="meta-date">{html.escape(ep['date_short'])}</span>
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
) -> str:
    newest_first = list(reversed(site_episodes))
    latest = newest_first[0] if newest_first else None
    og_image_rel = latest["thumb_image"] if latest else fallback_og_image
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
        <section class="hero-section" aria-label="최신 에피소드">
          <div class="hero-card">
            <a class="hero-thumb-link" href="{latest_href}">
              <img src="{html.escape(latest['thumb_image'])}" alt="EP.{latest['episode_number']} {html.escape(latest['title'])} 썸네일" class="hero-thumb" loading="eager">
              <span class="thumb-flag">LATEST · EP.{latest['episode_number']}</span>
              <span class="thumb-cuts">{latest['cut_count']}컷 상황극</span>
            </a>
            <div class="hero-body">
              <div class="meta-row">
                <span class="ep-pill">EP.{latest['episode_number']} · #{html.escape(latest['source_post_no'])}</span>
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
        <section class="empty-hero">
          <p>아직 등록된 에피소드가 없습니다. <code>sloptoon run-once</code>로 첫 화를 생성해 보세요!</p>
        </section>
        """

    filter_buttons = [
        f'<button type="button" class="filter-chip is-active" data-cast="">전체 <span class="filter-count">{total_episodes}</span></button>'
    ]
    for c in cast_payload:
        filter_buttons.append(
            f'<button type="button" class="filter-chip" data-cast="{html.escape(c["name"])}">'
            f'<span class="cast-dot" style="background:{html.escape(c["color_hex"])};"></span>'
            f'{html.escape(c["name"])} <span class="filter-count">{c["episode_count"]}</span>'
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
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
  <link rel="stylesheet" href="assets/style.css">
</head>
<body data-page="home">
  {_render_nav('home')}

  <main class="container main-content">
    <section class="masthead">
      <div class="pill-badge">
        <span class="dot-sky"></span>{SITE_TAGLINE}
      </div>
      <h1 class="masthead-title">{SITE_NAME}</h1>
      <p class="masthead-sub">포에버갤 레전드 개념글을 시안 C 9종족×9직업 귀염뽀짝 미소녀 100% 라이브 상황극으로 연재하는 순백 웹 아카이브</p>
      <div class="masthead-stats">
        <span class="stat-pill">총 <strong>{total_episodes}</strong>화 아카이브</span>
        <span class="stat-pill">시안 C 9×9 캐스트</span>
        <span class="stat-pill">순백 무경계 4~6컷</span>
      </div>
    </section>

    <hr class="ink-divider">

    {hero_html}

    <section class="archive-section" aria-label="전체 에피소드 목록">
      <div class="section-head">
        <div>
          <h2 class="section-title">전체 에피소드</h2>
          <p class="section-meta" id="resultCount">총 {total_episodes}개의 에피소드</p>
        </div>
        <div class="controls-right">
          <div class="search-box">
            <span class="search-icon" aria-hidden="true">⌕</span>
            <input type="search" id="searchInput" class="search-input" placeholder="제목, 화수(EP.12), 글번호(#92059), 캐릭터 검색..." autocomplete="off">
          </div>
          <button type="button" id="sortToggle" class="btn btn-subtle" data-order="desc" title="정렬 순서 전환">최신순 ↓</button>
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
        <button type="button" id="showAllBtn" class="btn btn-subtle">전체 펼치기</button>
      </div>

      <div class="empty-filter" id="emptyFilter" hidden>
        <p class="empty-filter-title">조건에 맞는 에피소드가 아직 없어요!</p>
        <p class="empty-filter-sub">다른 검색어나 캐릭터를 선택해 보세요.</p>
        <button type="button" id="resetFiltersBtn" class="btn btn-outline">필터 초기화</button>
      </div>
    </section>

    <aside class="slop-sponsor-slot" data-slot="home-feed-bottom" aria-label="스폰서 영역"></aside>
  </main>

  {_render_footer(total_episodes)}

  <script>window.__SLOPTOON_DATA__ = {embedded_data};</script>
  <script src="assets/app.js"></script>
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
) -> str:
    """Render `episode.html` (dynamic `?id=...`) or a static `episodes/<id>.html` page."""
    ep = default_episode
    total_episodes = len(site_episodes)
    # Keep pinned episode pages lean at 30–80+ episodes by omitting other episodes' page_images
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
    og_img_rel = ep["thumb_image"] if ep else fallback_og_image
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

    # Pre-render initial episode SSR content so no-JS crawlers, tests, and instant first paint work!
    if ep:
        idx = next((i for i, item in enumerate(site_episodes) if item["episode_id"] == ep["episode_id"]), 0)
        prev_ep = site_episodes[idx - 1] if idx > 0 else None
        next_ep = site_episodes[idx + 1] if idx + 1 < len(site_episodes) else None
        recommended = _select_recommended_episodes(site_episodes, ep["episode_id"], limit=3)
        cast_chips = "".join(_render_cast_chip_html(c, root_prefix=root_prefix) for c in ep["cast_used"])
        pages_imgs_html = "".join(
            f'<img src="{root_prefix}{html.escape(p)}" alt="EP.{ep["episode_number"]} 페이지 {pi}" class="reader-page-img" loading="lazy">'
            for pi, p in enumerate(ep["page_images"], start=1)
        )
        canonical_url = html.escape(ep["canonical_url"])

        prev_link_html = (
            f'<a class="nav-ep-card" href="{root_prefix}episodes/{html.escape(prev_ep["episode_id"])}.html">'
            f'<div class="nav-ep-thumb-wrap">'
            f'<img src="{root_prefix}{html.escape(prev_ep["thumb_image"])}" alt="EP.{prev_ep["episode_number"]} {html.escape(prev_ep["title"])}" class="nav-ep-thumb" loading="lazy">'
            f'</div>'
            f'<div class="nav-ep-info">'
            f'<span class="nav-ep-dir">← 이전 화 정주행</span>'
            f'<strong class="nav-ep-title">EP.{prev_ep["episode_number"]} {html.escape(prev_ep["title"])}</strong>'
            f'<span class="nav-ep-sub">{html.escape(prev_ep["subtitle"])}</span>'
            f'</div>'
            f'</a>'
            if prev_ep
            else '<div class="nav-ep-card is-disabled"><div class="nav-ep-info"><span class="nav-ep-dir">← 이전 화</span><span class="nav-ep-title">첫 번째 에피소드입니다</span><span class="nav-ep-sub">지금 1화부터 정주행 중이에요!</span></div></div>'
        )
        next_link_html = (
            f'<a class="nav-ep-card nav-ep-next" href="{root_prefix}episodes/{html.escape(next_ep["episode_id"])}.html">'
            f'<div class="nav-ep-info">'
            f'<span class="nav-ep-dir nav-ep-dir-accent">다음 화 바로 보기 →</span>'
            f'<strong class="nav-ep-title">EP.{next_ep["episode_number"]} {html.escape(next_ep["title"])}</strong>'
            f'<span class="nav-ep-sub">{html.escape(next_ep["subtitle"])}</span>'
            f'</div>'
            f'<div class="nav-ep-thumb-wrap">'
            f'<img src="{root_prefix}{html.escape(next_ep["thumb_image"])}" alt="EP.{next_ep["episode_number"]} {html.escape(next_ep["title"])}" class="nav-ep-thumb" loading="lazy">'
            f'</div>'
            f'</a>'
            if next_ep
            else '<div class="nav-ep-card nav-ep-next is-disabled"><div class="nav-ep-info"><span class="nav-ep-dir">다음 화 →</span><span class="nav-ep-title">가장 최신 에피소드입니다</span><span class="nav-ep-sub">랜덤 화 보기로 다른 명장면도 즐겨보세요!</span></div></div>'
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
            <button type="button" class="mode-btn is-active" data-mode="full">통합 스크롤</button>
            <button type="button" class="mode-btn" data-mode="pages">페이지별 보기</button>
          </div>
          <div class="reader-top-actions">
            {jump_select_html}
            <button type="button" class="btn btn-sm btn-outline js-share-url" data-share-url="{canonical_url}">🔗 링크 복사</button>
          </div>
        </div>

        <header class="episode-header">
          <div class="meta-row center-row">
            <span class="ep-pill" id="epBadge">EP.{ep['episode_number']} · #{html.escape(ep['source_post_no'])}</span>
            <span class="meta-date" id="epDate">{html.escape(ep['date_short'])}</span>
            <span class="stat-pill" id="epCuts">{ep['cut_count']}컷 상황극</span>
          </div>
          <h1 class="episode-title" id="epTitle">{html.escape(ep['title'])}</h1>
          <p class="episode-sub" id="epSub">{html.escape(ep['subtitle'])}</p>
          <div class="chip-row center-row" id="epCastRow">{cast_chips}</div>
          <div class="source-bar">
            <a id="epSourceLink" class="source-link" href="{html.escape(ep['source_url'])}" target="_blank" rel="noopener noreferrer">
              원본 디시 WOW 포에버 마이너 갤러리 개념글 (#{html.escape(ep['source_post_no'])}) 바로가기 ↗
            </a>
          </div>
        </header>

        <section class="comic-stage" aria-label="웹툰 본문">
          <div id="readerFullView" class="reader-full-view">
            <img id="epFullImg" src="{root_prefix}{html.escape(ep['full_image'])}" alt="와우 포에버 슬롭툰 EP.{ep['episode_number']} {html.escape(ep['title'])} 통합본" class="reader-full-img">
          </div>
          <div id="readerPagesView" class="reader-pages-view" hidden>
            {pages_imgs_html}
          </div>
        </section>

        <aside class="slop-sponsor-slot" data-slot="episode-strip-bottom" aria-label="스폰서 영역"></aside>

        <section class="episode-action-strip" aria-label="공유 및 다음 정주행">
          <div class="action-strip-copy">
            <strong>이 념글 상황극, 재밌게 보셨나요?</strong>
            <span>링크를 복사해 공유하거나 랜덤 화로 바로 이어서 정주행해 보세요!</span>
          </div>
          <div class="action-strip-btns">
            <button type="button" id="shareCopyBtn" class="btn btn-outline btn-sm js-share-url" data-share-url="{canonical_url}">🔗 링크 복사</button>
            <button type="button" id="bottomRandomBtn" class="btn btn-sky btn-sm js-random-ep">🎲 랜덤 화 보기</button>
            <a id="epBottomSourceLink" class="btn btn-subtle btn-sm" href="{html.escape(ep['source_url'])}" target="_blank" rel="noopener noreferrer">원본 개념글 ↗</a>
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
            <a class="btn btn-subtle btn-sm" href="{root_prefix}index.html">전체 아카이브 →</a>
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
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
  <link rel="stylesheet" href="{root_prefix}assets/style.css">
</head>
<body data-page="episode">
  {_render_nav('home', root_prefix=root_prefix)}

  <main class="container reader-container" id="episodeRoot">
    {reader_initial_html}
  </main>

  {_render_footer(total_episodes, root_prefix=root_prefix)}

  <script>window.__SLOPTOON_DATA__ = {embedded_data};</script>
  <script src="{root_prefix}assets/app.js"></script>
</body>
</html>
"""


def _render_cast_html(
    cast_payload: list[dict[str, Any]],
    site_episodes: list[dict[str, Any]],
    has_labeled_sheet: bool,
    has_clean_sheet: bool,
    *,
    base_url: str = DEFAULT_ARCHIVE_BASE_URL,
) -> str:
    total_episodes = len(site_episodes)
    page_title = f"9×9 캐스트 도감 (시안 C) — {SITE_NAME}"
    page_desc = "와우 포에버 슬롭툰 공식 확정 시안 C 9종족×9직업 귀염뽀짝 미소녀 캐릭터 도감"

    ep_by_cast: dict[str, list[dict[str, Any]]] = {c["name"]: [] for c in cast_payload}
    for ep in reversed(site_episodes):
        for name in ep["cast_used"]:
            ep_by_cast.setdefault(name, []).append(ep)

    sheet_buttons = ""
    if has_labeled_sheet and has_clean_sheet:
        sheet_buttons = """
        <div class="reader-mode-toggle" role="group" aria-label="캐스트 시트 버전">
          <button type="button" class="mode-btn is-active" data-sheet="assets/cast/cast_sheet_c_labeled.png">라벨 공식 시트</button>
          <button type="button" class="mode-btn" data-sheet="assets/cast/cast_sheet_c.jpg">클린 원화 시트</button>
        </div>
        """

    sheet_src = (
        "assets/cast/cast_sheet_c_labeled.png"
        if has_labeled_sheet
        else ("assets/cast/cast_sheet_c.jpg" if has_clean_sheet else "")
    )
    og_image_rel = sheet_src or (site_episodes[-1]["thumb_image"] if site_episodes else "")
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
        <section class="cast-sheet-section" aria-label="공식 시안 C 전체 시트">
          <div class="section-head">
            <div>
              <h2 class="section-title">공식 시안 C 전체 캐릭터 시트</h2>
              <p class="section-meta">이미지를 클릭하면 원본 고해상도로 확대해서 감상할 수 있습니다.</p>
            </div>
            {sheet_buttons}
          </div>
          <div class="cast-sheet-frame">
            <img id="castSheetImg" src="{html.escape(sheet_src)}" alt="와우 포에버 슬롭툰 공식 시안 C 9종족 9직업 전원 미소녀 캐릭터 시트" class="cast-sheet-img">
          </div>
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
            appearances_html = '<p class="cast-ep-empty">곧 새로운 개념글 상황극으로 등판 예정!</p>'

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
                f'<img src="{t_src}" alt="{html.escape(c["name"])} 정면 측면 후면 3면 턴어라운드 도면" '
                f'class="cast-turnaround-img" loading="lazy" decoding="async">'
                f'<span class="cast-turnaround-caption">3면 턴어라운드 도면 (클릭 확대)</span>'
                f'</button>'
                f'</div>'
            )

        cards_parts.append(
            f"""
            <article class="cast-card" id="{html.escape(c['id'])}">
              <div class="cast-card-accent" style="background:linear-gradient(90deg, {html.escape(c['color_hex'])}, {html.escape(c['accent_hex'])});"></div>
              <div class="cast-card-top">
                <div class="cast-avatar-wrap">
                  {avatar_html}
                  <span class="cast-num">0{idx}</span>
                </div>
                <div class="cast-identity">
                  <div class="meta-row">
                    <span class="cast-race-pill" style="border-color:{html.escape(c['color_hex'])};">
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
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
  <link rel="stylesheet" href="assets/style.css">
</head>
<body data-page="cast">
  {_render_nav('cast')}

  <main class="container main-content">
    <section class="masthead">
      <div class="pill-badge">
        <span class="dot-sky"></span>공식 확정 시안 C · 초귀염 팝·개그 웹툰 특화형
      </div>
      <h1 class="masthead-title">전원 미소녀 9×9 캐스트 도감</h1>
      <p class="masthead-sub">오크·언데드·노움·드워프·트롤·타우렌·나이트엘프·인간·스카이본 — 포에버갤 상황극을 책임지는 9종족×9직업 고정 멤버를 소개합니다.</p>
    </section>

    <hr class="ink-divider">

    {sheet_section}

    <section class="cast-grid-section" aria-label="9명 캐릭터 프로필">
      <div class="section-head">
        <div>
          <h2 class="section-title">캐릭터별 프로필 ({len(cast_payload)}명)</h2>
          <p class="section-meta">각 캐릭터를 클릭하면 출연 에피소드 바로가기 및 아카이브 필터링이 가능합니다.</p>
        </div>
      </div>
      <div class="cast-grid">
        {''.join(cards_parts)}
      </div>
    </section>
  </main>

  <div id="lightbox" class="lightbox" hidden aria-modal="true" role="dialog" aria-label="이미지 확대 보기">
    <button type="button" id="lightboxClose" class="lightbox-close" aria-label="닫기">✕</button>
    <img id="lightboxImg" src="" alt="확대 이미지" class="lightbox-img">
  </div>

  {_render_footer(total_episodes)}

  <script>window.__SLOPTOON_DATA__ = {embedded_data};</script>
  <script src="assets/app.js"></script>
</body>
</html>
"""


def _render_publish_html(
    site_episodes: list[dict[str, Any]],
) -> str:
    """Render `publish.html` — Creator DCInside manual upload queue manager."""
    total_episodes = len(site_episodes)
    newest_first = list(reversed(site_episodes))
    page_title = f"업로드 큐 관리 — {SITE_NAME}"

    if newest_first:
        queue_items_parts: list[str] = []
        for ep in newest_first:
            ep_id = html.escape(ep["episode_id"])
            ep_href = f"episodes/{ep_id}.html"
            queue_items_parts.append(
                f"""
                <article class="publish-card" data-episode-id="{ep_id}" data-status="pending">
                  <div class="publish-card-main">
                    <a class="publish-thumb-link" href="{ep_href}">
                      <img src="{html.escape(ep['thumb_image'])}" alt="EP.{ep['episode_number']} {html.escape(ep['title'])}" class="publish-thumb" loading="lazy">
                    </a>
                    <div class="publish-info">
                      <div class="publish-top-row">
                        <div class="meta-row">
                          <span class="ep-pill ep-pill-sm">EP.{ep['episode_number']}</span>
                          <span class="post-no">#{html.escape(ep['source_post_no'])}</span>
                          <span class="meta-date">{html.escape(ep['date_short'])}</span>
                          <span class="stat-pill">{ep['cut_count']}컷</span>
                        </div>
                        <button type="button" class="publish-status-toggle" data-ep="{ep_id}" aria-pressed="false">
                          <span class="status-dot" aria-hidden="true"></span>
                          <span class="status-label">대기 중</span>
                        </button>
                      </div>
                      <h2 class="publish-ep-title">
                        <a href="{ep_href}">{html.escape(ep['title'])}</a>
                      </h2>
                      <p class="publish-ep-sub">{html.escape(ep['subtitle'])}</p>
                      <div class="publish-meta-links">
                        <a href="{ep_href}">아카이브 페이지 열기 →</a>
                        <a href="{html.escape(ep['source_url'])}" target="_blank" rel="noopener noreferrer">원본 개념글 (#{html.escape(ep['source_post_no'])}) ↗</a>
                      </div>
                      <div class="publish-actions">
                        <button type="button" class="btn btn-outline btn-sm js-pub-copy-title" data-ep="{ep_id}">제목 복사</button>
                        <button type="button" class="btn btn-outline btn-sm js-pub-copy-body" data-ep="{ep_id}">본문·주소 복사</button>
                        <a class="btn btn-outline btn-sm" href="{html.escape(ep['full_image'])}" download="wow_sloptoon_{ep_id}_full.jpg">워터마크 통합본 JPG 저장</a>
                        <a class="btn btn-primary btn-sm" href="{DC_GALLERY_WRITE_URL}" target="_blank" rel="noopener noreferrer">포에버갤 글쓰기 열기 ↗</a>
                      </div>
                    </div>
                  </div>
                  <details class="publish-preview-details">
                    <summary>복사될 제목 · 본문 미리보기</summary>
                    <div class="dc-preview-grid">
                      <div class="dc-preview-box">
                        <div class="dc-preview-label">글 제목</div>
                        <pre class="dc-preview-text">{html.escape(ep['dc_title'])}</pre>
                      </div>
                      <div class="dc-preview-box">
                        <div class="dc-preview-label">본문 &amp; 정주행 아카이브 주소</div>
                        <pre class="dc-preview-text">{html.escape(ep['dc_body'])}</pre>
                      </div>
                    </div>
                  </details>
                </article>
                """
            )
        queue_html = f'<div class="publish-list" id="publishList">{"".join(queue_items_parts)}</div>'
    else:
        queue_html = """
        <section class="empty-hero">
          <p>아직 생성된 에피소드가 없습니다. 새 에피소드를 빌드하면 업로드 큐에 자동 표시됩니다.</p>
        </section>
        """

    embedded_data = _safe_json_for_script({
        "episodes": site_episodes,
        "rootPrefix": "",
        "dcWriteUrl": DC_GALLERY_WRITE_URL,
    })

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="noindex, nofollow">
  <title>{html.escape(page_title)}</title>
  <meta name="description" content="와우 포에버 슬롭툰 디시 WOW 포에버 마이너 갤러리 수동 업로드 큐 관리 페이지">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
  <link rel="stylesheet" href="assets/style.css">
</head>
<body data-page="publish">
  {_render_nav('publish')}

  <main class="container main-content">
    <section class="masthead">
      <div class="pill-badge">
        <span class="dot-sky"></span>CREATOR UPLOAD QUEUE · 수동 업로드 도우미
      </div>
      <h1 class="masthead-title">포에버갤 업로드 큐 관리</h1>
      <p class="masthead-sub">최신 에피소드부터 제목·본문 복사, 워터마크 통합본 JPG 저장, 공식 포에버갤 글쓰기 열기 및 등록 상태를 브라우저에서 간편하게 관리합니다.</p>
      <p class="publish-policy-note">
        ※ 디시인사이드 정책 준수: 로그인, 이미지 첨부, 캡차(자동등록방지) 확인 및 최종 등록은 공식 포에버갤 글쓰기 페이지에서 직접 진행해 주세요. 등록 완료 상태는 현재 브라우저(localStorage)에 안전하게 저장됩니다.
      </p>
    </section>

    <hr class="ink-divider">

    <section class="publish-controls" aria-label="업로드 상태 필터">
      <div class="publish-filter-bar" id="publishFilterBar" role="group" aria-label="상태별 필터">
        <button type="button" class="filter-chip is-active" data-filter="all">전체 <span class="filter-count" id="pubCountAll">{total_episodes}</span></button>
        <button type="button" class="filter-chip" data-filter="pending">대기 중 <span class="filter-count" id="pubCountPending">{total_episodes}</span></button>
        <button type="button" class="filter-chip" data-filter="done">완료 <span class="filter-count" id="pubCountDone">0</span></button>
      </div>
      <p class="section-meta" id="publishSummary">전체 {total_episodes}화 중 0화 포에버갤 등록 완료</p>
    </section>

    {queue_html}

    <div class="empty-filter" id="publishEmptyFilter" hidden>
      <p class="empty-filter-title">선택한 상태에 해당하는 에피소드가 없습니다.</p>
      <p class="empty-filter-sub">다른 필터 탭을 선택해 전체 에피소드를 확인해 보세요.</p>
      <button type="button" id="publishResetFilterBtn" class="btn btn-outline">전체 보기</button>
    </div>
  </main>

  {_render_footer(total_episodes)}

  <script>window.__SLOPTOON_DATA__ = {embedded_data};</script>
  <script src="assets/app.js"></script>
</body>
</html>
"""


_STYLE_CSS = """/* 와우 포에버 슬롭툰 — 순백(#FFFFFF) 초고속 정적 웹 아카이브 스타일 */
:root {
  --bg: #ffffff;
  --surface: #f8fafc;
  --surface-2: #f1f5f9;
  --ink: #111111;
  --ink-muted: #52525b;
  --ink-soft: #71717a;
  --border: #e4e4e7;
  --border-strong: #111111;
  --navy: #1e3a8a;
  --sky: #0ea5e9;
  --sky-dark: #0284c7;
  --sky-soft: #f0f9ff;
  --sky-border: #bae6fd;
  --radius-sm: 10px;
  --radius-md: 16px;
  --radius-lg: 22px;
  --shadow-comic: 4px 4px 0 #111111;
  --shadow-comic-lg: 6px 6px 0 #111111;
  --font-sans: "Pretendard", "Noto Sans KR", "Malgun Gothic", -apple-system, BlinkMacSystemFont, sans-serif;
}

*, *::before, *::after { box-sizing: border-box; }
html { scroll-behavior: smooth; background: var(--bg); }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: var(--font-sans);
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
}
a { color: inherit; text-decoration: none; }
img { display: block; max-width: 100%; height: auto; }
button, input { font-family: inherit; }

.container {
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 20px;
}

/* Sticky minimal white header */
.site-header {
  position: sticky;
  top: 0;
  z-index: 40;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(10px);
  border-bottom: 1.5px solid var(--border);
}
.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 62px;
  padding-top: 6px;
  padding-bottom: 6px;
}
.brand {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  font-weight: 800;
  font-size: 1.05rem;
  letter-spacing: -0.02em;
  flex-shrink: 0;
}
.brand-dot {
  width: 11px;
  height: 11px;
  border-radius: 999px;
  background: var(--ink);
  box-shadow: 0 0 0 3px var(--sky);
}
.brand-tag {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  padding: 2px 7px;
  border: 1.5px solid var(--ink);
  border-radius: 999px;
  background: var(--bg);
}
.site-nav {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}
.nav-link {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--ink-muted);
  padding: 7px 13px;
  border-radius: 999px;
  transition: background 0.15s ease, color 0.15s ease;
}
.nav-link:hover { background: var(--surface-2); color: var(--ink); }
.nav-link.is-active { background: var(--ink); color: #ffffff; }
.nav-ext { border: 1px solid var(--border); }
.nav-pill-random {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.86rem;
  font-weight: 800;
  color: var(--ink);
  background: #ffffff;
  border: 1.5px solid var(--ink);
  border-radius: 999px;
  padding: 6px 13px;
  cursor: pointer;
  transition: transform 0.14s ease, box-shadow 0.14s ease, background 0.14s ease, border-color 0.14s ease;
}
.nav-pill-random:hover {
  background: var(--sky-soft);
  border-color: var(--sky);
  color: var(--sky-dark);
  transform: translate(-1px, -1px);
  box-shadow: 2px 2px 0 var(--sky);
}

/* Editorial masthead matching comic header */
.main-content { padding-top: 38px; padding-bottom: 72px; }
.masthead { text-align: center; padding: 8px 0 26px; }
.pill-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--ink);
  color: #ffffff;
  font-size: 0.84rem;
  font-weight: 700;
  padding: 7px 18px;
  border-radius: 999px;
  letter-spacing: -0.01em;
}
.pill-sm { font-size: 0.74rem; padding: 5px 12px; }
.dot-sky {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--sky);
  display: inline-block;
  flex-shrink: 0;
}
.masthead-title {
  margin: 16px 0 10px;
  font-size: clamp(2rem, 4.8vw, 3.15rem);
  font-weight: 900;
  letter-spacing: -0.04em;
  line-height: 1.12;
}
.masthead-sub {
  margin: 0 auto;
  max-width: 640px;
  color: var(--ink-muted);
  font-size: 1rem;
  word-break: keep-all;
}
.masthead-stats {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 18px;
}
.stat-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--ink-muted);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 4px 12px;
}
.ink-divider {
  border: 0;
  height: 2px;
  background: var(--ink);
  margin: 0 0 34px;
}

/* Shared pills & buttons */
.ep-pill {
  display: inline-flex;
  align-items: center;
  font-size: 0.84rem;
  font-weight: 800;
  color: var(--navy);
  background: #ffffff;
  border: 2px solid var(--navy);
  border-radius: 999px;
  padding: 4px 13px;
  letter-spacing: -0.01em;
}
.ep-pill-sm { font-size: 0.76rem; padding: 2px 10px; border-width: 1.5px; }
.meta-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.center-row { justify-content: center; }
.meta-date, .post-no { font-size: 0.82rem; color: var(--ink-soft); font-weight: 600; }

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  font-weight: 700;
  font-size: 0.92rem;
  padding: 11px 18px;
  border-radius: 12px;
  border: 2px solid var(--ink);
  cursor: pointer;
  transition: transform 0.14s ease, box-shadow 0.14s ease, background 0.14s ease, border-color 0.14s ease;
}
.btn:hover { transform: translate(-1px, -1px); }
.btn-primary {
  background: var(--ink);
  color: #ffffff;
  box-shadow: 3px 3px 0 var(--sky);
}
.btn-primary:hover { box-shadow: 4px 4px 0 var(--sky); }
.btn-sky {
  background: var(--sky);
  color: #ffffff;
  border-color: var(--ink);
  box-shadow: 3px 3px 0 var(--ink);
}
.btn-sky:hover { background: var(--sky-dark); box-shadow: 4px 4px 0 var(--ink); }
.btn-outline { background: #ffffff; color: var(--ink); }
.btn-outline:hover { background: var(--surface); box-shadow: 3px 3px 0 var(--ink); }
.btn-subtle { background: var(--surface); border-color: var(--border); color: var(--ink); }
.btn-subtle:hover { border-color: var(--ink); }
.btn-sm { font-size: 0.82rem; padding: 7px 13px; border-radius: 10px; border-width: 1.5px; }
.btn-lg { font-size: 0.98rem; padding: 14px 22px; width: 100%; }

/* Collapsible sponsor / ad slot — zero-height & invisible when empty */
.slop-sponsor-slot {
  width: 100%;
  max-width: 900px;
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

/* Hero featured latest card */
.hero-section { margin-bottom: 48px; }
.hero-card {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
  background: var(--bg);
  border: 2px solid var(--border-strong);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-comic-lg);
}
.hero-thumb-link {
  position: relative;
  display: block;
  background: #ffffff;
  border-right: 2px solid var(--border-strong);
  overflow: hidden;
}
.hero-thumb {
  width: 100%;
  height: 100%;
  min-height: 290px;
  object-fit: contain;
  background: #ffffff;
  transition: transform 0.25s ease;
}
.hero-thumb-link:hover .hero-thumb { transform: scale(1.025); }
.thumb-flag {
  position: absolute;
  top: 14px;
  left: 14px;
  background: var(--ink);
  color: #ffffff;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  padding: 5px 11px;
  border-radius: 999px;
}
.thumb-cuts {
  position: absolute;
  bottom: 12px;
  right: 12px;
  background: rgba(255, 255, 255, 0.95);
  color: var(--ink);
  border: 1.5px solid var(--ink);
  font-size: 0.74rem;
  font-weight: 800;
  padding: 3px 10px;
  border-radius: 999px;
}
.hero-body {
  padding: 28px 30px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 14px;
}
.hero-title {
  margin: 0;
  font-size: clamp(1.45rem, 2.5vw, 1.95rem);
  font-weight: 900;
  letter-spacing: -0.03em;
  line-height: 1.25;
  word-break: keep-all;
}
.hero-title a:hover { text-decoration: underline; text-underline-offset: 4px; }
.hero-sub {
  margin: 0;
  color: var(--ink-muted);
  font-size: 0.97rem;
  word-break: keep-all;
}
.hero-actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 4px; }

/* Cast chips */
.chip-row { display: flex; flex-wrap: wrap; gap: 7px; }
.cast-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  font-weight: 700;
  padding: 4px 11px;
  border-radius: 999px;
  background: var(--surface);
  border: 1px solid var(--border);
  transition: border-color 0.15s ease, transform 0.15s ease;
}
.cast-chip:hover { border-color: var(--ink); transform: translateY(-1px); }
.cast-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  display: inline-block;
  flex-shrink: 0;
}

/* Search & filter controls */
.section-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 14px;
  margin-bottom: 18px;
}
.section-title {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 900;
  letter-spacing: -0.03em;
}
.section-meta { margin: 4px 0 0; font-size: 0.86rem; color: var(--ink-soft); }
.controls-right { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.search-box { position: relative; }
.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--ink-soft);
  font-size: 1rem;
  pointer-events: none;
}
.search-input {
  width: 260px;
  max-width: 100%;
  padding: 9px 14px 9px 34px;
  border: 1.5px solid var(--border);
  border-radius: 12px;
  font-size: 0.88rem;
  background: #ffffff;
  color: var(--ink);
  outline: none;
  transition: border-color 0.15s ease;
}
.search-input:focus { border-color: var(--ink); }

.cast-filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-bottom: 24px;
}
.filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #ffffff;
  color: var(--ink-muted);
  border: 1.5px solid var(--border);
  border-radius: 999px;
  padding: 6px 13px;
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.14s ease;
}
.filter-chip:hover { border-color: var(--ink); color: var(--ink); }
.filter-chip.is-active { background: var(--ink); border-color: var(--ink); color: #ffffff; }
.filter-count {
  font-size: 0.72rem;
  opacity: 0.75;
}

/* Episode card grid */
.episode-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
  gap: 22px;
}
.ep-card {
  background: #ffffff;
  border: 1.8px solid var(--ink);
  border-radius: var(--radius-md);
  overflow: hidden;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}
.ep-card:hover {
  transform: translate(-2px, -3px);
  box-shadow: var(--shadow-comic);
}
.ep-card-link { display: flex; flex-direction: column; height: 100%; }
.ep-thumb-wrap {
  position: relative;
  aspect-ratio: 16 / 10;
  background: #ffffff;
  border-bottom: 1.5px solid var(--border);
  overflow: hidden;
}
.ep-thumb {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #ffffff;
  transition: transform 0.22s ease;
}
.ep-card:hover .ep-thumb { transform: scale(1.03); }
.ep-card-body {
  padding: 16px 18px 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}
.ep-card-title {
  margin: 2px 0 0;
  font-size: 1.1rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.3;
  word-break: keep-all;
}
.ep-card-sub {
  margin: 0;
  font-size: 0.87rem;
  color: var(--ink-muted);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: keep-all;
}
.mini-chip-row { display: flex; flex-wrap: wrap; gap: 5px; margin-top: auto; padding-top: 6px; }
.mini-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.74rem;
  font-weight: 600;
  color: var(--ink-muted);
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 2px 8px;
  border-radius: 999px;
}

.empty-filter, .empty-hero {
  text-align: center;
  padding: 52px 20px;
  border: 1.5px dashed var(--border);
  border-radius: var(--radius-md);
  background: var(--surface);
}
.empty-filter-title { margin: 0 0 6px; font-weight: 800; font-size: 1.05rem; }
.empty-filter-sub { margin: 0 0 16px; color: var(--ink-muted); font-size: 0.9rem; }

.archive-load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 28px;
}
.archive-load-more[hidden] { display: none; }

.ep-jump-select {
  max-width: 220px;
  padding: 6px 10px;
  border: 1.5px solid var(--border);
  border-radius: 10px;
  background: #ffffff;
  color: var(--ink);
  font-family: inherit;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
}
.ep-jump-select:focus { outline: none; border-color: var(--ink); }

.cast-ep-more {
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--ink-soft);
  padding-top: 2px;
}

.back-to-top {
  position: fixed;
  right: 22px;
  bottom: 24px;
  z-index: 60;
  background: #ffffff;
  color: var(--ink);
  border: 1.8px solid var(--ink);
  border-radius: 999px;
  padding: 8px 14px;
  font-size: 0.82rem;
  font-weight: 800;
  cursor: pointer;
  box-shadow: 3px 3px 0 var(--ink);
  transition: transform 0.14s ease, box-shadow 0.14s ease, background 0.14s ease;
}
.back-to-top:hover {
  background: var(--sky-soft);
  transform: translate(-1px, -1px);
  box-shadow: 4px 4px 0 var(--sky);
}
.back-to-top[hidden] { display: none; }

/* Episode Reader page */
.reader-container {
  max-width: 940px;
  padding-top: 22px;
  padding-bottom: 72px;
}
.reader-top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--border);
}
.reader-top-actions {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.back-link { font-weight: 700; font-size: 0.9rem; color: var(--ink-muted); }
.back-link:hover { color: var(--ink); }
.reader-mode-toggle {
  display: inline-flex;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 3px;
  gap: 3px;
}
.mode-btn {
  border: 0;
  background: transparent;
  color: var(--ink-muted);
  font-size: 0.8rem;
  font-weight: 700;
  padding: 6px 13px;
  border-radius: 999px;
  cursor: pointer;
}
.mode-btn.is-active { background: var(--ink); color: #ffffff; }

.episode-header { text-align: center; padding: 28px 0 22px; }
.episode-title {
  margin: 12px 0 8px;
  font-size: clamp(1.6rem, 3.8vw, 2.3rem);
  font-weight: 900;
  letter-spacing: -0.03em;
  word-break: keep-all;
}
.episode-sub { margin: 0 0 14px; color: var(--ink-muted); font-size: 0.98rem; word-break: keep-all; }
.source-bar { margin-top: 14px; }
.source-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.84rem;
  font-weight: 700;
  color: var(--sky-dark);
  padding: 6px 14px;
  border-radius: 999px;
  background: var(--sky-soft);
  border: 1px solid var(--sky-border);
}
.source-link:hover { background: #e0f2fe; }

.comic-stage {
  background: #ffffff;
  margin: 12px auto 28px;
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
.reader-pages-view { display: flex; flex-direction: column; gap: 28px; }
.reader-pages-view[hidden], .reader-full-view[hidden] { display: none; }
.reader-page-img {
  border: 1px solid var(--border);
  border-radius: 10px;
}

/* Post-comic Share & Random Binge Strip */
.episode-action-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 14px;
  padding: 18px 22px;
  background: #ffffff;
  border: 1.8px solid var(--ink);
  border-radius: var(--radius-md);
  box-shadow: 3px 3px 0 var(--sky);
  margin-bottom: 24px;
}
.action-strip-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.action-strip-copy strong {
  font-size: 0.98rem;
  font-weight: 900;
  letter-spacing: -0.02em;
}
.action-strip-copy span {
  font-size: 0.83rem;
  color: var(--ink-muted);
  word-break: keep-all;
}
.action-strip-btns {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

/* Sleek Prev / Next Episode Binge Cards */
.episode-pager {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 42px;
}
.nav-ep-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border: 1.8px solid var(--ink);
  border-radius: var(--radius-md);
  background: #ffffff;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}
.nav-ep-card:not(.is-disabled):hover {
  transform: translate(-2px, -2px);
  box-shadow: var(--shadow-comic);
}
.nav-ep-card.is-disabled {
  border-color: var(--border);
  color: var(--ink-soft);
  background: var(--surface);
}
.nav-ep-next {
  justify-content: flex-end;
  text-align: right;
}
.nav-ep-thumb-wrap {
  width: 108px;
  height: 70px;
  flex-shrink: 0;
  border: 1.5px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  background: #ffffff;
}
.nav-ep-thumb {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #ffffff;
}
.nav-ep-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
  flex: 1;
}
.nav-ep-dir { font-size: 0.76rem; font-weight: 800; color: var(--ink-soft); }
.nav-ep-dir-accent { color: var(--sky-dark); }
.nav-ep-title { font-size: 0.98rem; font-weight: 900; line-height: 1.25; word-break: keep-all; }
.nav-ep-sub {
  font-size: 0.8rem;
  color: var(--ink-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Recommended "다른 레전드 념글 만화" Grid */
.recommend-section {
  margin-bottom: 42px;
}
.recommend-section[hidden] { display: none; }
.recommend-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 18px;
}

/* Cast page */
.cast-sheet-section { margin-bottom: 46px; }
.cast-sheet-frame {
  border: 2px solid var(--ink);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: #ffffff;
  box-shadow: var(--shadow-comic);
  cursor: zoom-in;
}
.cast-sheet-img { width: 100%; height: auto; background: #ffffff; }
.cast-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
  gap: 20px;
}
.cast-card {
  border: 1.8px solid var(--ink);
  border-radius: var(--radius-md);
  background: #ffffff;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.cast-card:hover { transform: translate(-2px, -2px); box-shadow: var(--shadow-comic); }
.cast-card-accent { height: 6px; width: 100%; }
.cast-card-top {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px 10px;
}
.cast-avatar-wrap {
  position: relative;
  width: 86px;
  height: 86px;
  flex-shrink: 0;
  border: 1.5px solid var(--ink);
  border-radius: 14px;
  overflow: hidden;
  background: #ffffff;
}
.cast-avatar { width: 100%; height: 100%; object-fit: contain; background: #ffffff; }
.cast-avatar-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-weight: 900;
  font-size: 1.4rem;
}
.cast-num {
  position: absolute;
  top: 4px;
  left: 5px;
  font-size: 0.65rem;
  font-weight: 900;
  background: rgba(255, 255, 255, 0.9);
  padding: 1px 5px;
  border-radius: 6px;
}
.cast-identity { min-width: 0; }
.cast-race-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.74rem;
  font-weight: 700;
  border: 1.5px solid var(--border);
  border-radius: 999px;
  padding: 2px 9px;
}
.cast-name { margin: 5px 0 2px; font-size: 1.12rem; font-weight: 900; letter-spacing: -0.02em; }
.cast-role { margin: 0; font-size: 0.83rem; font-weight: 700; color: var(--navy); }
.cast-bio {
  margin: 0;
  padding: 4px 18px 12px;
  font-size: 0.87rem;
  color: var(--ink-muted);
  word-break: keep-all;
}
.cast-turnaround-wrap { padding: 0 18px 12px; }
.cast-turnaround-btn {
  display: block;
  width: 100%;
  padding: 6px;
  border: 1.5px solid var(--border);
  border-radius: 10px;
  background: #ffffff;
  cursor: zoom-in;
  text-align: center;
  transition: border-color 0.15s ease, transform 0.15s ease;
}
.cast-turnaround-btn:hover { border-color: var(--ink); transform: translateY(-1px); }
.cast-turnaround-img {
  display: block;
  width: 100%;
  height: auto;
  border-radius: 6px;
  background: #ffffff;
}
.cast-turnaround-caption {
  display: block;
  margin-top: 5px;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--ink-soft);
}
.alias-row { display: flex; flex-wrap: wrap; gap: 5px; padding: 0 18px 14px; }
.alias-tag {
  font-size: 0.73rem;
  color: var(--ink-soft);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 2px 8px;
}
.cast-card-foot {
  margin-top: auto;
  padding: 12px 18px 16px;
  border-top: 1px solid var(--border);
  background: var(--surface);
}
.cast-foot-label { font-size: 0.74rem; font-weight: 800; color: var(--ink-soft); margin-bottom: 6px; }
.cast-ep-list { display: flex; flex-direction: column; gap: 5px; margin-bottom: 10px; }
.ep-mini-link {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ep-mini-link:hover { color: var(--navy); text-decoration: underline; }
.cast-ep-empty { margin: 0 0 8px; font-size: 0.8rem; color: var(--ink-soft); }
.cast-filter-link { font-size: 0.8rem; font-weight: 800; color: var(--navy); }
.cast-filter-link:hover { text-decoration: underline; }

/* Lightbox modal */
.lightbox {
  position: fixed;
  inset: 0;
  z-index: 80;
  background: rgba(17, 17, 17, 0.88);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.lightbox[hidden] { display: none; }
.lightbox-img {
  max-width: 96vw;
  max-height: 92vh;
  border-radius: 12px;
  background: #ffffff;
}
.lightbox-close {
  position: fixed;
  top: 18px;
  right: 22px;
  width: 42px;
  height: 42px;
  border-radius: 999px;
  border: 0;
  background: #ffffff;
  color: var(--ink);
  font-size: 1.15rem;
  font-weight: 900;
  cursor: pointer;
}

/* Pure-White Footer, Legal Notice & Toast */
.site-footer {
  border-top: 1.5px solid var(--border);
  background: #ffffff;
  padding: 34px 0 38px;
}
.footer-inner {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 20px;
}
.footer-desc {
  margin: 10px 0 0;
  max-width: 540px;
  font-size: 0.85rem;
  color: var(--ink-muted);
  word-break: keep-all;
}
.footer-links {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  font-size: 0.86rem;
  font-weight: 700;
  color: var(--ink-muted);
}
.footer-links a:hover { color: var(--ink); }
.footer-link-discreet {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--ink-soft);
}
.footer-link-discreet:hover { color: var(--sky-dark); }
.footer-legal {
  margin-top: 22px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}
.legal-notice {
  margin: 0;
  font-size: 0.78rem;
  line-height: 1.65;
  color: var(--ink-soft);
  word-break: keep-all;
}

.toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 90;
  background: var(--ink);
  color: #ffffff;
  font-size: 0.88rem;
  font-weight: 700;
  padding: 12px 20px;
  border-radius: 999px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.22);
  max-width: calc(100vw - 32px);
  text-align: center;
}

@media (max-width: 820px) {
  .header-inner { flex-wrap: wrap; padding-top: 10px; padding-bottom: 10px; }
  .nav-link { font-size: 0.84rem; padding: 6px 10px; }
  .nav-pill-random { font-size: 0.82rem; padding: 5px 11px; }
  .hero-card { grid-template-columns: 1fr; }
  .hero-thumb-link { border-right: 0; border-bottom: 2px solid var(--border-strong); }
  .hero-thumb { min-height: 220px; }
  .hero-body { padding: 20px; }
  .episode-pager { grid-template-columns: 1fr; }
  .nav-ep-next { text-align: left; flex-direction: row-reverse; justify-content: flex-start; }
  .nav-ep-thumb-wrap { width: 88px; height: 58px; }
  .brand-tag { display: none; }
  .search-input { width: 100%; }
  .ep-jump-select { max-width: 170px; font-size: 0.76rem; }
  .back-to-top { right: 14px; bottom: 16px; padding: 7px 12px; font-size: 0.78rem; }
}
"""


_APP_JS = """/* 와우 포에버 슬롭툰 — 정적 웹 아카이브 인터랙션 */
(function () {
  "use strict";

  var HOME_PAGE_SIZE = 24;

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
            showToast("현재 1화만 등록되어 있어요! 곧 새로운 념글 만화가 추가됩니다.");
            return;
          }
          pool = episodes;
        }
        var picked = pool[Math.floor(Math.random() * pool.length)];
        window.location.href = episodeHref(rootPrefix, picked.episode_id);
      });
    });
  }

  /* ---------------- HOME PAGE (SEARCH / FILTER / SORT / PAGINATION) ---------------- */
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

    var cards = Array.prototype.slice.call(grid.querySelectorAll(".ep-card"));
    var totalAll = cards.length;
    var activeCast = "";
    var sortOrder = "desc";
    var renderedOrder = "desc";
    var visibleLimit = HOME_PAGE_SIZE;

    // Sync initial ?cast= query parameter if linked from cast.html
    var params = new URLSearchParams(window.location.search);
    var initCast = params.get("cast");
    if (initCast && filterBar) {
      activeCast = initCast;
      var btns = filterBar.querySelectorAll(".filter-chip");
      btns.forEach(function (btn) {
        btn.classList.toggle("is-active", btn.getAttribute("data-cast") === activeCast);
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
    }
    if (filterBar) {
      filterBar.addEventListener("click", function (ev) {
        var btn = ev.target.closest(".filter-chip");
        if (!btn) return;
        activeCast = btn.getAttribute("data-cast") || "";
        visibleLimit = HOME_PAGE_SIZE;
        filterBar.querySelectorAll(".filter-chip").forEach(function (b) {
          b.classList.toggle("is-active", b === btn);
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
            b.classList.toggle("is-active", (b.getAttribute("data-cast") || "") === "");
          });
        }
        applyFilters();
      });
    }

    applyFilters();
  }

  /* ---------------- EPISODE READER, SHARE, BINGE & DC HELPER ---------------- */
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

    var link = document.createElement("a");
    link.className = "ep-card-link";
    link.href = episodeHref(rootPrefix, rec.episode_id);

    var thumbWrap = document.createElement("div");
    thumbWrap.className = "ep-thumb-wrap";
    var img = document.createElement("img");
    img.src = rootPrefix + rec.thumb_image;
    img.alt = "EP." + rec.episode_number + " " + rec.title;
    img.className = "ep-thumb";
    img.loading = "lazy";
    var cuts = document.createElement("span");
    cuts.className = "thumb-cuts";
    cuts.textContent = rec.cut_count + "컷";
    thumbWrap.appendChild(img);
    thumbWrap.appendChild(cuts);

    var body = document.createElement("div");
    body.className = "ep-card-body";
    var metaRow = document.createElement("div");
    metaRow.className = "meta-row";
    var pill = document.createElement("span");
    pill.className = "ep-pill ep-pill-sm";
    pill.textContent = "EP." + rec.episode_number;
    var postNo = document.createElement("span");
    postNo.className = "post-no";
    postNo.textContent = "#" + rec.source_post_no;
    var dt = document.createElement("span");
    dt.className = "meta-date";
    dt.textContent = rec.date_short || "";
    metaRow.appendChild(pill);
    metaRow.appendChild(postNo);
    metaRow.appendChild(dt);

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
      dot.style.background = chip.color || "#111111";
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
      hint.textContent = isNext ? "랜덤 화 보기로 다른 명장면도 즐겨보세요!" : "지금 1화부터 정주행 중이에요!";
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
    img.loading = "lazy";
    thumbWrap.appendChild(img);

    var infoBox = document.createElement("div");
    infoBox.className = "nav-ep-info";
    var dirSpan = document.createElement("span");
    dirSpan.className = isNext ? "nav-ep-dir nav-ep-dir-accent" : "nav-ep-dir";
    dirSpan.textContent = isNext ? "다음 화 바로 보기 →" : "← 이전 화 정주행";
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

    var prevEp = currentIndex > 0 ? episodes[currentIndex - 1] : null;
    var nextEp = currentIndex + 1 < episodes.length ? episodes[currentIndex + 1] : null;
    var canonicalShareUrl =
      ep.canonical_url || ((data.archiveBaseUrl || "https://slopwow.github.io").replace(/\\/+$/, "") + "/episodes/" + ep.episode_id + ".html");

    // Update DOM dynamically when ?id= differs from default SSR episode
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
      sourceEl.textContent =
        "원본 디시 WOW 포에버 마이너 갤러리 개념글 (#" + ep.source_post_no + ") 바로가기 ↗";
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
        dot.style.background = chip.color || "#111111";
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
      ep.page_images.forEach(function (rel, idx) {
        var img = document.createElement("img");
        img.src = rootPrefix + rel;
        img.alt = "EP." + ep.episode_number + " 페이지 " + (idx + 1);
        img.className = "reader-page-img";
        img.loading = "lazy";
        pagesView.appendChild(img);
      });
    }

    var titlePreview = document.getElementById("dcTitlePreview");
    if (titlePreview) titlePreview.textContent = ep.dc_title;
    var bodyPreview = document.getElementById("dcBodyPreview");
    if (bodyPreview) bodyPreview.textContent = ep.dc_body;

    var dlBtn = document.getElementById("dcDownloadBtn");
    var dlFileName = "wow_sloptoon_" + ep.episode_id + "_full.jpg";
    if (dlBtn) {
      dlBtn.href = fullSrc;
      dlBtn.setAttribute("download", dlFileName);
    }

    // Wire Share URL ("링크 복사") buttons
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

    // Update sleek Prev / Next binge cards
    var pager = document.getElementById("epPager");
    if (pager) {
      pager.innerHTML = "";
      pager.appendChild(buildBingeCardEl(prevEp, false, rootPrefix));
      pager.appendChild(buildBingeCardEl(nextEp, true, rootPrefix));
    }

    // Update "다른 레전드 념글 만화" recommended episode grid (up to 3)
    var recSection = document.getElementById("epRecommendSection");
    var recGrid = document.getElementById("epRecommendGrid");
    if (recSection && recGrid) {
      var recs = selectRecommended(episodes, currentIndex, 3);
      recGrid.innerHTML = "";
      if (recs.length > 0) {
        recs.forEach(function (rec) {
          recGrid.appendChild(buildRecommendCardEl(rec, rootPrefix));
        });
        recSection.hidden = false;
      } else {
        recSection.hidden = true;
      }
    }

    // View mode switch (full vertical scroll vs page-by-page)
    var fullView = document.getElementById("readerFullView");
    document.querySelectorAll(".mode-btn[data-mode]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var mode = btn.getAttribute("data-mode");
        document.querySelectorAll(".mode-btn[data-mode]").forEach(function (b) {
          b.classList.toggle("is-active", b === btn);
        });
        if (fullView) fullView.hidden = mode !== "full";
        if (pagesView) pagesView.hidden = mode !== "pages";
      });
    });

    // Wire quick episode jump dropdown
    var jumpSelect = document.getElementById("epJumpSelect");
    if (jumpSelect) {
      jumpSelect.value = ep.episode_id;
      jumpSelect.addEventListener("change", function () {
        if (jumpSelect.value && jumpSelect.value !== ep.episode_id) {
          window.location.href = episodeHref(rootPrefix, jumpSelect.value);
        }
      });
    }

    // Keyboard prev/next navigation
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
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
    toggleBtn();
  }

  /* ---------------- CAST PAGE (SHEET SWITCH + LIGHTBOX) ---------------- */
  function initCastPage() {
    var sheetImg = document.getElementById("castSheetImg");
    var lightbox = document.getElementById("lightbox");
    var lightboxImg = document.getElementById("lightboxImg");
    var lightboxClose = document.getElementById("lightboxClose");

    document.querySelectorAll(".mode-btn[data-sheet]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var src = btn.getAttribute("data-sheet");
        if (sheetImg && src) sheetImg.src = src;
        document.querySelectorAll(".mode-btn[data-sheet]").forEach(function (b) {
          b.classList.toggle("is-active", b === btn);
        });
      });
    });

    if (lightbox && lightboxImg) {
      var openLightbox = function (src, alt) {
        if (!src) return;
        lightboxImg.src = src;
        if (alt) lightboxImg.alt = alt;
        lightbox.hidden = false;
      };
      if (sheetImg) {
        sheetImg.addEventListener("click", function () {
          openLightbox(sheetImg.src, sheetImg.alt);
        });
      }
      document.querySelectorAll("[data-lightbox-src]").forEach(function (el) {
        el.addEventListener("click", function () {
          var src = el.getAttribute("data-lightbox-src");
          var img = el.querySelector("img");
          openLightbox(src, img ? img.alt : "");
        });
      });
      var closeLightbox = function () {
        lightbox.hidden = true;
      };
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

    Copies cast sheets, generates individual 9×9 cast portraits, syncs episode images,
    auto-generates missing episode thumbnails, and emits `index.html`, `episode.html`,
    static `episodes/<id>.html`, `cast.html`, `publish.html`, `sitemap.xml`,
    `robots.txt`, `assets/style.css`, `assets/app.js`, and `data/episodes.json`.

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

    # 1. Sync cast sheet assets and crop individual portraits
    labeled_src = assets_dir / "cast_sheet_c_labeled.png"
    clean_src = assets_dir / "cast_sheet_c.jpg"
    has_labeled = False
    has_clean = False
    if labeled_src.exists():
        _copy_if_different(labeled_src, site_cast_dir / "cast_sheet_c_labeled.png")
        has_labeled = True
    if clean_src.exists():
        _copy_if_different(clean_src, site_cast_dir / "cast_sheet_c.jpg")
        has_clean = True

    portraits = extract_cast_portraits(clean_src, site_cast_dir) if has_clean else {}
    turnarounds_src_dir = assets_dir / "turnarounds"
    site_turnarounds_dir = site_cast_dir / "turnarounds"
    turnarounds: dict[str, str] = {}
    if turnarounds_src_dir.exists():
        site_turnarounds_dir.mkdir(parents=True, exist_ok=True)
        for member in CAST_BIBLE:
            t_src = turnarounds_src_dir / member.turnaround_filename
            if t_src.exists() and t_src.is_file():
                _copy_if_different(t_src, site_turnarounds_dir / member.turnaround_filename)
                turnarounds[member.id] = f"assets/cast/turnarounds/{member.turnaround_filename}"
    fallback_og_image = (
        "assets/cast/cast_sheet_c_labeled.png"
        if has_labeled
        else ("assets/cast/cast_sheet_c.jpg" if has_clean else "")
    )

    # 2. Load episodes and sync media assets into site/assets/episodes/<id>/
    records = load_episodes(episodes_json)
    site_episodes: list[dict[str, Any]] = []
    ep_counts: dict[str, int] = {}

    for record in records:
        ep_out_dir = site_episodes_assets_dir / record.episode_id
        ep_out_dir.mkdir(parents=True, exist_ok=True)

        # Resolve and copy full image
        full_src = _resolve_media_path(record.full_image_rel, episodes_json, assets_dir, site_dir)
        full_dst = ep_out_dir / "episode_full.jpg"
        if full_src is not None:
            _copy_if_different(full_src, full_dst)

        # Resolve and copy page images
        page_web_paths: list[str] = []
        resolved_pages: list[Path] = []
        for idx, page_rel in enumerate(record.page_images_rel, start=1):
            p_src = _resolve_media_path(page_rel, episodes_json, assets_dir, site_dir)
            if p_src is not None:
                ext = p_src.suffix.lower() or ".png"
                p_name = f"page_{idx}{ext}"
                _copy_if_different(p_src, ep_out_dir / p_name)
                page_web_paths.append(f"assets/episodes/{record.episode_id}/{p_name}")
                resolved_pages.append(p_src)

        # Resolve, copy, or auto-generate thumbnail
        thumb_src = _resolve_media_path(record.thumb_image_rel, episodes_json, assets_dir, site_dir)
        thumb_dst = ep_out_dir / "thumb.jpg"
        if thumb_src is not None:
            _copy_if_different(thumb_src, thumb_dst)
        else:
            # Auto-generate crisp card thumbnail from page_1 (or full image fallback)
            thumb_basis = resolved_pages[0] if resolved_pages else full_src
            if thumb_basis is not None and thumb_basis.exists():
                generate_episode_thumbnail(thumb_basis, thumb_dst)
                # Also persist to the declared data path if its parent exists
                declared_data_thumb = episodes_json.parent.parent / record.thumb_image_rel
                if declared_data_thumb.parent.exists() and not declared_data_thumb.exists():
                    _copy_if_different(thumb_dst, declared_data_thumb)

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
            "full_image": f"assets/episodes/{record.episode_id}/episode_full.jpg",
            "thumb_image": f"assets/episodes/{record.episode_id}/thumb.jpg",
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
        )
        for member in CAST_BIBLE
    ]

    # 4. Write shared static assets, site JSON, and crawler metadata
    (site_assets_dir / "style.css").write_text(_STYLE_CSS, encoding="utf-8")
    (site_assets_dir / "app.js").write_text(_APP_JS, encoding="utf-8")
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
            ),
            encoding="utf-8",
        )

    (site_dir / "cast.html").write_text(
        _render_cast_html(
            cast_payload,
            site_episodes,
            has_labeled,
            has_clean,
            base_url=clean_base,
        ),
        encoding="utf-8",
    )

    # Never expose creator upload helper pages publicly on the reader archive
    (site_dir / "publish.html").unlink(missing_ok=True)

    return index_path
