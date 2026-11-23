"""Episode script writer powered by Google GenAI Interactions API (`gemini-4-hydrogen`).

Produces strictly 100% live in-game WoW Forever (2026 Classic+) dungeon/party gag skits
(4~6 cuts, 1~2 cast members per cut, 2~4 core cast members per episode, at least one
signature wordless shocked/deadpan freeze-frame cut, Draft C Clean Hand visual anchors,
consistent medium chibi framing, pure #FFFFFF background, and strict script quality auditing).
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
from wow_sloptoon.models import ComicCut, EpisodeScript, GalleryPost
from wow_sloptoon.wow_lore import (
    ALLIANCE_ZONES,
    HORDE_ZONES,
    build_wow_lore_guidance,
    find_modern_slang_violations,
)

WRITER_SYSTEM_RULES = """당신은 디시인사이드 '와우 포에버 마이너 갤러리(wowforever)' 개념글을 4~6컷 초귀염 팝·개그 웹툰(《와우 포에버 슬롭툰》) 대본으로 각색하는 전문 시나리오 작가입니다.

[절대 준수 연출 규칙]
1. **100% 라이브 던전/인던/대도시/파티 상황극 & 서사 연속성**:
   - 원글의 에피소드와 재미있는 댓글 드립을 전부 게임 속 현장 대사·상황극으로 녹여내세요.
   - "어 댓글 반응 보니까~", "갤러들이 이렇게 말하네~", "개념글 올라갔네~" 같은 **어색한 메타 댓글 반응 컷/제4의 벽 깨기는 절대 금지**합니다!
   - **4~6컷 서사 인과 연속성 엄수**: 발단(결정적 드랍/입찰/닌자/귀환석/실수 장면) → 갈등·뻔뻔한 변명 → 무언 충격 정지 컷 → 여파·펀치라인까지 사건의 핵심 계기를 절대 건너뛰지 말고 자연스럽게 연결하세요.
2. **분량 및 리듬 (4~6컷)**:
   - 정확히 **4컷, 5컷, 또는 6컷**으로 구성하세요 (`cut_index`는 1부터 순차 증가).
   - 2단 슬롭툰 페이지 구조에 맞춰 슬롯과 비율을 배치하세요:
     * 홀수 컷(1, 3, 5번): `layout_slot="top"`, `aspect_ratio="4:3"` (단, 전체가 5컷일 때 마지막 5번 컷은 단독 피날레 리액션 박스이므로 `layout_slot="bottom"`, `aspect_ratio="16:9"` 권장).
     * 짝수 컷(2, 4, 6번): `layout_slot="bottom"`, `aspect_ratio="16:9"`.
3. **출연 인원 집중 규칙 (컷당 1~2명 · 한 화당 핵심 2~4명 엄수)**:
   - 각 컷의 `characters` 배열에는 반드시 아래 공식 시안 C 캐스트 9명 중 **정확히 1명 또는 2명**의 정식 한국어 이름만 넣으세요.
   - **한 에피소드 전체에 등장하는 고유 캐릭터 수는 반드시 핵심 2~4명 이내로 집중**하세요! 5~6명의 캐스트를 6컷에 무작위로 흩뿌리면 산만해지므로 금지합니다.
4. **시그니처 무언 동공지진 정지 화면 (`wordless=True`) 최소 1컷 필수**:
   - 애용갤 슬롭툰 특유의 찰진 개그 타이밍을 위해, **최소 1개 컷(권장: 하단 `bottom` / `16:9` 컷)은 반드시 `wordless=True`, `speaker=null`, `dialogue=null`** 로 설정하세요.
   - 무언 컷의 `visual_prompt`에는 캐릭터 1명의 정중앙 클로즈업(chest-up close-up), 동공지진·정색·영혼 가출·땀방울·충격 정지 표정을 아주 생생하게 영문으로 묘사하세요.
