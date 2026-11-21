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
from wow_sloptoon.config import DEFAULT_GALLERY_ID
from wow_sloptoon.models import EpisodeRecord

DC_GALLERY_RECOMMEND_URL = (
    f"https://gall.dcinside.com/mgallery/board/lists/?id={DEFAULT_GALLERY_ID}&exception_mode=recommend"
)
DC_GALLERY_WRITE_URL = (
    f"https://gall.dcinside.com/mgallery/board/write/?id={DEFAULT_GALLERY_ID}"
)

# Normalized (x0, y0, x1, y1) portrait crop boxes on the 1376x768 clean Draft C cast sheet.
_CAST_PORTRAIT_BOXES: dict[str, tuple[float, float, float, float]] = {
    "orc_warrior": (0.012, 0.018, 0.215, 0.468),
    "undead_paladin": (0.212, 0.018, 0.415, 0.468),
    "gnome_rogue": (0.417, 0.018, 0.604, 0.468),
    "dwarf_hunter": (0.604, 0.018, 0.790, 0.468),
    "troll_shaman": (0.789, 0.018, 0.995, 0.468),
    "tauren_druid": (0.041, 0.538, 0.300, 0.956),
    "nightelf_priest": (0.299, 0.538, 0.500, 0.956),
    "human_warlock": (0.503, 0.538, 0.744, 0.956),
    "skyborne_mage": (0.749, 0.538, 0.988, 0.956),
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


def _build_dc_post_title(ep: EpisodeRecord) -> str:
    return f"[만화] 와우 포에버 슬롭툰 EP.{ep.episode_number} — {ep.title}"


def _build_dc_post_body(ep: EpisodeRecord, archive_base_url: str = "") -> str:
    lines = [
        f"와우 포에버 슬롭툰 EP.{ep.episode_number} — {ep.title}",
        ep.subtitle,
        "",
        f"원본 포에버갤 개념글 (#{ep.source_post_no}):",
        ep.source_url,
    ]
    if archive_base_url:
        clean_base = archive_base_url.rstrip("/")
        lines.extend(["", f"웹 아카이브에서 정주행: {clean_base}/episode.html?id={ep.episode_id}"])
    lines.extend([
        "",
        "※ 시안 C 귀염뽀짝 9×9 미소녀 상황극 봇 (순수 팬메이드 패러디)",
    ])
    return "\n".join(lines)


def _format_date_short(created_at: str) -> str:
    if not created_at:
        return ""
    return created_at.split("T", 1)[0].strip()


def _cast_member_payload(
    member: CastMember,
    portrait_rel: str | None,
    ep_counts: dict[str, int],
) -> dict[str, Any]:
    return {
        "id": member.id,
        "name": member.name,
        "race": member.race,
        "wow_class": member.wow_class,
        "role_tag": member.role_tag,
        "color_hex": member.color_hex,
        "accent_hex": member.accent_hex,
        "personality": member.personality,
        "aliases": list(member.aliases[:5]),
        "portrait": portrait_rel or "",
        "episode_count": ep_counts.get(member.name, 0),
    }


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
          <span class="pill-badge pill-sm"><span class="dot-sky"></span>디시 WOW 포에버 마이너 갤러리 개념글 상황극 봇</span>
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
    </footer>
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


def _render_index_html(
    site_episodes: list[dict[str, Any]],
    cast_payload: list[dict[str, Any]],
    total_episodes: int,
) -> str:
    newest_first = list(reversed(site_episodes))
    latest = newest_first[0] if newest_first else None

    if latest:
        latest_chips = "".join(_render_cast_chip_html(c) for c in latest["cast_used"])
        hero_html = f"""
        <section class="hero-section" aria-label="최신 에피소드">
          <div class="hero-card">
            <a class="hero-thumb-link" href="episode.html?id={html.escape(latest['episode_id'])}">
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
                <a href="episode.html?id={html.escape(latest['episode_id'])}">{html.escape(latest['title'])}</a>
              </h2>
              <p class="hero-sub">{html.escape(latest['subtitle'])}</p>
              <div class="chip-row">{latest_chips}</div>
              <div class="hero-actions">
                <a class="btn btn-primary" href="episode.html?id={html.escape(latest['episode_id'])}">지금 바로 감상하기 →</a>
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

    cards_html_parts: list[str] = []
    for ep in newest_first:
        chips = "".join(
            f'<span class="mini-chip"><span class="cast-dot" style="background:{html.escape((CAST_BY_NAME[c].color_hex if c in CAST_BY_NAME else "#111111"))};"></span>{html.escape(c)}</span>'
            for c in ep["cast_used"]
        )
        cards_html_parts.append(
            f"""
            <article class="ep-card"
              data-id="{html.escape(ep['episode_id'])}"
              data-num="{ep['episode_number']}"
              data-title="{html.escape(ep['title'].lower())}"
              data-sub="{html.escape(ep['subtitle'].lower())}"
              data-post="{html.escape(ep['source_post_no'].lower())}"
              data-cast="{html.escape('|'.join(ep['cast_used']))}">
              <a class="ep-card-link" href="episode.html?id={html.escape(ep['episode_id'])}">
                <div class="ep-thumb-wrap">
                  <img src="{html.escape(ep['thumb_image'])}" alt="EP.{ep['episode_number']} {html.escape(ep['title'])}" class="ep-thumb" loading="lazy">
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
        )

    embedded_data = _safe_json_for_script({"episodes": site_episodes, "cast": cast_payload})

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>와우 포에버 슬롭툰 — 디시 WOW 포에버 마이너 갤러리 개념글 상황극 봇</title>
  <meta name="description" content="디시인사이드 WOW 포에버 마이너 갤러리 개념글을 시안 C 귀염뽀짝 9×9 미소녀 4~6컷 상황극 웹툰으로 아카이빙합니다.">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
  <link rel="stylesheet" href="assets/style.css">
