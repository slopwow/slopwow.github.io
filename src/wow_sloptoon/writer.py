"""Episode script writer powered by Google GenAI Interactions API (`gemini-4-hydrogen`).

Route A Single Canonical Pipeline:
- 4~7 cuts (recommended 5~6 cuts) self-contained gag webtoon scripts understood 100%
  without reading the original DCInside `wowforever` post.
- Crisp 1~2 line punchy Korean WoW colloquial dialogue (16~30 chars; zero 40+ char text walls,
  zero robotic customer-service narration, zero copy-paste aegyo catchphrases).
- Unified 2-to-2.5 head cute plump Korean anime SD chibi direction across all cast, companions
  (baby bear for Dwarf Hunter, purple Voidwalker for Human Warlock), mobs, and NPCs.
- Automatic `audit_script_quality` retry gate wired directly into `generate_episode_script`.
"""

from __future__ import annotations

import json
import re
from typing import Any, Sequence

from google import genai
from pydantic import ValidationError

from wow_sloptoon.cast import (
    canonical_cast_name,
    format_cast_bible_for_writer,
    resolve_cast_member,
)
from wow_sloptoon.config import DEFAULT_TEXT_MODEL, Settings, load_settings
from wow_sloptoon.models import ComicCut, EpisodeScript, GalleryPost
from wow_sloptoon.wow_lore import (
    ALLIANCE_ZONES,
    HORDE_ZONES,
    build_wow_lore_guidance,
    find_modern_slang_violations,
)

