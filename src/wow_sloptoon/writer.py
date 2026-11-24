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
from wow_sloptoon.layouts import PAGE_LAYOUTS, get_page_layout
from wow_sloptoon.models import ActPage, BackgroundStyle, ComicCut, EpisodeScript, GalleryPost
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


V4_WRITER_SYSTEM_RULES = """당신은 디시인사이드 '와우 포에버 마이너 갤러리(wowforever)' 개념글을 **V4 5막 가변 레이아웃(5 Acts · 10~14컷 · 페이지 배치 작화)** 초귀염 팝·개그 웹툰(《와우 포에버 슬롭툰》) 대본으로 각색하는 전문 시나리오 작가입니다.

[V4 5막 가변 레이아웃 절대 준수 규칙]
1. **5막(5 Acts) · 10~14컷 장편 서사 리듬 (`layout_mode="v4_five_act"`)**:
   - 반드시 `layout_mode`를 `"v4_five_act"`로 설정하고, `acts` 배열에 정확히 **5개의 막(`act_number`: 1, 2, 3, 4, 5)**을 순서대로 작성하세요.
   - 각 막의 역할:
     * **1막 (발단·현장 진입)**: 원글의 실제 인게임 상황·던전/필드 현장·스샷 디테일과 전투/현장 분위기를 생생히 제시.
     * **2막 (전개·조짐)**: 꼰대짓·억까·입찰/어그로 사고·갈등의 불씨를 노골적이고 자극적으로 점화.
     * **3막 (위기·확산)**: 사건 본격화, 몬스터 전투 난장판·슬랩스틱 몸개그·격앙된 대립과 갈등 폭발.
     * **4막 (절정·무언 충격 정지)**: `impact_freeze_2cut` 레이아웃 강력 권장! 하단 초대형 패널에 **풀-블리드 극장판 배경 + 엑스트라/보스 카메오**를 활용한 **시그니처 무언 충격 정지 클로즈업(`wordless=True`)**을 배치해 극대화된 개그 임팩트를 연출하세요.
     * **5막 (여파·막장 반전 펀치라인)**: 맑눈광 꽃밭 반전·흑화·현타·귀환석 도주 등 찰진 엔딩 펀치라인.
   - 5개 막의 모든 컷을 합산한 총 컷 수는 반드시 **10~14컷(권장 12~13컷)**이어야 합니다.
2. **6종 가변 페이지 레이아웃(`layout_id`) 조합 및 다양성 규칙**:
   - 각 막(`ActPage`)은 아래 6종 `layout_id` 중 하나를 선택하고, `act.cuts` 개수를 해당 레이아웃의 **정확한 패널 수**와 100% 일치시켜야 합니다:
     * `"open_top_split_bottom"` (3컷): 상단 보더리스 오픈 와이드 + 하단 좌/우 세로 분할 2컷.
     * `"split_top_wide_bottom"` (3컷): 상단 좌/우 세로 분할 2컷 + 하단 와이드 1컷.
     * `"diagonal_tempo_2cut"` (2컷): 상단 대형 오픈 컷 + 하단 와이드 1컷.
     * `"impact_freeze_2cut"` (2컷): 상단 빌드업 와이드 컷 + 하단 초대형 클라이맥스/무언 정지 컷.
     * `"wide_reaction_wide"` (3컷): 상/중/하 3단 시네마틱 와이드 스트립.
     * `"four_beat_gag"` (4컷): 2×2 빠른 4박자 개그 그리드.
   - **연속 동일 레이아웃 금지**: 인접한 두 막(예: 1막과 2막, 2막과 3막)에 같은 `layout_id`를 절대 연달아 쓰지 마세요!
   - **최소 3종 이상 다양성**: 5개 막 전체에서 **최소 3종 이상(권장 4~5종)**의 서로 다른 `layout_id`를 조합해 페이지마다 리듬을 살리세요.
   - V4 컷의 `aspect_ratio`는 `"auto"`, `layout_slot`은 `"panel"`로 기입하세요.
3. **원글 100% 현장 재현 · 막장드라마급 자극적 감정선 & 갈등 극대화 의무화**:
   - **막장드라마급 자극적 감정선 & 갈등 극대화 의무화**: 물 흐르듯 심심하고 예의 바른 대화를 절대 금지합니다! 원글 개념글의 분노·억까·꼰대짓·배신·먹튀·반전을 과장된 만화적 자극과 슬랩스틱(**두루마리 낚아채기, 그을음 폭탄 머리, 흑화 오라, 도끼 뽑기, 맑눈광 꽃밭 반전, 멱살잡이, 턱 빠짐·영혼 탈출**)으로 극대화하세요!
   - 원글의 실제 사건·스샷 디테일을 100% 인게임 라이브 상황극으로 재현하세요.
   - "댓글 반응 보니까~", "개념글 갔네~" 같은 메타 댓글 컷/제4의 벽 깨기는 절대 금지합니다.
   - 타 커뮤니티(와우 인벤 등) 언급은 영구 금지합니다.
4. **고정 캐스트 집중 + 몬스터 전투 씬 & 엑스트라·보스·NPC 필수 투입 + 인접 컷 인물 연속성**:
   - 각 컷의 `characters`에는 시안 C 9명 중 **1~2명**만 기입하고, 한 화 전체 주연 고정 캐스트는 **2~4명(최대 5인 파티 이내)**으로 집중하세요.
   - **인접 컷 인물 연속성 절대 엄수**: 직전 컷에서 캐릭터 A가 B에게 따졌다면 바로 다음 컷에서 B가 역공할 때 반드시 같은 대상 A가 맞받아쳐야 합니다(갑자기 다른 캐릭터 C로 대상이 바뀌는 콘티 연속성 오류 금지). 또한 배경 엑스트라에 주연 캐릭터와 똑같이 생긴 복제 인물을 넣지 마세요.
   - **몬스터 전투 씬 & 엑스트라·보스·NPC 필수 투입**: 한 화 5막(10~14컷) 중 **최소 2~3컷 이상에 던전 몬스터 때려잡는 전투 액션, 몹 떼거리, 보스 카메오(해적 선원·고블린·오우거·던전 네임드 등), 엑스트라 유저/경비병/NPC 군중**을 `visual_prompt`에 적극 배치해 살아있는 와우 인게임 현장감을 살리세요! (귀여운 만화풍·비고어 쪼렙 시체/해골 더미, 펫, 탈것도 적극 활용)
5. **시그니처 무언 충격 정지 컷 (`wordless=True`) 최소 1컷 필수 — 풀-블리드 극장판 연출**:
   - 최소 1컷(권장: 4막 `impact_freeze_2cut`의 2번 초대형 패널)은 반드시 `wordless=True`, `speaker=null`, `dialogue=null`로 설정하세요.
   - `wordless=True` 절정 컷은 말풍선이 없으므로 텅 빈 흰 배경 대신 **풀-블리드 극장판 배경(던전 전당, 해적선 갑판, 불타는 갱도, 지켜보는 보스/몹/엑스트라 카메오, 극적인 만화 조명·충격파)**을 패널 가득 적극 활용해 압도적인 개그 임팩트를 연출하세요!
6. **1말풍선 1화자 · 좁은 패널 압축 대사 · 와우 인게임 어휘 · 100% 익명화**:
   - **괄호 다중 화자 편법 절대 금지**: `(도적: ...)`, `[전사: ...]` 금지! 한 컷 `dialogue`에는 `speaker` 단 1명의 대사만 적으세요.
   - **세로 분할 좁은 컷(410px)**에서는 대사를 1~3줄(줄당 10~12자 내외, `\\n` 줄바꿈)로 짧고 임팩트 있게 압축하세요. 와이드 컷은 1~3줄(줄당 14자 내외).
   - **현실 현대어 금지**: "119", "112", "구급차", "경찰", "카톡", "편의점", "택시", "배민" 대신 "무덤 이동", "영혼의 치유사", "경비병", "귓말/파티창", "여관 주인", "와이번/그리핀" 등 100% 와우 인게임 어휘만 사용하세요.
   - **100% 익명성 준수**: 실제 닉네임·아이디·`<길드명>`(패러디 포함)을 대사·막 제목·부제·이미지 프롬프트·툴팁 어디에도 절대 적지 말고 오직 직업·역할 호칭(`도적`, `징기`, `보기`, `전탱`, `흑마`, `사제`, `파장님`)만 사용하세요.
7. **V4.3 선별 믹스 배경 리듬(`background_style="selective_mix"` 기본) · 시네마틱 연출 · 표정 다양화 · Clean Hand · 와우 포에버 고증**:
   - **V4.3 `selective_mix` 절대 원칙 — "넣을 컷은 100% 전면 풀-블리드 박스, 뺄 컷은 100% 깔끔한 순백 `#FFFFFF`!" (어설픈 반쪽짜리 비네트 컷아웃·박스 안 둥둥 떠 있는 부분 배경 영구 금지!)**:
     * `background_style="selective_mix"`일 때 모든 컷에 배경을 억지로 욱여넣지 마세요! 전체 10~14컷 중 **40~60%**는 **현장 진입·전투 난장판·군중/몹/보스·클라이맥스 무언 정지·여운 엔딩 컷**으로 `full_bleed_bg=True`를 지정하고, 나머지 **40~60%**는 **찰진 티키타카 대화·리액션·몸개그 컷**으로 `full_bleed_bg=False`를 지정해 화면의 완급과 호흡을 살리세요!
     * **`full_bleed_bg=True` 컷 규칙**: 패널 상하좌우 100% 끝까지 꽉 차는 풀-블리드 컬러 배경(던전 석조 갱도·나무 서까래·횃불·광차 레일, 선착장·해적선 돛과 갑판, 밤하늘, 여관 벽면, 폭발 화염·연기, 흑화 오라/꽃밭 반전 등)으로 `visual_prompt`를 작성하고, 대사 컷이라면 캐릭터를 **하단 62~66%(또는 화자 측 절반)**에 배치해 말풍선 영역(와이드 상단 30~35% / 세로 좁은 컷 상단 34~38% / 슬림 와이드 반대쪽 44% 또는 상단 34%)이 **인물이 없는 트인 풀-블리드 배경 풍경**이 되게 설계하세요.
     * **`full_bleed_bg=False` 컷 규칙**: **100% 깔끔한 순백 `#FFFFFF` 배경**에 캐릭터 연기 + 최소한의 만화 개그 이펙트(땀방울·분노 마크·스피드선·충격선·영혼 탈출)만 넣도록 `visual_prompt`를 작성하세요(**어설픈 반쪽짜리 비네트 배경·박스 안 떠 있는 부분 배경 사각형 절대 금지!**).
     * `background_style="full_bleed"`일 때는 모든 컷을 `full_bleed_bg=True`(100% 엣지투엣지 풀-블리드 박스)로, `background_style="clean_white"`일 때는 모든 컷을 `full_bleed_bg=False`(100% 순백 `#FFFFFF` 깔끔한 배경, 부분 비네트 금지)로 작성하세요.
     * **페이지 외곽 여백·거터는 모든 모드에서 항상 `#FFFFFF` 순백 유지!**
   - **시네마틱 카메라 & 물리 슬랩스틱**: 정면 나란히 서기 만담 도장찍기 금지! 5막 전체에서 OTS(오버더숄더), 로우앵글, 하이앵글, 더치 틸트, 측면 90° 프로필, 뒷모습, 물리 슬랩스틱(돌진·도주·죽은 척·은신·귀환석 소용돌이·두루마리 낚아채기·그을음 폭탄 머리·도끼 뽑기·무릎 꿇기 등)을 다채롭게 배합하세요.
   - **Clean Hand Rule**: 전리품·방패·주사위·귀환석·물약을 들거나 제스처 시 기본 무기는 등/허리에 수납(`sheathed on back/belt`)하거나 생략하세요(한 캐릭터 무기 3개 동시 소지 금지).
   - **고증 필수**: `전탱`/`보기` 탱커는 반드시 한손 무기 + 방패, `사슬(Mail)`은 링메일 사슬 갑옷(쇠사슬/수갑 금지), 음료·물약은 코르크 유리병/나무 머그잔(종이팩/빨대 금지), 주사위는 점 눈금만(숫자·글자 금지).
   - **시안 C 최신 3면 도면 디테일 고정**: 노움 도적은 머리핀 0개(X·별핀 금지), 나이트엘프 사제는 평범한 뽀얀 피부·연보라 반묶음·은빛 발광눈·보라 사제복·허리 미니 성서 & 황금 묵주·황금 십자/성광 지팡이(천사링·날개 0개), 스카이본 마법사는 뽀얀 피부·하늘색 하이 사이드포니·웃는 구름/날개 뱃지 파란 마법사 모자·구름 망토·허리 미니 변이 양 키링·파란 수정구 지팡이(세일러복 금지).
8. **원본 제목 100% 원문 유지 (`source_title`) & 선택적 `item_tooltip`**:
   - `source_title`은 제공된 원본 개념글 제목(`post.title`)을 토씨 하나 바꾸지 말고 그대로 기입하세요.
   - 실제 와우 아이템이 핵심 소재인 컷에만 선택적으로 `item_tooltip`을 붙이세요(유저 닉네임·길드명 절대 금지).
"""


