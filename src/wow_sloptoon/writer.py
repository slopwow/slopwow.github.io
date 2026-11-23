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
1. **원글 실제 상황·스샷 100% 현장 재현 (억지 만담 상황극 절대 금지!)**:
   - **작성자가 의도한 진짜 그 상황과 원본 스샷의 핵심 디테일을 100% 그대로 그림으로 재현하세요!** (예: 원글 스샷에 땅바닥에 호드 쪼렙 시체/해골이 수북이 쌓여 있다면 반드시 그 시체 더미 장면을 직접 그려야 합니다! 원글이 1인칭 독백/후기/현장 폭로라면 억지로 두 캐릭터가 주거니 받거니 하는 만담 대화로 바꾸지 말고, 독백·내레이션·현장 액션·군중/몹/보스/시체 더미 컷으로 그대로 살리세요!)
   - "어 댓글 반응 보니까~", "갤러들이 이렇게 말하네~", "개념글 올라갔네~" 같은 **어색한 메타 댓글 반응 컷/제4의 벽 깨기는 절대 금지**합니다!
   - **4~6컷 서사 인과 연속성 엄수**: 발단(현장 상황·스샷 디테일) → 전개/사건 → 무언 충격/개그 정지 컷 → 여파·펀치라인까지 핵심 시각 계기를 빠뜨리지 마세요.
2. **분량 및 리듬 (4~6컷)**:
   - 정확히 **4컷, 5컷, 또는 6컷**으로 구성하세요 (`cut_index`는 1부터 순차 증가).
   - 2단 슬롭툰 페이지 구조에 맞춰 슬롯과 비율을 배치하세요:
     * 홀수 컷(1, 3, 5번): `layout_slot="top"`, `aspect_ratio="4:3"` (단, 전체가 5컷일 때 마지막 5번 컷은 단독 피날레 리액션 박스이므로 `layout_slot="bottom"`, `aspect_ratio="16:9"` 권장).
     * 짝수 컷(2, 4, 6번): `layout_slot="bottom"`, `aspect_ratio="16:9"`.