WRITER_SYSTEM_RULES = """당신은 디시인사이드 '와우 포에버 마이너 갤러리(wowforever)' 개념글을 **5~6컷(허용 4~7컷) 2~2.5등신 동글동글 귀염뽀짝 SD 개그 웹툰(《와우 포에버 슬롭툰》)** 대본으로 각색하는 시나리오 작가입니다.

[핵심 원칙]
1. **념글을 안 읽고도 100% 이해되는 완결 서사 (최우선!)**:
   - 독자는 원본 게시글 제목·본문을 전혀 보지 않고 만화만 처음 읽는다고 가정하세요.
   - 반드시 **① 상황 설정**(어디 던전/필드인지, 어떤 파티·룰인지) → **② 사건 발단**(무슨 템·요구·행동이 터졌는지) → **③ 갈등·황당 포인트**(왜 어이없고 웃긴지 인과) → **④ 무언 대왕 클로즈업 충격 정지 컷(`wordless=True`)** → **⑤ 여파·펀치라인**이 자급자족으로 이어지게 쓰세요.
   - 원글에 없는 억지 전투 씬, 불필요한 캐릭터 끼워팔기, 메타 댓글 반응("개념글 갔네~"), 타 커뮤니티(인벤 등) 언급을 금지합니다.

2. **분량 및 2단 페이지 슬롯 (권장 5~6컷, 허용 4~7컷)**:
   - 원글 밀도에 맞춰 정확히 **4~7컷(권장 5~6컷)**으로 구성하세요.
   - 홀수 컷(1, 3, 5): `layout_slot="top"`, `aspect_ratio="4:3"` (단, 전체 컷 수가 홀수인 5/7컷일 때 마지막 컷은 단독 피날레 박스이므로 `layout_slot="bottom"`, `aspect_ratio="16:9"`).
   - 짝수 컷(2, 4, 6): `layout_slot="bottom"`, `aspect_ratio="16:9"`.

3. **말풍선 리듬 혁신 — 진짜 와우 유저 채팅 구어체 (어색한 AI 대본투·벽돌 절대 금지!)**:
   - **말풍선당 1~2줄 (총 16~30자, 줄당 10~15자, `\\n` 줄바꿈)**으로 짧고 찰지게 쓰세요!
   - **3줄 말풍선은 1화 최대 1컷(36자 이하)**만 허용하며, **40자 이상 벽돌 텍스트는 절대 금지**입니다.
   - **진짜 한국 와우 유저 말투로 쓰세요 (AI 번역투·연극 독백투·교훈 요약투 금지!)**:
     - 실제 파티창·길드챗·디코에서 2초 만에 칠 법한 자연스러운 어순과 구어체(`아니`, `근데`, `걍`, `진짜`, `뭐임?`, `님`, `아`)를 쓰세요.
     - **혼잣말·속마음에 존댓말 절대 금지**: 혼자 중얼거릴 땐 `"15분째 잡고 있네요..."`(X) 대신 `"수사 솔플 개느리네… 15분째 한 마리씩"(O)처럼 무조건 자연스러운 반말로 쓰세요. 존댓말은 상대에게 직접 말 걸 때만 허용(1화 최대 1~2명).
     - **자기 행동 중계 & 억지 교훈 요약 금지**: `"정배 걸고 절벽으로 꺾기!"`, `"교훈 하나 기억해 둬"`, `"어이없어서 파탈도 까먹었네!"` 같은 정리충·연극투 대사를 버리고, **현타·황당함·깐족·직설 팩폭**으로 끝내세요.
   - 고정 애교 유행어(`옴뇸뇸~`, `으, 으엣?!`, `후훗…`, `~해야징~♪`, `~♡` 도배) 복붙 0건, 거친 욕설 금지.
   - **괄호 다중 화자 편법 절대 금지**: 1말풍선 1화자(`(도적: ...)` 금지). `tail_target`은 화자 위치(`left`/`right`/`center`).
   - 현실 현대어(`119`, `구급차`, `경찰`, `카톡`, `편의점`, `택시`) 대신 와우 어휘(`무덤 이동`, `영혼의 치유사`, `경비병`, `귓말/파티창`, `여관 주인`, `와이번/그리핀`)만 사용하세요.
   - 100% 익명화: 실제 아이디·닉네임·길드명(패러디 포함) 금지, 직업·역할 호칭(`도적`, `징기`, `보기`, `전탱`, `흑마`, `사제`, `파장님`)만 사용하세요.

4. **캐스트 집중 · 고정 동행 펫 · 무언 대왕 클로즈업 컷**:
   - 컷당 공식 9인 캐스트 **1~2명**, 한 화 전체 주연은 **핵심 1~4명** 이내.
   - **고정 동행 펫**: `드워프 사냥꾼` 등장 시 동글동글 **아기 곰**, `인간 흑마법사` 등장 시 동글동글 보라 **공허방랑자**가 곁에서 함께 리액션하도록 `visual_prompt`에 자연스럽게 포함하세요(컷당 1~2명 주연 제한 미산입). **빨간 임프 인형은 절대 언급 금지!**
   - 최소 1컷(권장: 절정 하단 `bottom` / `16:9`)은 **`wordless=True`, `speaker=null`, `dialogue=null`**로 설정하고 화면 높이 75~85%를 꽉 채우는 **대왕 바스트업/클로즈업 과장 표정 개그 컷**으로 연출하세요.

5. **간결한 영문 시각 연출 (`visual_prompt`, 2~3문장)**:
   - 의상·색상은 `artist.py`가 2.5등신 턴어라운드로 자동 고정하므로 의상 설명을 길게 반복하지 마세요.
   - **2~2.5등신 동글동글 귀염뽀짝 SD 웹툰**을 전제로 **① 카메라 구도**(OTS, 로우앵글, 하이앵글, 클로즈업, 측면, 뒷모습 — 정면 나란히 서기 최대 1컷) **② 행동·표정·위치(left/right/center)** **③ 핵심 소품·최소 바닥 터치**만 영문 2~3문장으로 적으세요.
   - **모든 엑스트라·몹·보스·NPC·탈것·동물도 반드시 `cute 2.5-head chibi SD`로 명시**해 화풍을 100% 통일하세요!
   - Clean Hand Rule(전리품·방패·주사위·귀환석·물약병을 들 땐 기본 무기 수납), 탱커(전탱/보기)는 한손 무기+방패, 사슬=링메일 갑옷, 음료=코르크 유리병/나무잔, 주사위=점 눈금만(숫자 없음), 순백 `#FFFFFF` 배경.

6. **원본 제목 100% 유지 (`source_title`) & 선택적 `item_tooltip`**:
   - `source_title`은 원본 개념글 제목(`post.title`)을 토씨 하나 바꾸지 말고 그대로 적으세요.
   - 핵심 와우 아이템이 등장하는 컷에만 선택적으로 `item_tooltip`을 붙이세요(포에버 커스텀 스탯 우선).
"""


def build_writer_prompt(post: GalleryPost, episode_number: int) -> str:
    """Assemble a concise, high-signal prompt for 4~7 cut Route A script generation."""
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


# ---------------------------------------------------------------------------
# Script Quality Auditor (real gate enforced in `generate_episode_script`)
# ---------------------------------------------------------------------------

