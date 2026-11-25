"""Tests for Route A `wow_sloptoon.composer`, bottom-box anti-shrinking & speaker targeting,
watermark banners, clean 6-command `cli.py`, and policy compliance.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
from PIL import Image, ImageDraw

from wow_sloptoon import cli
from wow_sloptoon.composer import (
    BOT_BOX_W,
    EPILOGUE_PAGE_H,
    FULL_PAGE_H,
    HEADER_H,
    PAGE_W,
    THUMB_SIZE,
    TOP_PANEL_H,
    WATERMARK_FOOTER_H,
    ComposeResult,
    _compose_bottom_box_panel,
    _compose_top_open_panel,
    append_watermark_footer,
    clean_white_bg,
    compose_episode,
    load_font,
    render_watermark_footer,
    retrofit_episode_watermark,
)
from wow_sloptoon.models import ComicCut, EpisodeRecord, EpisodeScript, GalleryPost


def _make_synthetic_cut(
    path: Path,
    size: tuple[int, int],
    *,
    bg_color: tuple[int, int, int] = (249, 248, 247),
    mode: str = "RGB",
    layout: str = "two_chars",
    full_bleed: bool = False,
) -> Path:
    """Create a realistic synthetic character illustration PNG/JPG fixture."""
    path.parent.mkdir(parents=True, exist_ok=True)
    w, h = size
    if mode == "RGBA":
        im = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    else:
        im = Image.new("RGB", (w, h), bg_color)

    draw = ImageDraw.Draw(im)

    if full_bleed:
        draw.rectangle([0, 0, w - 1, h - 1], fill=(92, 132, 210))
        draw.ellipse([w // 4, h // 4, 3 * w // 4, 3 * h // 4], fill=(245, 196, 118), outline=(25, 25, 25), width=6)
    elif layout == "two_chars":
        draw.ellipse([int(w * 0.14), int(h * 0.24), int(w * 0.42), int(h * 0.62)], fill=(140, 210, 145), outline=(24, 24, 24), width=5)
        draw.rectangle([int(w * 0.18), int(h * 0.56), int(w * 0.38), h - 1], fill=(214, 128, 178), outline=(24, 24, 24), width=5)
        draw.ellipse([int(w * 0.58), int(h * 0.22), int(w * 0.86), int(h * 0.60)], fill=(158, 134, 224), outline=(24, 24, 24), width=5)
        draw.rectangle([int(w * 0.62), int(h * 0.54), int(w * 0.82), h - 1], fill=(78, 92, 152), outline=(24, 24, 24), width=5)
    elif layout == "right_char":
        draw.ellipse([int(w * 0.54), int(h * 0.14), int(w * 0.88), int(h * 0.66)], fill=(184, 148, 226), outline=(24, 24, 24), width=5)
        draw.rectangle([int(w * 0.58), int(h * 0.58), int(w * 0.84), h - 1], fill=(95, 176, 132), outline=(24, 24, 24), width=5)
    elif layout == "left_char":
        draw.ellipse([int(w * 0.12), int(h * 0.14), int(w * 0.46), int(h * 0.66)], fill=(238, 174, 112), outline=(24, 24, 24), width=5)
        draw.rectangle([int(w * 0.16), int(h * 0.58), int(w * 0.42), h - 1], fill=(102, 156, 218), outline=(24, 24, 24), width=5)
    else:
        draw.ellipse([int(w * 0.34), int(h * 0.12), int(w * 0.66), int(h * 0.64)], fill=(136, 198, 242), outline=(24, 24, 24), width=5)
        draw.rectangle([int(w * 0.37), int(h * 0.58), int(w * 0.63), h - 1], fill=(242, 222, 140), outline=(24, 24, 24), width=5)

    if mode == "RGB" and not full_bleed:
        draw.rectangle([8, 8, 96, 40], fill=(244, 243, 242))
        draw.rectangle([w - 96, 8, w - 8, 40], fill=(247, 246, 245))

    if path.suffix.lower() in {".jpg", ".jpeg"}:
        im.convert("RGB").save(path, format="JPEG", quality=90)
    else:
        im.save(path, format="PNG")
    return path


def _assert_pure_white_outer_border(image_path: Path, margin: int = 2) -> None:
    with Image.open(image_path) as im:
        arr = np.asarray(im.convert("RGB"))
    h, w, _ = arr.shape
    assert np.all(arr[:margin, :, :] == 255), f"Top border not pure white in {image_path.name}"
    assert np.all(arr[h - margin :, :, :] == 255), f"Bottom border not pure white in {image_path.name}"
    assert np.all(arr[:, :margin, :] == 255), f"Left border not pure white in {image_path.name}"
    assert np.all(arr[:, w - margin :, :] == 255), f"Right border not pure white in {image_path.name}"


def _make_script(cut_count: int) -> EpisodeScript:
    cuts: list[ComicCut] = [
        ComicCut(
            cut_index=1,
            aspect_ratio="4:3",
            layout_slot="top",
            characters=["나이트엘프 사제", "인간 흑마법사"],
            speaker="나이트엘프 사제",
            dialogue="출발 전에 물 20개만\n나눠주실래요?",
            wordless=False,
            visual_prompt="Over-the-shoulder cute 2.5-head chibi SD shot of Priest asking Warlock for water.",
            tail_target="left",
        ),
        ComicCut(
            cut_index=2,
            aspect_ratio="16:9",
            layout_slot="bottom",
            characters=["인간 흑마법사"],
            speaker="인간 흑마법사",
            dialogue="남는 건데 멜론 주스\n20개 여기 있어!",
            wordless=False,
            visual_prompt="Low-angle cute 2.5-head chibi SD shot of Warlock offering glass flasks beside her Voidwalker.",
            tail_target="right",
        ),
        ComicCut(
            cut_index=3,
            aspect_ratio="4:3",
            layout_slot="top",
            characters=["인간 흑마법사", "나이트엘프 사제"],
            speaker="나이트엘프 사제",
            dialogue="상점 주스 말고요.\n법사님 마나 물이요.",
            wordless=False,
            visual_prompt="Side-profile cute 2.5-head chibi SD shot of Priest sighing beside Warlock.",
            tail_target="right",
        ),
        ComicCut(
            cut_index=4,
            aspect_ratio="16:9",
            layout_slot="bottom",
            characters=["인간 흑마법사"],
            speaker=None,
            dialogue=None,
            wordless=True,
            visual_prompt="Dutch-tilt big bust-up close-up shock freeze-frame of Human Warlock on pure #FFFFFF.",
            tail_target="center",
        ),
    ]
    if cut_count >= 5:
        is_last_5 = cut_count == 5
        cuts.append(
            ComicCut(
                cut_index=5,
                aspect_ratio="16:9" if is_last_5 else "4:3",
                layout_slot="bottom" if is_last_5 else "top",
                characters=["오크 전사", "드워프 사냥꾼"] if not is_last_5 else ["인간 흑마법사"],
                speaker="오크 전사" if not is_last_5 else "인간 흑마법사",
                dialogue="나 흑마법사거든?!\n물을 어케 뽑아?!" if is_last_5 else "전사도 무기숙련 올려야\n지능 템 필수거든!",
                wordless=False,
                visual_prompt="High-angle cute 2.5-head chibi SD epilogue reaction on pure #FFFFFF.",
                tail_target="right" if is_last_5 else "left",
            )
        )
    if cut_count >= 6:
        cuts.append(
            ComicCut(
                cut_index=6,
                aspect_ratio="16:9",
                layout_slot="bottom",
                characters=["드워프 사냥꾼"],
                speaker="드워프 사냥꾼",
                dialogue="나도 지능 필요하니까\n오늘 템 다 입찰한다!",
                wordless=False,
                visual_prompt="Low-angle cute 2.5-head chibi SD shot of Dwarf Hunter beside baby bear on pure #FFFFFF.",
                tail_target="left",
            )
        )
    if cut_count == 7:
        cuts.append(
            ComicCut(
                cut_index=7,
                aspect_ratio="16:9",
                layout_slot="bottom",
                characters=["나이트엘프 사제", "오크 전사"],
                speaker="나이트엘프 사제",
                dialogue="다음 파티엔 꼭\n진짜 법사님 모셔요...",
                wordless=False,
                visual_prompt="Back-view cute 2.5-head chibi SD shot of Priest walking away from Orc Warrior.",
                tail_target="left",
            )
        )

    return EpisodeScript(
        episode_number=cut_count,
        source_post_no=f"9205{cut_count}",
        source_title=f"테스트 {cut_count}컷 상황극 에피소드",
        source_url=f"https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=9205{cut_count}",
        subtitle=f"합성 파이프라인 {cut_count}컷 자동 식자 및 무겹침 검증 테스트",
        cuts=cuts,
    )


def _create_cut_fixtures(tmp_path: Path, cut_count: int) -> dict[int, Path]:
    specs = {
        1: ((1200, 896), "two_chars", ".jpg", "RGB"),
        2: ((1376, 768), "right_char", ".png", "RGBA"),
        3: ((1200, 896), "two_chars", ".jpg", "RGB"),
        4: ((1376, 768), "center_char", ".png", "RGB"),
        5: ((1376, 768) if cut_count == 5 else (1200, 896), "right_char" if cut_count == 5 else "two_chars", ".jpg", "RGB"),
        6: ((1376, 768), "left_char", ".png", "RGB"),
        7: ((1376, 768), "two_chars", ".png", "RGB"),
    }
    paths: dict[int, Path] = {}
    for idx in range(1, cut_count + 1):
        size, layout, ext, mode = specs[idx]
        p = tmp_path / f"cut_{idx:02d}{ext}"
        paths[idx] = _make_synthetic_cut(p, size, layout=layout, mode=mode)
    return paths


def test_clean_white_bg_removes_offwhite_noise_and_flattens_rgba() -> None:
    arr = np.full((120, 160, 3), 248, dtype=np.uint8)
    arr[10:30, 10:40] = (242, 241, 243)
    arr[10:30, 50:80] = (246, 246, 246)
    arr[50:90, 50:110] = (40, 120, 210)
    cleaned = clean_white_bg(Image.fromarray(arr, mode="RGB"))
    out = np.asarray(cleaned)

    assert np.all(out[:5, :, :] == 255)
    assert np.all(out[12:28, 12:38] >= 248)
    assert np.all(out[12:28, 52:78] == 255)
    assert out[70, 80, 0] < 60 and out[70, 80, 2] > 180

    rgba = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    rgba_clean = np.asarray(clean_white_bg(rgba))
    assert np.all(rgba_clean == 255)


def test_load_font_returns_usable_font() -> None:
    font = load_font(24, weight="Bold")
    assert font is not None
    dummy = ImageDraw.Draw(Image.new("RGB", (64, 64), (255, 255, 255)))
    assert dummy.textlength("와우 포에버 슬롭툰", font=font) > 0


@pytest.mark.parametrize("cut_count", [4, 5, 6, 7])
def test_compose_episode_4_5_6_7_cuts_and_orphan_cleanup(tmp_path: Path, cut_count: int) -> None:
    script = _make_script(cut_count)
    raw_paths = _create_cut_fixtures(tmp_path / f"raw_{cut_count}", cut_count)
    out_dir = tmp_path / f"out_{cut_count}"
    out_dir.mkdir(parents=True, exist_ok=True)
    # Seed a stale orphan page from an older longer layout to confirm automatic cleanup
    stale_page = out_dir / "page_9.png"
    Image.new("RGB", (100, 100), (255, 255, 255)).save(stale_page)

    result = compose_episode(script, raw_paths, out_dir)
    assert isinstance(result, ComposeResult)
    assert not stale_page.exists(), "Stale orphan page_9.png should be cleaned up automatically"

    assert result.header_path.exists()
    assert result.full_image_path.exists()
    assert result.thumb_path.exists()
    assert (out_dir / "audit.json").exists()
    assert all(p.exists() for p in result.page_paths)

    assert result.audit_report["passed"] is True
    assert result.audit_report["total_overlap_px"] == 0
    assert result.audit_report["total_tooltip_overlap_px"] == 0
    assert result.audit_report["border_pure_white"] is True
    assert result.audit_report["cut_count"] == cut_count

    for cut_audit in result.audit_report["cuts"]:
        assert cut_audit["overlap_px"] == 0
        assert cut_audit["art_height_ratio"] >= 0.50, (
            f"Cut {cut_audit['cut_index']} shrank below 50%: {cut_audit['art_height_ratio']}"
        )

    cut4 = next(c for c in result.audit_report["cuts"] if c["cut_index"] == 4)
    assert cut4["wordless"] is True
    assert cut4["bubble_count"] == 0
    assert abs(cut4["art_cx"] - BOT_BOX_W / 2.0) <= 2.0

    with Image.open(result.header_path) as hdr:
        assert hdr.size == (PAGE_W, HEADER_H)
    _assert_pure_white_outer_border(result.header_path)

    expected_map = {
        4: [(PAGE_W, FULL_PAGE_H), (PAGE_W, FULL_PAGE_H)],
        5: [(PAGE_W, FULL_PAGE_H), (PAGE_W, FULL_PAGE_H), (PAGE_W, EPILOGUE_PAGE_H)],
        6: [(PAGE_W, FULL_PAGE_H), (PAGE_W, FULL_PAGE_H), (PAGE_W, FULL_PAGE_H)],
        7: [(PAGE_W, FULL_PAGE_H), (PAGE_W, FULL_PAGE_H), (PAGE_W, FULL_PAGE_H), (PAGE_W, EPILOGUE_PAGE_H)],
    }
    expected_sizes = expected_map[cut_count]
    assert len(result.page_paths) == len(expected_sizes)
    for p_path, exp_size in zip(result.page_paths, expected_sizes):
        with Image.open(p_path) as pim:
            assert pim.size == exp_size
        _assert_pure_white_outer_border(p_path)

    with Image.open(result.full_image_path) as full_im:
        assert full_im.size[0] == PAGE_W
        assert full_im.size[1] > FULL_PAGE_H
    with Image.open(result.thumb_path) as thumb_im:
        assert thumb_im.size == THUMB_SIZE


def test_collision_solver_guarantees_zero_overlap_on_full_bleed_stress_fixtures(tmp_path: Path) -> None:
    cuts = [
        ComicCut(
            cut_index=1,
            aspect_ratio="4:3",
            layout_slot="top",
            characters=["오크 전사"],
            speaker="오크 전사",
            dialogue="아주 길고 시끄러운 대사라도\n캐릭터와 절대 안 겹쳐!",
            wordless=False,
            visual_prompt="Dense full bleed test cut 1.",
            tail_target="right",
        ),
        ComicCut(
            cut_index=2,
            aspect_ratio="16:9",
            layout_slot="bottom",
            characters=["언데드 성기사"],
            speaker="언데드 성기사",
            dialogue="중앙 꼬리 상단 말풍선도\n겹침 0px 보장!",
            wordless=False,
            visual_prompt="Dense full bleed test cut 2.",
            tail_target="center",
        ),
        ComicCut(
            cut_index=3,
            aspect_ratio="4:3",
            layout_slot="top",
            characters=["노움 도적"],
            speaker="노움 도적",
            dialogue="중앙 상단 꼬리 테스트!",
            wordless=False,
            visual_prompt="Dense full bleed test cut 3.",
            tail_target="center",
        ),
        ComicCut(
            cut_index=4,
            aspect_ratio="16:9",
            layout_slot="bottom",
            characters=["드워프 사냥꾼"],
            speaker=None,
            dialogue=None,
            wordless=True,
            visual_prompt="Silent freeze frame cut 4.",
            tail_target="center",
        ),
    ]
    script = EpisodeScript(
        episode_number=99,
        source_post_no="99999",
        source_title="충돌 회피 스트레스 테스트",
        source_url="https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=99999",
        subtitle="풀블리드 최악 케이스에서도 overlap_px == 0 강제 보장",
        cuts=cuts,
    )
    raw_paths = {
        idx: _make_synthetic_cut(
            tmp_path / f"bleed_{idx}.png",
            (1200, 896) if idx % 2 == 1 else (1376, 768),
            full_bleed=True,
        )
        for idx in range(1, 5)
    }

    result = compose_episode(script, raw_paths, tmp_path / "out_bleed")
    assert result.audit_report["passed"] is True
    assert result.audit_report["total_overlap_px"] == 0
    for c in result.audit_report["cuts"]:
        assert c["overlap_px"] == 0


def test_bottom_box_prevents_ant_shrinking_and_targets_actual_speaker() -> None:
    """2-character wide bottom boxes use speaker-aligned top bubbles & keep art tall;
    narrow 1-character cuts keep art >= 75% box height.
    """
    raw_two = Image.new("RGB", (960, 540), (255, 255, 255))
    d = ImageDraw.Draw(raw_two)
    d.ellipse([120, 120, 380, 520], fill=(120, 180, 240))
    d.ellipse([580, 120, 840, 520], fill=(240, 140, 140))

    cut_left = ComicCut(
        cut_index=2,
        aspect_ratio="16:9",
        layout_slot="bottom",
        characters=["나이트엘프 사제", "언데드 성기사"],
        speaker="나이트엘프 사제",
        dialogue="왼쪽 캐릭터가\n말하는 대사!",
        visual_prompt="Left priest speaks while right paladin listens.",
        tail_target="left",
    )
    _, audit_left = _compose_bottom_box_panel(cut_left, raw_two)
    assert audit_left["overlap_px"] == 0
    assert audit_left["bubble_side_resolved"] == "left"
    assert audit_left["art_height_ratio"] >= 0.55

    cut_right = ComicCut(
        cut_index=4,
        aspect_ratio="16:9",
        layout_slot="bottom",
        characters=["나이트엘프 사제", "언데드 성기사"],
        speaker="언데드 성기사",
        dialogue="오른쪽 캐릭터가\n말하는 대사!",
        visual_prompt="Right paladin speaks while left priest listens.",
        tail_target="right",
    )
    _, audit_right = _compose_bottom_box_panel(cut_right, raw_two)
    assert audit_right["overlap_px"] == 0
    assert audit_right["bubble_side_resolved"] == "right"
    assert audit_right["art_height_ratio"] >= 0.55

    # Explicit bubble_side override works on 1-character + NPC cuts
    cut_override = ComicCut(
        cut_index=6,
        aspect_ratio="16:9",
        layout_slot="bottom",
        characters=["언데드 성기사"],
        speaker="언데드 성기사",
        dialogue="오른쪽 화자 고정!",
        visual_prompt="Vendor NPC on left, Undead Paladin on right.",
        tail_target="right",
        bubble_side="right",
    )
    _, audit_override = _compose_bottom_box_panel(cut_override, raw_two)
    assert audit_override["overlap_px"] == 0
    assert audit_override["bubble_side_resolved"] == "right"

    # Narrow 1-character cut stays large via side-split
    raw_narrow = Image.new("RGB", (600, 600), (255, 255, 255))
    dn = ImageDraw.Draw(raw_narrow)
    dn.ellipse([120, 60, 480, 560], fill=(160, 140, 230))
    cut_single = ComicCut(
        cut_index=2,
        aspect_ratio="16:9",
        layout_slot="bottom",
        characters=["인간 흑마법사"],
        speaker="인간 흑마법사",
        dialogue="1인 컷은 큼직하게!",
        visual_prompt="Single cute 2.5-head SD character centered.",
        tail_target="right",
    )
    _, audit_single = _compose_bottom_box_panel(cut_single, raw_narrow)
    assert audit_single["overlap_px"] == 0
    assert audit_single["art_height_ratio"] >= 0.75


def test_top_open_and_wide_bottom_box_ignore_opposing_bubble_side_for_speaker_alignment() -> None:
    """Regression (#25): when tail_target='left' and an opposing bubble_side='right' is supplied,
    both top open panels and 2-char/wide bottom boxes MUST place the overhead bubble directly
    above the left speaker (`bubble_center_x < panel_w * 0.5`), never over the right listener/mob.
    """
    # 1. Top open panel (900x830): speaker on left, mob/listener on right
    raw_top = Image.new("RGB", (1200, 896), (255, 255, 255))
    dt = ImageDraw.Draw(raw_top)
    dt.ellipse([110, 260, 430, 860], fill=(138, 120, 212), outline=(24, 24, 24), width=5)
    dt.ellipse([740, 280, 1080, 860], fill=(216, 126, 118), outline=(24, 24, 24), width=5)

    cut_top = ComicCut(
        cut_index=1,
        aspect_ratio="4:3",
        layout_slot="top",
        characters=["나이트엘프 사제", "노움 도적"],
        speaker="나이트엘프 사제",
        dialogue="수사 솔플로 한 마리씩\n15분째 잡고 있어요...",
        visual_prompt="Left Night Elf Priest fighting SD bandit mobs on right.",
        tail_target="left",
        bubble_side="right",  # Opposing inertia from writer must be ignored!
    )
    top_panel, top_audit = _compose_top_open_panel(cut_top, raw_top)
    assert top_audit["overlap_px"] == 0
    assert top_audit["art_bbox"] is not None
    art_top_y = int(top_audit["art_bbox"][1])
    assert art_top_y > 40
    top_strip = np.asarray(top_panel.convert("RGB"))[: max(1, art_top_y - 4), :, :]
    non_white_mask = np.any(top_strip < 245, axis=2)
    xs = np.where(non_white_mask)[1]
    assert xs.size > 200, "Expected rendered speech bubble ink pixels above artwork"
    top_bubble_cx = float(xs.mean())
    assert top_bubble_cx < PAGE_W * 0.5, (
        f"Top open bubble drifted to right side (cx={top_bubble_cx:.1f} >= {PAGE_W * 0.5})"
    )

    # 2. 2-character / wide bottom box (844x436): tail_target='left' + opposing bubble_side='right'
    raw_bot = Image.new("RGB", (1376, 768), (255, 255, 255))
    db = ImageDraw.Draw(raw_bot)
    db.ellipse([140, 180, 500, 740], fill=(138, 120, 212), outline=(24, 24, 24), width=5)
    db.ellipse([860, 180, 1220, 740], fill=(224, 152, 112), outline=(24, 24, 24), width=5)

    cut_bot = ComicCut(
        cut_index=2,
        aspect_ratio="16:9",
        layout_slot="bottom",
        characters=["나이트엘프 사제", "노움 도적"],
        speaker="나이트엘프 사제",
        dialogue="드디어 남작 처치!\n얼른 루팅부터 해야—",
        visual_prompt="Left Night Elf Priest cheering beside defeated SD boss on right.",
        tail_target="left",
        bubble_side="right",  # Opposing inertia must be ignored in top_* box mode!
    )
    _, bot_audit = _compose_bottom_box_panel(cut_bot, raw_bot)
    assert bot_audit["overlap_px"] == 0
    assert bot_audit["bubble_side_resolved"] == "left"
    assert bot_audit["bubble_center"][0] < BOT_BOX_W * 0.5, (
        f"Bottom box bubble drifted right (cx={bot_audit['bubble_center'][0]} >= {BOT_BOX_W * 0.5})"
    )


def test_watermark_footer_rendering_and_append(tmp_path: Path) -> None:
    footer = render_watermark_footer(width=PAGE_W, site_url="https://slopwow.github.io/")
    assert footer.size == (PAGE_W, WATERMARK_FOOTER_H)
    assert footer.mode == "RGB"

    footer_path = tmp_path / "watermark_footer.png"
    footer.save(footer_path)
    _assert_pure_white_outer_border(footer_path, margin=6)

    arr = np.asarray(footer)
    dark_px = np.sum((arr[:, :, 0] < 40) & (arr[:, :, 1] < 40) & (arr[:, :, 2] < 40))
    assert dark_px > 2000
    sky_px = np.sum((arr[:, :, 2] > 180) & (arr[:, :, 1] > 120) & (arr[:, :, 0] < 60))
    assert sky_px > 120

    narrow = render_watermark_footer(width=480, site_url="slopwow.github.io")
    assert narrow.size == (480, WATERMARK_FOOTER_H)

    base_im = Image.new("RGB", (PAGE_W, 600), (255, 255, 255))
    stitched = append_watermark_footer(base_im, site_url="slopwow.github.io")
    assert stitched.size == (PAGE_W, 600 + WATERMARK_FOOTER_H)

    unchanged = append_watermark_footer(base_im, site_url="")
    assert unchanged.size == (PAGE_W, 600)


def test_compose_episode_watermark_default_optout_and_idempotent_retrofit(tmp_path: Path) -> None:
    script = _make_script(4)
    raw_paths = _create_cut_fixtures(tmp_path / "raw_wm", 4)

    out_with_wm = tmp_path / "with_wm"
    res_wm = compose_episode(script, raw_paths, out_with_wm)
    assert res_wm.audit_report["passed"] is True
    assert res_wm.audit_report["watermarked"] is True
    assert res_wm.audit_report["watermark_url"] == "slopwow.github.io"
    assert (out_with_wm / "episode_full_raw.jpg").exists()

    out_no_wm = tmp_path / "no_wm"
    res_no = compose_episode(script, raw_paths, out_no_wm, watermark_url=None)
    assert res_no.audit_report["passed"] is True
    assert res_no.audit_report["watermarked"] is False
    assert not (out_no_wm / "episode_full_raw.jpg").exists()

    with Image.open(res_wm.full_image_path) as im_wm, Image.open(res_no.full_image_path) as im_no:
        assert im_wm.size == (PAGE_W, im_no.size[1] + WATERMARK_FOOTER_H)
    _assert_pure_white_outer_border(res_wm.full_image_path, margin=2)

    expected_h = res_wm.audit_report["full_size"][1]
    retrofit_episode_watermark(out_with_wm, site_url="slopwow.github.io")
    with Image.open(out_with_wm / "episode_full.jpg") as after_re:
        assert after_re.size == (PAGE_W, expected_h)

    legacy_dir = tmp_path / "legacy_ep"
    legacy_dir.mkdir()
    orig_h = 1000
    Image.new("RGB", (PAGE_W, orig_h), (255, 255, 255)).save(
        legacy_dir / "episode_full.jpg", format="JPEG", quality=95
    )

    stamped1 = retrofit_episode_watermark(legacy_dir, site_url="slopwow.github.io")
    assert stamped1 == legacy_dir / "episode_full.jpg"
    assert (legacy_dir / "episode_full_raw.jpg").exists()
    with Image.open(stamped1) as s1:
        assert s1.size == (PAGE_W, orig_h + WATERMARK_FOOTER_H)

    stamped2 = retrofit_episode_watermark(legacy_dir, site_url="slopwow.github.io")
    with Image.open(stamped2) as s2:
        assert s2.size == (PAGE_W, orig_h + WATERMARK_FOOTER_H)


def test_cli_six_clean_commands_sync_record_and_reject_legacy(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n', encoding="utf-8")

    # 1. Seed script.json + raw_cuts for ep005 and run `compose`
    script = _make_script(5)
    ep_dir = tmp_path / "data" / "episodes" / "ep005"
    ep_dir.mkdir(parents=True, exist_ok=True)
    script_path = ep_dir / "script.json"
    script_path.write_text(script.model_dump_json(indent=2), encoding="utf-8")
    _create_cut_fixtures(tmp_path / "data" / "raw_cuts" / "ep005", 5)

    rc_comp = cli.main(["--project-root", str(tmp_path), "compose", "ep005", "--skip-site"])
    assert rc_comp == 0

    # Verify record.json and data/episodes.json are 100% identical metadata
    record_json = json.loads((ep_dir / "record.json").read_text(encoding="utf-8"))
    episodes_list = json.loads((tmp_path / "data" / "episodes.json").read_text(encoding="utf-8"))
    assert len(episodes_list) == 1
    assert episodes_list[0] == record_json
    assert record_json["title"] == script.source_title
    assert record_json["cut_count"] == 5
    assert len(record_json["page_images_rel"]) == 3

    # 2. `watermark` (and backward-compatible alias `watermark-all`) are idempotent
    with Image.open(ep_dir / "episode_full.jpg") as im_before:
        before_size = im_before.size
    assert cli.main(["--project-root", str(tmp_path), "watermark", "--episode-id", "ep005"]) == 0
    assert cli.main(["--project-root", str(tmp_path), "watermark-all", "--site-url", "slopwow.github.io"]) == 0
    with Image.open(ep_dir / "episode_full.jpg") as im_after:
        assert im_after.size == before_size

    # 3. `generate --post-no ... --dry-run` and `generate --from-script ... --dry-run`
    fake_post = GalleryPost(
        post_no="99888",
        title="던전 탱커가 마나 물약을 요구한 사연",
        url="https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=99888",
        author="포에버갤러",
        date_str="2026-11-21",
        recommends=35,
        comments_count=12,
        body="탱커가 지능 반지 입찰한 상황극 본문",
    )
    capsys.readouterr()
    with patch("wow_sloptoon.cli.GalleryScout.fetch_post_detail", return_value=fake_post):
        assert cli.main(["--project-root", str(tmp_path), "generate", "--post-no", "99888", "--dry-run"]) == 0
    out_gen = capsys.readouterr().out
    assert "[DRY-RUN]" in out_gen
    assert '"source_post_no": "99888"' in out_gen

    assert (
        cli.main(["--project-root", str(tmp_path), "generate", "--from-script", str(script_path), "--dry-run"])
        == 0
    )

    # Failing script gate returns exit code 1
    bad_cuts = list(script.cuts)
    bad_cuts[0] = bad_cuts[0].model_copy(update={"dialogue": "119 불러야 하나 진짜 어이없네!"})
    bad_script_path = tmp_path / "bad_script.json"
    bad_script_path.write_text(script.model_copy(update={"cuts": bad_cuts}).model_dump_json(), encoding="utf-8")
    assert (
        cli.main(["--project-root", str(tmp_path), "generate", "--from-script", str(bad_script_path), "--dry-run"])
        == 1
    )

    # 4. `autopilot --dry-run` (mocked scout)
    with patch("wow_sloptoon.cli.GalleryScout.scout_candidates", return_value=[(fake_post, 99.5)]):
        assert cli.main(["--project-root", str(tmp_path), "autopilot", "--dry-run"]) == 0

    # 5. Permanently retired commands/flags fail argparse with exit code 2
    for retired_argv in (
        ["pack-dc", "ep005"],
        ["queue"],
        ["publish-next"],
        ["mark-published", "ep005"],
        ["run-once"],
        ["serve"],
        ["generate", "--post-no", "1", "--layout", "v4"],
    ):
        with pytest.raises(SystemExit) as exc_info:
            cli.main(retired_argv)
        assert exc_info.value.code == 2


def test_policy_compliance_no_captcha_bypass_auto_post_or_retired_modules() -> None:
    """Verify retired V4/DC modules are absent and remaining pipeline avoids CAPTCHA bypass / legacy SDKs."""
    project_root = Path(__file__).resolve().parents[1]
    for retired in (
        project_root / "src" / "wow_sloptoon" / "layouts.py",
        project_root / "src" / "wow_sloptoon" / "dc_packager.py",
        project_root / "src" / "wow_sloptoon" / "scheduler.py",
    ):
        assert not retired.exists(), f"Retired module still exists: {retired}"

    checked_files = [
        project_root / "src" / "wow_sloptoon" / "cli.py",
        project_root / "src" / "wow_sloptoon" / "composer.py",
        project_root / "src" / "wow_sloptoon" / "site_builder.py",
        project_root / "setup-automation.ps1",
        project_root / "run-factory.ps1",
        project_root / ".github" / "workflows" / "auto-sloptoon.yml",
    ]
    forbidden_tokens = [
        "2captcha",
        "anticaptcha",
        "capsolver",
        "solve_captcha",
        "bypass_captcha",
        "playwright",
        "selenium",
        "puppeteer",
        "requests.post(",
        "httpx.post(",
        "Invoke-WebRequest",
        "google-generativeai",
        "gemini-2.5-",
    ]
    for file_path in checked_files:
        assert file_path.exists(), f"Missing expected file: {file_path}"
        content = file_path.read_text(encoding="utf-8").lower()
        for token in forbidden_tokens:
            assert token.lower() not in content, f"Forbidden policy/tech token '{token}' in {file_path.name}"
