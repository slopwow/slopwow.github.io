"""Episode script writer powered by Google GenAI Interactions API (`gemini-4-hydrogen`).

Produces self-contained WoW Forever (2026 Classic+) gag webtoon scripts that readers can
understand 100% WITHOUT reading the original DCInside post:
- Primary classic 2-tier mode: 4~8 cuts (recommended 5~6 cuts), crisp 3–3.5 head sleek
  Korean gag webtoon direction, 1~2 cast per cut, 2~4 core cast, mandatory wordless beat.
- Optional V4 5-act long-form mode: 5 acts / 10~14 cuts across variable page layouts.
- Clean, compact prompts with zero robotic catchphrase copy-paste and full quality auditing.
"""

from __future__ import annotations

import json
import re
from typing import Any, Sequence

from google import genai

from wow_sloptoon.cast import (
    canonical_cast_name,
    format_cast_bible_for_writer,
    resolve_cast_member,
)
from wow_sloptoon.config import DEFAULT_TEXT_MODEL, Settings, load_settings
from wow_sloptoon.layouts import PAGE_LAYOUTS, get_page_layout
from wow_sloptoon.models import ActPage, BackgroundStyle, ComicCut, EpisodeScript, GalleryPost
from wow_sloptoon.wow_lore import (
    ALLIANCE_ZONES,
    HORDE_ZONES,
    build_wow_lore_guidance,
    find_modern_slang_violations,
)

WRITER_SYSTEM_RULES = """당신은 디시인사이드 '와우 포에버 마이너 갤러리(wowforever)' 개념글을 4~8컷(권장 5~6컷) 날렵한 3~3.5등신 개그 웹툰(《와우 포에버 슬롭툰》) 대본으로 각색하는 시나리오 작가입니다.

[핵심 원칙]
1. **념글을 안 읽고도 100% 이해되는 완결 서사 (최우선!)**:
   - 독자는 원본 게시글 제목·본문을 전혀 보지 않고 이 만화만 처음 읽는다고 가정하세요.
   - 반드시 **① 상황 설정**(어디 던전/필드인지, 어떤 파티·룰·목적인지) → **② 사건 발단**(누가 무엇을 요구하거나 어떤 템·행동이 터졌는지) → **③ 황당·갈등 포인트**(왜 어이없고 웃긴지 명확한 인과) → **④ 무언 충격 정지 컷(`wordless=True`)** → **⑤ 여파·펀치라인**이 물 흐르듯 자급자족으로 이어지게 쓰세요.
   - 원글의 실제 상황과 핵심 디테일을 100% 인게임 현장극으로 살리고, 분량을 채우기 위한 억지 전투 씬·불필요한 캐릭터 끼워팔기를 금지합니다.
   - 메타 댓글 반응 컷("개념글 갔네~", "갤러들이~")과 타 커뮤니티(인벤 등) 언급을 금지합니다.

2. **분량 및 2단 페이지 슬롯 (4~8컷, 권장 5~6컷)**:
   - 원글 서사 밀도에 맞춰 정확히 **4~8컷**으로 구성하세요(짧은 썰은 4~6컷, 맥락 설명이 필요한 사건은 7~8컷).
   - 홀수 컷(1, 3, 5, 7번): `layout_slot="top"`, `aspect_ratio="4:3"` (단, 전체 컷 수가 홀수일 때 마지막 컷은 단독 피날레 박스이므로 `layout_slot="bottom"`, `aspect_ratio="16:9"`).
   - 짝수 컷(2, 4, 6, 8번): `layout_slot="bottom"`, `aspect_ratio="16:9"`.

3. **캐스트 집중 & 무언 충격 정지 컷**:
   - 각 컷의 `characters`는 공식 9인 캐스트 중 **1~2명**, 한 화 전체 주연은 **핵심 1~4명** 이내로 집중하세요.
   - 장면에 필요한 몹·보스·NPC·엑스트라·귀여운 비고어 해골/시체 더미·펫·탈것은 `visual_prompt`에 자연스럽게 넣으세요.
   - 사건의 황당함이 터지는 절정 1컷(권장: 하단 `bottom` / `16:9`)은 반드시 **`wordless=True`, `speaker=null`, `dialogue=null`**로 설정해 표정과 상황만으로 웃기세요.

4. **자연스러운 구어체 대사 (`dialogue`) & 100% 익명화**:
   - 캐릭터 성격은 은은한 말투 뉘앙스로만 살리고, 고정 유행어·애교 어미(`옴뇸뇸~`, `으, 으엣?!`, `후훗…`, `~해야징~♪`, 문장 끝 `~♡` 도배) 기계 복붙과 거친 욕설, AI 설명충 존댓말을 금지합니다.
   - **념글 미독자도 즉시 이해하도록** 필요한 맥락(던전명·역할·아이템·룰·이유)을 **1~3줄(줄당 12~16자, `\\n` 줄바꿈)** 자연스러운 와우 구어체로 담으세요.
   - **괄호 다중 화자 편법 절대 금지**: 한 컷 `dialogue`에는 `speaker` 단 1명의 대사만 적으세요(`(도적: ...)` 금지). `tail_target`은 화자 위치(`left`/`right`/`center`).
   - 현실 현대어(`119`, `구급차`, `경찰`, `카톡`, `편의점`, `택시`) 대신 와우 어휘(`무덤 이동`, `영혼의 치유사`, `경비병`, `귓말/파티창`, `여관 주인`, `와이번/그리핀`)만 사용하세요.
   - 실제 아이디·닉네임·길드명(패러디 포함)을 어디에도 적지 말고 직업·역할 호칭(`도적`, `징기`, `보기`, `전탱`, `흑마`, `사제`, `파장님`)만 사용하세요.

5. **간결한 영문 시각 연출 (`visual_prompt`, 2~4문장)**:
   - 캐릭터 의상·색상은 `artist.py`가 턴어라운드로 자동 고정하므로, 매 컷 의상 200단어나 가드레일을 복붙하지 마세요.
   - 대신 **3~3.5등신 날렵한 한국 개그 웹툰 스타일**을 전제로 **① 카메라 앵글**(OTS, 로우앵글, 하이앵글, 클로즈업, 측면, 뒷모습 — 평면 정면 나란히 서기는 한 화 최대 1컷) **② 캐릭터 행동·표정·위치(left/right/center)** **③ 핵심 소품·최소 바닥 터치**만 영문 2~4문장으로 생생하게 적으세요.
   - Clean Hand Rule(전리품·방패·주사위·귀환석·물약병을 들 때 기본 무기는 등/허리에 수납), 탱커(전탱/보기)는 한손 무기+방패, 사슬(Mail)=링메일 갑옷, 음료=판타지 코르크 유리병/나무 머그잔, 주사위=점 눈금만(숫자·글자 없음).
   - 배경은 **100% pure solid white `#FFFFFF` background** 바탕 + 필요 시 캐릭터 발밑의 자연스러운 미니멀 바닥/소품만 배치하세요.

6. **원본 제목 100% 유지 (`source_title`) & 선택적 `item_tooltip`**:
   - `source_title`은 제공된 원본 개념글 제목(`post.title`)을 토씨 하나 바꾸지 말고 그대로 기입하세요.
   - 핵심 와우 아이템이 등장하는 컷에만 선택적으로 `item_tooltip`을 붙이세요(유저 닉네임·길드명 금지, 포에버 커스텀 스탯 우선).
"""


