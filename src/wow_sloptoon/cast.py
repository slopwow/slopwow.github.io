"""Official Draft C (시안 C 귀염뽀짝 미소녀 9종족×9직업) Cast Bible for wow-forever-sloptoon."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CastMember:
    """Canonical character definition for Draft C cute pop-gag cast."""

    id: str
    name: str
    race: str
    wow_class: str
    role_tag: str
    color_hex: str
    accent_hex: str
    personality: str
    visual_anchor: str
    aliases: tuple[str, ...]
    sheet_position: str


CAST_BIBLE: tuple[CastMember, ...] = (
    CastMember(
        id="orc_warrior",
        name="오크 전사",
        race="오크",
        wow_class="전사",
        role_tag="포갤 억까 근딜러",
        color_hex="#4CAF50",
        accent_hex="#C62828",
        personality=(
            "열혈 호탕 근딜러. 던전 억까나 미터기 논쟁이 터지면 도끼부터 들고 웃으며 "
            "돌진하는 포에버갤 대표 전사."
        ),
        visual_anchor=(
            "Cute anime chibi girl wearing a vibrant green plush orc animal-onesie hood "
            "with curved cream horns, tiny upturned fangs, piggy snout and pointed green ears "
            "on top of the hood; black high ponytail hair with bangs, bright crimson-red eyes, "
            "confident mischievous grin; spiky red shoulder pauldrons over silver plate armor, "
            "holding a chunky silver battle axe (top-left #1 on Draft C cast sheet)."
        ),
        aliases=(
            "오크 전사",
            "오크전사",
            "전사",
            "오전",
            "무전",
            "분전",
            "방전",
            "전탱",
            "orc_warrior",
            "orc warrior",
            "warrior",
        ),
        sheet_position="top-row-1",
    ),
    CastMember(
        id="undead_paladin",
        name="언데드 성기사",
        race="언데드",
        wow_class="성기사",
        role_tag="3시간 묵언수행 보기",
        color_hex="#9E9E9E",
        accent_hex="#F5B700",
        personality=(
            "3시간 던전에서도 말없이 탱킹하다가 마지막에 무심한 팩트 한 줄 명언을 남기고 "
            "사라지는 묵언수행 성기사."
        ),
        visual_anchor=(
            "Cute anime chibi girl wearing a round white cartoon skull hood/cap with dark eye "
            "sockets, chin-length silver-white bob hair with icy blue inner tips, deadpan "
            "half-lidded golden-yellow eyes with faint tired eye bags and stoic face; crisp "
            "white-and-gold paladin cloak with a cream neck bow ribbon, holding a shiny golden "
            "warhammer (top-row #2 on Draft C cast sheet)."
        ),
        aliases=(
            "언데드 성기사",
            "언데드성기사",
            "성기사",
            "기사",
            "보기",
            "징기",
            "신기",
            "언기사",
            "undead_paladin",
            "undead paladin",
            "paladin",
        ),
        sheet_position="top-row-2",
    ),
    CastMember(
        id="gnome_rogue",
        name="노움 도적",
        race="노움",
        wow_class="도적",
        role_tag="칼소멸 · 근딜 훈수꾼",
        color_hex="#FFC107",
        accent_hex="#FF4081",
        personality=(
            "위험하면 빛의 속도로 칼소멸 쓰고 혼자 살아남아 파티창에 깐족 훈수와 드립을 "
            "던지는 장난꾸러기 도적."
        ),
        visual_anchor=(
            "Petite energetic anime chibi girl with blonde twin pigtails fading into hot-pink "
            "and electric-blue tips, green-lensed steampunk aviator goggles on her forehead, "
            "cross and star hairpins, bright blue eyes, cheeky wide grin, black stealth mask "
            "pulled down below her chin; dark charcoal rogue cloak, dual glowing poison-green "
            "daggers (top-row #3 on Draft C cast sheet)."
        ),
        aliases=(
            "노움 도적",
            "노움도적",
            "도적",
            "노도",
            "도비",
            "gnome_rogue",
            "gnome rogue",
            "rogue",
        ),
        sheet_position="top-row-3",
    ),
    CastMember(
        id="dwarf_hunter",
        name="드워프 사냥꾼",
        race="드워프",
        wow_class="사냥꾼",
        role_tag="팝콘 · 해탈 결론러",
        color_hex="#2E7D32",
        accent_hex="#E67E22",
        personality=(
            "아수라장 던전에서도 한 발 물러서 팝콘을 씹으며 한 마디로 해탈 결론을 내리는 "
            "마이웨이 사냥꾼."
        ),
        visual_anchor=(
            "Cute anime chibi girl wearing a forest-green fur-trimmed ranger hood, vivid "
            "orange-ginger hair in two thick braided pigtails wrapping under her chin like a "
            "cozy playful braid-beard, warm amber eyes, puffed cheeky cheeks; fur-trimmed brown "
            "leather hunter coat, holding a classic wooden blunderbuss rifle (top-row #4 on "
            "Draft C cast sheet)."
        ),
        aliases=(
            "드워프 사냥꾼",
            "드워프사냥꾼",
            "사냥꾼",
            "냥꾼",
            "드냥",
            "dwarf_hunter",
            "dwarf hunter",
            "hunter",
        ),
        sheet_position="top-row-4",
    ),
    CastMember(
        id="troll_shaman",
        name="트롤 주술사",
        race="트롤",
        wow_class="주술사",
        role_tag="토템 중계 · 팩폭러",
        color_hex="#00ACC1",
        accent_hex="#EF5350",
        personality=(
            "토템을 깔고 번개를 튕기며 던전 막장극을 신나게 중계하고 뼈 때리는 팩폭을 "
            "날리는 하이텐션 주술사."
        ),
        visual_anchor=(
            "Playful anime chibi girl wearing a sky-blue plush troll onesie hood with a bright "
            "red spiky mohawk crest, floppy pierced long ears and tiny white hood tusks; "
            "mint-teal bob hair, winking bright green eye and cheeky blep expression; patterned "
            "tribal scarf and light-blue sleeves with crackling blue lightning sparks around "
            "her hands (top-row #5 on Draft C cast sheet)."
        ),
        aliases=(
            "트롤 주술사",
            "트롤주술사",
            "주술사",
            "술사",
            "트술",
            "복술",
            "정술",
            "고술",
            "troll_shaman",
            "troll shaman",
            "shaman",
        ),
        sheet_position="top-row-5",
    ),
    CastMember(
        id="tauren_druid",
        name="타우렌 드루이드",
        race="타우렌",
        wow_class="드루이드",
        role_tag="마나 오링 · 54렙 캐삭 회드",
        color_hex="#8D6E63",
        accent_hex="#43A047",
        personality=(
            "힐하다 마나가 바닥나면 눈물 글썽이며 54렙 캐삭을 고민하는 순둥이 회드. "
            "억울할 때 볼을 빵빵하게 부풀린다."
        ),
        visual_anchor=(
            "Adorable shy anime chibi girl wearing a fluffy warm-brown plush tauren cow hood "
            "with curved ivory horns, cute cow snout with golden nose ring and floppy ears; "
            "chestnut-brown bangs, big watery glossy brown eyes, blushing puffed cheeks; leafy "
            "green foliage mantle over brown druid tunic, holding a gnarled sprouting wooden "
            "staff (bottom-row #1 on Draft C cast sheet)."
        ),
        aliases=(
            "타우렌 드루이드",
            "타우렌드루이드",
            "드루이드",
            "드루",
            "회드",
            "조드",
            "야드",
            "수드",
            "타드",
            "tauren_druid",
            "tauren druid",
            "druid",
        ),
        sheet_position="bottom-row-1",
    ),
    CastMember(
        id="nightelf_priest",
        name="나이트엘프 사제",
        race="나이트엘프",
        wow_class="사제",
        role_tag="다크서클 힐러 공감러",
        color_hex="#9575CD",
        accent_hex="#FFD54F",
        personality=(
            "밤샘 인던·레이드 힐링에 찌들어 다크서클이 짙게 내려온 힐러들의 영원한 대변인. "
            "항상 마나와 물빵이 고프다."
        ),
        visual_anchor=(
            "Slender graceful anime chibi girl with long silky lavender-silver hair, long "
            "pointed elf ears, delicate golden crescent-moon circlet on her forehead, tired "
            "lilac-purple eyes with pronounced dark under-eye circles; white-and-gold priestess "
            "robe with cream collar bow, holding a glowing golden crescent-moon staff "
            "(bottom-row #2 on Draft C cast sheet)."
        ),
        aliases=(
            "나이트엘프 사제",
            "나이트엘프사제",
            "나엘 사제",
            "나엘사제",
            "사제",
            "신사",
            "수사",
            "암사",
            "힐러",
            "nightelf_priest",
            "night elf priest",
            "priest",
        ),
        sheet_position="bottom-row-2",
    ),
    CastMember(
        id="human_warlock",
        name="인간 흑마법사",
        race="인간",
        wow_class="흑마법사",
        role_tag="지인팟 추리 명탐정",
        color_hex="#7E57C2",
        accent_hex="#E53935",
        personality=(
            "빨간 임프 인형을 품에 안고 지인팟·분배 사건을 예리하게 파헤치는 흑마법사. "
            "가끔 뉴비 티가 나 멜론 주스를 건네기도 한다."
        ),
        visual_anchor=(
            "Cute anime chibi girl wearing a deep dark-purple warlock hood over long jet-black "
            "twin pigtails with vivid purple highlights, sharp violet eyes, tiny fang smirk, "
            "floating purple soul-shard crystals around her; dark purple robe, hugging a plump "
            "grumpy red plush imp doll against her chest (bottom-row #3 on Draft C cast sheet)."
        ),
        aliases=(
            "인간 흑마법사",
            "인간흑마법사",
            "흑마법사",
            "흑마",
            "인흑",
            "고흑",
            "악흑",
            "파흑",
            "human_warlock",
            "human warlock",
            "warlock",
        ),
        sheet_position="bottom-row-3",
    ),
    CastMember(
        id="skyborne_mage",
        name="스카이본 마법사",
        race="스카이본",
        wow_class="마법사",
        role_tag="물빵 보급 · 20:06 폭로러",
        color_hex="#29B6F6",
        accent_hex="#FDD835",
        personality=(
            "호빵과 파란 물병을 들고 다니는 물빵 보급 담당. 어이없는 순간엔 말 한마디 없이 "
            "동공지진 정지 화면으로 응수하는 시그니처 리액션 요원."
        ),
        visual_anchor=(
            "Bright anime chibi girl with pointed elf ears and long golden-blonde hair fading "
            "into pastel sky-blue and aqua tips, big sparkling sapphire-blue eyes; blue-and-white "
            "sailor-collar mage uniform with a teal ribbon bow; holding a steaming warm round "
            "mage bun/bread and a glowing corked blue mana-water flask (bottom-row #4 on Draft "
            "C cast sheet)."
        ),
        aliases=(
            "스카이본 마법사",
            "스카이본마법사",
            "마법사",
            "법사",
            "냉법",
            "화법",
            "비법",
            "물빵",
            "skyborne_mage",
            "skyborne mage",
            "mage",
        ),
        sheet_position="bottom-row-4",
    ),
)

CAST_BY_NAME: dict[str, CastMember] = {member.name: member for member in CAST_BIBLE}
CAST_BY_ID: dict[str, CastMember] = {member.id: member for member in CAST_BIBLE}

_ALIAS_INDEX: dict[str, CastMember] = {}
for _member in CAST_BIBLE:
    _ALIAS_INDEX[_member.id.lower()] = _member
    _ALIAS_INDEX[_member.name.lower()] = _member
    _ALIAS_INDEX[_member.name.replace(" ", "").lower()] = _member
    for _alias in _member.aliases:
        _ALIAS_INDEX[_alias.strip().lower()] = _member
        _ALIAS_INDEX[_alias.strip().replace(" ", "").lower()] = _member


def resolve_cast_member(name_or_alias: str) -> CastMember | None:
    """Resolve a canonical cast name, ID, or Korean/English alias to a `CastMember`."""
    key = name_or_alias.strip().lower()
    if not key:
        return None
    if key in _ALIAS_INDEX:
        return _ALIAS_INDEX[key]
    compact = key.replace(" ", "")
    if compact in _ALIAS_INDEX:
        return _ALIAS_INDEX[compact]
    # Substring fallback for descriptors like "오크 전사 [여]" or "뉴비 흑마법사"
    for alias, member in sorted(_ALIAS_INDEX.items(), key=lambda kv: len(kv[0]), reverse=True):
        if len(alias) >= 2 and alias in compact:
            return member
    return None


def canonical_cast_name(name_or_alias: str) -> str:
    """Normalize an alias to its canonical Korean cast name, or return stripped input."""
    member = resolve_cast_member(name_or_alias)
    return member.name if member is not None else name_or_alias.strip()


def format_cast_bible_for_writer() -> str:
    """Render the full 9-character Draft C cast bible as a compact prompt reference."""
    lines: list[str] = [
        "=== 공식 확정 시안 C (초귀염 팝·개그 미소녀 9종족×9직업 캐스트 바이블) ==="
    ]
    for idx, member in enumerate(CAST_BIBLE, start=1):
        lines.append(
            f"{idx}. {member.name} ({member.role_tag}) | 성격: {member.personality}\n"
            f"   Visual Anchor: {member.visual_anchor}"
        )
    return "\n".join(lines)


def build_character_anchors_block(characters: list[str]) -> str:
    """Build exact English visual consistency anchors for the characters in a single cut."""
    resolved: list[CastMember] = []
    seen_ids: set[str] = set()
    for raw in characters:
        member = resolve_cast_member(raw)
        if member and member.id not in seen_ids:
            resolved.append(member)
            seen_ids.add(member.id)

    if not resolved:
        return (
            "Keep characters strictly faithful to the Draft C cute anime chibi girl style on "
            "the attached cast sheet."
        )

    lines = ["STRICT CHARACTER VISUAL ANCHORS (match attached Draft C cast sheet 100%):"]
    for member in resolved:
        lines.append(f"- {member.name} ({member.id}): {member.visual_anchor}")
    return "\n".join(lines)
