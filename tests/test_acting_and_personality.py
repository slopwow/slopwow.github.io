"""Route A test suite for 2~2.5-head cute SD style master (`diorama_style_ref.jpg`),
9-cast + 2 fixed companion mascots (baby bear & Voidwalker), compact prompts,
contradiction-free prompt guards, and `audit_script_quality` real retry gate.
"""

from __future__ import annotations

import base64
import io
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from PIL import Image

from wow_sloptoon import artist, writer
from wow_sloptoon.cast import (
    CAST_BIBLE,
    CAST_BY_ID,
    CastMember,
    build_character_anchors_block,
    format_cast_bible_for_writer,
    resolve_cast_member,
)
from wow_sloptoon.config import load_settings
from wow_sloptoon.models import ComicCut, EpisodeScript, GalleryPost

PROJECT_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_CONTRADICTION_TOKENS: tuple[str, ...] = (
    "3-to-3.5",
    "3~3.5",
    "3.5-head",
    "4-head",
    "avoid 2-head",
    "avoid stubby 2-head",
    "sleek",
    "sloptoon_style_ref",
    "plush imp",
    "imp doll",
    "1-hand chibi scale",
)

FORBIDDEN_CATCHPHRASE_TEMPLATES: tuple[str, ...] = (
    "옴뇸뇸~",
    "으, 으엣?!",
    "후훗…",
    "우웅~",
    "~당~♪",
    "~♡",
)


def _sample_post(post_no: str = "107884") -> GalleryPost:
    return GalleryPost(
        post_no=post_no,
        title="개꿀팁) 하이잘 도착하면 사제들 꼭 해야할 일....TIP",
        url=f"https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no={post_no}",
        author="포에버갤러",
        date_str="2026-11-24 18:00:00",
        views=3200,
        recommends=142,
        comments_count=65,
        body=(
            "하이잘 좁은 절벽 길에서 그림자 숨기 쓰고 기다리다가 지나가는 호드 유저한테 "
            "정신 지배 걸고 /인사 시킨 다음 절벽 아래로 꺾어 보내면 개꿀잼임 ㅋㅋ"
        ),
        comments=[
            "와 진짜 맑눈광 악마다 ㅋㅋㅋ",
            "도적은 혼란 딸깍이면 끝인데 사제는 직접 핸들 꺾는 손맛이 있네",
        ],
    )


def _fake_png_base64(size: tuple[int, int] = (96, 72)) -> str:
    buf = io.BytesIO()
    Image.new("RGB", size, (255, 255, 255)).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _assert_zero_contradiction_tokens(text: str, label: str) -> None:
    lower = text.lower()
    for token in FORBIDDEN_CONTRADICTION_TOKENS:
        assert token not in lower, f"Contradictory token '{token}' leaked into {label}"


def test_settings_uses_route_a_diorama_style_ref_and_drops_dc_fields() -> None:
    settings = load_settings(PROJECT_ROOT)
    assert settings.style_ref_path.name == "diorama_style_ref.jpg"
    assert settings.style_ref_path.exists()
    assert settings.cast_sheet_path.name == "cast_sheet_c.jpg"
    assert settings.cast_sheet_path.exists()
    assert not hasattr(settings, "upload_pack_dir")
    assert not hasattr(settings, "cast_sheet_labeled_path")
    assert not hasattr(settings, "gallery_write_url")


