"""Test suite for sleek 3–3.5 head webtoon Style-First prompts, copy-paste-free 9-cast
personalities, compact prompt budget, and self-contained storytelling rules.
"""

from __future__ import annotations

import base64
import io
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any

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
from wow_sloptoon.models import ComicCut, GalleryPost

PROJECT_ROOT = Path(__file__).resolve().parents[1]

HARDCODED_STATIC_EXPRESSIONS: tuple[str, ...] = (
    "playful fang grin",
    "cheeky fang grin",
    "grumpy-cute healer glare",
    "sly fang smirk",
    "lively wink/smile",
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


def _fake_png_base64(size: tuple[int, int] = (90, 135)) -> str:
    buf = io.BytesIO()
    Image.new("RGB", size, (255, 255, 255)).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def test_cast_bible_all_nine_members_have_unique_traits_and_zero_catchphrase_templates() -> None:
    assert len(CAST_BIBLE) == 9

    personalities: list[str] = []
    speech_styles: list[str] = []
    aegyo_signatures: list[str] = []
    acting_ranges: list[str] = []

    for member in CAST_BIBLE:
        assert member.personality.strip()
        assert member.speech_style.strip()
        assert member.aegyo_signature.strip()
        assert member.acting_range.strip()

        for cliché in FORBIDDEN_CATCHPHRASE_TEMPLATES:
            assert cliché not in member.aegyo_signature, (
                f"{member.id}.aegyo_signature must not hardcode copy-paste template '{cliché}'"
            )
            assert cliché not in member.speech_style

        personalities.append(member.personality.strip())
        speech_styles.append(member.speech_style.strip())
        aegyo_signatures.append(member.aegyo_signature.strip())
        acting_ranges.append(member.acting_range.strip())

    assert len(set(personalities)) == 9
    assert len(set(speech_styles)) == 9
    assert len(set(aegyo_signatures)) == 9
    assert len(set(acting_ranges)) == 9

    # Backward compatibility: optional fields default cleanly to ""
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
        appearance_anchor="Fair-skinned sleek 3-to-3.5 head identity only.",
        default_prop="Stowed sword.",
        aliases=("테스트",),
        sheet_position="custom",
    )
    assert minimal.speech_style == ""
    assert minimal.aegyo_signature == ""
    assert minimal.acting_range == ""


def test_cast_appearance_anchors_target_sleek_3_to_3_5_head_and_keep_costume_invariants() -> None:
    for member in CAST_BIBLE:
        lower_anchor = member.appearance_anchor.lower()
        for forbidden_expr in HARDCODED_STATIC_EXPRESSIONS:
            assert forbidden_expr not in lower_anchor
        assert "fair-skinned" in lower_anchor
        assert "3-to-3.5 head" in lower_anchor
        assert "2.5-to-2.8" not in lower_anchor
        assert "identity & costume only" in lower_anchor
        assert "facial expression and pose free" in lower_anchor

    rogue_anchor = CAST_BY_ID["gnome_rogue"].appearance_anchor.lower()
    assert "zero hairpins" in rogue_anchor
    assert "no x-pin" in rogue_anchor
    assert "no star hairpins" in rogue_anchor

    priest_anchor = CAST_BY_ID["nightelf_priest"].appearance_anchor.lower()
    assert "silver-white" in priest_anchor
    assert "zero angel halo" in priest_anchor
    assert "zero wings" in priest_anchor

    mage_anchor = CAST_BY_ID["skyborne_mage"].appearance_anchor.lower()
    assert "zero sailor uniform" in mage_anchor
    assert "polymorph sheep" in mage_anchor


def test_cast_formatters_stay_compact_and_style_first() -> None:
    writer_bible = format_cast_bible_for_writer()
    assert len(writer_bible) < 2500, f"Writer cast bible bloated again: {len(writer_bible)} chars"
    assert "Clean Hand Rule" in writer_bible
    assert "appearance_anchor" not in writer_bible
    for member in CAST_BIBLE:
        assert member.name in writer_bible
        assert member.personality in writer_bible
        assert member.appearance_anchor not in writer_bible  # English costume specs belong to artist.py only

    anchors = build_character_anchors_block(["나이트엘프 사제", "노움 도적"])
    assert "PROPORTIONS & STYLE FIRST" in anchors
    assert "3-to-3.5 head" in anchors
    assert "COSTUME, HAIR, HEADGEAR & COLOR IDENTITY ONLY" in anchors
    assert "CLEAN HAND RULE" in anchors
    for member_id in ("nightelf_priest", "gnome_rogue"):
        assert CAST_BY_ID[member_id].appearance_anchor in anchors

    fallback = build_character_anchors_block([])
    assert "PROPORTIONS & STYLE FIRST" in fallback
    assert "3-to-3.5 head" in fallback