def build_writer_prompt(post: GalleryPost, episode_number: int) -> str:
    """Assemble a concise, high-signal prompt for classic 4~8 cut script generation."""
    cast_bible = format_cast_bible_for_writer()
    comments_block = (
        "\n".join(f"- {c}" for c in post.comments[:10])
        if post.comments
        else "(별도 댓글 없음 — 본문 상황과 반전을 명확하게 살리세요)"
    )
    context_text = "\n".join(
        [post.title or "", post.body or "", *post.comments[:10]]
    )
    lore_guidance = build_wow_lore_guidance(context_text)

    return (
        f"{WRITER_SYSTEM_RULES}\n\n"
        f"{lore_guidance}\n\n"
        f"{cast_bible}\n\n"
        f"=== 각색 대상 포에버갤 개념글 ===\n"
        f"- 예정 화수: EP.{episode_number} | 게시글 번호: #{post.post_no}\n"
        f"- 원문 URL: {post.url}\n"
        f"- 원문 제목 (100% 그대로 유지): {post.title.strip()}\n"
        f"- 추천: {post.recommends} | 댓글: {post.comments_count}\n"
        f"- 본문:\n{post.body or '(본문 텍스트 없음 — 제목의 상황을 념글 미독자도 이해하게 현장극으로 풀어내세요)'}\n\n"
        f"- 주요 댓글 (메타 해설 금지, 웃긴 맥락만 대사·상황에 자연스럽게 흡수):\n{comments_block}\n\n"
        f"위 JSON 스키마(`EpisodeScript`)에 맞춰 출력하세요. "
        f"`episode_number`={episode_number}, `source_post_no`=\"{post.post_no}\", "
        f"`source_title`={json.dumps(post.title.strip(), ensure_ascii=False)}, "
        f"`source_url`=\"{post.url}\"."
    )


V4_WRITER_SYSTEM_RULES = """당신은 디시인사이드 '와우 포에버 마이너 갤러리(wowforever)' 개념글을 **V4 5막 가변 레이아웃(5 Acts · 10~14컷)** 날렵한 3~3.5등신 개그 웹툰(《와우 포에버 슬롭툰》) 대본으로 각색하는 시나리오 작가입니다.

[V4 5막 핵심 규칙]
1. **념글을 안 읽고도 100% 이해되는 5막 완결 서사 (`layout_mode="v4_five_act"`)**:
   - 독자는 원본 개념글을 읽지 않았다고 가정하고, 5개 막(`act_number`: 1~5, 총 **10~14컷**) 안에 **1막(장소·파티·룰 설정) → 2막(사건 발단) → 3막(갈등 확산) → 4막(절정 + 무언 충격 정지 컷 `wordless=True`) → 5막(여파·펀치라인)**이 물 흐르듯 이해되게 쓰세요.
   - 원글에 없는 억지 전투 씬 끼워팔기, 메타 댓글 컷, 타 커뮤니티(인벤 등) 언급을 금지합니다.

2. **6종 가변 레이아웃(`layout_id`) 조합**:
   - 각 막의 `cuts` 개수는 선택한 `layout_id` 패널 수와 정확히 일치해야 합니다(`open_top_split_bottom` 3컷, `split_top_wide_bottom` 3컷, `diagonal_tempo_2cut` 2컷, `impact_freeze_2cut` 2컷, `wide_reaction_wide` 3컷, `four_beat_gag` 4컷).
   - 인접 막에 동일 `layout_id` 연속 사용 금지, 5막 전체에서 **최소 3종 이상** 조합. 각 컷은 `aspect_ratio="auto"`, `layout_slot="panel"`.

3. **캐스트 집중 · 인접 컷 인물 연속성 · 무언 정지 컷**:
   - 각 컷 `characters`는 9인 중 **1~2명**, 전체 주연은 **2~5명** 이내.
   - **인접 컷 인물 연속성 절대 엄수**: 직전 컷에서 대화·대립한 상대가 바로 다음 컷에 바뀌지 않게 유지하고, 배경 엑스트라에 주연 복제 인물을 넣지 마세요.
   - 최소 1컷(권장 4막 `impact_freeze_2cut` 2번 패널)은 `wordless=True`, `speaker=null`, `dialogue=null`.

4. **자연스러운 구어체 대사 & 100% 익명화**:
   - 고정 유행어·애교 어미(`옴뇸뇸~`, `으, 으엣?!`, `후훗…`, `~해야징~♪`, 문장 끝 `~♡` 도배) 기계 복붙, 욕설, AI 설명충 존댓말, 현실 현대어(`119`, `카톡`, `편의점`, `택시`) 금지.
   - 념글 미독자도 즉시 이해할 핵심 맥락을 1~2줄(좁은 410px 컷은 줄당 10~12자, 와이드 컷은 12~15자, 3줄은 핵심 컷 1~2개 이하) 자연스러운 구어체로 담고, 1말풍선 1화자(`(도적: ...)` 금지) 및 100% 익명화(직업 호칭만)를 지키세요.

5. **간결한 영문 시각 연출 (`visual_prompt`, 2~4문장) & 배경 리듬**:
   - 의상 200단어·가드레일 복붙 대신 **3~3.5등신 날렵한 한국 개그 웹툰** 기준으로 **카메라 앵글(OTS, 로우앵글, 하이앵글, 클로즈업, 더치 틸트, 측면, 뒷모습) + 행동·표정 + 핵심 소품**만 2~4문장 영문으로 적으세요.
   - Clean Hand Rule(전리품·방패·주사위·귀환석·물약병을 들 때 기본 무기 수납), 탱커 방패, 링메일 사슬 갑옷, 판타지 코르크 유리병/나무잔, 점 눈금 주사위 고증을 지키세요.
   - 페이지 외곽 여백·거터는 항상 순백 `#FFFFFF` 유지.

6. **원본 제목 원문 유지 (`source_title`) & 선택적 `item_tooltip`**:
   - `source_title`은 `post.title` 원문을 그대로 쓰고, 핵심 와우 아이템 컷에만 선택적으로 `item_tooltip`을 붙이세요.
"""


def _format_v4_layouts_reference() -> str:
    lines = ["=== V4 가변 페이지 레이아웃 6종 (900x1350) ==="]
    for layout_id, spec in PAGE_LAYOUTS.items():
        slot_summary = ", ".join(
            f"P{s.slot_index}({'narrow' if s.is_narrow else 'wide'}, {s.border_style})"
            for s in spec.slots
        )
        lines.append(f"- `{layout_id}` ({spec.panel_count}컷): {slot_summary}")
    return "\n".join(lines)