def test_cast_bible_route_a_sd_invariants_and_single_warlock_voidwalker() -> None:
    assert len(CAST_BIBLE) == 9

    personalities: list[str] = []
    speech_styles: list[str] = []

    for member in CAST_BIBLE:
        assert member.personality.strip()
        assert member.speech_style.strip()
        assert not hasattr(member, "aegyo_signature")
        assert not hasattr(member, "acting_range")

        for cliche in FORBIDDEN_CATCHPHRASE_TEMPLATES:
            assert cliche not in member.speech_style
            assert cliche not in member.personality

        lower_anchor = member.appearance_anchor.lower()
        assert "2-to-2.5 head" in lower_anchor
        assert "sd chibi" in lower_anchor
        assert "fair skin" in lower_anchor
        _assert_zero_contradiction_tokens(member.appearance_anchor, f"{member.id}.appearance_anchor")
        _assert_zero_contradiction_tokens(member.default_prop, f"{member.id}.default_prop")

        personalities.append(member.personality.strip())
        speech_styles.append(member.speech_style.strip())

    assert len(set(personalities)) == 9
    assert len(set(speech_styles)) == 9

    # Costume & companion invariants
    rogue = CAST_BY_ID["gnome_rogue"]
    assert "bare unadorned blonde twin pigtails" in rogue.appearance_anchor.lower()

    priest = CAST_BY_ID["nightelf_priest"]
    assert "lavender-silver sd eyes" in priest.appearance_anchor.lower()
    assert "mini holy book" in priest.appearance_anchor.lower()
    assert "gold rosary" in priest.appearance_anchor.lower()
    assert "gold cross staff" in priest.default_prop.lower()

    mage = CAST_BY_ID["skyborne_mage"]
    assert "blue wizard hat" in mage.appearance_anchor.lower()
    assert "polymorph sheep" in mage.appearance_anchor.lower()
    assert "sailor" not in mage.appearance_anchor.lower()

    warlock = CAST_BY_ID["human_warlock"]
    assert warlock.companion_id == "warlock_voidwalker"
    assert warlock.companion_name == "공허방랑자"
    assert "imp" not in warlock.default_prop.lower()
    assert "imp" not in warlock.appearance_anchor.lower()
    assert "voidwalker" in warlock.companion_anchor.lower()

    hunter = CAST_BY_ID["dwarf_hunter"]
    assert hunter.companion_id == "hunter_bear"
    assert hunter.companion_name == "아기 곰"
    assert "baby bear" in hunter.companion_anchor.lower()

    # Optional fields default cleanly on CastMember
    minimal = CastMember(
        id="test_cast",
        name="테스트 캐스트",
        race="인간",
        wow_class="전사",
        faction="Alliance",
        role_tag="테스트",
        color_hex="#000000",
        accent_hex="#FFFFFF",
        personality="테스트 성격",
        appearance_anchor="Cute plump 2-to-2.5 head Korean anime SD chibi girl, fair skin; simple tunic.",
        default_prop="Back sword.",
        aliases=("테스트",),
        sheet_position="custom",
    )
    assert minimal.speech_style == ""
    assert minimal.companion_id == ""
    assert minimal.companion_turnaround_filename is None


def test_cast_formatters_stay_compact_and_route_a_consistent() -> None:
    writer_bible = format_cast_bible_for_writer()
    assert len(writer_bible) < 2500, f"Writer cast bible bloated: {len(writer_bible)} chars"
    assert "2~2.5등신" in writer_bible
    assert "Clean Hand Rule" in writer_bible
    assert "아기 곰" in writer_bible
    assert "공허방랑자" in writer_bible
    _assert_zero_contradiction_tokens(writer_bible, "format_cast_bible_for_writer")
    for member in CAST_BIBLE:
        assert member.name in writer_bible
        assert member.personality in writer_bible
        assert member.appearance_anchor not in writer_bible

    anchors = build_character_anchors_block(["인간 흑마법사", "드워프 사냥꾼"])
    assert "2-to-2.5 head SD" in anchors
    assert "warlock_voidwalker" in anchors
    assert "hunter_bear" in anchors
    assert "imp" not in anchors.lower()
    _assert_zero_contradiction_tokens(anchors, "build_character_anchors_block")

    fallback = build_character_anchors_block([])
    assert "2-to-2.5 head SD" in fallback
    _assert_zero_contradiction_tokens(fallback, "build_character_anchors_block(empty)")