_PAREN_DUAL_SPEAKER_RE = re.compile(
    r"[\(\[（]\s*([가-힣A-Za-z_]{1,12})\s*:\s*([^)\]）]{2,})[\)\]）]"
)
_LINE_SPEAKER_PREFIX_RE = re.compile(r"^\s*([가-힣]{1,6})\s*:\s*\S+")
_GUILD_TAG_RE = re.compile(r"<[가-힣A-Za-z0-9_ ]{2,20}>")
_EXPLICIT_ID_LEAK_RE = re.compile(r"(?:길드명|닉네임|아이디)\s*[:=]\s*\S+")
_POLITE_ENDING_RE = re.compile(
    r"(?:입니다|습니다|읍니다|습니까|십니까|세요|어요|아요|해요|예요|에요|이죠|하죠|까요|나요|네요|군요|드릴게요|할게요|볼게요|갈게요|주실래요|주세요|마세요|요)[.!?…~\"'”’]*$"
)
_IMP_KO_RE = re.compile(r"임프")
_IMP_EN_RE = re.compile(r"\b(?:imp|imps)\b", re.IGNORECASE)
_VOIDWALKER_RE = re.compile(r"(?:공허방랑자|보이드|voidwalker)", re.IGNORECASE)
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
    ("fisheye_extreme_cu", r"\b(?:fisheye|forced[- ]perspective|extreme\s+(?:face\s+)?close[- ]up|ultra[- ]close[- ]up|big\s+bust[- ]up)\b"),
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
            r"(?:\s+(?:a|an|any|literal|modern|real|paper|metal|red|plush))*$",
            prefix,
        )
    )


def _is_polite_dialogue(dialogue: str) -> bool:
    """Return True if a Korean dialogue bubble predominantly uses polite/honorific sentence endings."""
    lines = [ln.strip() for ln in dialogue.splitlines() if ln.strip()]
    if not lines:
        return False
    return any(_POLITE_ENDING_RE.search(ln) for ln in lines)


