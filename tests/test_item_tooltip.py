"""Tests for authentic Korean WoW item tooltips (`item_tooltip.py`), composer placement, and verbatim titles."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest
from PIL import Image, ImageDraw

from wow_sloptoon import writer
from wow_sloptoon.composer import compose_episode
from wow_sloptoon.item_tooltip import (
    EQUIP_GREEN,
    QUALITY_COLORS,
    TOOLTIP_BG_DARK,
    ItemTooltipSpec,
    parse_wowhead_tooltip_html,
    render_item_tooltip,
    resolve_tooltip_spec,
)
from wow_sloptoon.models import ComicCut, EpisodeScript, GalleryPost

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _make_raw_cut(path: Path, size: tuple[int, int], *, full_bleed: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    w, h = size
    im = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(im)
    if full_bleed:
        d.rectangle([0, 0, w - 1, h - 1], fill=(96, 138, 212))
        d.ellipse([w // 4, h // 4, 3 * w // 4, 3 * h // 4], fill=(242, 198, 122), outline=(24, 24, 24), width=5)
    else:
        d.ellipse([int(w * 0.16), int(h * 0.24), int(w * 0.44), int(h * 0.62)], fill=(150, 212, 155), outline=(24, 24, 24), width=5)
        d.rectangle([int(w * 0.20), int(h * 0.56), int(w * 0.40), h - 1], fill=(214, 132, 180), outline=(24, 24, 24), width=5)
        d.ellipse([int(w * 0.56), int(h * 0.22), int(w * 0.84), int(h * 0.60)], fill=(162, 138, 226), outline=(24, 24, 24), width=5)
        d.rectangle([int(w * 0.60), int(h * 0.54), int(w * 0.80), h - 1], fill=(82, 96, 156), outline=(24, 24, 24), width=5)
    im.save(path, format="PNG")
    return path


def test_backwards_compatibility_existing_script_json_without_item_tooltip() -> None:
    """All checked-in episode script.json files must validate cleanly under Route A (4~7 cuts)."""
    ep_dirs = sorted((PROJECT_ROOT / "data" / "episodes").glob("ep*"))
    validated = 0
    for ep_dir in ep_dirs:
        script_file = ep_dir / "script.json"
        if script_file.exists():
            script = EpisodeScript.model_validate_json(script_file.read_text(encoding="utf-8"))
            assert 4 <= len(script.cuts) <= 7
            validated += 1
    assert validated >= 1

    legacy_cut = ComicCut.model_validate(
        {
            "cut_index": 1,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["오크 전사"],
            "speaker": "오크 전사",
            "dialogue": "기존 스크립트 호환 테스트",
            "wordless": False,
            "visual_prompt": "Orc Warrior cute 2.5-head SD on pure #FFFFFF white background.",
            "tail_target": "left",
        }
    )
    assert legacy_cut.item_tooltip is None


def test_verbatim_concept_post_title_preserved_by_writer() -> None:
    verbatim = "  방금만난 기사님의 명-언.jpg  "
    post = GalleryPost(
        post_no="96849",
        title=verbatim,
        url="https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=96849",
        author="포에버갤러",
        date_str="2026-11-21",
        body="던전에서 기사님이 무적 귀환 명언을 남겼다.",
    )

    # 1. Dry-run script preserves exact trimmed original title
    dry = writer.build_dry_run_script(post, episode_number=2)
    assert dry.source_title == "방금만난 기사님의 명-언.jpg"

    # 2. Writer prompt explicitly embeds exact original title
    prompt = writer.build_writer_prompt(post, episode_number=2)
    assert '"방금만난 기사님의 명-언.jpg"' in prompt

    # 3. generate_episode_script overwrites any LLM-rewritten title back to verbatim post.title
    rewritten_llm_json = dry.model_copy(
        update={"source_title": "방금 만난 기사님의 명언 요약본"}
    ).model_dump_json()
    fake_client = SimpleNamespace(
        interactions=SimpleNamespace(
            create=lambda **kwargs: SimpleNamespace(output_text=rewritten_llm_json)
        )
    )
    normalized = writer.generate_episode_script(post, episode_number=2, client=fake_client)
    assert normalized.source_title == "방금만난 기사님의 명-언.jpg"


def test_user_librarian_scepter_asset_and_screenshot_rendering() -> None:
    asset_path = PROJECT_ROOT / "assets" / "items" / "scepter_of_the_librarian.png"
    assert asset_path.exists(), "Missing assets/items/scepter_of_the_librarian.png"

    card = render_item_tooltip(
        ItemTooltipSpec(
            image_path="assets/items/scepter_of_the_librarian.png",
            item_name="사서의 홀",
            quality="uncommon",
        ),
        project_root=PROJECT_ROOT,
        fetch_network=False,
    )
    assert card is not None
    assert card.mode == "RGBA"
    assert 260 <= card.width <= 315
    assert 130 <= card.height <= 200

    arr = np.asarray(card)
    green_px = np.sum((arr[:, :, 1] > 210) & (arr[:, :, 0] < 70) & (arr[:, :, 2] < 70))
    assert green_px > 200


def test_parse_wowhead_classic_html_and_programmatic_card_colors(monkeypatch: pytest.MonkeyPatch) -> None:
    sample_payload: dict[str, Any] = {
        "name": "정의의 망치",
        "quality": 3,
        "icon": "inv_hammer_02",
        "tooltip": (
            '<table><tr><td><table style="display:inline-table"><tr><td><!--nstart-->'
            '<b class="q3">정의의 망치</b><!--nend--></td><th><b class="q0 whtt-extra">디스커버리 2단계</b></th>'
            '</tr></table><span class="q"><br>아이템 레벨 <!--ilvl-->44</span><!--bo--><br>획득 시 귀속'
            '<table width="100%"><tr><td>주장비</td><th><span class="q1">둔기</span></th></tr></table>'
            '<table width="100%"><tr><td><span>공격력 56 - 105</span></td><th>속도 2.70</th></tr></table>'
            '(초당 공격력 29.81)<br><span>정신력 +8</span><br>내구도 90 / 90</td></tr></table>'
            '<table><tr><td>요구 레벨 39<br><span id="useText1" class="q2">착용 효과: '
            '<a href="/classic/ko/spell=7681" class="q2">모든 주문 및 효과에 의한 치유량이 최대 15만큼 증가합니다.</a>'
            '</span><div class="whtt-sellprice">판매 가격: 1 79 22</div></td></tr></table>'
        ),
    }
    parsed = parse_wowhead_tooltip_html(sample_payload)
    assert parsed.item_name == "정의의 망치"
    assert parsed.quality == "rare"
    assert parsed.slot_left == "주장비"
    assert parsed.slot_right == "둔기"
    assert "획득 시 귀속" in parsed.lines
    assert "공격력 56 - 105\t속도 2.70" in parsed.lines
    assert "(초당 공격력 29.81)" in parsed.lines
    assert "정신력 +8" in parsed.lines
    assert "요구 레벨 39" in parsed.lines
    assert all("디스커버리" not in ln and "판매 가격" not in ln for ln in parsed.lines)
    assert parsed.equip_effects == ("착용 효과: 모든 주문 및 효과에 의한 치유량이 최대 15만큼 증가합니다.",)

    monkeypatch.setenv("SLOPTOON_OFFLINE_TOOLTIPS", "1")
    triune_spec = resolve_tooltip_spec(ItemTooltipSpec(wowhead_item_id=7722), fetch_network=False)
    assert triune_spec.item_name == "삼위일체의 아뮬렛"
    assert triune_spec.slot_left == "목"
    assert "체력 +7" in triune_spec.lines
    assert "지능 +7" in triune_spec.lines
    assert "정신력 +7" in triune_spec.lines

    epic_card = render_item_tooltip(
        ItemTooltipSpec(
            item_name="교장의 해골지팡이",
            quality="epic",
            slot_left="양손 장비",
            slot_right="지팡이",
            lines=["획득 시 귀속", "공격력 135 - 204\t속도 2.90", "체력 +30", "정신력 +20"],
            equip_effects=["착용 효과: 파티원의 지능을 20만큼 증가시킵니다."],
        ),
        fetch_network=False,
    )
    assert epic_card is not None
    assert 256 <= epic_card.width <= 320
    arr = np.asarray(epic_card)
    dark_px = np.sum((arr[:, :, 0] < 28) & (arr[:, :, 1] < 30) & (arr[:, :, 2] < 45) & (arr[:, :, 3] > 220))
    assert dark_px > 10000
    epic_px = np.sum((arr[:, :, 0] > 120) & (arr[:, :, 1] < 90) & (arr[:, :, 2] > 180))
    assert epic_px > 40
    eq_px = np.sum((arr[:, :, 1] > 200) & (arr[:, :, 0] < 70) & (arr[:, :, 2] < 70))
    assert eq_px > 60
    assert QUALITY_COLORS["epic"] == (163, 53, 238)
    assert QUALITY_COLORS["rare"] == (0, 112, 221)
    assert EQUIP_GREEN == (30, 255, 0)
    assert TOOLTIP_BG_DARK == (11, 13, 22)


@pytest.mark.parametrize("full_bleed", [False, True])
def test_composer_places_item_tooltips_with_zero_overlap_across_all_cut_types(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    full_bleed: bool,
) -> None:
    monkeypatch.setenv("SLOPTOON_OFFLINE_TOOLTIPS", "1")
    cuts = [
        ComicCut(
            cut_index=1,
            aspect_ratio="4:3",
            layout_slot="top",
            characters=["오크 전사", "언데드 성기사"],
            speaker="오크 전사",
            dialogue="어어 저 목걸이\n삼위일체의 아뮬렛이네?!",
            wordless=False,
            visual_prompt="Orc Warrior and Undead Paladin looking at Rare amulet.",
            tail_target="left",
            item_tooltip=ItemTooltipSpec(wowhead_item_id=7722),
        ),
        ComicCut(
            cut_index=2,
            aspect_ratio="16:9",
            layout_slot="bottom",
            characters=["나이트엘프 사제", "인간 흑마법사"],
            speaker="나이트엘프 사제",
            dialogue="사서의 홀 내 건데\n왜 주사위를 굴려요?!",
            wordless=False,
            visual_prompt="Shocked Night Elf Priest protesting next to Human Warlock.",
            tail_target="left",
            item_tooltip=ItemTooltipSpec(
                image_path="assets/items/scepter_of_the_librarian.png",
                item_name="사서의 홀",
                quality="uncommon",
            ),
        ),
        ComicCut(
            cut_index=3,
            aspect_ratio="4:3",
            layout_slot="top",
            characters=["인간 흑마법사", "나이트엘프 사제"],
            speaker="인간 흑마법사",
            dialogue="모자 룩이 예뻐서\n입찰 눌렀어!",
            wordless=False,
            visual_prompt="Human Warlock smiling innocently next to Priest.",
            tail_target="left",
            item_tooltip=ItemTooltipSpec(wowhead_item_id=7720),
        ),
        ComicCut(
            cut_index=4,
            aspect_ratio="16:9",
            layout_slot="bottom",
            characters=["나이트엘프 사제"],
            wordless=True,
            visual_prompt="Deadpan silent freeze-frame of Night Elf Priest.",
            tail_target="center",
            item_tooltip=ItemTooltipSpec(item_name="사서의 홀", quality="uncommon"),
        ),
        ComicCut(
            cut_index=5,
            aspect_ratio="16:9",
            layout_slot="bottom",
            characters=["드워프 사냥꾼"],
            speaker="드워프 사냥꾼",
            dialogue="지능 붙으면 다\n냥꾼 무기거든!!",
            wordless=False,
            visual_prompt="Dwarf Hunter raising blunderbuss.",
            tail_target="left",
            item_tooltip=ItemTooltipSpec(wowhead_item_id=7721),
        ),
    ]

    script = EpisodeScript(
        episode_number=55,
        source_post_no="107380",
        source_title="와뉴비 다들 왜 사제 안키우는 지 알거같다",
        source_url="https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=107380",
        subtitle="붉은십자군 수도원 아이템 툴팁 무겹침 테스트",
        cuts=cuts,
    )

    raw_paths = {
        idx: _make_raw_cut(
            tmp_path / f"raw_{full_bleed}" / f"cut_{idx:02d}.png",
            (1200, 896) if idx in (1, 3) else (1376, 768),
            full_bleed=full_bleed,
        )
        for idx in range(1, 6)
    }

    res = compose_episode(script, raw_paths, tmp_path / f"out_{full_bleed}")
    assert res.audit_report["passed"] is True
    assert res.audit_report["total_overlap_px"] == 0
    assert res.audit_report["total_tooltip_overlap_px"] == 0
    assert res.audit_report["border_pure_white"] is True

    for cut_audit in res.audit_report["cuts"]:
        assert cut_audit["overlap_px"] == 0
        assert cut_audit["has_item_tooltip"] is True
        assert cut_audit["tooltip_overlap_px"] == 0
        assert cut_audit["art_height_ratio"] > 0.35
        bbox = cut_audit["tooltip_bbox"]
        assert len(bbox) == 4 and bbox[2] > bbox[0] and bbox[3] > bbox[1]

    dumped = json.loads(script.model_dump_json())
    reloaded = EpisodeScript.model_validate(dumped)
    assert reloaded.cuts[0].item_tooltip is not None
    assert reloaded.cuts[0].item_tooltip.wowhead_item_id == 7722
    assert reloaded.cuts[1].item_tooltip is not None
    assert reloaded.cuts[1].item_tooltip.image_path == "assets/items/scepter_of_the_librarian.png"