3. **고정 캐스트 + 엑스트라·군중·시체·몹 자유 등장 규칙**:
   - 각 컷의 `characters` 배열에는 해당 컷의 주연 고정 캐스트(시안 C 9명 중 **1~2명**)를 기입하고, 한 화 전체의 주연 고정 캐스트는 **핵심 1~4명 이내**로 유지하세요.
   - **단, 화면 안에 고정 캐스트 1~2명만 나와야 할 이유는 전혀 없습니다!** 원글 상황에 맞게 **엑스트라 유저들, 쪼렙 시체/해골 더미(귀여운 만화풍·비고어), 군중, 보스 몬스터, 몹 떼거리, 경비병 NPC, 펫, 탈것**을 `visual_prompt`에 과감하고 생생하게 그려 넣어 실제 와우 포에버 현장을 재현하세요!
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
6. **영문 비주얼 프롬프트 (`visual_prompt`) 규칙 — 시네마틱 액션·표정 다양화·정면 만담 금지·Clean Hand**:
   - **🚫 정면 나란히 스탠딩 만담 도장찍기 절대 금지**: 한 에피소드 6컷을 "On the lower-left A..., On the lower-right B..." 식의 평면 정면 2인 서기 대화로 채우지 마세요! 평면 정면 나란히 2인 구도는 **한 화에 최대 1컷 이하**로 제한합니다.
   - **🎬 6컷 시네마틱 샷 리듬 의무화 (Show, Don't Just Tell)**: 한 화 6컷 안에서 **최소 4가지 이상의 서로 다른 카메라 앵글 & 신체 모션**을 조합하세요!
     * **오버더숄더(Over-the-shoulder, OTS) 대각선 깊이감 샷** (Reference Image 2 스타일 — 전경 한쪽에 한 캐릭터 뒷모습·어깨가 크게 걸리고, 후경 캐릭터가 상체를 훅 숙이거나 고개 갸웃·삿대질·능글 표정으로 반응!)
     * **풀모션 인게임 물리 개그·액션 컷 (최소 2~3컷 필수!)**: 돌진·질주·몹 실루엣에 쫓겨 도주·은신 살금살금 기습·바닥에 철퍼덕 죽은 척 눕기·귀환석 빛기둥 속으로 빨려 들어가며 손 흔들기·보물상자 다이빙·배 난간 매달리기·뒤돌아 쿨하게 걸어가기·무릎 꿇고 절규·테이블/방패 쾅!
     * **로우앵글 / 하이앵글 / 기울어진 더치 앵글(Dutch tilt)** 및 **측면 90° 프로필 / 비대칭 클로즈업**으로 시점을 매 컷 역동적으로 전환!
     * **미니멀 액션 비네트 소품(Minimalist Vignette Props)**: 외곽 캔버스는 100% 순백 `#FFFFFF` 여백을 유지하되, 캐릭터 동작에 직접 붙는 단일 미니멀 소품(열린 보물상자, 야영 모닥불, 귀환석 빛기둥, 선착장 나무 난간, 여관 테이블 모서리, 흩날리는 먼지·스피드선·주문 불꽃·몹 그림자 실루엣)을 적극 활용해 살아 움직이는 현장감을 살리세요!
   - **🎭 표정·연기 매 컷 다양화**: `cast_sheet`의 고정 표정을 복붙하지 말고, 컷마다 썩소·턱 빠짐·소용돌이 눈·영혼 입으로 탈출·초점 나간 하얀 눈·음침 그림자·눈물 폭포·볼 빵빵 삐짐·곁눈질 등 다채로운 만화 과장 표정을 구체적으로 묘사하세요! 무언 정지 컷도 매 화 똑같은 정면 동공지진만 반복하지 말고 상황 맞춤형으로 변주하세요.
   - **일관된 미디엄 치비 프레이밍 (Micro-Chibi 축소 금지)**: `4:3` 컷과 `16:9` 컷 모두 일반 컷은 **일관된 2.5~3등신 허리~무릎 위(medium waist-up / knee-up chibi shot)** 크기로 선명하게 프레이밍하세요(원거리 점처럼 작아지기 금지).
   - **Clean Hand Rule (무기·소품 겹침 금지)**: 캐릭터가 전리품·방패·주사위·귀환석·물약병을 들거나 제스처를 취할 때는 기본 무기를 등/허리에 수납(`sheathed on back/belt`)하거나 생략하도록 명시하세요(한 캐릭터가 무기 3개 이상 동시 소지 절대 금지).
   - **와우 포에버 장비·소품 시각화 고증**:
     * `전탱`/`방전`/`보기` 탱커는 반드시 **한손 무기 + 방패(sturdy shield)** 착용!
     * `사슬(Mail)` 장비(`속박의 사슬` 등)는 쇠사슬·수갑이 아니라 **링메일 사슬 갑옷 허리띠/갑옷(interlocking ring-mesh mail armor belt)**으로 묘사!
     * `멜론 주스`·음료·물약은 현대 종이팩/빨대가 아니라 **중세 판타지 코르크 유리병 또는 나무 머그잔(fantasy corked glass flask / wooden mug)**으로 묘사!
     * 한손검(`장트라제`)·단검(`필살의 비수`)은 한 손 비율로(양손 대검화 금지), 주사위는 **점 눈금만 있는 6면체(dot pips only, ZERO digits/text)**로 묘사!
   - 모든 컷의 외곽 배경은 **100% pure solid white `#FFFFFF` borderless background (no full room walls/scenery, no text, no speech bubbles)** 조건을 유지하세요.
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
_CAMERA_ANGLE_TAGS: tuple[tuple[str, str], ...] = (
    ("over_the_shoulder", r"\b(?:over[- ]the[- ]shoulder|foreground\s+shoulder|back\s+of\s+(?:her|the)\s+head|foreground\s+back)\b"),
    ("low_angle", r"\b(?:low[- ]angle|worm'?s[- ]eye|looking\s+up\s+at|looming\s+above)\b"),
    ("high_angle", r"\b(?:high[- ]angle|bird'?s[- ]eye|top[- ]down|looking\s+down\s+at)\b"),
    ("dutch_tilt", r"\b(?:dutch\s*(?:tilt|angle)|tilted\s+(?:camera|angle|frame)|diagonal\s+(?:angle|camera|composition))\b"),
    ("side_profile", r"\b(?:side[- ]profile|profile\s+view|90[- ]degree|side\s+view|chasing\s+across)\b"),
    ("back_view", r"\b(?:back\s+view|seen\s+from\s+behind|walking\s+away|turning\s+her\s+back|looking\s+back\s+over\s+her\s+shoulder)\b"),
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

    # 7. Cinematic variety & anti-talking-heads check (prevents repetitive flat side-by-side cuts)
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

    cinematic_variety_ok = (len(detected_camera_tags) >= 3 and dynamic_cuts >= 3 and flat_two_shot_cuts <= 1)
    if strict_cinematic and not cinematic_variety_ok:
        errors.append(
            f"Cinematic variety too flat (dynamic_cuts={dynamic_cuts}/{cut_count}, "
            f"camera_tags={sorted(detected_camera_tags)}, flat_side_by_side={flat_two_shot_cuts}) — "
            "vary OTS/low-angle/high-angle/profile/back-view/slapstick action poses instead of static talking heads."
        )

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
            **({"cinematic_variety_ok": cinematic_variety_ok} if strict_cinematic else {}),
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
