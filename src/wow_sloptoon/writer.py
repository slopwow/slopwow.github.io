"""Episode script writer powered by Google GenAI Interactions API (`gemini-4-hydrogen`).

Produces strictly 100% live in-game dungeon/party gag skits (4~6 cuts, 1~2 cast members per cut,
at least one signature wordless shocked/deadpan freeze-frame cut, Draft C visual anchors, and
pure #FFFFFF background).
"""

from __future__ import annotations

import json
from typing import Any

from google import genai

from wow_sloptoon.cast import canonical_cast_name, format_cast_bible_for_writer
from wow_sloptoon.config import DEFAULT_TEXT_MODEL, Settings, load_settings
from wow_sloptoon.models import ComicCut, EpisodeScript, GalleryPost

WRITER_SYSTEM_RULES = """당신은 디시인사이드 '와우 포에버 마이너 갤러리(wowforever)' 개념글을 4~6컷 초귀염 팝·개그 웹툰(《와우 포에버 슬롭툰》) 대본으로 각색하는 전문 시나리오 작가입니다.

[절대 준수 연출 규칙]
1. **100% 라이브 던전/인던/대도시/파티 상황극**:
   - 원글의 에피소드와 재미있는 댓글 드립을 전부 게임 속 현장 대사·상황극으로 녹여내세요.
   - "어 댓글 반응 보니까~", "갤러들이 이렇게 말하네~", "개념글 올라갔네~" 같은 **어색한 메타 댓글 반응 컷/제4의 벽 깨기는 절대 금지**합니다!
2. **분량 및 리듬 (4~6컷)**:
   - 정확히 **4컷, 5컷, 또는 6컷**으로 구성하세요 (`cut_index`는 1부터 순차 증가).
   - 2단 슬롭툰 페이지 구조에 맞춰 슬롯과 비율을 배치하세요:
     * 홀수 컷(1, 3, 5번): `layout_slot="top"`, `aspect_ratio="4:3"` (단, 전체가 5컷일 때 마지막 5번 컷은 단독 피날레 리액션 박스이므로 `layout_slot="bottom"`, `aspect_ratio="16:9"` 권장).
     * 짝수 컷(2, 4, 6번): `layout_slot="bottom"`, `aspect_ratio="16:9"`.
3. **컷당 출연 인원 (1~2명 엄수)**:
   - 각 컷의 `characters` 배열에는 반드시 아래 공식 시안 C 캐스트 9명 중 **정확히 1명 또는 2명**의 정식 한국어 이름만 넣으세요.
   - 한 컷에 3명 이상을 절대 넣지 마세요.
4. **시그니처 무언 동공지진 정지 화면 (`wordless=True`) 최소 1컷 필수**:
   - 애용갤 슬롭툰 특유의 찰진 개그 타이밍을 위해, **최소 1개 컷(권장: 하단 `bottom` / `16:9` 컷)은 반드시 `wordless=True`, `speaker=null`, `dialogue=null`** 로 설정하세요.
   - 무언 컷의 `visual_prompt`에는 캐릭터 1명의 정중앙 클로즈업, 동공지진·정색·영혼 가출·땀방울·충격 정지 표정을 아주 생생하게 영문으로 묘사하세요.
5. **대사 (`dialogue`) 작성 규칙**:
   - 말풍선 안에 깔끔히 들어가도록 한국어 구어체 **1~3줄(줄당 14자 내외, `\\n` 줄바꿈 포함)**로 임팩트 있게 작성하세요.
   - `tail_target`은 화자가 화면 왼쪽이면 `"left"`, 오른쪽이면 `"right"`, 정중앙이면 `"center"`로 지정하세요.
   - 와우 포에버갤 감성을 살리되, 타 커뮤니티 이름은 절대 언급하지 마세요.
6. **영문 비주얼 프롬프트 (`visual_prompt`) 규칙**:
   - 반드시 영문으로 캐릭터의 좌우 위치, 포즈, 소품, 표정, 감정을 구체적으로 묘사하세요.
   - 모든 컷은 **100% pure solid white `#FFFFFF` borderless background (no scenery, no text, no speech bubbles)** 조건을 전제로 캐릭터와 최소한의 소품(물병, 멜론 주스, 도끼, 지팡이, 호빵 등)만 등장하도록 묘사하세요.
   - 공식 시안 C 미소녀 복장·헤어·후드·소품 디테일을 일관되게 유지하세요.
"""