</head>
<body data-page="home">
  {_render_nav('home')}

  <main class="container main-content">
    <section class="masthead">
      <div class="pill-badge">
        <span class="dot-sky"></span>디시 WOW 포에버 마이너 갤러리 개념글 상황극 봇
      </div>
      <h1 class="masthead-title">와우 포에버 슬롭툰</h1>
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
            <input type="search" id="searchInput" class="search-input" placeholder="제목, 글번호(#92059), 캐릭터 검색..." autocomplete="off">
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

      <div class="empty-filter" id="emptyFilter" hidden>
        <p class="empty-filter-title">조건에 맞는 에피소드가 아직 없어요!</p>
        <p class="empty-filter-sub">다른 검색어나 캐릭터를 선택해 보세요.</p>
        <button type="button" id="resetFiltersBtn" class="btn btn-outline">필터 초기화</button>
      </div>
    </section>
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
) -> str:
    """Render `episode.html` (dynamic `?id=...`) or a static `episodes/<id>.html` page."""
    ep = default_episode
    total_episodes = len(site_episodes)
    embedded_data = _safe_json_for_script({
        "episodes": site_episodes,
        "rootPrefix": root_prefix,
        "pinnedEpisodeId": pinned_episode_id or "",
        "dcWriteUrl": DC_GALLERY_WRITE_URL,
    })

    page_title = (
        f"EP.{ep['episode_number']} {ep['title']} — 와우 포에버 슬롭툰"
        if ep
        else "에피소드 리더 — 와우 포에버 슬롭툰"
    )
    og_desc = ep["subtitle"] if ep else "와우 포에버 슬롭툰 웹툰 뷰어"
    og_img = f"{root_prefix}{ep['thumb_image']}" if ep else ""

    # Pre-render initial episode SSR content so no-JS crawlers, tests, and instant first paint work!
    if ep:
        idx = next((i for i, item in enumerate(site_episodes) if item["episode_id"] == ep["episode_id"]), 0)
        prev_ep = site_episodes[idx - 1] if idx > 0 else None
        next_ep = site_episodes[idx + 1] if idx + 1 < len(site_episodes) else None
        cast_chips = "".join(_render_cast_chip_html(c, root_prefix=root_prefix) for c in ep["cast_used"])
        pages_imgs_html = "".join(
            f'<img src="{root_prefix}{html.escape(p)}" alt="EP.{ep["episode_number"]} 페이지 {pi}" class="reader-page-img" loading="lazy">'
            for pi, p in enumerate(ep["page_images"], start=1)
        )
        prev_link_html = (
            f'<a class="nav-ep-card" href="{root_prefix}episode.html?id={html.escape(prev_ep["episode_id"])}">'
            f'<span class="nav-ep-dir">← 이전 화</span>'
            f'<strong class="nav-ep-title">EP.{prev_ep["episode_number"]} {html.escape(prev_ep["title"])}</strong></a>'
            if prev_ep
            else '<div class="nav-ep-card is-disabled"><span class="nav-ep-dir">← 이전 화</span><span class="nav-ep-title">첫 번째 에피소드입니다</span></div>'
        )
        next_link_html = (
            f'<a class="nav-ep-card nav-ep-next" href="{root_prefix}episode.html?id={html.escape(next_ep["episode_id"])}">'
            f'<span class="nav-ep-dir">다음 화 →</span>'
            f'<strong class="nav-ep-title">EP.{next_ep["episode_number"]} {html.escape(next_ep["title"])}</strong></a>'
            if next_ep
            else '<div class="nav-ep-card nav-ep-next is-disabled"><span class="nav-ep-dir">다음 화 →</span><span class="nav-ep-title">가장 최신 에피소드입니다</span></div>'
        )

        reader_initial_html = f"""
        <div class="reader-top-bar">
          <a class="back-link" href="{root_prefix}index.html">← 전체 목록</a>
          <div class="reader-mode-toggle" role="group" aria-label="보기 방식">
            <button type="button" class="mode-btn is-active" data-mode="full">통합 스크롤</button>
            <button type="button" class="mode-btn" data-mode="pages">페이지별 보기</button>
          </div>
          <a class="btn btn-sm btn-outline" href="#dc-upload-helper">디시 업로드 도우미 ↓</a>
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

        <section class="dc-helper-card" id="dc-upload-helper" aria-label="디시 포에버갤 업로드 도우미">
          <div class="dc-helper-head">
            <div>
              <span class="pill-badge pill-sm"><span class="dot-sky"></span>1-CLICK UPLOAD HELPER</span>
              <h2 class="dc-helper-title">디시 포에버갤 업로드 도우미</h2>
              <p class="dc-helper-desc">
                버튼 한 번으로 <strong>[만화] 제목 + 본문/출처 복사</strong>, <strong>통합본 JPG 다운로드</strong>,
                <strong>공식 포에버갤 글쓰기창 새 탭 열기</strong>를 동시에 준비합니다.
                (로그인·캡차 확인 및 최종 등록은 공식 페이지에서 직접 완료해 주세요.)
              </p>
            </div>
          </div>

          <div class="dc-preview-grid">
            <div class="dc-preview-box">
              <div class="dc-preview-label">글 제목 (자동 복사)</div>
              <pre id="dcTitlePreview" class="dc-preview-text">{html.escape(ep['dc_title'])}</pre>
            </div>
            <div class="dc-preview-box">
              <div class="dc-preview-label">본문 &amp; 원본 출처</div>
              <pre id="dcBodyPreview" class="dc-preview-text">{html.escape(ep['dc_body'])}</pre>
            </div>
          </div>

          <div class="dc-helper-actions">
            <button type="button" id="dcOneClickBtn" class="btn btn-primary btn-lg">
              디시 포에버갤 업로드 도우미 실행 (복사 + 저장 + 글쓰기 열기)
            </button>
            <div class="dc-sub-actions">
              <button type="button" id="dcCopyTitleBtn" class="btn btn-outline btn-sm">제목만 복사</button>
              <button type="button" id="dcCopyBodyBtn" class="btn btn-outline btn-sm">본문·출처 복사</button>
              <a id="dcDownloadBtn" class="btn btn-outline btn-sm" href="{root_prefix}{html.escape(ep['full_image'])}" download="wow_sloptoon_{html.escape(ep['episode_id'])}_full.jpg">통합본 JPG 저장</a>
              <a id="dcWriteLink" class="btn btn-subtle btn-sm" href="{DC_GALLERY_WRITE_URL}" target="_blank" rel="noopener noreferrer">글쓰기창만 열기 ↗</a>
            </div>
          </div>
        </section>

        <nav class="episode-pager" id="epPager" aria-label="이전화 다음화 이동">
          {prev_link_html}
          {next_link_html}
        </nav>
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
  <meta name="description" content="{html.escape(og_desc)}">
  <meta property="og:title" content="{html.escape(page_title)}">
  <meta property="og:description" content="{html.escape(og_desc)}">
  <meta property="og:image" content="{html.escape(og_img)}">
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
) -> str:
    total_episodes = len(site_episodes)

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
            ep_links = "".join(
                f'<a class="ep-mini-link" href="episode.html?id={html.escape(ep["episode_id"])}">EP.{ep["episode_number"]} {html.escape(ep["title"])}</a>'
                for ep in appearances
            )
            appearances_html = f'<div class="cast-ep-list">{ep_links}</div>'
        else:
            appearances_html = '<p class="cast-ep-empty">곧 새로운 개념글 상황극으로 등판 예정!</p>'

        if c["portrait"]:
            avatar_html = f'<img src="{html.escape(c["portrait"])}" alt="{html.escape(c["name"])} 포트레이트" class="cast-avatar" loading="lazy">'
        else:
            avatar_html = (
                f'<div class="cast-avatar-fallback" style="background:{html.escape(c["color_hex"])};">'
                f'{html.escape(c["name"][:2])}</div>'
            )

        alias_tags = "".join(f'<span class="alias-tag">#{html.escape(a)}</span>' for a in c["aliases"])

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
                      {html.escape(c['race'])} · {html.escape(c['wow_class'])}
                    </span>
                  </div>
                  <h3 class="cast-name">{html.escape(c['name'])}</h3>
                  <p class="cast-role">{html.escape(c['role_tag'])}</p>
                </div>
              </div>
              <p class="cast-bio">{html.escape(c['personality'])}</p>
              <div class="alias-row">{alias_tags}</div>
              <div class="cast-card-foot">
                <div class="cast-foot-label">출연 에피소드 ({len(appearances)}화)</div>
                {appearances_html}
                <a class="cast-filter-link" href="index.html?cast={html.escape(c['name'])}">아카이브에서 모아보기 →</a>
              </div>
            </article>
            """
        )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>9×9 캐스트 도감 (시안 C) — 와우 포에버 슬롭툰</title>
  <meta name="description" content="와우 포에버 슬롭툰 공식 확정 시안 C 9종족×9직업 귀염뽀짝 미소녀 캐릭터 도감">
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
  --sky: #38bdf8;
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
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(10px);
  border-bottom: 1.5px solid var(--border);
}
.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  height: 62px;
}
.brand {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  font-weight: 800;
  font-size: 1.05rem;
  letter-spacing: -0.02em;
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
  gap: 6px;
}
.nav-link {
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--ink-muted);
  padding: 7px 13px;
  border-radius: 999px;
  transition: background 0.15s ease, color 0.15s ease;
}
.nav-link:hover { background: var(--surface-2); color: var(--ink); }
.nav-link.is-active { background: var(--ink); color: #ffffff; }
.nav-ext { border: 1px solid var(--border); }

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
  transition: transform 0.14s ease, box-shadow 0.14s ease, background 0.14s ease;
}
.btn:hover { transform: translate(-1px, -1px); }
.btn-primary {
  background: var(--ink);
  color: #ffffff;
  box-shadow: 3px 3px 0 var(--sky);
}
.btn-primary:hover { box-shadow: 4px 4px 0 var(--sky); }
.btn-outline { background: #ffffff; color: var(--ink); }
.btn-outline:hover { background: var(--surface); box-shadow: 3px 3px 0 var(--ink); }
.btn-subtle { background: var(--surface); border-color: var(--border); color: var(--ink); }
.btn-subtle:hover { border-color: var(--ink); }
.btn-sm { font-size: 0.82rem; padding: 7px 13px; border-radius: 10px; border-width: 1.5px; }
.btn-lg { font-size: 0.98rem; padding: 14px 22px; width: 100%; }

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
  color: var(--navy);
  padding: 6px 14px;
  border-radius: 999px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
}
.source-link:hover { background: #dbeafe; }

.comic-stage {
  background: #ffffff;
  margin: 12px auto 38px;
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

/* DCInside 1-Click Upload Helper */
.dc-helper-card {
  background: #ffffff;
  border: 2px solid var(--ink);
  border-radius: var(--radius-lg);
  padding: 24px 26px;
  box-shadow: var(--shadow-comic);
  margin-bottom: 34px;
}
.dc-helper-title {
  margin: 10px 0 6px;
  font-size: 1.25rem;
  font-weight: 900;
  letter-spacing: -0.02em;
}
.dc-helper-desc {
  margin: 0 0 18px;
  color: var(--ink-muted);
  font-size: 0.88rem;
  word-break: keep-all;
}
.dc-preview-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  margin-bottom: 18px;
}
.dc-preview-box {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px 14px;
}
.dc-preview-label {
  font-size: 0.74rem;
  font-weight: 800;
  color: var(--ink-soft);
  text-transform: uppercase;
  margin-bottom: 6px;
}
.dc-preview-text {
  margin: 0;
  font-family: var(--font-sans);
  font-size: 0.86rem;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--ink);
}
.dc-helper-actions { display: flex; flex-direction: column; gap: 10px; }
.dc-sub-actions { display: flex; flex-wrap: wrap; gap: 8px; }

