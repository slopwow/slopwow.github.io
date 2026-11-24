"""V4 5-act variable page-layout specs, clean blueprint renderer, and border-snapping panel extractor.

Defines 6 variable comic page layouts on a canonical `900x1350` (2:3) pure `#FFFFFF` canvas,
generates text-free structural blueprints for Gemini Nano Banana 2.1 page-batch illustration,
and extracts clean individual panel images with polarity-aware border snapping, residual
border stripping, and pure `#FFFFFF` background normalization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

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
    *,
    all_boxed: bool = False,
    slot_boxed: Sequence[bool] | None = None,
) -> Image.Image:
    """Render a zero-text structural panel blueprint on a pure solid `#FFFFFF` canvas.

    Draws crisp 4px `#141414` rectangular frames for `box` slots (and for ALL slots
    when `all_boxed=True`, or any slot `i` where `slot_boxed[i]` is True) and subtle
    3px `#B0B0B0` guide rectangles for remaining `open` slots, with ZERO text, digits,
    or labels.
    """
    spec = get_page_layout(layout_id)
    w, h = int(size[0]), int(size[1])
    if w <= 0 or h <= 0:
        raise ValueError(f"Blueprint size must be positive, got {size}.")
    if slot_boxed is not None and len(slot_boxed) != len(spec.slots):
        raise ValueError(
            f"slot_boxed length ({len(slot_boxed)}) must match layout '{layout_id}' "
            f"panel count ({len(spec.slots)})."
        )

    sx = w / float(V4_PAGE_W)
    sy = h / float(V4_PAGE_H)
    scale_stroke = min(sx, sy)

    img = Image.new("RGB", (w, h), _PURE_WHITE)
    draw = ImageDraw.Draw(img)

    for idx, slot in enumerate(spec.slots):
        x0 = int(round(slot.rect[0] * sx))
        y0 = int(round(slot.rect[1] * sy))
        x1 = int(round(slot.rect[2] * sx))
        y1 = int(round(slot.rect[3] * sy))

        is_boxed = (
            all_boxed
            or slot.border_style == "box"
            or (bool(slot_boxed[idx]) if slot_boxed is not None else False)
        )
        if is_boxed:
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
    *,
    strict_dark_only: bool = False,
) -> Image.Image:
    """Trim residual straight borders from cropped panels without clipping real character art.

    Two safeguards:
    1. Outer `edge_band_px` (14px): trims any straight dark/gray border (`chroma <= 42`,
       `cmin <= 220` in clean-white mode, or `chroma <= 36`, `cmin <= 165` when
       `strict_dark_only=True` for full-bleed colored panels, coverage `>= 0.55`).
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
    if strict_dark_only:
        neutral_line = (chroma <= 36) & (cmin <= 165)
    else:
        neutral_line = (chroma <= 42) & (cmin <= 220)
    dark_rule = (chroma <= 42) & (cmin <= 145)

    x0, y0, x1, y1 = 0, 0, w, h

    # 1. Outer 20% continuous straight dark frame rule safeguard (only when enabled)
    if deep_rule_ratio > 0.0:
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


