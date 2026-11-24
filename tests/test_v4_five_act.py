"""Adversarial end-to-end test suite for V4 5-act variable-layout & page-batch pipeline."""

from __future__ import annotations

import base64
import io
import json
import re
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.parse import urlsplit

import numpy as np
import pytest
from PIL import Image, ImageDraw
from pydantic import ValidationError

from wow_sloptoon import artist, cli, composer, writer
from wow_sloptoon.cast import resolve_cast_member
from wow_sloptoon.composer import (
    HEADER_H,
    PAGE_W,
    THUMB_SIZE,
    WATERMARK_FOOTER_H,
    ComposeResult,
    compose_episode,
    compose_v4_episode,
)
from wow_sloptoon.config import DEFAULT_IMAGE_MODEL, DEFAULT_TEXT_MODEL, load_settings
from wow_sloptoon.item_tooltip import ItemTooltipSpec
from wow_sloptoon.layouts import (
    PAGE_LAYOUTS,
    V4_ASPECT_RATIO,
    V4_PAGE_H,
    V4_PAGE_W,
    PageLayoutSpec,
    PanelSlotSpec,
    extract_panels_from_page,
    get_page_layout,
    render_layout_blueprint,
)
from wow_sloptoon.models import ActPage, ComicCut, EpisodeRecord, EpisodeScript, GalleryPost
from wow_sloptoon.site_builder import DC_GALLERY_WRITE_URL, build_static_site

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_HREF_SRC_RE = re.compile(r"""(?:href|src)=["']([^"']+)["']""")

EXPECTED_LAYOUT_RECTS: dict[str, list[tuple[tuple[int, int, int, int], str]]] = {
    "open_top_split_bottom": [
        ((28, 20, 872, 650), "open"),
        ((28, 678, 438, 1326), "box"),
        ((462, 678, 872, 1326), "box"),
    ],
    "split_top_wide_bottom": [
        ((28, 24, 438, 650), "box"),
        ((462, 24, 872, 650), "box"),
        ((28, 676, 872, 1326), "box"),
    ],
    "diagonal_tempo_2cut": [
        ((28, 20, 872, 740), "open"),
        ((28, 768, 872, 1326), "box"),
    ],
    "impact_freeze_2cut": [
        ((28, 24, 872, 496), "box"),
        ((28, 524, 872, 1326), "box"),
    ],
    "wide_reaction_wide": [
        ((28, 24, 872, 464), "box"),
        ((28, 488, 872, 898), "box"),
        ((28, 922, 872, 1326), "box"),
    ],
    "four_beat_gag": [
        ((28, 24, 438, 662), "box"),
        ((462, 24, 872, 662), "box"),
        ((28, 688, 438, 1326), "box"),
        ((462, 688, 872, 1326), "box"),
    ],
}

# Distinct high-saturation signature RGB colors for verifying panel isolation
_SLOT_COLORS: tuple[tuple[int, int, int], ...] = (
    (220, 48, 48),   # red
    (44, 178, 68),   # green
    (46, 108, 224),  # blue
    (224, 152, 28),  # amber
)


def _sample_post(post_no: str = "99001") -> GalleryPost:
    return GalleryPost(
        post_no=post_no,
        title="붉은십자군 도서관에서 탱커가 지능 지팡이 입찰한 썰",
        url=f"https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no={post_no}",
        author="포에버갤러",
        date_str="2026-11-24 12:00:00",
        views=2400,
        recommends=88,
        comments_count=41,
        body=(
            "붉은십자군 도서관 막넴 잡고 사서의 홀 나왔는데 탱커가 지능 붙었으니 "
            "무기 숙련 빨리 올린다고 주사위 입찰 눌러버림 ㅋㅋ 힐러랑 법사 10초 정적 흐르고 파티 터짐"
        ),
        comments=[
            "무기숙련은 지능 영향 맞긴 한데 그걸 거기서 굴리냐 ㅋㅋ",
            "힐러 영혼 가출했을 듯",
            "냥꾼이 옆에서 팝콘 씹으면서 다 내 무기라고 했겠네",
        ],
    )


def _make_v4_cut(
    idx: int,
    *,
    characters: list[str] | None = None,
    speaker: str | None = "나이트엘프 사제",
    dialogue: str | None = "저기요, 그거 힐러 지팡이인데요?!",
    wordless: bool = False,
    tail_target: str = "left",
    visual_prompt: str | None = None,
    item_tooltip: ItemTooltipSpec | None = None,
    act_number: int | None = None,
    panel_index: int | None = None,
) -> ComicCut:
    chars = characters or ["나이트엘프 사제", "오크 전사"]
    return ComicCut(
        cut_index=idx,
        aspect_ratio="auto",
        layout_slot="panel",
        act_number=act_number,
        panel_index=panel_index,
        characters=chars,
        speaker=None if wordless else speaker,
        dialogue=None if wordless else dialogue,
        wordless=wordless,
        visual_prompt=visual_prompt
        or (
            "Over-the-shoulder dynamic chibi gag scene on pure solid white #FFFFFF background, "
            "no text, no speech bubbles."
        ),
        tail_target="center" if wordless else tail_target,
        item_tooltip=item_tooltip,
    )


def _build_custom_v4_script(
    layout_ids: list[str],
    *,
    include_wordless: bool = True,
    with_tooltips: bool = False,
    long_dialogues: bool = False,
) -> EpisodeScript:
    """Build a valid 5-act V4 EpisodeScript using arbitrary 5 layout_ids."""
    assert len(layout_ids) == 5
    acts: list[ActPage] = []
    running_cut = 1
    prompts_cycle = [
        "Over-the-shoulder dynamic foreground view of Night Elf Priest pointing at loot chest, pure #FFFFFF white background.",
        "Low-angle heroic pose of Orc Warrior holding a sturdy steel shield and 1H axe, pure #FFFFFF white background.",
        "Side-profile frantic dashing action of Gnome Rogue sneaking behind loot pile, pure #FFFFFF white background.",
        "High-angle dramatic wide shot of Skyborne Mage staring in utter disbelief, pure #FFFFFF white background.",
        "Dutch-tilt chaotic slapstick reaction with Dwarf Hunter crouching and munching popcorn, pure #FFFFFF white background.",
    ]
    cast_pairs = [
        (["나이트엘프 사제", "오크 전사"], "나이트엘프 사제", "left"),
        (["오크 전사"], "오크 전사", "right"),
        (["노움 도적", "스카이본 마법사"], "노움 도적", "left"),
        (["스카이본 마법사"], "스카이본 마법사", "center"),
    ]
    total_planned = sum(get_page_layout(lid).panel_count for lid in layout_ids)
    wordless_target_act = 4

    for act_num, lid in enumerate(layout_ids, start=1):
        spec = get_page_layout(lid)
        act_cuts: list[ComicCut] = []
        for slot in spec.slots:
            is_wordless = (
                include_wordless
                and act_num == wordless_target_act
                and slot.slot_index == spec.panel_count
            )
            chars, spk, tail = cast_pairs[(running_cut - 1) % len(cast_pairs)]
            if is_wordless:
                chars = ["스카이본 마법사"]
                spk = None
                tail = "center"

            dlg: str | None
            if is_wordless:
                dlg = None
            elif long_dialogues:
                dlg = (
                    f"{act_num}막 {slot.slot_index}컷 아주 길고 시끄러운 던전 입찰 항의 대사! "
                    "이 지팡이는 힐러랑 캐스터 전용인데 전탱님이 주사위 굴리면 파티가 터져요!!"
                )
            else:
                dlg = f"{act_num}막 {slot.slot_index}컷!\n저거 힐러 템인데\n왜 입찰을 눌러요?!"

            tip: ItemTooltipSpec | None = None
            if with_tooltips and (
                (act_num == 1 and slot.slot_index == 1)
                or (act_num == 2 and slot.slot_index == 1)
                or (act_num == 3 and slot.slot_index == 2)
                or (act_num == 5 and slot.slot_index == spec.panel_count)
            ):
                tip = (
                    ItemTooltipSpec(
                        image_path="assets/items/scepter_of_the_librarian.png",
                        item_name="사서의 홀",
                        quality="uncommon",
                    )
                    if act_num == 1
                    else ItemTooltipSpec(wowhead_item_id=7722)
                )

            act_cuts.append(
                _make_v4_cut(
                    running_cut,
                    characters=chars,
                    speaker=spk,
                    dialogue=dlg,
                    wordless=is_wordless,
                    tail_target=tail,
                    visual_prompt=prompts_cycle[(running_cut - 1) % len(prompts_cycle)],
                    item_tooltip=tip,
                    act_number=act_num,
                    panel_index=slot.slot_index,
                )
            )
            running_cut += 1

        acts.append(
            ActPage(
                act_number=act_num,
                act_title=f"제{act_num}막 상황 전개",
                layout_id=lid,  # type: ignore[arg-type]
                cuts=act_cuts,
            )
        )

    assert running_cut - 1 == total_planned
    post = _sample_post()
    return EpisodeScript(
        episode_number=11,
        source_post_no=post.post_no,
        source_title=post.title,
        source_url=post.url,
        subtitle="붉은십자군 도서관 지능 지팡이 입찰 대참사 5막극",
        layout_mode="v4_five_act",
        acts=acts,
    )


def _assert_pure_white_outer_border(image_path: Path, margin: int = 2) -> None:
    with Image.open(image_path) as im:
        arr = np.asarray(im.convert("RGB"))
    h, w, _ = arr.shape
    assert np.all(arr[:margin, :, :] == 255), f"Top border not pure white in {image_path.name}"
    assert np.all(arr[h - margin :, :, :] == 255), f"Bottom border not pure white in {image_path.name}"
    assert np.all(arr[:, :margin, :] == 255), f"Left border not pure white in {image_path.name}"
    assert np.all(arr[:, w - margin :, :] == 255), f"Right border not pure white in {image_path.name}"


