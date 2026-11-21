"""Tests for `wow_sloptoon.composer`, `wow_sloptoon.dc_packager`, `wow_sloptoon.scheduler`, and CLI automation."""

from __future__ import annotations

import json
import sys
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
    WATERMARK_FOOTER_H,
    ComposeResult,
    append_watermark_footer,
    clean_white_bg,
    compose_episode,
    load_font,
    render_watermark_footer,
    retrofit_episode_watermark,
)
from wow_sloptoon.dc_packager import (
    DcUploadPack,
    build_dc_write_url,
    copy_to_clipboard,
    create_dc_upload_pack,
    format_post_body,
    open_dc_write_page,
    open_pack_folder,
)
from wow_sloptoon.models import ComicCut, EpisodeRecord, EpisodeScript, GalleryPost
from wow_sloptoon.scheduler import (
    get_next_unpublished,
    load_publish_queue,
    mark_episode_packed,
    mark_episode_published,
    notify_new_episode_ready,
    sync_publish_queue,
)


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
        # Worst-case stress test: solid colored artwork spanning entire frame with zero white margin
        draw.rectangle([0, 0, w - 1, h - 1], fill=(92, 132, 210))
        draw.ellipse([w // 4, h // 4, 3 * w // 4, 3 * h // 4], fill=(245, 196, 118), outline=(25, 25, 25), width=6)
    elif layout == "two_chars":
        # Two chibi characters standing on left and right, touching bottom edge, tall hoods reaching near top
        # Left character (Night Elf Priest / Dwarf Hunter)
        draw.ellipse([int(w * 0.14), int(h * 0.24), int(w * 0.42), int(h * 0.62)], fill=(140, 210, 145), outline=(24, 24, 24), width=5)
        draw.rectangle([int(w * 0.18), int(h * 0.56), int(w * 0.38), h - 1], fill=(214, 128, 178), outline=(24, 24, 24), width=5)
        # Right character (Human Warlock / Undead Paladin)
        draw.ellipse([int(w * 0.58), int(h * 0.22), int(w * 0.86), int(h * 0.60)], fill=(158, 134, 224), outline=(24, 24, 24), width=5)
        draw.rectangle([int(w * 0.62), int(h * 0.54), int(w * 0.82), h - 1], fill=(78, 92, 152), outline=(24, 24, 24), width=5)
    elif layout == "right_char":
        # Reaction character positioned on the right side
        draw.ellipse([int(w * 0.54), int(h * 0.14), int(w * 0.88), int(h * 0.66)], fill=(184, 148, 226), outline=(24, 24, 24), width=5)
        draw.rectangle([int(w * 0.58), int(h * 0.58), int(w * 0.84), h - 1], fill=(95, 176, 132), outline=(24, 24, 24), width=5)
    elif layout == "left_char":
        # Reaction character positioned on the left side
        draw.ellipse([int(w * 0.12), int(h * 0.14), int(w * 0.46), int(h * 0.66)], fill=(238, 174, 112), outline=(24, 24, 24), width=5)
        draw.rectangle([int(w * 0.16), int(h * 0.58), int(w * 0.42), h - 1], fill=(102, 156, 218), outline=(24, 24, 24), width=5)
    else:
        # Center character (e.g. silent shock freeze-frame)
        draw.ellipse([int(w * 0.34), int(h * 0.12), int(w * 0.66), int(h * 0.64)], fill=(136, 198, 242), outline=(24, 24, 24), width=5)
        draw.rectangle([int(w * 0.37), int(h * 0.58), int(w * 0.63), h - 1], fill=(242, 222, 140), outline=(24, 24, 24), width=5)

    # Add subtle off-white JPEG noise smudges on RGB fixtures to test pure-white normalization
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
            dialogue="저기 법사님, 마나 없는데 물 20개만 좀 뽑아주세요...",
            wordless=False,
            visual_prompt="Chibi Night Elf Priest asking Human Warlock for conjured water on pure white background.",
            tail_target="left",
        ),
        ComicCut(
            cut_index=2,
            aspect_ratio="16:9",
            layout_slot="bottom",
            characters=["인간 흑마법사"],
            speaker="인간 흑마법사",
            dialogue="어... 이거라도 드릴게요! (멜론 주스 20개)",
            wordless=False,
            visual_prompt="Chibi Human Warlock offering melon juice cartons on pure white background.",
            tail_target="right",
        ),
        ComicCut(
            cut_index=3,
            aspect_ratio="4:3",
            layout_slot="top",
            characters=["인간 흑마법사", "나이트엘프 사제"],
            speaker="인간 흑마법사",
            dialogue="이거 아닌가.... 혹시 생석 달라는 건가? 이거 1개밖에 못 만드는데...",
            wordless=False,
            visual_prompt="Confused Human Warlock tilting head with healthstone on pure white background.",
            tail_target="left",
        ),
        ComicCut(
            cut_index=4,
            aspect_ratio="16:9",
            layout_slot="bottom",
            characters=["스카이본 마법사"],
            speaker=None,
            dialogue=None,
            wordless=True,
            visual_prompt="Shocked Skyborne Mage deadpan freeze-frame centered on pure white background.",
            tail_target="center",
        ),
    ]
    if cut_count >= 5:
        cuts.append(
            ComicCut(
                cut_index=5,
                aspect_ratio="16:9" if cut_count == 5 else "4:3",
                layout_slot="bottom" if cut_count == 5 else "top",
                characters=["오크 전사", "드워프 사냥꾼"] if cut_count == 6 else ["인간 흑마법사"],
                speaker="오크 전사" if cut_count == 6 else "인간 흑마법사",
                dialogue=(
                    "ㅇㅈ 전사도 무기숙련 빨리 올려야 해서 지능 템 필수거든요!"
                    if cut_count == 6
                    else "멜론 주스도 맛있는 건데..."
                ),
                wordless=False,
                visual_prompt="Chibi character epilogue reaction on pure white background.",
                tail_target="left" if cut_count == 6 else "right",
            )
        )
    if cut_count == 6:
        cuts.append(
            ComicCut(
                cut_index=6,
                aspect_ratio="16:9",
                layout_slot="bottom",
                characters=["드워프 사냥꾼"],
                speaker="드워프 사냥꾼",
                dialogue="아 몰라!! 나도 힘 필요하고 지능 필요하니까 오늘 던전 템 다 입찰한다!!",
                wordless=False,
                visual_prompt="Furious chibi Dwarf Hunter with blunderbuss on pure white background.",
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
    }
    paths: dict[int, Path] = {}
    for idx in range(1, cut_count + 1):
        size, layout, ext, mode = specs[idx]
        p = tmp_path / f"raw_cut_{idx}{ext}"
        paths[idx] = _make_synthetic_cut(p, size, layout=layout, mode=mode)
    return paths


def test_clean_white_bg_removes_offwhite_noise_and_flattens_rgba() -> None:
    arr = np.full((120, 160, 3), 248, dtype=np.uint8)
    arr[10:30, 10:40] = (242, 241, 243)  # Faint neutral JPEG haze smoothly lifted toward white
    arr[10:30, 50:80] = (246, 246, 246)  # Near-white background strictly clamped to #FFFFFF
    arr[50:90, 50:110] = (40, 120, 210)  # Saturated character body
    cleaned = clean_white_bg(Image.fromarray(arr, mode="RGB"))
    out = np.asarray(cleaned)

    assert np.all(out[:5, :, :] == 255)
    assert np.all(out[12:28, 12:38] >= 248)
    assert np.all(out[12:28, 52:78] == 255)
    assert out[70, 80, 0] < 60 and out[70, 80, 2] > 180

    # Transparent RGBA must flatten onto pure #FFFFFF, never black
    rgba = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    rgba_clean = np.asarray(clean_white_bg(rgba))
    assert np.all(rgba_clean == 255)


def test_load_font_returns_usable_font() -> None:
    font = load_font(24, weight="Bold")
    assert font is not None
    dummy = ImageDraw.Draw(Image.new("RGB", (64, 64), (255, 255, 255)))
    width = dummy.textlength("와우 포에버 슬롭툰", font=font)
    assert width > 0


@pytest.mark.parametrize("cut_count", [4, 5, 6])
def test_compose_episode_4_5_6_cuts(tmp_path: Path, cut_count: int) -> None:
    script = _make_script(cut_count)
    raw_paths = _create_cut_fixtures(tmp_path / f"raw_{cut_count}", cut_count)
    out_dir = tmp_path / f"out_{cut_count}"

    result = compose_episode(script, raw_paths, out_dir)
    assert isinstance(result, ComposeResult)

    # All files exist
    assert result.header_path.exists()
    assert result.full_image_path.exists()
    assert result.thumb_path.exists()
    assert all(p.exists() for p in result.page_paths)

    # Audit passed with strictly zero overlap and pure white outer borders
    assert result.audit_report["passed"] is True
    assert result.audit_report["total_overlap_px"] == 0
    assert result.audit_report["border_pure_white"] is True
    assert result.audit_report["cut_count"] == cut_count

    for cut_audit in result.audit_report["cuts"]:
        assert cut_audit["overlap_px"] == 0

    # Verify wordless cut (Cut 4) has 0 bubbles and centered artwork
    cut4 = next(c for c in result.audit_report["cuts"] if c["cut_index"] == 4)
    assert cut4["wordless"] is True
    assert cut4["bubble_count"] == 0
    assert abs(cut4["art_cx"] - BOT_BOX_W / 2.0) <= 2.0

    # Verify exact page counts and dimensions
    with Image.open(result.header_path) as hdr:
        assert hdr.size == (PAGE_W, HEADER_H)
    _assert_pure_white_outer_border(result.header_path)

    if cut_count == 4:
        assert len(result.page_paths) == 2
        expected_page_sizes = [(PAGE_W, FULL_PAGE_H), (PAGE_W, FULL_PAGE_H)]
    elif cut_count == 5:
        assert len(result.page_paths) == 3
        expected_page_sizes = [(PAGE_W, FULL_PAGE_H), (PAGE_W, FULL_PAGE_H), (PAGE_W, EPILOGUE_PAGE_H)]
    else:
        assert len(result.page_paths) == 3
        expected_page_sizes = [(PAGE_W, FULL_PAGE_H), (PAGE_W, FULL_PAGE_H), (PAGE_W, FULL_PAGE_H)]

    for p_path, exp_size in zip(result.page_paths, expected_page_sizes):
        with Image.open(p_path) as pim:
            assert pim.size == exp_size
        _assert_pure_white_outer_border(p_path)

    # Verify full stitched image and thumbnail dimensions
    with Image.open(result.full_image_path) as full_im:
        assert full_im.size[0] == PAGE_W
        assert full_im.size[1] > FULL_PAGE_H
    with Image.open(result.thumb_path) as thumb_im:
        assert thumb_im.size == THUMB_SIZE


def test_collision_solver_guarantees_zero_overlap_on_full_bleed_stress_fixtures(tmp_path: Path) -> None:
    """Even with 100% solid-colored full-bleed raw frames, the solver enforces overlap_px == 0."""
    cuts = [
        ComicCut(
            cut_index=1,
            aspect_ratio="4:3",
            layout_slot="top",
            characters=["오크 전사"],
            speaker="오크 전사",
            dialogue="아주 길고 시끄러운 대사가 들어가도 절대 캐릭터와 말풍선이 겹치면 안 됩니다!",
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
            dialogue="중앙 꼬리 테스트! 상단 말풍선 아래에 깔끔하게 캐릭터를 배치해 겹침 0px 보장!",
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
            dialogue="중앙 상단 꼬리 테스트 대사입니다.",
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
    raw_paths: dict[int, Path] = {}
    for idx in range(1, 5):
        sz = (1200, 896) if idx % 2 == 1 else (1376, 768)
        raw_paths[idx] = _make_synthetic_cut(tmp_path / f"bleed_{idx}.png", sz, full_bleed=True)

    result = compose_episode(script, raw_paths, tmp_path / "out_bleed")
    assert result.audit_report["passed"] is True
    assert result.audit_report["total_overlap_px"] == 0
    for c in result.audit_report["cuts"]:
        assert c["overlap_px"] == 0


def test_dc_packager_standard_and_split_outputs(tmp_path: Path) -> None:
    record = EpisodeRecord(
        episode_id="ep001",
        episode_number=1,
        title="흑마법사가 물을 어케 줌?",
        subtitle="흑마를 법사로 착각한 힐러와 뉴비 흑마의 멜론 주스 상황극",
        source_post_no="92059",
        source_url="https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=92059",
        created_at="2026-11-21",
        cut_count=5,
        cast_used=["나이트엘프 사제", "인간 흑마법사", "스카이본 마법사"],
        full_image_rel="assets/episodes/ep001/episode_full.jpg",
        thumb_image_rel="assets/episodes/ep001/thumb.jpg",
        page_images_rel=["assets/episodes/ep001/page_1.png"],
    )

    # 1. Standard episode_full.jpg under height & byte limits -> single optimized JPG
    normal_img = tmp_path / "episode_full.jpg"
    _make_synthetic_cut(normal_img, (900, 2600), layout="two_chars")
    pack_dir = tmp_path / "upload_pack" / "ep001"
    pack = create_dc_upload_pack(
        record=record,
        full_image_path=normal_img,
        output_dir=pack_dir,
        archive_base_url="https://example.github.io/wow-forever-sloptoon/",
    )

    assert isinstance(pack, DcUploadPack)
    assert pack.pack_dir == pack_dir
    assert len(pack.image_paths) == 1
    assert pack.image_paths[0].exists()
    assert pack.image_paths[0].stat().st_size <= int(4.5 * 1024 * 1024)
    assert pack.title_text == "[와포슬롭툰]흑마법사가 물을 어케 줌?"
    assert "EP." not in pack.title_text
    assert pack.write_url == "https://gall.dcinside.com/mgallery/board/write/?id=wowforever"

    title_file = pack_dir / "post_title.txt"
    body_file = pack_dir / "post_body.txt"
    assert title_file.read_text(encoding="utf-8") == pack.title_text
    body_content = body_file.read_text(encoding="utf-8")
    assert body_content == pack.body_text
    assert record.source_url in body_content
    assert "https://example.github.io/wow-forever-sloptoon/episode.html?id=ep001" in body_content
    assert "시안 C" in body_content
    assert "인벤" not in body_content
    assert "인벤" not in pack.title_text

    # 2. Oversized tall image with white gutters -> safe white-gutter multi-part JPG split
    tall_img = tmp_path / "tall_episode.jpg"
    tall = Image.new("RGB", (900, 8200), (255, 255, 255))
    td = ImageDraw.Draw(tall)
    for y0 in (100, 1400, 2700, 4200, 5600, 7000):
        td.rectangle([60, y0, 840, y0 + 1000], fill=(120, 160, 220), outline=(20, 20, 20), width=4)
    tall.save(tall_img, format="JPEG", quality=92)

    split_dir = tmp_path / "upload_pack" / "ep001_split"
    split_pack = create_dc_upload_pack(
        record=record,
        full_image_path=tall_img,
        output_dir=split_dir,
        max_slice_height=4500,
    )
    assert len(split_pack.image_paths) >= 2
    total_h = 0
    for part_path in split_pack.image_paths:
        assert part_path.exists()
        with Image.open(part_path) as pim:
            assert pim.size[0] == 900
            assert pim.size[1] <= 4500
            total_h += pim.size[1]
    assert total_h == 8200


def test_open_dc_write_page_and_clipboard_policy_safety() -> None:
    assert build_dc_write_url() == "https://gall.dcinside.com/mgallery/board/write/?id=wowforever"
    with pytest.raises(ValueError):
        build_dc_write_url("bad id/../../")

    with patch("wow_sloptoon.dc_packager.webbrowser.open", return_value=True) as mock_open:
        url = open_dc_write_page("wowforever")
        assert url == "https://gall.dcinside.com/mgallery/board/write/?id=wowforever"
        mock_open.assert_called_once_with(url, new=2)

    # Clipboard helper must return bool and never raise
    result = copy_to_clipboard("와우 포에버 슬롭툰 클립보드 테스트")
    assert isinstance(result, bool)


def test_watermark_footer_rendering_and_append(tmp_path: Path) -> None:
    footer = render_watermark_footer(width=PAGE_W, site_url="https://slopwow.github.io/")
    assert footer.size == (PAGE_W, WATERMARK_FOOTER_H)
    assert footer.mode == "RGB"

    footer_path = tmp_path / "watermark_footer.png"
    footer.save(footer_path)
    _assert_pure_white_outer_border(footer_path, margin=6)

    arr = np.asarray(footer)
    # Must contain crisp dark Sloptoon ink pixels (rounded card border / pill / typography)
    dark_px = np.sum((arr[:, :, 0] < 40) & (arr[:, :, 1] < 40) & (arr[:, :, 2] < 40))
    assert dark_px > 2000
    # Must contain #0EA5E9 sky-blue accent pixels (high blue, mid-high green, low red)
    sky_px = np.sum((arr[:, :, 2] > 180) & (arr[:, :, 1] > 120) & (arr[:, :, 0] < 60))
    assert sky_px > 120

    # Narrow width auto-fit must still succeed cleanly
    narrow = render_watermark_footer(width=480, site_url="slopwow.github.io")
    assert narrow.size == (480, WATERMARK_FOOTER_H)

    # Append seamlessly increases height by exact WATERMARK_FOOTER_H
    base_im = Image.new("RGB", (PAGE_W, 600), (255, 255, 255))
    stitched = append_watermark_footer(base_im, site_url="slopwow.github.io")
    assert stitched.size == (PAGE_W, 600 + WATERMARK_FOOTER_H)

    # Empty site_url acts as clean opt-out
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

    # Calling retrofit on an already-watermarked composed episode must NEVER double-stamp
    expected_h = res_wm.audit_report["full_size"][1]
    retrofit_episode_watermark(out_with_wm, site_url="slopwow.github.io")
    with Image.open(out_with_wm / "episode_full.jpg") as after_re:
        assert after_re.size == (PAGE_W, expected_h)

    # Legacy un-watermarked episode retrofit: backs up raw once and stays strictly idempotent
    legacy_dir = tmp_path / "legacy_ep"
    legacy_dir.mkdir()
    orig_h = 1000
    orig_im = Image.new("RGB", (PAGE_W, orig_h), (255, 255, 255))
    orig_im.save(legacy_dir / "episode_full.jpg", format="JPEG", quality=95)

    stamped1 = retrofit_episode_watermark(legacy_dir, site_url="slopwow.github.io")
    assert stamped1 == legacy_dir / "episode_full.jpg"
    assert (legacy_dir / "episode_full_raw.jpg").exists()
    with Image.open(legacy_dir / "episode_full_raw.jpg") as raw_bak:
        assert raw_bak.size == (PAGE_W, orig_h)
    with Image.open(stamped1) as s1:
        assert s1.size == (PAGE_W, orig_h + WATERMARK_FOOTER_H)

    # Repeated calls produce identical dimensions (zero double-stamping)
    stamped2 = retrofit_episode_watermark(legacy_dir, site_url="slopwow.github.io")
    with Image.open(stamped2) as s2:
        assert s2.size == (PAGE_W, orig_h + WATERMARK_FOOTER_H)


def test_dc_packager_promotes_slopwow_and_open_pack_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = EpisodeRecord(
        episode_id="ep001",
        episode_number=1,
        title="흑마법사가 물을 어케 줌?",
        subtitle="흑마를 법사로 착각한 힐러와 뉴비 흑마의 멜론 주스 상황극",
        source_post_no="92059",
        source_url="https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=92059",
        created_at="2026-11-21",
        cut_count=5,
        cast_used=["나이트엘프 사제", "인간 흑마법사"],
        full_image_rel="data/episodes/ep001/episode_full.jpg",
        thumb_image_rel="data/episodes/ep001/thumb.jpg",
        page_images_rel=[],
    )

    body = format_post_body(record)
    assert "전편 정주행 아카이브: https://slopwow.github.io/episodes/ep001.html" in body
    assert "전체 목록: https://slopwow.github.io" in body
    assert "https://slopwow.github.io/episode.html?id=ep001" in body

    pack_dir = tmp_path / "pack"
    pack_dir.mkdir()

    # In CI / headless mode, open_pack_folder must safely no-op without calling os.startfile
    monkeypatch.setenv("CI", "true")
    assert open_pack_folder(pack_dir) is False
    assert open_pack_folder(tmp_path / "does_not_exist") is False

    # On non-CI Windows, open_pack_folder delegates to os.startfile safely
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("SLOPTOON_HEADLESS", raising=False)
    if sys.platform == "win32":
        with patch("wow_sloptoon.dc_packager.os.startfile", create=True) as mock_start:
            assert open_pack_folder(pack_dir) is True
            mock_start.assert_called_once_with(str(pack_dir.resolve()))


def _write_sample_episodes_json(project_root: Path, count: int = 2) -> list[EpisodeRecord]:
    records: list[EpisodeRecord] = []
    for n in range(1, count + 1):
        ep_id = f"ep{n:03d}"
        ep_dir = project_root / "data" / "episodes" / ep_id
        ep_dir.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (PAGE_W, 800), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 100, 800, 700], fill=(140, 180, 230), outline=(20, 20, 20), width=4)
        img.save(ep_dir / "episode_full.jpg", format="JPEG", quality=92)
        img.resize((800, 600)).save(ep_dir / "thumb.jpg", format="JPEG", quality=90)
        records.append(
            EpisodeRecord(
                episode_id=ep_id,
                episode_number=n,
                title=f"테스트 에피소드 {n}",
                subtitle=f"서브타이틀 {n}",
                source_post_no=f"9200{n}",
                source_url=f"https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=9200{n}",
                created_at="2026-11-21T15:00:00+09:00",
                cut_count=5,
                cast_used=["오크 전사", "나이트엘프 사제"],
                full_image_rel=f"data/episodes/{ep_id}/episode_full.jpg",
                thumb_image_rel=f"data/episodes/{ep_id}/thumb.jpg",
                page_images_rel=[],
            )
        )
    ep_json = project_root / "data" / "episodes.json"
    ep_json.parent.mkdir(parents=True, exist_ok=True)
    ep_json.write_text(
        json.dumps([r.model_dump(mode="json") for r in records], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return records


def test_publish_queue_lifecycle_and_notifications(tmp_path: Path) -> None:
    _write_sample_episodes_json(tmp_path, count=2)
    ep_json = tmp_path / "data" / "episodes.json"
    queue_path = tmp_path / "data" / "publish_queue.json"

    items = sync_publish_queue(episodes_json=ep_json, queue_path=queue_path)
    assert [i.episode_id for i in items] == ["ep001", "ep002"]
    assert all(i.status == "pending" for i in items)

    nxt = get_next_unpublished(queue_path=queue_path)
    assert nxt is not None and nxt.episode_id == "ep001"

    packed = mark_episode_packed("ep001", pack_dir=tmp_path / "upload_pack" / "ep001", queue_path=queue_path)
    assert packed.status == "packed"
    assert packed.packed_at is not None

    # Still unpublished until explicitly marked published
    nxt2 = get_next_unpublished(queue_path=queue_path)
    assert nxt2 is not None and nxt2.episode_id == "ep001"

    dc_url = "https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=999999"
    pub1 = mark_episode_published("ep001", dc_post_url=dc_url, queue_path=queue_path)
    assert pub1.status == "published"
    assert pub1.published_at is not None
    assert pub1.dc_post_url == dc_url

    # Next unpublished advances to ep002
    nxt3 = get_next_unpublished(queue_path=queue_path)
    assert nxt3 is not None and nxt3.episode_id == "ep002"

    # Re-syncing after adding ep003 preserves ep001 published status
    _write_sample_episodes_json(tmp_path, count=3)
    resynced = sync_publish_queue(episodes_json=ep_json, queue_path=queue_path)
    by_id = {i.episode_id: i for i in resynced}
    assert by_id["ep001"].status == "published"
    assert by_id["ep001"].dc_post_url == dc_url
    assert by_id["ep002"].status == "pending"
    assert by_id["ep003"].status == "pending"

    mark_episode_published("ep002", queue_path=queue_path)
    mark_episode_published("ep003", queue_path=queue_path)
    assert get_next_unpublished(queue_path=queue_path) is None
    assert len(load_publish_queue(queue_path)) == 3

    # Notification helper must never block or raise in CI/pytest
    assert notify_new_episode_ready("ep003", "테스트 에피소드 3", use_toast=True) is False


def test_cli_watermark_queue_publish_next_and_autopilot_dry_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n', encoding="utf-8")
    _write_sample_episodes_json(tmp_path, count=2)

    # 1. watermark-all (twice -> idempotent!)
    rc = cli.main(["--project-root", str(tmp_path), "watermark-all", "--site-url", "slopwow.github.io"])
    assert rc == 0
    with Image.open(tmp_path / "data" / "episodes" / "ep001" / "episode_full.jpg") as im1:
        assert im1.size == (PAGE_W, 800 + WATERMARK_FOOTER_H)

    rc2 = cli.main(["--project-root", str(tmp_path), "watermark-all", "--site-url", "slopwow.github.io"])
    assert rc2 == 0
    with Image.open(tmp_path / "data" / "episodes" / "ep001" / "episode_full.jpg") as im2:
        assert im2.size == (PAGE_W, 800 + WATERMARK_FOOTER_H)

    # 2. queue --json
    capsys.readouterr()
    assert cli.main(["--project-root", str(tmp_path), "queue", "--json"]) == 0
    q_data = json.loads(capsys.readouterr().out)
    assert [row["episode_id"] for row in q_data] == ["ep001", "ep002"]
    assert all(row["status"] == "pending" for row in q_data)

    # 3. publish-next (mock clipboard/folder/browser so test stays headless & fast)
    with (
        patch("wow_sloptoon.dc_packager.copy_to_clipboard", return_value=True) as mock_clip,
        patch("wow_sloptoon.dc_packager.open_pack_folder", return_value=True) as mock_folder,
        patch(
            "wow_sloptoon.dc_packager.open_dc_write_page",
            return_value="https://gall.dcinside.com/mgallery/board/write/?id=wowforever",
        ) as mock_browser,
    ):
        rc_pub = cli.main(
            [
                "--project-root",
                str(tmp_path),
                "publish-next",
                "--open-folder",
                "--open-browser",
                "--copy-body",
            ]
        )
        assert rc_pub == 0
        mock_clip.assert_called_once()
        mock_folder.assert_called_once()
        mock_browser.assert_called_once_with("wowforever")

    pack_body = (tmp_path / "upload_pack" / "ep001" / "post_body.txt").read_text(encoding="utf-8")
    assert "https://slopwow.github.io/episodes/ep001.html" in pack_body
    assert "전체 목록: https://slopwow.github.io" in pack_body

    # 4. mark-published ep001
    dc_post = "https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=123456"
    assert (
        cli.main(["--project-root", str(tmp_path), "mark-published", "ep001", "--dc-url", dc_post])
        == 0
    )
    nxt = get_next_unpublished(queue_path=tmp_path / "data" / "publish_queue.json")
    assert nxt is not None and nxt.episode_id == "ep002"

    # 5. autopilot --dry-run (mocked scout, zero API calls or deploy)
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
    with patch("wow_sloptoon.cli.GalleryScout.scout_candidates", return_value=[(fake_post, 99.5)]):
        rc_auto = cli.main(["--project-root", str(tmp_path), "autopilot", "--dry-run"])
        assert rc_auto == 0


def test_policy_compliance_no_captcha_bypass_or_auto_post() -> None:
    """Verify automation modules strictly avoid CAPTCHA bypass, headless login, or DC auto-POST."""
    project_root = Path(__file__).resolve().parents[1]
    checked_files = [
        project_root / "src" / "wow_sloptoon" / "dc_packager.py",
        project_root / "src" / "wow_sloptoon" / "scheduler.py",
        project_root / "src" / "wow_sloptoon" / "cli.py",
        project_root / "setup-automation.ps1",
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