def build_v4_writer_prompt(
    post: GalleryPost,
    episode_number: int,
    *,
    background_style: BackgroundStyle = "clean_white",
) -> str:
    """Assemble a concise V4 5-act variable-layout structured prompt."""
    cast_bible = format_cast_bible_for_writer()
    layouts_ref = _format_v4_layouts_reference()
    comments_block = (
        "\n".join(f"- {c}" for c in post.comments[:12])
        if post.comments
        else "(별도 댓글 없음 — 본문 사건의 맥락과 반전을 5막으로 명확히 살리세요)"
    )
    context_text = "\n".join(
        [post.title or "", post.body or "", *post.comments[:12]]
    )
    lore_guidance = build_wow_lore_guidance(context_text)

    if background_style == "selective_mix":
        bg_directive = (
            "이번 화 `background_style`은 `\"selective_mix\"`입니다. 전체 10~14컷 중 40~60% 핵심 현장 컷은 "
            "`full_bleed_bg=true`(전면 풀-블리드 박스), 나머지 40~60% 리액션 컷은 `full_bleed_bg=false`"
            "(순백 `#FFFFFF`, 반쪽 비네트 금지)로 배합하세요."
        )
    elif background_style == "full_bleed":
        bg_directive = (
            "이번 화 `background_style`은 `\"full_bleed\"`입니다. 모든 컷에 `full_bleed_bg=true`를 설정하고 "
            "각 박스를 전면 컬러 배경(말풍선 자리는 트인 배경)으로 채우세요."
        )
    else:
        bg_directive = (
            "이번 화 `background_style`은 `\"clean_white\"`입니다. 1막 도입 등 장소 설정 1~2컷만 "
            "`full_bleed_bg=true`(와우 지역 풀배경 박스)로 쓰고, 나머지 컷은 `full_bleed_bg=false`로 "
            "순백 `#FFFFFF` 배경(필요 시 하단 자연 바닥·소품 터치, 공중 부유 섬·반쪽 비네트 금지)으로 깔끔히 연출하세요."
        )

    return (
        f"{V4_WRITER_SYSTEM_RULES}\n\n"
        f"{layouts_ref}\n\n"
        f"{lore_guidance}\n\n"
        f"{cast_bible}\n\n"
        f"=== 각색 대상 포에버갤 개념글 (V4 5막 10~14컷) ===\n"
        f"- 예정 화수: EP.{episode_number} | 게시글 번호: #{post.post_no}\n"
        f"- 원문 URL: {post.url}\n"
        f"- 원문 제목 (100% 그대로 유지): {post.title.strip()}\n"
        f"- 추천: {post.recommends} | 댓글: {post.comments_count}\n"
        f"- 본문:\n{post.body or '(본문 텍스트 없음 — 제목의 사건을 념글 미독자도 이해하게 5막으로 풀어내세요)'}\n\n"
        f"- 주요 댓글 (메타 해설 금지, 웃긴 맥락만 대사·상황에 자연스럽게 흡수):\n{comments_block}\n\n"
        f"[배경 모드] {bg_directive}\n\n"
        f"위 JSON 스키마(`EpisodeScript`)에 맞춰 출력하세요. "
        f"`layout_mode`=\"v4_five_act\", `background_style`=\"{background_style}\", "
        f"`episode_number`={episode_number}, `source_post_no`=\"{post.post_no}\", "
        f"`source_title`={json.dumps(post.title.strip(), ensure_ascii=False)}, "
        f"`source_url`=\"{post.url}\"."
    )


# ---------------------------------------------------------------------------
# Script Quality Auditor (catches structural, lore, and anonymity flaws)
# ---------------------------------------------------------------------------

_PAREN_DUAL_SPEAKER_RE = re.compile(
    r"[\(\[（]\s*([가-힣A-Za-z_]{1,12})\s*:\s*([^)\]）]{2,})[\)\]）]"
)
_LINE_SPEAKER_PREFIX_RE = re.compile(r"^\s*([가-힣]{1,6})\s*:\s*\S+")
_GUILD_TAG_RE = re.compile(r"<[가-힣A-Za-z0-9_ ]{2,20}>")
_EXPLICIT_ID_LEAK_RE = re.compile(r"(?:길드명|닉네임|아이디)\s*[:=]\s*\S+")
_HEARTH_HOME_CUES: tuple[str, ...] = (
    "귀환석",
    "귀환지",
    "귀환",
    "여관",
    "내 집",
    "본진",
    "고향",
    "시작 마을",
)
_TANK_ROLE_CUES: tuple[str, ...] = ("전탱", "방전", "보기", "탱커", "탱킹", "protection tank", "tanking")
_SHIELD_CUES: tuple[str, ...] = ("shield", "buckler", "bulwark", "방패")
_TWO_HAND_HOLD_RE = re.compile(
    r"\b(?:holding|wielding|swinging|raising|brandishing|carrying)\b[^.,;]{0,45}"
    r"\b(?:two-handed|2h|greataxe|greatsword|battle\s*axe|warhammer)\b",
    re.IGNORECASE,
)
_VISUAL_TRAP_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\b(?:juice\s*(?:box|carton)|tetra\s*pak|plastic\s*straw|soda\s*can)\b", "modern drink packaging"),
    (r"\b(?:prison\s*chains?|iron\s*shackles?|handcuffs?)\b", "literal prison chains"),
)
_CAMERA_ANGLE_TAGS: tuple[tuple[str, str], ...] = (
    ("over_the_shoulder", r"\b(?:over[- ]the[- ]shoulder|foreground\s+shoulder|back\s+of\s+(?:her|the)\s+head|foreground\s+back)\b"),
    ("low_angle", r"\b(?:low[- ]angle|worm'?s[- ]eye|looking\s+up\s+at|looming\s+above)\b"),
    ("high_angle", r"\b(?:high[- ]angle|bird'?s[- ]eye|top[- ]down|looking\s+down\s+at)\b"),
    ("dutch_tilt", r"\b(?:dutch[- ]?(?:tilt|angle)|tilted\s+(?:camera|angle|frame)|diagonal\s+(?:angle|camera|composition))\b"),
    ("fisheye_extreme_cu", r"\b(?:fisheye|forced[- ]perspective|extreme\s+(?:face\s+)?close[- ]up|ultra[- ]close[- ]up)\b"),
    ("side_profile", r"\b(?:side[- ]profile|profile\s+view|90[- ]degree|side\s+view|chasing\s+across)\b"),
    ("back_view", r"\b(?:back[- ]view|seen\s+from\s+behind|walking\s+away|turning\s+her\s+back|looking\s+back\s+over\s+her\s+shoulder)\b"),
    ("action_motion", r"\b(?:dashing|sprinting|running\s+away|leaping|diving|lunging|crouching|sneaking|tiptoeing|sprawled|collapsed|faceplant|kneeling|clinging|hanging|tossing|slamming|swinging|flinging|charging|sliding|tumbling|falling|flying\s+back|ghost\s+floating|vortex)\b"),
)