def audit_script_quality(
    script: EpisodeScript,
    *,
    forbidden_names: Sequence[str] | None = None,
    strict_cinematic: bool = False,
) -> dict[str, Any]:
    """Audit a 4~7 cut Route A `EpisodeScript` against narrative, rhythm, lore, and anonymity rules."""
    errors: list[str] = []
    warnings: list[str] = []

    cuts: list[ComicCut] = list(script.cuts)
    cut_count = len(cuts)

    cut_count_ok = 4 <= cut_count <= 7
    if not cut_count_ok:
        errors.append(f"Cut count must be 4–7, got {cut_count}.")

    wordless_cuts = [cut.cut_index for cut in cuts if cut.wordless]
    wordless_cut_ok = len(wordless_cuts) >= 1
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
    cast_focus_ok = unique_cast_count <= 4
    if unique_cast_count > 4:
        errors.append(
            f"Cast sprawl: {unique_cast_count} unique cast members exceeds max 4 ({', '.join(unique_cast)})."
        )
    elif unique_cast_count < 2:
        warnings.append(
            f"Only {unique_cast_count} unique cast member in episode; 2–4 core participants recommended."
        )

    no_dual_speaker_hack = True
    no_modern_slang = True
    anonymity_ok = True
    faction_zone_ok = True
    tank_shield_ok = True
    no_forbidden_community = True
    visual_prompt_clean = True
    no_imp_voidwalker_conflict = True
    dialogue_concise_ok = True

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

    episode_has_warlock = "인간 흑마법사" in seen_cast
    episode_has_voidwalker = False
    episode_imp_cuts: list[int] = []

    for cut in cuts:
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
                        f"Visual fidelity violation in {loc}: prompt requests {desc} ('{match.group(0)}')."
                    )
                    break

        # Detect Imp + Voidwalker dual-pet conflict (Human Warlock's sole fixed pet is Voidwalker)
        if _VOIDWALKER_RE.search(dlg) or _VOIDWALKER_RE.search(vp):
            episode_has_voidwalker = True

        has_affirmative_imp = bool(_IMP_KO_RE.search(dlg)) or any(
            not _is_negated_match(vp, m.start()) for m in _IMP_EN_RE.finditer(vp)
        )
        if has_affirmative_imp:
            episode_imp_cuts.append(cut.cut_index)

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

    if episode_imp_cuts and (episode_has_warlock or episode_has_voidwalker):
        no_imp_voidwalker_conflict = False
        errors.append(
            f"Warlock dual-pet conflict (Imp + Voidwalker) in cut(s) {episode_imp_cuts}: "
            "인간 흑마법사's sole fixed companion is 공허방랑자 (Voidwalker) — remove all Imp references."
        )

    # Dialogue pacing, 3-line brick wall, and excessive honorific checks
    dialogue_cuts = [c for c in cuts if not c.wordless and (c.dialogue or "").strip()]
    three_line_cuts: list[int] = []
    bloated_3line_cuts: list[int] = []
    short_1line_cuts: list[int] = []
    polite_cuts: list[int] = []

    for cut in dialogue_cuts:
        dlg = (cut.dialogue or "").strip()
        non_empty_lines = [ln.strip() for ln in dlg.splitlines() if ln.strip()]
        char_len = len(dlg.replace("\n", "").strip())

        if len(non_empty_lines) >= 3:
            three_line_cuts.append(cut.cut_index)
        if char_len > 38 or len(non_empty_lines) >= 4:
            bloated_3line_cuts.append(cut.cut_index)
            dialogue_concise_ok = False
            errors.append(
                f"Dialogue brick wall in cut #{cut.cut_index} ({len(non_empty_lines)} lines, "
                f"{char_len} chars > 38 limit) — tighten to punchy 1–2 lines (16–30 chars)."
            )
        elif len(non_empty_lines) == 3 and char_len > 36:
            warnings.append(
                f"3-line dialogue slightly long in cut #{cut.cut_index} ({char_len} chars; keep <= 36 chars)."
            )
        elif len(non_empty_lines) == 1 and char_len <= 18:
            short_1line_cuts.append(cut.cut_index)

        if _is_polite_dialogue(dlg):
            polite_cuts.append(cut.cut_index)

    three_line_ratio = (len(three_line_cuts) / len(dialogue_cuts)) if dialogue_cuts else 0.0
    if len(dialogue_cuts) >= 3 and three_line_ratio > 0.35:
        dialogue_concise_ok = False
        errors.append(
            f"Too many 3-line speech bubbles: {len(three_line_cuts)}/{len(dialogue_cuts)} "
            f"({three_line_ratio:.0%} > 35%, cuts {three_line_cuts}) — max 1 three-line bubble per episode."
        )

    polite_ratio = (len(polite_cuts) / len(dialogue_cuts)) if dialogue_cuts else 0.0
    if len(dialogue_cuts) >= 3 and polite_ratio > 0.60:
        warnings.append(
            f"Excessive polite/honorific dialogue tone: {len(polite_cuts)}/{len(dialogue_cuts)} "
            f"({polite_ratio:.0%} > 60%, cuts {polite_cuts}) — balance with natural casual WoW banter."
        )

    # Camera variety metrics
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

    cinematic_variety_ok = (
        len(detected_camera_tags) >= 3
        and dynamic_cuts >= 3
        and flat_two_shot_cuts <= 1
    )
    if strict_cinematic and not cinematic_variety_ok:
        errors.append(
            f"Cinematic variety too flat (dynamic_cuts={dynamic_cuts}/{cut_count}, "
            f"camera_tags={sorted(detected_camera_tags)}, flat_side_by_side={flat_two_shot_cuts}) — "
            "vary OTS/low-angle/high-angle/profile/back-view/slapstick action poses."
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
        "no_imp_voidwalker_conflict": no_imp_voidwalker_conflict,
        "dialogue_concise_ok": dialogue_concise_ok,
    }
    if strict_cinematic:
        checks["cinematic_variety_ok"] = cinematic_variety_ok

    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
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
            "three_line_cuts": three_line_cuts,
            "three_line_ratio": round(three_line_ratio, 3),
            "bloated_3line_cuts": bloated_3line_cuts,
            "short_1line_cuts": short_1line_cuts,
            "polite_cuts": polite_cuts,
            "polite_ratio": round(polite_ratio, 3),
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


def _normalize_cut(cut: ComicCut, *, cut_index: int) -> ComicCut:
    norm_chars = [canonical_cast_name(c) for c in cut.characters]
    norm_speaker = (
        None
        if cut.wordless or not cut.speaker
        else canonical_cast_name(cut.speaker)
    )
    return cut.model_copy(
        update={
            "cut_index": cut_index,
            "characters": norm_chars,
            "speaker": norm_speaker,
            "dialogue": None if cut.wordless else cut.dialogue,
        }
    )


def _normalize_script(
    script: EpisodeScript,
    post: GalleryPost,
    episode_number: int,
) -> EpisodeScript:
    """Ensure canonical cast names and exact verbatim source metadata on scripts."""
    verbatim_title = post.title.strip() or script.source_title.strip()
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


def _strip_markdown_fences(raw_text: str) -> str:
    if raw_text.startswith("```"):
        lines = raw_text.splitlines()
        return "\n".join(
            line for line in lines if not line.strip().startswith("```")
        ).strip()
    return raw_text


