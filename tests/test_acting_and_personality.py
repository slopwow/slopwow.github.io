"""Dedicated test suite for the 9-Cast Personality/Aegyo Bible, Identity-vs-Acting
Decoupling, Dynamic Acting & Bold Camera Artist Prompts, and Show-Don't-Tell Writer Engine.
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


# ---------------------------------------------------------------------------
# 1. Cast Bible: 9 Unique Personalities, Aegyo Signatures & Pure Identity Locks
# ---------------------------------------------------------------------------


def test_cast_bible_all_nine_members_have_unique_personality_speech_aegyo_and_acting_range() -> None:
    assert len(CAST_BIBLE) == 9

    personalities: list[str] = []
    speech_styles: list[str] = []
    aegyo_signatures: list[str] = []
    acting_ranges: list[str] = []

    for member in CAST_BIBLE:
        assert member.personality.strip(), f"{member.id} missing personality"
        assert member.speech_style.strip(), f"{member.id} missing speech_style"
        assert member.aegyo_signature.strip(), f"{member.id} missing aegyo_signature"
        assert member.acting_range.strip(), f"{member.id} missing acting_range"

        personalities.append(member.personality.strip())
        speech_styles.append(member.speech_style.strip())
        aegyo_signatures.append(member.aegyo_signature.strip())
        acting_ranges.append(member.acting_range.strip())

    # Strictly zero duplicated personalities, speech styles, aegyo signatures, or acting ranges
    assert len(set(personalities)) == 9
    assert len(set(speech_styles)) == 9
    assert len(set(aegyo_signatures)) == 9
    assert len(set(acting_ranges)) == 9

    # Backward compatibility: new CastMember fields default cleanly to ""
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
        appearance_anchor="Fair-skinned chibi identity only.",
        default_prop="Stowed sword.",
        aliases=("테스트",),
        sheet_position="custom",
    )
    assert minimal.speech_style == ""
    assert minimal.aegyo_signature == ""
    assert minimal.acting_range == ""


def test_cast_appearance_anchors_strip_hardcoded_expression_locks_and_keep_identity_invariants() -> None:
    for member in CAST_BIBLE:
        lower_anchor = member.appearance_anchor.lower()
        for forbidden_expr in HARDCODED_STATIC_EXPRESSIONS:
            assert forbidden_expr not in lower_anchor, (
                f"{member.id}.appearance_anchor still hardcodes static expression '{forbidden_expr}'"
            )
        assert "fair-skinned" in lower_anchor, f"{member.id} lost fair-skinned invariant"
        assert "identity only" in lower_anchor, (
            f"{member.id}.appearance_anchor must explicitly mark identity ONLY"
        )
        assert "facial expression" in lower_anchor and "free" in lower_anchor, (
            f"{member.id}.appearance_anchor must leave facial expression free per scene"
        )

    # Canonical Draft C turnaround visual invariants remain 100% intact
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


def test_cast_formatters_include_personality_aegyo_and_identity_vs_acting_decoupling() -> None:
    writer_bible = format_cast_bible_for_writer()
    assert "9인 개성·애교 차별화" in writer_bible
    assert "성격:" in writer_bible
    assert "말투·애교 시그니처:" in writer_bible
    assert "표정 스펙트럼:" in writer_bible
    assert "~해야징~♪" in writer_bible  # explicitly cited as robotic copy-paste to avoid

    for member in CAST_BIBLE:
        assert member.name in writer_bible
        assert member.personality in writer_bible
        assert member.aegyo_signature in writer_bible
        assert member.acting_range in writer_bible

    anchors = build_character_anchors_block(["나이트엘프 사제", "타우렌 드루이드", "노움 도적"])
    assert "IDENTITY LOCK ONLY" in anchors
    assert "UNLEASHED DYNAMIC ACTING" in anchors
    assert "ZERO fixed expression sheet" in anchors
    assert "NEVER copy the stiff front-facing standing turnaround pose" in anchors
    assert "bland polite smile" in anchors
    for member_id in ("nightelf_priest", "tauren_druid", "gnome_rogue"):
        member = CAST_BY_ID[member_id]
        assert member.appearance_anchor in anchors
        assert member.acting_range in anchors

    # Empty character fallback also preserves Identity-vs-Acting decoupling
    fallback = build_character_anchors_block([])
    assert "IDENTITY LOCK ONLY" in fallback
    assert "UNLEASHED DYNAMIC ACTING" in fallback


# ---------------------------------------------------------------------------
# 2. Artist Prompts & Attachments: Identity vs Acting Decoupling + 0 Expr Sheet
# ---------------------------------------------------------------------------


def test_artist_build_page_batch_and_cut_prompts_enforce_unleashed_acting_anti_repetition_and_bold_cameras() -> None:
    post = _sample_post()
    script = writer.build_dry_run_v4_script(post, episode_number=20, background_style="clean_white")
    assert script.acts is not None

    # Test Act 1 (Tier 1 full-bleed Cut 1 + Tier 2/3 Cuts 2-3) AND Act 3 (Tier 2/3 clean_white)
    for act in (script.acts[0], script.acts[2], script.acts[3]):
        prompt = artist.build_page_batch_prompt(
            act,
            attached_turnarounds=["나이트엘프 사제 (nightelf_priest)", "노움 도적 (gnome_rogue)"],
            background_style="clean_white",
        )
        upper = prompt.upper()

        # Root cause fixed: no rigid full-silhouette lock!
        assert "LOCK 100% ONTO EXACT FRONT/SIDE/BACK SILHOUETTE" not in upper
        assert "IDENTITY & COSTUME LOCK ONLY" in upper
        assert "STRICT IDENTITY VS UNLEASHED ACTING DECOUPLING" in upper
        assert "BREAK THE PRETTY-FACE SAFETY ZONE" in upper
        assert "ZERO FIXED EXPRESSION SHEETS" in upper
        assert "GENERIC POLITE SMILE/WINK" in upper

        # Unleashed anime gag acting vocabulary
        for acting_cue in (
            "pinpoint psychotic pupils",
            "empty white shock eyes",
            "spiral dizzy eyes",
            "waterfalls",
            "jaw-dropped screaming",
            "smug cat `:3`",
            "gremlin grin",
            "forehead gloom shadows",
            "squash-and-stretch",
        ):
            assert acting_cue in prompt.lower(), f"Missing acting cue '{acting_cue}' in Act {act.act_number} prompt"

        # Anti-repetition & bold camera freedom
        assert "ANTI-REPETITION" in upper
        assert "NEVER REPEAT THE SAME FACIAL EXPRESSION" in upper
        for camera_cue in (
            "extreme face close-up",
            "fisheye forced-perspective",
            "bird's-eye top-down",
            "low-angle loom",
            "30° dutch tilt",
            "over-the-shoulder",
        ):
            assert camera_cue in prompt.lower(), f"Missing camera cue '{camera_cue}' in Act {act.act_number} prompt"
        assert "full-body dolls" in prompt.lower()

        # Existing 3-Tier Smart Background contracts remain 100% intact
        assert "NATURAL GROUNDED SCENERY" in upper
        assert "WHITE SKY" in upper
        assert "ZERO FLOATING MINIATURE TOY ISLANDS" in upper
        assert "ZERO TEXT" in upper
        assert "SOFT-VIGNETTE" not in upper
        assert "diorama_style_ref.jpg" not in prompt

    # Single-cut prompt (`build_cut_image_prompt`) also decouples Identity vs Acting
    cut = ComicCut(
        cut_index=5,
        aspect_ratio="4:3",
        layout_slot="top",
        characters=["나이트엘프 사제"],
        speaker="나이트엘프 사제",
        dialogue="어머, 귀여운 손님 왔네?\n정배 딸깍~♡",
        wordless=False,
        visual_prompt=(
            "Extreme low-angle face close-up with dark forehead gloom shadow, "
            "pinpoint psychotic glowing silver-white pupils, wide sweetly-evil grin."
        ),
        tail_target="center",
    )
    single_prompt = artist.build_cut_image_prompt(
        cut,
        attached_turnarounds=["나이트엘프 사제 (nightelf_priest)"],
    )
    assert "lock 100% onto this character's exact front/side/back silhouette" not in single_prompt.lower()
    assert "IDENTITY & COSTUME LOCK ONLY" in single_prompt
    assert "STRICT IDENTITY vs UNLEASHED ACTING DECOUPLING" in single_prompt
    assert "BREAK THE PRETTY-FACE SAFETY ZONE" in single_prompt
    assert "fisheye" in single_prompt.lower()
    assert "30° Dutch tilt" in single_prompt


def test_artist_attaches_zero_expression_sheets_and_exact_reference_order(tmp_path: Path) -> None:
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
        assert "STRICT IDENTITY vs UNLEASHED ACTING DECOUPLING" in prompt_text
        assert "ZERO FIXED EXPRESSION SHEETS" in prompt_text

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

        # Exact attachment count: [text, cast_sheet, style_ref, layout_blueprint, *turnarounds]
        # STRICTLY ZERO expression sheet attachments!
        assert len(items) == 4 + len(unique_members), (
            f"Act {act.act_number} expected {4 + len(unique_members)} items (0 expression sheets), got {len(items)}"
        )
        assert base64.b64decode(items[1]["data"]) == cast_sheet_bytes
        assert base64.b64decode(items[2]["data"]) == style_ref_bytes

        attached_turnarounds = {base64.b64decode(item["data"]) for item in items[4:]}
        expected_turnarounds = {
            (settings.turnarounds_dir / m.turnaround_filename).read_bytes()
            for m in unique_members
        }
        assert attached_turnarounds == expected_turnarounds

    assert matched_acts == {1, 2, 3, 4, 5}

    # Single-cut generation also attaches exact [text, cast_sheet, style_ref, *turnarounds] (0 expression sheets)
    single_calls: list[dict[str, Any]] = []

    class FakeSingleInteractions:
        def create(self, **kwargs: Any) -> Any:
            single_calls.append(kwargs)
            return SimpleNamespace(output_image=SimpleNamespace(data=fake_png_b64))

    cut = ComicCut(
        cut_index=1,
        aspect_ratio="4:3",
        layout_slot="top",
        characters=["나이트엘프 사제", "노움 도적"],
        speaker="나이트엘프 사제",
        dialogue="정배 딸깍~♡",
        wordless=False,
        visual_prompt="Extreme face close-up on pure #FFFFFF white background.",
        tail_target="left",
    )
    artist.generate_cut_image(
        cut,
        tmp_path / "single_cut.png",
        client=SimpleNamespace(interactions=FakeSingleInteractions()),
        settings=settings,
    )
    assert len(single_calls) == 1
    assert len(single_calls[0]["input"]) == 3 + 2


# ---------------------------------------------------------------------------
# 3. Writer Engine: Show-Don't-Tell, Aegyo Retention, 1–2 Line Rhythm & Acting Diet
# ---------------------------------------------------------------------------


def test_writer_prompts_enforce_show_dont_tell_aegyo_punch_rhythm_and_acting_first_diet() -> None:
    post = _sample_post()
    classic_prompt = writer.build_writer_prompt(post, episode_number=20)
    v4_prompt = writer.build_v4_writer_prompt(post, episode_number=20, background_style="clean_white")

    for label, prompt in (("classic", classic_prompt), ("v4", v4_prompt)):
        # Show, Don't Tell
        assert "Show, Don't Tell" in prompt, f"{label} prompt missing Show, Don't Tell rule"
        assert "그림 중계 절대 금지" in prompt, f"{label} prompt missing anti-narration rule"

        # Per-character aegyo retention (NOT flat robotic copy-paste)
        assert "애교" in prompt
        assert "애교 시그니처" in prompt
        assert "~해야징~♪" in prompt  # cited as robotic repetition to avoid
        for member in CAST_BIBLE:
            assert member.aegyo_signature in prompt, f"{label} prompt missing {member.id} aegyo_signature"

        # 1–2 line snappy punch rhythm + 2-Pass internal dialogue polish
        assert "30~40%" in prompt
        assert "5~15자" in prompt
        assert "1~2줄" in prompt
        assert "2-Pass" in prompt

        # Visual prompt acting-first diet (70%+ acting/expression/bold cameras)
        assert "Visual Prompt Diet" in prompt
        assert "70%" in prompt
        assert "squash-and-stretch" in prompt.lower()
        assert "fisheye" in prompt.lower()
        assert "bird's-eye" in prompt.lower()
        assert "30° 더치 틸트" in prompt
        assert "고정 6표정 시트 금지" in prompt


def test_v4_dry_run_pacing_and_non_breaking_dialogue_bloat_warning() -> None:
    post = _sample_post()
    dry = writer.build_dry_run_v4_script(post, episode_number=20, background_style="clean_white")

    audit = writer.audit_script_quality(dry, strict_cinematic=True)
    assert audit["passed"] is True, f"Dry-run V4 script failed strict audit: {audit['errors']}"
    assert audit["errors"] == []
    assert audit["warnings"] == []

    pacing = audit["dialogue_pacing"]
    assert pacing["bloated_3line_cuts"] == []
    assert len(pacing["short_1line_cuts"]) >= 4, (
        f"Expected >= 4 snappy 1-line punch cuts in V4 dry-run, got {pacing['short_1line_cuts']}"
    )

    # Bloated V4 script (>70% dense 3-line >32-char walls) emits a SOFT warning without breaking `passed=True`
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
    assert bloated_audit["passed"] is True, "Bloat check must remain a soft non-breaking warning"
    assert any("Dialogue pacing bloat" in w for w in bloated_audit["warnings"]), (
        f"Expected soft dialogue bloat warning, got warnings={bloated_audit['warnings']}"
    )
    assert len(bloated_audit["dialogue_pacing"]["bloated_3line_cuts"]) == len(
        [c for c in bloated_script.cuts if not c.wordless]
    )