def test_artist_single_cut_prompts_are_compact_and_zero_contradiction() -> None:
    cut_dialogue = ComicCut(
        cut_index=1,
        aspect_ratio="4:3",
        layout_slot="top",
        characters=["나이트엘프 사제", "인간 흑마법사"],
        speaker="나이트엘프 사제",
        dialogue="법사님, 마나 없는데\n물 20개만 주세요!",
        wordless=False,
        visual_prompt=(
            "Over-the-shoulder shot of exhausted Night Elf Priest asking Human Warlock "
            "and her floating purple Voidwalker for water."
        ),
        tail_target="left",
    )
    prompt = artist.build_cut_image_prompt(
        cut_dialogue,
        attached_turnarounds=["나이트엘프 사제 (nightelf_priest)", "인간 흑마법사 (human_warlock)"],
        attached_companions=["공허방랑자 (warlock_voidwalker, companion of 인간 흑마법사)"],
    )
    assert len(prompt) < 2500, f"Single-cut prompt bloated: {len(prompt)} chars"
    assert "diorama_style_ref.jpg" in prompt
    assert "DO NOT copy Ref 1's characters" in prompt
    assert "2-to-2.5 head" in prompt
    assert "All extras, mobs, bosses, NPCs" in prompt
    assert "#FFFFFF" in prompt
    assert "Zero text" in prompt
    _assert_zero_contradiction_tokens(prompt, "build_cut_image_prompt(dialogue)")

    cut_wordless = ComicCut(
        cut_index=4,
        aspect_ratio="16:9",
        layout_slot="bottom",
        characters=["나이트엘프 사제"],
        wordless=True,
        visual_prompt="Centered extreme close-up shock reaction of Night Elf Priest.",
        tail_target="center",
    )
    wordless_prompt = artist.build_cut_image_prompt(
        cut_wordless,
        attached_turnarounds=["나이트엘프 사제 (nightelf_priest)"],
    )
    assert len(wordless_prompt) < 2000
    assert "75-85%" in wordless_prompt
    assert "diorama_style_ref.jpg" in wordless_prompt
    _assert_zero_contradiction_tokens(wordless_prompt, "build_cut_image_prompt(wordless)")


def test_artist_attaches_diorama_style_ref_first_and_handles_companions_and_fallback(
    tmp_path: Path,
) -> None:
    settings = load_settings(PROJECT_ROOT)
    style_ref_bytes = settings.style_ref_path.read_bytes()
    cast_sheet_bytes = settings.cast_sheet_path.read_bytes()
    bear_bytes = (settings.turnarounds_dir / "hunter_bear.jpg").read_bytes()
    vw_bytes = (settings.turnarounds_dir / "warlock_voidwalker.jpg").read_bytes()

    fake_png_b64 = _fake_png_base64()
    lock = threading.Lock()
    captured: list[dict[str, Any]] = []

    class FakeInteractions:
        def create(self, **kwargs: Any) -> Any:
            with lock:
                captured.append(kwargs)
            return SimpleNamespace(output_image=SimpleNamespace(data=fake_png_b64))

    fake_client = SimpleNamespace(interactions=FakeInteractions())

    for idx, (char_name, expected_companion) in enumerate(
        (
            ("드워프 사냥꾼", bear_bytes),
            ("인간 흑마법사", vw_bytes),
            ("오크 전사", None),
        ),
        start=1,
    ):
        cut = ComicCut(
            cut_index=idx,
            layout_slot="bottom",
            aspect_ratio="16:9",
            characters=[char_name],
            speaker=char_name,
            dialogue="테스트 대사",
            tail_target="center",
            wordless=False,
            visual_prompt=f"Low-angle cute 2.5-head chibi SD shot of {char_name} on pure #FFFFFF.",
        )
        artist.generate_cut_image(
            cut,
            tmp_path / f"cut_{idx}.png",
            client=fake_client,
            settings=settings,
        )
        call = captured[-1]
        assert call["response_format"]["aspect_ratio"] == "16:9"
        items = call["input"]
        _assert_zero_contradiction_tokens(items[0]["text"], f"cut_{idx} prompt")
        assert base64.b64decode(items[1]["data"]) == style_ref_bytes
        blobs = [base64.b64decode(it["data"]) for it in items[1:]]
        assert cast_sheet_bytes not in blobs
        if expected_companion is not None:
            assert len(items) == 4  # text + diorama_style_ref + owner + companion
            assert expected_companion in blobs
            assert "cute round SD mascot" in items[0]["text"]
        else:
            assert len(items) == 3  # text + diorama_style_ref + owner
            assert bear_bytes not in blobs
            assert vw_bytes not in blobs

    # Fallback: when turnarounds_dir is empty, cast_sheet_c.jpg attaches as Ref 2
    empty_turnarounds = tmp_path / "empty_turnarounds"
    empty_turnarounds.mkdir()
    fallback_settings = settings.__class__(
        **{**settings.__dict__, "turnarounds_dir": empty_turnarounds}
    )
    fallback_cut = ComicCut(
        cut_index=9,
        layout_slot="top",
        aspect_ratio="4:3",
        characters=["오크 전사"],
        speaker="오크 전사",
        dialogue="폴백 테스트",
        tail_target="left",
        wordless=False,
        visual_prompt="Side-profile cute 2.5-head chibi SD shot of Orc Warrior.",
    )
    artist.generate_cut_image(
        fallback_cut,
        tmp_path / "cut_fallback.png",
        client=fake_client,
        settings=fallback_settings,
    )
    fb_items = captured[-1]["input"]
    assert len(fb_items) == 3
    assert base64.b64decode(fb_items[1]["data"]) == style_ref_bytes
    assert base64.b64decode(fb_items[2]["data"]) == cast_sheet_bytes
    assert "cast sheet" in fb_items[0]["text"]