def generate_episode_script(
    post: GalleryPost,
    episode_number: int,
    *,
    client: Any | None = None,
    settings: Settings | None = None,
    model: str | None = None,
    max_retries: int = 2,
    forbidden_names: Sequence[str] | None = None,
) -> EpisodeScript:
    """Generate, audit, and auto-retry a 4~7 cut `EpisodeScript` via Gemini Interactions API."""
    cfg = settings or load_settings()
    target_model = model or cfg.text_model or DEFAULT_TEXT_MODEL

    if client is None:
        if not cfg.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Configure GEMINI_API_KEY in .env or environment, "
                "or run with --dry-run."
            )
        client = genai.Client(api_key=cfg.gemini_api_key)

    base_prompt = build_writer_prompt(post, episode_number=episode_number)
    retry_feedback: list[str] = []
    last_errors: list[str] = []
    total_attempts = max(1, int(max_retries) + 1)

    for attempt in range(total_attempts):
        if retry_feedback:
            feedback_block = "\n".join(f"- {err}" for err in retry_feedback)
            prompt = (
                f"{base_prompt}\n\n"
                f"=== [이전 초안 자동 품질 검수 실패 (시도 {attempt}/{max_retries}) — 아래 항목을 반드시 수정해 재작성] ===\n"
                f"{feedback_block}"
            )
        else:
            prompt = base_prompt

        interaction = client.interactions.create(
            model=target_model,
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": EpisodeScript.model_json_schema(),
            },
        )

        raw_json = _strip_markdown_fences(_extract_interaction_text(interaction))
        try:
            script = EpisodeScript.model_validate_json(raw_json)
        except (ValidationError, ValueError) as exc:
            last_errors = [f"Schema validation error: {exc}"]
            retry_feedback = last_errors
            continue

        normalized = _normalize_script(script, post=post, episode_number=episode_number)
        audit = audit_script_quality(normalized, forbidden_names=forbidden_names)
        if audit["passed"]:
            return normalized

        last_errors = list(audit["errors"])
        retry_feedback = list(audit["errors"]) + [
            f"(참고 경고) {w}" for w in audit["warnings"][:2]
        ]

    raise ValueError(
        f"Generated script failed audit_script_quality after {total_attempts} attempt(s): "
        + "; ".join(last_errors)
    )


def build_dry_run_script(post: GalleryPost, episode_number: int) -> EpisodeScript:
    """Build a deterministic offline 4-cut Route A (2~2.5 head SD) script for `--dry-run`."""
    verbatim_title = post.title.strip()
    dialogue_hook = verbatim_title or f"개념글 #{post.post_no}"
    short_hook = dialogue_hook[:12]

    cuts = [
        ComicCut(
            cut_index=1,
            aspect_ratio="4:3",
            layout_slot="top",
            characters=["나이트엘프 사제", "오크 전사"],
            speaker="나이트엘프 사제",
            dialogue=f"주특입 파티 맞죠?\n'{short_hook}' 실화예요?",
            wordless=False,
            visual_prompt=(
                "Over-the-shoulder shot in cute 2.5-head chibi SD style: left, exhausted Night Elf "
                "Priest pleading with clasped hands (staff on back); foreground right, back shoulder "
                "of Orc Warrior tank grinning with steel shield and 1H sword on pure #FFFFFF."
            ),
            tail_target="left",
        ),
        ComicCut(
            cut_index=2,
            aspect_ratio="16:9",
            layout_slot="bottom",
            characters=["오크 전사"],
            speaker="오크 전사",
            dialogue="당연하지! 던전 템은\n먼저 집는 사람이 임자야!",
            wordless=False,
            visual_prompt=(
                "Low-angle shot on the right half in cute 2.5-head chibi SD style: Orc Warrior tank "
                "raising her steel kite shield and 1H sword proudly with a confident grin. "
                "Open pure #FFFFFF space on left."
            ),
            tail_target="right",
        ),
        ComicCut(
            cut_index=3,
            aspect_ratio="4:3",
            layout_slot="top",
            characters=["노움 도적", "스카이본 마법사"],
            speaker="노움 도적",
            dialogue="야 방금 파티창에\n전부 다 찍혔는데?",
            wordless=False,
            visual_prompt=(
                "Side-profile comedic shot in cute 2.5-head chibi SD style: left, Gnome Rogue "
                "smirking and pointing thumb back (daggers sheathed); right, Skyborne Mage staring "
                "sideways in disbelief (staff on back) on pure #FFFFFF."
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
                "Centered Dutch-tilt big bust-up close-up in cute 2.5-head chibi SD style: "
                "Skyborne Mage with blank white shock eyes, jaw dropped wide, and a cold sweat drop "
                "filling 80% of canvas height on pure #FFFFFF."
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


def script_to_pretty_json(script: EpisodeScript) -> str:
    """Serialize an `EpisodeScript` as UTF-8 readable JSON."""
    return json.dumps(script.model_dump(mode="json"), ensure_ascii=False, indent=2)
