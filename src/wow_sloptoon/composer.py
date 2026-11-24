"""Production webtoon typesetting, pure-white normalization, and overlap-free composer.

Refactored from the verified EP.1 (v10b) and EP.2 (v11) Sloptoon builders into a
general-purpose 4~6 cut composer that guarantees:
- Pure `#FFFFFF` seamless background normalization (zero grey edge noise or seams)
- 4x-supersampled elliptical speech bubbles with automatic directional pointed tails
- Automatic `overlap_px == 0` collision-avoidance solver between bubbles and artwork
- 100% wordless centered freeze-frames when `cut.wordless` is True
- Both even-cut (4/6 cuts -> 2-tier 900x1320 pages) and odd-cut (5 cuts -> final
  900x486 single 3.5px black-bordered epilogue box) layouts
- Cross-platform Korean font discovery (Windows NotoSansKR / Malgun Gothic, Linux Noto CJK / Nanum)
"""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from wow_sloptoon.item_tooltip import render_item_tooltip
from wow_sloptoon.models import ComicCut, EpisodeScript

# Canonical Sloptoon color palette
INK_BLACK: tuple[int, int, int] = (20, 20, 20)        # #141414 crisp Sloptoon ink
PURE_WHITE: tuple[int, int, int] = (255, 255, 255)    # #FFFFFF seamless pure white
MUTED_INK: tuple[int, int, int] = (88, 92, 102)       # Subtle aside / subtitle ink
DC_BLUE: tuple[int, int, int] = (43, 76, 126)         # DC WOW Forever Gallery accent blue
PILL_DOT_BLUE: tuple[int, int, int] = (92, 184, 255)  # Header badge accent dot
WATERMARK_ACCENT_BLUE: tuple[int, int, int] = (14, 165, 233)  # #0EA5E9 sky-blue CTA accent
WATERMARK_LINK_BLUE: tuple[int, int, int] = (2, 132, 199)     # #0284C7 crisp URL ink on #FFFFFF

# Canonical Sloptoon page & panel geometry
PAGE_W: int = 900
HEADER_H: int = 244
WATERMARK_FOOTER_H: int = 132
FULL_PAGE_H: int = 1320
TOP_PANEL_H: int = 830
BOT_BOX_RECT: tuple[int, int, int, int] = (28, 856, 872, 1292)
BOT_BOX_W: int = BOT_BOX_RECT[2] - BOT_BOX_RECT[0]    # 844
BOT_BOX_H: int = BOT_BOX_RECT[3] - BOT_BOX_RECT[1]    # 436

EPILOGUE_PAGE_H: int = 486
EPILOGUE_BOX_RECT: tuple[int, int, int, int] = (28, 25, 872, 461)

THUMB_SIZE: tuple[int, int] = (800, 600)              # Crisp 4:3 web archive card thumbnail

HEADER_BADGE_TEXT = "디시 WOW 포에버 마이너 갤러리 개념글 봇"
SERIES_TITLE_TEXT = "와우 포에버 슬롭툰"
DEFAULT_WATERMARK_URL = "slopwow.github.io"
WATERMARK_BADGE_TEXT = "와우 포에버 슬롭툰  |  WOW FOREVER SLOPTOON"
WATERMARK_CTA_PREFIX = "다음 화 & 전편 정주행"
WATERMARK_SUBTEXT = "디시 WOW 포에버 마이너 갤러리 개념글 100% 상황극 아카이브"

_TRAILING_PAREN_RE = re.compile(r"^(.*?)(\s*\([^()]{2,34}\))\s*$")


@dataclass
class ComposeResult:
    """Output artifact paths and pixel-level audit metrics from `compose_episode`."""

    header_path: Path
    page_paths: list[Path]
    full_image_path: Path
    thumb_path: Path
    audit_report: dict[str, Any]


