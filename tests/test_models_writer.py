"""Unit tests for Route A models (4~7 cuts), 9-cast SD bible, and Gemini Interactions writer & artist."""

from __future__ import annotations

import base64
import io
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from PIL import Image
from pydantic import ValidationError

from wow_sloptoon import artist, writer
from wow_sloptoon.cast import (
    CAST_BIBLE,
    build_character_anchors_block,
    canonical_cast_name,
    resolve_cast_member,
)
from wow_sloptoon.config import (
    DEFAULT_IMAGE_MODEL,
    DEFAULT_TEXT_MODEL,
    SUPPORTED_IMAGE_MODELS,
    load_settings,
)
from wow_sloptoon.models import ComicCut, EpisodeRecord, EpisodeScript, GalleryPost


def _sample_post() -> GalleryPost:
    return GalleryPost(
        post_no="99001",
        title="흑마가 멜론 주스 준 썰",
        url="https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=99001",
        author="포에버갤러",
        date_str="2026-11-21 14:00:00",
        views=1200,
        recommends=55,
        comments_count=24,
        body="던전에서 마나 없다고 물 달랬는데 흑마가 멜론 주스 20개 거래창에 올림 ㅋㅋ",
        comments=["법사가 옆에서 기절했겠다 ㅋㅋ", "마셔라 헬스크림"],
    )


def _sample_cuts(count: int = 5, *, include_wordless: bool = True) -> list[ComicCut]:
    cuts: list[ComicCut] = []
    for i in range(1, count + 1):
        is_wordless = include_wordless and i == 4
        slot = "top" if (i % 2 == 1 and not (count % 2 == 1 and i == count)) else "bottom"
        ratio = "4:3" if slot == "top" else "16:9"
        cuts.append(
            ComicCut(
                cut_index=i,
                aspect_ratio=ratio,
                layout_slot=slot,
                characters=["인간 흑마법사"] if is_wordless else ["나이트엘프 사제", "인간 흑마법사"],
                speaker=None if is_wordless else "나이트엘프 사제",
                dialogue=None if is_wordless else f"테스트 대사 {i}",
                wordless=is_wordless,
                visual_prompt=f"Cut {i} cute 2.5-head chibi SD reaction on pure #FFFFFF.",
                tail_target="center" if is_wordless else "left",
            )
        )
    return cuts


def test_episode_script_validates_route_a_4_to_7_cuts_characters_and_wordless() -> None:
    # 4~7 cuts are valid when at least one wordless cut is present
    for n in (4, 5, 6, 7):
        script = EpisodeScript(
            episode_number=3,
            source_post_no="99001",
            source_title="테스트 화",
            source_url="https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=99001",
            subtitle="테스트 부제",
            cuts=_sample_cuts(n, include_wordless=True),
        )
        assert len(script.cuts) == n

    # 3 cuts fails
    with pytest.raises(ValidationError):
        EpisodeScript(
            episode_number=3,
            source_post_no="99001",
            source_title="너무 짧음",
            source_url="https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=99001",
            subtitle="실패",
            cuts=_sample_cuts(3, include_wordless=True),
        )

    # 8 cuts fails (V4 / 8+ cuts permanently retired; strict 4~7 cut window)
    with pytest.raises(ValidationError):
        EpisodeScript(
            episode_number=3,
            source_post_no="99001",
            source_title="너무 김",
            source_url="https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=99001",
            subtitle="실패",
            cuts=_sample_cuts(8, include_wordless=True),
        )

    # Missing wordless cut fails
    with pytest.raises(ValidationError):
        EpisodeScript(
            episode_number=3,
            source_post_no="99001",
            source_title="무언 컷 없음",
            source_url="https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=99001",
            subtitle="실패",
            cuts=_sample_cuts(4, include_wordless=False),
        )

    # 3 characters in a single cut fails
    with pytest.raises(ValidationError):
        ComicCut(
            cut_index=1,
            aspect_ratio="4:3",
            layout_slot="top",
            characters=["오크 전사", "노움 도적", "트롤 주술사"],
            speaker="오크 전사",
            dialogue="셋은 너무 많아",
            wordless=False,
            visual_prompt="Too many characters",
        )