def test_writer_prompt_and_audit_script_quality_route_a_gates() -> None:
    post = _sample_post()
    prompt = writer.build_writer_prompt(post, episode_number=20)
    assert len(prompt) < 9000, f"Writer prompt bloated: {len(prompt)} chars"
    assert "념글을 안 읽고도 100% 이해" in prompt
    assert "2~2.5등신" in prompt
    assert "4~7컷" in prompt
    assert "1~2줄" in prompt
    assert "아기 곰" in prompt and "공허방랑자" in prompt
    assert "빨간 임프 인형은 절대 언급 금지" in prompt
    _assert_zero_contradiction_tokens(prompt, "build_writer_prompt")

    # Dry-run script passes strict_cinematic=True with 0 errors and 0 warnings
    dry = writer.build_dry_run_script(post, episode_number=20)
    audit = writer.audit_script_quality(dry, strict_cinematic=True)
    assert audit["passed"] is True, f"Dry-run script failed strict audit: {audit['errors']}"
    assert audit["errors"] == []
    assert audit["warnings"] == []

    # 1) 3-line brick wall (> 38 chars) triggers hard error
    brick_cuts = list(dry.cuts)
    brick_cuts[0] = brick_cuts[0].model_copy(
        update={
            "dialogue": (
                "내가 지금 하이잘 절벽 길에서\n"
                "그림자 숨기를 쓰고 기다리다가\n"
                "지나가는 상대한테 정배를 거는 중이야!"
            )
        }
    )
    brick_audit = writer.audit_script_quality(dry.model_copy(update={"cuts": brick_cuts}))
    assert brick_audit["passed"] is False
    assert brick_audit["checks"]["dialogue_concise_ok"] is False
    assert 1 in brick_audit["dialogue_pacing"]["bloated_3line_cuts"]

    # 2) > 35% 3-line bubbles (2 of 3 dialogue cuts = 66.7%) triggers hard error even when <= 36 chars
    three_line_cuts = list(dry.cuts)
    three_line_cuts[0] = three_line_cuts[0].model_copy(update={"dialogue": "첫째 줄 짧게\n둘째 줄 짧게\n셋째 줄 끝!"})
    three_line_cuts[1] = three_line_cuts[1].model_copy(update={"dialogue": "여기도 한 줄\n두 번째 줄에\n세 번째 줄!"})
    ratio_audit = writer.audit_script_quality(dry.model_copy(update={"cuts": three_line_cuts}))
    assert ratio_audit["passed"] is False
    assert ratio_audit["checks"]["dialogue_concise_ok"] is False
    assert ratio_audit["dialogue_pacing"]["three_line_ratio"] > 0.35

    # 3) Excessive honorifics (> 60% polite dialogue) triggers warning
    polite_cuts = list(dry.cuts)
    polite_cuts[0] = polite_cuts[0].model_copy(update={"dialogue": "저기요 파티 규칙\n확인 부탁드려요."})
    polite_cuts[1] = polite_cuts[1].model_copy(update={"dialogue": "네 알겠습니다\n제가 진행할게요."})
    polite_cuts[2] = polite_cuts[2].model_copy(update={"dialogue": "로그에도 정확히\n기록되어 있어요."})
    polite_audit = writer.audit_script_quality(dry.model_copy(update={"cuts": polite_cuts}))
    assert polite_audit["passed"] is True
    assert polite_audit["dialogue_pacing"]["polite_ratio"] > 0.60
    assert any("polite/honorific" in w for w in polite_audit["warnings"])

    # 4) Warlock Imp + Voidwalker dual-pet conflict triggers hard error
    imp_cuts = list(dry.cuts)
    imp_cuts[0] = imp_cuts[0].model_copy(
        update={
            "characters": ["인간 흑마법사", "나이트엘프 사제"],
            "speaker": "인간 흑마법사",
            "dialogue": "내 임프보다 더한 악마네!",
            "visual_prompt": (
                "Over-the-shoulder cute 2.5-head chibi SD shot of Human Warlock holding a red imp "
                "beside her purple Voidwalker."
            ),
        }
    )
    imp_audit = writer.audit_script_quality(dry.model_copy(update={"cuts": imp_cuts}))
    assert imp_audit["passed"] is False
    assert imp_audit["checks"]["no_imp_voidwalker_conflict"] is False