def _trim_stray_white_edge_strips(
    panel_im: Image.Image,
    max_strip_px: int = 10,
) -> Image.Image:
    """Trim accidental stray thin white strips (<= `max_strip_px`) on full-bleed panel edges
    only when the immediately adjacent interior pixels are colored/non-white.
    """
    arr = np.asarray(panel_im.convert("RGB"))
    h, w, _ = arr.shape
    if h < 48 or w < 48:
        return panel_im

    white_px = (arr[:, :, 0] >= 246) & (arr[:, :, 1] >= 246) & (arr[:, :, 2] >= 246)
    x0, y0, x1, y1 = 0, 0, w, h

    # Top stray white strip
    top_cap = min(max_strip_px, (y1 - y0) // 8)
    lead = 0
    while lead < top_cap and float(white_px[y0 + lead, x0:x1].mean()) >= 0.85:
        lead += 1
    if lead > 0 and (y0 + lead + 12) <= y1:
        inner_nonwhite = float((~white_px[y0 + lead : y0 + lead + 12, x0:x1]).mean())
        if inner_nonwhite >= 0.45:
            y0 += lead

    # Bottom stray white strip
    bot_cap = min(max_strip_px, (y1 - y0) // 8)
    lead = 0
    while lead < bot_cap and float(white_px[y1 - 1 - lead, x0:x1].mean()) >= 0.85:
        lead += 1
    if lead > 0 and (y1 - lead - 12) >= y0:
        inner_nonwhite = float((~white_px[y1 - lead - 12 : y1 - lead, x0:x1]).mean())
        if inner_nonwhite >= 0.45:
            y1 -= lead

    # Left stray white strip
    left_cap = min(max_strip_px, (x1 - x0) // 8)
    lead = 0
    while lead < left_cap and float(white_px[y0:y1, x0 + lead].mean()) >= 0.85:
        lead += 1
    if lead > 0 and (x0 + lead + 12) <= x1:
        inner_nonwhite = float((~white_px[y0:y1, x0 + lead : x0 + lead + 12]).mean())
        if inner_nonwhite >= 0.45:
            x0 += lead

    # Right stray white strip
    right_cap = min(max_strip_px, (x1 - x0) // 8)
    lead = 0
    while lead < right_cap and float(white_px[y0:y1, x1 - 1 - lead].mean()) >= 0.85:
        lead += 1
    if lead > 0 and (x1 - lead - 12) >= x0:
        inner_nonwhite = float((~white_px[y0:y1, x1 - lead - 12 : x1 - lead]).mean())
        if inner_nonwhite >= 0.45:
            x1 -= lead

    if x1 - x0 < 32 or y1 - y0 < 32 or (x0, y0, x1, y1) == (0, 0, w, h):
        return panel_im
    return panel_im.crop((x0, y0, x1, y1))


def _find_white_gutter_run(
    white_mask: np.ndarray,
    axis: Literal["h", "v"],
    expected_mid: int,
    perp_lo: int,
    perp_hi: int,
    search_lo: int,
    search_hi: int,
    *,
    min_white_ratio: float = 0.85,
    min_thickness: int = 4,
    max_thickness: int = 96,
    require_bracket_walls: bool = False,
    frame_break_bands: Sequence[tuple[int, int]] | None = None,
) -> tuple[int, int] | None:
    """Locate the pure-`#FFFFFF` gutter band closest to `expected_mid` along `axis`."""
    h, w = white_mask.shape
    if axis == "h":
        s0 = max(0, search_lo)
        s1 = min(h - 1, search_hi)
        p0 = max(0, perp_lo)
        p1 = min(w, perp_hi)
        if s1 <= s0 or p1 - p0 < 24:
            return None
        profile = white_mask[s0 : s1 + 1, p0:p1].mean(axis=1)
    else:
        s0 = max(0, search_lo)
        s1 = min(w - 1, search_hi)
        p0 = max(0, perp_lo)
        p1 = min(h, perp_hi)
        if s1 <= s0 or p1 - p0 < 24:
            return None
        profile = white_mask[p0:p1, s0 : s1 + 1].mean(axis=0)

    hits = np.where(profile >= min_white_ratio)[0] + s0
    if len(hits) == 0:
        return None

    # Group contiguous white rows/cols (gutters are typically 6..80px)
    runs: list[tuple[int, int]] = []
    start = int(hits[0])
    prev = start
    for raw_idx in hits[1:]:
        idx = int(raw_idx)
        if idx == prev + 1:
            prev = idx
        else:
            thickness = prev - start + 1
            if min_thickness <= thickness <= max_thickness:
                runs.append((start, prev))
            start = idx
            prev = idx
    thickness = prev - start + 1
    if min_thickness <= thickness <= max_thickness:
        runs.append((start, prev))
    if not runs:
        return None

    best_run: tuple[int, int] | None = None
    best_key: tuple[float, float, float, float] | None = None
    for r0, r1 in runs:
        # Check whether dark box-frame walls bracket BOTH sides of this white band
        if axis == "h":
            ab0, ab1 = max(0, r0 - 8), r0
            bl0, bl1 = r1 + 1, min(h, r1 + 9)
            has_pre = ab1 > ab0 and float(white_mask[ab0:ab1, p0:p1].mean(axis=1).min()) < 0.45
            has_post = bl1 > bl0 and float(white_mask[bl0:bl1, p0:p1].mean(axis=1).min()) < 0.45
        else:
            lf0, lf1 = max(0, r0 - 8), r0
            rt0, rt1 = r1 + 1, min(w, r1 + 9)
            has_pre = lf1 > lf0 and float(white_mask[p0:p1, lf0:lf1].mean(axis=0).min()) < 0.45
            has_post = rt1 > rt0 and float(white_mask[p0:p1, rt0:rt1].mean(axis=0).min()) < 0.45
        bracket_ok = bool(has_pre and has_post)
        if require_bracket_walls and not bracket_ok:
            continue

        # Check whether perpendicular outer box walls break cleanly across this gutter
        frame_break_ok = True
        if frame_break_bands:
            for b0, b1 in frame_break_bands:
                if b1 <= b0:
                    continue
                if axis == "h":
                    band_ratio = float(white_mask[r0 : r1 + 1, b0:b1].mean())
                else:
                    band_ratio = float(white_mask[b0:b1, r0 : r1 + 1].mean())
                if band_ratio < 0.80:
                    frame_break_ok = False
                    break

        center = 0.5 * (r0 + r1)
        dist = abs(center - expected_mid)
        run_thick = float(r1 - r0 + 1)
        # Strongly prefer gutters where outer box walls break & both sides have frame walls
        key = (
            1.0 if frame_break_ok else 0.0,
            1.0 if bracket_ok else 0.0,
            -dist + min(run_thick, 32.0) * 0.15,
            run_thick,
        )
        if best_key is None or key > best_key:
            best_key = key
            best_run = (r0, r1)
    return best_run


def _peel_black_box_frame(
    panel_im: Image.Image,
    max_frame_px: int = 12,
) -> Image.Image:
    """Peel ONLY the crisp neutral-black rectangular box frame (and <=4px outer white jitter)
    from a white-gutter-segmented full-bleed panel, without touching dark colored interior art.
    """
    arr = np.asarray(panel_im.convert("RGB"))
    h, w, _ = arr.shape
    if h < 48 or w < 48:
        return panel_im

    cmin = arr.min(axis=2)
    cmax = arr.max(axis=2)
    chroma = cmax - cmin
    # Strictly crisp neutral-black frame line (#141414), NOT mid-dark slate/stone interiors like (64,68,72)!
    frame_px = (chroma <= 20) & (cmax <= 55)

    def _peel_1d(line_frame: np.ndarray, limit: int) -> int:
        n = min(limit, len(line_frame))
        # Find the first crisp black frame row/col within the outer 5px (skipping white/gray AA transition)
        start = -1
        for i in range(min(5, n)):
            if float(line_frame[i]) >= 0.55:
                start = i
                break
        if start < 0:
            return 0
        end = start
        while (end + 1) < n and (end - start + 1) < max_frame_px and float(line_frame[end + 1]) >= 0.55:
            end += 1
        # Peel through the frame plus 2px anti-aliasing inset
        return min(n, end + 3)

    top_lim = min(max_frame_px + 5, h // 8)
    bot_lim = min(max_frame_px + 5, h // 8)
    left_lim = min(max_frame_px + 5, w // 8)
    right_lim = min(max_frame_px + 5, w // 8)

    # Sample middle 80% along perpendicular axis so rounded corners don't skew frame density
    mx0, mx1 = max(0, w // 10), min(w, w - w // 10)
    my0, my1 = max(0, h // 10), min(h, h - h // 10)

    top_peel = _peel_1d(frame_px[:top_lim, mx0:mx1].mean(axis=1), top_lim)
    bot_peel = _peel_1d(frame_px[h - bot_lim : h, mx0:mx1].mean(axis=1)[::-1], bot_lim)
    left_peel = _peel_1d(frame_px[my0:my1, :left_lim].mean(axis=0), left_lim)
    right_peel = _peel_1d(frame_px[my0:my1, w - right_lim : w].mean(axis=0)[::-1], right_lim)

    x0, y0, x1, y1 = left_peel, top_peel, w - right_peel, h - bot_peel
    if x1 - x0 < 32 or y1 - y0 < 32:
        return panel_im
    return panel_im.crop((x0, y0, x1, y1))


def _extract_all_boxed_panels(
    page: Image.Image,
    spec: PageLayoutSpec,
    *,
    slot_full_bleed: Sequence[bool] | None = None,
) -> list[Image.Image] | None:
    """Segment an all-boxed V4 page directly from its pure-`#FFFFFF` page margins and
    inter-panel gutters, then peel only the outer crisp `#141414` box frames.

    Because full-bleed panels can contain dark neutral stone/cavern backgrounds, locating the
    `#FFFFFF` gutters first guarantees ZERO cross-gutter neighbor bleed and ZERO false interior cuts.
    Supports mixed full-bleed and clean-white interiors on the SAME page via `slot_full_bleed`:
    - `is_fb[i] == True`: keeps edge-to-edge full-bleed color pixels (`_peel_black_box_frame` +
      `_trim_stray_white_edge_strips`, NO `_level_near_white_bg`, NO 20% dark-interior chopper).
    - `is_fb[i] == False`: trims any residual edge border within outer 14px and applies
      `_level_near_white_bg` for crisp pure `#FFFFFF`.
    Returns `None` only if outer/internal white gutters cannot be detected cleanly (triggering fallback).
    """
    arr = np.asarray(page)
    h, w, _ = arr.shape
    is_fb = (
        [bool(v) for v in slot_full_bleed]
        if slot_full_bleed is not None
        else [True] * len(spec.slots)
    )
    white_px = (arr[:, :, 0] >= 240) & (arr[:, :, 1] >= 240) & (arr[:, :, 2] >= 240)
    all_neighbors = [_slot_edge_neighbors(spec.slots, i) for i in range(len(spec.slots))]

    # 1. Detect outer non-white page content envelope (outside all black panel frames)
    row_white = white_px.mean(axis=1)
    col_white = white_px.mean(axis=0)
    nonwhite_rows = np.where(row_white < 0.90)[0]
    nonwhite_cols = np.where(col_white < 0.90)[0]
    if len(nonwhite_rows) < 100 or len(nonwhite_cols) < 100:
        return None
    page_top = int(nonwhite_rows[0])
    page_bot = int(nonwhite_rows[-1])
    page_left = int(nonwhite_cols[0])
    page_right = int(nonwhite_cols[-1])

    outer_v_bands = (
        (page_left, min(w, page_left + 6)),
        (max(0, page_right - 5), min(w, page_right + 1)),
    )

    # 2. Detect vertical span (outer top/bottom of each slot's black frame) via white horizontal gutters
    box_y0: list[int] = [0] * len(spec.slots)
    box_y1: list[int] = [0] * len(spec.slots)

    # Cache detected internal horizontal gutters keyed by canonical midpoint
    h_gutter_cache: dict[int, tuple[int, int] | None] = {}

    def _get_h_gutter(upper_idx: int, lower_idx: int) -> tuple[int, int] | None:
        u = spec.slots[upper_idx]
        lo = spec.slots[lower_idx]
        mid_y = (u.rect[3] + lo.rect[1]) // 2
        key = round(mid_y / 8) * 8
        if key not in h_gutter_cache:
            radius = max(60, min(140, int(min(u.height, lo.height) * 0.34)))
            h_gutter_cache[key] = _find_white_gutter_run(
                white_px,
                "h",
                expected_mid=mid_y,
                perp_lo=page_left + 16,
                perp_hi=page_right - 16,
                search_lo=max(page_top + 60, mid_y - radius),
                search_hi=min(page_bot - 60, mid_y + radius),
                require_bracket_walls=True,
                frame_break_bands=outer_v_bands,
            )
        return h_gutter_cache[key]

    for idx, slot in enumerate(spec.slots):
        nb = all_neighbors[idx]
        # Top edge
        if not nb["top"]:
            # Scan down from top page margin within slot's approximate horizontal span
            sx0 = max(page_left + 12, slot.rect[0] + 24)
            sx1 = min(page_right - 12, slot.rect[2] - 24)
            band_w = white_px[: min(h, slot.rect[1] + 96), sx0:sx1].mean(axis=1)
            nw = np.where(band_w < 0.85)[0]
            box_y0[idx] = int(nw[0]) if len(nw) > 0 else page_top
        else:
            gut = _get_h_gutter(nb["top"][0], idx)
            if gut is None:
                return None
            box_y0[idx] = gut[1] + 1

        # Bottom edge
        if not nb["bottom"]:
            sx0 = max(page_left + 12, slot.rect[0] + 24)
            sx1 = min(page_right - 12, slot.rect[2] - 24)
            y_start = max(0, slot.rect[3] - 96)
            band_w = white_px[y_start:h, sx0:sx1].mean(axis=1)
            nw = np.where(band_w < 0.85)[0]
            box_y1[idx] = int(y_start + nw[-1]) if len(nw) > 0 else page_bot
        else:
            gut = _get_h_gutter(idx, nb["bottom"][0])
            if gut is None:
                return None
            box_y1[idx] = gut[0] - 1

    # 3. Detect horizontal span (outer left/right of each slot's black frame) via white vertical gutters
    box_x0: list[int] = [0] * len(spec.slots)
    box_x1: list[int] = [0] * len(spec.slots)

    for idx, slot in enumerate(spec.slots):
        nb = all_neighbors[idx]
        sy0 = min(h - 1, box_y0[idx] + 20)
        sy1 = max(sy0 + 24, box_y1[idx] - 20)
        row_h_bands = (
            (box_y0[idx], min(h, box_y0[idx] + 6)),
            (max(0, box_y1[idx] - 5), min(h, box_y1[idx] + 1)),
        )

        # Left edge
        if not nb["left"]:
            band_w = white_px[sy0:sy1, : min(w, slot.rect[0] + 96)].mean(axis=0)
            nw = np.where(band_w < 0.85)[0]
            box_x0[idx] = int(nw[0]) if len(nw) > 0 else page_left
        else:
            left_nb = spec.slots[nb["left"][0]]
            mid_x = (left_nb.rect[2] + slot.rect[0]) // 2
            radius = max(60, min(140, int(min(left_nb.width, slot.width) * 0.34)))
            gut = _find_white_gutter_run(
                white_px,
                "v",
                expected_mid=mid_x,
                perp_lo=sy0,
                perp_hi=sy1,
                search_lo=max(page_left + 60, mid_x - radius),
                search_hi=min(page_right - 60, mid_x + radius),
                require_bracket_walls=True,
                frame_break_bands=row_h_bands,
            )
            if gut is None:
                return None
            box_x0[idx] = gut[1] + 1

        # Right edge
        if not nb["right"]:
            x_start = max(0, slot.rect[2] - 96)
            band_w = white_px[sy0:sy1, x_start:w].mean(axis=0)
            nw = np.where(band_w < 0.85)[0]
            box_x1[idx] = int(x_start + nw[-1]) if len(nw) > 0 else page_right
        else:
            right_nb = spec.slots[nb["right"][0]]
            mid_x = (slot.rect[2] + right_nb.rect[0]) // 2
            radius = max(60, min(140, int(min(slot.width, right_nb.width) * 0.34)))
            gut = _find_white_gutter_run(
                white_px,
                "v",
                expected_mid=mid_x,
                perp_lo=sy0,
                perp_hi=sy1,
                search_lo=max(page_left + 60, mid_x - radius),
                search_hi=min(page_right - 60, mid_x + radius),
                require_bracket_walls=True,
                frame_break_bands=row_h_bands,
            )
            if gut is None:
                return None
            box_x1[idx] = gut[0] - 1

    # 4. Crop each exact frame box, peel ONLY its outer crisp black frame, then finish per-slot
    extracted: list[Image.Image] = []
    for idx in range(len(spec.slots)):
        cx0 = max(0, min(w - 32, box_x0[idx]))
        cy0 = max(0, min(h - 32, box_y0[idx]))
        cx1 = max(cx0 + 32, min(w, box_x1[idx] + 1))
        cy1 = max(cy0 + 32, min(h, box_y1[idx] + 1))
        if (cx1 - cx0) < int(spec.slots[idx].width * 0.55) or (cy1 - cy0) < int(spec.slots[idx].height * 0.55):
            return None
        cropped = page.crop((cx0, cy0, cx1, cy1))
        peeled = _peel_black_box_frame(cropped, max_frame_px=12)
        if is_fb[idx]:
            cleaned = _trim_stray_white_edge_strips(peeled, max_strip_px=10)
        else:
            trimmed = _trim_residual_edge_borders(
                peeled,
                edge_band_px=14,
                deep_rule_ratio=0.0,
                strict_dark_only=False,
            )
            cleaned = _level_near_white_bg(trimmed)
        extracted.append(cleaned)

    return extracted


def extract_panels_from_page(
    raw_page_im: Image.Image,
    layout_id: str,
    *,
    all_boxed: bool = False,
    slot_full_bleed: Sequence[bool] | None = None,
) -> list[Image.Image]:
    """Extract clean, border-stripped panel images from a generated V4 act page.

    Steps:
    1. Convert to RGB and normalize to `(V4_PAGE_W, V4_PAGE_H)` (900x1350) preserving 2:3 framing.
    2. Resolve per-slot `is_fb[i]` (`True` if `all_boxed` or `slot_full_bleed[i]`). When ALL slots
       are boxed (either `all_boxed=True` or every slot has `is_fb[i]` or `border_style == "box"`)
       and at least one slot is full-bleed (or `all_boxed=True` / `slot_full_bleed` is given):
       segment every box directly via the pure-`#FFFFFF` outer page margins & inter-panel gutters
       first (immune to dark neutral dungeon/cave interior backgrounds!).
    3. Otherwise (mixed open + box slots, clean-white mode, or fallback): detect drawn horizontal
       & vertical frame lines with wide search windows (`±140px` internal, `±56px` outer),
       corner-polarity disambiguation, and adjacent-slot coupling.
    4. Finish each extracted panel `i` strictly according to `is_fb[i]`:
       - `is_fb[i] == True`: peel crisp `#141414` black frame (`_peel_black_box_frame`) and trim
         stray thin white strips (`<= 10px`), preserving 100% edge-to-edge full-bleed color pixels
         (NO `_level_near_white_bg`, NO 20% dark-interior chopper!).
       - `is_fb[i] == False`: strip residual edge borders and apply `_level_near_white_bg` for
         crisp pure `#FFFFFF`.
    """
    spec = get_page_layout(layout_id)
    if slot_full_bleed is not None and len(slot_full_bleed) != len(spec.slots):
        raise ValueError(
            f"slot_full_bleed length ({len(slot_full_bleed)}) must match layout '{layout_id}' "
            f"panel count ({len(spec.slots)})."
        )

    is_fb: list[bool] = (
        [True if all_boxed else bool(v) for v in slot_full_bleed]
        if slot_full_bleed is not None
        else [bool(all_boxed)] * len(spec.slots)
    )
    eff_styles: list[Literal["open", "box"]] = [
        "box" if (all_boxed or is_fb[i] or s.border_style == "box") else "open"
        for i, s in enumerate(spec.slots)
    ]
    all_slots_boxed = all(st == "box" for st in eff_styles)

    page = _normalize_page_to_canvas(raw_page_im)
    if all_slots_boxed and (all_boxed or any(is_fb) or slot_full_bleed is not None):
        white_gutter_panels = _extract_all_boxed_panels(page, spec, slot_full_bleed=is_fb)
        if white_gutter_panels is not None:
            return white_gutter_panels

    arr = np.asarray(page)
    h, w, _ = arr.shape

    cmin = arr.min(axis=2)
    cmax = arr.max(axis=2)
    chroma = cmax - cmin
    line_mask = (chroma <= 42) & (cmin <= 215)
    dark_mask = (chroma <= 42) & (cmin <= 145)
    strict_black_mask = (chroma <= 24) & (cmax <= 55)

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
        eff_style = eff_styles[idx]
        slot_fb = is_fb[idx]
        nb = all_neighbors[idx]
        top_r = _internal_search_radius(slot, nb["top"], "h")
        bot_r = _internal_search_radius(slot, nb["bottom"], "h")

        top_clamp = (140, h - 180) if nb["top"] else (0, min(h - 1, y0 + 80))
        bot_clamp = (180, h - 140) if nb["bottom"] else (max(0, y1 - 80), h - 1)

        if all_boxed or slot_fb:
            # Full-bleed boxed panels have crisp #141414 frames that stand out cleanly from
            # dark neutral cave/stone interiors in `strict_black_mask`; fall back to `line_mask`.
            top_run = _detect_horizontal_border(
                strict_black_mask, strict_black_mask, y0, slot.rect, "top", "box",
                search_radius=top_r, clamp_bounds=top_clamp,
            )
            if top_run is None:
                top_run = _detect_horizontal_border(
                    line_mask, dark_mask, y0, slot.rect, "top", eff_style,
                    search_radius=top_r, clamp_bounds=top_clamp,
                )

            bot_run = _detect_horizontal_border(
                strict_black_mask, strict_black_mask, y1, slot.rect, "bottom", "box",
                search_radius=bot_r, clamp_bounds=bot_clamp,
            )
            if bot_run is None:
                bot_run = _detect_horizontal_border(
                    line_mask, dark_mask, y1, slot.rect, "bottom", eff_style,
                    search_radius=bot_r, clamp_bounds=bot_clamp,
                )
        else:
            top_run = _detect_horizontal_border(
                line_mask, dark_mask, y0, slot.rect, "top", eff_style,
                search_radius=top_r, clamp_bounds=top_clamp,
            )
            bot_run = _detect_horizontal_border(
                line_mask, dark_mask, y1, slot.rect, "bottom", eff_style,
                search_radius=bot_r, clamp_bounds=bot_clamp,
            )

        snapped_bounds.append({"left": None, "right": None, "top": top_run, "bottom": bot_run})

    # Sync row-mate box horizontal borders if one sibling detected a strong divider and another missed it
    for idx, slot in enumerate(spec.slots):
        if eff_styles[idx] != "box":
            continue
        b = snapped_bounds[idx]
        for side in ("top", "bottom"):
            if b[side] is not None:
                continue
            ref_coord = slot.rect[1] if side == "top" else slot.rect[3]
            for other_idx, other in enumerate(spec.slots):
                if other_idx == idx or eff_styles[other_idx] != "box":
                    continue
                other_coord = other.rect[1] if side == "top" else other.rect[3]
                if abs(other_coord - ref_coord) <= 6 and snapped_bounds[other_idx][side] is not None:
                    b[side] = snapped_bounds[other_idx][side]
                    break

    # Stage 2: Detect vertical borders using the snapped horizontal span (eff_y0..eff_y1)
    for idx, slot in enumerate(spec.slots):
        x0, y0, x1, y1 = slot.rect
        eff_style = eff_styles[idx]
        slot_fb = is_fb[idx]
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

        if all_boxed or slot_fb:
            b["left"] = _detect_vertical_border(
                strict_black_mask, strict_black_mask, x0, eff_rect, "left", "box",
                search_radius=left_r, clamp_bounds=left_clamp,
            )
            if b["left"] is None:
                b["left"] = _detect_vertical_border(
                    line_mask, dark_mask, x0, eff_rect, "left", eff_style,
                    search_radius=left_r, clamp_bounds=left_clamp,
                )

            b["right"] = _detect_vertical_border(
                strict_black_mask, strict_black_mask, x1, eff_rect, "right", "box",
                search_radius=right_r, clamp_bounds=right_clamp,
            )
            if b["right"] is None:
                b["right"] = _detect_vertical_border(
                    line_mask, dark_mask, x1, eff_rect, "right", eff_style,
                    search_radius=right_r, clamp_bounds=right_clamp,
                )
        else:
            b["left"] = _detect_vertical_border(
                line_mask, dark_mask, x0, eff_rect, "left", eff_style,
                search_radius=left_r, clamp_bounds=left_clamp,
            )
            b["right"] = _detect_vertical_border(
                line_mask, dark_mask, x1, eff_rect, "right", eff_style,
                search_radius=right_r, clamp_bounds=right_clamp,
            )

    # Sync column-mate box vertical borders if one sibling missed it
    for idx, slot in enumerate(spec.slots):
        if eff_styles[idx] != "box":
            continue
        b = snapped_bounds[idx]
        for side in ("left", "right"):
            if b[side] is not None:
                continue
            ref_coord = slot.rect[0] if side == "left" else slot.rect[2]
            for other_idx, other in enumerate(spec.slots):
                if other_idx == idx or eff_styles[other_idx] != "box":
                    continue
                other_coord = other.rect[0] if side == "left" else other.rect[2]
                if abs(other_coord - ref_coord) <= 6 and snapped_bounds[other_idx][side] is not None:
                    b[side] = snapped_bounds[other_idx][side]
                    break

    # Stage 3: Crop cleanly inside snapped borders & couple adjacent open/box slots to real dividers
    extracted: list[Image.Image] = []
    for idx, slot in enumerate(spec.slots):
        x0, y0, x1, y1 = slot.rect
        eff_style = eff_styles[idx]
        slot_fb = is_fb[idx]
        b = snapped_bounds[idx]
        nb = all_neighbors[idx]

        if slot_fb:
            # Include the detected crisp black box frame so `_peel_black_box_frame` peels ONLY
            # the black frame + 2px AA without over-cropping or touching dark interior art.
            cx0 = b["left"][0] if b["left"] is not None else x0
            cx1 = (b["right"][1] + 1) if b["right"] is not None else (x1 + 1)
            cy0 = b["top"][0] if b["top"] is not None else y0
            cy1 = (b["bottom"][1] + 1) if b["bottom"] is not None else (y1 + 1)
        else:
            inset_lo = 6
            inset_hi = 5
            # Open outer page edges with no drawn border keep generous margin so protruding props stay intact
            if b["left"] is not None:
                cx0 = b["left"][1] + inset_lo
            elif eff_style == "open" and not nb["left"]:
                cx0 = 4
            else:
                cx0 = x0 + 8

            if b["right"] is not None:
                cx1 = b["right"][0] - inset_hi
            elif eff_style == "open" and not nb["right"]:
                cx1 = w - 4
            else:
                cx1 = x1 - 8

            if b["top"] is not None:
                cy0 = b["top"][1] + inset_lo
            elif eff_style == "open" and not nb["top"]:
                cy0 = 4
            else:
                cy0 = y0 + 8

            if b["bottom"] is not None:
                cy1 = b["bottom"][0] - inset_hi
            elif eff_style == "open" and not nb["bottom"]:
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
                if eff_style == "open":
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
                if eff_style == "open":
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
                if eff_style == "open":
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
                if eff_style == "open":
                    cx0 = real_divider_x + 4
                else:
                    cx0 = max(cx0, real_divider_x + 5)

        cx0 = max(0, min(w - 32, cx0))
        cy0 = max(0, min(h - 32, cy0))
        cx1 = max(cx0 + 32, min(w, cx1))
        cy1 = max(cy0 + 32, min(h, cy1))

        cropped = page.crop((cx0, cy0, cx1, cy1))
        if slot_fb:
            peeled = _peel_black_box_frame(cropped, max_frame_px=12)
            cleaned = _trim_stray_white_edge_strips(peeled, max_strip_px=10)
        else:
            trimmed = _trim_residual_edge_borders(
                cropped,
                edge_band_px=14,
                deep_rule_ratio=0.20,
                strict_dark_only=False,
            )
            cleaned = _level_near_white_bg(trimmed)
        extracted.append(cleaned)

    return extracted