5. **대사 (`dialogue`) 작성 규칙 — 1말풍선 1화자 절대 엄수**:
   - **괄호 다중 화자 편법 절대 금지**: 한 컷의 `dialogue`에는 반드시 `speaker` **단 1명의 대사만** 적으세요. `(도적: ...)`, `(사제: ...)`, `[전사: ...]` 처럼 한 말풍선 안에 다른 캐릭터 대사를 끼워 넣는 편법은 절대 금지합니다!
   - 말풍선 안에 깔끔히 들어가도록 한국어 구어체 **1~3줄(줄당 14자 내외, `\\n` 줄바꿈 포함)**로 임팩트 있게 작성하세요.
   - `tail_target`은 화자가 화면 왼쪽이면 `"left"`, 오른쪽이면 `"right"`, 정중앙이면 `"center"`로 지정하세요.
   - **와우 인게임 어휘 엄수 (현실 현대어 금지)**: "119 불러야 되나", "구급차", "경찰 불러", "카톡", "편의점", "택시" 같은 현실 표현 대신 **"무덤 이동 눌러야 되나", "영혼의 치유사", "부활 좀요", "귀환석", "와이번/그리핀", "경비병", "귓말/파티창"** 등 100% 와우 인게임 어휘를 사용하세요.
   - 와우 포에버갤 감성을 살리되, 타 커뮤니티 이름은 절대 언급하지 마세요.
   - **명예훼손·고소 방지 익명성 절대 준수**: 사건·사고 당사자의 실제 인게임 닉네임·아이디·길드명(`<길드명>` 태그 및 패러디 별명 포함)은 대사·부제·이미지 프롬프트·툴팁 어디에도 절대 적지 마세요. 오직 직업·역할 호칭(`도적`, `징기`, `보기`, `전탱`, `흑마`, `사제`, `파장님` 등)으로만 표현하세요.
6. **영문 비주얼 프롬프트 (`visual_prompt`) 규칙 — 일관된 스케일 · Clean Hand · 판타지 고증**:
   - 반드시 영문으로 캐릭터의 좌우 위치, 포즈, 소품, 표정, 감정을 구체적으로 묘사하세요.
   - **일관된 미디엄 치비 프레이밍 (Micro-Chibi 축소 금지)**: `4:3` 컷과 `16:9` 컷 모두 일반 대화 컷은 **일관된 2.5~3등신 허리~무릎 위(medium waist-up / knee-up chibi shot)** 크기로 크고 선명하게 프레이밍하세요. 특히 `16:9` 2인 컷에서 캐릭터가 콩알만한 전신 마이크로 치비로 작아지지 않도록 주의하세요!
   - **Clean Hand Rule (무기·소품 겹침 금지)**: 캐릭터가 전리품·방패·주사위·귀환석·물약병을 들거나 제스처를 취할 때는 기본 무기를 등/허리에 수납(`sheathed on back/belt`)하거나 생략하도록 명시하세요(한 캐릭터가 무기 3개 이상 동시 소지 절대 금지).
   - **와우 포에버 장비·소품 시각화 고증**:
     * `전탱`/`방전`/`보기` 탱커는 반드시 **한손 무기 + 방패(sturdy shield)** 착용!
     * `사슬(Mail)` 장비(`속박의 사슬` 등)는 쇠사슬·수갑이 아니라 **링메일 사슬 갑옷 허리띠/갑옷(interlocking ring-mesh mail armor belt)**으로 묘사!
     * `멜론 주스`·음료·물약은 현대 종이팩/빨대가 아니라 **중세 판타지 코르크 유리병 또는 나무 머그잔(fantasy corked glass flask / wooden mug)**으로 묘사!
     * 한손검(`장트라제`)·단검(`필살의 비수`)은 한 손 비율로(양손 대검화 금지), 주사위는 **점 눈금만 있는 6면체(dot pips only, ZERO digits/text)**로 묘사!
   - 모든 컷은 **100% pure solid white `#FFFFFF` borderless background (no scenery, no text, no speech bubbles)** 조건을 전제로 캐릭터와 최소한의 판타지 소품만 등장하도록 묘사하세요.
7. **원본 개념글 제목 100% 원문 유지 (`source_title`)**:
   - `source_title`에는 절대 임의로 요약·재작성한 제목을 넣지 말고, 제공된 **포에버갤 원본 개념글 제목(`post.title`)을 100% 글자 그대로** 기입하세요.
8. **와우 포에버 실제 아이템 툴팁 카드 (`item_tooltip`, 선택 사항)**:
   - 실제 와우 아이템이 핵심 소재로 등장하는 컷에만 선택적으로 `item_tooltip`을 지정할 수 있습니다. 유저 닉네임·캐릭터명·길드명에는 절대 `item_tooltip`을 붙이지 마세요.
   - **포에버 커스텀 스탯 최우선**: 바닐라 와우헤드 DB가 와우 포에버 개편 스탯(예: `모드레쉬의 이글거리는 눈`, `크롤도크 보루` 커스텀 템)과 다를 수 있으므로, 원글 본문이나 첨부 툴팁 스크린샷에 명시된 포에버 실스탯을 최우선으로 반영하세요.
