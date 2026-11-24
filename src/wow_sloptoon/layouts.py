"""V4 5-act variable page-layout specs, clean blueprint renderer, and border-snapping panel extractor.

Defines 6 variable comic page layouts on a canonical `900x1350` (2:3) pure `#FFFFFF` canvas,
generates text-free structural blueprints for Gemini Nano Banana 2.1 page-batch illustration,
and extracts clean individual panel images with polarity-aware border snapping, residual
border stripping, and pure `#FFFFFF` background normalization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from PIL import Image, ImageDraw

V4_PAGE_W: int = 900
V4_PAGE_H: int = 1350
V4_ASPECT_RATIO: str = "2:3"

_PURE_WHITE: tuple[int, int, int] = (255, 255, 255)
_BOX_BORDER_COLOR: tuple[int, int, int] = (20, 20, 20)      # #141414 crisp box frame
_OPEN_GUIDE_COLOR: tuple[int, int, int] = (176, 176, 176)   # #B0B0B0 subtle open guide


@dataclass(frozen=True)
class PanelSlotSpec:
    """Geometry and composition metadata for one panel slot inside a 900x1350 V4 page."""

    slot_index: int
    rect: tuple[int, int, int, int]
    border_style: Literal["open", "box"]
    position_label: str
    bubble_hint: str

    @property
    def width(self) -> int:
        return self.rect[2] - self.rect[0]

    @property
    def height(self) -> int:
        return self.rect[3] - self.rect[1]

    @property
    def is_narrow(self) -> bool:
        return self.width < 580


@dataclass(frozen=True)
class PageLayoutSpec:
    """Definition of one variable V4 comic page layout on a 900x1350 (2:3) canvas."""

    layout_id: str
    description: str
    slots: tuple[PanelSlotSpec, ...]

    @property
    def panel_count(self) -> int:
        return len(self.slots)


PAGE_LAYOUTS: dict[str, PageLayoutSpec] = {
    "open_top_split_bottom": PageLayoutSpec(
        layout_id="open_top_split_bottom",
        description=(
            "Open wide establishing top half followed by two side-by-side narrow vertical reaction boxes "
            "(3 panels; ideal for Act 1 opening or quick two-beat punchline reactions)."
        ),
        slots=(
            PanelSlotSpec(
                slot_index=1,
                rect=(28, 20, 872, 650),
                border_style="open",
                position_label="TOP WIDE PANEL (full top half)",
                bubble_hint=(
                    "Borderless open wide top panel (844x630): place characters in the lower two-thirds "
                    "and reserve the top 32% as 100% pure #FFFFFF empty headroom for external speech bubbles."
                ),
            ),
            PanelSlotSpec(
                slot_index=2,
                rect=(28, 678, 438, 1326),
                border_style="box",
                position_label="BOTTOM-LEFT VERTICAL PANEL",
                bubble_hint=(
                    "Narrow vertical box (410x648): place character in the lower 60-64% and reserve "
                    "the top 36-40% as 100% pure #FFFFFF empty headroom for vertical speech bubble."
                ),
            ),
            PanelSlotSpec(
                slot_index=3,
                rect=(462, 678, 872, 1326),
                border_style="box",
                position_label="BOTTOM-RIGHT VERTICAL PANEL",
                bubble_hint=(
                    "Narrow vertical box (410x648): place character in the lower 60-64% and reserve "
                    "the top 36-40% as 100% pure #FFFFFF empty headroom for vertical speech bubble."
                ),
            ),
        ),
    ),
    "split_top_wide_bottom": PageLayoutSpec(
        layout_id="split_top_wide_bottom",
        description=(
            "Two side-by-side narrow vertical setup boxes on top leading into a wide payoff box below "
            "(3 panels; ideal for fast back-and-forth exchange into a dramatic group reveal)."
        ),
        slots=(
            PanelSlotSpec(
                slot_index=1,
                rect=(28, 24, 438, 650),
                border_style="box",
                position_label="TOP-LEFT VERTICAL PANEL",
                bubble_hint=(
                    "Narrow vertical box (410x626): place character in the lower 60-64% and reserve "
                    "the top 36-40% as 100% pure #FFFFFF empty headroom for vertical speech bubble."
                ),
            ),
            PanelSlotSpec(
                slot_index=2,
                rect=(462, 24, 872, 650),
                border_style="box",
                position_label="TOP-RIGHT VERTICAL PANEL",
                bubble_hint=(
                    "Narrow vertical box (410x626): place character in the lower 60-64% and reserve "
                    "the top 36-40% as 100% pure #FFFFFF empty headroom for vertical speech bubble."
                ),
            ),
            PanelSlotSpec(
                slot_index=3,
                rect=(28, 676, 872, 1326),
                border_style="box",
                position_label="BOTTOM WIDE PANEL (full bottom half)",
                bubble_hint=(
                    "Tall wide bottom box (844x650): place characters in the lower two-thirds and "
                    "reserve the top 32% as 100% pure #FFFFFF headroom for external speech bubbles."
                ),
            ),
        ),
    ),
    "diagonal_tempo_2cut": PageLayoutSpec(
        layout_id="diagonal_tempo_2cut",
        description=(
            "Generous borderless open top showcase over a punchy wide bottom response panel "
            "(2 panels; ideal for big physical slapstick action, crowd/mob reveals, or finale beats)."
        ),
        slots=(
            PanelSlotSpec(
                slot_index=1,
                rect=(28, 20, 872, 740),
                border_style="open",
                position_label="TOP LARGE OPEN PANEL",
                bubble_hint=(
                    "Large borderless open panel (844x720): dynamic diagonal/OTS staging in the lower "
                    "two-thirds with top 32% pure #FFFFFF empty headroom for external speech bubbles."
                ),
            ),
            PanelSlotSpec(
                slot_index=2,
                rect=(28, 768, 872, 1326),
                border_style="box",
                position_label="BOTTOM WIDE PANEL",
                bubble_hint=(
                    "Wide bottom box (844x558): place character(s) cleanly in the lower two-thirds or "
                    "non-bubble half with pure #FFFFFF headroom at top 32% or speaker-opposite upper corner."
                ),
            ),
        ),
    ),
    "impact_freeze_2cut": PageLayoutSpec(
        layout_id="impact_freeze_2cut",
        description=(
            "Crisp wide buildup panel above a massive climax/wordless shock freeze-frame panel "
            "(2 panels; signature Act 4 climax page)."
        ),
        slots=(
            PanelSlotSpec(
                slot_index=1,
                rect=(28, 24, 872, 496),
                border_style="box",
                position_label="TOP WIDE BUILDUP PANEL",
                bubble_hint=(
                    "Slim cinematic wide box (844x472): keep speaker clearly positioned to one side "
                    "with generous pure #FFFFFF space on the opposite upper half for speech bubble."
                ),
            ),
            PanelSlotSpec(
                slot_index=2,
                rect=(28, 524, 872, 1326),
                border_style="box",
                position_label="BOTTOM GIANT CLIMAX/FREEZE-FRAME PANEL",
                bubble_hint=(
                    "Giant climax box (844x802): ideal for a signature wordless shocked close-up filling "
                    "78-88% height; if dialogue is used, reserve top 32% pure #FFFFFF empty headroom."
                ),
            ),
        ),
    ),
    "wide_reaction_wide": PageLayoutSpec(
        layout_id="wide_reaction_wide",
        description=(
            "Three stacked cinematic widescreen strips for escalating tension, chases, or three-step escalation "
            "(3 panels)."
        ),
        slots=(
            PanelSlotSpec(
                slot_index=1,
                rect=(28, 24, 872, 464),
                border_style="box",
                position_label="TOP CINEMATIC WIDE PANEL",
                bubble_hint=(
                    "Cinematic wide strip (844x440): place character(s) on the speaker side and leave "
                    "generous pure #FFFFFF empty space on the opposite upper half for speech bubble."
                ),
            ),
            PanelSlotSpec(
                slot_index=2,
                rect=(28, 488, 872, 898),
                border_style="box",
                position_label="MIDDLE CINEMATIC WIDE PANEL",
                bubble_hint=(
                    "Cinematic wide strip (844x410): place character(s) on the speaker side and leave "
                    "generous pure #FFFFFF empty space on the opposite upper half for speech bubble."
                ),
            ),
            PanelSlotSpec(
                slot_index=3,
                rect=(28, 922, 872, 1326),
                border_style="box",
                position_label="BOTTOM CINEMATIC WIDE PANEL",
                bubble_hint=(
                    "Cinematic wide strip (844x404): place character(s) on the speaker side and leave "
                    "generous pure #FFFFFF empty space on the opposite upper half for speech bubble."
                ),
            ),
        ),
    ),
    "four_beat_gag": PageLayoutSpec(
        layout_id="four_beat_gag",
        description=(
            "Rapid-fire 2x2 four-beat comedic grid for quick dungeon chaos, loot-roll escalation, or slapstick "
            "(4 panels)."
        ),
        slots=(
            PanelSlotSpec(
                slot_index=1,
                rect=(28, 24, 438, 662),
                border_style="box",
                position_label="TOP-LEFT PANEL",
                bubble_hint=(
                    "Narrow vertical box (410x638): place character in the lower 60-64% and reserve "
                    "the top 36-40% as 100% pure #FFFFFF empty headroom for vertical speech bubble."
                ),
            ),
            PanelSlotSpec(
                slot_index=2,
                rect=(462, 24, 872, 662),
                border_style="box",
                position_label="TOP-RIGHT PANEL",
                bubble_hint=(
                    "Narrow vertical box (410x638): place character in the lower 60-64% and reserve "
                    "the top 36-40% as 100% pure #FFFFFF empty headroom for vertical speech bubble."
                ),
            ),
            PanelSlotSpec(
                slot_index=3,
                rect=(28, 688, 438, 1326),
                border_style="box",
                position_label="BOTTOM-LEFT PANEL",
                bubble_hint=(
                    "Narrow vertical box (410x638): place character in the lower 60-64% and reserve "
                    "the top 36-40% as 100% pure #FFFFFF empty headroom for vertical speech bubble."
                ),
            ),
            PanelSlotSpec(
                slot_index=4,
                rect=(462, 688, 872, 1326),
                border_style="box",
                position_label="BOTTOM-RIGHT PANEL",
                bubble_hint=(
                    "Narrow vertical box (410x638): place character in the lower 60-64% and reserve "
                    "the top 36-40% as 100% pure #FFFFFF empty headroom for vertical speech bubble."
                ),
            ),
        ),
    ),
}


def get_page_layout(layout_id: str) -> PageLayoutSpec:
    """Return the canonical `PageLayoutSpec` for `layout_id`, or raise `ValueError`."""
    key = (layout_id or "").strip()
    if key not in PAGE_LAYOUTS:
        allowed = ", ".join(PAGE_LAYOUTS.keys())
        raise ValueError(f"Unknown V4 page layout_id '{layout_id}'. Allowed layouts: {allowed}")
    return PAGE_LAYOUTS[key]


def render_layout_blueprint(
    layout_id: str,
    size: tuple[int, int] = (V4_PAGE_W, V4_PAGE_H),
) -> Image.Image:
    """Render a zero-text structural panel blueprint on a pure solid `#FFFFFF` canvas.

    Draws crisp 4px `#141414` rectangular frames for `box` slots and subtle 3px `#B0B0B0`
    guide rectangles for `open` slots with ZERO text, digits, or labels.
    """
    spec = get_page_layout(layout_id)
    w, h = int(size[0]), int(size[1])
    if w <= 0 or h <= 0:
        raise ValueError(f"Blueprint size must be positive, got {size}.")

    sx = w / float(V4_PAGE_W)
    sy = h / float(V4_PAGE_H)
    scale_stroke = min(sx, sy)

    img = Image.new("RGB", (w, h), _PURE_WHITE)
    draw = ImageDraw.Draw(img)

    for slot in spec.slots:
        x0 = int(round(slot.rect[0] * sx))
        y0 = int(round(slot.rect[1] * sy))
        x1 = int(round(slot.rect[2] * sx))
        y1 = int(round(slot.rect[3] * sy))

        if slot.border_style == "box":
            width = max(1, int(round(4 * scale_stroke)))
            draw.rectangle([x0, y0, x1, y1], outline=_BOX_BORDER_COLOR, width=width)
        else:
            width = max(1, int(round(3 * scale_stroke)))
            draw.rectangle([x0, y0, x1, y1], outline=_OPEN_GUIDE_COLOR, width=width)

    return img


# ---------------------------------------------------------------------------
# Panel extraction & pure-#FFFFFF normalization helpers
# ---------------------------------------------------------------------------

def _flatten_to_white_rgb(im: Image.Image) -> Image.Image:
    """Convert any PIL image mode to RGB by compositing transparency onto `#FFFFFF`."""
    if im.mode == "RGB":
        return im
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        rgba = im.convert("RGBA")
        bg = Image.new("RGB", rgba.size, _PURE_WHITE)
        bg.paste(rgba, mask=rgba.getchannel("A"))
        return bg
    return im.convert("RGB")


def _level_near_white_bg(
    im: Image.Image,
    low: float = 236.0,
    high: float = 245.0,
    chroma_max: float = 22.0,
) -> Image.Image:
    """Level near-white neutral background noise to strict `#FFFFFF` (255, 255, 255)."""
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


def _normalize_page_to_canvas(raw_page_im: Image.Image) -> Image.Image:
    """Normalize a raw page image to exact `(V4_PAGE_W, V4_PAGE_H)` on pure white."""
    rgb = _flatten_to_white_rgb(raw_page_im)
    sw, sh = rgb.size
    if sw == V4_PAGE_W and sh == V4_PAGE_H:
        return rgb

    target_aspect = V4_PAGE_W / float(V4_PAGE_H)
    src_aspect = sw / float(max(1, sh))
    if abs(src_aspect - target_aspect) / target_aspect <= 0.035:
        return rgb.resize((V4_PAGE_W, V4_PAGE_H), Image.Resampling.LANCZOS)

    scale = min(V4_PAGE_W / float(max(1, sw)), V4_PAGE_H / float(max(1, sh)))
    nw = max(1, int(round(sw * scale)))
    nh = max(1, int(round(sh * scale)))
    resized = rgb.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (V4_PAGE_W, V4_PAGE_H), _PURE_WHITE)
    ox = (V4_PAGE_W - nw) // 2
    oy = (V4_PAGE_H - nh) // 2
    canvas.paste(resized, (ox, oy))
    return canvas


def _find_contiguous_runs(
    indices: np.ndarray,
    max_thickness: int = 18,
) -> list[tuple[int, int]]:
    """Group sorted 1D indices into contiguous `(start, end)` inclusive runs."""
    if len(indices) == 0:
        return []
    runs: list[tuple[int, int]] = []
    start = int(indices[0])
    prev = start
    for raw_idx in indices[1:]:
        idx = int(raw_idx)
        if idx == prev + 1:
            prev = idx
        else:
            if (prev - start + 1) <= max_thickness:
                runs.append((start, prev))
            start = idx
            prev = idx
    if (prev - start + 1) <= max_thickness:
        runs.append((start, prev))
    return runs


def _detect_vertical_border(
    line_mask: np.ndarray,
    dark_mask: np.ndarray,
    expected_x: int,
    slot_rect: tuple[int, int, int, int],
    side: Literal["left", "right"],
    border_style: Literal["open", "box"],
    search_radius: int = 56,
    clamp_bounds: tuple[int, int] | None = None,
) -> tuple[int, int] | None:
    """Detect a vertical panel frame line near `expected_x` with corner-polarity disambiguation."""
    h, w = line_mask.shape
    _x0, y0, _x1, y1 = slot_rect

    wx0 = max(0, expected_x - search_radius)
    wx1 = min(w - 1, expected_x + search_radius)
    if clamp_bounds is not None:
        wx0 = max(wx0, clamp_bounds[0])
        wx1 = min(wx1, clamp_bounds[1])
    if wx1 <= wx0:
        return None

    # Sample strictly inside the vertical span so vertical drift still lies along the drawn wall
    span_h = max(1, y1 - y0)
    margin_y = min(52, max(12, span_h // 6))
    sy0 = max(0, y0 + margin_y)
    sy1 = min(h, y1 - margin_y)
    if sy1 - sy0 < 24:
        sy0, sy1 = max(0, y0), min(h, y1)

    col_density = line_mask[sy0:sy1, wx0 : wx1 + 1].mean(axis=0)
    col_dark_density = dark_mask[sy0:sy1, wx0 : wx1 + 1].mean(axis=0)
    hits = np.where(col_density >= 0.62)[0] + wx0
    runs = _find_contiguous_runs(hits, max_thickness=18)
    if not runs:
        return None

    perp_y_pad = max(48, min(148, span_h // 3))
    top_band = (max(0, y0 - perp_y_pad), min(h, y0 + perp_y_pad))
    bot_band = (max(0, y1 - perp_y_pad), min(h, y1 + perp_y_pad))

    def _has_perp_bar(x_start: int, x_end: int) -> int:
        if x_end - x_start < 6:
            return 0
        count = 0
        for by0, by1 in (top_band, bot_band):
            if by1 > by0:
                row_means = line_mask[by0:by1, x_start:x_end].mean(axis=1)
                if float(row_means.max()) >= 0.62:
                    count += 1
        return count

    best_run: tuple[int, int] | None = None
    best_score: tuple[float, ...] | None = None

    for c0, c1 in runs:
        # Check perpendicular horizontal bars extending left vs right (skip 4px for rounded corners)
        has_left = _has_perp_bar(max(0, c0 - 30), max(0, c0 - 4))
        has_right = _has_perp_bar(min(w, c1 + 5), min(w, c1 + 31))

        want_in = has_right if side == "left" else has_left
        want_out = has_left if side == "left" else has_right

        # Reject borders that unambiguously belong to the adjacent panel across the gutter
        if want_out > 0 and want_in == 0:
            continue

        center = 0.5 * (c0 + c1)
        dist = abs(center - expected_x)
        local_idx = slice(c0 - wx0, c1 - wx0 + 1)
        mean_line = float(col_density[local_idx].max())
        mean_dark = float(col_dark_density[local_idx].max())

        # Ignore weak noisy art lines far from expected position unless strong continuous frame
        if dist > 48 and mean_line < 0.78 and want_in == 0:
            continue

        dark_bonus = mean_dark if border_style == "box" else 0.0
        strong_frame = 1.0 if mean_line >= 0.82 else 0.0

        score = (
            float(want_in > want_out),
            float(want_in - want_out),
            strong_frame,
            dark_bonus * 0.5 + mean_line * 0.5 - dist * 0.002,
            -dist,
        )
        if best_score is None or score > best_score:
            best_score = score
            best_run = (c0, c1)

    return best_run


def _detect_horizontal_border(
    line_mask: np.ndarray,
    dark_mask: np.ndarray,
    expected_y: int,
    slot_rect: tuple[int, int, int, int],
    side: Literal["top", "bottom"],
    border_style: Literal["open", "box"],
    search_radius: int = 56,
    clamp_bounds: tuple[int, int] | None = None,
) -> tuple[int, int] | None:
    """Detect a horizontal panel frame line near `expected_y` with corner-polarity disambiguation."""
    h, w = line_mask.shape
    x0, _y0, x1, _y1 = slot_rect

    wy0 = max(0, expected_y - search_radius)
    wy1 = min(h - 1, expected_y + search_radius)
    if clamp_bounds is not None:
        wy0 = max(wy0, clamp_bounds[0])
        wy1 = min(wy1, clamp_bounds[1])
    if wy1 <= wy0:
        return None

    span_w = max(1, x1 - x0)
    margin_x = min(52, max(12, span_w // 6))
    sx0 = max(0, x0 + margin_x)
    sx1 = min(w, x1 - margin_x)
    if sx1 - sx0 < 24:
        sx0, sx1 = max(0, x0), min(w, x1)

    row_density = line_mask[wy0 : wy1 + 1, sx0:sx1].mean(axis=1)
    row_dark_density = dark_mask[wy0 : wy1 + 1, sx0:sx1].mean(axis=1)
    hits = np.where(row_density >= 0.62)[0] + wy0
    runs = _find_contiguous_runs(hits, max_thickness=18)
    if not runs:
        return None

    perp_x_pad = max(48, min(140, span_w // 3))
    left_band = (max(0, x0 - perp_x_pad), min(w, x0 + perp_x_pad))
    right_band = (max(0, x1 - perp_x_pad), min(w, x1 + perp_x_pad))

    def _has_perp_bar(y_start: int, y_end: int) -> int:
        if y_end - y_start < 6:
            return 0
        count = 0
        for bx0, bx1 in (left_band, right_band):
            if bx1 > bx0:
                col_means = line_mask[y_start:y_end, bx0:bx1].mean(axis=0)
                if float(col_means.max()) >= 0.62:
                    count += 1
        return count

    best_run: tuple[int, int] | None = None
    best_score: tuple[float, ...] | None = None

    for r0, r1 in runs:
        has_up = _has_perp_bar(max(0, r0 - 30), max(0, r0 - 4))
        has_down = _has_perp_bar(min(h, r1 + 5), min(h, r1 + 31))

        want_in = has_down if side == "top" else has_up
        want_out = has_up if side == "top" else has_down

        if want_out > 0 and want_in == 0:
            continue

        center = 0.5 * (r0 + r1)
        dist = abs(center - expected_y)
        local_idx = slice(r0 - wy0, r1 - wy0 + 1)
        mean_line = float(row_density[local_idx].max())
        mean_dark = float(row_dark_density[local_idx].max())

        # Ignore weak noisy character art far from expected line unless strong continuous frame
        if dist > 48 and mean_line < 0.78 and want_in == 0:
            continue

        dark_bonus = mean_dark if border_style == "box" else 0.0
        strong_frame = 1.0 if mean_line >= 0.82 else 0.0

        score = (
            float(want_in > want_out),
            float(want_in - want_out),
            strong_frame,
            dark_bonus * 0.5 + mean_line * 0.5 - dist * 0.002,
            -dist,
        )
        if best_score is None or score > best_score:
            best_score = score
            best_run = (r0, r1)

    return best_run


def _longest_dark_span_ratio(mask_1d: np.ndarray, max_gap: int = 4) -> float:
    """Return ratio of the longest nearly-continuous True segment in a 1D boolean array."""
    n = len(mask_1d)
    if n == 0:
        return 0.0
    best = 0
    cur = 0
    gap = 0
    for val in mask_1d:
        if val:
            cur += gap + 1
            gap = 0
            if cur > best:
                best = cur
        else:
            if cur > 0:
                gap += 1
                if gap > max_gap:
                    cur = 0
                    gap = 0
    return best / float(n)


def _trim_residual_edge_borders(
    panel_im: Image.Image,
    edge_band_px: int = 14,
    deep_rule_ratio: float = 0.20,
) -> Image.Image:
    """Trim residual straight borders from cropped panels without clipping real character art.

    Two safeguards:
    1. Outer `edge_band_px` (14px): trims any straight dark/gray border (`chroma <= 42`,
       `cmin <= 220`, coverage `>= 0.55`).
    2. Outer `deep_rule_ratio` (20%): trims from any thin (`<= 16px`), continuous straight dark
       frame rule (`chroma <= 42`, `cmin <= 145`, coverage `> 0.60`, continuous span `>= 0.55`)
       outward to the edge so ZERO neighbor-panel bleed or stray black dividers ever leak in.
    """
    arr = np.asarray(panel_im.convert("RGB"))
    h, w, _ = arr.shape
    if h < 48 or w < 48:
        return panel_im

    cmin = arr.min(axis=2)
    cmax = arr.max(axis=2)
    chroma = cmax - cmin
    neutral_line = (chroma <= 42) & (cmin <= 220)
    dark_rule = (chroma <= 42) & (cmin <= 145)

    x0, y0, x1, y1 = 0, 0, w, h

    # 1. Outer 20% continuous straight dark frame rule safeguard
    deep_y = max(edge_band_px, int(round((y1 - y0) * deep_rule_ratio)))
    deep_x = max(edge_band_px, int(round((x1 - x0) * deep_rule_ratio)))

    # Top 20%
    top_dark_rows = np.where(dark_rule[y0 : y0 + deep_y, x0:x1].mean(axis=1) > 0.60)[0] + y0
    top_dark_runs = [
        (r0, r1)
        for r0, r1 in _find_contiguous_runs(top_dark_rows, max_thickness=16)
        if any(_longest_dark_span_ratio(dark_rule[r, x0:x1]) >= 0.55 for r in range(r0, r1 + 1))
    ]
    if top_dark_runs:
        y0 = max(y0, top_dark_runs[-1][1] + 3)

    # Bottom 20%
    bot_start = max(y0 + 32, y1 - deep_y)
    bot_dark_rows = np.where(dark_rule[bot_start:y1, x0:x1].mean(axis=1) > 0.60)[0] + bot_start
    bot_dark_runs = [
        (r0, r1)
        for r0, r1 in _find_contiguous_runs(bot_dark_rows, max_thickness=16)
        if any(_longest_dark_span_ratio(dark_rule[r, x0:x1]) >= 0.55 for r in range(r0, r1 + 1))
    ]
    if bot_dark_runs:
        y1 = min(y1, bot_dark_runs[0][0] - 3)

    # Left 20%
    left_dark_cols = np.where(dark_rule[y0:y1, x0 : x0 + deep_x].mean(axis=0) > 0.60)[0] + x0
    left_dark_runs = [
        (c0, c1)
        for c0, c1 in _find_contiguous_runs(left_dark_cols, max_thickness=16)
        if any(_longest_dark_span_ratio(dark_rule[y0:y1, c]) >= 0.55 for c in range(c0, c1 + 1))
    ]
    if left_dark_runs:
        x0 = max(x0, left_dark_runs[-1][1] + 3)

    # Right 20%
    right_start = max(x0 + 32, x1 - deep_x)
    right_dark_cols = np.where(dark_rule[y0:y1, right_start:x1].mean(axis=0) > 0.60)[0] + right_start
    right_dark_runs = [
        (c0, c1)
        for c0, c1 in _find_contiguous_runs(right_dark_cols, max_thickness=16)
        if any(_longest_dark_span_ratio(dark_rule[y0:y1, c]) >= 0.55 for c in range(c0, c1 + 1))
    ]
    if right_dark_runs:
        x1 = min(x1, right_dark_runs[0][0] - 3)

    if x1 - x0 < 32 or y1 - y0 < 32:
        x0, y0, x1, y1 = 0, 0, w, h

    # 2. Outer 14px neutral dark/gray border strip (catches #B0B0B0 open guides & residual anti-aliasing)
    top_limit = min(edge_band_px, (y1 - y0) // 6)
    top_dens = neutral_line[y0 : y0 + top_limit, x0:x1].mean(axis=1)
    top_bad = np.where(top_dens >= 0.55)[0]
    if len(top_bad) > 0:
        y0 += min(edge_band_px, int(top_bad[-1]) + 2)

    bot_limit = min(edge_band_px, (y1 - y0) // 6)
    bot_dens = neutral_line[y1 - bot_limit : y1, x0:x1].mean(axis=1)
    bot_bad = np.where(bot_dens >= 0.55)[0]
    if len(bot_bad) > 0:
        trim_b = bot_limit - int(bot_bad[0]) + 1
        y1 -= min(edge_band_px, trim_b)

    left_limit = min(edge_band_px, (x1 - x0) // 6)
    left_dens = neutral_line[y0:y1, x0 : x0 + left_limit].mean(axis=0)
    left_bad = np.where(left_dens >= 0.55)[0]
    if len(left_bad) > 0:
        x0 += min(edge_band_px, int(left_bad[-1]) + 2)

    right_limit = min(edge_band_px, (x1 - x0) // 6)
    right_dens = neutral_line[y0:y1, x1 - right_limit : x1].mean(axis=0)
    right_bad = np.where(right_dens >= 0.55)[0]
    if len(right_bad) > 0:
        trim_r = right_limit - int(right_bad[0]) + 1
        x1 -= min(edge_band_px, trim_r)

    if x1 - x0 < 32 or y1 - y0 < 32:
        return panel_im
    if (x0, y0, x1, y1) == (0, 0, w, h):
        return panel_im
    return panel_im.crop((x0, y0, x1, y1))


def _slot_edge_neighbors(
    slots: tuple[PanelSlotSpec, ...],
    idx: int,
) -> dict[str, list[int]]:
    """Return indices of neighboring slots directly facing each of the 4 sides of `slots[idx]`."""
    x0, y0, x1, y1 = slots[idx].rect
    neighbors: dict[str, list[int]] = {"left": [], "right": [], "top": [], "bottom": []}
    for other_idx, other in enumerate(slots):
        if other_idx == idx:
            continue
        ox0, oy0, ox1, oy1 = other.rect
        horiz_overlap = min(x1, ox1) - max(x0, ox0) > 40
        vert_overlap = min(y1, oy1) - max(y0, oy0) > 40
        if horiz_overlap and 0 <= (oy0 - y1) <= 80:
            neighbors["bottom"].append(other_idx)
        if horiz_overlap and 0 <= (y0 - oy1) <= 80:
            neighbors["top"].append(other_idx)
        if vert_overlap and 0 <= (ox0 - x1) <= 80:
            neighbors["right"].append(other_idx)
        if vert_overlap and 0 <= (x0 - ox1) <= 80:
            neighbors["left"].append(other_idx)
    return neighbors


def extract_panels_from_page(
    raw_page_im: Image.Image,
    layout_id: str,
) -> list[Image.Image]:
    """Extract clean, border-stripped, pure-`#FFFFFF` panel images from a generated V4 act page.

    Steps:
    1. Convert to RGB and normalize to `(V4_PAGE_W, V4_PAGE_H)` (900x1350) preserving 2:3 framing.
    2. Detect actual drawn horizontal & vertical dark/gray panel frame lines using a wide search
       window (up to `±140px` for internal dividers, `±56px` for outer edges) with corner-polarity
       disambiguation, two-stage horizontal/vertical refinement, and adjacent-slot coupling so
       both open top slots and bottom/split boxes snap cleanly to real drawn dividers.
    3. Crop cleanly inside the snapped border + run outer-20% continuous-dark-rule & outer-14px
       border-strip safeguards so zero neighbor bleed or stray frame lines leak in.
    4. Level near-white neutral pixels to strict `#FFFFFF` so extracted panels composite seamlessly.
    """
    spec = get_page_layout(layout_id)
    page = _normalize_page_to_canvas(raw_page_im)
    arr = np.asarray(page)
    h, w, _ = arr.shape

    cmin = arr.min(axis=2)
    cmax = arr.max(axis=2)
    chroma = cmax - cmin
    line_mask = (chroma <= 42) & (cmin <= 215)
    dark_mask = (chroma <= 42) & (cmin <= 145)

    all_neighbors = [_slot_edge_neighbors(spec.slots, i) for i in range(len(spec.slots))]

    def _internal_search_radius(slot: PanelSlotSpec, nb_indices: list[int], axis: Literal["h", "v"]) -> int:
        if not nb_indices:
            return 56
        own_span = slot.height if axis == "h" else slot.width
        nb_min_span = min(
            (spec.slots[n].height if axis == "h" else spec.slots[n].width) for n in nb_indices
        )
        return max(56, min(140, int(min(own_span, nb_min_span) * 0.34)))

    # Stage 1: Detect horizontal borders first (with wide ±140px window on internal dividers)
    snapped_bounds: list[dict[str, tuple[int, int] | None]] = []
    for idx, slot in enumerate(spec.slots):
        x0, y0, x1, y1 = slot.rect
        nb = all_neighbors[idx]
        top_r = _internal_search_radius(slot, nb["top"], "h")
        bot_r = _internal_search_radius(slot, nb["bottom"], "h")

        top_clamp = (140, h - 180) if nb["top"] else (0, min(h - 1, y0 + 80))
        bot_clamp = (180, h - 140) if nb["bottom"] else (max(0, y1 - 80), h - 1)

        top_run = _detect_horizontal_border(
            line_mask, dark_mask, y0, slot.rect, "top", slot.border_style,
            search_radius=top_r, clamp_bounds=top_clamp,
        )
        bot_run = _detect_horizontal_border(
            line_mask, dark_mask, y1, slot.rect, "bottom", slot.border_style,
            search_radius=bot_r, clamp_bounds=bot_clamp,
        )
        snapped_bounds.append({"left": None, "right": None, "top": top_run, "bottom": bot_run})

    # Sync row-mate box horizontal borders if one sibling detected a strong divider and another missed it
    for idx, slot in enumerate(spec.slots):
        if slot.border_style != "box":
            continue
        b = snapped_bounds[idx]
        for side in ("top", "bottom"):
            if b[side] is not None:
                continue
            ref_coord = slot.rect[1] if side == "top" else slot.rect[3]
            for other_idx, other in enumerate(spec.slots):
                if other_idx == idx or other.border_style != "box":
                    continue
                other_coord = other.rect[1] if side == "top" else other.rect[3]
                if abs(other_coord - ref_coord) <= 6 and snapped_bounds[other_idx][side] is not None:
                    b[side] = snapped_bounds[other_idx][side]
                    break

    # Stage 2: Detect vertical borders using the snapped horizontal span (eff_y0..eff_y1)
    for idx, slot in enumerate(spec.slots):
        x0, y0, x1, y1 = slot.rect
        b = snapped_bounds[idx]
        nb = all_neighbors[idx]
        eff_y0 = b["top"][0] if b["top"] is not None else y0
        eff_y1 = b["bottom"][1] if b["bottom"] is not None else y1
        if eff_y1 - eff_y0 < 60:
            eff_y0, eff_y1 = y0, y1
        eff_rect = (x0, eff_y0, x1, eff_y1)

        left_r = _internal_search_radius(slot, nb["left"], "v")
        right_r = _internal_search_radius(slot, nb["right"], "v")
        left_clamp = (120, w - 120) if nb["left"] else (0, min(w - 1, x0 + 80))
        right_clamp = (120, w - 120) if nb["right"] else (max(0, x1 - 80), w - 1)

        b["left"] = _detect_vertical_border(
            line_mask, dark_mask, x0, eff_rect, "left", slot.border_style,
            search_radius=left_r, clamp_bounds=left_clamp,
        )
        b["right"] = _detect_vertical_border(
            line_mask, dark_mask, x1, eff_rect, "right", slot.border_style,
            search_radius=right_r, clamp_bounds=right_clamp,
        )

    # Sync column-mate box vertical borders if one sibling missed it
    for idx, slot in enumerate(spec.slots):
        if slot.border_style != "box":
            continue
        b = snapped_bounds[idx]
        for side in ("left", "right"):
            if b[side] is not None:
                continue
            ref_coord = slot.rect[0] if side == "left" else slot.rect[2]
            for other_idx, other in enumerate(spec.slots):
                if other_idx == idx or other.border_style != "box":
                    continue
                other_coord = other.rect[0] if side == "left" else other.rect[2]
                if abs(other_coord - ref_coord) <= 6 and snapped_bounds[other_idx][side] is not None:
                    b[side] = snapped_bounds[other_idx][side]
                    break

    # Stage 3: Crop cleanly inside snapped borders & couple adjacent open/box slots to real dividers
    extracted: list[Image.Image] = []
    for idx, slot in enumerate(spec.slots):
        x0, y0, x1, y1 = slot.rect
        b = snapped_bounds[idx]
        nb = all_neighbors[idx]

        # Open outer page edges with no drawn border keep generous margin so protruding props stay intact
        if b["left"] is not None:
            cx0 = b["left"][1] + 6
        elif slot.border_style == "open" and not nb["left"]:
            cx0 = 4
        else:
            cx0 = x0 + 8

        if b["right"] is not None:
            cx1 = b["right"][0] - 5
        elif slot.border_style == "open" and not nb["right"]:
            cx1 = w - 4
        else:
            cx1 = x1 - 8

        if b["top"] is not None:
            cy0 = b["top"][1] + 6
        elif slot.border_style == "open" and not nb["top"]:
            cy0 = 4
        else:
            cy0 = y0 + 8

        if b["bottom"] is not None:
            cy1 = b["bottom"][0] - 5
        elif slot.border_style == "open" and not nb["bottom"]:
            cy1 = h - 4
        else:
            cy1 = y1 - 8

        # Couple undetected (especially borderless `open`) internal edges directly to real adjacent dividers
        if b["bottom"] is None and nb["bottom"]:
            below_tops = [
                snapped_bounds[n]["top"][0]
                for n in nb["bottom"]
                if snapped_bounds[n]["top"] is not None
            ]
            if below_tops:
                real_divider_y = min(below_tops)
                if slot.border_style == "open":
                    # Follow the real downward/upward drift so open-panel artwork isn't clipped!
                    cy1 = real_divider_y - 3
                else:
                    cy1 = min(cy1, real_divider_y - 4)

        if b["top"] is None and nb["top"]:
            above_bots = [
                snapped_bounds[n]["bottom"][1]
                for n in nb["top"]
                if snapped_bounds[n]["bottom"] is not None
            ]
            if above_bots:
                real_divider_y = max(above_bots)
                if slot.border_style == "open":
                    cy0 = real_divider_y + 4
                else:
                    cy0 = max(cy0, real_divider_y + 5)

        if b["right"] is None and nb["right"]:
            right_lefts = [
                snapped_bounds[n]["left"][0]
                for n in nb["right"]
                if snapped_bounds[n]["left"] is not None
            ]
            if right_lefts:
                real_divider_x = min(right_lefts)
                if slot.border_style == "open":
                    cx1 = real_divider_x - 3
                else:
                    cx1 = min(cx1, real_divider_x - 4)

        if b["left"] is None and nb["left"]:
            left_rights = [
                snapped_bounds[n]["right"][1]
                for n in nb["left"]
                if snapped_bounds[n]["right"] is not None
            ]
            if left_rights:
                real_divider_x = max(left_rights)
                if slot.border_style == "open":
                    cx0 = real_divider_x + 4
                else:
                    cx0 = max(cx0, real_divider_x + 5)

        cx0 = max(0, min(w - 32, cx0))
        cy0 = max(0, min(h - 32, cy0))
        cx1 = max(cx0 + 32, min(w, cx1))
        cy1 = max(cy0 + 32, min(h, cy1))

        cropped = page.crop((cx0, cy0, cx1, cy1))
        trimmed = _trim_residual_edge_borders(cropped, edge_band_px=14, deep_rule_ratio=0.20)
        cleaned = _level_near_white_bg(trimmed)
        extracted.append(cleaned)

    return extracted
