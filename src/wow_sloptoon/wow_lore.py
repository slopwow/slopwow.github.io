"""World of Warcraft: Forever (2026 Classic+) Lore, Dungeon, Class & Visual Fidelity Bible.

Provides concise domain knowledge for both:
- `writer.py`: accurate WoW Forever systems, dungeons, faction-locked outdoor zones,
  class/spec roles, WoW Forever custom item tooltips, and authentic Korean WoW phrasing.
- `artist.py`: compact (<= 300-500 char) visual fidelity hints covering Clean Hands,
  tank shields, ring-mesh mail armor, corked glass flasks, dot-pip loot dice, and
  unified 2-to-2.5 head cute SD proportions across all props, mobs, and NPCs.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Literal


@dataclass(frozen=True)
class DungeonInfo:
    """Canonical WoW Forever or Classic 5-man / 10-man dungeon reference."""

    name: str
    level_range: str
    region: str
    category: Literal["wow_forever_new", "classic"]
    signature_notes: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class ClassVisualSpec:
    """Equipment and spell/effect visual guidelines for a WoW Forever playable class."""

    wow_class: str
    english_class: str
    role_specs: str
    equipment_rules: str
    spell_visual_cues: str
    keywords: tuple[str, ...]
    tank_shield_required: bool = False


@dataclass(frozen=True)
class AntiHallucinationRule:
    """Visual/narrative fidelity rule learned from episode audits."""

    key: str
    title: str
    korean_triggers: tuple[str, ...]
    english_triggers: tuple[str, ...]
    writer_note: str
    artist_note: str


# ---------------------------------------------------------------------------
# 1. WoW Forever (2026 Classic+) Unique Systems & Faction Rules
# ---------------------------------------------------------------------------

WOW_FOREVER_CORE_SYSTEMS: str = """[월드 오브 워크래프트: 포에버 (2026 Classic+) 핵심 고증]
- **레벨 60 클래식+**: 신규 종족 스카이본(Zephras Isle, 공중 활강 Walk on Air; 얼라 마법사·호드 주술사), 신규 조합 6종(언데드 성기사·오크 마법사·트롤 흑마법사·인간 사냥꾼·드워프 주술사·노움 사제), 40레벨 이중 특성(Dual Spec), 침낭퀘(Lv.14+ 야영 3분 휴식 경험치 버프), 계정 공유 Legacy, 10인 공격대, FindParty Forever / MessageQueue Forever.
- **진영 규칙**: 인던·공격대는 얼라+호드 진영 통합 가능. 야외 필드·대도시·귀환석은 진영 엄격 분리(얼라: 스톰윈드·아이언포지·다르나서스·돌라나르·서부 몰락지대·황금골 / 호드: 오그리마·언더시티·썬더 블러프·불모의 땅·십자로·듀로타·티리스팔 / 중립: 제프라스 섬·무법항·가젯잔·톱니항).
- **포에버 커스텀 스탯 우선 & 현대어 금지**: 원글/스샷의 포에버 실스탯을 바닐라 DB보다 우선 반영. 119·112·구급차·경찰·카톡·편의점·택시 대신 무덤 이동·영혼의 치유사·경비병·귓말/파티창·여관 주인·와이번/그리핀 사용."""


# ---------------------------------------------------------------------------
# 2. All 9 New WoW Forever 5-Man Dungeons + Iconic Classic Dungeons
# ---------------------------------------------------------------------------

WOW_FOREVER_NEW_DUNGEONS: tuple[DungeonInfo, ...] = (
    DungeonInfo(
        name="영주의 전당",
        level_range="13–18",
        region="저렙 신규 지역",
        category="wow_forever_new",
        signature_notes="와우 포에버 신규 저렙 5인 던전(13~18). 초반 탱·힐·뉴비 파티 에피소드 단골 무대.",
        keywords=("영주의 전당", "영주전당", "영주 전당"),
    ),
    DungeonInfo(
        name="로데론의 폐허",
        level_range="15–20",
        region="티리스팔 숲 / 로데론",
        category="wow_forever_new",
        signature_notes="와우 포에버 신규 5인 던전(15~20). 폐허가 된 로데론 왕궁·지하 구역 컨셉.",
        keywords=("로데론의 폐허", "로데론 폐허", "로폐"),
    ),
    DungeonInfo(
        name="발굴 현장",
        level_range="24–29",
        region="중저렙 유적지",
        category="wow_forever_new",
        signature_notes="와우 포에버 신규 5인 던전(24~29). 고대 유적 발굴지·골렘/트로그/탐험가 컨셉.",
        keywords=("발굴 현장", "발굴현장"),
    ),
    DungeonInfo(
        name="달라란",
        level_range="28–33",
        region="알터랙 / 은빛소나무 경계",
        category="wow_forever_new",
        signature_notes="와우 포에버 신규 5인 던전(28~33). 마법 도시 달라란 구역 비전 마법사 컨셉.",
        keywords=("달라란", "달라란 인던", "달라란 던전"),
    ),
    DungeonInfo(
        name="가라앉은 도시",
        level_range="35–40",
        region="수몰 유적",
        category="wow_forever_new",
        signature_notes="와우 포에버 신규 5인 던전(35~40). 수몰된 고대 도시 탐험 및 중렙 파밍 구간.",
        keywords=("가라앉은 도시", "가라앉은도시"),
    ),
    DungeonInfo(
        name="크롤도크 보루",
        level_range="40–45",
        region="강물터",
        category="wow_forever_new",
        signature_notes=(
            "와우 포에버 신규 5인 던전(40~45, 강물터). 주문력 사슬 허리띠 '속박의 사슬'(Chain of Binding = "
            "사슬 갑옷 허리띠!)과 치유 반지 '두목의 고리' 등 커스텀 하이브리드 템 분쟁이 잦은 명소."
        ),
        keywords=("크롤도크 보루", "크롤도크", "강물터", "속박의 사슬", "두목의 고리"),
    ),
    DungeonInfo(
        name="알카즈 감옥",
        level_range="48–53",
        region="알카즈섬 (먼지진흙 습지대)",
        category="wow_forever_new",
        signature_notes="와우 포에버 신규 5인 던전(48~53, 알카즈섬). 후반부 육성 구간 정예 감옥 던전.",
        keywords=("알카즈 감옥", "알카즈감옥", "알카즈섬", "알카즈"),
    ),
    DungeonInfo(
        name="검은아귀 요새",
        level_range="55–60",
        region="만렙 진입 요새",
        category="wow_forever_new",
        signature_notes="와우 포에버 신규 만렙 진입 5인 던전(55~60). 프리비스(Pre-BiS) 파밍 격전지.",
        keywords=("검은아귀 요새", "검은아귀요새", "검은아귀"),
    ),
    DungeonInfo(
        name="구체자의 정원",
        level_range="58–60",
        region="만렙 최상위 구역",
        category="wow_forever_new",
        signature_notes="와우 포에버 신규 최상위 5인 던전(58~60). 만렙 최종 5인 파밍·고난도 패턴 던전.",
        keywords=("구체자의 정원", "구체자 정원", "구체자"),
    ),
)

CLASSIC_DUNGEONS: tuple[DungeonInfo, ...] = (
    DungeonInfo(
        name="성난불길 협곡",
        level_range="13–18",
        region="오그리마 지하",
        category="classic",
        signature_notes="오그리마 지하 용암 동굴 초보 인던.",
        keywords=("성난불길", "성불"),
    ),
    DungeonInfo(
        name="죽음의 폐광",
        level_range="17–26",
        region="서부 몰락지대 (얼라이언스 지역)",
        category="classic",
        signature_notes="데피아즈단 밴클리프와 해적선 광산 인던.",
        keywords=("죽음의 폐광", "죽폐", "폐광", "밴클리프"),
    ),
    DungeonInfo(
        name="통곡의 동굴",
        level_range="17–24",
        region="불모의 땅 (호드 지역)",
        category="classic",
        signature_notes="길 잃기 악명 높은 송곳니 드루이드 동굴, 점프 구간 추락 참사 단골.",
        keywords=("통곡의 동굴", "통곡", "통동"),
    ),
    DungeonInfo(
        name="그림자송곳니 성채",
        level_range="22–30",
        region="은빛소나무 숲",
        category="classic",
        signature_notes="아루갈과 늑대인간 성채 인던.",
        keywords=("그림자송곳니", "그송", "성채", "아루갈"),
    ),
    DungeonInfo(
        name="검은심연의 나락",
        level_range="24–32",
        region="잿빛 골짜기",
        category="classic",
        signature_notes="수중 구간·나가·황혼의 망치단 인던.",
        keywords=("검은심연", "검심"),
    ),
    DungeonInfo(
        name="스톰윈드 지하감옥",
        level_range="24–32",
        region="스톰윈드 (얼라이언스 대도시)",
        category="classic",
        signature_notes="스톰윈드 도심 속 데피아즈단 폭동 감옥.",
        keywords=("지하감옥", "지감", "스톰윈드 감옥"),
    ),
    DungeonInfo(
        name="놈리건",
        level_range="29–38",
        region="던 모로",
        category="classic",
        signature_notes="낙하산 점프 구간·펫 미해제 전멸 애드·기계 함정·천장 압사 참사 단골 인던.",
        keywords=("놈리건", "놈리", "멕기니어"),
    ),
    DungeonInfo(
        name="가시덩굴 우리",
        level_range="29–38",
        region="불모의 땅 남부",
        category="classic",
        signature_notes="가시멧돼지 족장 찰가 인던.",
        keywords=("가시덩굴 우리", "가시우리"),
    ),
    DungeonInfo(
        name="붉은십자군 수도원",
        level_range="26–45",
        region="티리스팔 숲",
        category="classic",
        signature_notes=(
            "묘지·도서관·무기고·예배당 4구역. 화이트메인의 모자, 삼위일체의 아뮬렛, 사서의 홀, "
            "정의의 망치, 폭풍의 눈(헤로드) 등 입찰 분쟁 최다 발생 성지."
        ),
        keywords=(
            "붉은십자군",
            "붉십",
            "수도원",
            "화이트메인",
            "헤로드",
            "삼위일체",
            "사서의 홀",
            "정의의 망치",
            "폭풍의 눈",
        ),
    ),
    DungeonInfo(
        name="가시덩굴 구릉",
        level_range="37–46",
        region="불모의 땅 남부",
        category="classic",
        signature_notes=(
            "언데드 스컬지 가시구릉. 모드레쉬의 이글거리는 눈(포에버 커스텀 스탯 주의!), "
            "냉기수호자 아므넨나르 드랍."
        ),
        keywords=("가시덩굴 구릉", "가시구릉", "구릉", "모드레쉬"),
    ),
    DungeonInfo(
        name="울다만",
        level_range="41–51",
        region="황야의 땅",
        category="classic",
        signature_notes="고대 티탄 유적·아카에다스. 렙차 심해 막넴 전멸 잦음.",
        keywords=("울다만", "아카에다스"),
    ),
    DungeonInfo(
        name="줄파락",
        level_range="42–46",
        region="타나리스",
        category="classic",
        signature_notes=(
            "트롤 피라미드 디펜스 명소. 한손검 '보호의 장트라제' + '무적의 상트라제'를 합쳐 "
            "에픽 양손검 '질풍의 술트라제'를 만드는 곳."
        ),
        keywords=("줄파락", "줄파", "장트라제", "상트라제", "술트라제"),
    ),
    DungeonInfo(
        name="마라우돈",
        level_range="46–55",
        region="잊혀진 땅",
        category="classic",
        signature_notes="보라·주황·공주 직행(홀) 루트. 검은바위 반지 파밍 명소.",
        keywords=("마라우돈", "마라", "공주직"),
    ),
    DungeonInfo(
        name="가라앉은 사원",
        level_range="50–56",
        region="슬픔의 늪",
        category="classic",
        signature_notes="아탈학카르 신전. 2층 미로 길찾기·에라니쿠스 애드 단골.",
        keywords=("가라앉은 사원", "아탈학카르", "가사원"),
    ),
    DungeonInfo(
        name="검은바위 나락",
        level_range="52–60",
        region="불타는 평원 / 이글거리는 협곡",
        category="classic",
        signature_notes="초대형 드워프 도시 던전. 투기장·주점·황제직·심판의 손길(심손) 파밍.",
        keywords=("검은바위 나락", "검바나", "나락", "심손", "황제직", "투기장"),
    ),
    DungeonInfo(
        name="검은바위 첨탑",
        level_range="55–60",
        region="검은바위 산",
        category="classic",
        signature_notes=(
            "하층(첨하)과 상층(첨상 10인). 상층 대족장 렌드 블랙핸드가 한손 에픽 단검 "
            "'필살의 비수(필비)'를 드랍하며, 드라키사스·제드 런으로 유명."
        ),
        keywords=("검은바위 첨탑", "첨상", "첨하", "상층", "하층", "렌드", "필살의 비수", "필비", "드라키사스"),
    ),
    DungeonInfo(
        name="혈투의 전장",
        level_range="55–60",
        region="페랄라스",
        category="classic",
        signature_notes="동·서·북쪽 3지구. 공물런(북쪽)과 도서관 퀘스트 명소.",
        keywords=("혈투의 전장", "혈장", "공물런", "혈동", "혈서", "혈북"),
    ),
    DungeonInfo(
        name="스트라솔름",
        level_range="58–60",
        region="동부 역병지대",
        category="classic",
        signature_notes="정문(십자군)과 후문(남작 리븐데어 45분 타임어택·해골마).",
        keywords=("스트라솔름", "스트", "남작", "리븐데어", "정문", "후문"),
    ),
    DungeonInfo(
        name="스칼로맨스",
        level_range="58–60",
        region="서부 역병지대",
        category="classic",
        signature_notes="강령술 학원. 간들링(교장)과 어둠스승·방 6개 보스전.",
        keywords=("스칼로맨스", "스칼", "간들링"),
    ),
)

ALL_DUNGEONS: tuple[DungeonInfo, ...] = WOW_FOREVER_NEW_DUNGEONS + CLASSIC_DUNGEONS


# ---------------------------------------------------------------------------
# 3. Faction-Locked Outdoor Zones & Capitals
# ---------------------------------------------------------------------------

ALLIANCE_ZONES: tuple[str, ...] = (
    "스톰윈드",
    "아이언포지",
    "다르나서스",
    "돌라나르",
    "텔드랏실",
    "서부 몰락지대",
    "감시의 언덕",
    "골드샤이어",
    "황금골",
    "엘윈 숲",
    "붉은마루 산맥",
    "그늘숲",
    "모단 호수",
    "던 모로",
    "아우버다인",
    "어둠해안",
    "테라모어",
    "stormwind",
    "ironforge",
    "darnassus",
    "dolanaar",
    "westfall",
    "goldshire",
)

HORDE_ZONES: tuple[str, ...] = (
    "오그리마",
    "언더시티",
    "썬더 블러프",
    "불모의 땅",
    "십자로",
    "크로스로드",
    "듀로타",
    "칼바위 언덕",
    "티리스팔 숲",
    "브릴",
    "멀고어",
    "블러드후프 마을",
    "은빛소나무 숲",
    "타렌 밀농장",
    "스토나드",
    "orgrimmar",
    "undercity",
    "thunder bluff",
    "barrens",
    "crossroads",
    "durotar",
)

NEUTRAL_ZONES: tuple[str, ...] = (
    "제프라스 섬",
    "zephras isle",
    "무법항",
    "가젯잔",
    "톱니항",
    "눈망루 마을",
    "세나리온 요새",
    "희망의 빛 예배당",
    "booty bay",
    "gadgetzan",
    "ratchet",
    "everlook",
)

FACTION_ZONES: dict[str, tuple[str, ...]] = {
    "Alliance": ALLIANCE_ZONES,
    "Horde": HORDE_ZONES,
    "Neutral": NEUTRAL_ZONES,
}


# ---------------------------------------------------------------------------
# 4. Class / Spec Accurate Visual Equipment & Spell Cues
# ---------------------------------------------------------------------------

CLASS_SPEC_VISUAL_RULES: dict[str, ClassVisualSpec] = {
    "전사": ClassVisualSpec(
        wow_class="전사",
        english_class="Warrior",
        role_specs="전탱/방전(Protection Tank), 무전(Arms 2H), 분전(Fury Dual-Wield)",
        equipment_rules=(
            "전탱/방전(탱커) 역할일 때는 반드시 한손 무기(한손검/한손도끼) + 튼튼한 방패를 착용. "
            "무전은 양손 도끼/대검, 분전은 쌍수 한손 무기."
        ),
        spell_visual_cues="Shield Block metallic glow, Taunt red shockwave, Charge motion streak.",
        keywords=("전사", "전탱", "방전", "무전", "분전", "방패", "오크 전사", "warrior", "tank"),
        tank_shield_required=True,
    ),
    "성기사": ClassVisualSpec(
        wow_class="성기사",
        english_class="Paladin",
        role_specs="보기(Protection Tank), 징기(Retribution 2H), 신기(Holy Healer)",
        equipment_rules=(
            "보기(보호 탱커)는 반드시 한손 둔기/검 + 황금빛 방패 착용. "
            "징기는 양손 황금 전투망치, 신기는 한손 치유 둔기 + 보조장비/방패."
        ),
        spell_visual_cues="Golden Consecration rune glow, translucent golden Divine Shield bubble, Holy Light beams.",
        keywords=("성기사", "기사", "보기", "징기", "신기", "무적귀환", "언데드 성기사", "paladin"),
        tank_shield_required=True,
    ),
    "도적": ClassVisualSpec(
        wow_class="도적",
        english_class="Rogue",
        role_specs="암살/전투/잠행 근접 딜러",
        equipment_rules="단검(쌍수 단검) 또는 한손 도검만 사용. 전리품·주사위를 집을 때는 기본 단검을 허리에 수납.",
        spell_visual_cues="Vanish smoke puff & stealth shimmer, green poison droplets, Sprint speed lines.",
        keywords=("도적", "노도", "소멸", "칼소멸", "은신", "단검", "노움 도적", "rogue", "vanish"),
    ),
    "사냥꾼": ClassVisualSpec(
        wow_class="사냥꾼",
        english_class="Hunter",
        role_specs="야수/사격/생존 원거리 딜러",
        equipment_rules="화승총(wooden blunderbuss gun) 또는 활 + 고정 동행 아기 곰 펫. 근접 무기는 등에 수납.",
        spell_visual_cues="Cute baby brown bear cub beside her, flat sprawled Feign Death flop, icy Freezing Trap crystal.",
        keywords=("사냥꾼", "냥꾼", "드냥", "죽척", "죽은 척", "펫", "야수", "드워프 사냥꾼", "hunter", "feign"),
    ),
    "마법사": ClassVisualSpec(
        wow_class="마법사",
        english_class="Mage",
        role_specs="냉법/화법/비법 원거리 딜러 & 물빵·포탈 보급",
        equipment_rules="수정구 지팡이; 물빵 보급 장면에서만 코르크 유리 마나 물병과 둥근 빵을 들고 그 외엔 지팡이 수납.",
        spell_visual_cues="Polymorph fluffy white cartoon sheep, swirling blue Arcane Portal, crystalline Ice Block.",
        keywords=("마법사", "법사", "냉법", "화법", "비법", "물빵", "변이", "양변", "포탈", "차원문", "스카이본", "mage", "polymorph"),
    ),
    "흑마법사": ClassVisualSpec(
        wow_class="흑마법사",
        english_class="Warlock",
        role_specs="고흑/악흑/파흑 원거리 딜러 & 소환·생석",
        equipment_rules=(
            "작은 보라 마법서/영혼의 조각 + 고정 동행 보라 공허방랑자(Voidwalker). "
            "(빨간 임프 인형은 소지하지 않음!)"
        ),
        spell_visual_cues="Cute floating purple Voidwalker companion, floating violet soul-shard crystals, glowing green Healthstone, purple summoning rift.",
        keywords=("흑마법사", "흑마", "보이드", "공허방랑자", "생석", "생명석", "영혼의 조각", "소환", "인간 흑마법사", "warlock"),
    ),
    "사제": ClassVisualSpec(
        wow_class="사제",
        english_class="Priest",
        role_specs="신사/수사 힐러, 암사 딜러",
        equipment_rules="황금 십자 지팡이 + 허리 미니 성서 & 황금 묵주; 두 손 제스처/전리품 시 지팡이 수납.",
        spell_visual_cues="Golden Power Word: Shield bubble, golden-white healing sparkles, purple Shadowform aura.",
        keywords=("사제", "신사", "수사", "암사", "힐러", "보호막", "영혼", "부활", "나이트엘프 사제", "priest"),
    ),
    "주술사": ClassVisualSpec(
        wow_class="주술사",
        english_class="Shaman",
        role_specs="복술 힐러, 정술 원딜, 고술 근딜",
        equipment_rules="한손 둔기/도끼 + 방패(정술/복술) 또는 양손/쌍수(고술), 바닥에 세우는 나무 토템.",
        spell_visual_cues="Carved wooden elemental totems, crackling blue Chain Lightning arcs, golden Reincarnation burst.",
        keywords=("주술사", "술사", "복술", "정술", "고술", "토템", "윤회", "연번", "질풍", "트롤 주술사", "shaman", "totem"),
    ),
    "드루이드": ClassVisualSpec(
        wow_class="드루이드",
        english_class="Druid",
        role_specs="회드 힐러, 수드/야탱 탱커, 야딜 근딜, 조드 원딜",
        equipment_rules="나뭇잎 돋은 나무 지팡이; 변신 개그 시 귀여운 SD 곰/표범/부엉이 폼 연출 가능.",
        spell_visual_cues="Cute SD Bear/Cat Form puffs, cyan-teal Innervate mana stream, swirling green nature leaves.",
        keywords=("드루이드", "드루", "회드", "수드", "야드", "조드", "야탱", "자극", "변신", "타우렌 드루이드", "druid", "innervate"),
    ),
}


# ---------------------------------------------------------------------------
# 5. Concise Visual Fidelity Rules (Positive, Zero Bloat)
# ---------------------------------------------------------------------------

VISUAL_ANTI_HALLUCINATION_RULES: tuple[AntiHallucinationRule, ...] = (
    AntiHallucinationRule(
        key="mail_armor",
        title="사슬 방어구 (Mail Armor = 링메일 갑옷)",
        korean_triggers=("사슬", "속박의 사슬", "허리띠", "갑옷", "쇠사슬"),
        english_triggers=("chain", "mail", "waist belt", "belt", "hauberk", "binding"),
        writer_note=(
            "와우 '사슬(Mail)' 장비(예: 속박의 사슬)는 중세 링메일 갑옷입니다. "
            "영문 `visual_prompt`에 'silver interlocking ring-mesh mail-armor belt/tunic'으로 묘사하세요."
        ),
        artist_note="Mail gear = silver ring-mesh medieval armor belt/tunic.",
    ),
    AntiHallucinationRule(
        key="fantasy_drinks",
        title="판타지 음료·물약 (코르크 유리병·나무잔)",
        korean_triggers=("멜론 주스", "주스", "물빵", "물약", "마나 물", "음료", "마나물약", "치유물약", "물 좀"),
        english_triggers=("juice", "melon", "drink", "potion", "flask", "water", "beverage", "mug", "vial"),
        writer_note=(
            "'상큼한 멜론 주스', 마나 물, 물약 등 모든 음료는 중세 판타지 코르크 마개 유리 물약병"
            "(corked glass flask) 또는 나무 머그잔(wooden tavern mug)으로 묘사하세요."
        ),
        artist_note="Drinks/potions = medieval corked glass flasks or wooden mugs.",
    ),
    AntiHallucinationRule(
        key="tank_shield",
        title="전탱·보기 탱커 방패 필수",
        korean_triggers=("전탱", "방전", "보기", "탱커", "탱킹", "방패", "보호 성기사", "방어 전사"),
        english_triggers=("tank", "tanking", "protection", "shield", "kite shield", "tower shield", "bulwark"),
        writer_note=(
            "오크 전사(전탱/방전)나 언데드 성기사(보기)가 탱커 역할이면 반드시 한손 무기 + 튼튼한 방패를 착용하세요."
        ),
        artist_note="Tank Warrior/Paladin = 1H weapon + sturdy fantasy shield.",
    ),
    AntiHallucinationRule(
        key="weapon_scale_clean_hands",
        title="한손 무기 크기 & Clean Hand Rule",
        korean_triggers=("한손", "단검", "장트라제", "상트라제", "필살의 비수", "필비", "비수", "한손검", "입찰", "전리품", "드랍"),
        english_triggers=("one-handed", "1h", "dagger", "shortblade", "broadsword", "sword", "loot", "weapon", "blade"),
        writer_note=(
            "한손검·단검은 2.5등신 SD 한 손에 맞는 아담한 크기로 묘사하고, 전리품·주사위를 들 땐 기본 무기를 등·허리에 수납하세요."
        ),
        artist_note="1H swords/daggers stay compact single-hand SD scale.",
    ),
    AntiHallucinationRule(
        key="loot_die",
        title="입찰 주사위 (점 눈금만)",
        korean_triggers=("주사위", "입찰", "차비", "굴림", "굴렸", "올굴림", "닌자"),
        english_triggers=("dice", "die", "roll", "need roll", "greed roll", "cube"),
        writer_note=(
            "주사위는 'chunky 6-sided white-and-gold cube with round dot pips only (no digits)'로 묘사하세요."
        ),
        artist_note="Loot die = 6-sided white-gold cube with round dot pips only (no digits).",
    ),
    AntiHallucinationRule(
        key="hearthstone",
        title="귀환석 (파란 소용돌이 룬석)",
        korean_triggers=("귀환석", "귀환", "무적귀환", "여관"),
        english_triggers=("hearthstone", "teleport", "recall", "swirl"),
        writer_note=(
            "귀환석은 푸른 소용돌이 룬이 빛나는 매끄러운 타원형 돌로 묘사하고, 반드시 캐릭터 진영 마을만 사용하세요."
        ),
        artist_note="Hearthstone = smooth oval stone with glowing cyan spiral rune.",
    ),
    AntiHallucinationRule(
        key="gold_pouch",
        title="골드 (가죽 주머니 + 금화)",
        korean_triggers=("골드", "분배금", "골팟", "수리비", "10골", "20골", "100골", "돈"),
        english_triggers=("gold", "coin", "pouch", "purse", "money"),
        writer_note="골드는 끈으로 묶은 갈색 가죽 주머니와 둥근 금화로 묘사하세요.",
        artist_note="Gold = tied brown leather pouch with round gold coins.",
    ),
    AntiHallucinationRule(
        key="sleeping_bag",
        title="침낭퀘 (중세 양모 침낭)",
        korean_triggers=("침낭", "침낭퀘", "야영", "휴식"),
        english_triggers=("sleeping bag", "bedroll", "camping", "camp"),
        writer_note="침낭은 가죽 끈이 달린 따뜻한 베이지·갈색 중세 누빔 양모 침낭으로 묘사하세요.",
        artist_note="Sleeping bag = warm quilted medieval wool bedroll with leather straps.",
    ),
    AntiHallucinationRule(
        key="wow_forever_tooltips",
        title="와우 포에버 커스텀 아이템 툴팁 우선 원칙",
        korean_triggers=("툴팁", "모드레쉬", "속박의 사슬", "두목의 고리", "주문력", "치유량", "옵션", "스탯"),
        english_triggers=("tooltip", "custom", "mordresh", "stats"),
        writer_note="원글 본문·스샷에 나온 포에버 실스탯을 바닐라 DB보다 최우선으로 반영하세요.",
        artist_note="No painted UI tooltip boxes inside raw art.",
    ),
)


# ---------------------------------------------------------------------------
# 6. Forbidden Modern Real-World Slang -> Authentic WoW Replacements
# ---------------------------------------------------------------------------

MODERN_SLANG_FORBIDDEN: tuple[tuple[str, str, str], ...] = (
    (r"(?<!\d)119(?!\d)", "119", "무덤 이동 / 영혼의 치유사"),
    (r"(?<!\d)112(?!\d)", "112", "경비병 불러"),
    (r"구급차", "구급차", "영혼의 치유사 / 부활"),
    (r"경찰서|경찰\s*불러", "경찰", "경비병 / 사사게"),
    (r"카카오톡|카톡", "카톡", "귓말 / 파티창 / 길드창"),
    (r"편의점", "편의점", "여관 주인 / 잡화 상인"),
    (r"택시", "택시", "와이번 / 그리핀 / 법사 차원문"),
    (r"배달의민족|배민", "배민", "우편함 / 법사 물빵 배달"),
)


# ---------------------------------------------------------------------------
# 7. Dynamic Guidance Builders for `writer.py` & `artist.py`
# ---------------------------------------------------------------------------

def _contains_any(text_lower: str, keywords: Iterable[str]) -> bool:
    return any(kw.lower() in text_lower for kw in keywords)


def detect_mentioned_dungeons(context_text: str) -> list[DungeonInfo]:
    """Return WoW Forever and Classic dungeons referenced in `context_text`."""
    lower = context_text.lower()
    matched: list[DungeonInfo] = []
    for dungeon in ALL_DUNGEONS:
        if _contains_any(lower, dungeon.keywords):
            matched.append(dungeon)
    return matched


def detect_mentioned_faction_zones(context_text: str) -> dict[str, list[str]]:
    """Return faction-locked outdoor zones/capitals mentioned in `context_text`."""
    lower = context_text.lower()
    found: dict[str, list[str]] = {"Alliance": [], "Horde": [], "Neutral": []}
    for faction, zones in FACTION_ZONES.items():
        for zone in zones:
            if zone.lower() in lower and zone not in found[faction]:
                found[faction].append(zone)
    return found


def build_wow_lore_guidance(context_text: str) -> str:
    """Build dynamic WoW Forever (2026 Classic+) lore & visual guidance for `writer.py`."""
    lower = (context_text or "").lower()
    sections: list[str] = [WOW_FOREVER_CORE_SYSTEMS]

    # 1. Matched dungeons
    dungeons = detect_mentioned_dungeons(lower)
    if dungeons:
        d_lines = ["[감지된 와우 포에버 / 클래식 던전 컨텍스트]"]
        for d in dungeons[:5]:
            badge = "포에버 신규 5인" if d.category == "wow_forever_new" else "클래식 인던"
            d_lines.append(f"- **{d.name}** ({badge}, Lv.{d.level_range}, {d.region}): {d.signature_notes}")
        sections.append("\n".join(d_lines))
    else:
        new_list = ", ".join(f"{d.name}({d.level_range})" for d in WOW_FOREVER_NEW_DUNGEONS)
        sections.append(
            "[와우 포에버 신규 5인 인던 9곳 참조]\n"
            f"- {new_list}\n"
            "- 클래식 대표 인던: 죽음의 폐광, 통곡의 동굴, 그림자송곳니 성채, 놈리건, 붉은십자군 수도원, "
            "가시덩굴 구릉, 울다만, 줄파락, 마라우돈, 가라앉은 사원, 검은바위 나락/첨탑, 혈투의 전장, 스트라솔름, 스칼로맨스."
        )

    # 2. Matched outdoor faction zones
    zone_hits = detect_mentioned_faction_zones(lower)
    zone_lines: list[str] = []
    if zone_hits["Alliance"]:
        zone_lines.append(
            f"- 얼라이언스 전용 야외/대도시 감지 ({', '.join(zone_hits['Alliance'][:4])}): "
            "해당 마을 귀환석·여관·퀘스트 주체는 얼라이언스/스카이본(상급 마법사) 캐스트만 배정하세요."
        )
    if zone_hits["Horde"]:
        zone_lines.append(
            f"- 호드 전용 야외/대도시 감지 ({', '.join(zone_hits['Horde'][:4])}): "
            "해당 마을 귀환석·여관·퀘스트 주체는 호드 캐스트만 배정하세요."
        )
    if zone_hits["Neutral"]:
        zone_lines.append(
            f"- 중립 지역 감지 ({', '.join(zone_hits['Neutral'][:4])}): "
            "얼라이언스·호드·스카이본 모두 출입 가능합니다."
        )
    if zone_lines:
        sections.append("[야외 지역 진영 일치 경고]\n" + "\n".join(zone_lines))

    # 3. Matched class/spec visual equipment & spell cues
    class_lines: list[str] = []
    for spec in CLASS_SPEC_VISUAL_RULES.values():
        if _contains_any(lower, spec.keywords):
            class_lines.append(
                f"- **{spec.wow_class}** ({spec.role_specs}): {spec.equipment_rules} "
                f"(스킬 연출: {spec.spell_visual_cues})"
            )
    if class_lines:
        sections.append("[감지된 직업·특성별 장비 및 스킬 고증]\n" + "\n".join(class_lines[:6]))

    # 4. Matched visual fidelity warnings
    matched_rules: list[AntiHallucinationRule] = []
    for rule in VISUAL_ANTI_HALLUCINATION_RULES:
        if _contains_any(lower, rule.korean_triggers) or _contains_any(lower, rule.english_triggers):
            matched_rules.append(rule)

    ah_lines = ["[시각 고증 수칙 (영문 visual_prompt 반영)]"]
    if matched_rules:
        for rule in matched_rules:
            ah_lines.append(f"- **{rule.title}**: {rule.writer_note}")
    else:
        ah_lines.extend([
            "- **탱커 방패 필수**: 전탱/보기 탱킹 장면은 한손 무기 + 방패 착용.",
            "- **사슬=링메일 갑옷 / 음료=판타지 유리병·나무잔**: 중세 판타지 소품으로만 묘사.",
            "- **Clean Hand & SD 비율**: 전리품/주사위/귀환석을 들 땐 기본 무기 수납, 주사위는 점 눈금만.",
        ])
    sections.append("\n".join(ah_lines))

    return "\n\n".join(sections)


def build_cut_visual_lore_hints(visual_prompt: str, characters: list[str]) -> str:
    """Build compact (<= 300-500 char) English WoW Forever visual fidelity facts for `artist.py`."""
    combined_lower = f"{visual_prompt or ''} {' '.join(characters)}".lower()

    base_parts: list[str] = [
        "PROPS: Clean hands (stow default weapon on back/belt when hands are busy); "
        "medieval WoW fantasy props in matching 2-to-2.5 head SD style."
    ]

    extras: list[str] = []
    added_keys: set[str] = set()
    for rule in VISUAL_ANTI_HALLUCINATION_RULES:
        if _contains_any(combined_lower, rule.korean_triggers) or _contains_any(combined_lower, rule.english_triggers):
            extras.append(rule.artist_note)
            added_keys.add(rule.key)

    has_tank_class = any(
        tok in combined_lower for tok in ("오크 전사", "언데드 성기사", "orc_warrior", "undead_paladin", "전탱", "보기")
    )
    if (
        has_tank_class
        and "tank_shield" not in added_keys
        and any(tok in combined_lower for tok in ("tank", "shield", "전탱", "방전", "보기", "탱커", "protection"))
    ):
        tank_rule = next(r for r in VISUAL_ANTI_HALLUCINATION_RULES if r.key == "tank_shield")
        extras.append(tank_rule.artist_note)

    spell_cue_triggers: tuple[tuple[tuple[str, ...], str], ...] = (
        (("polymorph", "sheep", "변이", "양변"), "Polymorph = cute fluffy white cartoon sheep."),
        (("vanish", "stealth", "소멸", "은신", "smoke"), "Vanish = crisp swirling smoke puff."),
        (("totem", "lightning", "토템", "번개", "reincarnation", "윤회"), "Shaman = wooden totem + blue lightning sparks."),
        (("holy bubble", "golden bubble", "divine shield", "power word", "보호막", "무적"), "Holy shield = translucent golden bubble aura."),
        (("feign death", "죽은 척", "죽척"), "Feign Death = sprawled flat on white floor with shut eyes."),
        (("portal", "차원문", "포탈", "summon", "소환"), "Portal = glowing arcane/violet rift (no letters)."),
        (("innervate", "bear form", "cat form", "자극", "곰 변신", "표범"), "Druid = green leaves or cute SD Bear/Cat form."),
    )
    for triggers, note in spell_cue_triggers:
        if _contains_any(combined_lower, triggers):
            extras.append(note)

    # Cap total length strictly within compact 300-420 char budget
    out = base_parts[0]
    for item in extras:
        candidate = f"{out} {item}"
        if len(candidate) > 380:
            break
        out = candidate
    return out


def find_modern_slang_violations(text: str) -> list[tuple[str, str]]:
    """Return list of `(matched_label, wow_replacement)` for modern real-world slang in `text`."""
    if not text:
        return []
    violations: list[tuple[str, str]] = []
    seen: set[str] = set()
    for pattern, label, replacement in MODERN_SLANG_FORBIDDEN:
        if label not in seen and re.search(pattern, text, flags=re.IGNORECASE):
            seen.add(label)
            violations.append((label, replacement))
    return violations