def test_wordless_cut_clears_dialogue_and_speaker() -> None:
    cut = ComicCut(
        cut_index=4,
        aspect_ratio="16:9",
        layout_slot="bottom",
        characters=["스카이본 마법사"],
        speaker="스카이본 마법사",
        dialogue="말하면 안됨",
        wordless=True,
        visual_prompt="Silent shocked mage big close-up in cute 2.5-head SD style",
        tail_target="center",
    )
    assert cut.speaker is None
    assert cut.dialogue is None


def test_cast_bible_has_9_route_a_sd_characters_and_alias_mapping() -> None:
    assert len(CAST_BIBLE) == 9
    expected_names = {
        "오크 전사",
        "언데드 성기사",
        "노움 도적",
        "드워프 사냥꾼",
        "트롤 주술사",
        "타우렌 드루이드",
        "나이트엘프 사제",
        "인간 흑마법사",
        "스카이본 마법사",
    }
    assert {m.name for m in CAST_BIBLE} == expected_names

    assert canonical_cast_name("흑마") == "인간 흑마법사"
    assert canonical_cast_name("보기") == "언데드 성기사"
    assert canonical_cast_name("나엘사제") == "나이트엘프 사제"
    assert canonical_cast_name("법사") == "스카이본 마법사"
    druid = resolve_cast_member("회드")
    assert druid is not None and druid.name == "타우렌 드루이드"

    anchors = build_character_anchors_block(["흑마", "법사"])
    assert "human_warlock" in anchors
    assert "warlock_voidwalker" in anchors
    assert "skyborne_mage" in anchors
    assert "2-to-2.5 head SD" in anchors
    assert "tilted blue wizard hat" in anchors
    assert "Polymorph Sheep charm" in anchors
    assert "imp" not in anchors.lower()
    assert "sailor" not in anchors.lower()
    assert "3-to-3.5" not in anchors.lower()
    assert "sleek" not in anchors.lower()


def test_writer_uses_interactions_api_gemini_4_hydrogen_and_normalizes_cast() -> None:
    post = _sample_post()
    raw_script = EpisodeScript(
        episode_number=3,
        source_post_no=post.post_no,
        source_title="LLM이 임의로 바꾼 제목",
        source_url=post.url,
        subtitle="뉴비 흑마의 멜론 주스 보급 사건",
        cuts=[
            ComicCut(
                cut_index=1,
                aspect_ratio="4:3",
                layout_slot="top",
                characters=["나엘사제", "흑마"],
                speaker="나엘사제",
                dialogue="저기 물 좀 주세요...",
                wordless=False,
                visual_prompt="Over-the-shoulder cute 2.5-head SD shot of Priest asking Warlock for water.",
                tail_target="left",
            ),
            ComicCut(
                cut_index=2,
                aspect_ratio="16:9",
                layout_slot="bottom",
                characters=["흑마"],
                speaker="흑마",
                dialogue="멜론 주스 20개 챙겼어!",
                wordless=False,
                visual_prompt="Low-angle cute 2.5-head SD shot of Warlock offering glass flasks beside her Voidwalker.",
                tail_target="right",
            ),
            ComicCut(
                cut_index=3,
                aspect_ratio="4:3",
                layout_slot="top",
                characters=["도적", "법사"],
                speaker="도적",
                dialogue="야 흑마가 물을 왜 줘 ㅋㅋ",
                wordless=False,
                visual_prompt="Side-profile cute 2.5-head SD shot of Rogue pointing next to Mage.",
                tail_target="left",
            ),
            ComicCut(
                cut_index=4,
                aspect_ratio="16:9",
                layout_slot="bottom",
                characters=["법사"],
                wordless=True,
                visual_prompt="Dutch-tilt big bust-up close-up of shocked speechless Mage on pure #FFFFFF.",
                tail_target="center",
            ),
        ],
    )

    captured_calls: list[dict[str, Any]] = []

    class FakeInteractions:
        def create(self, **kwargs: Any) -> Any:
            captured_calls.append(kwargs)
            return SimpleNamespace(output_text=raw_script.model_dump_json())

    fake_client = SimpleNamespace(interactions=FakeInteractions())

    result = writer.generate_episode_script(post, episode_number=3, client=fake_client)
    assert len(captured_calls) == 1
    call = captured_calls[0]
    assert call["model"] == DEFAULT_TEXT_MODEL == "gemini-4-hydrogen"
    assert call["response_format"]["type"] == "text"
    assert call["response_format"]["mime_type"] == "application/json"
    assert "properties" in call["response_format"]["schema"]
    assert "메타 댓글 반응" in call["input"]
    assert "wordless=True" in call["input"]
    assert "#FFFFFF" in call["input"]

    # Verbatim source title enforced & aliases normalized to canonical Korean names
    assert result.source_title == post.title
    assert result.cuts[0].characters == ["나이트엘프 사제", "인간 흑마법사"]
    assert result.cuts[0].speaker == "나이트엘프 사제"
    assert result.cuts[3].characters == ["스카이본 마법사"]
    assert result.cuts[3].wordless is True