def test_artist_prompts_stay_compact_and_enforce_sleek_3_to_3_5_head_style_first() -> None:
    post = _sample_post()
    script = writer.build_dry_run_v4_script(post, episode_number=20, background_style="clean_white")
    assert script.acts is not None

    for act in (script.acts[0], script.acts[2], script.acts[3]):
        prompt = artist.build_page_batch_prompt(
            act,
            attached_turnarounds=["나이트엘프 사제 (nightelf_priest)", "노움 도적 (gnome_rogue)"],
            background_style="clean_white",
        )
        assert len(prompt) < 9500, f"Act {act.act_number} image prompt bloated again: {len(prompt)} chars"
        assert "3-to-3.5 head" in prompt
        assert "2.5-to-2.8" not in prompt
        assert "Reference Image 1 (`assets/sloptoon_style_ref.jpg`)" in prompt
        assert "Costume & Color Sheet" in prompt
        assert "diorama_style_ref.jpg" not in prompt
        assert "Zero text" in prompt

    cut = ComicCut(
        cut_index=1,
        aspect_ratio="4:3",
        layout_slot="top",
        characters=["나이트엘프 사제", "인간 흑마법사"],
        speaker="나이트엘프 사제",
        dialogue="저기 법사님, 마나 없는데\n물 20개만 뽑아주세요...",
        wordless=False,
        visual_prompt="Over-the-shoulder shot of exhausted Night Elf Priest asking Human Warlock for water.",
        tail_target="left",
    )
    single_prompt = artist.build_cut_image_prompt(
        cut,
        attached_turnarounds=["나이트엘프 사제 (nightelf_priest)", "인간 흑마법사 (human_warlock)"],
    )
    assert len(single_prompt) < 5000, f"Single-cut prompt bloated: {len(single_prompt)} chars"
    assert "3-to-3.5 head" in single_prompt
    assert "Reference Image 1 (`assets/sloptoon_style_ref.jpg`)" in single_prompt
    assert "Costume & Color Sheet" in single_prompt
    assert "#FFFFFF" in single_prompt


def test_artist_attaches_style_ref_first_and_only_active_turnarounds(tmp_path: Path) -> None:
    settings = load_settings(PROJECT_ROOT)
    post = _sample_post()
    script = writer.build_dry_run_v4_script(post, episode_number=20, background_style="clean_white")

    fake_png_b64 = _fake_png_base64()
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
        tmp_path / "v4_pages",
        client=fake_client,
        settings=settings,
    )
    assert len(captured_calls) == 5

    cast_sheet_bytes = settings.cast_sheet_path.read_bytes()
    style_ref_bytes = settings.style_ref_path.read_bytes()

    matched_acts: set[int] = set()
    for call in captured_calls:
        items = call["input"]
        assert items[0]["type"] == "text"
        prompt_text = items[0]["text"]
        assert "3-to-3.5 head" in prompt_text

        act = next(
            (a for a in (script.acts or []) if f"(Act {a.act_number}:" in prompt_text),
            None,
        )
        assert act is not None
        matched_acts.add(act.act_number)

        unique_members = []
        seen_ids: set[str] = set()
        for cut in act.cuts:
            for c_name in cut.characters:
                member = resolve_cast_member(c_name)
                if member and member.id not in seen_ids:
                    seen_ids.add(member.id)
                    unique_members.append(member)

        # Style-First exact attachments: [text, style_ref, layout_blueprint, *turnarounds, *companions]
        # Zero redundant 9-cast 2-head SD sheet when turnarounds exist, zero expression sheets!
        companion_files = [
            m.companion_turnaround_filename
            for m in unique_members
            if m.companion_turnaround_filename
            and (settings.turnarounds_dir / m.companion_turnaround_filename).exists()
        ]
        assert len(items) == 3 + len(unique_members) + len(companion_files)
        assert base64.b64decode(items[1]["data"]) == style_ref_bytes
        assert all(base64.b64decode(it["data"]) != cast_sheet_bytes for it in items[1:])

        attached_turnarounds = {base64.b64decode(item["data"]) for item in items[3:]}
        expected_turnarounds = {
            (settings.turnarounds_dir / m.turnaround_filename).read_bytes()
            for m in unique_members
        } | {
            (settings.turnarounds_dir / fname).read_bytes()
            for fname in companion_files
        }
        assert attached_turnarounds == expected_turnarounds

    assert matched_acts == {1, 2, 3, 4, 5}

    # Single-cut generation: [text, style_ref, *turnarounds] (parallel max_workers=2 supported)
    single_calls: list[dict[str, Any]] = []

    class FakeSingleInteractions:
        def create(self, **kwargs: Any) -> Any:
            with lock:
                single_calls.append(kwargs)
            return SimpleNamespace(output_image=SimpleNamespace(data=fake_png_b64))

    dry_classic = writer.build_dry_run_script(post, episode_number=21)
    out = artist.generate_episode_cuts(
        dry_classic,
        tmp_path / "classic_cuts",
        client=SimpleNamespace(interactions=FakeSingleInteractions()),
        settings=settings,
        max_workers=2,
    )
    assert sorted(out.keys()) == [1, 2, 3, 4]
    assert len(single_calls) == 4
    for call in single_calls:
        assert base64.b64decode(call["input"][1]["data"]) == style_ref_bytes
        assert all(base64.b64decode(it["data"]) != cast_sheet_bytes for it in call["input"][1:])


