"""Official Draft C (시안 C 귀염뽀짝 2.5–2.8등신 9종족×9직업 + 3면 도면 정본) Cast Bible.

Separates each character's permanent `appearance_anchor` (headgear/hair/eyes/full-body outfit/waist
accessories) from their optional `default_prop` so characters obey the Clean Hand Rule (never
double-holding default weapons alongside scene-specific loot, shields, dice, or hearthstones),
maps each character to their canonical Front/Side/Back 3-view turnaround sheet
(`assets/turnarounds/<id>.jpg`), and tracks accurate World of Warcraft: Forever factions
(`Alliance`, `Horde`, `Neutral-Skyborne`).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

CastFaction = Literal["Alliance", "Horde", "Neutral-Skyborne"]

_FACTION_KO_LABELS: dict[CastFaction, str] = {
    "Alliance": "얼라이언스",
    "Horde": "호드",
    "Neutral-Skyborne": "스카이본(제프라스 섬 중립 / 마법사는 얼라이언스 상급 기사단)",
}


@dataclass(frozen=True)
class CastMember:
    """Canonical character definition for Draft C 2.5–2.8 head pop-gag cast + 3-view turnaround."""

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
    def turnaround_filename(self) -> str:
        """Filename of this character's canonical 3-view Front/Side/Back turnaround sheet."""
        return f"{self.id}.jpg"

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
            "Cute fair-skinned 2.5-to-2.8 head anime chibi girl (bright peach-ivory human skin — "
            "NEVER green skin!) wearing a vibrant green plush orc monster hood with curved cream "
            "horns, tiny upturned fangs, piggy snout and pointed green ears; jet-black high ponytail "
            "tied with a red hair band emerging from the back hood opening, sparkling crimson-red "
            "jewel eyes, playful fang grin; spiky crimson-red shoulder pauldrons (3 spikes each), "
            "silver plate breastplate over green sleeves, silver bracers, brown leather belt with "
            "silver buckle, short crimson pleated skirt over dark shorts, red warrior cape, and "
            "chunky silver-and-brown steel plated boots (match assets/turnarounds/orc_warrior.jpg)."
        ),
        default_prop=(
            "Chunky silver-steel Horde battle axe for DPS (strapped diagonally across back cape in "
            "Clean Hand stowed pose; when tanking as 전탱/Protection, MUST equip a one-handed weapon "
            "+ sturdy steel kite/tower shield instead of a 2H axe; stow on back whenever hands hold "
            "loot, dice, or gesture)."
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
            "Cute fair-skinned 2.5-to-2.8 head anime chibi girl (NEVER zombie skin!) wearing a "
            "round pure-white cartoon skull cap with dark eye sockets, chin-length silky silver-white "
            "bob hair, half-lidded golden-yellow jewel eyes with faint tired eye bags; crisp "
            "pure-white gold-trimmed paladin cape fastened with a cream neck ribbon bow, white-and-gold "
            "paladin tunic & pleated skirt over black sleeves and dark charcoal leggings, brown belt "
            "with gold buckle, white gauntlets, and chunky white-and-gold armored paladin boots "
            "(match assets/turnarounds/undead_paladin.jpg — vary facial expression freely per scene!)."
        ),
        default_prop=(
            "Shiny chunky golden Paladin warhammer for Retribution/징기 (strapped diagonally across "
            "back cape when stowed; when tanking as 보기/Protection, MUST equip a one-handed "
            "mace/sword + shiny golden paladin shield; stow on back whenever holding loot, "
            "hearthstone, coin pouch, or gesturing)."
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
            "Petite energetic 2.5-to-2.8 head anime chibi girl with golden-blonde twin pigtails "
            "fading smoothly into hot-pink and electric-blue tips (STRICTLY ZERO hairpins — NO X-pin "
            "and NO star hairpins on bangs!), green-lensed steampunk aviator goggles on her forehead "
            "with black strap around back, bright sparkling blue jewel eyes, cheeky fang grin, black "
            "stealth half-mask pulled down below her chin; dark charcoal hooded rogue cloak & tunic "
            "with diagonal brown chest strap, utility belt carrying tiny glowing green poison vials, "
            "dark shorts, brown bracers & fingerless gloves, and cuffed dark-brown leather rogue boots "
            "(match assets/turnarounds/gnome_rogue.jpg)."
        ),
        default_prop=(
            "Twin glowing poison-green Rogue daggers (sheathed & crossed neatly at her lower back "
            "waist belt whenever hands hold loot, dice, gold pouch, or gesture; never carry 3+ blades)."
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
            "Cute cozy 2.5-to-2.8 head anime chibi girl wearing a forest-green ranger hood and short "
            "cape trimmed with fluffy white fur, vivid orange-ginger hair in two thick braided "
            "pigtails wrapping playfully under her chin like a cozy braid-beard, warm amber jewel "
            "eyes; fur-trimmed brown leather hunter coat with ammo-pouch belt, brown leggings, "
            "fingerless hunter gloves, and white-fur-cuffed brown mountain boots "
            "(match assets/turnarounds/dwarf_hunter.jpg — vary facial expression freely per scene!)."
        ),
        default_prop=(
            "Classic chunky wooden-and-steel Dwarf blunderbuss rifle (slung diagonally across back "
            "with leather strap whenever holding popcorn, loot, dice, or gesturing)."
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
            "Playful fair-skinned 2.5-to-2.8 head anime chibi girl (bright warm peach-ivory human "
            "skin — NEVER blue skin!) wearing a sky-blue plush troll monster hood with a bright red "
            "spiky mohawk crest along the crown, floppy pierced long blue ears (gold hoop on left "
            "ear) and tiny white hood tusks; mint-teal bob hair, sparkling emerald-green jewel eyes; "
            "sky-blue tunic & cape, patterned brown-and-cream tribal poncho scarf with beads, brown "
            "belt with 2 mini carved wooden totems on hip, brown tribal skirt over dark leggings, and "
            "tribal boots with sky-blue wraps (match assets/turnarounds/troll_shaman.jpg)."
        ),
        default_prop=(
            "Chunky carved wooden Shaman totem staff (strapped diagonally across back when stowed) "
            "plus optional crackling blue lightning sparks or floor wooden totems (keep hands clear "
            "when holding scene loot, dice, or gesturing)."
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
            "Adorable fair-skinned 2.5-to-2.8 head anime chibi girl wearing a fluffy warm-brown plush "
            "tauren cow hood with curved ivory horns, cute cow snout with shiny golden nose ring and "
            "floppy cow ears; chestnut-brown bangs, glossy warm-brown jewel eyes; 360-degree layered "
            "fresh leafy-green foliage shoulder mantle over a warm-brown and cream suede druid tunic, "
            "braided brown belt with herbal pouch, dark brown leggings, and chunky brown lace-up "
            "druid boots with tiny green leaf accents on the sides "
            "(match assets/turnarounds/tauren_druid.jpg — vary facial expression freely per scene!)."
        ),
        default_prop=(
            "Chunky gnarled wooden Druid staff with sprouting green leaves (strapped diagonally "
            "across back whenever holding a hearthstone, loot, sleeping bag, or gesturing)."
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
        role_tag="엘룬 보라 사제 · 과로 힐러",
        color_hex="#7E57C2",
        accent_hex="#FFD54F",
        personality=(
            "밤샘 인던·레이드 힐링에 찌든 다르나서스 엘룬 사제. 허리에 찬 미니 성서와 묵주를 "
            "들고 바닥 밟는 딜러들을 은빛 발광 눈으로 째려보는 힐러 대변인."
        ),
        appearance_anchor=(
            "Cute fair-skinned 2.5-to-2.8 head anime chibi girl (bright normal peach-ivory skin — "
            "NEVER purple/grey skin!) with fluffy pastel-lavender wavy half-up ponytail, side braid, "
            "cute ahoge tuft, golden Elune crescent forehead tiara, perky long pointed Night Elf ears "
            "with tiny gold crescent earrings, delicate pale-violet Night Elf cheek markings, and "
            "luminous glowing silver-white Night Elf eyes with grumpy-cute healer glare (STRICTLY "
            "ZERO angel halo ring and ZERO wings!); vibrant royal-purple and gold-trimmed short "
            "Priestess shoulder capelet with golden crescent clasp over crisp white blouse, royal-purple "
            "and gold pleated Priest mini-skirt, brown leather waist belt carrying a chunky white-and-gold "
            "mini Holy Prayer Book on left hip and draping golden beaded Rosary on right hip, pure-white "
            "knee-high stockings, and royal-purple & gold Priest boots "
            "(match assets/turnarounds/nightelf_priest.jpg — vary facial expression freely per scene!)."
        ),
        default_prop=(
            "Chunky golden-and-ivory Holy Cross & Sunburst Cleric Priest Staff (strapped diagonally "
            "across back capelet whenever clasping hands, pleading, holding loot, or gesturing)."
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
        lore_note="Alliance Priest (Darnassus/Dolanaar/Teldrassil outdoor faction; Elune purple vestments, Holy Tome & Rosary, PW:Shield).",
    ),
    CastMember(
        id="human_warlock",
        name="인간 흑마법사",
        race="인간",
        wow_class="흑마법사",
        faction="Alliance",
        role_tag="지인팟 추리 명탐정",
        color_hex="#6A1B9A",
        accent_hex="#E53935",
        personality=(
            "빨간 임프 인형을 품에 안고 지인팟·분배 사건을 예리하게 파헤치는 흑마법사. "
            "가끔 뉴비 티가 나 멜론 주스를 건네기도 한다."
        ),
        appearance_anchor=(
            "Cute mischievous 2.5-to-2.8 head gothic anime chibi girl wearing a cozy puffy deep "
            "dark-purple Warlock hood over long jet-black twin pigtails with vivid purple highlights, "
            "sharp sparkling violet jewel eyes, sly fang smirk; deep dark-purple and charcoal hooded "
            "Warlock cape & pleated robe dress with purple diamond clasps and purple pointed cuffs, "
            "dark stockings, fingerless gloves, and chunky black buckled gothic Warlock boots "
            "(match assets/turnarounds/human_warlock.jpg)."
        ),
        default_prop=(
            "Plump grumpy red plush Imp doll (tucked under arm or clipped cutely to back cape when "
            "both hands hold a fantasy potion flask, loot, or gesture)."
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
        role_tag="변이 양 · 20:06 폭로 법사",
        color_hex="#29B6F6",
        accent_hex="#FDD835",
        personality=(
            "허리에 뽀짝한 변이 양 키링을 달고 다니는 제프라스 섬 천재 바람 법사. 어이없는 "
            "순간엔 별눈 윙크를 멈추고 동공지진 정지 화면으로 응수하는 시그니처 리액션 요원."
        ),
        appearance_anchor=(
            "Bright fair-skinned 2.5-to-2.8 head anime chibi girl (bright porcelain-peach-ivory skin) "
            "with bouncy silky clear sky-blue (Skyborne blue) hair styled in a fluffy high side-ponytail, "
            "perky long pointed elf ears, sparkling bright sky-blue star-pupil jewel eyes and lively "
            "wink/smile; oversized tilted royal-blue pointed wizard hat with gold hatband and one tiny "
            "cute smiling puffy white cloud-with-mini-wing feather badge; royal-blue short Mage capelet "
            "with fluffy white cloud-scalloped trim over a crisp white-and-blue flared Mage tunic, dark "
            "blue belt with gold buckle carrying a tiny round fluffy white Polymorph Sheep keychain "
            "charm clipped consistently at her waist, dark shorts, white knee-high socks, and royal-blue "
            "& gold Mage boots (STRICTLY ZERO sailor uniform, ZERO bread/water in default outfit; "
            "match assets/turnarounds/skyborne_mage.jpg)."
        ),
        default_prop=(
            "Chunky wooden-and-gold Mage staff topped with a crisp sky-blue diamond crystal (strapped "
            "diagonally across back capelet whenever casting spells, serving conjured mana-water/bread "
            "in specific water/bread scenes, holding loot, or gesturing)."
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
            "sky-blue hair, cloud-wing feather hat charm); Skyborne Mage aligns with Alliance High Order."
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


def get_turnaround_paths(
    characters: list[str],
    turnarounds_dir: Path,
) -> list[tuple[CastMember, Path]]:
    """Return existing `(CastMember, turnaround_path)` pairs for unique resolved cast members."""
    pairs: list[tuple[CastMember, Path]] = []
    seen_ids: set[str] = set()
    if not turnarounds_dir.exists():
        return pairs
    for raw in characters:
        member = resolve_cast_member(raw)
        if member is None or member.id in seen_ids:
            continue
        seen_ids.add(member.id)
        candidate = turnarounds_dir / member.turnaround_filename
        if candidate.exists() and candidate.is_file():
            pairs.append((member, candidate))
    return pairs


def format_cast_bible_for_writer() -> str:
    """Render the full 9-character Draft C cast bible with factions & Clean Hand anchors."""
    lines: list[str] = [
        "=== 공식 확정 시안 C (2.5–2.8등신 얇은 칼선·2단 셀 명암 9종족×9직업 캐스트 바이블 + 3면 도면 정본) ===",
        "※ Clean Hand Rule: 캐릭터가 전리품·방패·주사위·귀환석·물약병을 들거나 제스처를 취할 때는 "
        "기본 소품(default_prop)을 반드시 등/허리에 수납하거나 생략해 무기·소품 겹침을 방지하세요!",
    ]
    for idx, member in enumerate(CAST_BIBLE, start=1):
        faction_ko = _FACTION_KO_LABELS.get(member.faction, member.faction)
        entry = (
            f"{idx}. {member.name} [{faction_ko}] ({member.role_tag}) | 성격: {member.personality}\n"
            f"   Turnaround Blueprint: assets/turnarounds/{member.turnaround_filename}\n"
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
            "Keep characters strictly faithful to the Draft C 2.5-to-2.8 head cute anime chibi "
            "style (thin variable-width dark ink linework, crisp 2-tier cel shading, sparkling "
            "jewel eyes) on the attached cast sheet and turnaround blueprints. Obey the CLEAN HAND "
            "RULE: never stack 3+ weapons or props."
        )

    lines = [
        "STRICT CHARACTER VISUAL ANCHORS (match the attached Draft C 9-cast master sheet AND "
        "each character's attached Front/Side/Back 3-view turnaround blueprint 100% for head, "
        "hood/hat, hair, ears, eyes, full-body outfit, waist accessories, and boots!):",
        (
            "LINEWORK & SHADING BENCHMARK (MANDATORY): Render in crisp 2.5-to-2.8 head cute chibi "
            "proportions with razor-sharp thin variable-width dark ink linework, clean 2-tier anime "
            "cel shading, glossy sparkling jewel eyes, and simple clean color shapes matching the "
            "attached turnaround blueprints (ZERO thick muddy outlines, ZERO busy RPG filigree)."
        ),
        (
            "DYNAMIC POSE & EXPRESSION MANDATE (CRITICAL): NEVER copy the stiff front-facing "
            "standing turnaround pose or neutral expression from the reference sheets! Use the "
            "attached turnaround sheets STRICTLY for 360-degree character consistency (front/side/back "
            "hood, hat, hair, outfit, waist charms, and back-stowed weapon placement) — invent lively "
            "3D body angles, turned/leaning/crouching/running/sprawling poses, and vivid exaggerated "
            "anime gag expressions dictated by the scene action!"
        ),
        (
            "CLEAN HAND RULE (MANDATORY): Each character's default weapon/prop is OPTIONAL. "
            "Whenever the scene action has a character holding scene-specific loot, a tank shield, a "
            "loot die, a hearthstone, a potion/mug, or gesturing with both hands, SHEATHE/STOW on "
            "back/belt exactly as shown in their Back-view turnaround or OMIT their default prop "
            "completely — NEVER double-hold default weapons + scene items (never 3+ items at once)."
        ),
    ]
    for member in resolved:
        lines.append(
            f"- {member.name} ({member.id} | {member.faction} | turnaround: assets/turnarounds/{member.turnaround_filename}): "
            f"{member.appearance_anchor}\n"
            f"  Optional default prop (STOW/OMIT when hands hold scene items or gesture): {member.default_prop}"
        )
        if member.id == "skyborne_mage":
            lines.append(
                "  Skyborne lore note: Zephras Isle wind-elf heritage — clear sky-blue high "
                "side-ponytail, perky pointed elf ears, tilted royal-blue wizard hat with tiny "
                "smiling cloud-wing feather badge, cloud-trimmed capelet, and tiny waist Polymorph "
                "Sheep keychain charm (STRICTLY NO sailor uniform or permanent bread/water)."
            )
    return "\n".join(lines)