def test_artist_uses_interactions_api_nano_banana_and_attaches_route_a_refs(tmp_path: Path) -> None:
    settings = load_settings()
    assert settings.cast_sheet_path.exists()
    assert settings.style_ref_path.name == "diorama_style_ref.jpg"
    assert settings.style_ref_path.exists()
    assert settings.turnarounds_dir.exists()
    for member in CAST_BIBLE:
        assert (settings.turnarounds_dir / member.turnaround_filename).exists()
        if member.companion_turnaround_filename:
            assert (settings.turnarounds_dir / member.companion_turnaround_filename).exists()

    buf = io.BytesIO()
    Image.new("RGB", (64, 48), (255, 255, 255)).save(buf, format="PNG")
    fake_png_b64 = base64.b64encode(buf.getvalue()).decode("ascii")

    captured_calls: list[dict[str, Any]] = []

    class FakeInteractions:
        def create(self, **kwargs: Any) -> Any:
            captured_calls.append(kwargs)
            return SimpleNamespace(output_image=SimpleNamespace(data=fake_png_b64))

    fake_client = SimpleNamespace(interactions=FakeInteractions())
    script = writer.build_dry_run_script(_sample_post(), episode_number=3)

    out_paths = artist.generate_episode_cuts(
        script,
        tmp_path / "raw_cuts",
        client=fake_client,
        settings=settings,
        max_workers=1,
    )

    assert len(out_paths) == len(script.cuts)
    assert len(captured_calls) == len(script.cuts)

    first_call = captured_calls[0]
    assert first_call["model"] == DEFAULT_IMAGE_MODEL == "gemini-nano-banana-2.1"
    assert first_call["response_format"] == {
        "type": "image",
        "aspect_ratio": script.cuts[0].aspect_ratio,
        "image_size": "1K",
    }

    resolved_first = []
    seen_first: set[str] = set()
    for c in script.cuts[0].characters:
        m = resolve_cast_member(c)
        if m and m.id not in seen_first:
            seen_first.add(m.id)
            resolved_first.append(m)
    expected_companion_count = sum(
        1
        for m in resolved_first
        if m.companion_turnaround_filename
        and (settings.turnarounds_dir / m.companion_turnaround_filename).exists()
    )
    assert len(first_call["input"]) == 2 + len(resolved_first) + expected_companion_count
    assert first_call["input"][0]["type"] == "text"
    prompt_text = first_call["input"][0]["text"]
    assert "#FFFFFF" in prompt_text
    assert "2-to-2.5 head" in prompt_text
    assert "diorama_style_ref.jpg" in prompt_text
    assert "3-to-3.5" not in prompt_text
    assert "sleek" not in prompt_text.lower()
    assert base64.b64decode(first_call["input"][1]["data"]) == settings.style_ref_path.read_bytes()
    for img_item in first_call["input"][1:]:
        assert img_item["type"] == "image"

    for cut_idx, img_path in out_paths.items():
        assert img_path.exists()
        with Image.open(img_path) as im:
            assert im.size == (64, 48)

    for m in SUPPORTED_IMAGE_MODELS:
        assert artist.resolve_image_model(m, settings) == m
    with pytest.raises(ValueError):
        artist.resolve_image_model("invalid-legacy-model", settings)


def test_episode_record_model_validation() -> None:
    record = EpisodeRecord(
        episode_id="ep001",
        episode_number=1,
        title="흑마법사가 물을 어케 줌?",
        subtitle="멜론 주스 사건",
        source_post_no="92059",
        source_url="https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=92059",
        created_at="2026-11-21T01:30:00+09:00",
        cut_count=5,
        cast_used=["나이트엘프 사제", "인간 흑마법사", "스카이본 마법사"],
        full_image_rel="data/episodes/ep001/episode_full.jpg",
        thumb_image_rel="data/episodes/ep001/thumb.jpg",
        page_images_rel=["data/episodes/ep001/page_1.png"],
    )
    assert record.episode_id == "ep001"
    assert record.cut_count == 5