"""


def build_writer_prompt(post: GalleryPost, episode_number: int) -> str:
    """Assemble the complete structured prompt with WoW Forever lore & Draft C cast bible."""
    cast_bible = format_cast_bible_for_writer()
    comments_block = (
        "\n".join(f"- {c}" for c in post.comments[:12])
        if post.comments
        else "(별도 댓글 없음 — 본문 에피소드 자체를 찰진 라이브 상황극으로 극대화하세요)"
    )
    context_text = "\n".join(
        [post.title or "", post.body or "", *post.comments[:12]]
    )
    lore_guidance = build_wow_lore_guidance(context_text)

    return (
        f"{WRITER_SYSTEM_RULES}\n\n"
        f"{lore_guidance}\n\n"
        f"{cast_bible}\n\n"
        f"=== 각색 대상 포에버갤 개념글 ===\n"
        f"- 예정 화수: EP.{episode_number}\n"
        f"- 게시글 번호: #{post.post_no}\n"
        f"- 원문 URL: {post.url}\n"
        f"- 원문 제목 (100% 그대로 유지): {post.title.strip()}\n"
        f"- 작성자: {post.author} | 추천: {post.recommends} | 댓글: {post.comments_count}\n"
        f"- 본문:\n{post.body or '(본문 텍스트 없음 — 제목의 펀치라인을 던전 상황극으로 풀어내세요)'}\n\n"
        f"- 주요 댓글 (메타 해설 금지! 웃긴 포인트만 캐릭터 대사·상황극 소재로 흡수):\n{comments_block}\n\n"
        f"위 JSON 스키마(`EpisodeScript`)에 정확히 맞춰 출력하세요. "
        f"`episode_number`는 {episode_number}, `source_post_no`는 \"{post.post_no}\", "
        f"`source_title`은 원문 제목 100% 그대로인 {json.dumps(post.title.strip(), ensure_ascii=False)}, "
        f"`source_url`은 \"{post.url}\" 로 정확히 기입하세요."
    )


# ---------------------------------------------------------------------------
# Script Quality Auditor (catches EP.1–EP.10 flaws before expensive art gen)
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
) -> dict[str, Any]:
    """Audit an `EpisodeScript` against all WoW Forever lore, anonymity, and framing rules.

    Catches the exact quality regressions observed across EP.1–EP.10:
    - Cut count outside 4–6 or missing wordless freeze-frame cut
    - Cast sprawl (> 4 unique cast members across the episode)
    - Parenthetical or multi-line dual-speaker hacks inside one bubble (e.g. `(도적: ...)`)
    - Modern real-world phrasing (e.g. `119`, `구급차`, `카톡`, `편의점`)
    - Real player nicknames / guild tags (`<Guild>`) / forbidden community (`인벤`)
    - Outdoor faction/zone hearthstone mismatch (e.g. Tauren Druid claiming Dolanaar)
    - Tanking Warrior/Paladin wielding a 2H weapon with no shield
    - Literal anti-hallucination visual prompt traps (juice box, prison chains)
    """
    errors: list[str] = []
    warnings: list[str] = []

    cuts = list(script.cuts)
    cut_count = len(cuts)
    cut_count_ok = 4 <= cut_count <= 6
    if not cut_count_ok:
        errors.append(f"Cut count must be 4–6, got {cut_count}.")

    wordless_cuts = [cut.cut_index for cut in cuts if cut.wordless]
    wordless_cut_ok = len(wordless_cuts) >= 1
    if not wordless_cut_ok:
        errors.append("Missing mandatory wordless freeze-frame cut (wordless=True).")

    # Cast sprawl check (2–4 core cast members)
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

    # Check subtitle
    _check_text_anonymity_and_community(script.subtitle, "subtitle")
    if _GUILD_TAG_RE.search(script.subtitle) or _EXPLICIT_ID_LEAK_RE.search(script.subtitle):
        anonymity_ok = False
        errors.append(f"Possible guild tag / ID leak in subtitle: '{script.subtitle}'.")
    for label, replacement in find_modern_slang_violations(script.subtitle):
        no_modern_slang = False
        errors.append(
            f"Modern real-world phrasing '{label}' in subtitle (use WoW phrasing like '{replacement}')."
        )

    for cut in cuts:
        loc = f"cut #{cut.cut_index}"
        dlg = (cut.dialogue or "").strip()
        vp = (cut.visual_prompt or "").strip()

        # Non-wordless cut checks
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

        # 1. Dual-speaker hacks in dialogue
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

            # 2. Modern slang check
            for label, replacement in find_modern_slang_violations(dlg):
                no_modern_slang = False
                errors.append(
                    f"Modern real-world phrasing '{label}' in {loc} dialogue "
                    f"(use WoW phrasing like '{replacement}')."
                )

            # 3. Anonymity & community check
            _check_text_anonymity_and_community(dlg, f"{loc} dialogue")
            if _GUILD_TAG_RE.search(dlg) or _EXPLICIT_ID_LEAK_RE.search(dlg):
                anonymity_ok = False
                errors.append(f"Possible guild tag / ID leak in {loc} dialogue.")

            # 4. Outdoor faction/zone hearthstone mismatch
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

        # 5. Visual prompt checks (anonymity, forbidden community, tank shield, anti-hallucination traps)
        _check_text_anonymity_and_community(vp, f"{loc} visual_prompt")

        for pat, desc in _VISUAL_TRAP_PATTERNS:
            for match in re.finditer(pat, vp, flags=re.IGNORECASE):
                if not _is_negated_match(vp, match.start()):
                    visual_prompt_clean = False
                    errors.append(
                        f"Visual anti-hallucination violation in {loc}: prompt requests {desc} ('{match.group(0)}')."
                    )
                    break

        # Tank shield check when Warrior/Paladin appears in a tanking cut holding a 2H weapon with no shield
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

        # 6. Item tooltip anonymity guard (never attach tooltips to user/cast names)
        if cut.item_tooltip and cut.item_tooltip.item_name:
            tip_name = cut.item_tooltip.item_name.strip()
            _check_text_anonymity_and_community(tip_name, f"{loc} item_tooltip")
            if resolve_cast_member(tip_name) is not None or tip_name.endswith(("님", "길드")):
                anonymity_ok = False
                errors.append(
                    f"Invalid item_tooltip.item_name '{tip_name}' in {loc}: tooltips are strictly for WoW items."
                )

    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "cut_count": cut_count,
        "wordless_cuts": wordless_cuts,
        "unique_cast": unique_cast,
        "unique_cast_count": unique_cast_count,
        "checks": {
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
        },
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

    verbatim_title = post.title.strip() or script.source_title.strip()
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
    verbatim_title = post.title.strip()
    dialogue_hook = verbatim_title or f"개념글 #{post.post_no}"
    snippet = (post.body.strip().splitlines()[0][:28] + "...") if post.body.strip() else dialogue_hook[:28]

    cuts = [
        ComicCut(
            cut_index=1,
            aspect_ratio="4:3",
            layout_slot="top",
            characters=["나이트엘프 사제", "오크 전사"],
            speaker="나이트엘프 사제",
            dialogue=f"저기요...\n'{dialogue_hook[:18]}'\n이거 실화예요?",
            wordless=False,
            visual_prompt=(
                "Medium waist-up 2.5-head chibi framing. Left: Night Elf Priest chibi girl with "
                "dark under-eye circles leaning her golden crescent staff beside her while asking "
                "nervously with clasped hands. Right: Orc Warrior chibi girl in green orc hood "
                "grinning confidently with her axe strapped on her back. Pure solid white #FFFFFF "
                "background, no text, no speech bubbles."
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
                "Medium waist-up chibi framing on the right side of the wide 16:9 frame: Orc "
                "Warrior chibi girl in vibrant green orc animal hood giving a bold proud thumbs-up "
                "with sparkles and cheeky grin, her silver battle axe strapped across her back. "
                "Pure solid white #FFFFFF background, no text, no speech bubbles."
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
                "Medium waist-up chibi framing. Left: Gnome Rogue chibi girl with blonde-pink-blue "
                "pigtails and green goggles pointing mischievously with a sly grin (daggers "
                "sheathed at belt). Right: Skyborne Mage chibi girl with elf ears and airy "
                "sky-blue hair tips glancing sideways nervously (hands empty). Pure solid white "
                "#FFFFFF background, no text, no speech bubbles."
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
                "Centered dramatic deadpan chest-up close-up freeze-frame of Skyborne Mage chibi "
                "girl with pointed elf ears, golden-blonde-to-sky-blue hair, and sailor uniform, "
                "tiny trembling shocked pupils, frozen speechless in comedic disbelief. Pure solid "
                "white #FFFFFF background, no text, no speech bubbles."
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