def build_writer_prompt(post: GalleryPost, episode_number: int) -> str:
    """Assemble the complete structured prompt for `gemini-4-hydrogen`."""
    cast_bible = format_cast_bible_for_writer()
    comments_block = (
        "\n".join(f"- {c}" for c in post.comments[:12])
        if post.comments
        else "(별도 댓글 없음 — 본문 에피소드 자체를 찰진 라이브 상황극으로 극대화하세요)"
    )

    return (
        f"{WRITER_SYSTEM_RULES}\n\n"
        f"{cast_bible}\n\n"
        f"=== 각색 대상 포에버갤 개념글 ===\n"
        f"- 예정 화수: EP.{episode_number}\n"
        f"- 게시글 번호: #{post.post_no}\n"
        f"- 원문 URL: {post.url}\n"
        f"- 제목: {post.title}\n"
        f"- 작성자: {post.author} | 추천: {post.recommends} | 댓글: {post.comments_count}\n"
        f"- 본문:\n{post.body or '(본문 텍스트 없음 — 제목의 펀치라인을 던전 상황극으로 풀어내세요)'}\n\n"
        f"- 주요 댓글 (메타 해설 금지! 웃긴 포인트만 캐릭터 대사·상황극 소재로 흡수):\n{comments_block}\n\n"
        f"위 JSON 스키마(`EpisodeScript`)에 정확히 맞춰 출력하세요. "
        f"`episode_number`는 {episode_number}, `source_post_no`는 \"{post.post_no}\", "
        f"`source_url`은 \"{post.url}\" 로 정확히 기입하세요."
    )


def _extract_interaction_text(interaction: Any) -> str:
    """Extract raw text/JSON string from a google-genai Interactions API response."""
    output_text = getattr(interaction, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    outputs = getattr(interaction, "outputs", None)
    if outputs:
        for item in reversed(outputs):
            text = getattr(item, "text", None)
            if isinstance(text, str) and text.strip():
                return text.strip()
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                return item["text"].strip()

    raise ValueError("Gemini Interactions API response did not contain JSON text output.")


def _normalize_script(
    script: EpisodeScript,
    post: GalleryPost,
    episode_number: int,
) -> EpisodeScript:
    """Ensure canonical Draft C names and exact source post metadata on a parsed script."""
    normalized_cuts: list[ComicCut] = []
    for idx, cut in enumerate(script.cuts, start=1):
        norm_chars = [canonical_cast_name(c) for c in cut.characters]
        norm_speaker = (
            None
            if cut.wordless or not cut.speaker
            else canonical_cast_name(cut.speaker)
        )
        normalized_cuts.append(
            cut.model_copy(
                update={
                    "cut_index": idx,
                    "characters": norm_chars,
                    "speaker": norm_speaker,
                    "dialogue": None if cut.wordless else cut.dialogue,
                }
            )
        )

    return script.model_copy(
        update={
            "episode_number": episode_number,
            "source_post_no": str(post.post_no),
            "source_url": post.url,
            "cuts": normalized_cuts,
        }
    )


def generate_episode_script(
    post: GalleryPost,
    episode_number: int,
    *,
    client: Any | None = None,
    settings: Settings | None = None,
    model: str | None = None,
) -> EpisodeScript:
    """Generate and validate a 4~6 cut `EpisodeScript` via Gemini Interactions API."""
    cfg = settings or load_settings()
    target_model = model or cfg.text_model or DEFAULT_TEXT_MODEL

    if client is None:
        if not cfg.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Configure GEMINI_API_KEY in .env or environment, "
                "or run with --dry-run."
            )
        client = genai.Client(api_key=cfg.gemini_api_key)

    prompt = build_writer_prompt(post, episode_number=episode_number)
    interaction = client.interactions.create(
        model=target_model,
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": EpisodeScript.model_json_schema(),
        },
    )

    raw_json = _extract_interaction_text(interaction)
    # Strip accidental markdown fences if any
    if raw_json.startswith("```"):
        lines = raw_json.splitlines()
        raw_json = "\n".join(
            line for line in lines if not line.strip().startswith("```")
        ).strip()

    # Validate JSON directly with Pydantic v2
    script = EpisodeScript.model_validate_json(raw_json)
    return _normalize_script(script, post=post, episode_number=episode_number)