def _format_v4_layouts_reference() -> str:
    lines = ["=== V4 가변 페이지 레이아웃 6종 스펙 (900x1350, 2:3) ==="]
    for layout_id, spec in PAGE_LAYOUTS.items():
        slot_summary = ", ".join(
            f"P{s.slot_index}({s.position_label}, {'narrow 410px' if s.is_narrow else 'wide 844px'}, {s.border_style})"
            for s in spec.slots
        )
        lines.append(f"- `{layout_id}` ({spec.panel_count}컷): {spec.description}\n  구성: {slot_summary}")
    return "\n".join(lines)


def build_v4_writer_prompt(
    post: GalleryPost,
    episode_number: int,
    *,
    background_style: BackgroundStyle = "selective_mix",
) -> str:
    """Assemble the complete V4 5-act variable-layout structured prompt."""
    cast_bible = format_cast_bible_for_writer()
    layouts_ref = _format_v4_layouts_reference()
    comments_block = (
        "\n".join(f"- {c}" for c in post.comments[:15])
        if post.comments
        else "(별도 댓글 없음 — 본문 에피소드의 현장감과 반전을 5막 호흡으로 극대화하세요)"
    )
    context_text = "\n".join(
        [post.title or "", post.body or "", *post.comments[:15]]
    )
    lore_guidance = build_wow_lore_guidance(context_text)

    if background_style == "selective_mix":
        bg_directive = (
            "이번 화의 `background_style`은 `\"selective_mix\"`입니다. 전체 10~14컷 중 40~60% 핵심 현장·전투·군중·클라이맥스·엔딩 컷에는 "
            "`full_bleed_bg=true`(100% 전면 풀-블리드 박스 배경)를, 나머지 40~60% 티키타카 대화·리액션 컷에는 "
            "`full_bleed_bg=false`(100% 깔끔한 순백 `#FFFFFF` 배경, 반쪽짜리 비네트 컷아웃 절대 금지!)를 선별 배합하세요."
        )
    elif background_style == "full_bleed":
        bg_directive = (
            "이번 화의 `background_style`은 `\"full_bleed\"`입니다. 모든 컷에 `full_bleed_bg=true`를 설정하고 "
            "각 박스 패널을 상하좌우 100% 풀-블리드 컬러 배경(말풍선 영역은 인물이 없는 트인 배경 풍경)으로 채우세요."
        )
    else:
        bg_directive = (
            "이번 화의 `background_style`은 `\"clean_white\"`입니다. 모든 컷에 `full_bleed_bg=false`를 설정하고 "
            "100% 깔끔한 순백 `#FFFFFF` 배경(최소 만화 이펙트만, 반쪽짜리 비네트 컷아웃 절대 금지!)으로 작성하세요."
        )

    return (
        f"{V4_WRITER_SYSTEM_RULES}\n\n"
        f"{layouts_ref}\n\n"
        f"{lore_guidance}\n\n"
        f"{cast_bible}\n\n"
        f"=== 각색 대상 포에버갤 개념글 (V4 5막 10~14컷) ===\n"
        f"- 예정 화수: EP.{episode_number}\n"
        f"- 게시글 번호: #{post.post_no}\n"
        f"- 원문 URL: {post.url}\n"
        f"- 원문 제목 (100% 그대로 유지): {post.title.strip()}\n"
        f"- 작성자: {post.author} | 추천: {post.recommends} | 댓글: {post.comments_count}\n"
        f"- 본문:\n{post.body or '(본문 텍스트 없음 — 제목의 펀치라인을 5막 던전 상황극으로 풀어내세요)'}\n\n"
        f"- 주요 댓글 (메타 해설 금지! 웃긴 포인트만 캐릭터 대사·상황극 소재로 흡수):\n{comments_block}\n\n"
        f"[배경 리듬 지정] {bg_directive}\n\n"
        f"위 JSON 스키마(`EpisodeScript`)에 정확히 맞춰 출력하세요. "
        f"`layout_mode`는 \"v4_five_act\", `background_style`은 \"{background_style}\", "
        f"`episode_number`는 {episode_number}, "
        f"`source_post_no`는 \"{post.post_no}\", "
        f"`source_title`은 원문 제목 100% 그대로인 {json.dumps(post.title.strip(), ensure_ascii=False)}, "
        f"`source_url`은 \"{post.url}\" 로 기입하고, `acts`에 정확히 5개 막(총 10~14컷, 연속 동일 `layout_id` 금지, 최소 3종 이상 레이아웃 사용)을 작성하세요."
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
    """Audit an `EpisodeScript` (classic 2-tier OR V4 5-act) against all WoW Forever rules.

    Catches:
    - Classic cut count outside 4–6, or V4 cut count outside 10–14 / invalid 5-act layout structure
    - V4 layout diversity violations (consecutive identical `layout_id` or < 3 distinct layouts)
    - Missing mandatory wordless freeze-frame cut (`wordless=True`)
    - Cast sprawl (> 4 unique cast in classic, > 5 unique cast in V4 5-man party mode)
    - Parenthetical or multi-line dual-speaker hacks inside one bubble (e.g. `(도적: ...)`)
    - Modern real-world phrasing (e.g. `119`, `구급차`, `카톡`, `편의점`)
    - Real player nicknames / guild tags (`<Guild>`) / forbidden community (`인벤`)
    - Outdoor faction/zone hearthstone mismatch (e.g. Tauren Druid claiming Dolanaar)
    - Tanking Warrior/Paladin wielding a 2H weapon with no shield
    - Literal anti-hallucination visual prompt traps (juice box, prison chains)
    """
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
        cut_count_ok = 4 <= cut_count <= 6
        if not cut_count_ok:
            errors.append(f"Cut count must be 4–6, got {cut_count}.")

    wordless_cuts = [cut.cut_index for cut in cuts if cut.wordless]
    act_has_wordless = (not act_cuts) or any(cut.wordless for cut in act_cuts)
    wordless_cut_ok = (len(wordless_cuts) >= 1) and act_has_wordless
    if not wordless_cut_ok:
        errors.append("Missing mandatory wordless freeze-frame cut (wordless=True).")

    # Cast sprawl check (<= 4 core cast in classic, <= 5 party members in V4)
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

    # Check subtitle & V4 act titles
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

    # Audit every cut in `cuts`, plus any mutated cut present only in `script.acts`
    seen_cut_obj_ids = {id(c) for c in cuts}
    cuts_to_inspect: list[ComicCut] = list(cuts)
    for c in act_cuts:
        if id(c) not in seen_cut_obj_ids:
            cuts_to_inspect.append(c)

    for cut in cuts_to_inspect:
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
    """Ensure canonical Draft C names and exact source post metadata on classic or V4 scripts."""
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
        background_style=background_style or "selective_mix",
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


def build_dry_run_v4_script(
    post: GalleryPost,
    episode_number: int,
    *,
    background_style: BackgroundStyle = "clean_white",
) -> EpisodeScript:
    """Build a deterministic offline V4 5-act (13-cut, 5 distinct variable layouts) Draft C script.

    Uses the 5 distinct layouts (`open_top_split_bottom`, `diagonal_tempo_2cut`,
    `split_top_wide_bottom`, `impact_freeze_2cut`, `wide_reaction_wide` -> 3+2+3+2+3 = 13 cuts),
    updated 3-view turnaround descriptions, Clean Hand rules, and cinematic angle diversity.
    """
    verbatim_title = post.title.strip()
    dialogue_hook = verbatim_title or f"개념글 #{post.post_no}"
    snippet = (
        (post.body.strip().splitlines()[0][:24] + "...")
        if post.body.strip()
        else dialogue_hook[:24]
    )

    acts = [
        ActPage(
            act_number=1,
            act_title="발단 — 던전 앞 수상한 분위기",
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
                    dialogue=f"저기요...\n'{dialogue_hook[:16]}'\n진짜 이 파티 괜찮아요?",
                    wordless=False,
                    visual_prompt=(
                        "Dynamic over-the-shoulder diagonal shot in crisp 2.5-head chibi style: "
                        "foreground back shoulder of Orc Warrior chibi girl in vibrant green orc plush hood "
                        "and red warrior cape with steel shield and 1H sword ready; background fair-skinned "
                        "Night Elf Priest chibi girl with lavender half-up ponytail, golden Elune crescent "
                        "forehead tiara, luminous glowing silver eyes, purple-and-gold Priestess vestments, "
                        "waist mini Holy Prayer Book and golden Rosary (Holy Cross staff strapped across back) "
                        "clasping her hands nervously. Pure solid white #FFFFFF background, no text, no speech bubbles."
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
                    dialogue="걱정 마!\n전탱 방패 단단하니까\n믿고 따라와!",
                    wordless=False,
                    visual_prompt=(
                        "Low-angle heroic comedic shot looking up at fair-skinned Orc Warrior chibi girl "
                        "in vibrant green orc plush hood puffing her chest out proudly while holding a "
                        "sturdy steel kite shield and compact 1H sword for tanking. Pure solid white #FFFFFF "
                        "background, generous top pure-white headroom, no text, no speech bubbles."
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
                    dialogue="헤헤, 탱님만\n믿고 빡딜\n준비 완료요!",
                    wordless=False,
                    visual_prompt=(
                        "Side-profile crouching pose of petite Gnome Rogue chibi girl with blonde-pink-blue "
                        "twin pigtails (zero hairpins), forehead green steampunk goggles, and sly fang grin "
                        "peeking mischievously from behind a wooden dungeon crate with daggers sheathed at belt. "
                        "Pure solid white #FFFFFF background, generous top pure-white headroom, no text, no speech bubbles."
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
                    dialogue=f"어어 잠깐!\n{snippet}\n저 칼소멸 먼저 쓸게요!",
                    wordless=False,
                    visual_prompt=(
                        "High-angle chaotic action shot: Orc Warrior chibi girl tanking with sturdy steel "
                        "kite shield and 1H sword bracing against comedic cartoon dungeon mob silhouettes "
                        "while Gnome Rogue chibi girl (zero hairpins, green goggles) sprints away sideways "
                        "in a swirling cartoon Vanish smoke puff. Pure solid white #FFFFFF background, "
                        "no text, no speech bubbles."
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
                    dialogue="잠깐만요, 보스 잡히기도 전에\n주사위 창부터 열리는데요?!",
                    wordless=False,
                    visual_prompt=(
                        "Dutch-tilt dynamic reaction shot: Left, fair-skinned Skyborne Mage chibi girl with "
                        "sky-blue high side-ponytail, pointed elf ears, oversized tilted royal-blue wizard hat "
                        "with tiny smiling cloud-wing feather badge, cloud-trimmed blue capelet, waist Polymorph "
                        "Sheep keychain charm, and sky-blue crystal staff strapped on back pointing wide-eyed; "
                        "Right, fair-skinned Night Elf Priest in purple vestments clutching her brow in disbelief. "
                        "Pure solid white #FFFFFF background, no text, no speech bubbles."
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
                    dialogue="힐러 마나 0%인데\n지금 입찰부터\n누르시는 거예요?!",
                    wordless=False,
                    visual_prompt=(
                        "Dramatic tilted close-up of fair-skinned Night Elf Priest chibi girl with lavender "
                        "half-up hair, golden Elune crescent forehead tiara, glowing silver eyes, purple Priestess "
                        "capelet, waist mini Holy Prayer Book and golden Rosary (Holy Cross staff stowed on back) "
                        "gesturing frantically with exasperated healer glare. Pure solid white #FFFFFF background, "
                        "generous top pure-white headroom, no text, no speech bubbles."
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
                    dialogue="이중특성으로\n언젠가 쓸 수도\n있지 않을까?!",
                    wordless=False,
                    visual_prompt=(
                        "Cheeky low-angle waist-up shot of fair-skinned Orc Warrior chibi girl in green orc "
                        "hood giving an overly innocent grin while cradling her sturdy steel kite shield and "
                        "1H sword with cartoon sweat drops. Pure solid white #FFFFFF background, generous top "
                        "pure-white headroom, no text, no speech bubbles."
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
                    dialogue="어차피 주사위는 공정하잖아요!\n먼저 굴리는 사람이 임자지!",
                    wordless=False,
                    visual_prompt=(
                        "Over-the-shoulder reveal shot past Skyborne Mage's cloud-trimmed blue capelet toward "
                        "Gnome Rogue chibi girl (zero hairpins, daggers sheathed at belt) leaning over an open "
                        "wooden dungeon loot chest tossing a chunky 6-sided white-and-gold loot die showing ONLY "
                        "round black dot pips (strictly zero digits, zero letters). Pure solid white #FFFFFF "
                        "background, no text, no speech bubbles."
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
                    dialogue="와 대박! 올입찰 100 떴다!\n수고하셨습니다, 귀환석 탈게요!",
                    wordless=False,
                    visual_prompt=(
                        "Dynamic Dutch-tilt slapstick leap: Gnome Rogue chibi girl (zero hairpins, green goggles, "
                        "daggers sheathed) leaping gleefully holding a glowing cyan spiral-rune Hearthstone while "
                        "Orc Warrior tank (steel shield and 1H sword) lunges sideways in total panic with flying "
                        "dust puffs. Pure solid white #FFFFFF background, no text, no speech bubbles."
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
                        "Massive centered dramatic chest-up close-up freeze-frame of fair-skinned Skyborne Mage "
                        "chibi girl with sky-blue high side-ponytail, perky pointed elf ears, oversized tilted "
                        "royal-blue wizard hat with tiny smiling cloud-wing feather badge, cloud-trimmed blue "
                        "capelet, and waist Polymorph Sheep keychain charm; tiny trembling shocked pinpoint "
                        "pupils, jaw dropped wide open, comedic cartoon ghost soul floating out of her mouth "
                        "in pure disbelief. Pure solid white #FFFFFF background, no text, no speech bubbles."
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
                    dialogue="마나 물약도 다 마셨는데...\n영혼의 치유사 면담 각이네요.",
                    wordless=False,
                    visual_prompt=(
                        "High-angle comedic despair shot looking down at fair-skinned Night Elf Priest chibi "
                        "girl in purple vestments (golden Elune crescent tiara, waist mini Holy Prayer Book & "
                        "golden Rosary, Holy Cross staff resting beside her) kneeling slumped on the white floor "
                        "beside an empty fantasy corked glass mana flask. Pure solid white #FFFFFF background, "
                        "no text, no speech bubbles."
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
                    dialogue="다음 파티도 화이팅!\n저는 먼저 여관으로 갑니다!",
                    wordless=False,
                    visual_prompt=(
                        "Back-view action shot of petite Gnome Rogue chibi girl (zero hairpins, daggers sheathed "
                        "at belt) seen from behind sprinting into a bright swirling cyan Hearthstone teleport "
                        "vortex while looking back over her shoulder waving cheekily. Pure solid white #FFFFFF "
                        "background, no text, no speech bubbles."
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
                    dialogue="다음엔 파티찾기 포에버에서\n주사위 룰부터 정하고 가자...",
                    wordless=False,
                    visual_prompt=(
                        "Side-profile exhausted aftermath shot: Orc Warrior chibi girl (green orc hood, resting "
                        "her sturdy steel shield and 1H sword) and Skyborne Mage chibi girl (sky-blue high "
                        "side-ponytail, tilted royal-blue wizard hat with cloud-wing badge, waist Polymorph Sheep "
                        "keychain charm, crystal staff on back) slumping side-by-side staring blankly into space "
                        "with cartoon sweat drops. Pure solid white #FFFFFF background, no text, no speech bubbles."
                    ),
                    tail_target="left",
                ),
            ],
        ),
    ]

    # Apply per-cut full_bleed_bg rhythm based on background_style:
    # - full_bleed: every cut full_bleed_bg=True
    # - selective_mix: ~50% key establishing/action/reveal/wordless/ending cuts (7/13 = 53.8%)
    #   set full_bleed_bg=True; dialogue-reaction ping-pong cuts stay crisp #FFFFFF (False).
    # - clean_white: every cut full_bleed_bg=False
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
                        "Pure solid white #FFFFFF background, generous top pure-white headroom, no text, no speech bubbles.",
                        "100% edge-to-edge full-bleed stone dungeon background with unobstructed upper cavern ceiling for speech bubble, no text, no speech bubbles.",
                    ).replace(
                        "Pure solid white #FFFFFF background, no text, no speech bubbles.",
                        "100% edge-to-edge full-bleed stone dungeon background with unobstructed upper scenery for speech bubble, no text, no speech bubbles.",
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