def _is_negated_match(text: str, match_start: int) -> bool:
    """Return True if a matched phrase in `text` is explicitly negated (e.g., 'NOT a juice box')."""
    prefix = text[max(0, match_start - 36) : match_start].lower().strip()
    return bool(
        re.search(
            r"\b(?:no|not|never|zero|without|avoid|instead\s+of)"
            r"(?:\s+(?:a|an|any|literal|modern|real|paper|metal))*$",
            prefix,
        )
    )


def audit_script_quality(
    script: EpisodeScript,
    *,
    forbidden_names: Sequence[str] | None = None,
    strict_cinematic: bool = False,
) -> dict[str, Any]:
    """Audit an `EpisodeScript` (classic 4~8 cut OR V4 5-act) against all WoW Forever rules."""
    errors: list[str] = []
    warnings: list[str] = []

    is_v4 = (script.layout_mode == "v4_five_act") or (script.acts is not None)
    act_cuts: list[ComicCut] = [c for act in (script.acts or []) for c in act.cuts]
    cuts: list[ComicCut] = list(script.cuts) if script.cuts else list(act_cuts)
    cut_count = len(cuts)

    acts_ok = True
    layout_diversity_ok = True

    if is_v4:
        cut_count_ok = 10 <= cut_count <= 14
        if not cut_count_ok:
            errors.append(f"V4 cut count must be 10–14, got {cut_count}.")

        if script.acts is None or len(script.acts) != 5:
            acts_ok = False
            layout_diversity_ok = False
            actual_acts = 0 if script.acts is None else len(script.acts)
            errors.append(f"V4 script must have exactly 5 acts, got {actual_acts}.")
        else:
            act_nums = [a.act_number for a in script.acts]
            if act_nums != [1, 2, 3, 4, 5]:
                acts_ok = False
                errors.append(f"V4 act_numbers must be [1, 2, 3, 4, 5], got {act_nums}.")
            for act in script.acts:
                try:
                    spec = get_page_layout(act.layout_id)
                    if len(act.cuts) != spec.panel_count:
                        acts_ok = False
                        errors.append(
                            f"Act {act.act_number} layout '{act.layout_id}' expects {spec.panel_count} cuts, got {len(act.cuts)}."
                        )
                except ValueError as exc:
                    acts_ok = False
                    layout_diversity_ok = False
                    errors.append(str(exc))

            layout_ids = [act.layout_id for act in script.acts]
            for idx in range(len(layout_ids) - 1):
                if layout_ids[idx] == layout_ids[idx + 1]:
                    layout_diversity_ok = False
                    errors.append(
                        f"Duplicate consecutive layout_id '{layout_ids[idx]}' on Act {idx + 1} and Act {idx + 2}."
                    )
            distinct_count = len(set(layout_ids))
            if distinct_count < 3:
                layout_diversity_ok = False
                errors.append(
                    f"Insufficient V4 layout diversity: {distinct_count} distinct layout(s) across 5 acts (need >= 3)."
                )
    else:
        cut_count_ok = 4 <= cut_count <= 8
        if not cut_count_ok:
            errors.append(f"Cut count must be 4–8, got {cut_count}.")

    wordless_cuts = [cut.cut_index for cut in cuts if cut.wordless]
    act_has_wordless = (not act_cuts) or any(cut.wordless for cut in act_cuts)
    wordless_cut_ok = (len(wordless_cuts) >= 1) and act_has_wordless
    if not wordless_cut_ok:
        errors.append("Missing mandatory wordless freeze-frame cut (wordless=True).")

    unique_cast: list[str] = []
    seen_cast: set[str] = set()
    for cut in cuts:
        for raw_name in cut.characters:
            canon = canonical_cast_name(raw_name)
            if canon not in seen_cast:
                seen_cast.add(canon)
                unique_cast.append(canon)

    unique_cast_count = len(unique_cast)
    max_unique_cast = 5 if is_v4 else 4
    cast_focus_ok = unique_cast_count <= max_unique_cast
    if unique_cast_count > max_unique_cast:
        errors.append(
            f"Cast sprawl: {unique_cast_count} unique cast members exceeds max {max_unique_cast} ({', '.join(unique_cast)})."
        )
    elif unique_cast_count < 2:
        warnings.append(
            f"Only {unique_cast_count} unique cast member in episode; 2–{max_unique_cast} core participants recommended."
        )

    no_dual_speaker_hack = True
    no_modern_slang = True
    anonymity_ok = True
    faction_zone_ok = True
    tank_shield_ok = True
    no_forbidden_community = True
    visual_prompt_clean = True

    cleaned_forbidden = [
        n.strip() for n in (forbidden_names or ()) if n and len(n.strip()) >= 2
    ]

    def _check_text_anonymity_and_community(text: str, location: str) -> None:
        nonlocal anonymity_ok, no_forbidden_community
        if not text:
            return
        lower = text.lower()
        for bad_name in cleaned_forbidden:
            if bad_name.lower() in lower:
                anonymity_ok = False
                errors.append(f"Anonymity leak in {location}: forbidden name '{bad_name}' detected.")
        if "인벤" in text or re.search(r"\binven\b", lower):
            no_forbidden_community = False
            errors.append(f"Forbidden community mention ('인벤') in {location}.")

    _check_text_anonymity_and_community(script.subtitle, "subtitle")
    if _GUILD_TAG_RE.search(script.subtitle) or _EXPLICIT_ID_LEAK_RE.search(script.subtitle):
        anonymity_ok = False
        errors.append(f"Possible guild tag / ID leak in subtitle: '{script.subtitle}'.")
    for label, replacement in find_modern_slang_violations(script.subtitle):
        no_modern_slang = False
        errors.append(
            f"Modern real-world phrasing '{label}' in subtitle (use WoW phrasing like '{replacement}')."
        )

    if script.acts:
        for act in script.acts:
            act_loc = f"act #{act.act_number} title"
            _check_text_anonymity_and_community(act.act_title, act_loc)
            if _GUILD_TAG_RE.search(act.act_title) or _EXPLICIT_ID_LEAK_RE.search(act.act_title):
                anonymity_ok = False
                errors.append(f"Possible guild tag / ID leak in {act_loc}: '{act.act_title}'.")
            for label, replacement in find_modern_slang_violations(act.act_title):
                no_modern_slang = False
                errors.append(
                    f"Modern real-world phrasing '{label}' in {act_loc} (use WoW phrasing like '{replacement}')."
                )

    seen_cut_obj_ids = {id(c) for c in cuts}
    cuts_to_inspect: list[ComicCut] = list(cuts)
    for c in act_cuts:
        if id(c) not in seen_cut_obj_ids:
            cuts_to_inspect.append(c)

    for cut in cuts_to_inspect:
        loc = f"cut #{cut.cut_index}"
        dlg = (cut.dialogue or "").strip()
        vp = (cut.visual_prompt or "").strip()

        if not cut.wordless:
            if not dlg:
                warnings.append(f"{loc} is non-wordless but has empty dialogue.")
            if not cut.speaker:
                warnings.append(f"{loc} is non-wordless but has no speaker.")
            else:
                canon_speaker = canonical_cast_name(cut.speaker)
                canon_chars = [canonical_cast_name(c) for c in cut.characters]
                if canon_speaker not in canon_chars:
                    warnings.append(
                        f"{loc} speaker '{canon_speaker}' is not in cut.characters {canon_chars}."
                    )

        if dlg:
            m_paren = _PAREN_DUAL_SPEAKER_RE.search(dlg)
            if m_paren:
                no_dual_speaker_hack = False
                errors.append(
                    f"Parenthetical dual-speaker hack in {loc}: '{m_paren.group(0)}' — use 1 speaker per bubble."
                )
            else:
                labeled_prefixes: list[str] = []
                speaker_member = resolve_cast_member(cut.speaker) if cut.speaker else None
                for ln in dlg.splitlines():
                    m_ln = _LINE_SPEAKER_PREFIX_RE.match(ln)
                    if m_ln:
                        prefix = m_ln.group(1)
                        pref_member = resolve_cast_member(prefix)
                        if pref_member is not None:
                            labeled_prefixes.append(pref_member.id)
                            if speaker_member is not None and pref_member.id != speaker_member.id:
                                no_dual_speaker_hack = False
                                errors.append(
                                    f"Dual-speaker prefix '{prefix}:' in {loc} conflicts with speaker '{cut.speaker}'."
                                )
                if len(set(labeled_prefixes)) >= 2:
                    no_dual_speaker_hack = False
                    errors.append(f"Multiple labeled speakers stuffed into one bubble in {loc}.")

            for label, replacement in find_modern_slang_violations(dlg):
                no_modern_slang = False
                errors.append(
                    f"Modern real-world phrasing '{label}' in {loc} dialogue "
                    f"(use WoW phrasing like '{replacement}')."
                )

            _check_text_anonymity_and_community(dlg, f"{loc} dialogue")
            if _GUILD_TAG_RE.search(dlg) or _EXPLICIT_ID_LEAK_RE.search(dlg):
                anonymity_ok = False
                errors.append(f"Possible guild tag / ID leak in {loc} dialogue.")

            speaker_ref = cut.speaker or (cut.characters[0] if cut.characters else "")
            speaker_member = resolve_cast_member(speaker_ref)
            if speaker_member is not None and any(cue in dlg for cue in _HEARTH_HOME_CUES):
                dlg_lower = dlg.lower()
                if speaker_member.faction == "Horde":
                    bad_zone = next((z for z in ALLIANCE_ZONES if z.lower() in dlg_lower), None)
                    if bad_zone:
                        faction_zone_ok = False
                        errors.append(
                            f"Faction/zone mismatch in {loc}: Horde cast '{speaker_member.name}' "
                            f"claims Alliance zone '{bad_zone}' as hearthstone/home."
                        )
                elif speaker_member.faction in {"Alliance", "Neutral-Skyborne"}:
                    bad_zone = next((z for z in HORDE_ZONES if z.lower() in dlg_lower), None)
                    if bad_zone:
                        faction_zone_ok = False
                        errors.append(
                            f"Faction/zone mismatch in {loc}: {speaker_member.faction} cast "
                            f"'{speaker_member.name}' claims Horde zone '{bad_zone}' as hearthstone/home."
                        )

        _check_text_anonymity_and_community(vp, f"{loc} visual_prompt")

        for pat, desc in _VISUAL_TRAP_PATTERNS:
            for match in re.finditer(pat, vp, flags=re.IGNORECASE):
                if not _is_negated_match(vp, match.start()):
                    visual_prompt_clean = False
                    errors.append(
                        f"Visual anti-hallucination violation in {loc}: prompt requests {desc} ('{match.group(0)}')."
                    )
                    break

        resolved_cut_members = [
            m for m in (resolve_cast_member(c) for c in cut.characters) if m is not None
        ]
        has_tank_class = any(m.id in {"orc_warrior", "undead_paladin"} for m in resolved_cut_members)
        if has_tank_class:
            combined_cut_lower = f"{dlg} {vp}".lower()
            is_tanking_context = any(cue in combined_cut_lower for cue in _TANK_ROLE_CUES)
            has_shield_mention = any(cue in vp.lower() for cue in _SHIELD_CUES)
            holds_2h = bool(_TWO_HAND_HOLD_RE.search(vp))
            if is_tanking_context and holds_2h and not has_shield_mention:
                tank_shield_ok = False
                errors.append(
                    f"Tank equipment mismatch in {loc}: Warrior/Paladin tanking cut depicts holding a "
                    "two-handed weapon with NO shield — 전탱/보기 must carry a 1H weapon + shield."
                )

        if cut.item_tooltip and cut.item_tooltip.item_name:
            tip_name = cut.item_tooltip.item_name.strip()
            _check_text_anonymity_and_community(tip_name, f"{loc} item_tooltip")
            if resolve_cast_member(tip_name) is not None or tip_name.endswith(("님", "길드")):
                anonymity_ok = False
                errors.append(
                    f"Invalid item_tooltip.item_name '{tip_name}' in {loc}: tooltips are strictly for WoW items."
                )

    detected_camera_tags: set[str] = set()
    dynamic_cuts = 0
    flat_two_shot_cuts = 0
    for cut in cuts:
        vp = (cut.visual_prompt or "").strip()
        cut_tags = [
            tag for tag, pat in _CAMERA_ANGLE_TAGS if re.search(pat, vp, flags=re.IGNORECASE)
        ]
        if cut_tags:
            dynamic_cuts += 1
            detected_camera_tags.update(cut_tags)
        elif not cut.wordless and len(cut.characters) == 2:
            if re.search(r"lower[- ]left", vp, re.IGNORECASE) and re.search(
                r"lower[- ]right", vp, re.IGNORECASE
            ):
                flat_two_shot_cuts += 1

    min_dynamic = 5 if is_v4 else 3
    max_flat = 2 if is_v4 else 1
    cinematic_variety_ok = (
        len(detected_camera_tags) >= 3
        and dynamic_cuts >= min_dynamic
        and flat_two_shot_cuts <= max_flat
    )
    if strict_cinematic and not cinematic_variety_ok:
        errors.append(
            f"Cinematic variety too flat (dynamic_cuts={dynamic_cuts}/{cut_count}, "
            f"camera_tags={sorted(detected_camera_tags)}, flat_side_by_side={flat_two_shot_cuts}) — "
            "vary OTS/low-angle/high-angle/profile/back-view/slapstick action poses instead of static talking heads."
        )

    dialogue_cuts = [c for c in cuts if not c.wordless and (c.dialogue or "").strip()]
    bloated_3line_cuts: list[int] = []
    short_1line_cuts: list[int] = []
    for cut in dialogue_cuts:
        dlg = (cut.dialogue or "").strip()
        non_empty_lines = [ln.strip() for ln in dlg.splitlines() if ln.strip()]
        char_len = len(dlg.replace("\n", "").strip())
        if len(non_empty_lines) >= 3 and char_len > 38:
            bloated_3line_cuts.append(cut.cut_index)
        elif len(non_empty_lines) == 1 and char_len <= 18:
            short_1line_cuts.append(cut.cut_index)

    if is_v4 and len(dialogue_cuts) >= 4:
        bloated_ratio = len(bloated_3line_cuts) / len(dialogue_cuts)
        if bloated_ratio > 0.70:
            warnings.append(
                f"Dialogue pacing bloat in V4 script: {len(bloated_3line_cuts)}/{len(dialogue_cuts)} "
                f"dialogue cuts ({bloated_ratio:.0%}) are dense 3-line walls (>38 chars, cuts "
                f"{bloated_3line_cuts})."
            )

    checks: dict[str, bool] = {
        "cut_count_ok": cut_count_ok,
        "wordless_cut_ok": wordless_cut_ok,
        "cast_focus_ok": cast_focus_ok,
        "no_dual_speaker_hack": no_dual_speaker_hack,
        "no_modern_slang": no_modern_slang,
        "anonymity_ok": anonymity_ok,
        "faction_zone_ok": faction_zone_ok,
        "tank_shield_ok": tank_shield_ok,
        "no_forbidden_community": no_forbidden_community,
        "visual_prompt_clean": visual_prompt_clean,
    }
    if is_v4:
        checks["acts_ok"] = acts_ok
        checks["layout_diversity_ok"] = layout_diversity_ok
    if strict_cinematic:
        checks["cinematic_variety_ok"] = cinematic_variety_ok

    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "layout_mode": script.layout_mode,
        "cut_count": cut_count,
        "wordless_cuts": wordless_cuts,
        "unique_cast": unique_cast,
        "unique_cast_count": unique_cast_count,
        "cinematic_metrics": {
            "dynamic_cuts": dynamic_cuts,
            "camera_tags": sorted(detected_camera_tags),
            "flat_two_shot_cuts": flat_two_shot_cuts,
        },
        "dialogue_pacing": {
            "dialogue_cut_count": len(dialogue_cuts),
            "bloated_3line_cuts": bloated_3line_cuts,
            "short_1line_cuts": short_1line_cuts,
        },
        "checks": checks,
    }


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


