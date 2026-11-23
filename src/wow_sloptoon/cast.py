"""Official Draft C (시안 C 귀염뽀짝 미소녀 9종족×9직업) Cast Bible for wow-forever-sloptoon.

Separates each character's permanent `appearance_anchor` (hood/hair/eyes/outfit) from
their optional `default_prop` so characters obey the Clean Hand Rule (never double-holding
default weapons alongside scene-specific loot, shields, dice, or hearthstones), and tracks
accurate World of Warcraft: Forever factions (`Alliance`, `Horde`, `Neutral-Skyborne`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CastFaction = Literal["Alliance", "Horde", "Neutral-Skyborne"]

_FACTION_KO_LABELS: dict[CastFaction, str] = {
    "Alliance": "얼라이언스",
    "Horde": "호드",
    "Neutral-Skyborne": "스카이본(제프라스 섬 중립 / 마법사는 얼라이언스 상급 기사단)",
}


@dataclass(frozen=True)
class CastMember:
    """Canonical character definition for Draft C cute pop-gag cast."""

    id: str
    name: str
    race: str
    wow_class: str
    faction: CastFaction
    role_tag: str
    color_hex: str
    accent_hex: str
    personality: str
    appearance_anchor: str
    default_prop: str
    aliases: tuple[str, ...]
    sheet_position: str
    lore_note: str = ""

    @property
    def visual_anchor(self) -> str:
        """Backward-compatible combined appearance + optional stowed default prop anchor."""
        return (
            f"{self.appearance_anchor} "
            f"Optional default prop (sheathe/stow/set aside when holding scene items or gesturing): "
            f"{self.default_prop}"
        )


CAST_BIBLE: tuple[CastMember, ...] = (
    CastMember(
        id="orc_warrior",
        name="오크 전사",
        race="오크",
        wow_class="전사",
        faction="Horde",
        role_tag="포갤 억까 근딜러",
        color_hex="#4CAF50",
        accent_hex="#C62828",
        personality=(
            "열혈 호탕 근딜러 겸 전탱. 던전 억까나 미터기 논쟁이 터지면 웃으며 돌진하는 "
            "포에버갤 대표 전사."
        ),
        appearance_anchor=(
            "Cute fair-skinned anime chibi girl (warm peach-ivory human skin — NEVER green skin!) "
            "wearing a vibrant green plush orc animal-onesie hood "
            "with curved cream horns, tiny upturned fangs, piggy snout and pointed green ears "
            "on top of the hood; black high ponytail hair with bangs, bright crimson-red eyes; "
            "spiky red shoulder pauldrons over silver plate armor (top-left #1 on Draft C cast sheet)."
        ),
        default_prop=(
            "Chunky silver battle axe for DPS (when tanking as 전탱/Protection, MUST equip a "
            "one-handed weapon + sturdy steel kite/tower shield instead of a 2H axe; strap across "
            "back or set aside whenever hands hold loot, dice, or gesture)."
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
        lore_note="Horde Warrior (Orgrimmar/Durotar outdoor faction; joins cross-faction dungeons/raids).",
    ),
    CastMember(
        id="undead_paladin",
        name="언데드 성기사",
        race="언데드",
        wow_class="성기사",
        faction="Horde",
        role_tag="3시간 묵언수행 보기",
        color_hex="#9E9E9E",
        accent_hex="#F5B700",
        personality=(
            "3시간 던전에서도 말없이 탱킹하다가 마지막에 무심한 팩트 한 줄 명언을 남기고 "
            "사라지는 묵언수행 성기사."
        ),
        appearance_anchor=(
            "Cute anime chibi girl wearing a round white cartoon skull hood/cap with dark eye "
            "sockets, chin-length silver-white bob hair with icy blue inner tips, golden-yellow "
            "eyes with faint tired eye bags; crisp white-and-gold paladin cloak with a cream neck "
            "bow ribbon (top-row #2 on Draft C cast sheet — vary facial expression freely per scene!)."
        ),
        default_prop=(
            "Shiny golden warhammer for Retribution/징기 (when tanking as 보기/Protection, MUST equip "
            "a one-handed mace/sword + shiny golden paladin shield; stow on back or set aside whenever "
            "holding loot, hearthstone, coin pouch, or gesturing)."
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
        lore_note="WoW Forever new race-class combo (Undead Paladin, Horde; Undercity/Tirisfal outdoor faction).",
    ),
    CastMember(
        id="gnome_rogue",
        name="노움 도적",
        race="노움",
        wow_class="도적",
        faction="Alliance",
        role_tag="칼소멸 · 근딜 훈수꾼",
        color_hex="#FFC107",
        accent_hex="#FF4081",
        personality=(
            "위험하면 빛의 속도로 칼소멸 쓰고 혼자 살아남아 파티창에 깐족 훈수와 드립을 "
            "던지는 장난꾸러기 도적."
        ),
        appearance_anchor=(
            "Petite energetic anime chibi girl with blonde twin pigtails fading into hot-pink "
            "and electric-blue tips, green-lensed steampunk aviator goggles on her forehead, "
            "cross and star hairpins, bright blue eyes, black stealth mask pulled down below "
            "her chin; dark charcoal rogue cloak (top-row #3 on Draft C cast sheet)."
        ),
        default_prop=(
            "Dual glowing poison-green daggers (sheathe neatly at waist belt whenever hands hold "
            "loot, dice, gold pouch, or gesture; never carry 3+ blades at once)."
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
        lore_note="Alliance Rogue (Ironforge/Dun Morogh outdoor faction; uses daggers or 1H swords + Vanish smoke).",
    ),
    CastMember(
        id="dwarf_hunter",
        name="드워프 사냥꾼",
        race="드워프",
        wow_class="사냥꾼",
        faction="Alliance",
        role_tag="팝콘 · 해탈 결론러",
        color_hex="#2E7D32",
        accent_hex="#E67E22",
        personality=(
            "아수라장 던전에서도 한 발 물러서 팝콘을 씹으며 한 마디로 해탈 결론을 내리는 "
            "마이웨이 사냥꾼."
        ),
        appearance_anchor=(
            "Cute anime chibi girl wearing a forest-green fur-trimmed ranger hood, vivid "
            "orange-ginger hair in two thick braided pigtails wrapping under her chin like a "
            "cozy playful braid-beard, warm amber eyes; fur-trimmed brown leather hunter coat "
            "(top-row #4 on Draft C cast sheet — vary facial expression freely per scene!)."
        ),
        default_prop=(
            "Classic wooden blunderbuss rifle (sling across back or set aside whenever holding "
            "popcorn, loot, dice, or gesturing)."
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
        lore_note="Alliance Hunter (Ironforge/Dun Morogh outdoor faction; blunderbuss/bow + beast pet + Feign Death).",
    ),
    CastMember(
        id="troll_shaman",
        name="트롤 주술사",
        race="트롤",
        wow_class="주술사",
        faction="Horde",
        role_tag="토템 중계 · 팩폭러",
        color_hex="#00ACC1",
        accent_hex="#EF5350",
        personality=(
            "토템을 깔고 번개를 튕기며 던전 막장극을 신나게 중계하고 뼈 때리는 팩폭을 "
            "날리는 하이텐션 주술사."
        ),
        appearance_anchor=(
            "Playful fair-skinned anime chibi girl (warm peach-ivory human skin — NEVER blue skin!) "
            "wearing a sky-blue plush troll onesie hood with a bright "
            "red spiky mohawk crest, floppy pierced long ears and tiny white hood tusks; "
            "mint-teal bob hair, bright green eyes; patterned tribal scarf and light-blue sleeves "
            "(top-row #5 on Draft C cast sheet)."
        ),
        default_prop=(
            "Crackling blue lightning sparks around her hands or a small carved wooden shaman totem "
            "on the floor nearby (keep hands clear when holding scene loot, dice, or gesturing)."
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
        lore_note="Horde Shaman (Durotar/Orgrimmar outdoor faction; wooden totems, Chain Lightning, Reincarnation).",
    ),
    CastMember(
        id="tauren_druid",
        name="타우렌 드루이드",
        race="타우렌",
        wow_class="드루이드",
        faction="Horde",
        role_tag="마나 오링 · 54렙 캐삭 회드",
        color_hex="#8D6E63",
        accent_hex="#43A047",
        personality=(
            "힐하다 마나가 바닥나면 눈물 글썽이며 54렙 캐삭을 고민하는 순둥이 회드. "
            "억울할 때 볼을 빵빵하게 부풀린다."
        ),
        appearance_anchor=(
            "Adorable anime chibi girl wearing a fluffy warm-brown plush tauren cow hood "
            "with curved ivory horns, cute cow snout with golden nose ring and floppy ears; "
            "chestnut-brown bangs, warm brown eyes; leafy green foliage mantle over brown "
            "druid tunic (bottom-row #1 on Draft C cast sheet — vary facial expression freely per scene!)."
        ),
        default_prop=(
            "Gnarled sprouting wooden staff (lean against shoulder or stow on back whenever holding "
            "a hearthstone, loot, sleeping bag, or gesturing with both hands)."
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
        lore_note="Horde Druid (Thunder Bluff/Mulgore/Barrens outdoor faction — NEVER Alliance towns like Dolanaar!).",
    ),
    CastMember(
        id="nightelf_priest",
        name="나이트엘프 사제",
        race="나이트엘프",
        wow_class="사제",
        faction="Alliance",
        role_tag="다크서클 힐러 공감러",
        color_hex="#9575CD",
        accent_hex="#FFD54F",
        personality=(
            "밤샘 인던·레이드 힐링에 찌들어 다크서클이 짙게 내려온 힐러들의 영원한 대변인. "
            "항상 마나와 물빵이 고프다."
        ),
        appearance_anchor=(
            "Slender graceful anime chibi girl with long silky lavender-silver hair, long "
            "pointed elf ears, delicate golden crescent-moon circlet on her forehead, "
            "lilac-purple eyes with faint dark under-eye circles; white-and-gold priestess "
            "robe with cream collar bow (bottom-row #2 on Draft C cast sheet — vary facial expression freely per scene!)."
        ),
        default_prop=(
            "Glowing golden crescent-moon staff (lean beside her or stow behind shoulder whenever "
            "clasping hands, pleading, holding loot, or gesturing)."
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
        lore_note="Alliance Priest (Darnassus/Dolanaar/Teldrassil outdoor faction; golden PW:Shield bubble & spirit cues).",
    ),
    CastMember(
        id="human_warlock",
        name="인간 흑마법사",
        race="인간",
        wow_class="흑마법사",
        faction="Alliance",
        role_tag="지인팟 추리 명탐정",
        color_hex="#7E57C2",
        accent_hex="#E53935",
        personality=(
            "빨간 임프 인형을 품에 안고 지인팟·분배 사건을 예리하게 파헤치는 흑마법사. "
            "가끔 뉴비 티가 나 멜론 주스를 건네기도 한다."
        ),
        appearance_anchor=(
            "Cute anime chibi girl wearing a deep dark-purple warlock hood over long jet-black "
            "twin pigtails with vivid purple highlights, sharp violet eyes, tiny fang; dark purple "
            "robe with optional small floating purple soul-shard crystals nearby "
            "(bottom-row #3 on Draft C cast sheet)."
        ),
        default_prop=(
            "Plump grumpy red plush imp doll (hug with one arm, perch beside hip, or set aside "
            "whenever both hands hold a fantasy potion flask, loot, or gesture)."
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
        lore_note="Alliance Warlock (Stormwind/Elwynn/Goldshire outdoor faction; imp/voidwalker, soul shards, healthstone).",
    ),
    CastMember(
        id="skyborne_mage",
        name="스카이본 마법사",
        race="스카이본",
        wow_class="마법사",
        faction="Neutral-Skyborne",
        role_tag="물빵 보급 · 20:06 폭로러",
        color_hex="#29B6F6",
        accent_hex="#FDD835",
        personality=(
            "물빵 보급 담당. 어이없는 순간엔 말 한마디 없이 동공지진 정지 화면으로 응수하는 "
            "시그니처 리액션 요원."
        ),
        appearance_anchor=(
            "Bright anime chibi girl with pointed elf ears and long golden-blonde hair fading "
            "into pastel sky-blue and aqua tips (with subtle airy wind-swept tips and optional "
            "tiny delicate white Skyborne feather hair charm), big sparkling sapphire-blue eyes; "
            "blue-and-white sailor-collar mage uniform with a teal ribbon bow "
            "(bottom-row #4 on Draft C cast sheet)."
        ),
        default_prop=(
            "Steaming warm round mage bun/bread and glowing corked blue mana-water glass flask "
            "(ONLY hold when idle or serving water/bread; put away completely whenever holding "
            "loot, casting spells, pointing, or gesturing)."
        ),
        aliases=(
            "스카이본 마법사",
            "스카이본마법사",
            "스카이본",
            "마법사",
            "법사",
            "냉법",
            "화법",
            "비법",
            "물빵",
            "skyborne_mage",
            "skyborne mage",
            "skyborne",
            "mage",
        ),
        sheet_position="bottom-row-4",
        lore_note=(
            "WoW Forever playable Skyborne race from Zephras Isle (Walk on Air gliding, pointed elf ears, "
            "subtle feather/wind accents); Skyborne Mage aligns with Alliance High Order."
        ),
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


def get_cast_by_faction(faction: str) -> tuple[CastMember, ...]:
    """Return cast members matching a faction (`Alliance`, `Horde`, or `Neutral-Skyborne`).

    For Alliance outdoor zones, note that `skyborne_mage` (`Neutral-Skyborne`) aligns with
    Alliance High Order and can visit Alliance capitals/towns as well.
    """
    target = faction.strip().lower()
    return tuple(m for m in CAST_BIBLE if m.faction.lower() == target)


def format_cast_bible_for_writer() -> str:
    """Render the full 9-character Draft C cast bible with factions & Clean Hand anchors."""
    lines: list[str] = [
        "=== 공식 확정 시안 C (초귀염 팝·개그 미소녀 9종족×9직업 캐스트 바이블) ===",
        "※ Clean Hand Rule: 캐릭터가 전리품·방패·주사위·귀환석·물약병을 들거나 제스처를 취할 때는 "
        "기본 소품(default_prop)을 반드시 등/허리에 수납하거나 생략해 무기·소품 겹침을 방지하세요!",
    ]
    for idx, member in enumerate(CAST_BIBLE, start=1):
        faction_ko = _FACTION_KO_LABELS.get(member.faction, member.faction)
        entry = (
            f"{idx}. {member.name} [{faction_ko}] ({member.role_tag}) | 성격: {member.personality}\n"
            f"   Appearance: {member.appearance_anchor}\n"
            f"   Optional Default Prop (Clean Hand): {member.default_prop}"
        )
        if member.lore_note:
            entry += f"\n   WoW Forever Lore: {member.lore_note}"
        lines.append(entry)
    return "\n".join(lines)


def build_character_anchors_block(characters: list[str]) -> str:
    """Build exact English visual consistency anchors + Clean Hand Rule for a single cut."""
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
            "the attached cast sheet. Obey the CLEAN HAND RULE: never stack 3+ weapons or props."
        )

    lines = [
        "STRICT CHARACTER VISUAL ANCHORS (match attached Draft C cast sheet 100% for head/hood/hair/eyes/outfit):",
        (
            "DYNAMIC POSE & EXPRESSION MANDATE (CRITICAL): NEVER copy the stiff front-facing passport "
            "portrait pose or default facial expression from Reference Image 1! Use Reference Image 1 "
            "STRICTLY for character identity (hood, horns/ears, hair colors, eye color, outfit) — "
            "invent lively 3D body angles, turned/leaning/crouching/running/sprawling poses, and "
            "vivid exaggerated anime gag expressions dictated by the scene action!"
        ),
        (
            "CLEAN HAND RULE (MANDATORY): Each character's default weapon/prop from Reference Image 1 is OPTIONAL. "
            "Whenever the scene action has a character holding scene-specific loot, a tank shield, a loot die, "
            "a hearthstone, a potion/mug, or gesturing with both hands, SHEATHE/STOW on back/belt or OMIT "
            "their default prop completely — NEVER double-hold default weapons + scene items (never 3+ items at once)."
        ),
    ]
    for member in resolved:
        lines.append(
            f"- {member.name} ({member.id} | {member.faction}): {member.appearance_anchor}\n"
            f"  Optional default prop (STOW/OMIT when hands hold scene items or gesture): {member.default_prop}"
        )
        if member.id == "skyborne_mage":
            lines.append(
                "  Skyborne lore note: Subtle airy feather/wind charm & pointed elf ears from Zephras Isle "
                "while staying 100% faithful to Draft C sailor-collar mage uniform."
            )
    return "\n".join(lines)