def test_writer_prompts_stay_compact_and_prioritize_self_contained_storytelling() -> None:
    post = _sample_post()
    classic_prompt = writer.build_writer_prompt(post, episode_number=20)
    v4_prompt = writer.build_v4_writer_prompt(post, episode_number=20, background_style="clean_white")

    assert len(classic_prompt) < 10000, f"Classic writer prompt bloated: {len(classic_prompt)} chars"
    assert len(v4_prompt) < 11000, f"V4 writer prompt bloated: {len(v4_prompt)} chars"

    for label, prompt in (("classic", classic_prompt), ("v4", v4_prompt)):
        assert "념글을 안 읽고도 100% 이해" in prompt, f"{label} prompt missing self-contained story rule"
        assert "3~3.5등신" in prompt, f"{label} prompt missing 3–3.5 head target"
        assert "아기 곰" in prompt and "공허방랑자" in prompt, f"{label} prompt missing fixed companion cues"
        assert "기계 복붙" in prompt, f"{label} prompt missing anti-catchphrase-copy rule"


def test_fixed_companions_auto_attach_for_hunter_and_warlock_only(tmp_path: Path) -> None:
    settings = load_settings(PROJECT_ROOT)
    hunter = resolve_cast_member("드워프 사냥꾼")
    warlock = resolve_cast_member("인간 흑마법사")
    warrior = resolve_cast_member("오크 전사")
    assert hunter is not None and hunter.companion_id == "hunter_bear"
    assert warlock is not None and warlock.companion_id == "warlock_voidwalker"
    assert warrior is not None and warrior.companion_id == ""

    bear_path = settings.turnarounds_dir / "hunter_bear.jpg"
    vw_path = settings.turnarounds_dir / "warlock_voidwalker.jpg"
    assert bear_path.exists() and vw_path.exists()
    bear_bytes = bear_path.read_bytes()
    vw_bytes = vw_path.read_bytes()

    fake_png_b64 = _fake_png_base64()
    captured: list[dict[str, Any]] = []

    class FakeInteractions:
        def create(self, **kwargs: Any) -> Any:
            captured.append(kwargs)
            return SimpleNamespace(output_image=SimpleNamespace(data=fake_png_b64))

    fake_client = SimpleNamespace(interactions=FakeInteractions())

    for idx, (char_name, expected_extra) in enumerate(
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
            visual_prompt=f"Low-angle 3-to-3.5 head comic reaction shot of {char_name} on pure #FFFFFF.",
        )
        artist.generate_cut_image(
            cut,
            tmp_path / f"cut_{idx}.png",
            client=fake_client,
            settings=settings,
        )
        items = captured[-1]["input"]
        attached_blobs = [base64.b64decode(it["data"]) for it in items[1:]]
        if expected_extra is not None:
            assert len(items) == 4  # text + style_ref + owner + companion
            assert expected_extra in attached_blobs
            assert "Cute Round Companion Mascot Sheet" in items[0]["text"]
        else:
            assert len(items) == 3  # text + style_ref + owner only
            assert bear_bytes not in attached_blobs
            assert vw_bytes not in attached_blobs
            assert "Cute Round Companion Mascot Sheet" not in items[0]["text"]


def test_v4_dry_run_pacing_and_non_breaking_dialogue_bloat_warning() -> None:
    post = _sample_post()
    dry = writer.build_dry_run_v4_script(post, episode_number=20, background_style="clean_white")

    audit = writer.audit_script_quality(dry, strict_cinematic=True)
    assert audit["passed"] is True, f"Dry-run V4 script failed strict audit: {audit['errors']}"
    assert audit["errors"] == []
    assert audit["warnings"] == []

    pacing = audit["dialogue_pacing"]
    assert pacing["bloated_3line_cuts"] == []
    assert len(pacing["short_1line_cuts"]) >= 4

    bloated_acts = []
    for act in dry.acts or []:
        new_cuts = []
        for c in act.cuts:
            if c.wordless:
                new_cuts.append(c)
            else:
                new_cuts.append(
                    c.model_copy(
                        update={
                            "dialogue": (
                                "내가 지금 하이잘 절벽 길에서\n"
                                "그림자 숨기를 쓰고 기다리다가\n"
                                "지나가는 상대한테 정배를 거는 중이야!"
                            )
                        }
                    )
                )
        bloated_acts.append(act.model_copy(update={"cuts": new_cuts}))
    bloated_script = dry.model_copy(
        update={
            "acts": bloated_acts,
            "cuts": [c for a in bloated_acts for c in a.cuts],
        }
    )

    bloated_audit = writer.audit_script_quality(bloated_script, strict_cinematic=True)
    assert bloated_audit["passed"] is True
    assert any("Dialogue pacing bloat" in w for w in bloated_audit["warnings"])
    assert len(bloated_audit["dialogue_pacing"]["bloated_3line_cuts"]) == len(
        [c for c in bloated_script.cuts if not c.wordless]
    )