def _normalize_cut(
    cut: ComicCut,
    *,
    cut_index: int,
    act_number: int | None = None,
    panel_index: int | None = None,
) -> ComicCut:
    norm_chars = [canonical_cast_name(c) for c in cut.characters]
    norm_speaker = (
        None
        if cut.wordless or not cut.speaker
        else canonical_cast_name(cut.speaker)
    )
    updates: dict[str, Any] = {
        "cut_index": cut_index,
        "characters": norm_chars,
        "speaker": norm_speaker,
        "dialogue": None if cut.wordless else cut.dialogue,
    }
    if act_number is not None:
        updates["act_number"] = act_number
    if panel_index is not None:
        updates["panel_index"] = panel_index
    return cut.model_copy(update=updates)


def _normalize_script(
    script: EpisodeScript,
    post: GalleryPost,
    episode_number: int,
) -> EpisodeScript:
    """Ensure canonical cast names and exact verbatim source metadata on classic or V4 scripts."""
    verbatim_title = post.title.strip() or script.source_title.strip()

    if script.acts is not None:
        normalized_acts: list[ActPage] = []
        flattened_cuts: list[ComicCut] = []
        seq = 1
        for act in script.acts:
            act_norm_cuts: list[ComicCut] = []
            for p_idx, cut in enumerate(act.cuts, start=1):
                norm_cut = _normalize_cut(
                    cut,
                    cut_index=seq,
                    act_number=act.act_number,
                    panel_index=p_idx,
                )
                act_norm_cuts.append(norm_cut)
                flattened_cuts.append(norm_cut)
                seq += 1
            normalized_acts.append(act.model_copy(update={"cuts": act_norm_cuts}))

        return script.model_copy(
            update={
                "episode_number": episode_number,
                "source_post_no": str(post.post_no),
                "source_title": verbatim_title,
                "source_url": post.url,
                "layout_mode": "v4_five_act",
                "acts": normalized_acts,
                "cuts": flattened_cuts,
            }
        )

    normalized_cuts: list[ComicCut] = [
        _normalize_cut(cut, cut_index=idx) for idx, cut in enumerate(script.cuts, start=1)
    ]
    return script.model_copy(
        update={
            "episode_number": episode_number,
            "source_post_no": str(post.post_no),
            "source_title": verbatim_title,
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
    """Generate and validate a 4~8 cut `EpisodeScript` via Gemini Interactions API."""
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
    if raw_json.startswith("```"):
        lines = raw_json.splitlines()
        raw_json = "\n".join(
            line for line in lines if not line.strip().startswith("```")
        ).strip()

    script = EpisodeScript.model_validate_json(raw_json)
    return _normalize_script(script, post=post, episode_number=episode_number)


def generate_v4_episode_script(
    post: GalleryPost,
    episode_number: int,
    *,
    client: Any | None = None,
    settings: Settings | None = None,
    model: str | None = None,
    background_style: BackgroundStyle | None = None,
) -> EpisodeScript:
    """Generate and validate a V4 5-act (10~14 cut) `EpisodeScript` via Gemini Interactions API."""
    cfg = settings or load_settings()
    target_model = model or cfg.text_model or DEFAULT_TEXT_MODEL

    if client is None:
        if not cfg.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Configure GEMINI_API_KEY in .env or environment, "
                "or run with --dry-run."
            )
        client = genai.Client(api_key=cfg.gemini_api_key)

    prompt = build_v4_writer_prompt(
        post,
        episode_number=episode_number,
        background_style=background_style or "clean_white",
    )
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
    if raw_json.startswith("```"):
        lines = raw_json.splitlines()
        raw_json = "\n".join(
            line for line in lines if not line.strip().startswith("```")
        ).strip()

    script = EpisodeScript.model_validate_json(raw_json)
    if script.layout_mode != "v4_five_act" or not script.acts:
        raise ValueError(
            "Gemini V4 script response did not produce a valid 5-act `v4_five_act` EpisodeScript."
        )
    normalized = _normalize_script(script, post=post, episode_number=episode_number)
    if background_style is not None and normalized.background_style != background_style:
        normalized = normalized.model_copy(update={"background_style": background_style})
    return normalized


def build_dry_run_script(post: GalleryPost, episode_number: int) -> EpisodeScript:
    """Build a deterministic offline 4-cut self-contained script for `--dry-run` previews."""
    verbatim_title = post.title.strip()
    dialogue_hook = verbatim_title or f"개념글 #{post.post_no}"
    snippet = (post.body.strip().splitlines()[0][:24] + "...") if post.body.strip() else dialogue_hook[:24]

    cuts = [
        ComicCut(
            cut_index=1,
            aspect_ratio="4:3",
            layout_slot="top",
            characters=["나이트엘프 사제", "오크 전사"],
            speaker="나이트엘프 사제",
            dialogue=f"던전 주특입 파티잖아요.\n'{dialogue_hook[:16]}' 실화예요?",
            wordless=False,
            visual_prompt=(
                "Over-the-shoulder shot in sleek 3-to-3.5 head webtoon style. Left: exhausted Night Elf Priest "
                "with tired dark circles pleading with clasped hands (staff on back). Foreground right: back "
                "shoulder of Orc Warrior grinning confidently with steel shield and 1H sword. Pure solid white "
                "#FFFFFF background."
            ),
            tail_target="left",
        ),
        ComicCut(
            cut_index=2,
            aspect_ratio="16:9",
            layout_slot="bottom",
            characters=["오크 전사"],
            speaker="오크 전사",
            dialogue=f"당연하지! {snippet}\n던전은 원래 선착순이야!",
            wordless=False,
            visual_prompt=(
                "Low-angle shot on the right half of the wide 16:9 frame: Orc Warrior tank raising her steel "
                "kite shield and 1H sword proudly with a confident grin. Generous empty pure solid white "
                "#FFFFFF space on left for speech bubble."
            ),
            tail_target="right",
        ),
        ComicCut(
            cut_index=3,
            aspect_ratio="4:3",
            layout_slot="top",
            characters=["노움 도적", "스카이본 마법사"],
            speaker="노움 도적",
            dialogue="잠깐, 방금 파티창에\n전탱·힐러 다 보고 있었는데?",
            wordless=False,
            visual_prompt=(
                "Side-profile comedic shot: Left, Gnome Rogue leaning in with a teasing smirk pointing thumb "
                "back (daggers sheathed). Right, Skyborne Mage glancing sideways in disbelief with hands empty "
                "(crystal staff on back). Pure solid white #FFFFFF background."
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
                "Centered Dutch-tilt close-up freeze-frame of Skyborne Mage with star-pupils switched off "
                "into blank white shock eyes, forehead gloom shadow, jaw dropped wide, and a small cold sweat "
                "drop. Pure solid white #FFFFFF background."
            ),
            tail_target="center",
        ),
    ]

    return EpisodeScript(
        episode_number=episode_number,
        source_post_no=str(post.post_no),
        source_title=verbatim_title or dialogue_hook,
        source_url=post.url,
        subtitle=f"포에버갤 #{post.post_no} 드라이런 상황극 프리뷰",
        cuts=cuts,
    )


def build_dry_run_v4_script(
    post: GalleryPost,
    episode_number: int,
    *,
    background_style: BackgroundStyle = "clean_white",
) -> EpisodeScript:
    """Build a deterministic offline V4 5-act (13-cut, 5 distinct layouts) self-contained script."""
    verbatim_title = post.title.strip()
    dialogue_hook = verbatim_title or f"개념글 #{post.post_no}"
    snippet = (
        (post.body.strip().splitlines()[0][:14] + "…")
        if post.body.strip()
        else dialogue_hook[:14]
    )

    acts = [
        ActPage(
            act_number=1,
            act_title="발단 — 던전 앞 주특입 파티 출발",
            layout_id="open_top_split_bottom",
            cuts=[
                ComicCut(
                    cut_index=1,
                    aspect_ratio="auto",
                    layout_slot="panel",
                    act_number=1,
                    panel_index=1,
                    characters=["나이트엘프 사제", "오크 전사"],
                    speaker="나이트엘프 사제",
                    dialogue=f"'{dialogue_hook[:14]}' 파티 맞죠?\n주특입 룰 지키고 가요.",
                    wordless=False,
                    full_bleed_bg=True,
                    visual_prompt=(
                        "Over-the-shoulder establishing shot at Scarlet Monastery stone archway with crimson "
                        "banners and open upper sky: foreground shoulder of Orc Warrior tank (steel kite shield "
                        "and 1H sword), midground Night Elf Priest confirming dungeon rules politely (staff on back)."
                    ),
                    tail_target="left",
                ),
                ComicCut(
                    cut_index=2,
                    aspect_ratio="auto",
                    layout_slot="panel",
                    act_number=1,
                    panel_index=2,
                    characters=["오크 전사"],
                    speaker="오크 전사",
                    dialogue="걱정 마, 내가 앞장선다!",
                    wordless=False,
                    visual_prompt=(
                        "Low-angle heroic brag looking up at Orc Warrior tank raising her sturdy steel kite "
                        "shield and 1H sword with a boisterous confident grin. Pure solid white #FFFFFF background."
                    ),
                    tail_target="center",
                ),
                ComicCut(
                    cut_index=3,
                    aspect_ratio="auto",
                    layout_slot="panel",
                    act_number=1,
                    panel_index=3,
                    characters=["노움 도적"],
                    speaker="노움 도적",
                    dialogue="어차피 터지면 내가 제일 먼저 짼다.",
                    wordless=False,
                    visual_prompt=(
                        "Side-profile sneaky crouch beside a wooden dungeon crate: Gnome Rogue nudging her "
                        "goggles up with a sly smirk (daggers sheathed at belt). Pure solid white #FFFFFF background."
                    ),
                    tail_target="center",
                ),
            ],
        ),
        ActPage(
            act_number=2,
            act_title="전개 — 풀링과 동시에 터진 변수",
            layout_id="diagonal_tempo_2cut",
            cuts=[
                ComicCut(
                    cut_index=4,
                    aspect_ratio="auto",
                    layout_slot="panel",
                    act_number=2,
                    panel_index=1,
                    characters=["오크 전사", "노움 도적"],
                    speaker="노움 도적",
                    dialogue=f"어어 {snippet}\n일단 소멸부터 탈게!",
                    wordless=False,
                    visual_prompt=(
                        "Dutch-tilt slapstick chase on dungeon stone tiles: Orc Warrior tank (steel shield and "
                        "1H sword) skidding backward against rushing mob silhouettes while Gnome Rogue darts "
                        "sideways in a swirling Vanish smoke puff. Pure solid white #FFFFFF background."
                    ),
                    tail_target="right",
                ),
                ComicCut(
                    cut_index=5,
                    aspect_ratio="auto",
                    layout_slot="panel",
                    act_number=2,
                    panel_index=2,
                    characters=["스카이본 마법사", "나이트엘프 사제"],
                    speaker="스카이본 마법사",
                    dialogue="잠깐, 방금 지능 지팡이에\n입찰 누른 거 누구야?",
                    wordless=False,
                    visual_prompt=(
                        "Fisheye forced-perspective reaction shot: Left, Skyborne Mage lunging toward camera "
                        "pointing accusingly with a cold deadpan glare (crystal staff on back); Right, Night "
                        "Elf Priest behind her eyeing the loot awkwardly. Pure solid white #FFFFFF background."
                    ),
                    tail_target="left",
                ),
            ],
        ),
        ActPage(
            act_number=3,
            act_title="위기 — 파밍보다 빠른 입찰 논리",
            layout_id="split_top_wide_bottom",
            cuts=[
                ComicCut(
                    cut_index=6,
                    aspect_ratio="auto",
                    layout_slot="panel",
                    act_number=3,
                    panel_index=1,
                    characters=["나이트엘프 사제"],
                    speaker="나이트엘프 사제",
                    dialogue="저런, 힐은 없어요.",
                    wordless=False,
                    visual_prompt=(
                        "Extreme face close-up of Night Elf Priest with dark gloom shadow over her brow, "
                        "chilling pinpoint silver pupils, and a razor-calm polite smile (staff on back). "
                        "Pure solid white #FFFFFF background."
                    ),
                    tail_target="center",
                ),
                ComicCut(
                    cut_index=7,
                    aspect_ratio="auto",
                    layout_slot="panel",
                    act_number=3,
                    panel_index=2,
                    characters=["오크 전사"],
                    speaker="오크 전사",
                    dialogue="피 1%야! 힐 좀 줘!",
                    wordless=False,
                    visual_prompt=(
                        "Low-angle panic breakdown: Orc Warrior dropping to her knees clinging forward in "
                        "tears hugging her steel kite shield and 1H sword desperately. Pure solid white #FFFFFF background."
                    ),
                    tail_target="center",
                ),
                ComicCut(
                    cut_index=8,
                    aspect_ratio="auto",
                    layout_slot="panel",
                    act_number=3,
                    panel_index=3,
                    characters=["노움 도적", "스카이본 마법사"],
                    speaker="노움 도적",
                    dialogue="주사위는 공정하잖아?\n높게 나온 사람이 임자지!",
                    wordless=False,
                    visual_prompt=(
                        "Over-the-shoulder reveal past Skyborne Mage's trembling shoulder toward Gnome Rogue "
                        "leaping onto an open wooden loot chest tossing a chunky 6-sided white-and-gold loot "
                        "die with dot pips only (daggers sheathed). Pure solid white #FFFFFF background."
                    ),
                    tail_target="left",
                ),
            ],
        ),
        ActPage(
            act_number=4,
            act_title="절정 — 모두의 영혼이 멈춘 순간",
            layout_id="impact_freeze_2cut",
            cuts=[
                ComicCut(
                    cut_index=9,
                    aspect_ratio="auto",
                    layout_slot="panel",
                    act_number=4,
                    panel_index=1,
                    characters=["노움 도적", "오크 전사"],
                    speaker="노움 도적",
                    dialogue="입찰 100 떴다!\n귀환석 먼저 탈게!",
                    wordless=False,
                    visual_prompt=(
                        "Dutch-tilt mid-air leap: Gnome Rogue soaring gleefully holding a glowing cyan "
                        "spiral-rune Hearthstone (daggers sheathed) while Orc Warrior tank (steel shield and "
                        "1H sword) dives face-first trying to grab her boot. Pure solid white #FFFFFF background."
                    ),
                    tail_target="right",
                ),
                ComicCut(
                    cut_index=10,
                    aspect_ratio="auto",
                    layout_slot="panel",
                    act_number=4,
                    panel_index=2,
                    characters=["스카이본 마법사"],
                    speaker=None,
                    dialogue=None,
                    wordless=True,
                    visual_prompt=(
                        "Centered extreme close-up comedic freeze-frame of Skyborne Mage with star-pupils "
                        "switched off into blank white shock eyes, jaw dropped wide, and a tiny translucent "
                        "soul drifting out of her mouth (staff on back). Pure solid white #FFFFFF background."
                    ),
                    tail_target="center",
                ),
            ],
        ),
        ActPage(
            act_number=5,
            act_title="여파 — 무덤 이동 각",
            layout_id="wide_reaction_wide",
            cuts=[
                ComicCut(
                    cut_index=11,
                    aspect_ratio="auto",
                    layout_slot="panel",
                    act_number=5,
                    panel_index=1,
                    characters=["나이트엘프 사제"],
                    speaker="나이트엘프 사제",
                    dialogue="영혼의 치유사 면담 각이네요.",
                    wordless=False,
                    visual_prompt=(
                        "High-angle bird's-eye shot looking down at Night Elf Priest kneeling beside an empty "
                        "corked glass mana flask with a calm resigned smile (staff resting beside her). "
                        "Pure solid white #FFFFFF background."
                    ),
                    tail_target="left",
                ),
                ComicCut(
                    cut_index=12,
                    aspect_ratio="auto",
                    layout_slot="panel",
                    act_number=5,
                    panel_index=2,
                    characters=["노움 도적"],
                    speaker="노움 도적",
                    dialogue="여관으로 먼저 갈게!",
                    wordless=False,
                    visual_prompt=(
                        "Back-view sprint action shot of Gnome Rogue diving into a bright swirling cyan "
                        "Hearthstone vortex while glancing back over her shoulder with a cheeky wave "
                        "(daggers sheathed). Pure solid white #FFFFFF background."
                    ),
                    tail_target="right",
                ),
                ComicCut(
                    cut_index=13,
                    aspect_ratio="auto",
                    layout_slot="panel",
                    act_number=5,
                    panel_index=3,
                    characters=["오크 전사", "스카이본 마법사"],
                    speaker="오크 전사",
                    dialogue="다음엔 파티찾기 포에버에서\n주사위 룰부터 못 박자…",
                    wordless=False,
                    visual_prompt=(
                        "Side-profile exhausted aftermath on dungeon stone floor: Orc Warrior slumped against "
                        "her steel kite shield and 1H sword sighing beside Skyborne Mage fuming with comic "
                        "anger steam (crystal staff on back). Pure solid white #FFFFFF background."
                    ),
                    tail_target="left",
                ),
            ],
        ),
    ]

    selective_fb_indices: set[int] = {1, 4, 8, 9, 10, 12, 13}
    if background_style in {"full_bleed", "selective_mix"}:
        adjusted_acts: list[ActPage] = []
        for act in acts:
            adjusted_cuts: list[ComicCut] = []
            for cut in act.cuts:
                use_fb = (
                    True
                    if background_style == "full_bleed"
                    else (cut.cut_index in selective_fb_indices)
                )
                vp = cut.visual_prompt
                if use_fb:
                    vp = vp.replace(
                        "Pure solid white #FFFFFF background.",
                        "Full-bleed stone dungeon background with open upper cavern ceiling for speech bubble.",
                    )
                adjusted_cuts.append(
                    cut.model_copy(update={"full_bleed_bg": use_fb, "visual_prompt": vp})
                )
            adjusted_acts.append(act.model_copy(update={"cuts": adjusted_cuts}))
        acts = adjusted_acts

    return EpisodeScript(
        episode_number=episode_number,
        source_post_no=str(post.post_no),
        source_title=verbatim_title or dialogue_hook,
        source_url=post.url,
        subtitle=f"포에버갤 #{post.post_no} V4 5막 드라이런 프리뷰",
        layout_mode="v4_five_act",
        background_style=background_style,
        acts=acts,
    )


def script_to_pretty_json(script: EpisodeScript) -> str:
    """Serialize an `EpisodeScript` as UTF-8 readable JSON."""
    return json.dumps(script.model_dump(mode="json"), ensure_ascii=False, indent=2)