def build_dry_run_script(post: GalleryPost, episode_number: int) -> EpisodeScript:
    """Build a deterministic offline 4-cut Draft C script for `--dry-run` previews and smoke tests."""
    short_title = post.title.strip() or f"개념글 #{post.post_no}"
    snippet = (post.body.strip().splitlines()[0][:28] + "...") if post.body.strip() else short_title[:28]

    cuts = [
        ComicCut(
            cut_index=1,
            aspect_ratio="4:3",
            layout_slot="top",
            characters=["나이트엘프 사제", "오크 전사"],
            speaker="나이트엘프 사제",
            dialogue=f"저기요...\n'{short_title[:18]}'\n이거 실화예요?",
            wordless=False,
            visual_prompt=(
                "Left: Night Elf Priest chibi girl with dark under-eye circles holding her "
                "golden crescent staff looking exhausted and asking nervously. Right: Orc "
                "Warrior chibi girl in green orc hood grinning confidently with her axe. "
                "Pure solid white #FFFFFF background, no text, no speech bubbles."
            ),
            tail_target="left",
        ),
        ComicCut(
            cut_index=2,
            aspect_ratio="16:9",
            layout_slot="bottom",
            characters=["오크 전사"],
            speaker="오크 전사",
            dialogue=f"당연하지!\n{snippet}\n던전이 원래 그런 곳이야!",
            wordless=False,
            visual_prompt=(
                "Right side: Orc Warrior chibi girl in vibrant green orc animal hood raising "
                "her silver battle axe proudly with sparkles and cheeky grin. Pure solid "
                "white #FFFFFF background, no text, no speech bubbles."
            ),
            tail_target="right",
        ),
        ComicCut(
            cut_index=3,
            aspect_ratio="4:3",
            layout_slot="top",
            characters=["노움 도적", "스카이본 마법사"],
            speaker="노움 도적",
            dialogue="어어 잠깐만,\n그거 탱커랑 힐러\n다 듣고 있는데?",
            wordless=False,
            visual_prompt=(
                "Left: Gnome Rogue chibi girl with blonde-pink-blue pigtails and green goggles "
                "pointing mischievously while flashing a sly grin. Right: Skyborne Mage chibi "
                "girl holding a warm steamed bun and blue mana flask looking over. Pure solid "
                "white #FFFFFF background, no text, no speech bubbles."
            ),
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
            visual_prompt=(
                "Centered dramatic deadpan close-up freeze-frame of Skyborne Mage chibi girl "
                "with blonde-to-sky-blue hair and sailor uniform, tiny trembling shocked pupils, "
                "frozen speechless while holding her glowing blue mana flask and steamed bun. "
                "Pure solid white #FFFFFF background, no text, no speech bubbles."
            ),
            tail_target="center",
        ),
    ]

    return EpisodeScript(
        episode_number=episode_number,
        source_post_no=str(post.post_no),
        source_title=short_title,
        source_url=post.url,
        subtitle=f"포에버갤 #{post.post_no} 드라이런 상황극 프리뷰",
        cuts=cuts,
    )


def script_to_pretty_json(script: EpisodeScript) -> str:
    """Serialize an `EpisodeScript` as UTF-8 readable JSON."""
    return json.dumps(script.model_dump(mode="json"), ensure_ascii=False, indent=2)