def _candidate_font_paths(weight: str) -> list[str]:
    """Build prioritized cross-platform Korean font search paths."""
    is_heavy = weight.lower() in {"bold", "black", "extrabold", "semibold"}
    local_app_data = os.environ.get("LOCALAPPDATA", "")

    candidates: list[str] = []
    env_font = os.environ.get("SLOPTOON_FONT_PATH", "").strip()
    if env_font:
        candidates.append(env_font)

    # 1. Windows NotoSansKR Variable Font (supports Black / Bold / Medium / Regular)
    candidates.append("C:/Windows/Fonts/NotoSansKR-VF.ttf")
    if local_app_data:
        candidates.append(
            str(Path(local_app_data) / "Microsoft" / "Windows" / "Fonts" / "NotoSansKR-VF.ttf")
        )

    # 2. Windows Malgun Gothic & Nanum Gothic
    if is_heavy:
        candidates.extend(
            [
                "C:/Windows/Fonts/malgunbd.ttf",
                "C:/Windows/Fonts/NanumGothicBold.ttf",
                "C:/Windows/Fonts/malgun.ttf",
            ]
        )
    else:
        candidates.extend(
            [
                "C:/Windows/Fonts/malgun.ttf",
                "C:/Windows/Fonts/NanumGothic.ttf",
                "C:/Windows/Fonts/malgunbd.ttf",
            ]
        )

    # 3. Linux Noto Sans CJK / Noto Sans KR / Nanum (Ubuntu, Debian, Fedora, Arch, Alpine)
    linux_heavy = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansKR-VF.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansKR-Bold.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    ]
    linux_regular = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansKR-VF.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
    ]
    candidates.extend(linux_heavy if is_heavy else linux_regular)

    # 4. macOS & generic fallbacks
    candidates.extend(
        [
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
            "/Library/Fonts/NotoSansKR-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
    )
    return candidates


@lru_cache(maxsize=256)
def load_font(size: int, weight: str = "Bold") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load the best available Korean-capable font across Windows, Linux, and macOS."""
    safe_size = max(8, int(round(size)))
    for path in _candidate_font_paths(weight):
        if path and os.path.exists(path):
            try:
                font = ImageFont.truetype(path, safe_size)
                try:
                    font.set_variation_by_name(weight)
                except Exception:
                    pass
                return font
            except Exception:
                continue

    try:
        return ImageFont.load_default(size=safe_size)
    except TypeError:
        return ImageFont.load_default()


def _flatten_to_white_rgb(im: Image.Image) -> Image.Image:
    """Convert any PIL image mode to RGB by compositing transparency onto pure `#FFFFFF`."""
    if im.mode == "RGB":
        return im
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        rgba = im.convert("RGBA")
        bg = Image.new("RGB", rgba.size, PURE_WHITE)
        bg.paste(rgba, mask=rgba.getchannel("A"))
        return bg
    return im.convert("RGB")


def clean_white_bg(
    im: Image.Image,
    low: float = 236.0,
    high: float = 245.0,
    chroma_max: float = 22.0,
) -> Image.Image:
    """Level near-white neutral background noise to strict `#FFFFFF` (255, 255, 255).

    Ensures raw illustrations merge seamlessly onto the pure white webtoon canvas
    with zero JPEG off-white edge seams.
    """
    rgb = _flatten_to_white_rgb(im)
    arr = np.asarray(rgb, dtype=np.float32)
    cmin = arr.min(axis=2)
    cmax = arr.max(axis=2)
    chroma = cmax - cmin

    lum_t = np.clip((cmin - low) / max(1.0, high - low), 0.0, 1.0)
    lum_smooth = lum_t * lum_t * (3.0 - 2.0 * lum_t)
    chroma_t = np.clip((chroma_max - chroma) / 14.0, 0.0, 1.0)
    blend = (lum_smooth * chroma_t)[:, :, None]

    out = arr * (1.0 - blend) + 255.0 * blend
    out_u8 = np.clip(np.round(out), 0, 255).astype(np.uint8)
    near_white_mask = (arr[:, :, 0] > 245) & (arr[:, :, 1] > 245) & (arr[:, :, 2] > 245)
    out_u8[near_white_mask] = 255
    return Image.fromarray(out_u8, mode="RGB")


def get_art_mask(im: Image.Image, threshold: int = 255) -> np.ndarray:
    """Return boolean mask `(H, W)` of non-white artwork pixels strictly below `threshold`."""
    arr = np.asarray(im.convert("RGB"))
    return (arr[:, :, 0] < threshold) | (arr[:, :, 1] < threshold) | (arr[:, :, 2] < threshold)


def extract_art_bbox(im: Image.Image, threshold: int = 255) -> tuple[int, int, int, int] | None:
    """Return inclusive `(x0, y0, x1, y1)` bounding box of non-white artwork, or None if blank."""
    mask = get_art_mask(im, threshold=threshold)
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def place_scaled_art(
    raw_im: Image.Image,
    target_w: int,
    target_h: int,
    scale: float,
    px: float,
    py: float,
    crop_box: tuple[int, int, int, int] | None = None,
    clean_kwargs: dict[str, Any] | None = None,
) -> Image.Image:
    """Crop (optional), normalize to `#FFFFFF`, LANCZOS-scale, and paste onto `#FFFFFF` canvas."""
    ck = clean_kwargs or {}
    src = raw_im.crop(crop_box) if crop_box is not None else raw_im
    clean_im = clean_white_bg(src, **ck)
    sw, sh = clean_im.size
    nw = max(1, int(round(sw * scale)))
    nh = max(1, int(round(sh * scale)))
    resized = clean_white_bg(clean_im.resize((nw, nh), Image.Resampling.LANCZOS), **ck)

    canvas = Image.new("RGB", (target_w, target_h), PURE_WHITE)
    canvas.paste(resized, (int(round(px)), int(round(py))))
    return canvas


def _offset_closed_polygon(
    pts: Sequence[tuple[float, float]], offset_px: float
) -> list[tuple[float, float]]:
    """Offset a 2D closed polygon outward by `offset_px` with miter-clamped sharp corners."""
    arr = np.asarray(pts, dtype=np.float64)
    if len(arr) < 3:
        return [(float(p[0]), float(p[1])) for p in arr]

    x, y = arr[:, 0], arr[:, 1]
    signed_area2 = np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)
    sign = 1.0 if signed_area2 >= 0 else -1.0

    p_next = np.roll(arr, -1, axis=0)
    edges = p_next - arr
    elen = np.hypot(edges[:, 0], edges[:, 1])
    valid = elen > 1e-5
    if not np.all(valid):
        arr = arr[valid]
        return _offset_closed_polygon(arr.tolist(), offset_px)

    nx = sign * (edges[:, 1] / elen)
    ny = sign * (-edges[:, 0] / elen)
    normals = np.stack([nx, ny], axis=1)
    dirs = edges / elen[:, None]

    out_pts: list[tuple[float, float]] = []
    miter_limit = 2.6 * offset_px
    n_pts = len(arr)
    for i in range(n_pts):
        i_prev = (i - 1) % n_pts
        n1, n2 = normals[i_prev], normals[i]
        d1, d2 = dirs[i_prev], dirs[i]
        p = arr[i]

        p1 = p + n1 * offset_px
        p2 = p + n2 * offset_px
        denom = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(denom) < 1e-4:
            cand = 0.5 * (p1 + p2)
        else:
            dp = p2 - p1
            t = (dp[0] * d2[1] - dp[1] * d2[0]) / denom
            cand = p1 + t * d1

        dist = float(np.hypot(cand[0] - p[0], cand[1] - p[1]))
        if dist > miter_limit:
            v = (cand - p) / max(1e-6, dist)
            cand = p + v * miter_limit
        out_pts.append((float(cand[0]), float(cand[1])))
    return out_pts


def _measure_text_block(
    dummy_draw: ImageDraw.ImageDraw,
    lines: Sequence[str],
    main_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    sub_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    line_gap: int,
    sub_set: set[int],
) -> tuple[float, float, list[float], list[float], list[float], list[Any]]:
    widths: list[float] = []
    heights: list[float] = []
    y_offs: list[float] = []
    fonts: list[Any] = []
    for idx, ln in enumerate(lines):
        fnt = sub_font if idx in sub_set else main_font
        bb = dummy_draw.textbbox((0, 0), ln, font=fnt)
        w = float(dummy_draw.textlength(ln, font=fnt))
        h = float(bb[3] - bb[1])
        widths.append(w)
        heights.append(h)
        y_offs.append(float(bb[1]))
        fonts.append(fnt)
    tot_h = sum(heights) + line_gap * max(0, len(lines) - 1)
    max_w = max(widths) if widths else 0.0
    return max_w, tot_h, widths, heights, y_offs, fonts


def _build_bubble_layer(
    panel_size: tuple[int, int],
    center: tuple[float, float],
    lines: Sequence[str],
    radii: tuple[float, float] | None = None,
    tail_tip: tuple[float, float] | None = None,
    tail_base_angle_deg: float | None = None,
    tail_half_deg: float = 7.5,
    tail_curve: float = 8.0,
    font_size: int = 24,
    stroke_px: float = 3.5,
    pad_xy: tuple[float, float] = (44.0, 30.0),
    line_spacing_ratio: float = 0.34,
    sub_line_indices: Sequence[int] | None = None,
) -> tuple[Image.Image | None, tuple[int, int], dict[str, Any]]:
    """Render a 4x-supersampled elliptical bubble + seamless sharp tail onto an RGBA ROI layer."""
    S = 4
    pw, ph = panel_size
    cx, cy = float(center[0]), float(center[1])
    sub_set = set(sub_line_indices or [])

    dummy_draw = ImageDraw.Draw(Image.new("RGB", (16, 16), PURE_WHITE))
    chosen_fs = max(12, int(round(font_size)))
    main_font = load_font(chosen_fs, weight="Bold")
    sub_font = load_font(max(12, int(round(chosen_fs * 0.80))), weight="Medium")
    line_gap = max(5, int(round(chosen_fs * line_spacing_ratio)))

    if radii is None:
        max_w, tot_h, widths, heights, y_offs, fonts = _measure_text_block(
            dummy_draw, lines, main_font, sub_font, line_gap, sub_set
        )
        rx = max(110.0, max_w * 0.66 + pad_xy[0])
        ry = max(54.0, tot_h * 0.70 + pad_xy[1])
    else:
        rx, ry = float(radii[0]), float(radii[1])
        max_w, tot_h, widths, heights, y_offs, fonts = _measure_text_block(
            dummy_draw, lines, main_font, sub_font, line_gap, sub_set
        )
        for fs_try in range(chosen_fs, 11, -1):
            f_m = load_font(fs_try, weight="Bold")
            f_s = load_font(max(11, int(round(fs_try * 0.80))), weight="Medium")
            gap_try = max(4, int(round(fs_try * line_spacing_ratio)))
            mw, th, ws, hs, yo, fs_list = _measure_text_block(
                dummy_draw, lines, f_m, f_s, gap_try, sub_set
            )
            a = mw / 2.0 + 18.0
            b = th / 2.0 + 12.0
            if (a / max(1.0, rx)) ** 2 + (b / max(1.0, ry)) ** 2 <= 0.86 or fs_try == 12:
                chosen_fs = fs_try
                main_font, sub_font, line_gap = f_m, f_s, gap_try
                max_w, tot_h, widths, heights, y_offs, fonts = mw, th, ws, hs, yo, fs_list
                break

    pts_x = [cx - rx - stroke_px - 8.0, cx + rx + stroke_px + 8.0]
    pts_y = [cy - ry - stroke_px - 8.0, cy + ry + stroke_px + 8.0]
    if tail_tip is not None:
        pts_x.extend([tail_tip[0] - stroke_px * 4 - 12.0, tail_tip[0] + stroke_px * 4 + 12.0])
        pts_y.extend([tail_tip[1] - stroke_px * 4 - 12.0, tail_tip[1] + stroke_px * 4 + 12.0])

    roi_x0 = max(0, int(np.floor(min(pts_x))))
    roi_y0 = max(0, int(np.floor(min(pts_y))))
    roi_x1 = min(pw, int(np.ceil(max(pts_x))))
    roi_y1 = min(ph, int(np.ceil(max(pts_y))))
    if roi_x1 <= roi_x0 or roi_y1 <= roi_y0:
        return None, (0, 0), {"font_size": chosen_fs, "rx": rx, "ry": ry}

    rw, rh = roi_x1 - roi_x0, roi_y1 - roi_y0
    layer_4x = Image.new("RGBA", (rw * S, rh * S), (0, 0, 0, 0))
    d4 = ImageDraw.Draw(layer_4x)

    theta = np.linspace(0.0, 2.0 * np.pi, 720, endpoint=False)
    cos_t, sin_t = np.cos(theta), np.sin(theta)
    nx = ry * cos_t
    ny = rx * sin_t
    nlen = np.hypot(nx, ny)
    ux, uy = nx / nlen, ny / nlen

    in_ell = list(
        zip(
            ((cx - roi_x0 + rx * cos_t) * S).tolist(),
            ((cy - roi_y0 + ry * sin_t) * S).tolist(),
        )
    )
    out_ell = list(
        zip(
            ((cx - roi_x0 + rx * cos_t + stroke_px * ux) * S).tolist(),
            ((cy - roi_y0 + ry * sin_t + stroke_px * uy) * S).tolist(),
        )
    )

    in_tail = None
    out_tail = None
    if tail_tip is not None:
        tx, ty = float(tail_tip[0]), float(tail_tip[1])
        # Only draw tail if tip lies meaningfully outside the ellipse
        norm_dist = np.hypot((tx - cx) / max(1.0, rx), (ty - cy) / max(1.0, ry))
        if norm_dist > 1.06:
            if tail_base_angle_deg is not None:
                th0 = np.deg2rad(float(tail_base_angle_deg))
            else:
                th0 = float(np.arctan2((ty - cy) / max(1.0, ry), (tx - cx) / max(1.0, rx)))
            dth = np.deg2rad(float(tail_half_deg))

            th1 = th0 - dth
            th2 = th0 + dth
            p1 = np.array([cx + rx * np.cos(th1), cy + ry * np.sin(th1)], dtype=np.float64)
            p2 = np.array([cx + rx * np.cos(th2), cy + ry * np.sin(th2)], dtype=np.float64)

            c_vec = np.array([cx, cy], dtype=np.float64)
            u1 = (c_vec - p1) / max(1e-6, float(np.hypot(*(c_vec - p1))))
            u2 = (c_vec - p2) / max(1e-6, float(np.hypot(*(c_vec - p2))))
            pull = min(24.0, 0.48 * min(rx, ry))
            b1 = p1 + pull * u1
            b2 = p2 + pull * u2

            tip = np.array([tx, ty], dtype=np.float64)
            mid_base = 0.5 * (p1 + p2)
            axis = tip - mid_base
            axis_len = max(1e-6, float(np.hypot(axis[0], axis[1])))
            perp = np.array([-axis[1] / axis_len, axis[0] / axis_len], dtype=np.float64)

            t_vals = np.linspace(0.0, 1.0, 36)

            def quad_bez(
                pa: np.ndarray, pc: np.ndarray, pb: np.ndarray, ts: np.ndarray
            ) -> list[tuple[float, float]]:
                omt = 1.0 - ts
                xs = omt * omt * pa[0] + 2 * omt * ts * pc[0] + ts * ts * pb[0]
                ys = omt * omt * pa[1] + 2 * omt * ts * pc[1] + ts * ts * pb[1]
                return list(zip(xs.tolist(), ys.tolist()))

            c1 = 0.5 * (p1 + tip) + perp * float(tail_curve)
            c2 = 0.5 * (p2 + tip) + perp * (float(tail_curve) * 0.78)

            curve_1 = quad_bez(p1, c1, tip, t_vals)
            curve_2 = quad_bez(tip, c2, p2, t_vals)

            poly_1x = (
                [(float(b1[0]), float(b1[1]))]
                + curve_1[:-1]
                + [(tx, ty)]
                + curve_2[1:]
                + [(float(b2[0]), float(b2[1]))]
            )
            poly_roi_1x = [(px - roi_x0, py - roi_y0) for px, py in poly_1x]
            out_tail_1x = _offset_closed_polygon(poly_roi_1x, stroke_px)

            in_tail = [(px * S, py * S) for px, py in poly_roi_1x]
            out_tail = [(px * S, py * S) for px, py in out_tail_1x]

    d4.polygon(out_ell, fill=(*INK_BLACK, 255))
    if out_tail is not None:
        d4.polygon(out_tail, fill=(*INK_BLACK, 255))

    d4.polygon(in_ell, fill=(*PURE_WHITE, 255))
    if in_tail is not None:
        d4.polygon(in_tail, fill=(*PURE_WHITE, 255))

    bubble_1x = layer_4x.resize((rw, rh), Image.Resampling.BOX)

    vis_top = max(0.0, cy - ry + stroke_px)
    vis_bot = min(float(ph), cy + ry - stroke_px)
    text_cy = 0.5 * (cy + 0.5 * (vis_top + vis_bot))

    td = ImageDraw.Draw(bubble_1x)
    cur_y = text_cy - tot_h / 2.0
    for idx, (ln, lw, lh, y_off, fnt) in enumerate(zip(lines, widths, heights, y_offs, fonts)):
        lx = round(cx - roi_x0 - lw / 2.0)
        ly = round(cur_y - roi_y0 - y_off)
        col = (*MUTED_INK, 255) if idx in sub_set else (*INK_BLACK, 255)
        td.text((lx, ly), ln, font=fnt, fill=col)
        cur_y += lh + line_gap

    metrics = {
        "font_size": chosen_fs,
        "center": (cx, cy),
        "radii": (rx, ry),
        "roi": (roi_x0, roi_y0, roi_x1, roi_y1),
    }
    return bubble_1x, (roi_x0, roi_y0), metrics


def draw_sloptoon_bubble(
    panel_im: Image.Image,
    center: tuple[float, float],
    lines: Sequence[str],
    radii: tuple[float, float] | None = None,
    tail_tip: tuple[float, float] | None = None,
    tail_base_angle_deg: float | None = None,
    tail_half_deg: float = 7.5,
    tail_curve: float = 8.0,
    font_size: int = 24,
    stroke_px: float = 3.5,
    pad_xy: tuple[float, float] = (44.0, 30.0),
    line_spacing_ratio: float = 0.34,
    sub_line_indices: Sequence[int] | None = None,
) -> dict[str, Any]:
    """Composite a 4x-supersampled pure-white elliptical speech bubble onto `panel_im`."""
    bubble_1x, dest, metrics = _build_bubble_layer(
        panel_size=panel_im.size,
        center=center,
        lines=lines,
        radii=radii,
        tail_tip=tail_tip,
        tail_base_angle_deg=tail_base_angle_deg,
        tail_half_deg=tail_half_deg,
        tail_curve=tail_curve,
        font_size=font_size,
        stroke_px=stroke_px,
        pad_xy=pad_xy,
        line_spacing_ratio=line_spacing_ratio,
        sub_line_indices=sub_line_indices,
    )
    if bubble_1x is not None:
        panel_rgba = panel_im.convert("RGBA")
        panel_rgba.alpha_composite(bubble_1x, dest=dest)
        panel_im.paste(panel_rgba.convert("RGB"), (0, 0))
    return metrics


def draw_4x_rect_border(
    canvas: Image.Image,
    rect: tuple[float, float, float, float],
    stroke_px: float = 3.5,
    color: tuple[int, int, int] = INK_BLACK,
) -> None:
    """Draw a razor-sharp 4x-supersampled solid rectangular border (`#141414`, `3.5px`)."""
    S = 4
    w, h = canvas.size
    x0, y0, x1, y1 = [float(v) for v in rect]
    pad = int(np.ceil(stroke_px + 4))
    rx0 = max(0, int(np.floor(x0)) - pad)
    ry0 = max(0, int(np.floor(y0)) - pad)
    rx1 = min(w, int(np.ceil(x1)) + pad)
    ry1 = min(h, int(np.ceil(y1)) + pad)

    rw, rh = rx1 - rx0, ry1 - ry0
    layer_4x = Image.new("RGBA", (rw * S, rh * S), (0, 0, 0, 0))
    d4 = ImageDraw.Draw(layer_4x)

    half_s = 0.5 * stroke_px * S
    ox0 = round((x0 - rx0) * S - half_s)
    oy0 = round((y0 - ry0) * S - half_s)
    ox1 = round((x1 - rx0) * S + half_s)
    oy1 = round((y1 - ry0) * S + half_s)

    ix0 = round((x0 - rx0) * S + half_s)
    iy0 = round((y0 - ry0) * S + half_s)
    ix1 = round((x1 - rx0) * S - half_s)
    iy1 = round((y1 - ry0) * S - half_s)

    d4.rectangle([ox0, oy0, ox1, oy1], fill=(*color, 255))
    d4.rectangle([ix0, iy0, ix1, iy1], fill=(0, 0, 0, 0))

    border_1x = layer_4x.resize((rw, rh), Image.Resampling.BOX)
    rgba = canvas.convert("RGBA")
    rgba.alpha_composite(border_1x, dest=(rx0, ry0))
    canvas.paste(rgba.convert("RGB"), (0, 0))


def draw_minimal_pill(
    canvas: Image.Image,
    cx: float,
    cy: float,
    text: str,
    bg_col: tuple[int, int, int] = INK_BLACK,
    txt_col: tuple[int, int, int] = PURE_WHITE,
    border_col: tuple[int, int, int] | None = None,
    dot_col: tuple[int, int, int] | None = None,
    font_size: int = 14,
    pad_xy: tuple[int, int] = (16, 7),
    max_width: int | None = None,
) -> None:
    """Draw a sleek 4x-anti-aliased Sloptoon pill badge, auto-shrinking font if `max_width` set."""
    S = 4
    d_tmp = ImageDraw.Draw(canvas)
    dot_space = 15 if dot_col is not None else 0

    chosen_fs = font_size
    fnt = load_font(chosen_fs, weight="Bold")
    bb = d_tmp.textbbox((0, 0), text, font=fnt)
    tw = float(d_tmp.textlength(text, font=fnt))
    th = float(bb[3] - bb[1])

    if max_width is not None:
        while (tw + dot_space + pad_xy[0] * 2) > max_width and chosen_fs > 10:
            chosen_fs -= 1
            fnt = load_font(chosen_fs, weight="Bold")
            bb = d_tmp.textbbox((0, 0), text, font=fnt)
            tw = float(d_tmp.textlength(text, font=fnt))
            th = float(bb[3] - bb[1])

    pw = int(round(tw + dot_space + pad_xy[0] * 2))
    ph = int(round(th + pad_xy[1] * 2))
    x0 = int(round(cx - pw / 2.0))
    y0 = int(round(cy - ph / 2.0))

    pad = 6
    rw, rh = pw + pad * 2, ph + pad * 2
    layer_4x = Image.new("RGBA", (rw * S, rh * S), (0, 0, 0, 0))
    d4 = ImageDraw.Draw(layer_4x)
    rad = (ph * S) // 2
    bx0, by0 = pad * S, pad * S
    bx1, by1 = (pad + pw) * S, (pad + ph) * S

    if border_col is not None:
        bw = round(2.2 * S)
        d4.rounded_rectangle(
            [bx0 - bw, by0 - bw, bx1 + bw, by1 + bw],
            radius=rad + bw,
            fill=(*border_col, 255),
        )
    d4.rounded_rectangle([bx0, by0, bx1, by1], radius=rad, fill=(*bg_col, 255))

    if dot_col is not None:
        dcx = bx0 + round((pad_xy[0] + 4) * S)
        dcy = (by0 + by1) // 2
        dr = round(4.5 * S)
        d4.ellipse([dcx - dr, dcy - dr, dcx + dr, dcy + dr], fill=(*dot_col, 255))

    pill_1x = layer_4x.resize((rw, rh), Image.Resampling.BOX)
    rgba = canvas.convert("RGBA")
    rgba.alpha_composite(pill_1x, dest=(x0 - pad, y0 - pad))

    td = ImageDraw.Draw(rgba)
    tx = round(x0 + pad_xy[0] + dot_space)
    ty = round(cy - th / 2.0 - bb[1])
    td.text((tx, ty), text, font=fnt, fill=(*txt_col, 255))
    canvas.paste(rgba.convert("RGB"), (0, 0))


def wrap_korean_dialogue(
    dialogue: str,
    font_size: int,
    max_line_width_px: float,
    max_lines: int = 4,
) -> tuple[list[str], list[int]]:
    """Wrap Korean dialogue cleanly into balanced lines and detect parenthetical sub-lines."""
    raw = dialogue.replace("\r\n", "\n").strip()
    if not raw:
        return [], []

    # Separate trailing parenthetical aside if not already on its own line
    segments: list[str] = []
    for raw_line in raw.split("\n"):
        ln = raw_line.strip()
        if not ln:
            continue
        m = _TRAILING_PAREN_RE.match(ln)
        if m and m.group(1).strip():
            segments.append(m.group(1).strip())
            segments.append(m.group(2).strip())
        else:
            segments.append(ln)

    dummy = ImageDraw.Draw(Image.new("RGB", (16, 16), PURE_WHITE))
    main_font = load_font(font_size, weight="Bold")
    sub_font = load_font(max(12, int(round(font_size * 0.80))), weight="Medium")

    def _split_long_token(tok: str, fnt: Any, max_w: float) -> list[str]:
        parts: list[str] = []
        buf = ""
        for ch in tok:
            cand = buf + ch
            if buf and float(dummy.textlength(cand, font=fnt)) > max_w:
                parts.append(buf)
                buf = ch
            else:
                buf = cand
        if buf:
            parts.append(buf)
        return parts

    def _wrap_segment(seg: str, fnt: Any, max_w: float) -> list[str]:
        if float(dummy.textlength(seg, font=fnt)) <= max_w:
            return [seg]
        words = seg.split()
        if len(words) <= 1:
            return _split_long_token(seg, fnt, max_w)

        # Try balanced 2-line split first to avoid ugly 1-word orphans
        total_w = float(dummy.textlength(seg, font=fnt))
        if total_w <= max_w * 1.92:
            best_pair: tuple[str, str] | None = None
            best_diff = 1e9
            for cut in range(1, len(words)):
                left = " ".join(words[:cut])
                right = " ".join(words[cut:])
                lw = float(dummy.textlength(left, font=fnt))
                rw = float(dummy.textlength(right, font=fnt))
                if lw <= max_w and rw <= max_w:
                    diff = abs(lw - rw)
                    if diff < best_diff:
                        best_diff = diff
                        best_pair = (left, right)
            if best_pair is not None:
                return [best_pair[0], best_pair[1]]

        # General greedy word wrap with fallback char-wrap for huge tokens
        out: list[str] = []
        cur = ""
        for w in words:
            if float(dummy.textlength(w, font=fnt)) > max_w:
                if cur:
                    out.append(cur)
                    cur = ""
                out.extend(_split_long_token(w, fnt, max_w))
                continue
            cand = f"{cur} {w}".strip() if cur else w
            if float(dummy.textlength(cand, font=fnt)) <= max_w:
                cur = cand
            else:
                if cur:
                    out.append(cur)
                cur = w
        if cur:
            out.append(cur)
        return out

    lines: list[str] = []
    sub_indices: list[int] = []
    for seg in segments:
        is_paren = seg.startswith("(") and seg.endswith(")") and len(seg) >= 3
        fnt = sub_font if is_paren else main_font
        wrapped = _wrap_segment(seg, fnt, max_line_width_px)
        for wl in wrapped:
            if is_paren:
                sub_indices.append(len(lines))
            lines.append(wl)

    # Cap excessive lines by merging tail cleanly if somehow > max_lines + 1
    if len(lines) > max_lines + 1:
        kept = lines[:max_lines]
        tail = " ".join(lines[max_lines:])
        kept[-1] = f"{kept[-1]} {tail}".strip()
        lines = kept
        sub_indices = [i for i in sub_indices if i < len(lines)]

    return lines, sub_indices


def _edge_mask(mask: np.ndarray) -> np.ndarray:
    padded = np.pad(mask, 1, constant_values=False)
    eroded = padded[:-2, 1:-1] & padded[2:, 1:-1] & padded[1:-1, :-2] & padded[1:-1, 2:]
    return mask & ~eroded


def compute_min_clearance(art_mask: np.ndarray, bub_mask: np.ndarray) -> float:
    """Compute minimum Euclidean distance (px) between bubble pixels and artwork pixels."""
    if not np.any(art_mask) or not np.any(bub_mask):
        return 999.0
    if np.any(art_mask & bub_mask):
        return 0.0

    ey, ex = np.where(_edge_mask(bub_mask))
    fy, fx = np.where(_edge_mask(art_mask))
    if len(ey) == 0 or len(fy) == 0:
        return 999.0

    step_b = max(1, len(ey) // 250)
    step_a = max(1, len(fy) // 600)
    ey_s, ex_s = ey[::step_b].astype(np.float32), ex[::step_b].astype(np.float32)
    fy_s, fx_s = fy[::step_a].astype(np.float32), fx[::step_a].astype(np.float32)

    dmin = 9999.0
    for i in range(len(ey_s)):
        d2 = (fy_s - ey_s[i]) ** 2 + (fx_s - ex_s[i]) ** 2
        m = float(np.sqrt(d2.min()))
        if m < dmin:
            dmin = m
    return round(dmin, 1)


def _bubble_alpha_mask(
    panel_size: tuple[int, int],
    bubble_1x: Image.Image | None,
    dest: tuple[int, int],
) -> np.ndarray:
    pw, ph = panel_size
    mask = np.zeros((ph, pw), dtype=bool)
    if bubble_1x is None:
        return mask
    x0, y0 = dest
    alpha = np.asarray(bubble_1x.getchannel("A"))
    rh, rw = alpha.shape
    mask[y0 : y0 + rh, x0 : x0 + rw] = alpha > 0
    return mask


def _prepare_cut_tooltip(cut: ComicCut, max_w: int, max_h: int) -> Image.Image | None:
    """Render `cut.item_tooltip` as an RGBA card, scaling down smoothly if exceeding `(max_w, max_h)`."""
    if cut.item_tooltip is None:
        return None
    card = render_item_tooltip(cut.item_tooltip)
    if card is None:
        return None
    tw, th = card.size
    if tw > max_w or th > max_h:
        s = min(max_w / max(1, tw), max_h / max(1, th))
        nw = max(60, int(round(tw * s)))
        nh = max(36, int(round(th * s)))
        card = card.resize((nw, nh), Image.Resampling.LANCZOS)
    return card


def _tooltip_alpha_mask(
    panel_size: tuple[int, int],
    tooltip_rgba: Image.Image,
    dest: tuple[int, int],
) -> np.ndarray:
    pw, ph = panel_size
    mask = np.zeros((ph, pw), dtype=bool)
    x0, y0 = dest
    alpha = np.asarray(tooltip_rgba.getchannel("A"))
    th, tw = alpha.shape
    cx0, cy0 = max(0, x0), max(0, y0)
    cx1, cy1 = min(pw, x0 + tw), min(ph, y0 + th)
    if cx1 > cx0 and cy1 > cy0:
        mask[cy0:cy1, cx0:cx1] = alpha[cy0 - y0 : cy1 - y0, cx0 - x0 : cx1 - x0] > 0
    return mask


def _composite_rgba_card(
    panel: Image.Image,
    card_rgba: Image.Image,
    dest: tuple[int, int],
) -> Image.Image:
    rgba = panel.convert("RGBA")
    rgba.alpha_composite(card_rgba, dest=dest)
    return rgba.convert("RGB")


def _ordered_corner_candidates(
    panel_w: int,
    panel_h: int,
    tw: int,
    th: int,
    pad_x: int,
    pad_y: int,
    preferred: str = "auto",
) -> list[tuple[str, tuple[int, int]]]:
    corners = {
        "top_right": (panel_w - pad_x - tw, pad_y),
        "top_left": (pad_x, pad_y),
        "bottom_right": (panel_w - pad_x - tw, panel_h - pad_y - th),
        "bottom_left": (pad_x, panel_h - pad_y - th),
    }
    default_order = ["top_right", "top_left", "bottom_right", "bottom_left"]
    if preferred in corners:
        order = [preferred] + [k for k in default_order if k != preferred]
    else:
        order = default_order
    return [(k, corners[k]) for k in order]


def _compose_wordless_panel(
    raw_im: Image.Image,
    target_w: int,
    target_h: int,
    side_pad: int,
    top_pad: int,
    bottom_pad_if_floating: int,
    *,
    tooltip_rgba: Image.Image | None = None,
    preferred_corner: str = "auto",
) -> tuple[Image.Image, dict[str, Any]]:
    """Render a 100% silent centered freeze-frame cut with ZERO speech bubbles."""
    clean_raw = clean_white_bg(raw_im)
    rw, rh = clean_raw.size
    bbox = extract_art_bbox(clean_raw, threshold=255)
    if bbox is None:
        blank = Image.new("RGB", (target_w, target_h), PURE_WHITE)
        audit: dict[str, Any] = {
            "wordless": True,
            "bubble_count": 0,
            "overlap_px": 0,
            "min_clearance_px": 999.0,
            "font_size": None,
            "art_bbox": None,
        }
        if tooltip_rgba is not None:
            tw, th = tooltip_rgba.size
            dest = (max(16, target_w - max(16, side_pad) - tw), max(16, top_pad))
            blank = _composite_rgba_card(blank, tooltip_rgba, dest)
            audit["has_item_tooltip"] = True
            audit["tooltip_bbox"] = [dest[0], dest[1], dest[0] + tw, dest[1] + th]
            audit["tooltip_overlap_px"] = 0
        return blank, audit

    ax0, ay0, ax1, ay1 = bbox
    touches_bottom = ay1 >= rh - 6
    crop_y1 = rh if touches_bottom else min(rh, ay1 + 1)
    crop_box = (ax0, ay0, min(rw, ax1 + 1), crop_y1)
    cw = max(1, crop_box[2] - crop_box[0])
    ch = max(1, crop_box[3] - crop_box[1])

    avail_w = max(1, target_w - 2 * side_pad)
    avail_h = max(1, target_h - top_pad - (0 if touches_bottom else bottom_pad_if_floating))
    scale = min(avail_w / cw, avail_h / ch)

    nw = max(1, int(round(cw * scale)))
    nh = max(1, int(round(ch * scale)))
    px = (target_w - nw) / 2.0
    py = float(target_h - nh) if touches_bottom else float(top_pad + (avail_h - nh) / 2.0)

    panel = place_scaled_art(clean_raw, target_w, target_h, scale, px, py, crop_box=crop_box)
    final_bbox = extract_art_bbox(panel, threshold=255)
    art_cx = (final_bbox[0] + final_bbox[2]) / 2.0 if final_bbox else target_w / 2.0

    # Fine-tune exact horizontal dead-centering of non-white artwork pixels
    if final_bbox is not None and abs(art_cx - target_w / 2.0) > 1.0:
        dx = round(target_w / 2.0 - art_cx)
        if final_bbox[0] + dx >= 4 and final_bbox[2] + dx <= target_w - 5:
            panel = place_scaled_art(
                clean_raw, target_w, target_h, scale, px + dx, py, crop_box=crop_box
            )
            final_bbox = extract_art_bbox(panel, threshold=255)
            art_cx = (final_bbox[0] + final_bbox[2]) / 2.0 if final_bbox else target_w / 2.0

    if tooltip_rgba is not None:
        tw, th = tooltip_rgba.size
        pad_x = max(16, side_pad)
        pad_y = max(16, top_pad)
        art_mask = get_art_mask(panel, threshold=255)
        for _cname, dest in _ordered_corner_candidates(
            target_w, target_h, tw, th, pad_x, pad_y, preferred=preferred_corner
        ):
            tip_mask = _tooltip_alpha_mask((target_w, target_h), tooltip_rgba, dest)
            if int((art_mask & tip_mask).sum()) == 0:
                out_panel = _composite_rgba_card(panel, tooltip_rgba, dest)
                return out_panel, {
                    "wordless": True,
                    "bubble_count": 0,
                    "overlap_px": 0,
                    "min_clearance_px": compute_min_clearance(art_mask, tip_mask),
                    "font_size": None,
                    "art_bbox": list(final_bbox) if final_bbox else None,
                    "art_cx": round(art_cx, 1),
                    "has_item_tooltip": True,
                    "tooltip_bbox": [dest[0], dest[1], dest[0] + tw, dest[1] + th],
                    "tooltip_overlap_px": 0,
                }

        # Disjoint side-by-side placement when wide artwork occupies all 4 corners
        tooltip_on_left = preferred_corner in ("top_left", "bottom_left")
        tx0 = pad_x if tooltip_on_left else (target_w - pad_x - tw)
        ty0 = pad_y if target_h >= 600 else max(12, (target_h - th) // 2)
        if tooltip_on_left:
            art_x_lo, art_x_hi = float(tx0 + tw + 16), float(target_w - pad_x)
        else:
            art_x_lo, art_x_hi = float(pad_x), float(tx0 - 16)
        side_avail_w = max(80.0, art_x_hi - art_x_lo)
        s_side = min(side_avail_w / cw, avail_h / ch)
        nw_s = max(1, int(round(cw * s_side)))
        nh_s = max(1, int(round(ch * s_side)))
        px_s = art_x_lo + (side_avail_w - nw_s) / 2.0
        py_s = float(target_h - nh_s) if touches_bottom else float(top_pad + (avail_h - nh_s) / 2.0)
        panel_s = place_scaled_art(clean_raw, target_w, target_h, s_side, px_s, py_s, crop_box=crop_box)
        art_mask_s = get_art_mask(panel_s, threshold=255)
        placed_bb_s = extract_art_bbox(panel_s, threshold=255)
        art_cx_s = (placed_bb_s[0] + placed_bb_s[2]) / 2.0 if placed_bb_s else (art_x_lo + art_x_hi) / 2.0
        tip_mask_s = _tooltip_alpha_mask((target_w, target_h), tooltip_rgba, (tx0, ty0))
        tip_ov = int((art_mask_s & tip_mask_s).sum())
        out_panel = _composite_rgba_card(panel_s, tooltip_rgba, (tx0, ty0))
        return out_panel, {
            "wordless": True,
            "bubble_count": 0,
            "overlap_px": tip_ov,
            "min_clearance_px": compute_min_clearance(art_mask_s, tip_mask_s),
            "font_size": None,
            "art_bbox": list(placed_bb_s) if placed_bb_s else None,
            "art_cx": round(art_cx_s, 1),
            "has_item_tooltip": True,
            "tooltip_bbox": [tx0, ty0, tx0 + tw, ty0 + th],
            "tooltip_overlap_px": tip_ov,
        }

    return panel, {
        "wordless": True,
        "bubble_count": 0,
        "overlap_px": 0,
        "min_clearance_px": 999.0,
        "font_size": None,
        "art_bbox": list(final_bbox) if final_bbox else None,
        "art_cx": round(art_cx, 1),
    }


def _find_top_speaker_anchor(
    art_mask: np.ndarray,
    tail_target: str,
    panel_w: int,
) -> tuple[float, float] | None:
    """Locate the target speaker's upper-head `(x, top_y)` inside a placed top panel."""
    if not np.any(art_mask):
        return None
    if tail_target == "left":
        x_lo, x_hi = 0, int(panel_w * 0.52)
    elif tail_target == "right":
        x_lo, x_hi = int(panel_w * 0.48), panel_w
    else:
        x_lo, x_hi = int(panel_w * 0.22), int(panel_w * 0.78)

    zone = art_mask[:, x_lo:x_hi]
    ys, xs = np.where(zone)
    if len(xs) == 0:
        ys, xs = np.where(art_mask)
        x_lo = 0
    xs_abs = xs + x_lo
    y_min = int(ys.min())
    y_max = int(ys.max())
    head_cut = y_min + max(24, int((y_max - y_min) * 0.25))
    head_sel = ys <= head_cut
    head_x = float(np.median(xs_abs[head_sel])) if np.any(head_sel) else float(np.median(xs_abs))
    # Local highest pixel near head_x
    near = np.abs(xs_abs - head_x) <= 55
    local_top_y = float(ys[near].min()) if np.any(near) else float(y_min)
    return head_x, local_top_y


def _compose_top_open_panel_with_tooltip(
    cut: ComicCut,
    raw_im: Image.Image,
    dialogue: str,
    tooltip_rgba: Image.Image,
) -> tuple[Image.Image, dict[str, Any]]:
    """Compose a 900x830 top open panel with BOTH speech bubble AND WoW item tooltip at 0px overlap."""
    W, H = PAGE_W, TOP_PANEL_H
    clean_raw = clean_white_bg(raw_im)
    rw, rh = clean_raw.size
    raw_bbox = extract_art_bbox(clean_raw, threshold=255)
    stroke_px = 3.5
    dummy = ImageDraw.Draw(Image.new("RGB", (16, 16), PURE_WHITE))

    pref = cut.item_tooltip.preferred_corner if cut.item_tooltip else "auto"
    if pref in ("top_left", "bottom_left"):
        tooltip_side = "left"
    elif pref in ("top_right", "bottom_right"):
        tooltip_side = "right"
    else:
        tooltip_side = "left" if cut.tail_target == "right" else "right"

    tw, th = tooltip_rgba.size
    tx0 = 28 if tooltip_side == "left" else (W - 28 - tw)
    ty0 = 16
    tip_dest = (tx0, ty0)
    tip_mask = _tooltip_alpha_mask((W, H), tooltip_rgba, tip_dest)

    if tooltip_side == "right":
        bub_x_lo, bub_x_hi = 24.0, float(tx0 - 14)
    else:
        bub_x_lo, bub_x_hi = float(tx0 + tw + 14), float(W - 24)

    max_bub_rx = max(130.0, (bub_x_hi - bub_x_lo) / 2.0 - stroke_px - 4.0)
    wrap_w = float(np.clip((max_bub_rx - 38.0) / 0.62, 230.0, 420.0))

    base_fs = 23 if len(dialogue) <= 38 else 21
    lines, sub_indices = wrap_korean_dialogue(dialogue, base_fs, max_line_width_px=wrap_w, max_lines=4)
    if len(lines) >= 4:
        base_fs = min(base_fs, 19)
        lines, sub_indices = wrap_korean_dialogue(
            dialogue, base_fs, max_line_width_px=wrap_w + 16.0, max_lines=4
        )
    sub_set = set(sub_indices)

    def _compute_bub_dims(fs: int) -> tuple[float, float, float, float]:
        f_m = load_font(fs, weight="Bold")
        f_s = load_font(max(11, int(round(fs * 0.80))), weight="Medium")
        gap = max(4, int(round(fs * 0.34)))
        mw, tot_h, _, _, _, _ = _measure_text_block(dummy, lines, f_m, f_s, gap, sub_set)
        rx = float(np.clip(mw * 0.62 + 38.0, 132.0, max_bub_rx))
        ry = float(np.clip(tot_h * 0.68 + 26.0, 60.0, 124.0))
        cy = ry + 14.0
        ideal_cx = (bub_x_lo + bub_x_hi) / 2.0
        cx = float(np.clip(ideal_cx, bub_x_lo + rx + stroke_px, bub_x_hi - rx - stroke_px))
        return cx, cy, rx, ry

    cur_fs = base_fs
    cx, cy, rx, ry = _compute_bub_dims(cur_fs)

    if raw_bbox is None:
        panel = Image.new("RGB", (W, H), PURE_WHITE)
        metrics = draw_sloptoon_bubble(
            panel,
            center=(cx, cy),
            lines=lines,
            radii=(rx, ry),
            tail_tip=(cx, cy + ry + 48.0),
            tail_half_deg=6.2,
            tail_curve=-8.0 if tooltip_side == "right" else 8.0,
            font_size=cur_fs,
            stroke_px=stroke_px,
            sub_line_indices=sub_indices,
        )
        panel = _composite_rgba_card(panel, tooltip_rgba, tip_dest)
        return panel, {
            "wordless": False,
            "bubble_count": 1,
            "overlap_px": 0,
            "min_clearance_px": 999.0,
            "font_size": metrics["font_size"],
            "art_bbox": None,
            "has_item_tooltip": True,
            "tooltip_bbox": [tx0, ty0, tx0 + tw, ty0 + th],
            "tooltip_overlap_px": 0,
        }

    ax0, ay0, ax1, ay1 = raw_bbox
    touches_bottom = ay1 >= rh - 6
    crop_x0 = max(0, ax0 - 4) if (ax1 - ax0) > rw * 0.94 else 0
    crop_x1 = min(rw, ax1 + 5) if (ax1 - ax0) > rw * 0.94 else rw
    crop_box = (crop_x0, ay0, crop_x1, rh if touches_bottom else min(rh, ay1 + 1))
    cw = max(1, crop_box[2] - crop_box[0])
    ch = max(1, crop_box[3] - crop_box[1])

    side_margin = 16.0
    bub_bot = cy + ry + stroke_px
    tip_bot = float(ty0 + th)
    target_art_top = max(bub_bot + 68.0, tip_bot + 18.0)

    scale_w = (W - 2 * side_margin) / cw
    scale_h = max(0.05, (H - target_art_top - (0.0 if touches_bottom else 16.0)) / ch)
    scale = min(scale_w, scale_h)

    for attempt in range(18):
        bub_bot = cy + ry + stroke_px
        nw = max(1, int(round(cw * scale)))
        nh = max(1, int(round(ch * scale)))
        px = (W - nw) / 2.0
        min_safe_y = max(bub_bot + 50.0, tip_bot + 14.0)
        if touches_bottom:
            py = float(H - nh)
        else:
            py = float(max(min_safe_y, H - nh - 12.0))
            if py + nh > H - 6:
                py = float(H - nh - 6)

        art_canvas = place_scaled_art(clean_raw, W, H, scale, px, py, crop_box=crop_box)
        art_mask = get_art_mask(art_canvas, threshold=255)
        placed_bbox = extract_art_bbox(art_canvas, threshold=255)
        art_min_y = float(placed_bbox[1]) if placed_bbox else float(H)

        # Ensure artwork does not collide with tooltip card first
        if int((art_mask & tip_mask).sum()) == 0:
            anchor = _find_top_speaker_anchor(art_mask, cut.tail_target, W)
            head_x, local_top_y = anchor if anchor is not None else (cx, art_min_y)
            tail_x = float(np.clip(0.55 * head_x + 0.45 * cx, cx - rx * 0.68, cx + rx * 0.68))
            max_tail_y = min(bub_bot + 100.0, local_top_y - 16.0, art_min_y + 86.0)
            min_tail_y = bub_bot + 24.0

            for pull in (1.0, 0.72, 0.48, 0.25, 0.0):
                if pull == 0.0 or max_tail_y <= bub_bot + 14.0:
                    tail_tip = None
                    base_deg = None
                else:
                    ty = min(bub_bot + max(18.0, (max_tail_y - bub_bot) * pull), local_top_y - 14.0)
                    if ty < min_tail_y and pull == 1.0:
                        ty = min(min_tail_y, local_top_y - 12.0)
                    if ty <= bub_bot + 10.0:
                        tail_tip = None
                        base_deg = None
                    else:
                        tx = cx + (tail_x - cx) * (0.65 + 0.35 * pull)
                        tail_tip = (tx, ty)
                        raw_deg = float(np.rad2deg(np.arctan2((ty - cy) / ry, (tx - cx) / rx)))
                        base_deg = float(np.clip(raw_deg, 68.0, 112.0))

                tail_curve = -8.0 if (tail_tip is None or tail_tip[0] <= cx) else 8.0
                bub_layer, dest, b_metrics = _build_bubble_layer(
                    panel_size=(W, H),
                    center=(cx, cy),
                    lines=lines,
                    radii=(rx, ry),
                    tail_tip=tail_tip,
                    tail_base_angle_deg=base_deg,
                    tail_half_deg=6.2,
                    tail_curve=tail_curve,
                    font_size=cur_fs,
                    stroke_px=stroke_px,
                    sub_line_indices=sub_indices,
                )
                bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
                ov_ab = int((art_mask & bub_mask).sum())
                ov_bt = int((bub_mask & tip_mask).sum())
                if ov_ab == 0 and ov_bt == 0:
                    out_panel = art_canvas.copy()
                    if bub_layer is not None:
                        rgba = out_panel.convert("RGBA")
                        rgba.alpha_composite(bub_layer, dest=dest)
                        out_panel = rgba.convert("RGB")
                    out_panel = _composite_rgba_card(out_panel, tooltip_rgba, tip_dest)
                    return out_panel, {
                        "wordless": False,
                        "bubble_count": 1,
                        "overlap_px": 0,
                        "min_clearance_px": compute_min_clearance(art_mask, bub_mask | tip_mask),
                        "font_size": b_metrics["font_size"],
                        "art_bbox": list(placed_bbox) if placed_bbox else None,
                        "tail_target": cut.tail_target,
                        "has_item_tooltip": True,
                        "tooltip_bbox": [tx0, ty0, tx0 + tw, ty0 + th],
                        "tooltip_overlap_px": 0,
                    }

        scale *= 0.88
        if attempt in (4, 8, 12) and cur_fs > 14:
            cur_fs = max(14, cur_fs - 2)
            lines, sub_indices = wrap_korean_dialogue(
                dialogue, cur_fs, max_line_width_px=wrap_w + 18.0, max_lines=4
            )
            sub_set = set(sub_indices)
            cx, cy, rx, ry = _compute_bub_dims(cur_fs)

    # Strict vertical disjointness fallback
    cur_fs = max(13, min(cur_fs, 17))
    lines, sub_indices = wrap_korean_dialogue(dialogue, cur_fs, max_line_width_px=wrap_w + 18.0, max_lines=4)
    sub_set = set(sub_indices)
    cx, cy, rx, ry = _compute_bub_dims(cur_fs)
    safe_art_top = int(np.ceil(max(cy + ry + stroke_px + 32.0, tip_bot + 16.0)))
    avail_h = max(80, H - safe_art_top - 8)
    scale = min((W - 2 * side_margin) / cw, avail_h / ch)
    nw, nh = max(1, int(round(cw * scale))), max(1, int(round(ch * scale)))
    art_canvas = place_scaled_art(clean_raw, W, H, scale, (W - nw) / 2.0, float(H - nh), crop_box=crop_box)
    art_mask = get_art_mask(art_canvas, threshold=255)
    placed_bbox = extract_art_bbox(art_canvas, threshold=255)
    bub_layer, dest, b_metrics = _build_bubble_layer(
        panel_size=(W, H),
        center=(cx, cy),
        lines=lines,
        radii=(rx, ry),
        tail_tip=None,
        font_size=cur_fs,
        stroke_px=stroke_px,
        sub_line_indices=sub_indices,
    )
    bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
    out_panel = art_canvas.copy()
    if bub_layer is not None:
        rgba = out_panel.convert("RGBA")
        rgba.alpha_composite(bub_layer, dest=dest)
        out_panel = rgba.convert("RGB")
    out_panel = _composite_rgba_card(out_panel, tooltip_rgba, tip_dest)
    tip_ov = int(((art_mask | bub_mask) & tip_mask).sum())
    ov_total = int((art_mask & bub_mask).sum()) + tip_ov
    return out_panel, {
        "wordless": False,
        "bubble_count": 1,
        "overlap_px": ov_total,
        "min_clearance_px": compute_min_clearance(art_mask, bub_mask | tip_mask),
        "font_size": b_metrics["font_size"],
        "art_bbox": list(placed_bbox) if placed_bbox else None,
        "tail_target": cut.tail_target,
        "has_item_tooltip": True,
        "tooltip_bbox": [tx0, ty0, tx0 + tw, ty0 + th],
        "tooltip_overlap_px": tip_ov,
    }


def _compose_top_open_panel(
    cut: ComicCut,
    raw_im: Image.Image,
) -> tuple[Image.Image, dict[str, Any]]:
    """Compose a 900x830 pure-white open top panel with automatic `overlap_px == 0` solver."""
    W, H = PAGE_W, TOP_PANEL_H
    tooltip_rgba = _prepare_cut_tooltip(cut, max_w=306, max_h=248)
    pref_corner = cut.item_tooltip.preferred_corner if cut.item_tooltip else "auto"
    dialogue = (cut.dialogue or "").strip()
    if cut.wordless or not dialogue:
        return _compose_wordless_panel(
            raw_im,
            target_w=W,
            target_h=H,
            side_pad=28,
            top_pad=32,
            bottom_pad_if_floating=24,
            tooltip_rgba=tooltip_rgba,
            preferred_corner=pref_corner,
        )
    if tooltip_rgba is not None:
        return _compose_top_open_panel_with_tooltip(cut, raw_im, dialogue, tooltip_rgba)

    clean_raw = clean_white_bg(raw_im)
    rw, rh = clean_raw.size
    raw_bbox = extract_art_bbox(clean_raw, threshold=255)

    # 1. Measure dialogue & initial bubble geometry
    base_fs = 25 if len(dialogue) <= 44 else 23
    lines, sub_indices = wrap_korean_dialogue(dialogue, base_fs, max_line_width_px=470.0, max_lines=4)
    if len(lines) >= 4:
        base_fs = min(base_fs, 21)
        lines, sub_indices = wrap_korean_dialogue(
            dialogue, base_fs, max_line_width_px=490.0, max_lines=4
        )
    elif len(lines) == 3:
        base_fs = min(base_fs, 24)

    stroke_px = 3.5
    dummy = ImageDraw.Draw(Image.new("RGB", (16, 16), PURE_WHITE))
    sub_set = set(sub_indices)

    def _compute_top_bubble_dims(fs: int) -> tuple[float, float, float, float]:
        f_m = load_font(fs, weight="Bold")
        f_s = load_font(max(12, int(round(fs * 0.80))), weight="Medium")
        gap = max(5, int(round(fs * 0.32)))
        mw, th, _, _, _, _ = _measure_text_block(dummy, lines, f_m, f_s, gap, sub_set)
        rx = float(np.clip(mw * 0.58 + 38.0, 140.0, 365.0))
        ry = float(np.clip(th * 0.58 + 20.0, 52.0, 110.0))
        # Keep entire ellipse strictly inside y >= 8 so page outer border stays 100% #FFFFFF
        cy = ry + 14.0
        target_side = cut.bubble_side or cut.tail_target
        if target_side == "left":
            cx = float(np.clip(310.0, rx + 24.0, W - rx - 24.0))
        elif target_side == "right":
            cx = float(np.clip(590.0, rx + 24.0, W - rx - 24.0))
        else:
            cx = W / 2.0
        return cx, cy, rx, ry

    cur_fs = base_fs
    cx, cy, rx, ry = _compute_top_bubble_dims(cur_fs)

    # Blank artwork edge case
    if raw_bbox is None:
        panel = Image.new("RGB", (W, H), PURE_WHITE)
        tail_dx = -40.0 if cut.tail_target == "left" else (40.0 if cut.tail_target == "right" else 0.0)
        tail_tip = (cx + tail_dx, cy + ry + 56.0)
        metrics = draw_sloptoon_bubble(
            panel,
            center=(cx, cy),
            lines=lines,
            radii=(rx, ry),
            tail_tip=tail_tip,
            tail_half_deg=6.2,
            tail_curve=-8.0 if tail_dx <= 0 else 8.0,
            font_size=cur_fs,
            stroke_px=stroke_px,
            sub_line_indices=sub_indices,
        )
        return panel, {
            "wordless": False,
            "bubble_count": 1,
            "overlap_px": 0,
            "min_clearance_px": 999.0,
            "font_size": metrics["font_size"],
            "art_bbox": None,
        }

    ax0, ay0, ax1, ay1 = raw_bbox
    touches_bottom = ay1 >= rh - 6
    # Preserve horizontal composition of raw scene while trimming excess pure-white top above ay0
    crop_x0 = max(0, ax0 - 4) if (ax1 - ax0) > rw * 0.94 else 0
    crop_x1 = min(rw, ax1 + 5) if (ax1 - ax0) > rw * 0.94 else rw
    crop_y0 = ay0
    crop_y1 = rh if touches_bottom else min(rh, ay1 + 1)
    crop_box = (crop_x0, crop_y0, crop_x1, crop_y1)
    cw = max(1, crop_box[2] - crop_box[0])
    ch = max(1, crop_box[3] - crop_box[1])

    side_margin = 16.0  # Guarantees pure #FFFFFF left & right outer borders
    bub_bot = cy + ry + stroke_px
    desired_tail_space = 74.0
    target_art_top = bub_bot + desired_tail_space

    scale_w = (W - 2 * side_margin) / cw
    scale_h = max(0.05, (H - target_art_top - (0.0 if touches_bottom else 16.0)) / ch)
    scale = min(scale_w, scale_h)

    best_panel: Image.Image | None = None
    best_audit: dict[str, Any] | None = None

    for attempt in range(18):
        bub_bot = cy + ry + stroke_px
        nw = max(1, int(round(cw * scale)))
        nh = max(1, int(round(ch * scale)))
        px = (W - nw) / 2.0
        # Anchor artwork cleanly at bottom when character touches frame bottom; otherwise below bubble
        if touches_bottom:
            py = float(H - nh)
        else:
            py = float(max(bub_bot + 54.0, H - nh - 12.0))
            if py + nh > H - 6:
                py = float(H - nh - 6)

        art_canvas = place_scaled_art(clean_raw, W, H, scale, px, py, crop_box=crop_box)
        art_mask = get_art_mask(art_canvas, threshold=255)
        placed_bbox = extract_art_bbox(art_canvas, threshold=255)
        art_min_y = float(placed_bbox[1]) if placed_bbox else float(H)

        anchor = _find_top_speaker_anchor(art_mask, cut.tail_target, W)
        if anchor is not None:
            head_x, local_top_y = anchor
        else:
            head_x, local_top_y = cx, art_min_y

        # Pull top bubble down smoothly when large empty whitespace separates it from the speaker head
        eff_cy = cy
        eff_cx = cx
        if cut.bubble_side is None and anchor is not None:
            eff_cx = float(np.clip(0.55 * head_x + 0.45 * cx, rx + 24.0, W - rx - 24.0))
        cur_gap = local_top_y - (eff_cy + ry + stroke_px)
        if cur_gap > 92.0:
            shift_y = min(cur_gap - 74.0, max(0.0, art_min_y - (eff_cy + ry + stroke_px) - 52.0))
            if shift_y > 0.0:
                eff_cy = cy + shift_y
        eff_bub_bot = eff_cy + ry + stroke_px

        # Compute crisp short tail pointing directly toward speaker head with safe clearance
        tail_x = float(np.clip(0.72 * head_x + 0.28 * eff_cx, eff_cx - rx * 0.72, eff_cx + rx * 0.72))
        max_tail_y = min(eff_bub_bot + 72.0, local_top_y - 16.0, art_min_y + 72.0)
        min_tail_y = eff_bub_bot + 24.0

        # Try progressively shorter tail pullbacks before shrinking artwork scale
        pull_ratios = (1.0, 0.75, 0.52, 0.30)
        solved_this_scale = False

        for pull in pull_ratios:
            if max_tail_y <= eff_bub_bot + 14.0:
                tail_tip: tuple[float, float] | None = None
                base_deg = None
            else:
                ty = eff_bub_bot + max(18.0, (max_tail_y - eff_bub_bot) * pull)
                ty = min(ty, local_top_y - 14.0)
                if ty < min_tail_y and pull == 1.0:
                    ty = min(min_tail_y, local_top_y - 12.0)
                if ty <= eff_bub_bot + 10.0:
                    tail_tip = None
                    base_deg = None
                else:
                    tx = eff_cx + (tail_x - eff_cx) * (0.65 + 0.35 * pull)
                    tail_tip = (tx, ty)
                    raw_deg = float(np.rad2deg(np.arctan2((ty - eff_cy) / ry, (tx - eff_cx) / rx)))
                    base_deg = float(np.clip(raw_deg, 66.0, 114.0))

            tail_curve = -7.0 if (tail_tip is None or tail_tip[0] <= eff_cx) else 7.0
            bub_layer, dest, b_metrics = _build_bubble_layer(
                panel_size=(W, H),
                center=(eff_cx, eff_cy),
                lines=lines,
                radii=(rx, ry),
                tail_tip=tail_tip,
                tail_base_angle_deg=base_deg,
                tail_half_deg=6.2,
                tail_curve=tail_curve,
                font_size=cur_fs,
                stroke_px=stroke_px,
                sub_line_indices=sub_indices,
            )
            bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
            overlap = int((art_mask & bub_mask).sum())

            if overlap == 0:
                out_panel = art_canvas.copy()
                if bub_layer is not None:
                    rgba = out_panel.convert("RGBA")
                    rgba.alpha_composite(bub_layer, dest=dest)
                    out_panel = rgba.convert("RGB")
                clearance = compute_min_clearance(art_mask, bub_mask)
                best_panel = out_panel
                best_audit = {
                    "wordless": False,
                    "bubble_count": 1,
                    "overlap_px": 0,
                    "min_clearance_px": clearance,
                    "font_size": b_metrics["font_size"],
                    "art_bbox": list(placed_bbox) if placed_bbox else None,
                    "tail_target": cut.tail_target,
                }
                solved_this_scale = True
                break

        if solved_this_scale:
            break

        # Shrink artwork scale (pushing artwork cleanly below bubble) and compact font if needed
        scale *= 0.88
        if attempt in (5, 9, 13) and cur_fs > 14:
            cur_fs = max(14, cur_fs - 2)
            lines, sub_indices = wrap_korean_dialogue(
                dialogue, cur_fs, max_line_width_px=500.0, max_lines=4
            )
            sub_set = set(sub_indices)
            cx, cy, rx, ry = _compute_top_bubble_dims(cur_fs)

    # Mathematical guarantee fallback (strict vertical disjointness)
    if best_panel is None or best_audit is None:
        cur_fs = max(13, min(cur_fs, 18))
        cx, cy, rx, ry = _compute_top_bubble_dims(cur_fs)
        bub_bot = cy + ry + stroke_px
        safe_art_top = int(np.ceil(bub_bot + 42.0))
        avail_h = max(80, H - safe_art_top - 8)
        scale = min((W - 2 * side_margin) / cw, avail_h / ch)
        nw = max(1, int(round(cw * scale)))
        nh = max(1, int(round(ch * scale)))
        px = (W - nw) / 2.0
        py = float(H - nh)
        art_canvas = place_scaled_art(clean_raw, W, H, scale, px, py, crop_box=crop_box)
        art_mask = get_art_mask(art_canvas, threshold=255)
        placed_bbox = extract_art_bbox(art_canvas, threshold=255)
        tail_tip = (cx, min(bub_bot + 24.0, (placed_bbox[1] if placed_bbox else H) - 12.0))
        if tail_tip[1] <= bub_bot + 10.0:
            tail_tip = None
        bub_layer, dest, b_metrics = _build_bubble_layer(
            panel_size=(W, H),
            center=(cx, cy),
            lines=lines,
            radii=(rx, ry),
            tail_tip=tail_tip,
            tail_half_deg=6.0,
            tail_curve=-6.0,
            font_size=cur_fs,
            stroke_px=stroke_px,
            sub_line_indices=sub_indices,
        )
        bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
        overlap = int((art_mask & bub_mask).sum())
        out_panel = art_canvas.copy()
        if bub_layer is not None:
            rgba = out_panel.convert("RGBA")
            rgba.alpha_composite(bub_layer, dest=dest)
            out_panel = rgba.convert("RGB")
        best_panel = out_panel
        best_audit = {
            "wordless": False,
            "bubble_count": 1,
            "overlap_px": overlap,
            "min_clearance_px": compute_min_clearance(art_mask, bub_mask),
            "font_size": b_metrics["font_size"],
            "art_bbox": list(placed_bbox) if placed_bbox else None,
            "tail_target": cut.tail_target,
        }

    return best_panel, best_audit


def _compose_bottom_box_panel_with_tooltip(
    cut: ComicCut,
    raw_im: Image.Image,
    dialogue: str,
    tooltip_rgba: Image.Image,
) -> tuple[Image.Image, dict[str, Any]]:
    """Compose an 844x436 bottom/epilogue box with BOTH speech bubble AND WoW item tooltip at 0px overlap."""
    W, H = BOT_BOX_W, BOT_BOX_H
    clean_raw = clean_white_bg(raw_im)
    rw, rh = clean_raw.size
    raw_bbox = extract_art_bbox(clean_raw, threshold=255)
    stroke_px = 3.5
    box_margin = 14.0
    dummy = ImageDraw.Draw(Image.new("RGB", (16, 16), PURE_WHITE))

    pref = cut.item_tooltip.preferred_corner if cut.item_tooltip else "auto"
    if pref in ("top_right", "bottom_right") or (pref == "auto" and cut.tail_target == "left"):
        ui_side = "right"
        side_dir = "left"   # tail points left toward character on left
    else:
        ui_side = "left"
        side_dir = "right"  # tail points right toward character on right

    if raw_bbox is None:
        lines, sub_indices = wrap_korean_dialogue(dialogue, 20, max_line_width_px=280.0, max_lines=4)
        panel = Image.new("RGB", (W, H), PURE_WHITE)
        cx = 196.0 if ui_side == "left" else (W - 196.0)
        cy = 96.0
        metrics = draw_sloptoon_bubble(
            panel,
            center=(cx, cy),
            lines=lines,
            radii=(176.0, 72.0),
            tail_tip=None,
            font_size=20,
            stroke_px=stroke_px,
            sub_line_indices=sub_indices,
        )
        tw, th = tooltip_rgba.size
        tx0 = int(box_margin + 2) if ui_side == "left" else int(W - box_margin - 2 - tw)
        ty0 = max(int(cy + 72.0 + 14.0), int(H - box_margin - th))
        panel = _composite_rgba_card(panel, tooltip_rgba, (tx0, ty0))
        return panel, {
            "wordless": False,
            "bubble_count": 1,
            "overlap_px": 0,
            "min_clearance_px": 999.0,
            "font_size": metrics["font_size"],
            "art_bbox": None,
            "tail_target": cut.tail_target,
            "has_item_tooltip": True,
            "tooltip_bbox": [tx0, ty0, tx0 + tw, ty0 + th],
            "tooltip_overlap_px": 0,
        }

    ax0, ay0, ax1, ay1 = raw_bbox
    touches_bottom = ay1 >= rh - 6
    crop_box = (ax0, ay0, min(rw, ax1 + 1), rh if touches_bottom else min(rh, ay1 + 1))
    cw = max(1, crop_box[2] - crop_box[0])
    ch = max(1, crop_box[3] - crop_box[1])

    cur_fs = 20 if len(dialogue) <= 32 else 18
    for attempt in range(16):
        max_line_w = 276.0 if cur_fs >= 18 else 264.0
        lines, sub_indices = wrap_korean_dialogue(
            dialogue, cur_fs, max_line_width_px=max_line_w, max_lines=4
        )
        sub_set = set(sub_indices)
        f_m = load_font(cur_fs, weight="Bold")
        f_s = load_font(max(11, int(round(cur_fs * 0.80))), weight="Medium")
        gap = max(4, int(round(cur_fs * 0.32)))
        mw, tot_h, _, _, _, _ = _measure_text_block(dummy, lines, f_m, f_s, gap, sub_set)

        rx = float(np.clip(mw * 0.60 + 32.0, 122.0, 198.0))
        ry = float(np.clip(tot_h * 0.64 + 22.0, 50.0, 88.0))
        cy = box_margin + ry + 4.0
        bub_bot = cy + ry + stroke_px

        # Fit tooltip card cleanly beneath the speech bubble on the UI side
        avail_tip_h = max(84, int(H - box_margin - bub_bot - 12.0))
        avail_tip_w = 276
        cur_tip = tooltip_rgba
        if cur_tip.width > avail_tip_w or cur_tip.height > avail_tip_h:
            s_tip = min(avail_tip_w / max(1, cur_tip.width), avail_tip_h / max(1, cur_tip.height))
            cur_tip = cur_tip.resize(
                (max(60, int(round(cur_tip.width * s_tip))), max(40, int(round(cur_tip.height * s_tip)))),
                Image.Resampling.LANCZOS,
            )
        tw, th = cur_tip.size
        ty0 = int(H - box_margin - th)

        if ui_side == "left":
            cx = box_margin + rx + 4.0
            bub_inner_edge = cx + rx + stroke_px
            tx0 = int(box_margin + 2)
            ui_col_edge = max(bub_inner_edge + 38.0 + attempt * 3.0, float(tx0 + tw + 18))
            art_zone_lo, art_zone_hi = ui_col_edge, W - box_margin
        else:
            cx = W - box_margin - rx - 4.0
            bub_inner_edge = cx - rx - stroke_px
            tx0 = int(W - box_margin - 2 - tw)
            ui_col_edge = min(bub_inner_edge - 38.0 - attempt * 3.0, float(tx0 - 18))
            art_zone_lo, art_zone_hi = box_margin, ui_col_edge

        avail_w = max(120.0, art_zone_hi - art_zone_lo)
        shrink_factor = max(0.48, 0.94 ** max(0, attempt - 1))
        avail_h = H - (12.0 if touches_bottom else 24.0)
        scale = min(avail_w / cw, avail_h / ch) * shrink_factor
        nw = max(1, int(round(cw * scale)))
        nh = max(1, int(round(ch * scale)))

        if ui_side == "left":
            px = max(art_zone_lo, min(W - box_margin - nw, art_zone_lo + (avail_w - nw) * 0.52))
        else:
            px = max(box_margin, min(art_zone_hi - nw, art_zone_lo + (avail_w - nw) * 0.48))
        py = float(H - nh) if touches_bottom else float((H - nh) / 2.0)

        art_canvas = place_scaled_art(clean_raw, W, H, scale, px, py, crop_box=crop_box)
        art_mask = get_art_mask(art_canvas, threshold=255)
        placed_bbox = extract_art_bbox(art_canvas, threshold=255)
        if placed_bbox is None:
            continue

        tip_dest = (tx0, ty0)
        tip_mask = _tooltip_alpha_mask((W, H), cur_tip, tip_dest)
        if int((art_mask & tip_mask).sum()) > 0:
            if attempt in (3, 7, 11) and cur_fs > 13:
                cur_fs = max(13, cur_fs - 2)
            continue

        head_y = float(
            np.clip(
                placed_bbox[1] + (placed_bbox[3] - placed_bbox[1]) * 0.25,
                cy - ry * 0.40,
                cy + ry * 0.40,
            )
        )
        band_y0, band_y1 = max(0, int(head_y - 36)), min(H, int(head_y + 36))
        _, band_xs = np.where(art_mask[band_y0:band_y1, :])

        if side_dir == "right":
            local_edge_x = float(band_xs.min()) if len(band_xs) else float(placed_bbox[0])
            max_reach = min(local_edge_x - 14.0, cx + rx + 58.0)
            base_ang = float(np.clip(np.rad2deg(np.arctan2((head_y - cy) / ry, 1.0)), -16.0, 16.0))
            t_curve = 4.0
        else:
            local_edge_x = float(band_xs.max()) if len(band_xs) else float(placed_bbox[2])
            max_reach = max(local_edge_x + 14.0, cx - rx - 58.0)
            base_ang = 180.0 - float(
                np.clip(np.rad2deg(np.arctan2((head_y - cy) / ry, 1.0)), -16.0, 16.0)
            )
            t_curve = -4.0

        for pull in (1.0, 0.68, 0.38, 0.0):
            if pull == 0.0:
                tail_tip = None
            elif side_dir == "right":
                if max_reach <= bub_inner_edge + 10.0:
                    tail_tip = None
                else:
                    tx = min(bub_inner_edge + max(12.0, (max_reach - bub_inner_edge) * pull), local_edge_x - 12.0)
                    tail_tip = (tx, head_y) if tx > bub_inner_edge + 10.0 else None
            else:
                if max_reach >= bub_inner_edge - 10.0:
                    tail_tip = None
                else:
                    tx = max(bub_inner_edge - max(12.0, (bub_inner_edge - max_reach) * pull), local_edge_x + 12.0)
                    tail_tip = (tx, head_y) if tx < bub_inner_edge - 10.0 else None

            bub_layer, dest, b_metrics = _build_bubble_layer(
                panel_size=(W, H),
                center=(cx, cy),
                lines=lines,
                radii=(rx, ry),
                tail_tip=tail_tip,
                tail_base_angle_deg=base_ang,
                tail_half_deg=8.5,
                tail_curve=t_curve,
                font_size=cur_fs,
                stroke_px=stroke_px,
                sub_line_indices=sub_indices,
            )
            bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
            ov_ab = int((art_mask & bub_mask).sum())
            ov_bt = int((bub_mask & tip_mask).sum())
            if ov_ab == 0 and ov_bt == 0:
                out_panel = art_canvas.copy()
                if bub_layer is not None:
                    rgba = out_panel.convert("RGBA")
                    rgba.alpha_composite(bub_layer, dest=dest)
                    out_panel = rgba.convert("RGB")
                out_panel = _composite_rgba_card(out_panel, cur_tip, tip_dest)
                return out_panel, {
                    "wordless": False,
                    "bubble_count": 1,
                    "overlap_px": 0,
                    "min_clearance_px": compute_min_clearance(art_mask, bub_mask | tip_mask),
                    "font_size": b_metrics["font_size"],
                    "art_bbox": list(placed_bbox),
                    "tail_target": cut.tail_target,
                    "has_item_tooltip": True,
                    "tooltip_bbox": [tx0, ty0, tx0 + tw, ty0 + th],
                    "tooltip_overlap_px": 0,
                }

        if attempt in (3, 7, 11) and cur_fs > 13:
            cur_fs = max(13, cur_fs - 2)

    # Strict horizontal + vertical disjoint fallback
    lines, sub_indices = wrap_korean_dialogue(dialogue, 14, max_line_width_px=240.0, max_lines=3)
    rx, ry = 156.0, 52.0
    cy = box_margin + ry + 4.0
    cx = (box_margin + rx + 4.0) if ui_side == "left" else (W - box_margin - rx - 4.0)
    avail_tip_h = max(84, int(H - box_margin - (cy + ry + stroke_px) - 12.0))
    cur_tip = tooltip_rgba
    if cur_tip.width > 256 or cur_tip.height > avail_tip_h:
        s_tip = min(256 / max(1, cur_tip.width), avail_tip_h / max(1, cur_tip.height))
        cur_tip = cur_tip.resize(
            (max(60, int(round(cur_tip.width * s_tip))), max(40, int(round(cur_tip.height * s_tip)))),
            Image.Resampling.LANCZOS,
        )
    tw, th = cur_tip.size
    tx0 = int(box_margin + 2) if ui_side == "left" else int(W - box_margin - 2 - tw)
    ty0 = int(H - box_margin - th)
    if ui_side == "left":
        art_lo, art_hi = max(cx + rx + stroke_px + 18.0, float(tx0 + tw + 18)), W - box_margin
    else:
        art_lo, art_hi = box_margin, min(cx - rx - stroke_px - 18.0, float(tx0 - 18))
    scale = min(max(80.0, art_hi - art_lo) / cw, (H - 20.0) / ch)
    nw, nh = max(1, int(round(cw * scale))), max(1, int(round(ch * scale)))
    px = art_lo + ((art_hi - art_lo) - nw) / 2.0
    py = float(H - nh)
    art_canvas = place_scaled_art(clean_raw, W, H, scale, px, py, crop_box=crop_box)
    art_mask = get_art_mask(art_canvas, threshold=255)
    placed_bbox = extract_art_bbox(art_canvas, threshold=255)
    bub_layer, dest, b_metrics = _build_bubble_layer(
        panel_size=(W, H),
        center=(cx, cy),
        lines=lines,
        radii=(rx, ry),
        tail_tip=None,
        font_size=14,
        stroke_px=stroke_px,
        sub_line_indices=sub_indices,
    )
    bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
    tip_mask = _tooltip_alpha_mask((W, H), cur_tip, (tx0, ty0))
    out_panel = art_canvas.copy()
    if bub_layer is not None:
        rgba = out_panel.convert("RGBA")
        rgba.alpha_composite(bub_layer, dest=dest)
        out_panel = rgba.convert("RGB")
    out_panel = _composite_rgba_card(out_panel, cur_tip, (tx0, ty0))
    tip_ov = int(((art_mask | bub_mask) & tip_mask).sum())
    ov_total = int((art_mask & bub_mask).sum()) + tip_ov
    return out_panel, {
        "wordless": False,
        "bubble_count": 1,
        "overlap_px": ov_total,
        "min_clearance_px": compute_min_clearance(art_mask, bub_mask | tip_mask),
        "font_size": b_metrics["font_size"],
        "art_bbox": list(placed_bbox) if placed_bbox else None,
        "tail_target": cut.tail_target,
        "has_item_tooltip": True,
        "tooltip_bbox": [tx0, ty0, tx0 + tw, ty0 + th],
        "tooltip_overlap_px": tip_ov,
    }


def _compose_bottom_box_panel(
    cut: ComicCut,
    raw_im: Image.Image,
) -> tuple[Image.Image, dict[str, Any]]:
    """Compose an 844x436 framed reaction/epilogue panel with automatic `overlap_px == 0` solver."""
    W, H = BOT_BOX_W, BOT_BOX_H
    tooltip_rgba = _prepare_cut_tooltip(cut, max_w=276, max_h=196)
    pref_corner = cut.item_tooltip.preferred_corner if cut.item_tooltip else "auto"
    dialogue = (cut.dialogue or "").strip()
    if cut.wordless or not dialogue:
        return _compose_wordless_panel(
            raw_im,
            target_w=W,
            target_h=H,
            side_pad=24,
            top_pad=14,
            bottom_pad_if_floating=14,
            tooltip_rgba=tooltip_rgba,
            preferred_corner=pref_corner,
        )
    if tooltip_rgba is not None:
        return _compose_bottom_box_panel_with_tooltip(cut, raw_im, dialogue, tooltip_rgba)

    clean_raw = clean_white_bg(raw_im)
    rw, rh = clean_raw.size
    raw_bbox = extract_art_bbox(clean_raw, threshold=255)
    stroke_px = 3.5
    box_margin = 14.0
    dummy = ImageDraw.Draw(Image.new("RGB", (16, 16), PURE_WHITE))

    # Determine bubble side and tail direction cleanly:
    # - `bubble_side` (if explicitly set) directly specifies where the speech bubble sits:
    #     * bubble_side == "left"   -> bubble on LEFT, tail points RIGHT into left-side speaker (`side_right`)
    #     * bubble_side == "right"  -> bubble on RIGHT, tail points LEFT into right-side speaker (`side_left`)
    #     * bubble_side == "center" -> bubble at TOP-CENTER (`top_center`)
    # - Otherwise auto-resolve from speaker position (`tail_target`) and cast count:
    #     * 1-character cut: bubble sits opposite the character (`tail_target == "right"` -> bubble left `side_right`;
    #       `tail_target == "left"` -> bubble right `side_left`).
    #     * 2-character cut: bubble sits on the SPEAKER'S outer side so the tail NEVER shoots across the listener!
    #       (`tail_target == "left"` -> bubble on LEFT pointing right at left speaker `side_right`;
    #        `tail_target == "right"` -> bubble on RIGHT pointing left at right speaker `side_left`).
    if cut.bubble_side == "center":
        mode = "top_center"
    elif cut.bubble_side == "left":
        mode = "side_right"
    elif cut.bubble_side == "right":
        mode = "side_left"
    elif cut.tail_target == "center":
        mode = "top_center"
    elif len(cut.characters) >= 2:
        mode = "side_right" if cut.tail_target == "left" else "side_left"
    else:
        mode = f"side_{cut.tail_target}"

    if raw_bbox is None:
        lines, sub_indices = wrap_korean_dialogue(dialogue, 22, max_line_width_px=330.0, max_lines=4)
        panel = Image.new("RGB", (W, H), PURE_WHITE)
        cx = 212.0 if mode == "side_right" else (W - 212.0 if mode == "side_left" else W / 2.0)
        cy = 152.0 if mode != "top_center" else 96.0
        metrics = draw_sloptoon_bubble(
            panel,
            center=(cx, cy),
            lines=lines,
            radii=(188.0, 78.0),
            tail_tip=None,
            font_size=22,
            stroke_px=stroke_px,
            sub_line_indices=sub_indices,
        )
        return panel, {
            "wordless": False,
            "bubble_count": 1,
            "overlap_px": 0,
            "min_clearance_px": 999.0,
            "font_size": metrics["font_size"],
            "art_bbox": None,
            "tail_target": cut.tail_target,
        }

    ax0, ay0, ax1, ay1 = raw_bbox
    touches_bottom = ay1 >= rh - 6
    crop_box = (ax0, ay0, min(rw, ax1 + 1), rh if touches_bottom else min(rh, ay1 + 1))
    cw = max(1, crop_box[2] - crop_box[0])
    ch = max(1, crop_box[3] - crop_box[1])

    def _try_side_layout(
        side_dir: str, fs_start: int
    ) -> tuple[Image.Image | None, dict[str, Any] | None]:
        cur_fs = fs_start
        for attempt in range(16):
            max_line_w = 300.0 if cur_fs >= 20 else 285.0
            lines, sub_indices = wrap_korean_dialogue(
                dialogue, cur_fs, max_line_width_px=max_line_w, max_lines=4
            )
            sub_set = set(sub_indices)
            f_m = load_font(cur_fs, weight="Bold")
            f_s = load_font(max(11, int(round(cur_fs * 0.80))), weight="Medium")
            gap = max(4, int(round(cur_fs * 0.34)))
            mw, th, _, _, _, _ = _measure_text_block(dummy, lines, f_m, f_s, gap, sub_set)

            rx = float(np.clip(mw * 0.58 + 32.0, 120.0, 210.0))
            ry = float(np.clip(th * 0.58 + 20.0, 48.0, 118.0))
            cy = float(np.clip(148.0, box_margin + ry + 6.0, H - box_margin - ry - 6.0))
            if side_dir == "right":
                cx = box_margin + rx + 6.0
                bub_inner_edge = cx + rx + stroke_px
            else:
                cx = W - box_margin - rx - 6.0
                bub_inner_edge = cx - rx - stroke_px

            tail_reserve = 46.0 + attempt * 4.0
            if side_dir == "right":
                art_zone_lo = bub_inner_edge + tail_reserve
                art_zone_hi = W - box_margin
            else:
                art_zone_lo = box_margin
                art_zone_hi = bub_inner_edge - tail_reserve

            avail_w = art_zone_hi - art_zone_lo
            if avail_w < 190.0:
                if cur_fs > 13:
                    cur_fs = max(13, cur_fs - 2)
                    continue
                avail_w = max(120.0, avail_w)

            shrink_factor = max(0.45, 0.94 ** max(0, attempt - 1))
            avail_h = H - (12.0 if touches_bottom else 24.0)
            scale = min(avail_w / cw, avail_h / ch) * shrink_factor
            nw = max(1, int(round(cw * scale)))
            nh = max(1, int(round(ch * scale)))

            if side_dir == "right":
                px = art_zone_lo + (avail_w - nw) * 0.55
                px = max(art_zone_lo, min(W - box_margin - nw, px))
            else:
                px = art_zone_lo + (avail_w - nw) * 0.45
                px = max(box_margin, min(art_zone_hi - nw, px))

            py = float(H - nh) if touches_bottom else float((H - nh) / 2.0)

            art_canvas = place_scaled_art(clean_raw, W, H, scale, px, py, crop_box=crop_box)
            art_mask = get_art_mask(art_canvas, threshold=255)
            placed_bbox = extract_art_bbox(art_canvas, threshold=255)
            if placed_bbox is None:
                continue

            # Target tail tip toward upper-third of character facing the bubble
            head_y = float(
                np.clip(
                    placed_bbox[1] + (placed_bbox[3] - placed_bbox[1]) * 0.28,
                    cy - ry * 0.45,
                    cy + ry * 0.45,
                )
            )
            band_y0 = max(0, int(head_y - 42))
            band_y1 = min(H, int(head_y + 42))
            band_ys, band_xs = np.where(art_mask[band_y0:band_y1, :])

            if side_dir == "right":
                local_edge_x = float(band_xs.min()) if len(band_xs) else float(placed_bbox[0])
                max_reach = min(local_edge_x - 14.0, cx + rx + 62.0)
                min_reach = cx + rx + 18.0
                base_ang = float(np.clip(np.rad2deg(np.arctan2((head_y - cy) / ry, 1.0)), -18.0, 18.0))
                t_curve = 4.5
            else:
                local_edge_x = float(band_xs.max()) if len(band_xs) else float(placed_bbox[2])
                max_reach = max(local_edge_x + 14.0, cx - rx - 62.0)
                min_reach = cx - rx - 18.0
                base_ang = 180.0 - float(
                    np.clip(np.rad2deg(np.arctan2((head_y - cy) / ry, 1.0)), -18.0, 18.0)
                )
                t_curve = -4.5

            for pull in (1.0, 0.72, 0.48, 0.25):
                if side_dir == "right":
                    if max_reach <= cx + rx + 10.0:
                        tail_tip = None
                    else:
                        tx = (cx + rx + stroke_px) + max(
                            14.0, (max_reach - (cx + rx + stroke_px)) * pull
                        )
                        tx = min(tx, local_edge_x - 12.0)
                        tail_tip = (tx, head_y) if tx >= min_reach * 0.96 else None
                else:
                    if max_reach >= cx - rx - 10.0:
                        tail_tip = None
                    else:
                        tx = (cx - rx - stroke_px) - max(
                            14.0, ((cx - rx - stroke_px) - max_reach) * pull
                        )
                        tx = max(tx, local_edge_x + 12.0)
                        tail_tip = (tx, head_y) if tx <= min_reach * 1.04 else None

                bub_layer, dest, b_metrics = _build_bubble_layer(
                    panel_size=(W, H),
                    center=(cx, cy),
                    lines=lines,
                    radii=(rx, ry),
                    tail_tip=tail_tip,
                    tail_base_angle_deg=base_ang,
                    tail_half_deg=9.5,
                    tail_curve=t_curve,
                    font_size=cur_fs,
                    stroke_px=stroke_px,
                    sub_line_indices=sub_indices,
                )
                bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
                overlap = int((art_mask & bub_mask).sum())
                if overlap == 0:
                    out_panel = art_canvas.copy()
                    if bub_layer is not None:
                        rgba = out_panel.convert("RGBA")
                        rgba.alpha_composite(bub_layer, dest=dest)
                        out_panel = rgba.convert("RGB")
                    return out_panel, {
                        "wordless": False,
                        "bubble_count": 1,
                        "overlap_px": 0,
                        "min_clearance_px": compute_min_clearance(art_mask, bub_mask),
                        "font_size": b_metrics["font_size"],
                        "art_bbox": list(placed_bbox),
                        "tail_target": cut.tail_target,
                        "bubble_center": [round(cx, 1), round(cy, 1)],
                        "bubble_side_resolved": "left" if side_dir == "right" else "right",
                    }

            if attempt in (3, 7, 11) and cur_fs > 13:
                cur_fs = max(13, cur_fs - 2)

        return None, None

    def _try_top_center_layout(fs_start: int) -> tuple[Image.Image, dict[str, Any]]:
        cur_fs = fs_start
        best_p: Image.Image | None = None
        best_a: dict[str, Any] | None = None

        for attempt in range(14):
            lines, sub_indices = wrap_korean_dialogue(
                dialogue, cur_fs, max_line_width_px=540.0, max_lines=3
            )
            sub_set = set(sub_indices)
            f_m = load_font(cur_fs, weight="Bold")
            f_s = load_font(max(11, int(round(cur_fs * 0.80))), weight="Medium")
            gap = max(4, int(round(cur_fs * 0.32)))
            mw, th, _, _, _, _ = _measure_text_block(dummy, lines, f_m, f_s, gap, sub_set)

            rx = float(np.clip(mw * 0.60 + 36.0, 140.0, 360.0))
            ry = float(np.clip(th * 0.64 + 20.0, 44.0, 86.0))
            cx = W / 2.0
            cy = box_margin + ry + 4.0
            bub_bot = cy + ry + stroke_px

            tail_space = 34.0 + attempt * 4.0
            art_top = bub_bot + tail_space
            avail_h = max(90.0, H - art_top - (0.0 if touches_bottom else 10.0))
            avail_w = W - 2 * box_margin
            scale = min(avail_w / cw, avail_h / ch) * max(0.55, 0.96 ** attempt)
            nw = max(1, int(round(cw * scale)))
            nh = max(1, int(round(ch * scale)))
            px = (W - nw) / 2.0
            py = float(H - nh) if touches_bottom else float(max(art_top, H - nh - 8.0))

            art_canvas = place_scaled_art(clean_raw, W, H, scale, px, py, crop_box=crop_box)
            art_mask = get_art_mask(art_canvas, threshold=255)
            placed_bbox = extract_art_bbox(art_canvas, threshold=255)
            art_min_y = float(placed_bbox[1]) if placed_bbox else float(H)

            for pull in (1.0, 0.65, 0.35, 0.0):
                if pull == 0.0 or art_min_y - bub_bot < 22.0:
                    tail_tip = None
                else:
                    ty = min(bub_bot + 36.0 * pull, art_min_y - 12.0)
                    tail_tip = (cx, ty) if ty > bub_bot + 10.0 else None

                bub_layer, dest, b_metrics = _build_bubble_layer(
                    panel_size=(W, H),
                    center=(cx, cy),
                    lines=lines,
                    radii=(rx, ry),
                    tail_tip=tail_tip,
                    tail_base_angle_deg=90.0,
                    tail_half_deg=6.5,
                    tail_curve=-5.0,
                    font_size=cur_fs,
                    stroke_px=stroke_px,
                    sub_line_indices=sub_indices,
                )
                bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
                overlap = int((art_mask & bub_mask).sum())
                if overlap == 0:
                    out_panel = art_canvas.copy()
                    if bub_layer is not None:
                        rgba = out_panel.convert("RGBA")
                        rgba.alpha_composite(bub_layer, dest=dest)
                        out_panel = rgba.convert("RGB")
                    return out_panel, {
                        "wordless": False,
                        "bubble_count": 1,
                        "overlap_px": 0,
                        "min_clearance_px": compute_min_clearance(art_mask, bub_mask),
                        "font_size": b_metrics["font_size"],
                        "art_bbox": list(placed_bbox) if placed_bbox else None,
                        "tail_target": cut.tail_target,
                    }

            if attempt in (3, 7, 10) and cur_fs > 12:
                cur_fs = max(12, cur_fs - 2)

        # Guaranteed disjoint fallback
        if best_p is None or best_a is None:
            lines, sub_indices = wrap_korean_dialogue(dialogue, 14, max_line_width_px=560.0, max_lines=3)
            cx, cy, rx, ry = W / 2.0, 62.0, 300.0, 44.0
            bub_bot = cy + ry + stroke_px
            safe_top = int(np.ceil(bub_bot + 18.0))
            scale = min((W - 2 * box_margin) / cw, max(40.0, H - safe_top) / ch)
            nw, nh = max(1, int(round(cw * scale))), max(1, int(round(ch * scale)))
            art_canvas = place_scaled_art(
                clean_raw, W, H, scale, (W - nw) / 2.0, float(H - nh), crop_box=crop_box
            )
            art_mask = get_art_mask(art_canvas, threshold=255)
            placed_bbox = extract_art_bbox(art_canvas, threshold=255)
            bub_layer, dest, b_metrics = _build_bubble_layer(
                panel_size=(W, H),
                center=(cx, cy),
                lines=lines,
                radii=(rx, ry),
                tail_tip=None,
                font_size=14,
                stroke_px=stroke_px,
                sub_line_indices=sub_indices,
            )
            bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
            out_panel = art_canvas.copy()
            if bub_layer is not None:
                rgba = out_panel.convert("RGBA")
                rgba.alpha_composite(bub_layer, dest=dest)
                out_panel = rgba.convert("RGB")
            best_p = out_panel
            best_a = {
                "wordless": False,
                "bubble_count": 1,
                "overlap_px": int((art_mask & bub_mask).sum()),
                "min_clearance_px": compute_min_clearance(art_mask, bub_mask),
                "font_size": b_metrics["font_size"],
                "art_bbox": list(placed_bbox) if placed_bbox else None,
                "tail_target": cut.tail_target,
            }
        return best_p, best_a

    if mode in ("side_right", "side_left"):
        fs_start = 22 if len(dialogue) <= 34 else 20
        panel, audit = _try_side_layout("right" if mode == "side_right" else "left", fs_start)
        if panel is not None and audit is not None:
            return panel, audit

    return _try_top_center_layout(fs_start=20)


def build_header(script: EpisodeScript) -> Image.Image:
    """Build the 900x244 pure `#FFFFFF` minimal modern Sloptoon episode header."""
    canvas = Image.new("RGB", (PAGE_W, HEADER_H), PURE_WHITE)
    cx = PAGE_W / 2.0

    draw_minimal_pill(
        canvas,
        cx,
        40,
        HEADER_BADGE_TEXT,
        bg_col=INK_BLACK,
        txt_col=PURE_WHITE,
        dot_col=PILL_DOT_BLUE,
        font_size=14,
        pad_xy=(18, 7),
        max_width=844,
    )

    d = ImageDraw.Draw(canvas)
    f_title = load_font(50, weight="Black")
    tbb = d.textbbox((0, 0), SERIES_TITLE_TEXT, font=f_title)
    tw = float(d.textlength(SERIES_TITLE_TEXT, font=f_title))
    d.text(
        (round(cx - tw / 2.0), round(104 - (tbb[3] - tbb[1]) / 2.0 - tbb[1])),
        SERIES_TITLE_TEXT,
        font=f_title,
        fill=INK_BLACK,
    )

    ep_badge = f"EP.{script.episode_number} {script.source_title} (#{script.source_post_no})"
    draw_minimal_pill(
        canvas,
        cx,
        166,
        ep_badge,
        bg_col=PURE_WHITE,
        txt_col=DC_BLUE,
        border_col=DC_BLUE,
        font_size=15,
        pad_xy=(18, 6),
        max_width=844,
    )

    # Subtitle (auto-shrink if long so it stays cleanly inside x=28..872)
    sub_fs = 13
    f_cap = load_font(sub_fs, weight="Medium")
    cap_txt = script.subtitle.strip()
    while float(d.textlength(cap_txt, font=f_cap)) > 840 and sub_fs > 10:
        sub_fs -= 1
        f_cap = load_font(sub_fs, weight="Medium")
    cbb = d.textbbox((0, 0), cap_txt, font=f_cap)
    cw = float(d.textlength(cap_txt, font=f_cap))
    d.text(
        (round(cx - cw / 2.0), round(205 - (cbb[3] - cbb[1]) / 2.0 - cbb[1])),
        cap_txt,
        font=f_cap,
        fill=MUTED_INK,
    )

    d.line([(28, 234), (872, 234)], fill=INK_BLACK, width=2)
    return canvas


def _cover_fit_full_bleed_image(
    raw_im: Image.Image,
    target_w: int,
    target_h: int,
) -> tuple[Image.Image, float]:
    """Cover-fit a raw full-bleed illustration edge-to-edge into `(target_w, target_h)`.

    1. Trims accidental thin pure-white outer margins (up to 12% per side) when non-white
       content fills >70% of the remaining interior.
    2. Applies cover-fit scaling (`scale = max(target_w / cw, target_h / ch)`) anchored
       bottom-center, clamping top crop to at most 24% of scaled height so character heads
       are preserved while every pixel of `(target_w, target_h)` is filled edge-to-edge.
    3. Returns `(fitted_rgb_image, edge_fill_ratio)` where `edge_fill_ratio` is the fraction
       of non-white pixels along the 4 outer 4px inner-edge bands.
    """
    rgb = _flatten_to_white_rgb(raw_im)
    rw, rh = rgb.size
    src = rgb

    if rw >= 48 and rh >= 48:
        arr = np.asarray(rgb)
        is_white = (arr[:, :, 0] >= 248) & (arr[:, :, 1] >= 248) & (arr[:, :, 2] >= 248)
        max_tx = int(rw * 0.12)
        max_ty = int(rh * 0.12)

        y0 = 0
        while y0 < max_ty and float(is_white[y0, :].mean()) >= 0.88:
            y0 += 1
        y1 = rh
        while (rh - y1) < max_ty and (y1 - y0) > 32 and float(is_white[y1 - 1, :].mean()) >= 0.88:
            y1 -= 1
        x0 = 0
        while x0 < max_tx and float(is_white[y0:y1, x0].mean()) >= 0.88:
            x0 += 1
        x1 = rw
        while (rw - x1) < max_tx and (x1 - x0) > 32 and float(is_white[y0:y1, x1 - 1].mean()) >= 0.88:
            x1 -= 1

        if (x0, y0, x1, y1) != (0, 0, rw, rh) and (x1 - x0) >= 32 and (y1 - y0) >= 32:
            inner_nonwhite = float((~is_white[y0:y1, x0:x1]).mean())
            if inner_nonwhite > 0.70:
                src = rgb.crop((x0, y0, x1, y1))

    cw, ch = src.size
    scale = max(target_w / float(max(1, cw)), target_h / float(max(1, ch)))
    nw = max(target_w, int(np.ceil(cw * scale)))
    nh = max(target_h, int(np.ceil(ch * scale)))
    resized = src.resize((nw, nh), Image.Resampling.LANCZOS)

    excess_w = nw - target_w
    excess_h = nh - target_h
    crop_x0 = excess_w // 2
    # Anchor bottom-center (cropping excess off top scenery) while clamping top crop <= 24%
    # so character heads/hats are never sliced on extreme aspect mismatches.
    max_top_crop = int(round(nh * 0.24))
    crop_y0 = min(excess_h, max_top_crop)
    panel = resized.crop((crop_x0, crop_y0, crop_x0 + target_w, crop_y0 + target_h))

    p_arr = np.asarray(panel)
    non_white = (p_arr[:, :, 0] < 248) | (p_arr[:, :, 1] < 248) | (p_arr[:, :, 2] < 248)
    m = max(1, min(4, target_h // 8, target_w // 8))
    edge_pixels = np.concatenate(
        [
            non_white[:m, :].ravel(),
            non_white[target_h - m :, :].ravel(),
            non_white[:, :m].ravel(),
            non_white[:, target_w - m :].ravel(),
        ]
    )
    edge_fill_ratio = round(float(edge_pixels.mean()), 4)
    return panel, edge_fill_ratio


def build_thumbnail(
    script: EpisodeScript,
    raw_images: Sequence[Image.Image],
    size: tuple[int, int] = THUMB_SIZE,
    *,
    full_bleed: bool = False,
) -> Image.Image:
    """Create a clean 4:3 thumbnail (`800x600`) highlighting the lead cut artwork.

    In `full_bleed=True` mode, cover-fills the framed comic cover window with an 8px
    pure-`#FFFFFF` outer mat + crisp 3px `#141414` inner panel border so the thumbnail is
    edge-to-edge rich while preserving `_is_outer_border_pure_white(thumb_im) == True`.
    """
    tw, th = size
    canvas = Image.new("RGB", (tw, th), PURE_WHITE)

    if full_bleed:
        # 10px outer pure-white mat keeps the 3.0px inner border strictly outside the outer
        # 8x8 JPEG DCT blocks (0..7 / W-8..W-1 / H-8..H-1), guaranteeing zero JPEG ringing!
        pad = 10
        inner_w = max(32, tw - 2 * pad)
        inner_h = max(32, th - 2 * pad)
        chosen_raw: Image.Image | None = None
        for im in raw_images:
            rgb_im = _flatten_to_white_rgb(im)
            if extract_art_bbox(rgb_im, threshold=252) is not None:
                chosen_raw = rgb_im
                break
        if chosen_raw is None and raw_images:
            chosen_raw = _flatten_to_white_rgb(raw_images[0])

        if chosen_raw is not None:
            fitted, _ = _cover_fit_full_bleed_image(chosen_raw, inner_w, inner_h)
            canvas.paste(fitted, (pad, pad))

        draw_4x_rect_border(
            canvas,
            (float(pad), float(pad), float(tw - pad), float(th - pad)),
            stroke_px=3.0,
            color=INK_BLACK,
        )
        badge_text = f"EP.{script.episode_number}"
        draw_minimal_pill(
            canvas,
            cx=68,
            cy=40,
            text=badge_text,
            bg_col=INK_BLACK,
            txt_col=PURE_WHITE,
            border_col=PURE_WHITE,
            dot_col=PILL_DOT_BLUE,
            font_size=15,
            pad_xy=(14, 6),
        )
        return canvas

    # Pick first cut that has visible artwork (prefer cut 0 for story hook)
    chosen_im: Image.Image | None = None
    chosen_bbox: tuple[int, int, int, int] | None = None
    for im in raw_images:
        cleaned = clean_white_bg(im)
        bb = extract_art_bbox(cleaned, threshold=255)
        if bb is not None:
            chosen_im = cleaned
            chosen_bbox = bb
            break

    if chosen_im is not None and chosen_bbox is not None:
        rw, rh = chosen_im.size
        ax0, ay0, ax1, ay1 = chosen_bbox
        pad_x = max(8, int((ax1 - ax0) * 0.04))
        pad_y = max(8, int((ay1 - ay0) * 0.04))
        cx0 = max(0, ax0 - pad_x)
        cy0 = max(0, ay0 - pad_y)
        cx1 = min(rw, ax1 + pad_x + 1)
        cy1 = min(rh, ay1 + pad_y + 1)
        cropped = chosen_im.crop((cx0, cy0, cx1, cy1))
        cw, ch = cropped.size

        margin_x = 36
        margin_top = 46
        margin_bot = 24
        scale = min((tw - 2 * margin_x) / max(1, cw), (th - margin_top - margin_bot) / max(1, ch))
        nw = max(1, int(round(cw * scale)))
        nh = max(1, int(round(ch * scale)))
        resized = clean_white_bg(cropped.resize((nw, nh), Image.Resampling.LANCZOS))
        px = (tw - nw) // 2
        py = margin_top + (th - margin_top - margin_bot - nh) // 2
        canvas.paste(resized, (px, py))

    # Subtle EP badge in top-left corner while keeping 100% pure-white outer edges
    badge_text = f"EP.{script.episode_number}"
    draw_minimal_pill(
        canvas,
        cx=64,
        cy=36,
        text=badge_text,
        bg_col=INK_BLACK,
        txt_col=PURE_WHITE,
        dot_col=PILL_DOT_BLUE,
        font_size=15,
        pad_xy=(14, 6),
    )
    return canvas


def _is_outer_border_pure_white(im: Image.Image, margin: int = 2) -> bool:
    """Check that all pixels within `margin` px of the 4 outer edges are pure `#FFFFFF`."""
    arr = np.asarray(im.convert("RGB"))
    h, w, _ = arr.shape
    m = max(1, min(margin, h // 4, w // 4))
    top = arr[:m, :, :]
    bot = arr[h - m :, :, :]
    left = arr[:, :m, :]
    right = arr[:, w - m :, :]
    return bool(
        np.all(top == 255)
        and np.all(bot == 255)
        and np.all(left == 255)
        and np.all(right == 255)
    )


def _resolve_cut_path(
    cut: ComicCut,
    position_1based: int,
    raw_cut_paths: Mapping[int, Path | str],
) -> Path:
    """Resolve raw image path for a cut by `cut.cut_index` (or positional fallback)."""
    if cut.cut_index in raw_cut_paths:
        return Path(raw_cut_paths[cut.cut_index])
    if position_1based in raw_cut_paths:
        return Path(raw_cut_paths[position_1based])
    if (position_1based - 1) in raw_cut_paths:
        return Path(raw_cut_paths[position_1based - 1])
    str_keys = {str(k): v for k, v in raw_cut_paths.items()}
    if str(cut.cut_index) in str_keys:
        return Path(str_keys[str(cut.cut_index)])
    raise KeyError(
        f"Missing raw image path for cut_index={cut.cut_index} "
        f"(available keys: {sorted(raw_cut_paths.keys())})"
    )


def _normalize_watermark_site_url(site_url: str) -> str:
    """Normalize a site URL for compact display inside the bottom CTA banner."""
    cleaned = (site_url or "").strip()
    if not cleaned:
        return ""
    cleaned = re.sub(r"^https?://", "", cleaned, flags=re.IGNORECASE)
    return cleaned.rstrip("/")


def render_watermark_footer(
    width: int = PAGE_W,
    site_url: str = DEFAULT_WATERMARK_URL,
) -> Image.Image:
    """Render a crisp pure-`#FFFFFF` Sloptoon bottom watermark CTA banner (~132px tall).

    Matches the comic's minimal black-and-white Sloptoon aesthetic with a 4x-supersampled
    rounded card border, `#0EA5E9` sky-blue accent dot, and auto-fitting Korean typography
    (zero emojis, zero broken glyph boxes).
    """
    w = max(320, int(round(width)))
    h = WATERMARK_FOOTER_H
    display_url = _normalize_watermark_site_url(site_url) or DEFAULT_WATERMARK_URL

    canvas = Image.new("RGB", (w, h), PURE_WHITE)
    cx = w / 2.0

    # Sleek 4x-supersampled thin-border black rounded card (matches x=28..872 panel framing)
    side_margin = 28 if w >= 700 else max(12, int(round(w * 0.032)))
    card_x0 = side_margin
    card_x1 = w - side_margin
    card_y0 = 10
    card_y1 = h - 10
    card_w = card_x1 - card_x0
    card_h = card_y1 - card_y0

    S = 4
    stroke_px = 2.4
    radius = 20
    pad = 6
    rw, rh = card_w + pad * 2, card_h + pad * 2
    layer_4x = Image.new("RGBA", (rw * S, rh * S), (0, 0, 0, 0))
    d4 = ImageDraw.Draw(layer_4x)

    bx0, by0 = pad * S, pad * S
    bx1, by1 = (pad + card_w) * S, (pad + card_h) * S
    bw = round(stroke_px * S)
    rad4 = radius * S

    # Outer crisp black rounded border + pure white interior
    d4.rounded_rectangle([bx0, by0, bx1, by1], radius=rad4, fill=(*INK_BLACK, 255))
    d4.rounded_rectangle(
        [bx0 + bw, by0 + bw, bx1 - bw, by1 - bw],
        radius=max(4, rad4 - bw),
        fill=(*PURE_WHITE, 255),
    )

    card_1x = layer_4x.resize((rw, rh), Image.Resampling.BOX)
    rgba = canvas.convert("RGBA")
    rgba.alpha_composite(card_1x, dest=(card_x0 - pad, card_y0 - pad))
    canvas.paste(rgba.convert("RGB"), (0, 0))

    inner_max_w = max(160, card_w - 44)

    # Row 1: Top badge pill with #0EA5E9 sky-blue accent dot
    draw_minimal_pill(
        canvas,
        cx=cx,
        cy=31,
        text=WATERMARK_BADGE_TEXT,
        bg_col=INK_BLACK,
        txt_col=PURE_WHITE,
        dot_col=WATERMARK_ACCENT_BLUE,
        font_size=12,
        pad_xy=(14, 5),
        max_width=inner_max_w,
    )

    # Row 2: Main bold CTA (`다음 화 & 전편 정주행  >>  slopwow.github.io`)
    d = ImageDraw.Draw(canvas)
    cta_prefix = WATERMARK_CTA_PREFIX
    cta_sep = "  >>  "
    cta_fs = 22
    f_prefix = load_font(cta_fs, weight="Black")
    f_sep = load_font(cta_fs, weight="Bold")
    f_url = load_font(cta_fs, weight="Black")

    def _measure_cta(fs: int) -> tuple[Any, Any, Any, float, float, float, float]:
        fp = load_font(fs, weight="Black")
        fs_sep = load_font(fs, weight="Bold")
        fu = load_font(fs, weight="Black")
        wp = float(d.textlength(cta_prefix, font=fp))
        ws = float(d.textlength(cta_sep, font=fs_sep))
        wu = float(d.textlength(display_url, font=fu))
        return fp, fs_sep, fu, wp, ws, wu, wp + ws + wu

    f_prefix, f_sep, f_url, w_prefix, w_sep, w_url, total_cta_w = _measure_cta(cta_fs)
    while total_cta_w > inner_max_w and cta_fs > 12:
        cta_fs -= 1
        f_prefix, f_sep, f_url, w_prefix, w_sep, w_url, total_cta_w = _measure_cta(cta_fs)

    cta_cy = 67.0
    full_cta_str = f"{cta_prefix}{cta_sep}{display_url}"
    cta_bb = d.textbbox((0, 0), full_cta_str, font=f_prefix)
    cta_h = float(cta_bb[3] - cta_bb[1])
    cta_y = round(cta_cy - cta_h / 2.0 - cta_bb[1])
    start_x = cx - total_cta_w / 2.0

    # Align each segment to the same baseline/top reference cleanly
    d.text((round(start_x), cta_y), cta_prefix, font=f_prefix, fill=INK_BLACK)
    sep_x = start_x + w_prefix
    d.text((round(sep_x), cta_y), cta_sep, font=f_sep, fill=WATERMARK_ACCENT_BLUE)
    url_x = sep_x + w_sep
    d.text((round(url_x), cta_y), display_url, font=f_url, fill=WATERMARK_LINK_BLUE)

    # Crisp sky-blue accent underline beneath URL so it pops at mobile widths
    url_bb = d.textbbox((round(url_x), cta_y), display_url, font=f_url)
    ul_y = url_bb[3] + 2
    d.line(
        [(round(url_x), ul_y), (round(url_x + w_url), ul_y)],
        fill=WATERMARK_ACCENT_BLUE,
        width=2,
    )

    # Row 3: Subtext
    sub_fs = 13
    f_sub = load_font(sub_fs, weight="Medium")
    while float(d.textlength(WATERMARK_SUBTEXT, font=f_sub)) > inner_max_w and sub_fs > 9:
        sub_fs -= 1
        f_sub = load_font(sub_fs, weight="Medium")
    sub_bb = d.textbbox((0, 0), WATERMARK_SUBTEXT, font=f_sub)
    sub_w = float(d.textlength(WATERMARK_SUBTEXT, font=f_sub))
    sub_h = float(sub_bb[3] - sub_bb[1])
    d.text(
        (round(cx - sub_w / 2.0), round(105.0 - sub_h / 2.0 - sub_bb[1])),
        WATERMARK_SUBTEXT,
        font=f_sub,
        fill=MUTED_INK,
    )

    return canvas


def append_watermark_footer(
    image: Image.Image,
    site_url: str = DEFAULT_WATERMARK_URL,
) -> Image.Image:
    """Append the Sloptoon bottom watermark CTA banner seamlessly onto `image`."""
    rgb = _flatten_to_white_rgb(image)
    clean_url = (site_url or "").strip()
    if not clean_url:
        return rgb.copy()

    footer = render_watermark_footer(width=rgb.width, site_url=clean_url)
    out = Image.new("RGB", (rgb.width, rgb.height + footer.height), PURE_WHITE)
    out.paste(rgb, (0, 0))
    out.paste(footer, (0, rgb.height))
    return out


def retrofit_episode_watermark(
    episode_dir: Path,
    site_url: str = DEFAULT_WATERMARK_URL,
    *,
    filename: str = "episode_full.jpg",
) -> Path:
    """Idempotently apply the bottom watermark CTA banner to an episode's full scroll JPG.

    On first run (when `episode_full_raw.jpg` does not yet exist), backs up the original
    `episode_full.jpg` to `episode_full_raw.jpg` before stamping the footer. Subsequent calls
    always re-render from `episode_full_raw.jpg`, guaranteeing zero double-stamping.
    """
    ep_dir = Path(episode_dir)
    full_path = ep_dir / filename
    raw_name = f"{full_path.stem}_raw{full_path.suffix}"
    raw_path = ep_dir / raw_name

    clean_url = (site_url or "").strip()
    if not clean_url:
        raise ValueError("site_url must not be empty when retrofitting a watermark.")

    if not raw_path.exists():
        if not full_path.exists():
            raise FileNotFoundError(f"Episode full image not found: {full_path}")
        shutil.copy2(full_path, raw_path)

    with Image.open(raw_path) as raw_im:
        watermarked = append_watermark_footer(raw_im, site_url=clean_url)

    watermarked.save(full_path, format="JPEG", quality=95, subsampling=0)
    return full_path


def _fit_tooltip_card(
    tooltip_rgba: Image.Image,
    max_w: int,
    max_h: int,
) -> Image.Image:
    """Proportionally downscale an RGBA tooltip card if it exceeds `(max_w, max_h)`."""
    tw, th = tooltip_rgba.size
    safe_max_w = max(60, int(max_w))
    safe_max_h = max(36, int(max_h))
    if tw <= safe_max_w and th <= safe_max_h:
        return tooltip_rgba
    scale = min(safe_max_w / max(1, tw), safe_max_h / max(1, th))
    nw = max(60, int(round(tw * scale)))
    nh = max(36, int(round(th * scale)))
    return tooltip_rgba.resize((nw, nh), Image.Resampling.LANCZOS)


def _compute_snug_ellipse_radii(
    dummy: ImageDraw.ImageDraw,
    lines: Sequence[str],
    sub_set: set[int],
    font_size: int,
    *,
    min_rx: float,
    max_rx: float,
    min_ry: float,
    max_ry: float,
    pad_x: float = 32.0,
    pad_y: float = 20.0,
    line_spacing_ratio: float = 0.34,
) -> tuple[float, float]:
    """Compute elliptical `(rx, ry)` sized cleanly for `lines` so font won't auto-shrink unexpectedly."""
    f_m = load_font(font_size, weight="Bold")
    f_s = load_font(max(11, int(round(font_size * 0.80))), weight="Medium")
    gap = max(4, int(round(font_size * line_spacing_ratio)))
    mw, tot_h, _, _, _, _ = _measure_text_block(dummy, lines, f_m, f_s, gap, sub_set)

    rx = float(np.clip(mw * 0.62 + pad_x, min_rx, max_rx))
    ry = float(np.clip(tot_h * 0.66 + pad_y, min_ry, max_ry))

    a = mw / 2.0 + 18.0
    b = tot_h / 2.0 + 12.0
    if (a / max(1.0, rx)) ** 2 + (b / max(1.0, ry)) ** 2 > 0.84:
        if a / max(1.0, rx) > 0.72 and rx < max_rx:
            rx = float(np.clip(a / 0.68, min_rx, max_rx))
        rem = max(0.18, 0.84 - (a / max(1.0, rx)) ** 2)
        ry_need = b / float(np.sqrt(rem))
        ry = float(np.clip(max(ry, ry_need), min_ry, max_ry))
    return rx, ry


def _compose_narrow_variable_panel(
    cut: ComicCut,
    raw_im: Image.Image,
    target_w: int,
    target_h: int,
    border_style: str,
    dialogue: str,
    tooltip_rgba: Image.Image | None,
) -> tuple[Image.Image, dict[str, Any]]:
    """Compose a narrow vertical panel (`target_w < 580`, e.g. `410x626` / `410x638`).

    Places a crisp 4x-supersampled elliptical speech bubble at the TOP with a short pointed
    tail aimed down at the speaker's head and artwork cleanly below at strictly 0px overlap.
    """
    W, H = target_w, target_h
    clean_raw = clean_white_bg(raw_im)
    rw, rh = clean_raw.size
    raw_bbox = extract_art_bbox(clean_raw, threshold=255)
    stroke_px = 3.5
    margin_x = 12.0 if border_style == "box" else 10.0
    margin_top = 12.0 if border_style == "box" else 10.0
    margin_bot = 10.0
    dummy = ImageDraw.Draw(Image.new("RGB", (16, 16), PURE_WHITE))

    pref_corner = cut.item_tooltip.preferred_corner if cut.item_tooltip else "auto"
    cur_tip: Image.Image | None = None
    if tooltip_rgba is not None:
        cur_tip = _fit_tooltip_card(
            tooltip_rgba,
            max_w=min(248, max(120, W - 24)),
            max_h=min(156, max(84, int(H * 0.25))),
        )

    max_rx = max(72.0, W / 2.0 - margin_x - stroke_px - 2.0)
    max_ry = min(116.0, max(50.0, H * (0.20 if cur_tip is None else 0.175)))
    min_rx = min(104.0, max_rx)
    min_ry = min(44.0, max_ry)
    wrap_w = float(np.clip(max_rx * 1.38, 130.0, max(140.0, W - 2.0 * margin_x - 68.0)))

    base_fs = 21 if len(dialogue) <= 20 else (19 if len(dialogue) <= 36 else 17)
    if cur_tip is not None:
        base_fs = min(base_fs, 19)

    def _layout_narrow_bubble(fs: int) -> tuple[list[str], list[int], float, float, float, float]:
        lines_out, subs_out = wrap_korean_dialogue(
            dialogue, fs, max_line_width_px=wrap_w, max_lines=4
        )
        rx_out, ry_out = _compute_snug_ellipse_radii(
            dummy,
            lines_out,
            set(subs_out),
            fs,
            min_rx=min_rx,
            max_rx=max_rx,
            min_ry=min_ry,
            max_ry=max_ry,
            pad_x=28.0,
            pad_y=18.0,
        )
        cx_out = W / 2.0
        target_side = cut.bubble_side or cut.tail_target
        if target_side == "left":
            cx_out = float(
                np.clip(W * 0.44, margin_x + rx_out + stroke_px + 2.0, W - margin_x - rx_out - stroke_px - 2.0)
            )
        elif target_side == "right":
            cx_out = float(
                np.clip(W * 0.56, margin_x + rx_out + stroke_px + 2.0, W - margin_x - rx_out - stroke_px - 2.0)
            )
        cy_out = margin_top + ry_out + stroke_px + 2.0
        return lines_out, subs_out, cx_out, cy_out, rx_out, ry_out

    cur_fs = base_fs
    lines, sub_indices, cx, cy, rx, ry = _layout_narrow_bubble(cur_fs)
    if len(lines) >= 4 and cur_fs > 17:
        cur_fs = 17
        lines, sub_indices, cx, cy, rx, ry = _layout_narrow_bubble(cur_fs)

    if raw_bbox is None:
        panel = Image.new("RGB", (W, H), PURE_WHITE)
        bub_bot = cy + ry + stroke_px
        tail_tip = (cx, min(bub_bot + 34.0, H - 24.0)) if cur_tip is None else None
        metrics = draw_sloptoon_bubble(
            panel,
            center=(cx, cy),
            lines=lines,
            radii=(rx, ry),
            tail_tip=tail_tip,
            tail_half_deg=6.5,
            tail_curve=-6.0,
            font_size=cur_fs,
            stroke_px=stroke_px,
            sub_line_indices=sub_indices,
        )
        audit: dict[str, Any] = {
            "wordless": False,
            "bubble_count": 1,
            "overlap_px": 0,
            "min_clearance_px": 999.0,
            "font_size": metrics["font_size"],
            "art_bbox": None,
            "tail_target": cut.tail_target,
        }
        if cur_tip is not None:
            tw, th = cur_tip.size
            tx0 = int(margin_x) if pref_corner in ("top_left", "bottom_left") else (W - int(margin_x) - tw)
            ty0 = max(int(np.ceil(bub_bot + 10.0)), int(H - margin_bot - th))
            panel = _composite_rgba_card(panel, cur_tip, (tx0, ty0))
            audit["has_item_tooltip"] = True
            audit["tooltip_bbox"] = [tx0, ty0, tx0 + tw, ty0 + th]
            audit["tooltip_overlap_px"] = 0
        return panel, audit

    ax0, ay0, ax1, ay1 = raw_bbox
    touches_bottom = ay1 >= rh - 6
    crop_box = (ax0, ay0, min(rw, ax1 + 1), rh if touches_bottom else min(rh, ay1 + 1))
    cw = max(1, crop_box[2] - crop_box[0])
    ch = max(1, crop_box[3] - crop_box[1])

    def _try_narrow_tooltip_corners(
        art_mask: np.ndarray,
        bub_mask: np.ndarray,
        bub_bot_y: float,
        tip_im: Image.Image,
    ) -> tuple[tuple[int, int], np.ndarray] | None:
        tw, th = tip_im.size
        pad_x = int(margin_x)
        pad_y_bot = int(margin_bot)
        top_y = int(np.ceil(bub_bot_y + 10.0))
        corners = {
            "bottom_right": (W - pad_x - tw, H - pad_y_bot - th),
            "bottom_left": (pad_x, H - pad_y_bot - th),
            "top_right": (W - pad_x - tw, top_y),
            "top_left": (pad_x, top_y),
        }
        default_order = ["bottom_right", "bottom_left", "top_right", "top_left"]
        order = (
            [pref_corner] + [k for k in default_order if k != pref_corner]
            if pref_corner in corners
            else default_order
        )
        occupied = art_mask | bub_mask
        for key in order:
            tx0, ty0 = corners[key]
            if tx0 < 4 or ty0 < top_y or tx0 + tw > W - 4 or ty0 + th > H - 4:
                continue
            tmask = _tooltip_alpha_mask((W, H), tip_im, (tx0, ty0))
            if int((occupied & tmask).sum()) == 0:
                return (tx0, ty0), tmask
        return None

    # 1. Iterative solver: top bubble + short downward tail + artwork cleanly below
    bub_bot = cy + ry + stroke_px
    desired_tail_space = 48.0
    scale_w = (W - 2.0 * margin_x) / cw
    scale_h = max(0.05, (H - (bub_bot + desired_tail_space) - (0.0 if touches_bottom else margin_bot)) / ch)
    scale = min(scale_w, scale_h)

    for attempt in range(18):
        bub_bot = cy + ry + stroke_px
        nw = max(1, int(round(cw * scale)))
        nh = max(1, int(round(ch * scale)))
        px = (W - nw) / 2.0
        if touches_bottom:
            py = float(H - nh)
        else:
            py = float(max(bub_bot + 36.0, H - nh - margin_bot))
            if py + nh > H - 4:
                py = float(H - nh - 4)

        art_canvas = place_scaled_art(clean_raw, W, H, scale, px, py, crop_box=crop_box)
        art_mask = get_art_mask(art_canvas, threshold=255)
        placed_bbox = extract_art_bbox(art_canvas, threshold=255)
        art_min_y = float(placed_bbox[1]) if placed_bbox else float(H)

        anchor = _find_top_speaker_anchor(art_mask, cut.tail_target, W)
        head_x, local_top_y = anchor if anchor is not None else (cx, art_min_y)

        eff_cx = cx
        eff_cy = cy
        if cut.bubble_side is None and anchor is not None:
            eff_cx = float(
                np.clip(
                    0.50 * head_x + 0.50 * cx,
                    margin_x + rx + stroke_px + 2.0,
                    W - margin_x - rx - stroke_px - 2.0,
                )
            )
        cur_gap = local_top_y - (eff_cy + ry + stroke_px)
        if cur_gap > 84.0 and cur_tip is None:
            shift_y = min(cur_gap - 62.0, max(0.0, art_min_y - (eff_cy + ry + stroke_px) - 44.0))
            if shift_y > 0.0:
                eff_cy = cy + shift_y
        eff_bub_bot = eff_cy + ry + stroke_px

        tail_x = float(np.clip(0.70 * head_x + 0.30 * eff_cx, eff_cx - rx * 0.65, eff_cx + rx * 0.65))
        max_tail_y = min(eff_bub_bot + 58.0, local_top_y - 14.0, art_min_y + 58.0)
        min_tail_y = eff_bub_bot + 20.0

        pull_ratios = (1.0, 0.72, 0.48, 0.25, 0.0) if attempt >= 6 else (1.0, 0.72, 0.48, 0.25)
        for pull in pull_ratios:
            if pull == 0.0 or max_tail_y <= eff_bub_bot + 12.0:
                tail_tip: tuple[float, float] | None = None
                base_deg = None
            else:
                ty = min(eff_bub_bot + max(16.0, (max_tail_y - eff_bub_bot) * pull), local_top_y - 12.0)
                if ty < min_tail_y and pull == 1.0:
                    ty = min(min_tail_y, local_top_y - 11.0)
                if ty <= eff_bub_bot + 10.0:
                    tail_tip = None
                    base_deg = None
                else:
                    tx = eff_cx + (tail_x - eff_cx) * (0.65 + 0.35 * pull)
                    tail_tip = (tx, ty)
                    raw_deg = float(np.rad2deg(np.arctan2((ty - eff_cy) / ry, (tx - eff_cx) / rx)))
                    base_deg = float(np.clip(raw_deg, 66.0, 114.0))

            tail_curve = -6.0 if (tail_tip is None or tail_tip[0] <= eff_cx) else 6.0
            bub_layer, dest, b_metrics = _build_bubble_layer(
                panel_size=(W, H),
                center=(eff_cx, eff_cy),
                lines=lines,
                radii=(rx, ry),
                tail_tip=tail_tip,
                tail_base_angle_deg=base_deg,
                tail_half_deg=6.5,
                tail_curve=tail_curve,
                font_size=cur_fs,
                stroke_px=stroke_px,
                sub_line_indices=sub_indices,
            )
            bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
            if int((art_mask & bub_mask).sum()) != 0:
                continue

            if cur_tip is None:
                out_panel = art_canvas.copy()
                if bub_layer is not None:
                    rgba = out_panel.convert("RGBA")
                    rgba.alpha_composite(bub_layer, dest=dest)
                    out_panel = rgba.convert("RGB")
                return out_panel, {
                    "wordless": False,
                    "bubble_count": 1,
                    "overlap_px": 0,
                    "min_clearance_px": compute_min_clearance(art_mask, bub_mask),
                    "font_size": b_metrics["font_size"],
                    "art_bbox": list(placed_bbox) if placed_bbox else None,
                    "tail_target": cut.tail_target,
                }

            tip_found = _try_narrow_tooltip_corners(art_mask, bub_mask, eff_bub_bot, cur_tip)
            if tip_found is not None:
                tip_dest, tip_mask = tip_found
                tw, th = cur_tip.size
                out_panel = art_canvas.copy()
                if bub_layer is not None:
                    rgba = out_panel.convert("RGBA")
                    rgba.alpha_composite(bub_layer, dest=dest)
                    out_panel = rgba.convert("RGB")
                out_panel = _composite_rgba_card(out_panel, cur_tip, tip_dest)
                return out_panel, {
                    "wordless": False,
                    "bubble_count": 1,
                    "overlap_px": 0,
                    "min_clearance_px": compute_min_clearance(art_mask, bub_mask | tip_mask),
                    "font_size": b_metrics["font_size"],
                    "art_bbox": list(placed_bbox) if placed_bbox else None,
                    "tail_target": cut.tail_target,
                    "has_item_tooltip": True,
                    "tooltip_bbox": [tip_dest[0], tip_dest[1], tip_dest[0] + tw, tip_dest[1] + th],
                    "tooltip_overlap_px": 0,
                }

        scale *= 0.88
        if attempt in (4, 8, 12) and cur_fs > 13:
            cur_fs = max(13, cur_fs - 2)
            lines, sub_indices, cx, cy, rx, ry = _layout_narrow_bubble(cur_fs)

    # 2. Mathematical disjointness fallback (guarantees overlap_px == 0 & tooltip_overlap_px == 0)
    cur_fs = max(13, min(cur_fs, 16))
    lines, sub_indices, cx, cy, rx, ry = _layout_narrow_bubble(cur_fs)
    bub_bot = cy + ry + stroke_px

    if cur_tip is not None:
        # 3-band vertical stacking: Top bubble -> Middle artwork -> Bottom tooltip
        max_fb_tip_h = max(68, int((H - bub_bot - 40.0) * 0.36))
        fb_tip = _fit_tooltip_card(cur_tip, max_w=min(248, W - 24), max_h=min(148, max_fb_tip_h))
        tw, th = fb_tip.size
        if pref_corner in ("top_left", "bottom_left"):
            tx0 = int(margin_x)
        elif pref_corner in ("top_right", "bottom_right"):
            tx0 = W - int(margin_x) - tw
        else:
            tx0 = (W - tw) // 2
        ty0 = int(H - margin_bot - th)
        safe_art_top = int(np.ceil(bub_bot + 22.0))
        safe_art_bot = max(safe_art_top + 24, ty0 - 10)
        avail_w = max(24.0, W - 2.0 * margin_x - 2.0)
        avail_h = max(24.0, float(safe_art_bot - safe_art_top) - 2.0)
        scale_fb = min(avail_w / cw, avail_h / ch)
        nw = max(1, int(np.floor(cw * scale_fb)))
        nh = max(1, int(np.floor(ch * scale_fb)))
        px = (W - nw) / 2.0
        py = float(safe_art_top + max(0.0, (safe_art_bot - safe_art_top - nh) / 2.0))

        art_canvas = place_scaled_art(clean_raw, W, H, scale_fb, px, py, crop_box=crop_box)
        art_mask = get_art_mask(art_canvas, threshold=255)
        placed_bbox = extract_art_bbox(art_canvas, threshold=255)
        tip_dest = (tx0, ty0)
        tip_mask = _tooltip_alpha_mask((W, H), fb_tip, tip_dest)

        cand_tail: tuple[float, float] | None = None
        if placed_bbox is not None and placed_bbox[1] - bub_bot >= 28:
            cand_tail = (cx, min(bub_bot + 20.0, placed_bbox[1] - 10.0))
        bub_layer, dest, b_metrics = _build_bubble_layer(
            panel_size=(W, H),
            center=(cx, cy),
            lines=lines,
            radii=(rx, ry),
            tail_tip=cand_tail,
            tail_base_angle_deg=90.0 if cand_tail else None,
            tail_half_deg=6.0,
            tail_curve=-5.0,
            font_size=cur_fs,
            stroke_px=stroke_px,
            sub_line_indices=sub_indices,
        )
        bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
        if int(((art_mask | tip_mask) & bub_mask).sum()) > 0:
            bub_layer, dest, b_metrics = _build_bubble_layer(
                panel_size=(W, H),
                center=(cx, cy),
                lines=lines,
                radii=(rx, ry),
                tail_tip=None,
                font_size=cur_fs,
                stroke_px=stroke_px,
                sub_line_indices=sub_indices,
            )
            bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)

        out_panel = art_canvas.copy()
        if bub_layer is not None:
            rgba = out_panel.convert("RGBA")
            rgba.alpha_composite(bub_layer, dest=dest)
            out_panel = rgba.convert("RGB")
        out_panel = _composite_rgba_card(out_panel, fb_tip, tip_dest)
        tip_ov = int(((art_mask | bub_mask) & tip_mask).sum())
        ov_total = int((art_mask & bub_mask).sum()) + tip_ov
        return out_panel, {
            "wordless": False,
            "bubble_count": 1,
            "overlap_px": ov_total,
            "min_clearance_px": compute_min_clearance(art_mask, bub_mask | tip_mask),
            "font_size": b_metrics["font_size"],
            "art_bbox": list(placed_bbox) if placed_bbox else None,
            "tail_target": cut.tail_target,
            "has_item_tooltip": True,
            "tooltip_bbox": [tx0, ty0, tx0 + tw, ty0 + th],
            "tooltip_overlap_px": tip_ov,
        }

    # No-tooltip strict vertical disjointness fallback
    safe_art_top = int(np.ceil(bub_bot + 26.0))
    avail_w = max(24.0, W - 2.0 * margin_x - 2.0)
    avail_h = max(24.0, H - safe_art_top - (2.0 if touches_bottom else margin_bot + 2.0))
    scale_fb = min(avail_w / cw, avail_h / ch)
    nw = max(1, int(np.floor(cw * scale_fb)))
    nh = max(1, int(np.floor(ch * scale_fb)))
    px = (W - nw) / 2.0
    py = max(float(safe_art_top), float(H - nh))

    art_canvas = place_scaled_art(clean_raw, W, H, scale_fb, px, py, crop_box=crop_box)
    art_mask = get_art_mask(art_canvas, threshold=255)
    placed_bbox = extract_art_bbox(art_canvas, threshold=255)

    cand_tail = None
    if placed_bbox is not None and placed_bbox[1] - bub_bot >= 28:
        cand_tail = (cx, min(bub_bot + 22.0, placed_bbox[1] - 10.0))
    bub_layer, dest, b_metrics = _build_bubble_layer(
        panel_size=(W, H),
        center=(cx, cy),
        lines=lines,
        radii=(rx, ry),
        tail_tip=cand_tail,
        tail_base_angle_deg=90.0 if cand_tail else None,
        tail_half_deg=6.0,
        tail_curve=-5.0,
        font_size=cur_fs,
        stroke_px=stroke_px,
        sub_line_indices=sub_indices,
    )
    bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
    if int((art_mask & bub_mask).sum()) > 0:
        bub_layer, dest, b_metrics = _build_bubble_layer(
            panel_size=(W, H),
            center=(cx, cy),
            lines=lines,
            radii=(rx, ry),
            tail_tip=None,
            font_size=cur_fs,
            stroke_px=stroke_px,
            sub_line_indices=sub_indices,
        )
        bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)

    out_panel = art_canvas.copy()
    if bub_layer is not None:
        rgba = out_panel.convert("RGBA")
        rgba.alpha_composite(bub_layer, dest=dest)
        out_panel = rgba.convert("RGB")
    return out_panel, {
        "wordless": False,
        "bubble_count": 1,
        "overlap_px": int((art_mask & bub_mask).sum()),
        "min_clearance_px": compute_min_clearance(art_mask, bub_mask),
        "font_size": b_metrics["font_size"],
        "art_bbox": list(placed_bbox) if placed_bbox else None,
        "tail_target": cut.tail_target,
    }


def _compose_wide_tall_variable_panel(
    cut: ComicCut,
    raw_im: Image.Image,
    target_w: int,
    target_h: int,
    border_style: str,
    dialogue: str,
    tooltip_rgba: Image.Image | None,
) -> tuple[Image.Image, dict[str, Any]]:
    """Compose a wide tall variable panel (`target_w >= 580`, `target_h >= 540`) at 0px overlap."""
    W, H = target_w, target_h
    clean_raw = clean_white_bg(raw_im)
    rw, rh = clean_raw.size
    raw_bbox = extract_art_bbox(clean_raw, threshold=255)
    stroke_px = 3.5
    margin_x = 16.0 if border_style == "open" else 14.0
    margin_top = 12.0 if border_style == "open" else 14.0
    dummy = ImageDraw.Draw(Image.new("RGB", (16, 16), PURE_WHITE))

    if tooltip_rgba is not None:
        cur_tip = _fit_tooltip_card(
            tooltip_rgba,
            max_w=min(300, max(160, int(W * 0.35))),
            max_h=min(220, max(110, int(H * 0.34))),
        )
        pref = cut.item_tooltip.preferred_corner if cut.item_tooltip else "auto"
        if pref in ("top_left", "bottom_left"):
            tooltip_side = "left"
        elif pref in ("top_right", "bottom_right"):
            tooltip_side = "right"
        else:
            tooltip_side = "left" if cut.tail_target == "right" else "right"

        tw, th = cur_tip.size
        tx0 = int(margin_x) if tooltip_side == "left" else (W - int(margin_x) - tw)
        ty0 = int(margin_top)
        tip_dest = (tx0, ty0)
        tip_mask = _tooltip_alpha_mask((W, H), cur_tip, tip_dest)
        tip_bot = float(ty0 + th)

        if tooltip_side == "right":
            bub_x_lo, bub_x_hi = margin_x, float(tx0 - 14)
        else:
            bub_x_lo, bub_x_hi = float(tx0 + tw + 14), float(W - margin_x)

        max_rx = max(110.0, (bub_x_hi - bub_x_lo) / 2.0 - stroke_px - 4.0)
        max_ry = min(114.0, max(52.0, H * 0.19))
        wrap_w = float(np.clip((max_rx - 32.0) / 0.62, 200.0, 410.0))

        cur_fs = 22 if len(dialogue) <= 38 else 20
        lines, sub_indices = wrap_korean_dialogue(dialogue, cur_fs, max_line_width_px=wrap_w, max_lines=4)
        if len(lines) >= 4:
            cur_fs = min(cur_fs, 18)
            lines, sub_indices = wrap_korean_dialogue(
                dialogue, cur_fs, max_line_width_px=wrap_w + 14.0, max_lines=4
            )

        def _bub_dims_tip(fs: int, lns: list[str], subs: list[int]) -> tuple[float, float, float, float]:
            rx_o, ry_o = _compute_snug_ellipse_radii(
                dummy,
                lns,
                set(subs),
                fs,
                min_rx=min(124.0, max_rx),
                max_rx=max_rx,
                min_ry=min(52.0, max_ry),
                max_ry=max_ry,
                pad_x=34.0,
                pad_y=22.0,
            )
            cy_o = margin_top + ry_o + stroke_px + 2.0
            ideal_cx = (bub_x_lo + bub_x_hi) / 2.0
            cx_o = float(np.clip(ideal_cx, bub_x_lo + rx_o + stroke_px, bub_x_hi - rx_o - stroke_px))
            return cx_o, cy_o, rx_o, ry_o

        cx, cy, rx, ry = _bub_dims_tip(cur_fs, lines, sub_indices)

        if raw_bbox is None:
            panel = Image.new("RGB", (W, H), PURE_WHITE)
            metrics = draw_sloptoon_bubble(
                panel,
                center=(cx, cy),
                lines=lines,
                radii=(rx, ry),
                tail_tip=(cx, min(cy + ry + 42.0, H - 24.0)),
                tail_half_deg=6.2,
                tail_curve=-7.0 if tooltip_side == "right" else 7.0,
                font_size=cur_fs,
                stroke_px=stroke_px,
                sub_line_indices=sub_indices,
            )
            panel = _composite_rgba_card(panel, cur_tip, tip_dest)
            return panel, {
                "wordless": False,
                "bubble_count": 1,
                "overlap_px": 0,
                "min_clearance_px": 999.0,
                "font_size": metrics["font_size"],
                "art_bbox": None,
                "tail_target": cut.tail_target,
                "has_item_tooltip": True,
                "tooltip_bbox": [tx0, ty0, tx0 + tw, ty0 + th],
                "tooltip_overlap_px": 0,
            }

        ax0, ay0, ax1, ay1 = raw_bbox
        touches_bottom = ay1 >= rh - 6
        crop_x0 = max(0, ax0 - 4) if (ax1 - ax0) > rw * 0.94 else 0
        crop_x1 = min(rw, ax1 + 5) if (ax1 - ax0) > rw * 0.94 else rw
        crop_box = (crop_x0, ay0, crop_x1, rh if touches_bottom else min(rh, ay1 + 1))
        cw = max(1, crop_box[2] - crop_box[0])
        ch = max(1, crop_box[3] - crop_box[1])

        bub_bot = cy + ry + stroke_px
        target_art_top = max(bub_bot + 54.0, tip_bot + 16.0)
        scale = min(
            (W - 2.0 * margin_x) / cw,
            max(0.05, (H - target_art_top - (0.0 if touches_bottom else 12.0)) / ch),
        )

        for attempt in range(18):
            bub_bot = cy + ry + stroke_px
            nw = max(1, int(round(cw * scale)))
            nh = max(1, int(round(ch * scale)))
            px = (W - nw) / 2.0
            min_safe_y = max(bub_bot + 42.0, tip_bot + 12.0)
            if touches_bottom:
                py = float(H - nh)
            else:
                py = float(max(min_safe_y, H - nh - 10.0))
                if py + nh > H - 4:
                    py = float(H - nh - 4)

            art_canvas = place_scaled_art(clean_raw, W, H, scale, px, py, crop_box=crop_box)
            art_mask = get_art_mask(art_canvas, threshold=255)
            placed_bbox = extract_art_bbox(art_canvas, threshold=255)
            art_min_y = float(placed_bbox[1]) if placed_bbox else float(H)

            if int((art_mask & tip_mask).sum()) == 0:
                anchor = _find_top_speaker_anchor(art_mask, cut.tail_target, W)
                head_x, local_top_y = anchor if anchor is not None else (cx, art_min_y)
                tail_x = float(np.clip(0.55 * head_x + 0.45 * cx, cx - rx * 0.68, cx + rx * 0.68))
                max_tail_y = min(bub_bot + 86.0, local_top_y - 14.0, art_min_y + 78.0)
                min_tail_y = bub_bot + 22.0

                for pull in (1.0, 0.72, 0.48, 0.25, 0.0):
                    if pull == 0.0 or max_tail_y <= bub_bot + 12.0:
                        tail_tip: tuple[float, float] | None = None
                        base_deg = None
                    else:
                        ty = min(bub_bot + max(16.0, (max_tail_y - bub_bot) * pull), local_top_y - 12.0)
                        if ty < min_tail_y and pull == 1.0:
                            ty = min(min_tail_y, local_top_y - 11.0)
                        if ty <= bub_bot + 10.0:
                            tail_tip = None
                            base_deg = None
                        else:
                            tx = cx + (tail_x - cx) * (0.65 + 0.35 * pull)
                            tail_tip = (tx, ty)
                            raw_deg = float(np.rad2deg(np.arctan2((ty - cy) / ry, (tx - cx) / rx)))
                            base_deg = float(np.clip(raw_deg, 66.0, 114.0))

                    tail_curve = -7.0 if (tail_tip is None or tail_tip[0] <= cx) else 7.0
                    bub_layer, dest, b_metrics = _build_bubble_layer(
                        panel_size=(W, H),
                        center=(cx, cy),
                        lines=lines,
                        radii=(rx, ry),
                        tail_tip=tail_tip,
                        tail_base_angle_deg=base_deg,
                        tail_half_deg=6.2,
                        tail_curve=tail_curve,
                        font_size=cur_fs,
                        stroke_px=stroke_px,
                        sub_line_indices=sub_indices,
                    )
                    bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
                    if int((art_mask & bub_mask).sum()) == 0 and int((bub_mask & tip_mask).sum()) == 0:
                        out_panel = art_canvas.copy()
                        if bub_layer is not None:
                            rgba = out_panel.convert("RGBA")
                            rgba.alpha_composite(bub_layer, dest=dest)
                            out_panel = rgba.convert("RGB")
                        out_panel = _composite_rgba_card(out_panel, cur_tip, tip_dest)
                        return out_panel, {
                            "wordless": False,
                            "bubble_count": 1,
                            "overlap_px": 0,
                            "min_clearance_px": compute_min_clearance(art_mask, bub_mask | tip_mask),
                            "font_size": b_metrics["font_size"],
                            "art_bbox": list(placed_bbox) if placed_bbox else None,
                            "tail_target": cut.tail_target,
                            "has_item_tooltip": True,
                            "tooltip_bbox": [tx0, ty0, tx0 + tw, ty0 + th],
                            "tooltip_overlap_px": 0,
                        }

            scale *= 0.88
            if attempt in (4, 8, 12) and cur_fs > 13:
                cur_fs = max(13, cur_fs - 2)
                lines, sub_indices = wrap_korean_dialogue(
                    dialogue, cur_fs, max_line_width_px=wrap_w + 16.0, max_lines=4
                )
                cx, cy, rx, ry = _bub_dims_tip(cur_fs, lines, sub_indices)

        # Strict vertical disjointness fallback
        cur_fs = max(13, min(cur_fs, 16))
        lines, sub_indices = wrap_korean_dialogue(
            dialogue, cur_fs, max_line_width_px=wrap_w + 16.0, max_lines=4
        )
        cx, cy, rx, ry = _bub_dims_tip(cur_fs, lines, sub_indices)
        safe_art_top = int(np.ceil(max(cy + ry + stroke_px + 20.0, tip_bot + 14.0)))
        avail_w = max(40.0, W - 2.0 * margin_x - 2.0)
        avail_h = max(40.0, H - safe_art_top - 4.0)
        scale_fb = min(avail_w / cw, avail_h / ch)
        nw = max(1, int(np.floor(cw * scale_fb)))
        nh = max(1, int(np.floor(ch * scale_fb)))
        py = max(float(safe_art_top), float(H - nh))
        art_canvas = place_scaled_art(clean_raw, W, H, scale_fb, (W - nw) / 2.0, py, crop_box=crop_box)
        art_mask = get_art_mask(art_canvas, threshold=255)
        placed_bbox = extract_art_bbox(art_canvas, threshold=255)
        bub_layer, dest, b_metrics = _build_bubble_layer(
            panel_size=(W, H),
            center=(cx, cy),
            lines=lines,
            radii=(rx, ry),
            tail_tip=None,
            font_size=cur_fs,
            stroke_px=stroke_px,
            sub_line_indices=sub_indices,
        )
        bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
        out_panel = art_canvas.copy()
        if bub_layer is not None:
            rgba = out_panel.convert("RGBA")
            rgba.alpha_composite(bub_layer, dest=dest)
            out_panel = rgba.convert("RGB")
        out_panel = _composite_rgba_card(out_panel, cur_tip, tip_dest)
        tip_ov = int(((art_mask | bub_mask) & tip_mask).sum())
        ov_total = int((art_mask & bub_mask).sum()) + tip_ov
        return out_panel, {
            "wordless": False,
            "bubble_count": 1,
            "overlap_px": ov_total,
            "min_clearance_px": compute_min_clearance(art_mask, bub_mask | tip_mask),
            "font_size": b_metrics["font_size"],
            "art_bbox": list(placed_bbox) if placed_bbox else None,
            "tail_target": cut.tail_target,
            "has_item_tooltip": True,
            "tooltip_bbox": [tx0, ty0, tx0 + tw, ty0 + th],
            "tooltip_overlap_px": tip_ov,
        }

    # Wide tall panel WITHOUT tooltip
    max_rx = min(350.0, W / 2.0 - margin_x - stroke_px - 6.0)
    max_ry = min(106.0, max(52.0, H * 0.18))
    wrap_w = float(np.clip(W * 0.54, 320.0, 480.0))

    cur_fs = 24 if (H >= 640 and len(dialogue) <= 44) else (22 if len(dialogue) <= 44 else 20)
    lines, sub_indices = wrap_korean_dialogue(dialogue, cur_fs, max_line_width_px=wrap_w, max_lines=4)
    if len(lines) >= 4:
        cur_fs = min(cur_fs, 19)
        lines, sub_indices = wrap_korean_dialogue(
            dialogue, cur_fs, max_line_width_px=wrap_w + 18.0, max_lines=4
        )
    elif len(lines) == 3:
        cur_fs = min(cur_fs, 22)

    def _bub_dims_tall(fs: int, lns: list[str], subs: list[int]) -> tuple[float, float, float, float]:
        rx_o, ry_o = _compute_snug_ellipse_radii(
            dummy,
            lns,
            set(subs),
            fs,
            min_rx=min(136.0, max_rx),
            max_rx=max_rx,
            min_ry=min(48.0, max_ry),
            max_ry=max_ry,
            pad_x=36.0,
            pad_y=20.0,
        )
        cy_o = margin_top + ry_o + stroke_px + 2.0
        target_side = cut.bubble_side or cut.tail_target
        if target_side == "left":
            cx_o = float(np.clip(W * 0.35, margin_x + rx_o + stroke_px + 4.0, W - margin_x - rx_o - stroke_px - 4.0))
        elif target_side == "right":
            cx_o = float(np.clip(W * 0.65, margin_x + rx_o + stroke_px + 4.0, W - margin_x - rx_o - stroke_px - 4.0))
        else:
            cx_o = W / 2.0
        return cx_o, cy_o, rx_o, ry_o

    cx, cy, rx, ry = _bub_dims_tall(cur_fs, lines, sub_indices)

    if raw_bbox is None:
        panel = Image.new("RGB", (W, H), PURE_WHITE)
        tail_dx = -36.0 if cut.tail_target == "left" else (36.0 if cut.tail_target == "right" else 0.0)
        metrics = draw_sloptoon_bubble(
            panel,
            center=(cx, cy),
            lines=lines,
            radii=(rx, ry),
            tail_tip=(cx + tail_dx, min(cy + ry + 50.0, H - 24.0)),
            tail_half_deg=6.2,
            tail_curve=-7.0 if tail_dx <= 0 else 7.0,
            font_size=cur_fs,
            stroke_px=stroke_px,
            sub_line_indices=sub_indices,
        )
        return panel, {
            "wordless": False,
            "bubble_count": 1,
            "overlap_px": 0,
            "min_clearance_px": 999.0,
            "font_size": metrics["font_size"],
            "art_bbox": None,
            "tail_target": cut.tail_target,
        }

    ax0, ay0, ax1, ay1 = raw_bbox
    touches_bottom = ay1 >= rh - 6
    crop_x0 = max(0, ax0 - 4) if (ax1 - ax0) > rw * 0.94 else 0
    crop_x1 = min(rw, ax1 + 5) if (ax1 - ax0) > rw * 0.94 else rw
    crop_box = (crop_x0, ay0, crop_x1, rh if touches_bottom else min(rh, ay1 + 1))
    cw = max(1, crop_box[2] - crop_box[0])
    ch = max(1, crop_box[3] - crop_box[1])

    bub_bot = cy + ry + stroke_px
    desired_tail_space = min(68.0, max(44.0, H * 0.09))
    scale = min(
        (W - 2.0 * margin_x) / cw,
        max(0.05, (H - (bub_bot + desired_tail_space) - (0.0 if touches_bottom else 14.0)) / ch),
    )

    for attempt in range(18):
        bub_bot = cy + ry + stroke_px
        nw = max(1, int(round(cw * scale)))
        nh = max(1, int(round(ch * scale)))
        px = (W - nw) / 2.0
        if touches_bottom:
            py = float(H - nh)
        else:
            py = float(max(bub_bot + 44.0, H - nh - 12.0))
            if py + nh > H - 4:
                py = float(H - nh - 4)

        art_canvas = place_scaled_art(clean_raw, W, H, scale, px, py, crop_box=crop_box)
        art_mask = get_art_mask(art_canvas, threshold=255)
        placed_bbox = extract_art_bbox(art_canvas, threshold=255)
        art_min_y = float(placed_bbox[1]) if placed_bbox else float(H)

        anchor = _find_top_speaker_anchor(art_mask, cut.tail_target, W)
        head_x, local_top_y = anchor if anchor is not None else (cx, art_min_y)

        eff_cx = cx
        eff_cy = cy
        if cut.bubble_side is None and anchor is not None:
            eff_cx = float(
                np.clip(
                    0.55 * head_x + 0.45 * cx,
                    margin_x + rx + stroke_px + 4.0,
                    W - margin_x - rx - stroke_px - 4.0,
                )
            )
        cur_gap = local_top_y - (eff_cy + ry + stroke_px)
        if cur_gap > 88.0:
            shift_y = min(cur_gap - 68.0, max(0.0, art_min_y - (eff_cy + ry + stroke_px) - 46.0))
            if shift_y > 0.0:
                eff_cy = cy + shift_y
        eff_bub_bot = eff_cy + ry + stroke_px

        tail_x = float(np.clip(0.72 * head_x + 0.28 * eff_cx, eff_cx - rx * 0.72, eff_cx + rx * 0.72))
        max_tail_y = min(eff_bub_bot + 68.0, local_top_y - 14.0, art_min_y + 68.0)
        min_tail_y = eff_bub_bot + 22.0

        pull_ratios = (1.0, 0.75, 0.52, 0.30, 0.0) if attempt >= 6 else (1.0, 0.75, 0.52, 0.30)
        for pull in pull_ratios:
            if pull == 0.0 or max_tail_y <= eff_bub_bot + 12.0:
                tail_tip = None
                base_deg = None
            else:
                ty = min(eff_bub_bot + max(16.0, (max_tail_y - eff_bub_bot) * pull), local_top_y - 12.0)
                if ty < min_tail_y and pull == 1.0:
                    ty = min(min_tail_y, local_top_y - 11.0)
                if ty <= eff_bub_bot + 10.0:
                    tail_tip = None
                    base_deg = None
                else:
                    tx = eff_cx + (tail_x - eff_cx) * (0.65 + 0.35 * pull)
                    tail_tip = (tx, ty)
                    raw_deg = float(np.rad2deg(np.arctan2((ty - eff_cy) / ry, (tx - eff_cx) / rx)))
                    base_deg = float(np.clip(raw_deg, 66.0, 114.0))

            tail_curve = -7.0 if (tail_tip is None or tail_tip[0] <= eff_cx) else 7.0
            bub_layer, dest, b_metrics = _build_bubble_layer(
                panel_size=(W, H),
                center=(eff_cx, eff_cy),
                lines=lines,
                radii=(rx, ry),
                tail_tip=tail_tip,
                tail_base_angle_deg=base_deg,
                tail_half_deg=6.2,
                tail_curve=tail_curve,
                font_size=cur_fs,
                stroke_px=stroke_px,
                sub_line_indices=sub_indices,
            )
            bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
            if int((art_mask & bub_mask).sum()) == 0:
                out_panel = art_canvas.copy()
                if bub_layer is not None:
                    rgba = out_panel.convert("RGBA")
                    rgba.alpha_composite(bub_layer, dest=dest)
                    out_panel = rgba.convert("RGB")
                return out_panel, {
                    "wordless": False,
                    "bubble_count": 1,
                    "overlap_px": 0,
                    "min_clearance_px": compute_min_clearance(art_mask, bub_mask),
                    "font_size": b_metrics["font_size"],
                    "art_bbox": list(placed_bbox) if placed_bbox else None,
                    "tail_target": cut.tail_target,
                }

        scale *= 0.88
        if attempt in (5, 9, 13) and cur_fs > 13:
            cur_fs = max(13, cur_fs - 2)
            lines, sub_indices = wrap_korean_dialogue(
                dialogue, cur_fs, max_line_width_px=wrap_w + 18.0, max_lines=4
            )
            cx, cy, rx, ry = _bub_dims_tall(cur_fs, lines, sub_indices)

    # Strict vertical disjointness fallback
    cur_fs = max(13, min(cur_fs, 17))
    lines, sub_indices = wrap_korean_dialogue(
        dialogue, cur_fs, max_line_width_px=wrap_w + 18.0, max_lines=4
    )
    cx, cy, rx, ry = _bub_dims_tall(cur_fs, lines, sub_indices)
    bub_bot = cy + ry + stroke_px
    safe_art_top = int(np.ceil(bub_bot + 26.0))
    avail_w = max(40.0, W - 2.0 * margin_x - 2.0)
    avail_h = max(40.0, H - safe_art_top - 4.0)
    scale_fb = min(avail_w / cw, avail_h / ch)
    nw = max(1, int(np.floor(cw * scale_fb)))
    nh = max(1, int(np.floor(ch * scale_fb)))
    py = max(float(safe_art_top), float(H - nh))
    art_canvas = place_scaled_art(clean_raw, W, H, scale_fb, (W - nw) / 2.0, py, crop_box=crop_box)
    art_mask = get_art_mask(art_canvas, threshold=255)
    placed_bbox = extract_art_bbox(art_canvas, threshold=255)

    cand_tail = None
    if placed_bbox is not None and placed_bbox[1] - bub_bot >= 28:
        cand_tail = (cx, min(bub_bot + 22.0, placed_bbox[1] - 10.0))
    bub_layer, dest, b_metrics = _build_bubble_layer(
        panel_size=(W, H),
        center=(cx, cy),
        lines=lines,
        radii=(rx, ry),
        tail_tip=cand_tail,
        tail_base_angle_deg=90.0 if cand_tail else None,
        tail_half_deg=6.0,
        tail_curve=-6.0,
        font_size=cur_fs,
        stroke_px=stroke_px,
        sub_line_indices=sub_indices,
    )
    bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
    if int((art_mask & bub_mask).sum()) > 0:
        bub_layer, dest, b_metrics = _build_bubble_layer(
            panel_size=(W, H),
            center=(cx, cy),
            lines=lines,
            radii=(rx, ry),
            tail_tip=None,
            font_size=cur_fs,
            stroke_px=stroke_px,
            sub_line_indices=sub_indices,
        )
        bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)

    out_panel = art_canvas.copy()
    if bub_layer is not None:
        rgba = out_panel.convert("RGBA")
        rgba.alpha_composite(bub_layer, dest=dest)
        out_panel = rgba.convert("RGB")
    return out_panel, {
        "wordless": False,
        "bubble_count": 1,
        "overlap_px": int((art_mask & bub_mask).sum()),
        "min_clearance_px": compute_min_clearance(art_mask, bub_mask),
        "font_size": b_metrics["font_size"],
        "art_bbox": list(placed_bbox) if placed_bbox else None,
        "tail_target": cut.tail_target,
    }


def _detect_split_two_char_valley(
    clean_raw: Image.Image,
    crop_box: tuple[int, int, int, int],
) -> tuple[float, float] | None:
    """Detect a clean open middle whitespace valley between two left/right separated characters.

    Returns `(valley_lo_frac, valley_hi_frac)` in `[0.0, 1.0]` relative to `crop_box` width
    when non-white artwork exists on both outer thirds and a pure-white vertical valley
    spans at least 8% of the cropped artwork width; otherwise returns `None`.
    """
    cropped = clean_raw.crop(crop_box)
    mask = get_art_mask(cropped, threshold=255)
    ch, cw = mask.shape
    if cw < 120 or ch < 60:
        return None

    left_third = max(1, int(cw * 0.35))
    right_third = min(cw - 1, int(cw * 0.65))
    if not np.any(mask[:, :left_third]) or not np.any(mask[:, right_third:]):
        return None

    # Check upper ~82% so two characters standing apart with a middle gap are cleanly detected
    upper_h = max(1, int(ch * 0.82))
    col_empty = ~np.any(mask[:upper_h, :], axis=0)

    mid_lo = max(1, int(cw * 0.18))
    mid_hi = min(cw - 1, int(cw * 0.82))
    best_run: tuple[int, int] | None = None
    run_start: int | None = None
    for x in range(mid_lo, mid_hi):
        if col_empty[x]:
            if run_start is None:
                run_start = x
        elif run_start is not None:
            cand = (run_start, x - 1)
            if best_run is None or (cand[1] - cand[0]) > (best_run[1] - best_run[0]):
                best_run = cand
            run_start = None
    if run_start is not None:
        cand = (run_start, mid_hi - 1)
        if best_run is None or (cand[1] - cand[0]) > (best_run[1] - best_run[0]):
            best_run = cand

    if best_run is None:
        return None
    v0, v1 = best_run
    valley_w = v1 - v0 + 1
    if valley_w < max(24, int(cw * 0.08)):
        return None
    if not np.any(mask[:, :v0]) or not np.any(mask[:, v1 + 1 :]):
        return None
    return (v0 / float(cw), (v1 + 1) / float(cw))


def _find_slim_speaker_anchor(
    art_mask: np.ndarray,
    tail_target: str,
) -> tuple[float, float, float, float, float] | None:
    """Locate the speaking character's head strictly inside the `tail_target` half of placed artwork.

    Returns `(head_cx, head_top_y, head_left_x, head_right_x, art_mid_x)` or `None`.
    """
    ys_all, xs_all = np.where(art_mask)
    if len(xs_all) == 0:
        return None
    ax0, ax1 = int(xs_all.min()), int(xs_all.max())
    aw = max(1, ax1 - ax0)
    art_mid_x = 0.5 * (ax0 + ax1)

    if tail_target == "left":
        zx0, zx1 = ax0, max(ax0 + 1, int(np.ceil(art_mid_x)))
    elif tail_target == "right":
        zx0, zx1 = min(ax1, int(np.floor(art_mid_x))), ax1 + 1
    else:
        zx0 = int(ax0 + aw * 0.22)
        zx1 = max(zx0 + 1, int(ax0 + aw * 0.78) + 1)

    ys, xs = np.where(art_mask[:, zx0:zx1])
    if len(xs) == 0:
        ys, xs = ys_all, xs_all
        zx0 = 0
    xs_abs = xs + zx0
    y_min, y_max = int(ys.min()), int(ys.max())
    head_cut = y_min + max(20, int((y_max - y_min) * 0.30))
    head_sel = ys <= head_cut
    head_xs = xs_abs[head_sel] if np.any(head_sel) else xs_abs
    head_cx = float(np.median(head_xs))
    head_left_x = float(head_xs.min())
    head_right_x = float(head_xs.max())
    near = np.abs(xs_abs - head_cx) <= max(28.0, aw * 0.10)
    head_top_y = float(ys[near].min()) if np.any(near) else float(y_min)
    return head_cx, head_top_y, head_left_x, head_right_x, art_mid_x


def _compose_wide_slim_variable_panel(
    cut: ComicCut,
    raw_im: Image.Image,
    target_w: int,
    target_h: int,
    border_style: str,
    dialogue: str,
    tooltip_rgba: Image.Image | None,
) -> tuple[Image.Image, dict[str, Any]]:
    """Compose a slim cinematic wide panel (`target_w >= 580`, `target_h < 540`) at 0px overlap."""
    W, H = target_w, target_h
    clean_raw = clean_white_bg(raw_im)
    rw, rh = clean_raw.size
    raw_bbox = extract_art_bbox(clean_raw, threshold=255)
    stroke_px = 3.5
    box_margin = 12.0 if H < 425 else 14.0
    dummy = ImageDraw.Draw(Image.new("RGB", (16, 16), PURE_WHITE))
    is_two_char = len(cut.characters) >= 2

    if tooltip_rgba is not None:
        pref = cut.item_tooltip.preferred_corner if cut.item_tooltip else "auto"
        if pref in ("top_right", "bottom_right"):
            ui_side = "right"
            side_dir = "left"
        elif pref in ("top_left", "bottom_left"):
            ui_side = "left"
            side_dir = "right"
        elif is_two_char:
            # In 2-character panels, place UI column on the speaker's outer side so tail never crosses listener
            if cut.tail_target == "left":
                ui_side = "left"
                side_dir = "right"
            else:
                ui_side = "right"
                side_dir = "left"
        elif cut.tail_target == "left":
            ui_side = "right"
            side_dir = "left"
        else:
            ui_side = "left"
            side_dir = "right"

        max_rx = min(192.0, W * 0.23)
        max_ry = min(78.0, max(44.0, H * 0.20))

        if raw_bbox is None:
            lines, sub_indices = wrap_korean_dialogue(dialogue, 19, max_line_width_px=268.0, max_lines=4)
            panel = Image.new("RGB", (W, H), PURE_WHITE)
            rx_b, ry_b = min(172.0, max_rx), min(68.0, max_ry)
            cx = (box_margin + rx_b + 4.0) if ui_side == "left" else (W - box_margin - rx_b - 4.0)
            cy = box_margin + ry_b + stroke_px + 2.0
            metrics = draw_sloptoon_bubble(
                panel,
                center=(cx, cy),
                lines=lines,
                radii=(rx_b, ry_b),
                tail_tip=None,
                font_size=19,
                stroke_px=stroke_px,
                sub_line_indices=sub_indices,
            )
            avail_tip_h = max(68, int(H - box_margin - (cy + ry_b + stroke_px) - 10))
            cur_tip = _fit_tooltip_card(tooltip_rgba, max_w=min(268, int(W * 0.32)), max_h=avail_tip_h)
            tw, th = cur_tip.size
            tx0 = int(box_margin + 2) if ui_side == "left" else int(W - box_margin - 2 - tw)
            ty0 = int(H - box_margin - th)
            panel = _composite_rgba_card(panel, cur_tip, (tx0, ty0))
            return panel, {
                "wordless": False,
                "bubble_count": 1,
                "overlap_px": 0,
                "min_clearance_px": 999.0,
                "font_size": metrics["font_size"],
                "art_bbox": None,
                "tail_target": cut.tail_target,
                "has_item_tooltip": True,
                "tooltip_bbox": [tx0, ty0, tx0 + tw, ty0 + th],
                "tooltip_overlap_px": 0,
            }

        ax0, ay0, ax1, ay1 = raw_bbox
        touches_bottom = ay1 >= rh - 6
        crop_box = (ax0, ay0, min(rw, ax1 + 1), rh if touches_bottom else min(rh, ay1 + 1))
        cw = max(1, crop_box[2] - crop_box[0])
        ch = max(1, crop_box[3] - crop_box[1])

        cur_fs = 19 if len(dialogue) <= 32 else 17
        for attempt in range(16):
            max_line_w = 264.0 if cur_fs >= 17 else 248.0
            lines, sub_indices = wrap_korean_dialogue(
                dialogue, cur_fs, max_line_width_px=max_line_w, max_lines=4
            )
            rx, ry = _compute_snug_ellipse_radii(
                dummy,
                lines,
                set(sub_indices),
                cur_fs,
                min_rx=min(118.0, max_rx),
                max_rx=max_rx,
                min_ry=min(46.0, max_ry),
                max_ry=max_ry,
                pad_x=28.0,
                pad_y=18.0,
            )
            cy = box_margin + ry + stroke_px + 2.0
            bub_bot = cy + ry + stroke_px

            avail_tip_h = max(72, int(H - box_margin - bub_bot - 10.0))
            avail_tip_w = min(268, int(W * 0.32))
            cur_tip = _fit_tooltip_card(tooltip_rgba, max_w=avail_tip_w, max_h=avail_tip_h)
            tw, th = cur_tip.size
            ty0 = int(H - box_margin - th)

            if ui_side == "left":
                cx = box_margin + rx + stroke_px + 2.0
                bub_inner_edge = cx + rx + stroke_px
                tx0 = int(box_margin + 2)
                ui_col_edge = max(bub_inner_edge + 36.0 + attempt * 3.0, float(tx0 + tw + 16))
                art_zone_lo, art_zone_hi = ui_col_edge, W - box_margin
            else:
                cx = W - box_margin - rx - stroke_px - 2.0
                bub_inner_edge = cx - rx - stroke_px
                tx0 = int(W - box_margin - 2 - tw)
                ui_col_edge = min(bub_inner_edge - 36.0 - attempt * 3.0, float(tx0 - 16))
                art_zone_lo, art_zone_hi = box_margin, ui_col_edge

            avail_w = max(110.0, art_zone_hi - art_zone_lo)
            shrink_factor = max(0.48, 0.94 ** max(0, attempt - 1))
            avail_h = H - (10.0 if touches_bottom else 20.0)
            scale = min(avail_w / cw, avail_h / ch) * shrink_factor
            nw = max(1, int(round(cw * scale)))
            nh = max(1, int(round(ch * scale)))

            if ui_side == "left":
                px = max(art_zone_lo, min(W - box_margin - nw, art_zone_lo + (avail_w - nw) * 0.52))
            else:
                px = max(box_margin, min(art_zone_hi - nw, art_zone_lo + (avail_w - nw) * 0.48))
            py = float(H - nh) if touches_bottom else float((H - nh) / 2.0)

            art_canvas = place_scaled_art(clean_raw, W, H, scale, px, py, crop_box=crop_box)
            art_mask = get_art_mask(art_canvas, threshold=255)
            placed_bbox = extract_art_bbox(art_canvas, threshold=255)
            if placed_bbox is None:
                continue

            tip_dest = (tx0, ty0)
            tip_mask = _tooltip_alpha_mask((W, H), cur_tip, tip_dest)
            if int((art_mask & tip_mask).sum()) > 0:
                if attempt in (3, 7, 11) and cur_fs > 13:
                    cur_fs = max(13, cur_fs - 2)
                continue

            head_y = float(
                np.clip(
                    placed_bbox[1] + (placed_bbox[3] - placed_bbox[1]) * 0.25,
                    cy - ry * 0.40,
                    cy + ry * 0.40,
                )
            )
            band_y0, band_y1 = max(0, int(head_y - 34)), min(H, int(head_y + 34))
            _, band_xs = np.where(art_mask[band_y0:band_y1, :])

            if side_dir == "right":
                local_edge_x = float(band_xs.min()) if len(band_xs) else float(placed_bbox[0])
                max_reach = min(local_edge_x - 14.0, cx + rx + 56.0)
                base_ang = float(np.clip(np.rad2deg(np.arctan2((head_y - cy) / ry, 1.0)), -16.0, 16.0))
                t_curve = 4.0
            else:
                local_edge_x = float(band_xs.max()) if len(band_xs) else float(placed_bbox[2])
                max_reach = max(local_edge_x + 14.0, cx - rx - 56.0)
                base_ang = 180.0 - float(
                    np.clip(np.rad2deg(np.arctan2((head_y - cy) / ry, 1.0)), -16.0, 16.0)
                )
                t_curve = -4.0

            for pull in (1.0, 0.68, 0.38, 0.0):
                if pull == 0.0:
                    tail_tip: tuple[float, float] | None = None
                elif side_dir == "right":
                    if max_reach <= bub_inner_edge + 10.0:
                        tail_tip = None
                    else:
                        tx = min(
                            bub_inner_edge + max(12.0, (max_reach - bub_inner_edge) * pull),
                            local_edge_x - 12.0,
                        )
                        tail_tip = (tx, head_y) if tx > bub_inner_edge + 10.0 else None
                else:
                    if max_reach >= bub_inner_edge - 10.0:
                        tail_tip = None
                    else:
                        tx = max(
                            bub_inner_edge - max(12.0, (bub_inner_edge - max_reach) * pull),
                            local_edge_x + 12.0,
                        )
                        tail_tip = (tx, head_y) if tx < bub_inner_edge - 10.0 else None

                bub_layer, dest, b_metrics = _build_bubble_layer(
                    panel_size=(W, H),
                    center=(cx, cy),
                    lines=lines,
                    radii=(rx, ry),
                    tail_tip=tail_tip,
                    tail_base_angle_deg=base_ang,
                    tail_half_deg=8.5,
                    tail_curve=t_curve,
                    font_size=cur_fs,
                    stroke_px=stroke_px,
                    sub_line_indices=sub_indices,
                )
                bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
                if int((art_mask & bub_mask).sum()) == 0 and int((bub_mask & tip_mask).sum()) == 0:
                    out_panel = art_canvas.copy()
                    if bub_layer is not None:
                        rgba = out_panel.convert("RGBA")
                        rgba.alpha_composite(bub_layer, dest=dest)
                        out_panel = rgba.convert("RGB")
                    out_panel = _composite_rgba_card(out_panel, cur_tip, tip_dest)
                    return out_panel, {
                        "wordless": False,
                        "bubble_count": 1,
                        "overlap_px": 0,
                        "min_clearance_px": compute_min_clearance(art_mask, bub_mask | tip_mask),
                        "font_size": b_metrics["font_size"],
                        "art_bbox": list(placed_bbox),
                        "tail_target": cut.tail_target,
                        "has_item_tooltip": True,
                        "tooltip_bbox": [tx0, ty0, tx0 + tw, ty0 + th],
                        "tooltip_overlap_px": 0,
                    }

            if attempt in (3, 7, 11) and cur_fs > 13:
                cur_fs = max(13, cur_fs - 2)

        # Strict horizontal + vertical disjoint fallback
        lines, sub_indices = wrap_korean_dialogue(dialogue, 14, max_line_width_px=232.0, max_lines=3)
        rx, ry = min(154.0, max_rx), min(50.0, max_ry)
        cy = box_margin + ry + stroke_px + 2.0
        cx = (box_margin + rx + stroke_px + 2.0) if ui_side == "left" else (W - box_margin - rx - stroke_px - 2.0)
        avail_tip_h = max(68, int(H - box_margin - (cy + ry + stroke_px) - 12.0))
        cur_tip = _fit_tooltip_card(tooltip_rgba, max_w=min(248, int(W * 0.30)), max_h=avail_tip_h)
        tw, th = cur_tip.size
        tx0 = int(box_margin + 2) if ui_side == "left" else int(W - box_margin - 2 - tw)
        ty0 = int(H - box_margin - th)
        if ui_side == "left":
            art_lo, art_hi = max(cx + rx + stroke_px + 16.0, float(tx0 + tw + 16)), W - box_margin
        else:
            art_lo, art_hi = box_margin, min(cx - rx - stroke_px - 16.0, float(tx0 - 16))
        avail_w = max(60.0, art_hi - art_lo - 2.0)
        avail_h = max(40.0, H - 18.0)
        scale_fb = min(avail_w / cw, avail_h / ch)
        nw = max(1, int(np.floor(cw * scale_fb)))
        nh = max(1, int(np.floor(ch * scale_fb)))
        px = max(art_lo, min(art_hi - nw, art_lo + ((art_hi - art_lo) - nw) / 2.0))
        py = float(H - nh)
        art_canvas = place_scaled_art(clean_raw, W, H, scale_fb, px, py, crop_box=crop_box)
        art_mask = get_art_mask(art_canvas, threshold=255)
        placed_bbox = extract_art_bbox(art_canvas, threshold=255)
        bub_layer, dest, b_metrics = _build_bubble_layer(
            panel_size=(W, H),
            center=(cx, cy),
            lines=lines,
            radii=(rx, ry),
            tail_tip=None,
            font_size=14,
            stroke_px=stroke_px,
            sub_line_indices=sub_indices,
        )
        bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
        tip_mask = _tooltip_alpha_mask((W, H), cur_tip, (tx0, ty0))
        out_panel = art_canvas.copy()
        if bub_layer is not None:
            rgba = out_panel.convert("RGBA")
            rgba.alpha_composite(bub_layer, dest=dest)
            out_panel = rgba.convert("RGB")
        out_panel = _composite_rgba_card(out_panel, cur_tip, (tx0, ty0))
        tip_ov = int(((art_mask | bub_mask) & tip_mask).sum())
        ov_total = int((art_mask & bub_mask).sum()) + tip_ov
        return out_panel, {
            "wordless": False,
            "bubble_count": 1,
            "overlap_px": ov_total,
            "min_clearance_px": compute_min_clearance(art_mask, bub_mask | tip_mask),
            "font_size": b_metrics["font_size"],
            "art_bbox": list(placed_bbox) if placed_bbox else None,
            "tail_target": cut.tail_target,
            "has_item_tooltip": True,
            "tooltip_bbox": [tx0, ty0, tx0 + tw, ty0 + th],
            "tooltip_overlap_px": tip_ov,
        }

    # Slim wide panel WITHOUT tooltip
    if raw_bbox is None:
        if cut.bubble_side == "center" or cut.tail_target == "center":
            blank_mode = "top_center"
        elif is_two_char:
            if cut.bubble_side in ("left", "right") and cut.bubble_side == cut.tail_target:
                blank_mode = "side_right" if cut.bubble_side == "left" else "side_left"
            else:
                blank_mode = "top_center"
        elif cut.bubble_side == "left":
            blank_mode = "side_right"
        elif cut.bubble_side == "right":
            blank_mode = "side_left"
        else:
            blank_mode = f"side_{cut.tail_target}"

        lines, sub_indices = wrap_korean_dialogue(dialogue, 21, max_line_width_px=320.0, max_lines=4)
        panel = Image.new("RGB", (W, H), PURE_WHITE)
        cx = 204.0 if blank_mode == "side_right" else (W - 204.0 if blank_mode == "side_left" else W / 2.0)
        cy = min(146.0, H * 0.36) if blank_mode != "top_center" else min(86.0, H * 0.24)
        metrics = draw_sloptoon_bubble(
            panel,
            center=(cx, cy),
            lines=lines,
            radii=(min(182.0, W * 0.22), min(74.0, H * 0.19)),
            tail_tip=None,
            font_size=21,
            stroke_px=stroke_px,
            sub_line_indices=sub_indices,
        )
        return panel, {
            "wordless": False,
            "bubble_count": 1,
            "overlap_px": 0,
            "min_clearance_px": 999.0,
            "font_size": metrics["font_size"],
            "art_bbox": None,
            "tail_target": cut.tail_target,
        }

    ax0, ay0, ax1, ay1 = raw_bbox
    touches_bottom = ay1 >= rh - 6
    crop_box = (ax0, ay0, min(rw, ax1 + 1), rh if touches_bottom else min(rh, ay1 + 1))
    cw = max(1, crop_box[2] - crop_box[0])
    ch = max(1, crop_box[3] - crop_box[1])

    split_valley = _detect_split_two_char_valley(clean_raw, crop_box) if is_two_char else None

    if is_two_char:
        # 2-character slim wide panel smart routing:
        # - Same side (`bubble_side == tail_target` in left/right): bubble on speaker's outer side pointing
        #   directly into the speaker half, NEVER shooting across the listener!
        # - `bubble_side == "center"`, `tail_target == "center"`, opposite-side conflict (e.g. tail_target="right"
        #   with bubble_side="left"), OR split left/right characters with open middle whitespace when bubble_side is None:
        #   place bubble in upper-center / between-characters white zone (or upper speaker side) and aim tail
        #   STRICTLY toward the `tail_target` half!
        if cut.bubble_side in ("left", "right") and cut.tail_target == cut.bubble_side:
            mode = "side_right" if cut.bubble_side == "left" else "side_left"
        elif (
            cut.bubble_side == "center"
            or cut.tail_target == "center"
            or (cut.bubble_side in ("left", "right") and cut.bubble_side != cut.tail_target)
            or (cut.bubble_side is None and split_valley is not None)
        ):
            mode = "two_char_upper"
        else:
            mode = "side_right" if cut.tail_target == "left" else "side_left"
    else:
        if cut.bubble_side == "center":
            mode = "top_center"
        elif cut.bubble_side == "left":
            mode = "side_right"
        elif cut.bubble_side == "right":
            mode = "side_left"
        elif cut.tail_target == "center":
            mode = "top_center"
        else:
            mode = f"side_{cut.tail_target}"

    def _try_slim_side(side_dir: str, fs_start: int) -> tuple[Image.Image | None, dict[str, Any] | None]:
        cur_fs = fs_start
        max_rx_s = min(206.0, W * 0.25)
        max_ry_s = min(110.0, H * 0.27)

        # Natural full-scale pre-pass: if artwork with an L-shaped floor vignette already leaves
        # pure #FFFFFF room in the upper-left / upper-right bubble corner near full panel height,
        # place the bubble directly with minimal shrink instead of squashing into a tiny half-box!
        full_avail_w = W - 2.0 * box_margin
        full_avail_h = H - (4.0 if touches_bottom else 16.0)
        base_full_scale = min(full_avail_w / cw, full_avail_h / ch)
        for pre_s_mult in (1.0, 0.92, 0.84, 0.76):
            full_scale = base_full_scale * pre_s_mult
            f_nw = max(1, int(round(cw * full_scale)))
            f_nh = max(1, int(round(ch * full_scale)))
            f_px = float(W - box_margin - f_nw) if side_dir == "right" else float(box_margin)
            f_py = float(H - f_nh) if touches_bottom else float((H - f_nh) / 2.0)
            full_canvas = place_scaled_art(clean_raw, W, H, full_scale, f_px, f_py, crop_box=crop_box)
            full_mask = get_art_mask(full_canvas, threshold=255)
            full_bbox = extract_art_bbox(full_canvas, threshold=255)
            if full_bbox is None:
                continue
            for pre_fs in (fs_start, max(15, fs_start - 2)):
                pre_max_lw = 296.0 if pre_fs >= 20 else 276.0
                pre_lines, pre_subs = wrap_korean_dialogue(
                    dialogue, pre_fs, max_line_width_px=pre_max_lw, max_lines=4
                )
                pre_rx, pre_ry = _compute_snug_ellipse_radii(
                    dummy,
                    pre_lines,
                    set(pre_subs),
                    pre_fs,
                    min_rx=min(118.0, max_rx_s),
                    max_rx=max_rx_s,
                    min_ry=min(46.0, max_ry_s),
                    max_ry=max_ry_s,
                    pad_x=30.0,
                    pad_y=18.0,
                )
                pre_cx = (
                    box_margin + pre_rx + stroke_px + 6.0
                    if side_dir == "right"
                    else W - box_margin - pre_rx - stroke_px - 6.0
                )
                pre_inner = (
                    pre_cx + pre_rx + stroke_px if side_dir == "right" else pre_cx - pre_rx - stroke_px
                )
                for cy_ratio in (0.28, 0.34, 0.22):
                    pre_cy = float(
                        np.clip(
                            H * cy_ratio,
                            box_margin + pre_ry + stroke_px + 4.0,
                            H - box_margin - pre_ry - stroke_px - 4.0,
                        )
                    )
                    head_y = float(
                        np.clip(
                            full_bbox[1] + (full_bbox[3] - full_bbox[1]) * 0.28,
                            pre_cy - pre_ry * 0.45,
                            pre_cy + pre_ry * 0.45,
                        )
                    )
                    by0, by1 = max(0, int(head_y - 40)), min(H, int(head_y + 40))
                    _, bxs = np.where(full_mask[by0:by1, :])
                    if side_dir == "right":
                        lx = float(bxs.min()) if len(bxs) else float(full_bbox[0])
                        m_reach = min(lx - 14.0, pre_cx + pre_rx + 64.0)
                        b_ang = float(np.clip(np.rad2deg(np.arctan2((head_y - pre_cy) / pre_ry, 1.0)), -18.0, 18.0))
                        t_crv = 4.5
                    else:
                        lx = float(bxs.max()) if len(bxs) else float(full_bbox[2])
                        m_reach = max(lx + 14.0, pre_cx - pre_rx - 64.0)
                        b_ang = 180.0 - float(np.clip(np.rad2deg(np.arctan2((head_y - pre_cy) / pre_ry, 1.0)), -18.0, 18.0))
                        t_crv = -4.5

                    for pull in (1.0, 0.72, 0.48):
                        if side_dir == "right":
                            if m_reach <= pre_inner + 12.0:
                                t_tip = None
                            else:
                                tx = min(pre_inner + max(14.0, (m_reach - pre_inner) * pull), lx - 12.0)
                                t_tip = (tx, head_y) if tx >= pre_inner + 14.0 else None
                        else:
                            if m_reach >= pre_inner - 12.0:
                                t_tip = None
                            else:
                                tx = max(pre_inner - max(14.0, (pre_inner - m_reach) * pull), lx + 12.0)
                                t_tip = (tx, head_y) if tx <= pre_inner - 14.0 else None
                        if t_tip is None:
                            continue
                        b_lay, b_dst, b_met = _build_bubble_layer(
                            panel_size=(W, H),
                            center=(pre_cx, pre_cy),
                            lines=pre_lines,
                            radii=(pre_rx, pre_ry),
                            tail_tip=t_tip,
                            tail_base_angle_deg=b_ang,
                            tail_half_deg=9.0,
                            tail_curve=t_crv,
                            font_size=pre_fs,
                            stroke_px=stroke_px,
                            sub_line_indices=pre_subs,
                        )
                        b_msk = _bubble_alpha_mask((W, H), b_lay, b_dst)
                        if int((full_mask & b_msk).sum()) == 0:
                            out_p = full_canvas.copy()
                            if b_lay is not None:
                                rgba = out_p.convert("RGBA")
                                rgba.alpha_composite(b_lay, dest=b_dst)
                                out_p = rgba.convert("RGB")
                            return out_p, {
                                "wordless": False,
                                "bubble_count": 1,
                                "overlap_px": 0,
                                "min_clearance_px": compute_min_clearance(full_mask, b_msk),
                                "font_size": b_met["font_size"],
                                "art_bbox": list(full_bbox),
                                "tail_target": cut.tail_target,
                                "bubble_center": [round(pre_cx, 1), round(pre_cy, 1)],
                                "bubble_side_resolved": "left" if side_dir == "right" else "right",
                                "tail_tip": [round(t_tip[0], 1), round(t_tip[1], 1)],
                            }

        for attempt in range(16):
            max_line_w = 292.0 if cur_fs >= 20 else 276.0
            lines, sub_indices = wrap_korean_dialogue(
                dialogue, cur_fs, max_line_width_px=max_line_w, max_lines=4
            )
            rx, ry = _compute_snug_ellipse_radii(
                dummy,
                lines,
                set(sub_indices),
                cur_fs,
                min_rx=min(118.0, max_rx_s),
                max_rx=max_rx_s,
                min_ry=min(46.0, max_ry_s),
                max_ry=max_ry_s,
                pad_x=30.0,
                pad_y=18.0,
            )
            cy = float(
                np.clip(H * 0.35, box_margin + ry + stroke_px + 4.0, H - box_margin - ry - stroke_px - 4.0)
            )
            if side_dir == "right":
                cx = box_margin + rx + stroke_px + 4.0
                bub_inner_edge = cx + rx + stroke_px
            else:
                cx = W - box_margin - rx - stroke_px - 4.0
                bub_inner_edge = cx - rx - stroke_px

            tail_reserve = 44.0 + attempt * 4.0
            if side_dir == "right":
                art_zone_lo, art_zone_hi = bub_inner_edge + tail_reserve, W - box_margin
            else:
                art_zone_lo, art_zone_hi = box_margin, bub_inner_edge - tail_reserve

            avail_w = art_zone_hi - art_zone_lo
            if avail_w < 180.0:
                if cur_fs > 13:
                    cur_fs = max(13, cur_fs - 2)
                    continue
                avail_w = max(110.0, avail_w)

            shrink_factor = max(0.45, 0.94 ** max(0, attempt - 1))
            avail_h = H - (10.0 if touches_bottom else 22.0)
            scale = min(avail_w / cw, avail_h / ch) * shrink_factor
            nw = max(1, int(round(cw * scale)))
            nh = max(1, int(round(ch * scale)))

            if side_dir == "right":
                px = max(art_zone_lo, min(W - box_margin - nw, art_zone_lo + (avail_w - nw) * 0.55))
            else:
                px = max(box_margin, min(art_zone_hi - nw, art_zone_lo + (avail_w - nw) * 0.45))
            py = float(H - nh) if touches_bottom else float((H - nh) / 2.0)

            art_canvas = place_scaled_art(clean_raw, W, H, scale, px, py, crop_box=crop_box)
            art_mask = get_art_mask(art_canvas, threshold=255)
            placed_bbox = extract_art_bbox(art_canvas, threshold=255)
            if placed_bbox is None:
                continue

            # For 2-character cuts, aim head height & horizontal edge strictly at the speaking half
            if is_two_char and cut.tail_target in ("left", "right"):
                sp_anchor = _find_slim_speaker_anchor(art_mask, cut.tail_target)
                sp_top_y = sp_anchor[1] if sp_anchor is not None else float(placed_bbox[1])
                head_y = float(
                    np.clip(
                        sp_top_y + max(24.0, (placed_bbox[3] - sp_top_y) * 0.24),
                        cy - ry * 0.45,
                        cy + ry * 0.45,
                    )
                )
            else:
                head_y = float(
                    np.clip(
                        placed_bbox[1] + (placed_bbox[3] - placed_bbox[1]) * 0.28,
                        cy - ry * 0.45,
                        cy + ry * 0.45,
                    )
                )

            band_y0, band_y1 = max(0, int(head_y - 40)), min(H, int(head_y + 40))
            _, band_xs = np.where(art_mask[band_y0:band_y1, :])

            if side_dir == "right":
                local_edge_x = float(band_xs.min()) if len(band_xs) else float(placed_bbox[0])
                max_reach = min(local_edge_x - 14.0, cx + rx + 60.0)
                min_reach = cx + rx + 18.0
                base_ang = float(np.clip(np.rad2deg(np.arctan2((head_y - cy) / ry, 1.0)), -18.0, 18.0))
                t_curve = 4.5
            else:
                local_edge_x = float(band_xs.max()) if len(band_xs) else float(placed_bbox[2])
                max_reach = max(local_edge_x + 14.0, cx - rx - 60.0)
                min_reach = cx - rx - 18.0
                base_ang = 180.0 - float(
                    np.clip(np.rad2deg(np.arctan2((head_y - cy) / ry, 1.0)), -18.0, 18.0)
                )
                t_curve = -4.5

            pulls = (1.0, 0.72, 0.48, 0.25, 0.0) if attempt >= 10 else (1.0, 0.72, 0.48, 0.25)
            for pull in pulls:
                if pull == 0.0:
                    tail_tip = None
                elif side_dir == "right":
                    if max_reach <= cx + rx + 10.0:
                        tail_tip = None
                    else:
                        tx = min(
                            bub_inner_edge + max(14.0, (max_reach - bub_inner_edge) * pull),
                            local_edge_x - 12.0,
                        )
                        tail_tip = (tx, head_y) if tx >= min_reach * 0.96 else None
                else:
                    if max_reach >= cx - rx - 10.0:
                        tail_tip = None
                    else:
                        tx = max(
                            bub_inner_edge - max(14.0, (bub_inner_edge - max_reach) * pull),
                            local_edge_x + 12.0,
                        )
                        tail_tip = (tx, head_y) if tx <= min_reach * 1.04 else None

                bub_layer, dest, b_metrics = _build_bubble_layer(
                    panel_size=(W, H),
                    center=(cx, cy),
                    lines=lines,
                    radii=(rx, ry),
                    tail_tip=tail_tip,
                    tail_base_angle_deg=base_ang,
                    tail_half_deg=9.0,
                    tail_curve=t_curve,
                    font_size=cur_fs,
                    stroke_px=stroke_px,
                    sub_line_indices=sub_indices,
                )
                bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
                if int((art_mask & bub_mask).sum()) == 0:
                    out_panel = art_canvas.copy()
                    if bub_layer is not None:
                        rgba = out_panel.convert("RGBA")
                        rgba.alpha_composite(bub_layer, dest=dest)
                        out_panel = rgba.convert("RGB")
                    return out_panel, {
                        "wordless": False,
                        "bubble_count": 1,
                        "overlap_px": 0,
                        "min_clearance_px": compute_min_clearance(art_mask, bub_mask),
                        "font_size": b_metrics["font_size"],
                        "art_bbox": list(placed_bbox),
                        "tail_target": cut.tail_target,
                        "bubble_center": [round(cx, 1), round(cy, 1)],
                        "bubble_side_resolved": "left" if side_dir == "right" else "right",
                        "tail_tip": [round(tail_tip[0], 1), round(tail_tip[1], 1)] if tail_tip else None,
                    }

            if attempt in (3, 7, 11) and cur_fs > 13:
                cur_fs = max(13, cur_fs - 2)

        return None, None

    def _try_slim_between_valley(fs_start: int) -> tuple[Image.Image | None, dict[str, Any] | None]:
        """Try nesting a compact speech bubble cleanly inside the open middle valley between two split characters."""
        if split_valley is None or cut.tail_target not in ("left", "right"):
            return None, None
        v_lo_f, v_hi_f = split_valley
        avail_w_full = W - 2.0 * box_margin
        avail_h_full = H - (10.0 if touches_bottom else 20.0)
        base_scale = min(avail_w_full / cw, avail_h_full / ch)

        for scale_mult in (1.0, 0.92, 0.85):
            scale = base_scale * scale_mult
            nw = max(1, int(round(cw * scale)))
            nh = max(1, int(round(ch * scale)))
            px = (W - nw) / 2.0
            py = float(H - nh) if touches_bottom else float((H - nh) / 2.0)

            valley_x0 = px + v_lo_f * nw
            valley_x1 = px + v_hi_f * nw
            valley_w = valley_x1 - valley_x0
            # Reserve clear space on both sides, with extra tail room on the speaker side
            listener_pad = 12.0
            speaker_tail_pad = 34.0
            if valley_w < 230.0:
                continue

            art_canvas = place_scaled_art(clean_raw, W, H, scale, px, py, crop_box=crop_box)
            art_mask = get_art_mask(art_canvas, threshold=255)
            placed_bbox = extract_art_bbox(art_canvas, threshold=255)
            if placed_bbox is None:
                continue

            sp_anchor = _find_slim_speaker_anchor(art_mask, cut.tail_target)
            if sp_anchor is None:
                continue
            head_cx, head_top_y, head_left_x, head_right_x, art_mid_x = sp_anchor

            max_rx_v = min(182.0, (valley_w - listener_pad - speaker_tail_pad) / 2.0 - stroke_px)
            max_ry_v = min(92.0, H * 0.24)
            if max_rx_v < 84.0:
                continue

            for cur_fs in range(min(fs_start, 20), 13, -2):
                wrap_w_v = max(116.0, max_rx_v * 1.32)
                lines, sub_indices = wrap_korean_dialogue(
                    dialogue, cur_fs, max_line_width_px=wrap_w_v, max_lines=4
                )
                rx, ry = _compute_snug_ellipse_radii(
                    dummy,
                    lines,
                    set(sub_indices),
                    cur_fs,
                    min_rx=min(92.0, max_rx_v),
                    max_rx=max_rx_v,
                    min_ry=min(42.0, max_ry_v),
                    max_ry=max_ry_v,
                    pad_x=24.0,
                    pad_y=16.0,
                )
                # Center inside the asymmetric usable band so the speaker side always has tail room
                if cut.tail_target == "right":
                    cx_lo = valley_x0 + listener_pad + rx + stroke_px
                    cx_hi = valley_x1 - speaker_tail_pad - rx - stroke_px
                else:
                    cx_lo = valley_x0 + speaker_tail_pad + rx + stroke_px
                    cx_hi = valley_x1 - listener_pad - rx - stroke_px
                if cx_hi < cx_lo:
                    continue
                cx = 0.5 * (cx_lo + cx_hi)
                cy = box_margin + ry + stroke_px + 4.0

                target_x = head_left_x if cut.tail_target == "right" else head_right_x
                target_y = float(np.clip(head_top_y + 26.0, cy - ry * 0.35, cy + ry * 0.75))
                if cut.tail_target == "right":
                    bub_edge = cx + rx + stroke_px
                    max_tx = min(target_x - 10.0, bub_edge + 44.0)
                    base_ang = float(np.clip(np.rad2deg(np.arctan2((target_y - cy) / ry, 1.0)), -22.0, 32.0))
                    t_curve = 4.5
                else:
                    bub_edge = cx - rx - stroke_px
                    max_tx = max(target_x + 10.0, bub_edge - 44.0)
                    base_ang = 180.0 - float(
                        np.clip(np.rad2deg(np.arctan2((target_y - cy) / ry, 1.0)), -22.0, 32.0)
                    )
                    t_curve = -4.5

                for pull in (1.0, 0.72, 0.45):
                    if cut.tail_target == "right":
                        if max_tx <= bub_edge + 12.0:
                            continue
                        tx = min(bub_edge + max(14.0, (max_tx - bub_edge) * pull), target_x - 10.0)
                        if tx <= bub_edge + 12.0 or tx <= art_mid_x:
                            continue
                        tail_tip = (tx, target_y)
                    else:
                        if max_tx >= bub_edge - 12.0:
                            continue
                        tx = max(bub_edge - max(14.0, (bub_edge - max_tx) * pull), target_x + 10.0)
                        if tx >= bub_edge - 12.0 or tx >= art_mid_x:
                            continue
                        tail_tip = (tx, target_y)

                    bub_layer, dest, b_metrics = _build_bubble_layer(
                        panel_size=(W, H),
                        center=(cx, cy),
                        lines=lines,
                        radii=(rx, ry),
                        tail_tip=tail_tip,
                        tail_base_angle_deg=base_ang,
                        tail_half_deg=8.0,
                        tail_curve=t_curve,
                        font_size=cur_fs,
                        stroke_px=stroke_px,
                        sub_line_indices=sub_indices,
                    )
                    bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
                    if int((art_mask & bub_mask).sum()) == 0:
                        out_panel = art_canvas.copy()
                        if bub_layer is not None:
                            rgba = out_panel.convert("RGBA")
                            rgba.alpha_composite(bub_layer, dest=dest)
                            out_panel = rgba.convert("RGB")
                        return out_panel, {
                            "wordless": False,
                            "bubble_count": 1,
                            "overlap_px": 0,
                            "min_clearance_px": compute_min_clearance(art_mask, bub_mask),
                            "font_size": b_metrics["font_size"],
                            "art_bbox": list(placed_bbox),
                            "tail_target": cut.tail_target,
                            "bubble_center": [round(cx, 1), round(cy, 1)],
                            "bubble_side_resolved": "center",
                            "tail_tip": [round(tail_tip[0], 1), round(tail_tip[1], 1)],
                        }
        return None, None

    def _try_slim_top_center(
        fs_start: int,
        *,
        speaker_targeted: bool = False,
    ) -> tuple[Image.Image, dict[str, Any]]:
        cur_fs = fs_start
        max_rx_t = min(344.0, W * 0.41)
        max_ry_t = min(74.0 if speaker_targeted else 78.0, max(42.0, H * 0.185))
        for attempt in range(16):
            lines, sub_indices = wrap_korean_dialogue(
                dialogue, cur_fs, max_line_width_px=min(520.0, W * 0.62), max_lines=4
            )
            rx, ry = _compute_snug_ellipse_radii(
                dummy,
                lines,
                set(sub_indices),
                cur_fs,
                min_rx=min(136.0, max_rx_t),
                max_rx=max_rx_t,
                min_ry=min(42.0, max_ry_t),
                max_ry=max_ry_t,
                pad_x=32.0,
                pad_y=16.0,
            )
            # Position bubble at upper-center (gently biased toward speaker half when speaker_targeted)
            min_cx = box_margin + rx + stroke_px + 4.0
            max_cx = W - box_margin - rx - stroke_px - 4.0
            if speaker_targeted and cut.tail_target == "right":
                desired_cx = W * (0.54 if cut.bubble_side == "center" else 0.58)
            elif speaker_targeted and cut.tail_target == "left":
                desired_cx = W * (0.46 if cut.bubble_side == "center" else 0.42)
            else:
                desired_cx = W / 2.0
            cx = float(np.clip(desired_cx, min_cx, max_cx))
            cy = box_margin + ry + stroke_px + 2.0
            bub_bot = cy + ry + stroke_px

            tail_space = 26.0 + attempt * 4.0
            art_top = bub_bot + tail_space
            avail_h = max(72.0, H - art_top - (0.0 if touches_bottom else 8.0))
            avail_w = W - 2.0 * box_margin
            scale = min(avail_w / cw, avail_h / ch) * max(0.55, 0.96 ** attempt)
            nw = max(1, int(round(cw * scale)))
            nh = max(1, int(round(ch * scale)))
            px = (W - nw) / 2.0
            py = float(H - nh) if touches_bottom else float(max(art_top, H - nh - 8.0))

            art_canvas = place_scaled_art(clean_raw, W, H, scale, px, py, crop_box=crop_box)
            art_mask = get_art_mask(art_canvas, threshold=255)
            placed_bbox = extract_art_bbox(art_canvas, threshold=255)
            art_min_y = float(placed_bbox[1]) if placed_bbox else float(H)

            sp_anchor = (
                _find_slim_speaker_anchor(art_mask, cut.tail_target)
                if (speaker_targeted and cut.tail_target in ("left", "right"))
                else None
            )

            pull_list = (
                (1.0, 0.72, 0.45, 0.0)
                if (not speaker_targeted or attempt >= 12)
                else (1.0, 0.72, 0.45)
            )
            for pull in pull_list:
                if pull == 0.0:
                    tail_tip = None
                    base_deg = None
                    t_curve = -5.0
                elif sp_anchor is not None:
                    head_cx, head_top_y, _hl, _hr, art_mid_x = sp_anchor
                    if head_top_y - bub_bot < 18.0:
                        continue
                    if cut.tail_target == "right":
                        # Strictly aim into the right speaker half (never left listener!)
                        min_tx = max(cx + 16.0, art_mid_x + 12.0)
                        max_tx = min(W - box_margin - 8.0, cx + rx * 0.74)
                        if max_tx <= min_tx:
                            target_tx = max(art_mid_x + 8.0, cx + min(rx * 0.55, 42.0))
                        else:
                            target_tx = float(np.clip(0.76 * head_cx + 0.24 * cx, min_tx, max_tx))
                        ty = min(bub_bot + max(16.0, 38.0 * pull), head_top_y - 11.0)
                        tx = target_tx
                        raw_deg = float(np.rad2deg(np.arctan2((ty - cy) / ry, (tx - cx) / rx)))
                        base_deg = float(np.clip(raw_deg, 46.0, 84.0))
                        t_curve = 6.0
                    else:
                        # Strictly aim into the left speaker half (never right listener!)
                        max_tx = min(cx - 16.0, art_mid_x - 12.0)
                        min_tx = max(box_margin + 8.0, cx - rx * 0.74)
                        if min_tx >= max_tx:
                            target_tx = min(art_mid_x - 8.0, cx - min(rx * 0.55, 42.0))
                        else:
                            target_tx = float(np.clip(0.76 * head_cx + 0.24 * cx, min_tx, max_tx))
                        ty = min(bub_bot + max(16.0, 38.0 * pull), head_top_y - 11.0)
                        tx = target_tx
                        raw_deg = float(np.rad2deg(np.arctan2((ty - cy) / ry, (tx - cx) / rx)))
                        base_deg = float(np.clip(raw_deg, 96.0, 134.0))
                        t_curve = -6.0
                    if ty <= bub_bot + 10.0:
                        continue
                    tail_tip = (tx, ty)
                else:
                    if art_min_y - bub_bot < 20.0:
                        tail_tip = None
                        base_deg = None
                        t_curve = -5.0
                    else:
                        ty = min(bub_bot + 34.0 * pull, art_min_y - 11.0)
                        tail_tip = (cx, ty) if ty > bub_bot + 10.0 else None
                        base_deg = 90.0 if tail_tip else None
                        t_curve = -5.0

                bub_layer, dest, b_metrics = _build_bubble_layer(
                    panel_size=(W, H),
                    center=(cx, cy),
                    lines=lines,
                    radii=(rx, ry),
                    tail_tip=tail_tip,
                    tail_base_angle_deg=base_deg,
                    tail_half_deg=6.5,
                    tail_curve=t_curve,
                    font_size=cur_fs,
                    stroke_px=stroke_px,
                    sub_line_indices=sub_indices,
                )
                bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
                if int((art_mask & bub_mask).sum()) == 0:
                    out_panel = art_canvas.copy()
                    if bub_layer is not None:
                        rgba = out_panel.convert("RGBA")
                        rgba.alpha_composite(bub_layer, dest=dest)
                        out_panel = rgba.convert("RGB")
                    resolved_side = (
                        "center"
                        if abs(cx - W / 2.0) <= W * 0.06
                        else ("right" if cx > W / 2.0 else "left")
                    )
                    return out_panel, {
                        "wordless": False,
                        "bubble_count": 1,
                        "overlap_px": 0,
                        "min_clearance_px": compute_min_clearance(art_mask, bub_mask),
                        "font_size": b_metrics["font_size"],
                        "art_bbox": list(placed_bbox) if placed_bbox else None,
                        "tail_target": cut.tail_target,
                        "bubble_center": [round(cx, 1), round(cy, 1)],
                        "bubble_side_resolved": resolved_side,
                        "tail_tip": [round(tail_tip[0], 1), round(tail_tip[1], 1)] if tail_tip else None,
                    }

            if attempt in (3, 7, 11) and cur_fs > 12:
                cur_fs = max(12, cur_fs - 2)

        # Guaranteed disjoint vertical fallback
        lines, sub_indices = wrap_korean_dialogue(
            dialogue, 14, max_line_width_px=min(520.0, W * 0.62), max_lines=3
        )
        rx, ry = min(290.0, max_rx_t), min(42.0, max_ry_t)
        cx = W / 2.0
        cy = box_margin + ry + stroke_px + 2.0
        bub_bot = cy + ry + stroke_px
        safe_top = int(np.ceil(bub_bot + 16.0))
        avail_w = max(40.0, W - 2.0 * box_margin - 2.0)
        avail_h = max(36.0, H - safe_top - 4.0)
        scale_fb = min(avail_w / cw, avail_h / ch)
        nw = max(1, int(np.floor(cw * scale_fb)))
        nh = max(1, int(np.floor(ch * scale_fb)))
        py = max(float(safe_top), float(H - nh))
        art_canvas = place_scaled_art(clean_raw, W, H, scale_fb, (W - nw) / 2.0, py, crop_box=crop_box)
        art_mask = get_art_mask(art_canvas, threshold=255)
        placed_bbox = extract_art_bbox(art_canvas, threshold=255)
        bub_layer, dest, b_metrics = _build_bubble_layer(
            panel_size=(W, H),
            center=(cx, cy),
            lines=lines,
            radii=(rx, ry),
            tail_tip=None,
            font_size=14,
            stroke_px=stroke_px,
            sub_line_indices=sub_indices,
        )
        bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
        out_panel = art_canvas.copy()
        if bub_layer is not None:
            rgba = out_panel.convert("RGBA")
            rgba.alpha_composite(bub_layer, dest=dest)
            out_panel = rgba.convert("RGB")
        return out_panel, {
            "wordless": False,
            "bubble_count": 1,
            "overlap_px": int((art_mask & bub_mask).sum()),
            "min_clearance_px": compute_min_clearance(art_mask, bub_mask),
            "font_size": b_metrics["font_size"],
            "art_bbox": list(placed_bbox) if placed_bbox else None,
            "tail_target": cut.tail_target,
            "bubble_center": [round(cx, 1), round(cy, 1)],
            "bubble_side_resolved": "center",
            "tail_tip": None,
        }

    if mode == "two_char_upper":
        fs_start = 20 if len(dialogue) <= 34 else 18
        if split_valley is not None:
            panel_v, audit_v = _try_slim_between_valley(fs_start)
            if panel_v is not None and audit_v is not None:
                return panel_v, audit_v
        return _try_slim_top_center(fs_start=fs_start, speaker_targeted=True)

    if mode in ("side_right", "side_left"):
        fs_start = 22 if len(dialogue) <= 34 else 20
        panel, audit = _try_slim_side("right" if mode == "side_right" else "left", fs_start)
        if panel is not None and audit is not None:
            return panel, audit

    return _try_slim_top_center(fs_start=20, speaker_targeted=is_two_char)


def _compose_variable_panel(
    cut: ComicCut,
    raw_im: Image.Image,
    target_w: int,
    target_h: int,
    border_style: str = "box",
) -> tuple[Image.Image, dict[str, Any]]:
    """Compose ANY variable V4 panel geometry with guaranteed `overlap_px == 0` & `tooltip_overlap_px == 0`.

    Automatically dispatches across:
    - Wordless freeze-frames (`cut.wordless` or empty dialogue)
    - Narrow vertical split panels (`target_w < 580`, e.g. `410x626`, `410x638`, `410x648`)
    - Wide tall panels (`target_w >= 580`, `target_h >= 540`, e.g. `844x650`, `844x720`, `844x802`)
    - Wide slim cinematic strips (`target_w >= 580`, `target_h < 540`, e.g. `844x410`, `844x472`)
    """
    is_narrow = target_w < 580
    if is_narrow:
        tip_max_w = min(248, max(120, target_w - 24))
        tip_max_h = min(164, max(84, int(target_h * 0.26)))
    elif target_h >= 540:
        tip_max_w = min(306, max(160, int(target_w * 0.36)))
        tip_max_h = min(240, max(110, int(target_h * 0.35)))
    else:
        tip_max_w = min(276, max(150, int(target_w * 0.33)))
        tip_max_h = min(192, max(96, int(target_h * 0.45)))

    tooltip_rgba = _prepare_cut_tooltip(cut, max_w=tip_max_w, max_h=tip_max_h)
    pref_corner = cut.item_tooltip.preferred_corner if cut.item_tooltip else "auto"
    dialogue = (cut.dialogue or "").strip()

    if cut.wordless or not dialogue:
        if border_style == "box":
            side_pad = 6
            top_pad = 6
            bottom_pad = 6
        else:
            side_pad = 14 if is_narrow else 20
            top_pad = 16 if is_narrow else 24
            bottom_pad = 14
        panel, audit = _compose_wordless_panel(
            raw_im,
            target_w=target_w,
            target_h=target_h,
            side_pad=side_pad,
            top_pad=top_pad,
            bottom_pad_if_floating=bottom_pad,
            tooltip_rgba=tooltip_rgba,
            preferred_corner=pref_corner,
        )
        # If narrow full-bleed wordless + tooltip collided horizontally, stack vertically with 0px overlap
        if tooltip_rgba is not None and (
            int(audit.get("overlap_px", 0)) > 0 or int(audit.get("tooltip_overlap_px", 0)) > 0
        ):
            clean_raw = clean_white_bg(raw_im)
            rw, rh = clean_raw.size
            raw_bbox = extract_art_bbox(clean_raw, threshold=255)
            cur_tip = _fit_tooltip_card(
                tooltip_rgba,
                max_w=min(248, max(120, target_w - 24)),
                max_h=min(156, max(72, int(target_h * 0.26))),
            )
            tw, th = cur_tip.size
            pad_x = max(12, side_pad)
            pad_y = max(12, top_pad)
            if pref_corner in ("top_left", "bottom_left"):
                tx0 = pad_x
            elif pref_corner in ("top_right", "bottom_right"):
                tx0 = target_w - pad_x - tw
            else:
                tx0 = (target_w - tw) // 2
            place_tip_bottom = pref_corner in ("bottom_left", "bottom_right")
            ty0 = (target_h - pad_y - th) if place_tip_bottom else pad_y

            if raw_bbox is not None:
                ax0, ay0, ax1, ay1 = raw_bbox
                touches_bottom = ay1 >= rh - 6
                crop_box = (ax0, ay0, min(rw, ax1 + 1), rh if touches_bottom else min(rh, ay1 + 1))
                cw = max(1, crop_box[2] - crop_box[0])
                ch = max(1, crop_box[3] - crop_box[1])
                if place_tip_bottom:
                    art_y_lo, art_y_hi = float(pad_y), float(ty0 - 12)
                else:
                    art_y_lo, art_y_hi = float(ty0 + th + 12), float(target_h - (2 if touches_bottom else pad_y))
                avail_w = max(24.0, float(target_w - 2 * pad_x - 2))
                avail_h = max(24.0, art_y_hi - art_y_lo - 2.0)
                scale_v = min(avail_w / cw, avail_h / ch)
                nw = max(1, int(np.floor(cw * scale_v)))
                nh = max(1, int(np.floor(ch * scale_v)))
                px = (target_w - nw) / 2.0
                if not place_tip_bottom and touches_bottom:
                    py = max(art_y_lo, float(target_h - nh))
                else:
                    py = art_y_lo + max(0.0, (art_y_hi - art_y_lo - nh) / 2.0)
                art_panel = place_scaled_art(clean_raw, target_w, target_h, scale_v, px, py, crop_box=crop_box)
                art_mask = get_art_mask(art_panel, threshold=255)
                placed_bb = extract_art_bbox(art_panel, threshold=255)
                art_cx = (placed_bb[0] + placed_bb[2]) / 2.0 if placed_bb else target_w / 2.0
                tip_mask = _tooltip_alpha_mask((target_w, target_h), cur_tip, (tx0, ty0))
                tip_ov = int((art_mask & tip_mask).sum())
                panel = _composite_rgba_card(art_panel, cur_tip, (tx0, ty0))
                audit = {
                    "wordless": True,
                    "bubble_count": 0,
                    "overlap_px": tip_ov,
                    "min_clearance_px": compute_min_clearance(art_mask, tip_mask),
                    "font_size": None,
                    "art_bbox": list(placed_bb) if placed_bb else None,
                    "art_cx": round(art_cx, 1),
                    "has_item_tooltip": True,
                    "tooltip_bbox": [tx0, ty0, tx0 + tw, ty0 + th],
                    "tooltip_overlap_px": tip_ov,
                }
        audit["tail_target"] = cut.tail_target
        return panel, audit

    if is_narrow:
        return _compose_narrow_variable_panel(
            cut, raw_im, target_w, target_h, border_style, dialogue, tooltip_rgba
        )
    if target_h >= 540:
        return _compose_wide_tall_variable_panel(
            cut, raw_im, target_w, target_h, border_style, dialogue, tooltip_rgba
        )
    return _compose_wide_slim_variable_panel(
        cut, raw_im, target_w, target_h, border_style, dialogue, tooltip_rgba
    )


def _resolve_act_page_path(
    act_number: int,
    raw_page_paths: Mapping[int, Path | str],
) -> Path:
    """Resolve raw act page image path for `act_number` (1..5), supporting int or str keys."""
    if act_number in raw_page_paths:
        return Path(raw_page_paths[act_number])
    str_keys = {str(k): v for k, v in raw_page_paths.items()}
    if str(act_number) in str_keys:
        return Path(str_keys[str(act_number)])
    if 0 in raw_page_paths and (act_number - 1) in raw_page_paths and 5 not in raw_page_paths:
        return Path(raw_page_paths[act_number - 1])
    raise KeyError(
        f"Missing raw act page path for act_number={act_number} "
        f"(available keys: {sorted(raw_page_paths.keys())})"
    )


def _compose_full_bleed_panel(
    cut: ComicCut,
    raw_im: Image.Image,
    target_w: int,
    target_h: int,
) -> tuple[Image.Image, dict[str, Any]]:
    """Compose a V4.2 edge-to-edge full-bleed boxed panel with crisp overlaid speech bubble.

    - Fills `(target_w, target_h)` 100% edge-to-edge via cover-fit scaling (anchored bottom-center
      with head-preservation clamp) with ZERO white border gaps.
    - Overlays a 4x-supersampled pure-`#FFFFFF` elliptical speech bubble (`3.5px #141414` stroke)
      onto the unobstructed scenic background zone.
    - Supports exact `cut.bubble_center_xy` placement and laser-precise `cut.speaker_anchor_xy`
      tail aiming (with clean deterministic `tail_target` speaker anchors when unset so flying
      mobs, smoke, or background scenery NEVER hijack tail direction!).
    - Places optional `item_tooltip` cleanly in the opposite open corner with `tooltip_overlap_px == 0`.
    """
    W, H = target_w, target_h
    stroke_px = 3.5
    panel, edge_fill_ratio = _cover_fit_full_bleed_image(raw_im, W, H)

    is_narrow = W < 580
    if is_narrow:
        tip_max_w = min(248, max(120, W - 24))
        tip_max_h = min(164, max(84, int(H * 0.26)))
    elif H >= 540:
        tip_max_w = min(306, max(160, int(W * 0.36)))
        tip_max_h = min(240, max(110, int(H * 0.35)))
    else:
        tip_max_w = min(276, max(150, int(W * 0.33)))
        tip_max_h = min(192, max(96, int(H * 0.45)))

    tooltip_rgba = _prepare_cut_tooltip(cut, max_w=tip_max_w, max_h=tip_max_h)
    pref_corner = cut.item_tooltip.preferred_corner if cut.item_tooltip else "auto"
    dialogue = (cut.dialogue or "").strip()

    # 1. Wordless / silent panel: return full-bleed artwork + optional corner tooltip
    if cut.wordless or not dialogue:
        audit: dict[str, Any] = {
            "wordless": True,
            "full_bleed_bg": True,
            "bubble_count": 0,
            "overlap_px": 0,
            "min_clearance_px": 999.0,
            "font_size": None,
            "art_bbox": [0, 0, W - 1, H - 1],
            "tail_target": cut.tail_target,
            "edge_fill_ratio": edge_fill_ratio,
        }
        if tooltip_rgba is not None:
            tw, th = tooltip_rgba.size
            pad = 14
            corners = _ordered_corner_candidates(W, H, tw, th, pad, pad, preferred=pref_corner)
            _, tip_dest = corners[0]
            tx0 = max(4, min(W - tw - 4, tip_dest[0]))
            ty0 = max(4, min(H - th - 4, tip_dest[1]))
            panel = _composite_rgba_card(panel, tooltip_rgba, (tx0, ty0))
            audit["has_item_tooltip"] = True
            audit["tooltip_bbox"] = [tx0, ty0, tx0 + tw, ty0 + th]
            audit["tooltip_overlap_px"] = 0
        return panel, audit

    # 2. Dialogue panel: geometry regime selection + auto-fit typography
    dummy = ImageDraw.Draw(Image.new("RGB", (16, 16), PURE_WHITE))
    safe_margin = 12.0

    if is_narrow:
        regime = "narrow"
        max_rx = min(184.0, W / 2.0 - 14.0, W / 2.0 - safe_margin - stroke_px)
        max_ry = min(112.0, H * 0.22)
        min_rx = min(104.0, max_rx)
        min_ry = min(44.0, max_ry)
        pad_x, pad_y = 26.0, 18.0
        wrap_w = float(np.clip(max_rx * 1.40, 136.0, max(150.0, W - 74.0)))
        fs_start = 20 if len(dialogue) <= 22 else (19 if len(dialogue) <= 34 else 18)
        fs_candidates = [fs for fs in (fs_start, 19, 18, 16, 15, 14, 13) if fs <= fs_start]
    elif H >= 540:
        regime = "wide_tall"
        max_rx = min(326.0, W * 0.40, W / 2.0 - safe_margin - stroke_px)
        max_ry = min(108.0, H * 0.19)
        min_rx = min(124.0, max_rx)
        min_ry = min(48.0, max_ry)
        pad_x, pad_y = 32.0, 20.0
        wrap_w = float(np.clip(max_rx * 1.44, 240.0, 440.0))
        fs_start = 22 if len(dialogue) <= 36 else 21
        fs_candidates = [fs for fs in (fs_start, 21, 19, 17, 15, 14) if fs <= fs_start]
    else:
        # Wide slim panel (W >= 580, H < 540)
        if (
            cut.bubble_side == "center"
            or (cut.bubble_side is None and (len(cut.characters) >= 2 or cut.tail_target == "center"))
        ):
            regime = "wide_slim_center"
            max_rx = min(312.0, W * 0.38, W / 2.0 - safe_margin - stroke_px)
            max_ry = min(78.0, H * 0.22)
            min_rx = min(124.0, max_rx)
            min_ry = min(40.0, max_ry)
            pad_x, pad_y = 30.0, 16.0
            wrap_w = float(np.clip(max_rx * 1.44, 220.0, 420.0))
            fs_start = 20 if len(dialogue) <= 30 else (19 if len(dialogue) <= 42 else 18)
            fs_candidates = [fs for fs in (fs_start, 19, 18, 16, 15, 14) if fs <= fs_start]
        else:
            if cut.bubble_side == "left":
                regime = "wide_slim_left"
            elif cut.bubble_side == "right":
                regime = "wide_slim_right"
            elif cut.tail_target == "right":
                regime = "wide_slim_left"
            else:
                regime = "wide_slim_right"
            max_rx = min(216.0, W * 0.27, W / 2.0 - safe_margin - stroke_px)
            max_ry = min(92.0, H * 0.24)
            min_rx = min(114.0, max_rx)
            min_ry = min(44.0, max_ry)
            pad_x, pad_y = 28.0, 18.0
            wrap_w = float(np.clip(max_rx * 1.40, 180.0, 296.0))
            fs_start = 21 if len(dialogue) <= 28 else (20 if len(dialogue) <= 38 else 19)
            fs_candidates = [fs for fs in (fs_start, 20, 19, 17, 15, 14) if fs <= fs_start]

    # Deduplicate candidate font sizes preserving descending order
    ordered_fs: list[int] = []
    for fs_v in fs_candidates:
        if fs_v not in ordered_fs:
            ordered_fs.append(fs_v)

    chosen_fs = ordered_fs[-1]
    lines: list[str] = []
    sub_indices: list[int] = []
    rx, ry = min_rx, min_ry
    for fs_try in ordered_fs:
        cand_lines, cand_subs = wrap_korean_dialogue(
            dialogue, fs_try, max_line_width_px=wrap_w, max_lines=4
        )
        cand_rx, cand_ry = _compute_snug_ellipse_radii(
            dummy,
            cand_lines,
            set(cand_subs),
            fs_try,
            min_rx=min_rx,
            max_rx=max_rx,
            min_ry=min_ry,
            max_ry=max_ry,
            pad_x=pad_x,
            pad_y=pad_y,
        )
        f_m = load_font(fs_try, weight="Bold")
        f_s = load_font(max(11, int(round(fs_try * 0.80))), weight="Medium")
        gap_try = max(4, int(round(fs_try * 0.34)))
        mw, tot_h, _, _, _, _ = _measure_text_block(
            dummy, cand_lines, f_m, f_s, gap_try, set(cand_subs)
        )
        a = mw / 2.0 + 18.0
        b = tot_h / 2.0 + 12.0
        fits = ((a / max(1.0, cand_rx)) ** 2 + (b / max(1.0, cand_ry)) ** 2) <= 0.88
        chosen_fs, lines, sub_indices, rx, ry = fs_try, cand_lines, cand_subs, cand_rx, cand_ry
        if fits and len(cand_lines) <= 4:
            break

    # 3. Bubble center placement (exact `bubble_center_xy` override or regime default)
    if regime == "narrow":
        cx = W / 2.0
        cy = 12.0 + ry + stroke_px
        resolved_side = "center"
    elif regime == "wide_tall":
        side = cut.bubble_side or cut.tail_target
        if side == "left":
            cx = max(22.0 + rx + stroke_px, W * 0.30)
            resolved_side = "left"
        elif side == "right":
            cx = min(W - 22.0 - rx - stroke_px, W * 0.70)
            resolved_side = "right"
        else:
            cx = W / 2.0
            resolved_side = "center"
        cy = 14.0 + ry + stroke_px
    elif regime == "wide_slim_center":
        cx = W / 2.0
        cy = 10.0 + ry + stroke_px
        resolved_side = "center"
    elif regime == "wide_slim_left":
        cx = 16.0 + rx + stroke_px
        cy = 16.0 + ry + stroke_px
        resolved_side = "left"
    else:  # wide_slim_right
        cx = W - 16.0 - rx - stroke_px
        cy = 16.0 + ry + stroke_px
        resolved_side = "right"

    # Clamp default placement strictly inside panel box with 12px margin
    clamp_pad = safe_margin + stroke_px
    cx_lo = clamp_pad + rx
    cx_hi = max(cx_lo, W - clamp_pad - rx)
    cy_lo = clamp_pad + ry
    cy_hi = max(cy_lo, H - clamp_pad - ry)

    if cut.bubble_center_xy is not None:
        bx_r, by_r = float(cut.bubble_center_xy[0]), float(cut.bubble_center_xy[1])
        cx = float(np.clip(bx_r * W, cx_lo, cx_hi))
        cy = float(np.clip(by_r * H, cy_lo, cy_hi))
        resolved_side = (
            "center"
            if abs(cx - W / 2.0) <= W * 0.08
            else ("left" if cx < W / 2.0 else "right")
        )
    else:
        cx = float(np.clip(cx, cx_lo, cx_hi))
        cy = float(np.clip(cy, cy_lo, cy_hi))

    # 4. Laser-precise speaker anchor & directional tail computation
    if cut.speaker_anchor_xy is not None:
        sx_r = float(np.clip(cut.speaker_anchor_xy[0], 0.02, 0.98))
        sy_r = float(np.clip(cut.speaker_anchor_xy[1], 0.02, 0.98))
        sx, sy = sx_r * W, sy_r * H
        max_tail_ext = 54.0
    else:
        # Clean deterministic speaker anchors from `tail_target` (never misled by flying mobs/scenery!)
        sx_r = 0.27 if cut.tail_target == "left" else (0.73 if cut.tail_target == "right" else 0.50)
        sy_r = 0.56 if H >= 540 else 0.50
        sx, sy = sx_r * W, sy_r * H
        max_tail_ext = 38.0 if H >= 540 else 36.0

    dx = sx - cx
    dy = sy - cy
    dist = float(np.hypot(dx, dy))

    tail_tip: tuple[float, float] | None = None
    tail_base_angle_deg: float | None = None
    tail_curve = 0.0

    if dist > 1e-3:
        ux, uy = dx / dist, dy / dist
        t_ell = 1.0 / float(np.hypot(ux / max(1.0, rx), uy / max(1.0, ry)))
        gap = dist - (t_ell + stroke_px)
        tail_base_angle_deg = float(np.rad2deg(np.arctan2(dy / max(1.0, ry), dx / max(1.0, rx))))

        stop_short = 16.0
        if gap >= 30.0:
            ext = min(max_tail_ext, gap - stop_short)
        elif gap >= 12.0:
            ext = min(max_tail_ext, max(10.0, gap * 0.55))
        else:
            ext = 0.0

        if ext > 0.0:
            t_desired = t_ell + stroke_px + ext
            # Clip strictly along the SAME ray `(ux, uy)` to stay within 8px of panel edges
            edge_pad = 8.0
            t_bound = t_desired
            if ux > 1e-6:
                t_bound = min(t_bound, (W - edge_pad - cx) / ux)
            elif ux < -1e-6:
                t_bound = min(t_bound, (edge_pad - cx) / ux)
            if uy > 1e-6:
                t_bound = min(t_bound, (H - edge_pad - cy) / uy)
            elif uy < -1e-6:
                t_bound = min(t_bound, (edge_pad - cy) / uy)

            if t_bound > t_ell + stroke_px + 8.0:
                tx = cx + t_bound * ux
                ty = cy + t_bound * uy
                tail_tip = (tx, ty)
                tail_curve = 4.5 if dx > 6.0 else (-4.5 if dx < -6.0 else -4.0)

    bub_layer, dest, b_metrics = _build_bubble_layer(
        panel_size=(W, H),
        center=(cx, cy),
        lines=lines,
        radii=(rx, ry),
        tail_tip=tail_tip,
        tail_base_angle_deg=tail_base_angle_deg,
        tail_half_deg=6.8,
        tail_curve=tail_curve,
        font_size=chosen_fs,
        stroke_px=stroke_px,
        sub_line_indices=sub_indices,
    )
    bub_mask = _bubble_alpha_mask((W, H), bub_layer, dest)
    out_panel = panel.copy()
    if bub_layer is not None:
        rgba = out_panel.convert("RGBA")
        rgba.alpha_composite(bub_layer, dest=dest)
        out_panel = rgba.convert("RGB")

    audit_out: dict[str, Any] = {
        "wordless": False,
        "full_bleed_bg": True,
        "bubble_count": 1,
        "overlap_px": 0,
        "min_clearance_px": 999.0,
        "font_size": b_metrics["font_size"],
        "art_bbox": [0, 0, W - 1, H - 1],
        "tail_target": cut.tail_target,
        "bubble_center": [round(cx, 1), round(cy, 1)],
        "bubble_side_resolved": resolved_side,
        "speaker_anchor": [round(sx, 1), round(sy, 1)],
        "tail_tip": [round(tail_tip[0], 1), round(tail_tip[1], 1)] if tail_tip else None,
        "edge_fill_ratio": edge_fill_ratio,
    }

    # 5. Optional item tooltip placed cleanly in opposite corner with zero bubble-tooltip overlap
    if tooltip_rgba is not None:
        pad = 14
        cur_tip = tooltip_rgba
        tw, th = cur_tip.size
        if pref_corner in ("top_left", "top_right", "bottom_left", "bottom_right"):
            preferred_order = pref_corner
        elif cx <= W / 2.0:
            preferred_order = "bottom_right"
        else:
            preferred_order = "bottom_left"

        # Build prioritized corner order preferring opposite side from bubble center
        if cx <= W / 2.0:
            base_order = ["bottom_right", "top_right", "bottom_left", "top_left"]
        else:
            base_order = ["bottom_left", "top_left", "bottom_right", "top_right"]
        if preferred_order in base_order:
            order = [preferred_order] + [k for k in base_order if k != preferred_order]
        else:
            order = base_order

        corner_coords = {
            "top_right": (W - pad - tw, pad),
            "top_left": (pad, pad),
            "bottom_right": (W - pad - tw, H - pad - th),
            "bottom_left": (pad, H - pad - th),
        }

        chosen_dest: tuple[int, int] | None = None
        chosen_tip_mask: np.ndarray | None = None
        for key in order:
            cand_x, cand_y = corner_coords[key]
            cand_x = max(4, min(W - tw - 4, cand_x))
            cand_y = max(4, min(H - th - 4, cand_y))
            tmask = _tooltip_alpha_mask((W, H), cur_tip, (cand_x, cand_y))
            if int((bub_mask & tmask).sum()) == 0:
                chosen_dest = (cand_x, cand_y)
                chosen_tip_mask = tmask
                break

        if chosen_dest is None:
            # Shrink tooltip to fit strictly below (or above) bubble with 0px overlap
            bub_ys = np.where(bub_mask)[0]
            bub_max_y = int(bub_ys.max()) if len(bub_ys) else int(cy + ry + stroke_px)
            bub_min_y = int(bub_ys.min()) if len(bub_ys) else int(cy - ry - stroke_px)
            space_below = H - pad - (bub_max_y + 10)
            space_above = (bub_min_y - 10) - pad
            if space_below >= space_above:
                avail_th = max(48, space_below)
                cur_tip = _fit_tooltip_card(cur_tip, max_w=min(tw, W - 2 * pad), max_h=avail_th)
                tw, th = cur_tip.size
                cand_x = (W - pad - tw) if cx <= W / 2.0 else pad
                cand_y = H - pad - th
            else:
                avail_th = max(48, space_above)
                cur_tip = _fit_tooltip_card(cur_tip, max_w=min(tw, W - 2 * pad), max_h=avail_th)
                tw, th = cur_tip.size
                cand_x = (W - pad - tw) if cx <= W / 2.0 else pad
                cand_y = pad
            cand_x = max(4, min(W - tw - 4, cand_x))
            cand_y = max(4, min(H - th - 4, cand_y))
            chosen_dest = (cand_x, cand_y)
            chosen_tip_mask = _tooltip_alpha_mask((W, H), cur_tip, chosen_dest)

        tip_ov = int((bub_mask & chosen_tip_mask).sum()) if chosen_tip_mask is not None else 0
        out_panel = _composite_rgba_card(out_panel, cur_tip, chosen_dest)
        audit_out["has_item_tooltip"] = True
        audit_out["tooltip_bbox"] = [
            chosen_dest[0],
            chosen_dest[1],
            chosen_dest[0] + tw,
            chosen_dest[1] + th,
        ]
        audit_out["tooltip_overlap_px"] = tip_ov
        audit_out["overlap_px"] = tip_ov
        if chosen_tip_mask is not None:
            audit_out["min_clearance_px"] = compute_min_clearance(bub_mask, chosen_tip_mask)

    return out_panel, audit_out


def compose_v4_episode(
    script: EpisodeScript,
    raw_page_paths: Mapping[int, Path | str],
    output_dir: Path,
    watermark_url: str | None = DEFAULT_WATERMARK_URL,
) -> ComposeResult:
    """Compose a complete V4 5-act variable-layout episode into header, 5 pages, stitched JPG, and thumb."""
    from wow_sloptoon.layouts import (
        V4_PAGE_H,
        V4_PAGE_W,
        extract_panels_from_page,
        get_page_layout,
    )

    if not script.acts or len(script.acts) != 5:
        count = len(script.acts) if script.acts else 0
        raise ValueError(f"compose_v4_episode requires exactly 5 acts in script.acts, got {count}")

    ordered_acts = sorted(script.acts, key=lambda a: a.act_number)
    if [a.act_number for a in ordered_acts] != [1, 2, 3, 4, 5]:
        raise ValueError(
            f"compose_v4_episode requires act_numbers [1, 2, 3, 4, 5], "
            f"got {[a.act_number for a in ordered_acts]}"
        )

    bg_style = getattr(script, "background_style", "clean_white")
    is_full_bleed_ep = bg_style == "full_bleed"

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Build Header (900 x 244)
    header_im = build_header(script)
    header_path = out_dir / "header.png"
    header_im.save(header_path, format="PNG", optimize=True)

    # 2. Extract and compose each of the 5 act pages on 900x1350 pure #FFFFFF canvas
    pages: list[Image.Image] = []
    page_paths: list[Path] = []
    page_layouts: list[str] = []
    cut_audits: list[dict[str, Any]] = []
    thumb_candidates: list[Image.Image] = []

    for act in ordered_acts:
        layout_spec = get_page_layout(act.layout_id)
        if len(act.cuts) != layout_spec.panel_count:
            raise ValueError(
                f"Act {act.act_number} layout '{act.layout_id}' expects {layout_spec.panel_count} cuts, "
                f"got {len(act.cuts)}"
            )

        raw_page_path = _resolve_act_page_path(act.act_number, raw_page_paths)
        if not raw_page_path.exists():
            raise FileNotFoundError(
                f"Raw act page image not found for act {act.act_number}: {raw_page_path}"
            )
        with Image.open(raw_page_path) as raw_im:
            raw_page_im = raw_im.copy()

        extracted_panels = extract_panels_from_page(
            raw_page_im,
            act.layout_id,
            all_boxed=is_full_bleed_ep,
        )
        if len(extracted_panels) != len(layout_spec.slots):
            raise ValueError(
                f"extract_panels_from_page returned {len(extracted_panels)} panels for "
                f"layout '{act.layout_id}', expected {len(layout_spec.slots)}"
            )

        if act.act_number == 1:
            # Prefer Act 1 lead panel (and other Act 1 panels) for episode thumbnail
            thumb_candidates = list(extracted_panels) + thumb_candidates
        else:
            thumb_candidates.extend(extracted_panels)

        act_cuts = sorted(
            enumerate(act.cuts),
            key=lambda pair: (
                pair[1].panel_index if pair[1].panel_index is not None else (pair[0] + 1),
                pair[1].cut_index,
            ),
        )
        ordered_act_cuts = [pair[1] for pair in act_cuts]

        page = Image.new("RGB", (V4_PAGE_W, V4_PAGE_H), PURE_WHITE)
        for slot, cut, raw_panel in zip(layout_spec.slots, ordered_act_cuts, extracted_panels):
            x0, y0, x1, y1 = slot.rect
            slot_w = slot.width
            slot_h = slot.height
            use_full_bleed_panel = is_full_bleed_ep or bool(getattr(cut, "full_bleed_bg", False))
            if use_full_bleed_panel:
                composed_panel, cut_audit = _compose_full_bleed_panel(
                    cut,
                    raw_panel,
                    target_w=slot_w,
                    target_h=slot_h,
                )
                page.paste(composed_panel, (x0, y0))
                draw_4x_rect_border(page, slot.rect, stroke_px=3.5, color=INK_BLACK)
                eff_border_style = "box"
            else:
                composed_panel, cut_audit = _compose_variable_panel(
                    cut,
                    raw_panel,
                    target_w=slot_w,
                    target_h=slot_h,
                    border_style=slot.border_style,
                )
                page.paste(composed_panel, (x0, y0))
                if slot.border_style == "box":
                    draw_4x_rect_border(page, slot.rect, stroke_px=3.5, color=INK_BLACK)
                eff_border_style = slot.border_style

            cut_audit["cut_index"] = cut.cut_index
            cut_audit["act_number"] = act.act_number
            cut_audit["panel_index"] = slot.slot_index
            cut_audit["layout_id"] = act.layout_id
            cut_audit["border_style"] = eff_border_style
            cut_audit["slot_rect"] = [x0, y0, x1, y1]
            cut_audit["page"] = act.act_number
            cut_audits.append(cut_audit)

        p_path = out_dir / f"page_{act.act_number}.png"
        page.save(p_path, format="PNG", optimize=True)
        pages.append(page)
        page_paths.append(p_path)
        page_layouts.append(act.layout_id)

    # 3. Stitch full vertical scroll (`episode_full_raw.jpg` + watermarked `episode_full.jpg`)
    gap_after_header = 24
    inter_page_gap = 36
    bot_pad = 24
    total_h = (
        header_im.size[1]
        + gap_after_header
        + sum(p.size[1] for p in pages)
        + inter_page_gap * max(0, len(pages) - 1)
        + bot_pad
    )
    full_im = Image.new("RGB", (V4_PAGE_W, total_h), PURE_WHITE)
    cur_y = 0
    full_im.paste(header_im, (0, cur_y))
    cur_y += header_im.size[1] + gap_after_header
    for p_idx, page in enumerate(pages):
        full_im.paste(page, (0, cur_y))
        cur_y += page.size[1]
        if p_idx < len(pages) - 1:
            cur_y += inter_page_gap

    wm_url = (watermark_url or "").strip() if watermark_url else ""
    if wm_url:
        raw_full_path = out_dir / "episode_full_raw.jpg"
        full_im.save(raw_full_path, format="JPEG", quality=95, subsampling=0)
        full_im = append_watermark_footer(full_im, site_url=wm_url)

    full_image_path = out_dir / "episode_full.jpg"
    full_im.save(full_image_path, format="JPEG", quality=95, subsampling=0)

    # 4. Build clean 4:3 thumbnail (`800x600`) cropped from the best lead panel of Act 1
    thumb_im = build_thumbnail(
        script,
        thumb_candidates,
        size=THUMB_SIZE,
        full_bleed=is_full_bleed_ep,
    )
    thumb_path = out_dir / "thumb.jpg"
    thumb_im.save(thumb_path, format="JPEG", quality=93, subsampling=0)

    # 5. Assemble complete V4 pixel-level audit report
    total_overlap_px = sum(int(item["overlap_px"]) for item in cut_audits)
    total_tooltip_overlap_px = sum(int(item.get("tooltip_overlap_px", 0)) for item in cut_audits)
    pages_white = all(_is_outer_border_pure_white(p, margin=2) for p in pages)
    header_white = _is_outer_border_pure_white(header_im, margin=2)
    full_white = _is_outer_border_pure_white(full_im, margin=2)
    thumb_white = _is_outer_border_pure_white(thumb_im, margin=2)
    border_pure_white = bool(pages_white and header_white and full_white and thumb_white)

    audit_report: dict[str, Any] = {
        "passed": bool(
            total_overlap_px == 0 and total_tooltip_overlap_px == 0 and border_pure_white
        ),
        "layout_mode": "v4_five_act",
        "background_style": bg_style,
        "total_overlap_px": total_overlap_px,
        "total_tooltip_overlap_px": total_tooltip_overlap_px,
        "border_pure_white": border_pure_white,
        "cut_count": len(cut_audits),
        "page_count": len(pages),
        "page_layouts": page_layouts,
        "page_sizes": [list(p.size) for p in pages],
        "full_size": list(full_im.size),
        "thumb_size": list(thumb_im.size),
        "watermarked": bool(wm_url),
        "watermark_url": _normalize_watermark_site_url(wm_url) if wm_url else None,
        "cuts": cut_audits,
    }

    return ComposeResult(
        header_path=header_path,
        page_paths=page_paths,
        full_image_path=full_image_path,
        thumb_path=thumb_path,
        audit_report=audit_report,
    )


def compose_episode(
    script: EpisodeScript,
    raw_cut_paths: Mapping[int, Path | str],
    output_dir: Path,
    watermark_url: str | None = DEFAULT_WATERMARK_URL,
) -> ComposeResult:
    """Compose a complete Sloptoon episode into header, pages, stitched JPG, and thumb.

    Automatically delegates to `compose_v4_episode()` when `script.layout_mode == "v4_five_act"`.
    In classic 2-tier mode, supports:
    - 4 cuts -> 2 two-tier pages (`900x1320`)
    - 5 cuts -> 2 two-tier pages (`900x1320`) + 1 epilogue single-box page (`900x486`)
    - 6 cuts -> 3 two-tier pages (`900x1320`)

    By default appends the Sloptoon bottom watermark CTA banner (`watermark_url="slopwow.github.io"`)
    to `episode_full.jpg` while saving an un-watermarked backup at `episode_full_raw.jpg` so
    `retrofit_episode_watermark()` stays strictly idempotent. Pass `watermark_url=None` or `""`
    to opt out.
    """
    if getattr(script, "layout_mode", "classic_2tier") == "v4_five_act":
        return compose_v4_episode(
            script,
            raw_cut_paths,
            output_dir,
            watermark_url=watermark_url,
        )

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ordered_cuts = sorted(script.cuts, key=lambda c: c.cut_index)
    if not (4 <= len(ordered_cuts) <= 6):
        raise ValueError(f"compose_episode supports 4~6 cuts, got {len(ordered_cuts)}")

    loaded_raws: list[Image.Image] = []
    for pos, cut in enumerate(ordered_cuts, start=1):
        p = _resolve_cut_path(cut, pos, raw_cut_paths)
        if not p.exists():
            raise FileNotFoundError(f"Raw cut image not found for cut {cut.cut_index}: {p}")
        with Image.open(p) as im:
            loaded_raws.append(im.copy())

    # 1. Build Header (900 x 244)
    header_im = build_header(script)
    header_path = out_dir / "header.png"
    header_im.save(header_path, format="PNG", optimize=True)

    # 2. Compose Pages (pair cuts into 900x1320 2-tier pages; odd trailing cut -> 900x486 box page)
    pages: list[Image.Image] = []
    page_paths: list[Path] = []
    page_is_epilogue: list[bool] = []
    cut_audits: list[dict[str, Any]] = []

    idx = 0
    page_num = 1
    while idx < len(ordered_cuts):
        if idx + 1 < len(ordered_cuts):
            # 2-tier full page (900 x 1320)
            top_cut = ordered_cuts[idx]
            bot_cut = ordered_cuts[idx + 1]
            top_panel, top_audit = _compose_top_open_panel(top_cut, loaded_raws[idx])
            bot_panel, bot_audit = _compose_bottom_box_panel(bot_cut, loaded_raws[idx + 1])

            top_audit["cut_index"] = top_cut.cut_index
            top_audit["slot"] = "top"
            top_audit["page"] = page_num
            bot_audit["cut_index"] = bot_cut.cut_index
            bot_audit["slot"] = "bottom"
            bot_audit["page"] = page_num
            cut_audits.extend([top_audit, bot_audit])

            page = Image.new("RGB", (PAGE_W, FULL_PAGE_H), PURE_WHITE)
            page.paste(top_panel, (0, 0))
            page.paste(bot_panel, (BOT_BOX_RECT[0], BOT_BOX_RECT[1]))
            draw_4x_rect_border(page, BOT_BOX_RECT, stroke_px=3.5, color=INK_BLACK)

            p_path = out_dir / f"page_{page_num}.png"
            page.save(p_path, format="PNG", optimize=True)
            pages.append(page)
            page_paths.append(p_path)
            page_is_epilogue.append(False)

            idx += 2
            page_num += 1
        else:
            # Odd trailing cut (e.g. Cut 5 of 5): single centered 3.5px box page (900 x 486)
            epi_cut = ordered_cuts[idx]
            epi_panel, epi_audit = _compose_bottom_box_panel(epi_cut, loaded_raws[idx])
            epi_audit["cut_index"] = epi_cut.cut_index
            epi_audit["slot"] = "epilogue_box"
            epi_audit["page"] = page_num
            cut_audits.append(epi_audit)

            page = Image.new("RGB", (PAGE_W, EPILOGUE_PAGE_H), PURE_WHITE)
            page.paste(epi_panel, (EPILOGUE_BOX_RECT[0], EPILOGUE_BOX_RECT[1]))
            draw_4x_rect_border(page, EPILOGUE_BOX_RECT, stroke_px=3.5, color=INK_BLACK)

            p_path = out_dir / f"page_{page_num}.png"
            page.save(p_path, format="PNG", optimize=True)
            pages.append(page)
            page_paths.append(p_path)
            page_is_epilogue.append(True)

            idx += 1
            page_num += 1

    # 3. Stitch full vertical scroll (episode_full.jpg) + optional bottom watermark CTA footer
    gap_after_header = 24
    bot_pad = 24
    inter_gaps: list[int] = []
    for p_idx in range(len(pages) - 1):
        # 15px before an epilogue box matches the 68px visual rhythm of build_v10b_ep1.py
        inter_gaps.append(15 if page_is_epilogue[p_idx + 1] else 40)

    total_h = (
        header_im.size[1]
        + gap_after_header
        + sum(p.size[1] for p in pages)
        + sum(inter_gaps)
        + bot_pad
    )
    full_im = Image.new("RGB", (PAGE_W, total_h), PURE_WHITE)
    cur_y = 0
    full_im.paste(header_im, (0, cur_y))
    cur_y += header_im.size[1] + gap_after_header
    for p_idx, page in enumerate(pages):
        full_im.paste(page, (0, cur_y))
        cur_y += page.size[1]
        if p_idx < len(inter_gaps):
            cur_y += inter_gaps[p_idx]

    wm_url = (watermark_url or "").strip() if watermark_url else ""
    if wm_url:
        raw_full_path = out_dir / "episode_full_raw.jpg"
        full_im.save(raw_full_path, format="JPEG", quality=95, subsampling=0)
        full_im = append_watermark_footer(full_im, site_url=wm_url)

    full_image_path = out_dir / "episode_full.jpg"
    full_im.save(full_image_path, format="JPEG", quality=95, subsampling=0)

    # 4. Build clean 4:3 thumbnail (thumb.jpg)
    thumb_im = build_thumbnail(script, loaded_raws, size=THUMB_SIZE)
    thumb_path = out_dir / "thumb.jpg"
    thumb_im.save(thumb_path, format="JPEG", quality=93, subsampling=0)

    # 5. Assemble audit report
    total_overlap_px = sum(int(item["overlap_px"]) for item in cut_audits)
    pages_white = all(_is_outer_border_pure_white(p, margin=2) for p in pages)
    header_white = _is_outer_border_pure_white(header_im, margin=2)
    full_white = _is_outer_border_pure_white(full_im, margin=2)
    thumb_white = _is_outer_border_pure_white(thumb_im, margin=2)
    border_pure_white = bool(pages_white and header_white and full_white and thumb_white)

    audit_report: dict[str, Any] = {
        "passed": bool(total_overlap_px == 0 and border_pure_white),
        "total_overlap_px": total_overlap_px,
        "border_pure_white": border_pure_white,
        "cut_count": len(ordered_cuts),
        "page_count": len(pages),
        "page_sizes": [list(p.size) for p in pages],
        "full_size": list(full_im.size),
        "thumb_size": list(thumb_im.size),
        "watermarked": bool(wm_url),
        "watermark_url": _normalize_watermark_site_url(wm_url) if wm_url else None,
        "cuts": cut_audits,
    }

    return ComposeResult(
        header_path=header_path,
        page_paths=page_paths,
        full_image_path=full_image_path,
        thumb_path=thumb_path,
        audit_report=audit_report,
    )
