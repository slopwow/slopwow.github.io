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


def build_thumbnail(
    script: EpisodeScript,
    raw_images: Sequence[Image.Image],
    size: tuple[int, int] = THUMB_SIZE,
) -> Image.Image:
    """Create a clean 4:3 pure-white thumbnail (`800x600`) highlighting the lead cut artwork."""
    tw, th = size
    canvas = Image.new("RGB", (tw, th), PURE_WHITE)

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


def compose_episode(
    script: EpisodeScript,
    raw_cut_paths: dict[int, Path],
    output_dir: Path,
    watermark_url: str | None = DEFAULT_WATERMARK_URL,
) -> ComposeResult:
    """Compose a complete 4~6 cut Sloptoon episode into header, pages, stitched JPG, and thumb.

    Supports:
    - 4 cuts -> 2 two-tier pages (`900x1320`)
    - 5 cuts -> 2 two-tier pages (`900x1320`) + 1 epilogue single-box page (`900x486`)
    - 6 cuts -> 3 two-tier pages (`900x1320`)

    By default appends the Sloptoon bottom watermark CTA banner (`watermark_url="slopwow.github.io"`)
    to `episode_full.jpg` while saving an un-watermarked backup at `episode_full_raw.jpg` so
    `retrofit_episode_watermark()` stays strictly idempotent. Pass `watermark_url=None` or `""`
    to opt out.
    """
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
