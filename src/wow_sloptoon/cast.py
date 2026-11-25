"""Official 9-Race x 9-Class Cast Bible (+ 2 Fixed Round Companion Mascots) for WOW Forever Sloptoon.

Route A Single Canonical Art Style:
- Cute plump 2-to-2.5 head Korean anime SD chibi girls matching `assets/diorama_style_ref.jpg`
  (Style Master) and the 2.5-head 3-view turnaround sheets (`assets/turnarounds/<id>.jpg`).
- Fixed ultra-cute round companion mascots (`hunter_bear.jpg` baby brown bear for Dwarf Hunter
  and `warlock_voidwalker.jpg` purple Voidwalker for Human Warlock) auto-attach with their owners.
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

_SD_PREFIX = "Cute plump 2-to-2.5 head Korean anime SD chibi girl, fair skin; "


@dataclass(frozen=True)
class CastMember:
    """Canonical character definition for the 9-member 2-to-2.5 head SD Sloptoon cast."""

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
    speech_style: str = ""
    companion_id: str = ""
    companion_name: str = ""
    companion_anchor: str = ""

    @property
    def turnaround_filename(self) -> str:
        """Filename of this character's 2.5-head 3-view costume/color turnaround."""
        return f"{self.id}.jpg"

    @property
    def companion_turnaround_filename(self) -> str | None:
        """Filename of this character's fixed companion 3-view turnaround sheet, if any."""
        return f"{self.companion_id}.jpg" if self.companion_id else None