def _make_synthetic_raw_v4_page(
    layout_id: str,
    *,
    size: tuple[int, int] = (V4_PAGE_W, V4_PAGE_H),
    drift_xy: tuple[int, int] = (0, 0),
    border_width: int = 5,
    full_bleed_panels: bool = False,
    offwhite_bg: tuple[int, int, int] = (250, 249, 248),
    open_slot_border: str = "gray",
) -> Image.Image:
    """Create a synthetic AI-generated 2:3 multi-panel page image for extraction/composition tests."""
    spec = get_page_layout(layout_id)
    w, h = size
    sx = w / V4_PAGE_W
    sy = h / V4_PAGE_H
    dx, dy = drift_xy

    im = Image.new("RGB", (w, h), offwhite_bg)
    draw = ImageDraw.Draw(im)

    for idx, slot in enumerate(spec.slots):
        x0 = max(6, min(w - 20, int(round((slot.rect[0] + dx) * sx))))
        y0 = max(6, min(h - 20, int(round((slot.rect[1] + dy) * sy))))
        x1 = max(x0 + 40, min(w - 6, int(round((slot.rect[2] + dx) * sx))))
        y1 = max(y0 + 40, min(h - 6, int(round((slot.rect[3] + dy) * sy))))

        pw = x1 - x0
        ph = y1 - y0
        color = _SLOT_COLORS[idx % len(_SLOT_COLORS)]

        if full_bleed_panels:
            # Fill interior right up to the border with dense saturated color + character circle
            inset = max(4, border_width)
            draw.rectangle([x0 + inset, y0 + inset, x1 - inset, y1 - inset], fill=color)
            draw.ellipse(
                [x0 + pw // 4, y0 + ph // 4, x0 + (3 * pw) // 4, y0 + (3 * ph) // 4],
                fill=(245, 210, 130),
                outline=(25, 25, 25),
                width=4,
            )
        else:
            # Realistic chibi figure positioned in lower-middle 55% of panel, pure headroom on top
            cx0 = x0 + int(pw * 0.24)
            cx1 = x0 + int(pw * 0.76)
            cy0 = y0 + int(ph * 0.38)
            cy1 = y0 + int(ph * 0.88)
            draw.ellipse([cx0, cy0, cx1, cy0 + int((cy1 - cy0) * 0.58)], fill=color, outline=(24, 24, 24), width=4)
            draw.rectangle(
                [cx0 + int((cx1 - cx0) * 0.12), cy0 + int((cy1 - cy0) * 0.48), cx1 - int((cx1 - cx0) * 0.12), cy1],
                fill=color,
                outline=(24, 24, 24),
                width=4,
            )

        # Draw panel borders (dark crisp frame for box; configurable for open)
        if slot.border_style == "box":
            draw.rectangle([x0, y0, x1, y1], outline=(18, 18, 18), width=border_width)
        elif open_slot_border == "gray":
            draw.rectangle([x0, y0, x1, y1], outline=(176, 176, 176), width=max(2, border_width - 1))
        elif open_slot_border == "dark":
            draw.rectangle([x0, y0, x1, y1], outline=(24, 24, 24), width=border_width)
        # else "none": borderless open panel

    return im


def _count_color_match(arr: np.ndarray, target_rgb: tuple[int, int, int], tol: int = 35) -> int:
    diff = np.abs(arr.astype(np.int16) - np.array(target_rgb, dtype=np.int16))
    return int(np.sum(np.all(diff <= tol, axis=2)))


def _assert_internal_links_resolve(html_path: Path) -> None:
    content = html_path.read_text(encoding="utf-8")
    matches = _HREF_SRC_RE.findall(content)
    assert matches, f"No href/src attributes found in {html_path}"
    for raw_ref in matches:
        ref = raw_ref.strip()
        if (
            not ref
            or ref.startswith("#")
            or ref.startswith("http://")
            or ref.startswith("https://")
            or ref.startswith("mailto:")
            or ref.startswith("data:")
        ):
            continue
        clean_path = urlsplit(ref).path
        if not clean_path:
            continue
        target = (html_path.parent / clean_path).resolve()
        assert target.exists(), f"Broken local reference '{raw_ref}' in {html_path} -> {target}"
        assert target.is_file() and target.stat().st_size > 0


# ---------------------------------------------------------------------------
# 1. layouts.py: geometry, blueprints, and drifted panel extraction
# ---------------------------------------------------------------------------


def test_page_layouts_geometry_non_overlapping_and_contract() -> None:
    assert V4_PAGE_W == 900
    assert V4_PAGE_H == 1350
    assert V4_ASPECT_RATIO == "2:3"
    assert set(PAGE_LAYOUTS.keys()) == set(EXPECTED_LAYOUT_RECTS.keys())
    assert len(PAGE_LAYOUTS) == 6

    with pytest.raises(ValueError):
        get_page_layout("nonexistent_layout")

    for layout_id, expected_slots in EXPECTED_LAYOUT_RECTS.items():
        spec = get_page_layout(layout_id)
        assert isinstance(spec, PageLayoutSpec)
        assert spec.layout_id == layout_id
        assert spec.panel_count == len(expected_slots) == len(spec.slots)
        assert spec.description.strip()

        rects: list[tuple[int, int, int, int]] = []
        for idx, (slot, (exp_rect, exp_border)) in enumerate(zip(spec.slots, expected_slots), start=1):
            assert isinstance(slot, PanelSlotSpec)
            assert slot.slot_index == idx
            assert slot.rect == exp_rect
            assert slot.border_style == exp_border
            assert slot.position_label.strip()
            assert slot.bubble_hint.strip()

            x0, y0, x1, y1 = slot.rect
            assert 20 <= x0 < x1 <= V4_PAGE_W - 20
            assert 20 <= y0 < y1 <= V4_PAGE_H - 20
            assert slot.width == x1 - x0
            assert slot.height == y1 - y0
            assert slot.is_narrow is (slot.width < 580)
            rects.append(slot.rect)

        # Pairwise non-overlap + positive gutter check
        for i in range(len(rects)):
            for j in range(i + 1, len(rects)):
                ax0, ay0, ax1, ay1 = rects[i]
                bx0, by0, bx1, by1 = rects[j]
                inter_w = max(0, min(ax1, bx1) - max(ax0, bx0))
                inter_h = max(0, min(ay1, by1) - max(ay0, by0))
                assert inter_w * inter_h == 0, f"Overlapping slots {i + 1} & {j + 1} in {layout_id}"
                gap_x = max(bx0 - ax1, ax0 - bx1)
                gap_y = max(by0 - ay1, ay0 - by1)
                assert max(gap_x, gap_y) >= 20, f"Too-thin gutter between slots {i + 1} & {j + 1} in {layout_id}"


@pytest.mark.parametrize("layout_id", list(EXPECTED_LAYOUT_RECTS.keys()))
def test_render_layout_blueprint_pure_white_outer_border_and_zero_text(layout_id: str) -> None:
    bp = render_layout_blueprint(layout_id)
    assert bp.size == (V4_PAGE_W, V4_PAGE_H)
    assert bp.mode == "RGB"
    arr = np.asarray(bp)

    # Outer 16px margin around the entire 900x1350 blueprint must be 100% pure white
    assert np.all(arr[:16, :, :] == 255)
    assert np.all(arr[-16:, :, :] == 255)
    assert np.all(arr[:, :16, :] == 255)
    assert np.all(arr[:, -16:, :] == 255)

    spec = get_page_layout(layout_id)
    for slot in spec.slots:
        x0, y0, x1, y1 = slot.rect
        # Deep interior of every slot must be 100% pure white -> guarantees ZERO text/numbers/labels!
        interior = arr[y0 + 12 : y1 - 12, x0 + 12 : x1 - 12, :]
        assert np.all(interior == 255), f"Unexpected interior ink/label inside {layout_id} slot {slot.slot_index}"

        # Border region along top edge must contain expected guide or box stroke
        top_band = arr[max(0, y0 - 4) : y0 + 6, x0 + 20 : x1 - 20, :]
        if slot.border_style == "box":
            dark_px = np.sum((top_band[:, :, 0] < 40) & (top_band[:, :, 1] < 40) & (top_band[:, :, 2] < 40))
            assert dark_px > 200, f"Missing dark box border in {layout_id} slot {slot.slot_index}"
        else:
            gray_px = np.sum(
                (top_band[:, :, 0] < 210) & (top_band[:, :, 0] > 120)
                & (np.abs(top_band[:, :, 0].astype(int) - top_band[:, :, 2].astype(int)) < 15)
            )
            assert gray_px > 150, f"Missing subtle gray guide border for open slot in {layout_id}"

    # Scaled blueprint size works cleanly
    scaled = render_layout_blueprint(layout_id, size=(450, 675))
    assert scaled.size == (450, 675)


@pytest.mark.parametrize("layout_id", list(EXPECTED_LAYOUT_RECTS.keys()))
@pytest.mark.parametrize(
    "case_name,page_size,drift_xy",
    [
        ("exact_900x1350", (900, 1350), (0, 0)),
        ("exact_2k_1365x2048", (1365, 2048), (0, 0)),
        ("drifted_plus18_minus16", (1365, 2048), (18, -16)),
        ("drifted_minus17_plus15", (900, 1350), (-17, 15)),
    ],
)
def test_extract_panels_from_page_exact_and_drifted_strips_borders_preserves_art(
    layout_id: str,
    case_name: str,
    page_size: tuple[int, int],
    drift_xy: tuple[int, int],
) -> None:
    spec = get_page_layout(layout_id)
    raw_page = _make_synthetic_raw_v4_page(
        layout_id,
        size=page_size,
        drift_xy=drift_xy,
        border_width=6,
        offwhite_bg=(249, 248, 247),
    )

    panels = extract_panels_from_page(raw_page, layout_id)
    assert len(panels) == spec.panel_count

    for idx, (panel, slot) in enumerate(zip(panels, spec.slots)):
        assert panel.mode == "RGB"
        pw, ph = panel.size
        assert pw >= int(slot.width * 0.70), f"{layout_id} ({case_name}) panel {idx + 1} width collapsed: {pw}"
        assert ph >= int(slot.height * 0.70), f"{layout_id} ({case_name}) panel {idx + 1} height collapsed: {ph}"

        arr = np.asarray(panel)
        # Outer 2px border of each extracted panel must NOT contain leftover straight dark/gray border bars
        for edge_name, strip in (
            ("top", arr[:2, :, :]),
            ("bottom", arr[-2:, :, :]),
            ("left", arr[:, :2, :]),
            ("right", arr[:, -2:, :]),
        ):
            non_white_ratio = float(np.mean(np.any(strip < 240, axis=2)))
            assert non_white_ratio < 0.25, (
                f"Residual border line on {edge_name} edge of {layout_id} ({case_name}) "
                f"slot {idx + 1}: ratio={non_white_ratio:.2f}"
            )

        # Verify pure #FFFFFF background normalization on top headroom band
        headroom = arr[4 : min(24, ph - 4), pw // 4 : (3 * pw) // 4, :]
        assert float(np.mean(np.all(headroom == 255, axis=2))) > 0.90

        # Own distinct color artwork survived intact; neighbor slots' colors did not leak in
        own_color = _SLOT_COLORS[idx % len(_SLOT_COLORS)]
        own_px = _count_color_match(arr, own_color)
        assert own_px > 1200, f"Inner artwork lost in {layout_id} ({case_name}) slot {idx + 1}: {own_px}px"

        for other_idx in range(spec.panel_count):
            if other_idx == idx:
                continue
            other_color = _SLOT_COLORS[other_idx % len(_SLOT_COLORS)]
            leaked_px = _count_color_match(arr, other_color)
            assert leaked_px < 50, (
                f"Neighbor slot {other_idx + 1} leaked ({leaked_px}px) into slot {idx + 1} of {layout_id} ({case_name})"
            )


@pytest.mark.parametrize("open_slot_border", ["none", "dark"])
@pytest.mark.parametrize("layout_id", ["open_top_split_bottom", "diagonal_tempo_2cut"])
def test_extract_panels_handles_borderless_or_accidental_dark_open_slots_and_rgba(
    layout_id: str, open_slot_border: str
) -> None:
    raw = _make_synthetic_raw_v4_page(
        layout_id,
        size=(1024, 1536),
        drift_xy=(10, -10),
        open_slot_border=open_slot_border,
    ).convert("RGBA")
    panels = extract_panels_from_page(raw, layout_id)
    spec = get_page_layout(layout_id)
    assert len(panels) == spec.panel_count
    for idx, panel in enumerate(panels):
        assert panel.mode == "RGB"
        arr = np.asarray(panel)
        own_px = _count_color_match(arr, _SLOT_COLORS[idx % len(_SLOT_COLORS)])
        assert own_px > 1200, f"Artwork clipped on {layout_id} ({open_slot_border}) slot {idx + 1}"
        # Even when AI accidentally drew dark box around open slot, outer 2px edges must be stripped clean
        for edge_name, strip in (
            ("top", arr[:2, :, :]),
            ("bottom", arr[-2:, :, :]),
            ("left", arr[:, :2, :]),
            ("right", arr[:, -2:, :]),
        ):
            assert float(np.mean(np.any(strip < 240, axis=2))) < 0.25, (
                f"Unstripped {edge_name} border on {layout_id} ({open_slot_border}) slot {idx + 1}"
            )


def test_extract_panels_handles_large_86px_mid_divider_drift_zero_bleed() -> None:
    """Regression test: when AI draws open_top_split_bottom's bottom box border ~86px lower
    (y=764 instead of 678), P1 keeps its full lower artwork and P2/P3 have zero P1 bleed
    and zero floating horizontal black frame lines inside their top 22%."""
    w, h = 1365, 2048
    sx, sy = w / float(V4_PAGE_W), h / float(V4_PAGE_H)
    im = Image.new("RGB", (w, h), (251, 250, 249))
    draw = ImageDraw.Draw(im)

    # P1 (open top) extends down to y=746 (skirt/book artwork sitting inside y=660..746!)
    p1_art = (int(120 * sx), int(260 * sy), int(780 * sx), int(744 * sy))
    draw.rectangle(p1_art, fill=_SLOT_COLORS[0], outline=(24, 24, 24), width=4)
    # Extra lower skirt/book fragment specifically in the drift zone (y=680..742)
    p1_lower = (int(220 * sx), int(680 * sy), int(680 * sx), int(742 * sy))
    draw.rectangle(p1_lower, fill=(240, 20, 140))

    # Bottom split boxes start at y=764 (+86px downward drift from 678!)
    p2_rect = (int(28 * sx), int(764 * sy), int(438 * sx), int(1326 * sy))
    p3_rect = (int(462 * sx), int(764 * sy), int(872 * sx), int(1326 * sy))

    # Draw P2 (green) and P3 (blue) artwork strictly inside the drifted boxes
    draw.ellipse(
        [int(110 * sx), int(940 * sy), int(360 * sx), int(1260 * sy)],
        fill=_SLOT_COLORS[1],
        outline=(24, 24, 24),
        width=4,
    )
    draw.ellipse(
        [int(540 * sx), int(940 * sy), int(790 * sx), int(1260 * sy)],
        fill=_SLOT_COLORS[2],
        outline=(24, 24, 24),
        width=4,
    )
    # Crisp dark box borders at drifted y=764
    draw.rectangle(p2_rect, outline=(16, 16, 16), width=6)
    draw.rectangle(p3_rect, outline=(16, 16, 16), width=6)

    panels = extract_panels_from_page(im, "open_top_split_bottom")
    assert len(panels) == 3

    # P1 must retain the lower skirt/book fragment (magenta pixels) from y=680..742!
    arr1 = np.asarray(panels[0])
    lower_skirt_px = _count_color_match(arr1, (240, 20, 140), tol=35)
    assert lower_skirt_px > 4000, f"P1 lower artwork (y=680..742) was clipped! Only {lower_skirt_px}px survived"

    # P2 & P3 must have ZERO P1 red/magenta bleed AND zero floating horizontal dark lines in top 22%
    for idx, (panel, own_rgb) in enumerate(((panels[1], _SLOT_COLORS[1]), (panels[2], _SLOT_COLORS[2])), start=2):
        arr = np.asarray(panel)
        assert _count_color_match(arr, _SLOT_COLORS[0], tol=35) < 30, f"P1 red art bled into P{idx}"
        assert _count_color_match(arr, (240, 20, 140), tol=35) < 30, f"P1 lower skirt bled into P{idx}"
        assert _count_color_match(arr, own_rgb, tol=35) > 1500, f"P{idx} own artwork lost"

        top_zone = arr[: max(10, int(arr.shape[0] * 0.22)), :, :]
        dark_row_cov = np.mean((top_zone[:, :, 0] < 80) & (top_zone[:, :, 1] < 80) & (top_zone[:, :, 2] < 80), axis=1)
        assert float(dark_row_cov.max()) < 0.50, (
            f"Floating horizontal dark frame line leaked into top 22% of P{idx}: max_cov={float(dark_row_cov.max()):.2f}"
        )

    # Also verify -95px upward horizontal drift + +65px center vertical shift on split_top_wide_bottom
    im2 = Image.new("RGB", (V4_PAGE_W, V4_PAGE_H), (250, 250, 250))
    d2 = ImageDraw.Draw(im2)
    d2.ellipse([100, 200, 440, 500], fill=_SLOT_COLORS[0])
    d2.ellipse([580, 200, 820, 500], fill=_SLOT_COLORS[1])
    d2.ellipse([160, 620, 740, 1250], fill=_SLOT_COLORS[2])
    d2.rectangle([28, 24, 503, 555], outline=(16, 16, 16), width=5)
    d2.rectangle([527, 24, 872, 555], outline=(16, 16, 16), width=5)
    d2.rectangle([28, 581, 872, 1326], outline=(16, 16, 16), width=5)

    split_panels = extract_panels_from_page(im2, "split_top_wide_bottom")
    assert len(split_panels) == 3
    for i, sp in enumerate(split_panels):
        sa = np.asarray(sp)
        assert _count_color_match(sa, _SLOT_COLORS[i], tol=35) > 2000
        for j in range(3):
            if j != i:
                assert _count_color_match(sa, _SLOT_COLORS[j], tol=35) < 20


# ---------------------------------------------------------------------------
# 2. models.py: ActPage & EpisodeScript V4 vs classic validation
# ---------------------------------------------------------------------------


def test_v4_models_validation_and_classic_backward_compatibility() -> None:
    # Valid V4 scripts at 10, 13, 14 cuts
    for layouts, exp_cuts in (
        (["diagonal_tempo_2cut", "impact_freeze_2cut", "diagonal_tempo_2cut", "impact_freeze_2cut", "diagonal_tempo_2cut"], 10),
        (["open_top_split_bottom", "wide_reaction_wide", "split_top_wide_bottom", "impact_freeze_2cut", "diagonal_tempo_2cut"], 13),
        (["open_top_split_bottom", "four_beat_gag", "wide_reaction_wide", "impact_freeze_2cut", "diagonal_tempo_2cut"], 14),
    ):
        script = _build_custom_v4_script(layouts)
        assert script.layout_mode == "v4_five_act"
        assert script.acts is not None and len(script.acts) == 5
        assert len(script.cuts) == exp_cuts
        assert [c.cut_index for c in script.cuts] == list(range(1, exp_cuts + 1))
        assert all(c.act_number is not None and 1 <= c.act_number <= 5 for c in script.cuts)
        assert all(c.panel_index is not None and c.panel_index >= 1 for c in script.cuts)

        # JSON round-trip preserves everything
        reloaded = EpisodeScript.model_validate_json(script.model_dump_json())
        assert reloaded.layout_mode == "v4_five_act"
        assert reloaded.acts is not None and len(reloaded.acts) == 5
        assert len(reloaded.cuts) == exp_cuts

    # Auto-inferred layout_mode when acts is supplied without explicit layout_mode
    sample_v4 = _build_custom_v4_script(
        ["open_top_split_bottom", "split_top_wide_bottom", "wide_reaction_wide", "impact_freeze_2cut", "diagonal_tempo_2cut"]
    )
    inferred = EpisodeScript(
        episode_number=12,
        source_post_no="99002",
        source_title="자동 V4 모드 추론 테스트",
        source_url="https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=99002",
        subtitle="acts 제공 시 자동 v4_five_act 설정",
        acts=sample_v4.acts,
    )
    assert inferred.layout_mode == "v4_five_act"
    assert len(inferred.cuts) == 13

    # ActPage slot count mismatch fails (open_top_split_bottom requires 3, given 2)
    with pytest.raises(ValidationError):
        ActPage(
            act_number=1,
            act_title="잘못된 슬롯 수",
            layout_id="open_top_split_bottom",
            cuts=[_make_v4_cut(1), _make_v4_cut(2)],
        )

    # ActPage out-of-range act_number fails
    with pytest.raises(ValidationError):
        ActPage(
            act_number=6,
            act_title="6막은 금지",
            layout_id="diagonal_tempo_2cut",
            cuts=[_make_v4_cut(1), _make_v4_cut(2)],
        )

    # Fewer than 5 acts fails
    with pytest.raises(ValidationError):
        EpisodeScript(
            episode_number=12,
            source_post_no="99002",
            source_title="4막은 실패",
            source_url="https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=99002",
            subtitle="실패",
            layout_mode="v4_five_act",
            acts=sample_v4.acts[:4],
        )

    # Duplicate act_numbers fail ([1, 2, 2, 4, 5])
    bad_acts = list(sample_v4.acts)
    bad_acts[2] = bad_acts[2].model_copy(update={"act_number": 2})
    with pytest.raises(ValidationError):
        EpisodeScript(
            episode_number=12,
            source_post_no="99002",
            source_title="막 번호 중복",
            source_url="https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=99002",
            subtitle="실패",
            layout_mode="v4_five_act",
            acts=bad_acts,
        )

    # V4 mode with acts=None fails
    with pytest.raises(ValidationError):
        EpisodeScript(
            episode_number=12,
            source_post_no="99002",
            source_title="acts 누락",
            source_url="https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=99002",
            subtitle="실패",
            layout_mode="v4_five_act",
            acts=None,
            cuts=[_make_v4_cut(i, wordless=(i == 10)) for i in range(1, 11)],
        )

    # > 14 total cuts in V4 fails (4 + 3 + 3 + 3 + 2 = 15 cuts)
    with pytest.raises(ValidationError):
        _build_custom_v4_script(
            ["four_beat_gag", "open_top_split_bottom", "split_top_wide_bottom", "wide_reaction_wide", "diagonal_tempo_2cut"]
        )

    # Missing wordless cut in V4 fails
    with pytest.raises(ValidationError):
        _build_custom_v4_script(
            ["open_top_split_bottom", "split_top_wide_bottom", "wide_reaction_wide", "impact_freeze_2cut", "diagonal_tempo_2cut"],
            include_wordless=False,
        )

    # Classic mode strictly unchanged: 3 cuts fail, 7 cuts fail, 12 cuts without acts fail!
    for bad_classic_n in (3, 7, 12):
        with pytest.raises(ValidationError):
            EpisodeScript(
                episode_number=3,
                source_post_no="99003",
                source_title="클래식 컷 수 위반",
                source_url="https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=99003",
                subtitle="실패",
                cuts=[
                    ComicCut(
                        cut_index=i,
                        aspect_ratio="4:3" if i % 2 else "16:9",
                        layout_slot="top" if i % 2 else "bottom",
                        characters=["오크 전사"],
                        speaker=None if i == 3 else "오크 전사",
                        dialogue=None if i == 3 else "테스트",
                        wordless=(i == 3),
                        visual_prompt="Classic cut test on pure #FFFFFF white background.",
                        tail_target="center" if i == 3 else "left",
                    )
                    for i in range(1, bad_classic_n + 1)
                ],
            )


# ---------------------------------------------------------------------------
# 3. writer.py: V4 dry-run, Interactions API generation, and quality auditor
# ---------------------------------------------------------------------------


def test_writer_v4_dry_run_and_prompt() -> None:
    post = _sample_post()
    dry = writer.build_dry_run_v4_script(post, episode_number=11)

    assert dry.layout_mode == "v4_five_act"
    assert dry.acts is not None and len(dry.acts) == 5
    assert [a.act_number for a in dry.acts] == [1, 2, 3, 4, 5]
    assert 10 <= len(dry.cuts) <= 14
    assert dry.source_title == post.title.strip()
    assert any(c.wordless for c in dry.cuts)

    # 5 distinct layouts in dry-run (no consecutive duplicates)
    layout_seq = [a.layout_id for a in dry.acts]
    assert len(set(layout_seq)) >= 4
    assert all(layout_seq[i] != layout_seq[i + 1] for i in range(4))

    # Updated Draft C turnaround rules respected (no sailor uniform, no angel halo)
    all_vp = " ".join(c.visual_prompt.lower() for c in dry.cuts)
    assert "sailor" not in all_vp
    assert "angel halo" not in all_vp

    audit = writer.audit_script_quality(dry)
    assert audit["passed"] is True, f"Dry-run V4 script failed audit: {audit['errors']}"

    prompt = writer.build_v4_writer_prompt(post, episode_number=11)
    for lid in EXPECTED_LAYOUT_RECTS:
        assert lid in prompt
    assert post.title.strip() in prompt
    assert "#FFFFFF" in prompt
    assert "wordless" in prompt


def test_writer_generate_v4_episode_script_mocked_interactions_and_normalization() -> None:
    post = _sample_post("99111")
    raw_v4 = writer.build_dry_run_v4_script(post, episode_number=15)

    # Inject character aliases inside acts AND tamper with source_title to verify normalization
    tampered_acts = []
    for act in raw_v4.acts or []:
        new_cuts = []
        for c in act.cuts:
            if c.wordless:
                new_cuts.append(c.model_copy(update={"characters": ["법사"]}))
            else:
                new_cuts.append(c.model_copy(update={"characters": ["나엘사제", "흑마"], "speaker": "나엘사제"}))
        tampered_acts.append(act.model_copy(update={"cuts": new_cuts}))
    tampered_script = raw_v4.model_copy(
        update={
            "source_title": "LLM이 임의로 바꿔버린 제목",
            "acts": tampered_acts,
            "cuts": [c for a in tampered_acts for c in a.cuts],
        }
    )

    captured: list[dict[str, Any]] = []

    class FakeInteractions:
        def create(self, **kwargs: Any) -> Any:
            captured.append(kwargs)
            return SimpleNamespace(output_text=tampered_script.model_dump_json())

    fake_client = SimpleNamespace(interactions=FakeInteractions())
    result = writer.generate_v4_episode_script(post, episode_number=15, client=fake_client)

    assert len(captured) == 1
    assert captured[0]["model"] == DEFAULT_TEXT_MODEL == "gemini-4-hydrogen"
    assert captured[0]["response_format"]["type"] == "text"
    assert captured[0]["response_format"]["mime_type"] == "application/json"
    assert "properties" in captured[0]["response_format"]["schema"]

    # Verbatim source title restored
    assert result.source_title == post.title.strip()
    assert result.layout_mode == "v4_five_act"
    assert result.acts is not None and len(result.acts) == 5

    # Both flattened result.cuts AND nested result.acts[*].cuts must be canonicalized
    for c in result.cuts:
        if c.wordless:
            assert c.characters == ["스카이본 마법사"]
            assert c.speaker is None and c.dialogue is None
        else:
            assert c.characters == ["나이트엘프 사제", "인간 흑마법사"]
            assert c.speaker == "나이트엘프 사제"

    for act in result.acts:
        for c in act.cuts:
            if c.wordless:
                assert c.characters == ["스카이본 마법사"]
            else:
                assert c.characters == ["나이트엘프 사제", "인간 흑마법사"]
                assert c.speaker == "나이트엘프 사제"


def test_audit_script_quality_v4_catches_layout_anonymity_slang_and_wordless_violations() -> None:
    clean = _build_custom_v4_script(
        ["open_top_split_bottom", "split_top_wide_bottom", "wide_reaction_wide", "impact_freeze_2cut", "diagonal_tempo_2cut"]
    )
    clean_audit = writer.audit_script_quality(clean)
    assert clean_audit["passed"] is True, clean_audit["errors"]

    # 1. Consecutive duplicate layouts must fail
    dup_consec = _build_custom_v4_script(
        ["open_top_split_bottom", "open_top_split_bottom", "wide_reaction_wide", "impact_freeze_2cut", "diagonal_tempo_2cut"]
    )
    res_dup = writer.audit_script_quality(dup_consec)
    assert res_dup["passed"] is False
    assert any("layout" in err.lower() or "consecutive" in err.lower() or "연속" in err for err in res_dup["errors"])

    # 2. Fewer than 3 distinct layouts across 5 acts (alternating A-B-A-B-A) must fail
    too_few_layouts = _build_custom_v4_script(
        ["diagonal_tempo_2cut", "impact_freeze_2cut", "diagonal_tempo_2cut", "impact_freeze_2cut", "diagonal_tempo_2cut"]
    )
    res_few = writer.audit_script_quality(too_few_layouts)
    assert res_few["passed"] is False

    # 3. Anonymity leak (forbidden name + <GuildTag>)
    leaked_acts = list(clean.acts or [])
    leaked_cut = leaked_acts[0].cuts[0].model_copy(
        update={"dialogue": "<전설의길드> 악질유저닉 님이 다 먹튀했어요!"}
    )
    leaked_acts[0] = leaked_acts[0].model_copy(update={"cuts": [leaked_cut, *leaked_acts[0].cuts[1:]]})
    leaked_script = clean.model_copy(
        update={"acts": leaked_acts, "cuts": [c for a in leaked_acts for c in a.cuts]}
    )
    res_leak = writer.audit_script_quality(leaked_script, forbidden_names=["악질유저닉"])
    assert res_leak["passed"] is False
    assert res_leak["checks"]["anonymity_ok"] is False

    # 4. Modern slang violation
    slang_acts = list(clean.acts or [])
    slang_cut = slang_acts[1].cuts[0].model_copy(
        update={"dialogue": "아 힐러 쓰러졌어요 빨리 119 불러야 되나 카톡 보내봐요!"}
    )
    slang_acts[1] = slang_acts[1].model_copy(update={"cuts": [slang_cut, *slang_acts[1].cuts[1:]]})
    slang_script = clean.model_copy(
        update={"acts": slang_acts, "cuts": [c for a in slang_acts for c in a.cuts]}
    )
    res_slang = writer.audit_script_quality(slang_script)
    assert res_slang["passed"] is False
    assert res_slang["checks"]["no_modern_slang"] is False

    # 5. Missing wordless cut caught directly by auditor (bypassing Pydantic via model_construct)
    no_wl_cuts = [
        c.model_copy(update={"wordless": False, "speaker": c.characters[0], "dialogue": "말풍선 있음"})
        for c in clean.cuts
    ]
    no_wl_script = EpisodeScript.model_construct(
        episode_number=clean.episode_number,
        source_post_no=clean.source_post_no,
        source_title=clean.source_title,
        source_url=clean.source_url,
        subtitle=clean.subtitle,
        layout_mode="v4_five_act",
        acts=clean.acts,
        cuts=no_wl_cuts,
    )
    res_wl = writer.audit_script_quality(no_wl_script)
    assert res_wl["passed"] is False
    assert res_wl["checks"]["wordless_cut_ok"] is False


# ---------------------------------------------------------------------------
# 4. artist.py: V4 parallel 5-page 2K batch generation & attachments
# ---------------------------------------------------------------------------


def test_artist_generate_v4_episode_pages_attaches_blueprint_and_all_turnarounds(tmp_path: Path) -> None:
    settings = load_settings(PROJECT_ROOT)
    script = _build_custom_v4_script(
        ["open_top_split_bottom", "split_top_wide_bottom", "wide_reaction_wide", "impact_freeze_2cut", "diagonal_tempo_2cut"]
    )

    buf = io.BytesIO()
    Image.new("RGB", (90, 135), (255, 255, 255)).save(buf, format="PNG")
    fake_png_b64 = base64.b64encode(buf.getvalue()).decode("ascii")

    lock = threading.Lock()
    captured_calls: list[dict[str, Any]] = []

    class FakeInteractions:
        def create(self, **kwargs: Any) -> Any:
            with lock:
                captured_calls.append(kwargs)
            return SimpleNamespace(output_image=SimpleNamespace(data=fake_png_b64))

    fake_client = SimpleNamespace(interactions=FakeInteractions())
    out_dir = tmp_path / "raw_pages"
    page_paths = artist.generate_v4_episode_pages(
        script,
        out_dir,
        client=fake_client,
        settings=settings,
    )

    assert sorted(page_paths.keys()) == [1, 2, 3, 4, 5]
    for act_num, path in page_paths.items():
        assert path == out_dir / f"raw_page_{act_num:02d}.png"
        assert path.exists()
        with Image.open(path) as im:
            assert im.size == (90, 135)

    assert len(captured_calls) == 5

    cast_sheet_bytes = settings.cast_sheet_path.read_bytes()
    style_ref_bytes = settings.style_ref_path.read_bytes()

    # Match each captured call back to its ActPage via its layout_id / act_number in prompt text
    matched_acts: set[int] = set()
    for call in captured_calls:
        assert call["model"] == DEFAULT_IMAGE_MODEL == "gemini-nano-banana-2.1"
        assert call["response_format"] == {
            "type": "image",
            "aspect_ratio": "2:3",
            "image_size": "2K",
        }

        items = call["input"]
        assert items[0]["type"] == "text"
        prompt_text = items[0]["text"]
        assert "#FFFFFF" in prompt_text
        assert "ZERO" in prompt_text.upper() or "NO TEXT" in prompt_text.upper()

        # Identify which act this call belongs to (via prompt text OR exact attached blueprint image)
        bp_bytes = base64.b64decode(items[3]["data"])
        with Image.open(io.BytesIO(bp_bytes)) as attached_bp:
            attached_bp_arr = np.asarray(attached_bp.convert("RGB"))
            assert attached_bp.size == (V4_PAGE_W, V4_PAGE_H)

        act = next(
            (
                a
                for a in (script.acts or [])
                if np.array_equal(attached_bp_arr, np.asarray(render_layout_blueprint(a.layout_id)))
            ),
            None,
        )
        assert act is not None, f"Attached Image 3 did not match any act layout blueprint! Prompt: {prompt_text[:200]}"
        matched_acts.add(act.act_number)

        # Collect unique appearing cast members across ALL cuts in this act
        unique_members = []
        seen_ids: set[str] = set()
        for cut in act.cuts:
            for c_name in cut.characters:
                member = resolve_cast_member(c_name)
                if member and member.id not in seen_ids:
                    seen_ids.add(member.id)
                    unique_members.append(member)

        # Verify exact attachment count: text + cast_sheet + style_ref + layout_blueprint + unique turnarounds
        assert len(items) == 4 + len(unique_members), (
            f"Act {act.act_number} expected {4 + len(unique_members)} input items, got {len(items)}"
        )
        assert all(item["type"] == "image" for item in items[1:])

        # Image 1: cast_sheet_c.jpg
        assert base64.b64decode(items[1]["data"]) == cast_sheet_bytes
        # Image 2: sloptoon_style_ref.jpg
        assert base64.b64decode(items[2]["data"]) == style_ref_bytes

        # Images 4+: every unique character's 3-view turnaround blueprint from assets/turnarounds/
        attached_turnaround_blobs = {base64.b64decode(item["data"]) for item in items[4:]}
        expected_turnaround_blobs = {
            (settings.turnarounds_dir / member.turnaround_filename).read_bytes()
            for member in unique_members
        }
        assert attached_turnaround_blobs == expected_turnaround_blobs

    assert matched_acts == {1, 2, 3, 4, 5}

    # Offline dry-run page renderer produces 5 valid 900x1350 pure-white-bordered PNGs
    dry_pages = artist.render_dry_run_v4_pages(script, tmp_path / "dry_pages")
    assert sorted(dry_pages.keys()) == [1, 2, 3, 4, 5]
    for p in dry_pages.values():
        assert p.exists()
        with Image.open(p) as im:
            assert im.size == (V4_PAGE_W, V4_PAGE_H)


# ---------------------------------------------------------------------------
# 5. composer.py: V4 end-to-end composition & full-bleed worst-case stress
# ---------------------------------------------------------------------------


def test_compose_v4_episode_end_to_end_mixed_layouts_and_tooltips(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SLOPTOON_OFFLINE_TOOLTIPS", "1")
    # 3 + 3 + 4 + 2 + 2 = 14 cuts covering open wide, narrow split, slim cinematic, 4-beat, and giant wordless!
    layout_plan = [
        "open_top_split_bottom",
        "wide_reaction_wide",
        "four_beat_gag",
        "impact_freeze_2cut",
        "diagonal_tempo_2cut",
    ]
    script = _build_custom_v4_script(layout_plan, include_wordless=True, with_tooltips=True)

    raw_dir = tmp_path / "raw_pages"
    raw_dir.mkdir(parents=True)
    raw_paths: dict[int, Path] = {}
    for act in script.acts or []:
        # Mix exact and slightly drifted 2K pages to test full extract -> compose pipeline
        drift = (12, -10) if act.act_number % 2 == 0 else (0, 0)
        raw_im = _make_synthetic_raw_v4_page(
            act.layout_id,
            size=(1365, 2048),
            drift_xy=drift,
            full_bleed_panels=False,
        )
        p = raw_dir / f"raw_page_{act.act_number:02d}.png"
        raw_im.save(p, format="PNG")
        raw_paths[act.act_number] = p

    out_dir = tmp_path / "composed_v4"
    res = compose_v4_episode(script, raw_paths, out_dir)
    assert isinstance(res, ComposeResult)

    # Core audit assertions
    audit = res.audit_report
    assert audit["passed"] is True, f"V4 composition audit failed: {audit}"
    assert audit["layout_mode"] == "v4_five_act"
    assert audit["total_overlap_px"] == 0
    assert audit["total_tooltip_overlap_px"] == 0
    assert audit["border_pure_white"] is True
    assert audit["page_count"] == 5
    assert audit["cut_count"] == len(script.cuts) == 14
    assert audit["watermarked"] is True
    assert audit["page_layouts"] == layout_plan

    # Every cut strictly 0px bubble overlap and 0px tooltip overlap
    tooltip_cuts = 0
    wordless_cuts = 0
    for c_audit in audit["cuts"]:
        assert c_audit["overlap_px"] == 0, f"Bubble overlap in cut {c_audit}"
        if c_audit.get("has_item_tooltip"):
            tooltip_cuts += 1
            assert c_audit["tooltip_overlap_px"] == 0
        if c_audit.get("wordless"):
            wordless_cuts += 1
            assert c_audit["bubble_count"] == 0
    assert tooltip_cuts == 4
    assert wordless_cuts == 1

    # Output artifacts check
    assert res.header_path.exists()
    with Image.open(res.header_path) as hdr:
        assert hdr.size == (PAGE_W, HEADER_H)
    _assert_pure_white_outer_border(res.header_path)

    assert len(res.page_paths) == 5
    for idx, (page_path, lid) in enumerate(zip(res.page_paths, layout_plan), start=1):
        assert page_path.exists()
        assert page_path.name == f"page_{idx}.png"
        with Image.open(page_path) as pim:
            assert pim.size == (V4_PAGE_W, V4_PAGE_H)
            arr = np.asarray(pim.convert("RGB"))
        _assert_pure_white_outer_border(page_path, margin=4)

        # Verify box slots have crisp dark borders along all 4 edges while open slots remain borderless!
        spec = get_page_layout(lid)
        for slot in spec.slots:
            x0, y0, x1, y1 = slot.rect
            left_band = arr[y0 + 16 : y1 - 16, max(0, x0 - 3) : x0 + 5, :]
            right_band = arr[y0 + 16 : y1 - 16, max(0, x1 - 5) : min(V4_PAGE_W, x1 + 3), :]
            left_cov = float(np.mean(np.any((left_band < 45).all(axis=2), axis=1)))
            right_cov = float(np.mean(np.any((right_band < 45).all(axis=2), axis=1)))
            if slot.border_style == "box":
                assert left_cov > 0.90 and right_cov > 0.90, (
                    f"Box border missing on page {idx} ({lid}) slot {slot.slot_index}: "
                    f"left={left_cov:.2f}, right={right_cov:.2f}"
                )
            else:
                assert left_cov < 0.20 and right_cov < 0.20, (
                    f"Open slot unexpectedly boxed on page {idx} ({lid}) slot {slot.slot_index}: "
                    f"left={left_cov:.2f}, right={right_cov:.2f}"
                )

    # Full stitched + watermarked vs raw check
    raw_full = out_dir / "episode_full_raw.jpg"
    assert raw_full.exists()
    assert res.full_image_path.exists()
    with Image.open(raw_full) as im_raw, Image.open(res.full_image_path) as im_wm:
        assert im_raw.size[0] == PAGE_W
        assert im_wm.size == (PAGE_W, im_raw.size[1] + WATERMARK_FOOTER_H)
    _assert_pure_white_outer_border(res.full_image_path, margin=2)

    # Valid thumbnail
    assert res.thumb_path.exists()
    with Image.open(res.thumb_path) as thumb_im:
        assert thumb_im.size == THUMB_SIZE


def test_compose_v4_full_bleed_worst_case_stress_and_auto_delegation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Full-bleed panels across all 5 acts (including split_top_wide_bottom + long Korean text + tooltips)
    must still achieve strictly 0px bubble/tooltip overlap and delegate cleanly via `compose_episode`."""
    monkeypatch.setenv("SLOPTOON_OFFLINE_TOOLTIPS", "1")
    # 3 + 2 + 4 + 2 + 3 = 14 cuts covering split_top_wide_bottom, diagonal, 4-beat, freeze, and 3-strip wide!
    layout_plan = [
        "split_top_wide_bottom",
        "diagonal_tempo_2cut",
        "four_beat_gag",
        "impact_freeze_2cut",
        "wide_reaction_wide",
    ]
    script = _build_custom_v4_script(
        layout_plan,
        include_wordless=True,
        with_tooltips=True,
        long_dialogues=True,
    )

    raw_dir = tmp_path / "bleed_pages"
    raw_dir.mkdir(parents=True)
    raw_paths: dict[int, Path] = {}
    for act in script.acts or []:
        raw_im = _make_synthetic_raw_v4_page(
            act.layout_id,
            size=(V4_PAGE_W, V4_PAGE_H),
            drift_xy=(0, 0),
            full_bleed_panels=True,
        )
        p = raw_dir / f"raw_page_{act.act_number:02d}.png"
        raw_im.save(p, format="PNG")
        raw_paths[act.act_number] = p

    # Call compose_episode (NOT compose_v4_episode directly) to verify automatic delegation!
    out_dir = tmp_path / "bleed_out"
    res = compose_episode(script, raw_paths, out_dir)
    assert res.audit_report["passed"] is True, f"Full-bleed V4 stress failed: {res.audit_report}"
    assert res.audit_report["layout_mode"] == "v4_five_act"
    assert res.audit_report["total_overlap_px"] == 0
    assert res.audit_report["total_tooltip_overlap_px"] == 0
    assert res.audit_report["border_pure_white"] is True
    assert len(res.page_paths) == 5
    for p in res.page_paths:
        with Image.open(p) as im:
            assert im.size == (V4_PAGE_W, V4_PAGE_H)
        _assert_pure_white_outer_border(p, margin=4)

    # Also stress-test narrow wordless panel (410x626) + ItemTooltipSpec on full-bleed art
    narrow_wl_cut = _make_v4_cut(
        99,
        characters=["스카이본 마법사"],
        wordless=True,
        item_tooltip=ItemTooltipSpec(wowhead_item_id=7722),
    )
    bleed_narrow = Image.new("RGB", (410, 626), (72, 118, 210))
    panel_wl, audit_wl = composer._compose_variable_panel(
        narrow_wl_cut, bleed_narrow, target_w=410, target_h=626, border_style="box"
    )
    assert panel_wl.size == (410, 626)
    assert audit_wl["wordless"] is True
    assert audit_wl["bubble_count"] == 0
    assert audit_wl["overlap_px"] == 0
    assert audit_wl["tooltip_overlap_px"] == 0

    # Verify watermark opt-out in compose_v4_episode
    out_no_wm = tmp_path / "bleed_no_wm"
    res_no_wm = compose_v4_episode(script, raw_paths, out_no_wm, watermark_url=None)
    assert res_no_wm.audit_report["passed"] is True
    assert res_no_wm.audit_report["watermarked"] is False
    assert not (out_no_wm / "episode_full_raw.jpg").exists()
    with Image.open(res.full_image_path) as im_wm, Image.open(res_no_wm.full_image_path) as im_no:
        assert im_wm.size == (PAGE_W, im_no.size[1] + WATERMARK_FOOTER_H)


@pytest.mark.parametrize("with_valley", [True, False])
@pytest.mark.parametrize("tail_target", ["left", "right"])
@pytest.mark.parametrize("bubble_side", ["center", "left", "right", None])
def test_compose_v4_two_char_slim_panel_targets_speaker_never_listener(
    with_valley: bool,
    tail_target: str,
    bubble_side: str | None,
) -> None:
    """Regression test (#8): In 2-char slim wide panels (844x404), the bubble tail MUST aim
    strictly toward the `tail_target` speaker half and NEVER misfire toward the listener."""
    raw = Image.new("RGB", (844, 404), (255, 255, 255))
    d = ImageDraw.Draw(raw)
    if with_valley:
        # Left & right characters with wide pure-white middle valley (x=280..564)
        d.ellipse([60, 70, 270, 398], fill=(100, 190, 110), outline=(24, 24, 24), width=4)
        d.ellipse([574, 70, 784, 398], fill=(160, 140, 220), outline=(24, 24, 24), width=4)
    else:
        # Closer 2-character staging without a wide valley
        d.ellipse([160, 70, 420, 398], fill=(100, 190, 110), outline=(24, 24, 24), width=4)
        d.ellipse([424, 70, 684, 398], fill=(160, 140, 220), outline=(24, 24, 24), width=4)

    cut = ComicCut(
        cut_index=13,
        aspect_ratio="auto",
        layout_slot="panel",
        characters=["오크 전사", "언데드 성기사"],
        speaker="오크 전사" if tail_target == "left" else "언데드 성기사",
        dialogue="그럴 줄 알았다... 다음엔 꼭 룰부터 정하고 가자!",
        wordless=False,
        visual_prompt="Two characters side-by-side aftermath reaction on pure #FFFFFF white background.",
        tail_target=tail_target,  # type: ignore[arg-type]
        bubble_side=bubble_side,  # type: ignore[arg-type]
    )

    panel, audit = composer._compose_variable_panel(
        cut, raw, target_w=844, target_h=404, border_style="box"
    )
    assert panel.size == (844, 404)
    assert audit["overlap_px"] == 0
    assert audit["bubble_count"] == 1

    art_bbox = audit["art_bbox"]
    assert art_bbox is not None
    art_mid_x = 0.5 * (art_bbox[0] + art_bbox[2])
    tail_tip = audit.get("tail_tip")
    assert tail_tip is not None, f"Expected visible speaker-targeted tail for {tail_target}/{bubble_side}"

    if tail_target == "right":
        assert tail_tip[0] > art_mid_x, (
            f"Tail misfired left of art_mid ({tail_tip[0]} <= {art_mid_x}) for right speaker "
            f"(with_valley={with_valley}, bubble_side={bubble_side})"
        )
        if bubble_side == "right":
            assert audit["bubble_side_resolved"] == "right"
    else:
        assert tail_tip[0] < art_mid_x, (
            f"Tail misfired right of art_mid ({tail_tip[0]} >= {art_mid_x}) for left speaker "
            f"(with_valley={with_valley}, bubble_side={bubble_side})"
        )
        if bubble_side == "left":
            assert audit["bubble_side_resolved"] == "left"


# ---------------------------------------------------------------------------
# 6. cli.py: --layout v4 --dry-run and policy compliance
# ---------------------------------------------------------------------------


def test_cli_generate_v4_dry_run_and_classic_default(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        cli.GalleryScout,
        "fetch_post_detail",
        lambda self, post_no, base_post=None: _sample_post(post_no=str(post_no)),
    )

    rc = cli.main(["generate", "--post-no", "99001", "--layout", "v4", "--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "[DRY-RUN]" in out

    # Extract JSON payload from CLI stdout and validate strictly as a V4 EpisodeScript
    json_start = out.find("{")
    assert json_start != -1, f"Expected JSON output from CLI dry-run, got: {out}"
    parsed_obj, _ = json.JSONDecoder().raw_decode(out[json_start:])
    parsed = EpisodeScript.model_validate(parsed_obj)
    assert parsed.layout_mode == "v4_five_act"
    assert parsed.source_post_no == "99001"
    assert parsed.acts is not None and len(parsed.acts) == 5
    assert 10 <= len(parsed.cuts) <= 14

    # Default --layout stays classic_2tier (4..6 cuts)
    rc_classic = cli.main(["generate", "--post-no", "99001", "--dry-run"])
    assert rc_classic == 0
    out_classic = capsys.readouterr().out
    c_start = out_classic.find("{")
    parsed_classic_obj, _ = json.JSONDecoder().raw_decode(out_classic[c_start:])
    parsed_classic = EpisodeScript.model_validate(parsed_classic_obj)
    assert parsed_classic.layout_mode == "classic_2tier"
    assert 4 <= len(parsed_classic.cuts) <= 6


def test_cli_generate_v4_real_pipeline_saves_script_and_5_pages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n', encoding="utf-8")
    post = _sample_post("99222")
    v4_script = _build_custom_v4_script(
        ["open_top_split_bottom", "split_top_wide_bottom", "wide_reaction_wide", "impact_freeze_2cut", "diagonal_tempo_2cut"]
    )

    monkeypatch.setattr(
        cli.GalleryScout,
        "fetch_post_detail",
        lambda self, post_no, base_post=None: post,
    )
    monkeypatch.setattr(
        writer,
        "generate_v4_episode_script",
        lambda p, episode_number, **kwargs: v4_script.model_copy(
            update={"episode_number": episode_number, "source_post_no": str(p.post_no)}
        ),
    )

    def _fake_pages(script: EpisodeScript, out_dir: Path, **kwargs: Any) -> dict[int, Path]:
        out_dir.mkdir(parents=True, exist_ok=True)
        paths: dict[int, Path] = {}
        for act in script.acts or []:
            p = out_dir / f"raw_page_{act.act_number:02d}.png"
            _make_synthetic_raw_v4_page(act.layout_id).save(p, format="PNG")
            paths[act.act_number] = p
        return paths

    monkeypatch.setattr(artist, "generate_v4_episode_pages", _fake_pages)

    rc = cli.main(
        ["--project-root", str(tmp_path), "generate", "--post-no", "99222", "--layout", "v4", "--skip-site"]
    )
    assert rc == 0

    ep_dir = tmp_path / "data" / "episodes" / "ep001"
    assert (ep_dir / "script.json").exists()
    saved_script = EpisodeScript.model_validate_json((ep_dir / "script.json").read_text(encoding="utf-8"))
    assert saved_script.layout_mode == "v4_five_act"
    assert len(saved_script.cuts) == 13

    records = json.loads((tmp_path / "data" / "episodes.json").read_text(encoding="utf-8"))
    assert len(records) == 1
    assert records[0]["episode_id"] == "ep001"
    assert records[0]["cut_count"] == 13
    assert len(records[0]["page_images_rel"]) == 5
    for rel in records[0]["page_images_rel"]:
        assert (tmp_path / rel).exists()


def test_v4_source_files_policy_and_pii_compliance() -> None:
    checked = [
        PROJECT_ROOT / "src" / "wow_sloptoon" / "layouts.py",
        PROJECT_ROOT / "src" / "wow_sloptoon" / "models.py",
        PROJECT_ROOT / "src" / "wow_sloptoon" / "writer.py",
        PROJECT_ROOT / "src" / "wow_sloptoon" / "artist.py",
        PROJECT_ROOT / "src" / "wow_sloptoon" / "composer.py",
        PROJECT_ROOT / "src" / "wow_sloptoon" / "cli.py",
    ]
    forbidden = [
        "google-generativeai",
        "gemini-2.5-",
        "2captcha",
        "solve_captcha",
        "bypass_captcha",
        "requests.post(",
        "httpx.post(",
        "c:\\users\\",
        "c:/users/",
    ]
    for fpath in checked:
        assert fpath.exists(), f"Missing expected V4 source file: {fpath}"
        lower = fpath.read_text(encoding="utf-8").lower()
        for tok in forbidden:
            assert tok not in lower, f"Forbidden token '{tok}' found in {fpath.name}"


# ---------------------------------------------------------------------------
# 7. site_builder.py: V4 5-page 13-cut static archive compatibility
# ---------------------------------------------------------------------------


def test_site_builder_v4_five_page_13_cut_episode_compatibility(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SLOPTOON_OFFLINE_TOOLTIPS", "1")
    layout_plan = [
        "open_top_split_bottom",  # 3
        "split_top_wide_bottom",  # 3
        "wide_reaction_wide",     # 3
        "impact_freeze_2cut",     # 2
        "diagonal_tempo_2cut",    # 2 -> total 13 cuts
    ]
    script = _build_custom_v4_script(layout_plan, include_wordless=True, with_tooltips=True)
    assert len(script.cuts) == 13

    ep_id = "ep011"
    ep_dir = tmp_path / "data" / "episodes" / ep_id
    raw_dir = tmp_path / "raw_pages"
    raw_dir.mkdir(parents=True)
    raw_paths: dict[int, Path] = {}
    for act in script.acts or []:
        p = raw_dir / f"raw_page_{act.act_number:02d}.png"
        _make_synthetic_raw_v4_page(act.layout_id).save(p, format="PNG")
        raw_paths[act.act_number] = p

    composed = compose_v4_episode(script, raw_paths, ep_dir)
    assert composed.audit_report["passed"] is True
    assert len(composed.page_paths) == 5

    record = EpisodeRecord(
        episode_id=ep_id,
        episode_number=11,
        title=script.source_title,
        subtitle=script.subtitle,
        source_post_no=script.source_post_no,
        source_url=script.source_url,
        created_at="2026-11-24T16:00:00+09:00",
        cut_count=len(script.cuts),
        cast_used=["나이트엘프 사제", "오크 전사", "노움 도적", "스카이본 마법사"],
        full_image_rel=f"data/episodes/{ep_id}/episode_full.jpg",
        thumb_image_rel=f"data/episodes/{ep_id}/thumb.jpg",
        page_images_rel=[f"data/episodes/{ep_id}/page_{i}.png" for i in range(1, 6)],
    )
    episodes_json = tmp_path / "data" / "episodes.json"
    episodes_json.write_text(
        json.dumps([record.model_dump(mode="json")], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    real_assets = load_settings(PROJECT_ROOT).assets_dir
    out_site = tmp_path / "site"
    index_path = build_static_site(episodes_json, out_site, real_assets)
    assert index_path == out_site / "index.html"
    assert not (out_site / "publish.html").exists()

    for html_page in (
        out_site / "index.html",
        out_site / "episode.html",
        out_site / "cast.html",
        out_site / "episodes" / f"{ep_id}.html",
    ):
        assert html_page.exists()
        _assert_internal_links_resolve(html_page)
        text = html_page.read_text(encoding="utf-8")
        assert "publish.html" not in text
        assert DC_GALLERY_WRITE_URL not in text
        assert "인벤" not in text

    # All 5 V4 pages copied cleanly with exact 900x1350 dimensions
    site_ep_dir = out_site / "assets" / "episodes" / ep_id
    for i in range(1, 6):
        copied_page = site_ep_dir / f"page_{i}.png"
        assert copied_page.exists(), f"Missing copied V4 page_{i}.png"
        with Image.open(copied_page) as im:
            assert im.size == (V4_PAGE_W, V4_PAGE_H)

    ep_html = (out_site / "episodes" / f"{ep_id}.html").read_text(encoding="utf-8")
    assert "13컷" in ep_html
    assert script.source_title in ep_html

    site_data = json.loads((out_site / "data" / "episodes.json").read_text(encoding="utf-8"))
    assert len(site_data) == 1
    assert site_data[0]["cut_count"] == 13
    assert len(site_data[0]["page_images"]) == 5


# ---------------------------------------------------------------------------
# 8. V4.2 Edge-to-Edge Full-Bleed Boxed Panel Mode & Pinpoint Speaker Anchors
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("layout_id", list(EXPECTED_LAYOUT_RECTS.keys()))
def test_render_layout_blueprint_all_boxed_boxes_every_slot(layout_id: str) -> None:
    bp = render_layout_blueprint(layout_id, all_boxed=True)
    assert bp.size == (V4_PAGE_W, V4_PAGE_H)
    assert bp.mode == "RGB"
    arr = np.asarray(bp)

    # Outer 16px margin stays 100% pure white
    assert np.all(arr[:16, :, :] == 255)
    assert np.all(arr[-16:, :, :] == 255)
    assert np.all(arr[:, :16, :] == 255)
    assert np.all(arr[:, -16:, :] == 255)

    spec = get_page_layout(layout_id)
    for slot in spec.slots:
        x0, y0, x1, y1 = slot.rect
        # Deep interior strictly pure white -> ZERO text/digits/numbers
        interior = arr[y0 + 12 : y1 - 12, x0 + 12 : x1 - 12, :]
        assert np.all(interior == 255)

        # ALL slots (including open_top_split_bottom P1 & diagonal_tempo_2cut P1) must have dark #141414 frames
        top_band = arr[max(0, y0 - 4) : y0 + 6, x0 + 20 : x1 - 20, :]
        dark_px = np.sum((top_band[:, :, 0] < 40) & (top_band[:, :, 1] < 40) & (top_band[:, :, 2] < 40))
        assert dark_px > 200, f"Missing all_boxed dark frame on {layout_id} slot {slot.slot_index}"


@pytest.mark.parametrize(
    "layout_id,page_size,drift_xy",
    [
        ("open_top_split_bottom", (900, 1350), (0, 0)),
        ("diagonal_tempo_2cut", (1365, 2048), (14, -12)),
        ("four_beat_gag", (1365, 2048), (-12, 10)),
    ],
)
def test_extract_panels_from_page_all_boxed_preserves_full_bleed_and_strips_borders(
    layout_id: str,
    page_size: tuple[int, int],
    drift_xy: tuple[int, int],
) -> None:
    spec = get_page_layout(layout_id)
    raw_page = _make_synthetic_raw_v4_page(
        layout_id,
        size=page_size,
        drift_xy=drift_xy,
        border_width=6,
        full_bleed_panels=True,
        open_slot_border="dark",
    )

    panels = extract_panels_from_page(raw_page, layout_id, all_boxed=True)
    assert len(panels) == spec.panel_count

    for idx, (panel, slot) in enumerate(zip(panels, spec.slots)):
        pw, ph = panel.size
        assert pw >= int(slot.width * 0.75)
        assert ph >= int(slot.height * 0.75)

        arr = np.asarray(panel)
        # Edge-to-edge full-bleed color pixels preserved right up to all 4 crop edges (no dark border or white gap!)
        own_color = _SLOT_COLORS[idx % len(_SLOT_COLORS)]
        for edge_name, strip in (
            ("top", arr[:3, :, :]),
            ("bottom", arr[-3:, :, :]),
            ("left", arr[:, :3, :]),
            ("right", arr[:, -3:, :]),
        ):
            dark_border_ratio = float(np.mean((strip[:, :, 0] < 45) & (strip[:, :, 1] < 45) & (strip[:, :, 2] < 45)))
            assert dark_border_ratio < 0.15, (
                f"Black frame residue on {edge_name} of {layout_id} slot {idx + 1}: {dark_border_ratio:.2f}"
            )
            colored_ratio = float(np.mean(np.any(strip < 245, axis=2)))
            assert colored_ratio > 0.85, (
                f"Expected full-bleed colored pixels on {edge_name} of {layout_id} slot {idx + 1}, got {colored_ratio:.2f}"
            )

        assert _count_color_match(arr, own_color) > 10000
        for other_idx in range(spec.panel_count):
            if other_idx != idx:
                assert _count_color_match(arr, _SLOT_COLORS[other_idx % len(_SLOT_COLORS)]) < 50

    # Verify accidental stray thin white strip (<= 10px) inside a boxed full-bleed panel gets trimmed cleanly
    stray_page = Image.new("RGB", (V4_PAGE_W, V4_PAGE_H), (255, 255, 255))
    sd = ImageDraw.Draw(stray_page)
    for idx, slot in enumerate(spec.slots):
        x0, y0, x1, y1 = slot.rect
        # Leave an accidental 5px white gap inside the black frame before the colored background
        sd.rectangle([x0 + 10, y0 + 10, x1 - 10, y1 - 10], fill=_SLOT_COLORS[idx % len(_SLOT_COLORS)])
        sd.rectangle([x0, y0, x1, y1], outline=(20, 20, 20), width=4)

    trimmed_panels = extract_panels_from_page(stray_page, layout_id, all_boxed=True)
    for idx, panel in enumerate(trimmed_panels):
        arr = np.asarray(panel)
        for edge_name, strip in (
            ("top", arr[:2, :, :]),
            ("bottom", arr[-2:, :, :]),
            ("left", arr[:, :2, :]),
            ("right", arr[:, -2:, :]),
        ):
            colored_ratio = float(np.mean(np.any(strip < 245, axis=2)))
            assert colored_ratio > 0.90, (
                f"Stray thin white strip was not trimmed on {edge_name} of {layout_id} slot {idx + 1}"
            )


def test_artist_and_writer_v4_full_bleed_prompts_and_blueprint_attachment(tmp_path: Path) -> None:
    settings = load_settings(PROJECT_ROOT)
    post = _sample_post("99555")
    v4_prompt = writer.build_v4_writer_prompt(post, episode_number=12, background_style="full_bleed")
    assert "full_bleed" in v4_prompt
    assert "인접 컷 인물 연속성 절대 엄수" in v4_prompt
    assert "복제 인물" in v4_prompt
    assert "#FFFFFF" in v4_prompt

    script = _build_custom_v4_script(
        ["open_top_split_bottom", "split_top_wide_bottom", "wide_reaction_wide", "impact_freeze_2cut", "diagonal_tempo_2cut"]
    ).model_copy(update={"background_style": "full_bleed"})

    buf = io.BytesIO()
    Image.new("RGB", (90, 135), (255, 255, 255)).save(buf, format="PNG")
    fake_png_b64 = base64.b64encode(buf.getvalue()).decode("ascii")

    lock = threading.Lock()
    captured_calls: list[dict[str, Any]] = []

    class FakeInteractions:
        def create(self, **kwargs: Any) -> Any:
            with lock:
                captured_calls.append(kwargs)
            return SimpleNamespace(output_image=SimpleNamespace(data=fake_png_b64))

    fake_client = SimpleNamespace(interactions=FakeInteractions())
    artist.generate_v4_episode_pages(
        script,
        tmp_path / "fb_raw_pages",
        client=fake_client,
        settings=settings,
    )
    assert len(captured_calls) == 5

    for call in captured_calls:
        items = call["input"]
        prompt_text = items[0]["text"]
        assert "100% FULL-BLEED" in prompt_text
        assert "UNOBSTRUCTED" in prompt_text
        assert "#FFFFFF" in prompt_text
        assert "ATTACHED CHARACTER 3-VIEW TURNAROUND BLUEPRINTS" in prompt_text
        assert "ZERO TEXT" in prompt_text

        # Image 3 must match render_layout_blueprint(act.layout_id, all_boxed=True)
        bp_bytes = base64.b64decode(items[3]["data"])
        with Image.open(io.BytesIO(bp_bytes)) as attached_bp:
            attached_arr = np.asarray(attached_bp.convert("RGB"))
        matched = any(
            np.array_equal(attached_arr, np.asarray(render_layout_blueprint(a.layout_id, all_boxed=True)))
            for a in (script.acts or [])
        )
        assert matched, "Full-bleed V4 artist call did not attach all_boxed=True blueprint!"


def test_compose_v4_episode_full_bleed_edge_to_edge_all_boxed_and_pure_white_margins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SLOPTOON_OFFLINE_TOOLTIPS", "1")
    layout_plan = [
        "open_top_split_bottom",
        "wide_reaction_wide",
        "four_beat_gag",
        "impact_freeze_2cut",
        "diagonal_tempo_2cut",
    ]
    script = _build_custom_v4_script(
        layout_plan,
        include_wordless=True,
        with_tooltips=True,
    ).model_copy(update={"background_style": "full_bleed"})

    raw_dir = tmp_path / "fb_pages"
    raw_dir.mkdir(parents=True)
    raw_paths: dict[int, Path] = {}
    for act in script.acts or []:
        raw_im = _make_synthetic_raw_v4_page(
            act.layout_id,
            size=(1365, 2048),
            drift_xy=(10, -8) if act.act_number % 2 == 0 else (0, 0),
            border_width=6,
            full_bleed_panels=True,
            open_slot_border="dark",
        )
        p = raw_dir / f"raw_page_{act.act_number:02d}.png"
        raw_im.save(p, format="PNG")
        raw_paths[act.act_number] = p

    out_dir = tmp_path / "composed_full_bleed"
    res = compose_v4_episode(script, raw_paths, out_dir)
    audit = res.audit_report
    assert audit["passed"] is True, f"Full-bleed V4 composition failed: {audit}"
    assert audit["background_style"] == "full_bleed"
    assert audit["border_pure_white"] is True
    assert audit["total_overlap_px"] == 0
    assert audit["total_tooltip_overlap_px"] == 0
    assert len(res.page_paths) == 5

    for c_audit in audit["cuts"]:
        assert c_audit["full_bleed_bg"] is True
        assert c_audit["border_style"] == "box"
        assert c_audit["overlap_px"] == 0
        assert c_audit["edge_fill_ratio"] > 0.95
        if not c_audit["wordless"]:
            assert c_audit["bubble_count"] == 1
            assert c_audit["tail_tip"] is not None

    for idx, (page_path, lid) in enumerate(zip(res.page_paths, layout_plan), start=1):
        _assert_pure_white_outer_border(page_path, margin=4)
        with Image.open(page_path) as pim:
            assert pim.size == (V4_PAGE_W, V4_PAGE_H)
            arr = np.asarray(pim.convert("RGB"))

        spec = get_page_layout(lid)
        for slot in spec.slots:
            x0, y0, x1, y1 = slot.rect
            # ALL slots (including open_top_split_bottom P1 & diagonal_tempo_2cut P1) have crisp 3.5px borders!
            left_band = arr[y0 + 16 : y1 - 16, max(0, x0 - 3) : x0 + 5, :]
            right_band = arr[y0 + 16 : y1 - 16, max(0, x1 - 5) : min(V4_PAGE_W, x1 + 3), :]
            top_band = arr[max(0, y0 - 3) : y0 + 5, x0 + 16 : x1 - 16, :]
            bot_band = arr[max(0, y1 - 5) : min(V4_PAGE_H, y1 + 3), x0 + 16 : x1 - 16, :]
            for side_name, band, axis in (
                ("left", left_band, 1),
                ("right", right_band, 1),
                ("top", top_band, 0),
                ("bottom", bot_band, 0),
            ):
                cov = float(np.mean(np.any((band < 45).all(axis=2), axis=axis)))
                assert cov > 0.90, f"Missing 3.5px box border on {side_name} of page {idx} ({lid}) slot {slot.slot_index}"

            # Verify 4 inner edges immediately inside the 3.5px frame are filled with non-white background!
            # (Inset 5px inside frame so we are strictly past the 3.5px border, and outside bubble's >=12px pad!)
            in_top = arr[y0 + 4 : y0 + 8, x0 + 8 : x1 - 8, :]
            in_bot = arr[y1 - 8 : y1 - 4, x0 + 8 : x1 - 8, :]
            in_left = arr[y0 + 8 : y1 - 8, x0 + 4 : x0 + 8, :]
            in_right = arr[y0 + 8 : y1 - 8, x1 - 8 : x1 - 4, :]
            for edge_name, strip in (
                ("inner_top", in_top),
                ("inner_bot", in_bot),
                ("inner_left", in_left),
                ("inner_right", in_right),
            ):
                fill_ratio = float(np.mean(np.any(strip < 245, axis=2)))
                assert fill_ratio > 0.90, (
                    f"White gap found along {edge_name} of full-bleed page {idx} ({lid}) "
                    f"slot {slot.slot_index}: fill_ratio={fill_ratio:.2f}"
                )

    # Framed full-bleed thumbnail keeps pure white outer border + rich colored interior
    _assert_pure_white_outer_border(res.thumb_path, margin=2)
    with Image.open(res.thumb_path) as tim:
        assert tim.size == THUMB_SIZE
        t_arr = np.asarray(tim.convert("RGB"))
    interior_fill = float(np.mean(np.any(t_arr[24:-24, 24:-24, :] < 245, axis=2)))
    assert interior_fill > 0.90


def test_compose_full_bleed_panel_pinpoint_speaker_anchor_and_bubble_center_override() -> None:
    """Regression test (#17): Pinpoint `speaker_anchor_xy` + `bubble_center_xy` aims the speech bubble
    tail with laser precision at the actual speaking character's head, completely immune to distracting
    flying mobs or explosions drawn in other parts of the full-bleed background."""
    W, H = 844, 650
    raw = Image.new("RGB", (W, H), (56, 74, 118))  # Deep dungeon twilight background
    d = ImageDraw.Draw(raw)
    # Distracting flying pirate mob / explosion high in the UPPER-RIGHT corner!
    d.ellipse([610, 40, 810, 210], fill=(235, 92, 54), outline=(20, 20, 20), width=5)
    # Actual Undead Paladin speaker in the LOWER-LEFT!
    d.ellipse([110, 420, 260, 580], fill=(182, 204, 232), outline=(20, 20, 20), width=5)

    cut = ComicCut(
        cut_index=6,
        aspect_ratio="auto",
        layout_slot="panel",
        characters=["언데드 성기사"],
        speaker="언데드 성기사",
        dialogue="야 해적 몹 날아다니는데\n지금 주사위 굴릴 때가 아니라고!",
        wordless=False,
        visual_prompt="Full-bleed dungeon pirate deck combat scene with flying mob in upper right.",
        tail_target="left",
        full_bleed_bg=True,
        speaker_anchor_xy=(0.22, 0.76),
        bubble_center_xy=(0.68, 0.22),
    )

    panel, audit = composer._compose_full_bleed_panel(cut, raw, target_w=W, target_h=H)
    assert panel.size == (W, H)
    assert audit["full_bleed_bg"] is True
    assert audit["overlap_px"] == 0
    assert audit["bubble_count"] == 1
    assert audit["edge_fill_ratio"] > 0.98

    cx, cy = audit["bubble_center"]
    sx, sy = audit["speaker_anchor"]
    assert abs(cx - 0.68 * W) <= 2.0
    assert abs(cy - 0.22 * H) <= 2.0
    assert abs(sx - 0.22 * W) <= 1.0
    assert abs(sy - 0.76 * H) <= 1.0

    tail_tip = audit["tail_tip"]
    assert tail_tip is not None
    tx, ty = tail_tip

    # Vector from bubble center -> tail tip must align almost 100% with bubble center -> speaker anchor!
    v_tip = np.array([tx - cx, ty - cy], dtype=np.float64)
    v_spk = np.array([sx - cx, sy - cy], dtype=np.float64)
    cos_sim = float(np.dot(v_tip, v_spk) / (np.linalg.norm(v_tip) * np.linalg.norm(v_spk)))
    assert cos_sim > 0.999, f"Tail did not aim directly at speaker_anchor_xy (cos_sim={cos_sim:.4f})"

    # Tail tip must point DOWN-LEFT toward lower-left speaker (never toward upper-right flying mob!)
    assert tx < cx and ty > cy
    # Tail stops crisply short of speaker anchor (does not overshoot past head!)
    assert float(np.linalg.norm(v_tip)) < float(np.linalg.norm(v_spk)) - 10.0

    # Deterministic fallback (speaker_anchor_xy=None) across narrow, wide-tall, and wide-slim panels
    for (pw, ph), target, bside in (
        ((410, 638), "left", None),
        ((844, 650), "right", "right"),
        ((844, 404), "left", "center"),
        ((844, 404), "right", "left"),
        ((844, 404), "left", "right"),
    ):
        c_det = ComicCut(
            cut_index=7,
            aspect_ratio="auto",
            layout_slot="panel",
            characters=["오크 전사", "언데드 성기사"],
            speaker="오크 전사",
            dialogue="결정론적 화자 조준 테스트 대사!",
            wordless=False,
            visual_prompt="Full-bleed colored dungeon scene.",
            tail_target=target,  # type: ignore[arg-type]
            bubble_side=bside,   # type: ignore[arg-type]
            full_bleed_bg=True,
        )
        p_det, a_det = composer._compose_full_bleed_panel(c_det, raw, target_w=pw, target_h=ph)
        assert p_det.size == (pw, ph)
        assert a_det["overlap_px"] == 0
        assert a_det["tail_tip"] is not None
        exp_sx = (0.27 if target == "left" else 0.73) * pw
        assert abs(a_det["speaker_anchor"][0] - exp_sx) <= 1.0

    # Out-of-range ratios rejected cleanly by Pydantic
    with pytest.raises(ValidationError):
        ComicCut(
            cut_index=8,
            characters=["오크 전사"],
            speaker="오크 전사",
            dialogue="범위 초과 테스트",
            visual_prompt="Invalid anchor.",
            speaker_anchor_xy=(1.4, 0.5),
        )


def test_cli_generate_bg_flag_defaults_and_overrides(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        cli.GalleryScout,
        "fetch_post_detail",
        lambda self, post_no, base_post=None: _sample_post(post_no=str(post_no)),
    )

    # --layout v4 defaults to --bg full_bleed
    rc_v4 = cli.main(["generate", "--post-no", "99001", "--layout", "v4", "--dry-run"])
    assert rc_v4 == 0
    out_v4 = capsys.readouterr().out
    v4_obj, _ = json.JSONDecoder().raw_decode(out_v4[out_v4.find("{") :])
    assert EpisodeScript.model_validate(v4_obj).background_style == "full_bleed"

    # --layout v4 --bg clean_white overrides back to clean_white
    rc_cw = cli.main(["generate", "--post-no", "99001", "--layout", "v4", "--bg", "clean_white", "--dry-run"])
    assert rc_cw == 0
    out_cw = capsys.readouterr().out
    cw_obj, _ = json.JSONDecoder().raw_decode(out_cw[out_cw.find("{") :])
    assert EpisodeScript.model_validate(cw_obj).background_style == "clean_white"

    # --layout classic (default) defaults to clean_white
    rc_cl = cli.main(["generate", "--post-no", "99001", "--dry-run"])
    assert rc_cl == 0
    out_cl = capsys.readouterr().out
    cl_obj, _ = json.JSONDecoder().raw_decode(out_cl[out_cl.find("{") :])
    assert EpisodeScript.model_validate(cl_obj).background_style == "clean_white"


def test_extract_panels_all_boxed_dark_neutral_cave_interiors_preserve_exact_white_gutters() -> None:
    """Regression test: dark neutral slate/charcoal dungeon walls inside full-bleed boxes MUST NOT
    fool all-boxed panel extraction into crossing `#FFFFFF` vertical/horizontal gutters or chopping
    interior panel artwork."""
    lid = "split_top_wide_bottom"
    spec = get_page_layout(lid)
    page = Image.new("RGB", (V4_PAGE_W, V4_PAGE_H), (255, 255, 255))
    d = ImageDraw.Draw(page)

    # Fill every box with dark neutral stone/slate walls (chroma <= 15, cmin <= 80) + internal dark pillars
    dark_stone = (64, 68, 72)
    pillar_dark = (36, 38, 42)
    markers = [(230, 60, 60), (60, 210, 90), (70, 140, 240)]
    for idx, slot in enumerate(spec.slots):
        x0, y0, x1, y1 = slot.rect
        d.rectangle([x0, y0, x1, y1], fill=dark_stone)
        # Draw strong vertical & horizontal dark dungeon beams inside the panel interior!
        d.rectangle([x0 + 48, y0 + 8, x0 + 62, y1 - 8], fill=pillar_dark)
        d.rectangle([x1 - 62, y0 + 8, x1 - 48, y1 - 8], fill=pillar_dark)
        d.rectangle([x0 + 8, y0 + 70, x1 - 8, y0 + 82], fill=pillar_dark)
        # Put a distinct bright marker near the left & right edges so over-cropping or bleed is obvious
        d.rectangle([x0 + 18, y0 + 140, x0 + 42, y0 + 220], fill=markers[idx])
        d.rectangle([x1 - 42, y0 + 140, x1 - 18, y0 + 220], fill=markers[idx])
        d.rectangle([x0, y0, x1, y1], outline=(20, 20, 20), width=4)

    panels = extract_panels_from_page(page, lid, all_boxed=True)
    assert len(panels) == 3
    for idx, (panel, slot) in enumerate(zip(panels, spec.slots)):
        pw, ph = panel.size
        assert abs(pw - slot.width) <= 20, f"Slot {idx + 1} width over-cropped: {pw} vs {slot.width}"
        assert abs(ph - slot.height) <= 20, f"Slot {idx + 1} height over-cropped: {ph} vs {slot.height}"
        arr = np.asarray(panel)
        # Own markers on BOTH sides preserved; zero cross-gutter neighbor bleed; zero internal white gutter strip!
        assert _count_color_match(arr, markers[idx]) >= 3000
        for other_idx in range(3):
            if other_idx != idx:
                assert _count_color_match(arr, markers[other_idx]) == 0
        white_cols = (arr.min(axis=2) >= 245).mean(axis=0)
        assert float(white_cols.max()) < 0.50, f"White vertical gutter leaked inside slot {idx + 1}!"