/* Prev / Next episode pager */
.episode-pager {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}
.nav-ep-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px 18px;
  border: 1.8px solid var(--ink);
  border-radius: var(--radius-md);
  background: #ffffff;
  transition: transform 0.14s ease, box-shadow 0.14s ease;
}
.nav-ep-card:not(.is-disabled):hover {
  transform: translate(-1px, -2px);
  box-shadow: var(--shadow-comic);
}
.nav-ep-card.is-disabled { border-color: var(--border); color: var(--ink-soft); background: var(--surface); }
.nav-ep-next { text-align: right; }
.nav-ep-dir { font-size: 0.76rem; font-weight: 800; color: var(--ink-soft); }
.nav-ep-title { font-size: 0.95rem; font-weight: 800; word-break: keep-all; }

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

/* Footer & toast */
.site-footer {
  border-top: 1.5px solid var(--border);
  background: var(--surface);
  padding: 32px 0 42px;
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
  gap: 16px;
  font-size: 0.86rem;
  font-weight: 700;
  color: var(--ink-muted);
}
.footer-links a:hover { color: var(--ink); }

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
}

@media (max-width: 820px) {
  .hero-card { grid-template-columns: 1fr; }
  .hero-thumb-link { border-right: 0; border-bottom: 2px solid var(--border-strong); }
  .hero-thumb { min-height: 220px; }
  .hero-body { padding: 20px; }
  .episode-pager { grid-template-columns: 1fr; }
  .nav-ep-next { text-align: left; }
  .brand-tag { display: none; }
  .search-input { width: 100%; }
}
"""


_APP_JS = """/* 와우 포에버 슬롭툰 — 정적 웹 아카이브 인터랙션 */
(function () {
  "use strict";

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

  /* ---------------- HOME PAGE (SEARCH / FILTER / SORT) ---------------- */
  function initHomePage() {
    var grid = document.getElementById("episodeGrid");
    var searchInput = document.getElementById("searchInput");
    var filterBar = document.getElementById("castFilterBar");
    var sortToggle = document.getElementById("sortToggle");
    var resultCount = document.getElementById("resultCount");
    var emptyFilter = document.getElementById("emptyFilter");
    var resetBtn = document.getElementById("resetFiltersBtn");
    if (!grid) return;

    var cards = Array.prototype.slice.call(grid.querySelectorAll(".ep-card"));
    var activeCast = "";
    var sortOrder = "desc";

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

    function applyFilters() {
      var q = (searchInput ? searchInput.value : "").trim().toLowerCase();
      var visible = 0;

      cards.sort(function (a, b) {
        var na = parseInt(a.getAttribute("data-num") || "0", 10);
        var nb = parseInt(b.getAttribute("data-num") || "0", 10);
        return sortOrder === "desc" ? nb - na : na - nb;
      });
      cards.forEach(function (card) {
        grid.appendChild(card);
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
          post.indexOf(q.replace(/^#/, "")) !== -1 ||
          castStr.toLowerCase().indexOf(q) !== -1;

        var show = matchesCast && matchesQuery;
        card.hidden = !show;
        if (show) visible += 1;
      });

      if (resultCount) {
        resultCount.textContent = "총 " + visible + "개의 에피소드";
      }
      if (emptyFilter) {
        emptyFilter.hidden = visible > 0;
      }
    }

    if (searchInput) {
      searchInput.addEventListener("input", applyFilters);
    }
    if (filterBar) {
      filterBar.addEventListener("click", function (ev) {
        var btn = ev.target.closest(".filter-chip");
        if (!btn) return;
        activeCast = btn.getAttribute("data-cast") || "";
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
        applyFilters();
      });
    }
    if (resetBtn) {
      resetBtn.addEventListener("click", function () {
        activeCast = "";
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

  /* ---------------- EPISODE READER & 1-CLICK DC HELPER ---------------- */
  function initEpisodePage() {
    var data = window.__SLOPTOON_DATA__;
    if (!data || !Array.isArray(data.episodes) || data.episodes.length === 0) return;

    var episodes = data.episodes;
    var rootPrefix = data.rootPrefix || "";
    var dcWriteUrl = data.dcWriteUrl || "https://gall.dcinside.com/mgallery/board/write/?id=wowforever";

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
    var prevEp = currentIndex > 0 ? episodes[currentIndex - 1] : null;
    var nextEp = currentIndex + 1 < episodes.length ? episodes[currentIndex + 1] : null;

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

    // Update pager cards
    var pager = document.getElementById("epPager");
    if (pager) {
      pager.innerHTML = "";
      if (prevEp) {
        var prevA = document.createElement("a");
        prevA.className = "nav-ep-card";
        prevA.href = rootPrefix + "episode.html?id=" + encodeURIComponent(prevEp.episode_id);
        prevA.innerHTML =
          '<span class="nav-ep-dir">← 이전 화</span><strong class="nav-ep-title"></strong>';
        prevA.querySelector(".nav-ep-title").textContent =
          "EP." + prevEp.episode_number + " " + prevEp.title;
        pager.appendChild(prevA);
      } else {
        var prevD = document.createElement("div");
        prevD.className = "nav-ep-card is-disabled";
        prevD.innerHTML =
          '<span class="nav-ep-dir">← 이전 화</span><span class="nav-ep-title">첫 번째 에피소드입니다</span>';
        pager.appendChild(prevD);
      }

      if (nextEp) {
        var nextA = document.createElement("a");
        nextA.className = "nav-ep-card nav-ep-next";
        nextA.href = rootPrefix + "episode.html?id=" + encodeURIComponent(nextEp.episode_id);
        nextA.innerHTML =
          '<span class="nav-ep-dir">다음 화 →</span><strong class="nav-ep-title"></strong>';
        nextA.querySelector(".nav-ep-title").textContent =
          "EP." + nextEp.episode_number + " " + nextEp.title;
        pager.appendChild(nextA);
      } else {
        var nextD = document.createElement("div");
        nextD.className = "nav-ep-card nav-ep-next is-disabled";
        nextD.innerHTML =
          '<span class="nav-ep-dir">다음 화 →</span><span class="nav-ep-title">가장 최신 에피소드입니다</span>';
        pager.appendChild(nextD);
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

    // 1-Click DCInside Upload Helper (Clipboard + Image Download + Official Write Tab)
    var oneClickBtn = document.getElementById("dcOneClickBtn");
    if (oneClickBtn) {
      oneClickBtn.addEventListener("click", function () {
        var combined = ep.dc_title + "\\n\\n" + ep.dc_body;
        copyText(combined).then(function () {
          // Trigger JPG download
          var link = document.createElement("a");
          link.href = fullSrc;
          link.download = dlFileName;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);

          // Open official DCInside write page in new tab (user signs in & posts manually)
          window.open(dcWriteUrl, "_blank", "noopener,noreferrer");
          showToast("제목·본문 복사 완료 + JPG 저장 시작 + 포에버갤 글쓰기창을 열었습니다!");
        });
      });
    }

    var copyTitleBtn = document.getElementById("dcCopyTitleBtn");
    if (copyTitleBtn) {
      copyTitleBtn.addEventListener("click", function () {
        copyText(ep.dc_title).then(function () {
          showToast("글 제목을 클립보드에 복사했습니다!");
        });
      });
    }

    var copyBodyBtn = document.getElementById("dcCopyBodyBtn");
    if (copyBodyBtn) {
      copyBodyBtn.addEventListener("click", function () {
        copyText(ep.dc_body).then(function () {
          showToast("본문 및 원본 출처 링크를 클립보드에 복사했습니다!");
        });
      });
    }

    // Keyboard prev/next navigation
    document.addEventListener("keydown", function (ev) {
      if (ev.target && /INPUT|TEXTAREA/.test(ev.target.tagName)) return;
      if (ev.key === "ArrowLeft" && prevEp) {
        window.location.href = rootPrefix + "episode.html?id=" + encodeURIComponent(prevEp.episode_id);
      } else if (ev.key === "ArrowRight" && nextEp) {
        window.location.href = rootPrefix + "episode.html?id=" + encodeURIComponent(nextEp.episode_id);
      }
    });
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

    if (sheetImg && lightbox && lightboxImg) {
      sheetImg.addEventListener("click", function () {
        lightboxImg.src = sheetImg.src;
        lightbox.hidden = false;
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
  });
})();
"""


def build_static_site(
    episodes_json: Path,
    site_dir: Path,
    assets_dir: Path,
    archive_base_url: str = "",
) -> Path:
    """Build the complete static pure-white web archive into `site_dir`.

    Copies cast sheets, generates individual 9×9 cast portraits, syncs episode images,
    auto-generates missing episode thumbnails, and emits `index.html`, `episode.html`,
    static `episodes/<id>.html`, `cast.html`, `assets/style.css`, `assets/app.js`,
    and `data/episodes.json`.

    Returns:
        Path to the generated `site_dir / "index.html"`.
    """
    episodes_json = Path(episodes_json)
    site_dir = Path(site_dir)
    assets_dir = Path(assets_dir)

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
            "dc_title": _build_dc_post_title(record),
            "dc_body": _build_dc_post_body(record, archive_base_url=archive_base_url),
        })

    # 3. Build cast metadata payload
    cast_payload = [
        _cast_member_payload(member, portraits.get(member.id), ep_counts)
        for member in CAST_BIBLE
    ]

    # 4. Write shared static assets & site JSON
    (site_assets_dir / "style.css").write_text(_STYLE_CSS, encoding="utf-8")
    (site_assets_dir / "app.js").write_text(_APP_JS, encoding="utf-8")
    (site_data_dir / "episodes.json").write_text(
        json.dumps(site_episodes, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (site_dir / ".nojekyll").write_text("", encoding="utf-8")

    # 5. Write HTML pages
    index_path = site_dir / "index.html"
    index_path.write_text(
        _render_index_html(site_episodes, cast_payload, len(site_episodes)),
        encoding="utf-8",
    )

    latest_ep = site_episodes[-1] if site_episodes else None
    (site_dir / "episode.html").write_text(
        _render_episode_reader_html(site_episodes, latest_ep, root_prefix=""),
        encoding="utf-8",
    )

    for ep in site_episodes:
        (site_episodes_html_dir / f"{ep['episode_id']}.html").write_text(
            _render_episode_reader_html(
                site_episodes,
                ep,
                root_prefix="../",
                pinned_episode_id=ep["episode_id"],
            ),
            encoding="utf-8",
        )

    (site_dir / "cast.html").write_text(
        _render_cast_html(cast_payload, site_episodes, has_labeled, has_clean),
        encoding="utf-8",
    )

    return index_path