CAST_BIBLE: tuple[CastMember, ...] = (
    CastMember(
        id="orc_warrior",
        name="오크 전사",
        race="오크",
        wow_class="전사",
        faction="Horde",
        role_tag="열혈 직진 전사",
        color_hex="#4CAF50",
        accent_hex="#C62828",
        personality="근거 없는 자신감으로 먼저 돌진했다가 위기엔 다급하게 힐러를 찾는 직진형 전사·전탱.",
        speech_style="시원하고 솔직한 반말, 당당한 허세와 다급한 하소연의 대비.",
        appearance_anchor=(
            f"{_SD_PREFIX}green plush orc hood (horns/fangs), black ponytail, crimson eyes, "
            "spiked red pauldrons, silver armor, red skirt & cape."
        ),
        default_prop="Back battle axe (1H sword+steel shield if tank).",
        aliases=(
            "오크 전사", "오크전사", "전사", "오전", "무전", "분전", "방전", "전탱",
            "orc_warrior", "orc warrior", "warrior",
        ),
        sheet_position="top-row-1",
        lore_note="Horde Warrior (Orgrimmar/Durotar outdoor faction).",
    ),
    CastMember(
        id="undead_paladin",
        name="언데드 성기사",
        race="언데드",
        wow_class="성기사",
        faction="Horde",
        role_tag="나른 시니컬 보기",
        color_hex="#9E9E9E",
        accent_hex="#F5B700",
        personality="늘 피곤하고 귀찮아 보이지만 묵묵히 탱·딜을 해내며 무심한 팩폭을 날리는 쿨뷰티 성기사.",
        speech_style="힘 빠진 건조한 단답, 냉정한 현실 팩폭과 의외의 무심한 챙김.",
        appearance_anchor=(
            f"{_SD_PREFIX}round white skull cap, silver bob, big golden tired eyes, "
            "white-gold paladin cape with neck bow, tunic & boots."
        ),
        default_prop="Back gold warhammer (1H mace+gold shield if tank).",
        aliases=(
            "언데드 성기사", "언데드성기사", "성기사", "기사", "보기", "징기", "신기", "언기사",
            "undead_paladin", "undead paladin", "paladin",
        ),
        sheet_position="top-row-2",
        lore_note="WoW Forever Undead Paladin (Horde; Undercity/Tirisfal outdoor faction).",
    ),
    CastMember(
        id="gnome_rogue",
        name="노움 도적",
        race="노움",
        wow_class="도적",
        faction="Alliance",
        role_tag="장난꾸러기 칼소멸 도적",
        color_hex="#FFC107",
        accent_hex="#FF4081",
        personality="눈치 빠르고 장난기 많으며 위기엔 제일 먼저 소멸·도주하는 깐족 도적.",
        speech_style="빠르고 재치 있는 반말, 얄미운 팩트 체크와 즉각적인 도주 멘트.",
        appearance_anchor=(
            f"{_SD_PREFIX}bare unadorned blonde twin pigtails (pink/blue tips), green forehead goggles, "
            "blue eyes, chin mask, dark rogue cloak & poison-vial belt."
        ),
        default_prop="Waist-sheathed twin green daggers.",
        aliases=(
            "노움 도적", "노움도적", "도적", "노도", "도비",
            "gnome_rogue", "gnome rogue", "rogue",
        ),
        sheet_position="top-row-3",
        lore_note="Alliance Rogue (Ironforge/Dun Morogh outdoor faction).",
    ),
    CastMember(
        id="dwarf_hunter",
        name="드워프 사냥꾼",
        race="드워프",
        wow_class="사냥꾼",
        faction="Alliance",
        role_tag="느긋 마이웨이 냥꾼",
        color_hex="#2E7D32",
        accent_hex="#E67E22",
        personality="파티가 난장판이 되어도 한 발짝 떨어져 느긋하게 구경하다가 전리품엔 진심이고 위기엔 죽척하는 사냥꾼.",
        speech_style="여유롭고 능청스러운 구어체, 상황 관전 멘트와 뻔뻔한 입찰 논리.",
        appearance_anchor=(
            f"{_SD_PREFIX}green fur-trimmed ranger hood & short cape, thick ginger braided pigtails, "
            "amber eyes, brown fur-trimmed leather coat & boots."
        ),
        default_prop="Back-slung blunderbuss rifle.",
        aliases=(
            "드워프 사냥꾼", "드워프사냥꾼", "사냥꾼", "냥꾼", "드냥",
            "dwarf_hunter", "dwarf hunter", "hunter",
        ),
        sheet_position="top-row-4",
        lore_note="Alliance Hunter (Ironforge/Dun Morogh outdoor faction).",
        companion_id="hunter_bear",
        companion_name="아기 곰",
        companion_anchor="Round chubby brown baby bear (~0.45x, cream muzzle, cute smile, green scarf) beside her.",
    ),
    CastMember(
        id="troll_shaman",
        name="트롤 주술사",
        race="트롤",
        wow_class="주술사",
        faction="Horde",
        role_tag="하이텐션 중계 술사",
        color_hex="#00ACC1",
        accent_hex="#EF5350",
        personality="분위기 띄우기 좋아하고 던전 사건을 신나게 중계하며 사이다 팩폭을 날리는 수다쟁이 주술사.",
        speech_style="리듬감 있고 호들갑스러운 구어체, 빠른 리액션과 관객 공감 유도.",
        appearance_anchor=(
            f"{_SD_PREFIX}sky-blue plush troll hood (red mohawk, pierced ears, tiny tusks), mint bob, "
            "emerald eyes, sky-blue tunic, tribal scarf & mini waist totems."
        ),
        default_prop="Back wooden totem staff.",
        aliases=(
            "트롤 주술사", "트롤주술사", "주술사", "술사", "트술", "복술", "정술", "고술",
            "troll_shaman", "troll shaman", "shaman",
        ),
        sheet_position="top-row-5",
        lore_note="Horde Shaman (Durotar/Orgrimmar outdoor faction).",
    ),
    CastMember(
        id="tauren_druid",
        name="타우렌 드루이드",
        race="타우렌",
        wow_class="드루이드",
        faction="Horde",
        role_tag="순둥 유리멘탈 드루",
        color_hex="#8D6E63",
        accent_hex="#43A047",
        personality="평소엔 순하고 착한 힐러·드루이지만 억까나 마나 오링 앞에선 금방 멘붕해 울먹이는 유리멘탈.",
        speech_style="부드럽고 순한 구어체에서 억울할 때 급발진하는 감정 기복.",
        appearance_anchor=(
            f"{_SD_PREFIX}brown plush cow hood (ivory horns, gold nose ring), brown bangs & eyes, "
            "leafy-green shoulder mantle, suede tunic & herb pouch."
        ),
        default_prop="Back leafy wooden staff.",
        aliases=(
            "타우렌 드루이드", "타우렌드루이드", "드루이드", "드루", "회드", "조드", "야드", "수드", "타드",
            "tauren_druid", "tauren druid", "druid",
        ),
        sheet_position="bottom-row-1",
        lore_note="Horde Druid (Thunder Bluff/Mulgore/Barrens outdoor faction — never Alliance towns).",
    ),
    CastMember(
        id="nightelf_priest",
        name="나이트엘프 사제",
        race="나이트엘프",
        wow_class="사제",
        faction="Alliance",
        role_tag="격무 시달림·흑막 사제",
        color_hex="#7E57C2",
        accent_hex="#FFD54F",
        personality="평소엔 예의 바르고 마나에 시달리는 힐러지만, 선을 넘으면 웃는 얼굴로 정배·노힐 응징을 즐기는 갭모에 사제.",
        speech_style="차분하고 예의 바른 해요체, 정색할 때의 서늘한 팩폭.",
        appearance_anchor=(
            f"{_SD_PREFIX}lavender half-up hair, gold crescent tiara, elf ears, big lively "
            "lavender-silver SD eyes, purple gold-trimmed priest robe, waist mini Holy Book & gold Rosary."
        ),
        default_prop="Back gold cross staff.",
        aliases=(
            "나이트엘프 사제", "나이트엘프사제", "나엘 사제", "나엘사제", "사제", "신사", "수사", "암사", "힐러",
            "nightelf_priest", "night elf priest", "priest",
        ),
        sheet_position="bottom-row-2",
        lore_note="Alliance Priest (Darnassus/Dolanaar/Teldrassil outdoor faction).",
    ),
    CastMember(
        id="human_warlock",
        name="인간 흑마법사",
        race="인간",
        wow_class="흑마법사",
        faction="Alliance",
        role_tag="허당 고딕 흑마",
        color_hex="#6A1B9A",
        accent_hex="#E53935",
        personality="동글동글한 공허방랑자를 데리고 다니며 나름 진지하지만 어딘가 허당끼가 넘치고 억울할 땐 성실하게 해명하는 흑마법사.",
        speech_style="진지하거나 성실한 구어체, 당황했을 때의 어리둥절한 반전 리액션.",
        appearance_anchor=(
            f"{_SD_PREFIX}dark-purple Warlock hood, black twin pigtails (purple tips), bright violet eyes, "
            "dark-purple gothic hooded robe dress & black boots."
        ),
        default_prop="Small purple spellbook or violet soul shard.",
        aliases=(
            "인간 흑마법사", "인간흑마법사", "흑마법사", "흑마", "인흑", "고흑", "악흑", "파흑",
            "human_warlock", "human warlock", "warlock",
        ),
        sheet_position="bottom-row-3",
        lore_note="Alliance Warlock (Stormwind/Elwynn/Goldshire outdoor faction).",
        companion_id="warlock_voidwalker",
        companion_name="공허방랑자",
        companion_anchor="Round squishy floating purple Voidwalker (~0.45x, starry belly, cute eyes, gold bracers) beside her.",
    ),
    CastMember(
        id="skyborne_mage",
        name="스카이본 마법사",
        race="스카이본",
        wow_class="마법사",
        faction="Neutral-Skyborne",
        role_tag="도도 발랄 별눈 법사",
        color_hex="#29B6F6",
        accent_hex="#FDD835",
        personality="제프라스 섬 출신 자칭 천재 마법사. 평소엔 도도하지만 공짜 물빵 요구나 지능 템 입찰 억까 앞에서는 정색·폭발한다.",
        speech_style="새침하고 자신감 있는 반말, 억까 앞에서의 서늘한 정적과 즉각적인 버럭.",
        appearance_anchor=(
            f"{_SD_PREFIX}sky-blue high side-ponytail, elf ears, star-pupil eyes, tilted blue wizard hat "
            "(smiling cloud-wing badge), cloud capelet, blue-white tunic & waist Polymorph Sheep charm."
        ),
        default_prop="Back blue crystal staff.",
        aliases=(
            "스카이본 마법사", "스카이본마법사", "스카이본", "마법사", "법사", "냉법", "화법", "비법", "물빵",
            "skyborne_mage", "skyborne mage", "skyborne", "mage",
        ),
        sheet_position="bottom-row-4",
        lore_note="WoW Forever Skyborne race from Zephras Isle (Walk on Air, Alliance High Order Mage).",
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
    for alias, member in sorted(_ALIAS_INDEX.items(), key=lambda kv: len(kv[0]), reverse=True):
        if len(alias) >= 2 and alias in compact:
            return member
    return None


def canonical_cast_name(name_or_alias: str) -> str:
    """Normalize an alias to its canonical Korean cast name, or return stripped input."""
    member = resolve_cast_member(name_or_alias)
    return member.name if member is not None else name_or_alias.strip()


def get_cast_by_faction(faction: str) -> tuple[CastMember, ...]:
    """Return cast members matching a faction (`Alliance`, `Horde`, or `Neutral-Skyborne`)."""
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


def get_companion_turnaround_paths(
    characters: list[str],
    turnarounds_dir: Path,
) -> list[tuple[CastMember, Path]]:
    """Return existing `(owner_member, companion_turnaround_path)` pairs for cast with fixed pets."""
    pairs: list[tuple[CastMember, Path]] = []
    seen_ids: set[str] = set()
    if not turnarounds_dir.exists():
        return pairs
    for raw in characters:
        member = resolve_cast_member(raw)
        if member is None or member.id in seen_ids or not member.companion_turnaround_filename:
            continue
        seen_ids.add(member.id)
        candidate = turnarounds_dir / member.companion_turnaround_filename
        if candidate.exists() and candidate.is_file():
            pairs.append((member, candidate))
    return pairs


def format_cast_bible_for_writer() -> str:
    """Render a compact 9-character 2~2.5 head SD cast guide for the script writer."""
    lines: list[str] = [
        "=== 고정 캐스트 9인 (전원 2~2.5등신 귀염뽀짝 SD 미소녀 — 영문 she/her 사용 · 유행어 복붙 금지) ===",
        "※ Clean Hand Rule: 전리품·방패·주사위·귀환석·물약병을 들거나 제스처할 때는 기본 무기를 등/허리에 수납.",
        "※ 고정 동행 펫(주인 등장 시 곁에서 함께 리액션, 컷당 1~2명 주연 제한 미산입): 드워프 사냥꾼 → 아기 곰, 인간 흑마법사 → 보라 공허방랑자 (빨간 임프 언급 금지!).",
    ]
    for idx, member in enumerate(CAST_BIBLE, start=1):
        faction_ko = _FACTION_KO_LABELS.get(member.faction, member.faction)
        pet_tag = f" [동행 펫: {member.companion_name}]" if member.companion_name else ""
        lines.append(
            f"{idx}. {member.name} [{faction_ko}] ({member.role_tag}){pet_tag} — {member.personality} "
            f"말투: {member.speech_style}"
        )
    return "\n".join(lines)


def build_character_anchors_block(characters: list[str]) -> str:
    """Build ultra-compact 2-to-2.5 head SD costume & companion anchors for `artist.py`."""
    resolved: list[CastMember] = []
    seen_ids: set[str] = set()
    for raw in characters:
        member = resolve_cast_member(raw)
        if member and member.id not in seen_ids:
            resolved.append(member)
            seen_ids.add(member.id)

    header = "CAST (fair-skinned cute 2-to-2.5 head SD girls; Ref costume/hair/color, dynamic pose):"
    if not resolved:
        return header

    lines = [header]
    for member in resolved:
        compact_desc = member.appearance_anchor
        if compact_desc.startswith(_SD_PREFIX):
            compact_desc = compact_desc[len(_SD_PREFIX):]
        lines.append(f"- {member.id}: {compact_desc} Prop: {member.default_prop}")
        if member.companion_id and member.companion_anchor:
            lines.append(f"  Pet ({member.companion_id}): {member.companion_anchor}")
    return "\n".join(lines)