def test_generate_episode_script_auto_retries_when_audit_fails() -> None:
    post = _sample_post()
    good_script = writer.build_dry_run_script(post, episode_number=21)

    bad_cuts = list(good_script.cuts)
    bad_cuts[0] = bad_cuts[0].model_copy(
        update={
            "characters": ["인간 흑마법사", "나이트엘프 사제"],
            "speaker": "인간 흑마법사",
            "dialogue": "임프 소환해서 119 부를게!\n지금 너무 길게 설명하는 벽돌 대사를 세 줄로 가득 채워버릴 거야!",
        }
    )
    bad_script = good_script.model_copy(update={"cuts": bad_cuts})

    calls: list[dict[str, Any]] = []
    responses = [bad_script.model_dump_json(), good_script.model_dump_json()]

    class RetryFakeInteractions:
        def create(self, **kwargs: Any) -> Any:
            calls.append(kwargs)
            return SimpleNamespace(output_text=responses[len(calls) - 1])

    result = writer.generate_episode_script(
        post,
        episode_number=21,
        client=SimpleNamespace(interactions=RetryFakeInteractions()),
        max_retries=2,
    )
    assert len(calls) == 2
    assert "자동 품질 검수 실패" in calls[1]["input"]
    assert result.source_title == post.title.strip()
    assert writer.audit_script_quality(result)["passed"] is True

    # Exhausting all retries raises ValueError
    class AlwaysBadInteractions:
        def create(self, **kwargs: Any) -> Any:
            return SimpleNamespace(output_text=bad_script.model_dump_json())

    with pytest.raises(ValueError, match="failed audit_script_quality"):
        writer.generate_episode_script(
            post,
            episode_number=21,
            client=SimpleNamespace(interactions=AlwaysBadInteractions()),
            max_retries=1,
        )
