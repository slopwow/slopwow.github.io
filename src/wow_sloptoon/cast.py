"""Official 9-Race x 9-Class Cast Bible (+ 2 Fixed Round Companion Mascots) for WOW Forever Sloptoon.

Target art style: sleek 3-to-3.5 head Korean anime gag webtoon proportions matching
`assets/sloptoon_style_ref.jpg` (Reference Image 1) and the polished 3.5–4 head
turnaround sheets (`assets/turnarounds/<id>.jpg`) featuring fine hair strands, natural
clothing folds, and expressive faces. Fixed ultra-cute round companion mascots
(`hunter_bear.jpg` for Dwarf Hunter and `warlock_voidwalker.jpg` for Human Warlock)
auto-attach whenever their owners appear.

Personality and speech tones are concise behavioral cues (zero copy-paste catchphrase
templates) so dialogue stays natural, witty, and self-contained for readers who have never
read the source post.
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
    """Canonical character definition for the 9-member Sloptoon cast."""

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
    aegyo_signature: str = ""
    acting_range: str = ""
    companion_id: str = ""
    companion_name: str = ""
    companion_anchor: str = ""

    @property
    def turnaround_filename(self) -> str:
        """Filename of this character's 3-view costume/color design reference."""
        return f"{self.id}.jpg"

    @property
    def companion_turnaround_filename(self) -> str | None:
        """Filename of this character's fixed companion 3-view turnaround sheet, if any."""
        return f"{self.companion_id}.jpg" if self.companion_id else None

    @property
    def visual_anchor(self) -> str:
        """Backward-compatible combined appearance + optional stowed default prop anchor."""
        return (
            f"{self.appearance_anchor} "
            f"Optional default prop (stow on back/belt when hands hold scene items or gesture): "
            f"{self.default_prop}"
        )


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
        aegyo_signature="허세 부리다 금방 쩔쩔매는 솔직한 직진 톤(고정 감탄사 복붙 금지).",
        acting_range="boisterous battle grin, starry eager excitement, frantic HP-1% tearful panic",
        appearance_anchor=(
            "Fair-skinned sleek 3-to-3.5 head anime webtoon girl (never green skin) wearing a green plush "
            "orc monster hood with cream horns, hood fangs, snout and pointed ears; jet-black high ponytail "
            "with red band, crimson eyes; 3-spike crimson shoulder pauldrons, silver breastplate over green "
            "sleeves, crimson pleated skirt, red cape, steel boots (identity & costume only, facial "
            "expression and pose free per scene)."
        ),
        default_prop=(
            "Chunky silver battle axe for DPS (stowed across back); when tanking as 전탱/Protection, "
            "equip a 1H sword/axe + sturdy steel kite shield instead."
        ),
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
        aegyo_signature="무덤덤하고 나른한 단답 톤 속 은근한 배려(과도한 말줄임표·기호 남발 금지).",
        acting_range="heavy half-lidded deadpan stare, exhausted sigh, subtle flustered blush when praised",
        appearance_anchor=(
            "Fair-skinned sleek 3-to-3.5 head anime webtoon girl (never zombie skin) wearing a round white "
            "cartoon skull cap, chin-length silver-white bob hair, golden-yellow eyes with faint tired "
            "under-eye lines; white gold-trimmed paladin cape with cream neck bow, white-and-gold tunic and "
            "pleated skirt over black sleeves and charcoal leggings, white-and-gold boots (identity & costume "
            "only, facial expression and pose free per scene)."
        ),
        default_prop=(
            "Golden warhammer for Retribution/징기 (stowed across back); when tanking as 보기/Protection, "
            "equip a 1H mace/sword + golden crest shield."
        ),
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
        aegyo_signature="장난스럽고 깐족대는 빠른 템포(억지 웃음소리 복붙 금지).",
        acting_range="teasing smirk, pushing goggles up smugly, wide-eyed pale terror when cornered",
        appearance_anchor=(
            "Fair-skinned sleek 3-to-3.5 head anime webtoon girl with golden-blonde twin pigtails "
            "fading into hot-pink and electric-blue tips (zero hairpins — no X-pin, no star hairpins), "
            "green-lensed steampunk goggles on forehead, bright blue eyes, black stealth half-mask below chin; "
            "dark charcoal hooded rogue cloak and tunic, utility belt with tiny green poison vials, dark "
            "shorts, brown leather boots (identity & costume only, facial expression and pose free per scene)."
        ),
        default_prop=(
            "Twin glowing green daggers (sheathed crossed at lower back waist belt whenever hands hold loot, "
            "dice, or gesture)."
        ),
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
        aegyo_signature="여유롭고 구수하게 능청 떠는 관전 톤(매 화 팝콘·먹방 유행어 복붙 금지).",
        acting_range="serene deadpan grin, sly scheming loot eyes, flat sprawled Feign Death flop",
        appearance_anchor=(
            "Fair-skinned sleek 3-to-3.5 head anime webtoon girl wearing a forest-green fur-trimmed ranger "
            "hood and short cape, orange-ginger hair in two thick braided pigtails framing her chin, warm "
            "amber eyes; fur-trimmed brown leather hunter coat with ammo belt, brown leggings, fur-cuffed "
            "mountain boots (identity & costume only, facial expression and pose free per scene)."
        ),
        default_prop=(
            "Wooden-and-steel Dwarf blunderbuss rifle (slung across back whenever holding loot, dice, or gesturing)."
        ),
        aliases=(
            "드워프 사냥꾼", "드워프사냥꾼", "사냥꾼", "냥꾼", "드냥",
            "dwarf_hunter", "dwarf hunter", "hunter",
        ),
        sheet_position="top-row-4",
        lore_note="Alliance Hunter (Ironforge/Dun Morogh outdoor faction).",
        companion_id="hunter_bear",
        companion_name="아기 곰",
        companion_anchor=(
            "Ultra-cute round chubby baby brown bear cub (~0.4x height, fluffy brown fur, cream muzzle, "
            "cute cat-like smile, rosy blush, pink paw pads, pom-pom tail, forest-green neckerchief) beside Dwarf Hunter."
        ),
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
        aegyo_signature="에너지 넘치고 신나게 맞장구치는 인싸 톤(고정 추임새 도배 금지).",
        acting_range="uproarious cackle, glittering gossip eyes, shocked spiky-hair lightning jolt",
        appearance_anchor=(
            "Fair-skinned sleek 3-to-3.5 head anime webtoon girl (never blue skin) wearing a sky-blue plush "
            "troll monster hood with bright red mohawk crest, floppy pierced blue ears and tiny white hood "
            "tusks; mint-teal bob hair, emerald-green eyes; sky-blue tunic and cape, brown-and-cream tribal "
            "poncho scarf, belt with 2 mini wooden totems, tribal skirt and wrapped boots (identity & costume "
            "only, facial expression and pose free per scene)."
        ),
        default_prop=(
            "Carved wooden Shaman totem staff (stowed across back when holding loot, dice, or gesturing)."
        ),
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
        aegyo_signature="순둥하고 여린 말투와 억울한 멘붕 반전(과도한 콧소리·음표 기호 남발 금지).",
        acting_range="gentle warm smile, dizzy spiral-eye faint, waterfall crying panic, puffed sulking cheeks",
        appearance_anchor=(
            "Fair-skinned sleek 3-to-3.5 head anime webtoon girl wearing a warm-brown plush tauren cow hood "
            "with curved ivory horns, cow snout with golden nose ring and floppy ears; chestnut-brown bangs, "
            "warm-brown eyes; fresh leafy-green foliage shoulder mantle over brown-and-cream suede druid "
            "tunic, braided belt with herbal pouch, dark leggings, lace-up druid boots with tiny leaf accents "
            "(identity & costume only, facial expression and pose free per scene)."
        ),
        default_prop=(
            "Gnarled wooden Druid staff with green leaves (stowed across back when hands hold scene items)."
        ),
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
        speech_style="차분하고 예의 바른 말투(상황에 따라 존댓말·반말 자연 전환), 정색할 때의 서늘한 팩폭.",
        aegyo_signature="상냥한 겉모습과 지친 현실·서늘한 흑막의 갭모에(문장 끝 하트 기호 남발 금지).",
        acting_range="exhausted dark-circle pleading look, calm polite smile, chilling pinpoint-pupil glare with forehead gloom shadow",
        appearance_anchor=(
            "Fair-skinned sleek 3-to-3.5 head anime webtoon girl (never purple/grey skin) with pastel-lavender "
            "wavy half-up ponytail, side braid, ahoge, golden crescent forehead tiara, pointed Night Elf ears "
            "with tiny gold earrings, faint pale-violet cheek markings, luminous glowing silver-white eyes "
            "(zero angel halo, zero wings); royal-purple gold-trimmed Priestess capelet over white blouse, "
            "royal-purple pleated mini-skirt, belt carrying a white-and-gold mini Holy Prayer Book on left hip "
            "and golden beaded Rosary on right hip, white knee-highs, purple-and-gold boots (identity & costume "
            "only, facial expression and pose free per scene)."
        ),
        default_prop=(
            "Golden-and-ivory Holy Cross & Sunburst Cleric Priest Staff (stowed diagonally across back when "
            "hands clasp, plead, hold items, or gesture)."
        ),
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
        personality="빨간 임프 인형을 데리고 다니며 나름 진지하지만 어딘가 허당끼가 넘치고 억울할 땐 성실하게 해명하는 흑마법사.",
        speech_style="진지하거나 성실한 구어체, 당황했을 때의 어리둥절한 반전 리액션.",
        aegyo_signature="진지한 척하다 허당미가 터지는 자연스러운 리액션(고정 말더듬·웃음소리 복붙 금지).",
        acting_range="earnest puppy-eyed helpfulness, sharp gothic smirk, flustered crimson blush, bewildered shock alongside her plush imp",
        appearance_anchor=(
            "Fair-skinned sleek 3-to-3.5 head gothic anime webtoon girl wearing a deep dark-purple Warlock hood "
            "over long jet-black twin pigtails with vivid purple highlights, violet eyes; dark-purple and "
            "charcoal hooded robe dress with purple diamond clasps and pointed cuffs, dark stockings, black "
            "buckled boots (identity & costume only, facial expression and pose free per scene)."
        ),
        default_prop=(
            "Plump grumpy red plush Imp doll (tucked under arm, perched beside her, or clipped to back cape "
            "when both hands hold scene items)."
        ),
        aliases=(
            "인간 흑마법사", "인간흑마법사", "흑마법사", "흑마", "인흑", "고흑", "악흑", "파흑",
            "human_warlock", "human warlock", "warlock",
        ),
        sheet_position="bottom-row-3",
        lore_note="Alliance Warlock (Stormwind/Elwynn/Goldshire outdoor faction).",
        companion_id="warlock_voidwalker",
        companion_name="공허방랑자",
        companion_anchor=(
            "Ultra-cute round squishy floating purple Voidwalker (~0.42x height, plump cloud body, "
            "starry lavender belly glow, warm oval eyes, purple blush, golden wrist bracers, wispy tail) beside Warlock."
        ),
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
        aegyo_signature="도도하게 뻐기다 어이없는 상황에서 정색하는 반전 톤(고정 자화자찬 문구 복붙 금지).",
        acting_range="confident starry-eyed smirk, deadpan blank white-eye freeze with star-pupils off, volcanic furious outburst",
        appearance_anchor=(
            "Fair-skinned sleek 3-to-3.5 head anime webtoon girl with silky sky-blue high side-ponytail, "
            "pointed elf ears, sparkling sky-blue star-pupil eyes; tilted royal-blue pointed wizard hat with "
            "gold band and tiny smiling white cloud-with-wing feather badge; royal-blue cloud-trimmed capelet "
            "over white-and-blue flared Mage tunic, belt with tiny fluffy white Polymorph Sheep keychain charm, "
            "dark shorts, white knee-highs, blue-and-gold boots (zero sailor uniform; identity & costume only, "
            "facial expression and pose free per scene)."
        ),
        default_prop=(
            "Wooden-and-gold Mage staff topped with a sky-blue diamond crystal (stowed across back whenever "
            "casting, serving conjured water/bread, holding loot, or gesturing)."
        ),
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
    """Render a compact, copy-paste-free 9-character cast guide for the script writer.

    Omits 200-word English costume specs (handled by `artist.py`) so the writer focuses on
    story clarity, natural voice contrast, accurate factions, fixed companions, and Clean Hand staging.
    """
    lines: list[str] = [
        "=== 고정 캐스트 9인 (전원 미소녀 — 영문 visual_prompt에서 she/her 사용 · 고정 유행어 복붙 금지) ===",
        "※ Clean Hand Rule: 전리품·방패·주사위·귀환석·물약병을 들거나 제스처할 때는 기본 무기를 등/허리에 수납하세요.",
        "※ 고정 동행 펫(주인 등장 시 컷당 1~2명 주연 제한과 무관하게 곁에서 함께 리액션): 드워프 사냥꾼 → 동글동글 아기 곰, 인간 흑마법사 → 동글동글 공허방랑자.",
    ]
    for idx, member in enumerate(CAST_BIBLE, start=1):
        faction_ko = _FACTION_KO_LABELS.get(member.faction, member.faction)
        pet_tag = f" [고정 동행 펫: {member.companion_name}]" if member.companion_name else ""
        lines.append(
            f"{idx}. {member.name} [{faction_ko}] ({member.role_tag}){pet_tag} — {member.personality} "
            f"말투: {member.speech_style}"
        )
    return "\n".join(lines)


def build_character_anchors_block(characters: list[str]) -> str:
    """Build concise Style-First (3–3.5 head sleek webtoon) + Costume & Companion Identity anchors."""
    resolved: list[CastMember] = []
    seen_ids: set[str] = set()
    for raw in characters:
        member = resolve_cast_member(raw)
        if member and member.id not in seen_ids:
            resolved.append(member)
            seen_ids.add(member.id)

    header = (
        "PROPORTIONS & STYLE FIRST (MATCH REFERENCE IMAGE 1): Sleek 3-to-3.5 head Korean anime gag "
        "webtoon girls with slender limbs, crisp thin ink, fine hair strands, natural cloth folds, "
        "2-tier cel shading, and vivid expressions. Match turnarounds for COSTUME, HAIR, HEADGEAR & "
        "COLOR IDENTITY ONLY with dynamic scene poses.\n"
        "CLEAN HAND RULE: Stow default weapons on back/belt when holding loot, shield, dice, or gesturing."
    )
    if not resolved:
        return header

    lines = [header, "CHARACTERS IN SCENE:"]
    for member in resolved:
        lines.append(
            f"- {member.name} ({member.id}): {member.appearance_anchor} "
            f"Optional default prop: {member.default_prop}"
        )
        if member.companion_id and member.companion_anchor:
            lines.append(
                f"  Fixed companion mascot ({member.companion_name} / {member.companion_id}): "
                f"{member.companion_anchor}"
            )
        if member.id == "skyborne_mage":
            lines.append(
                "  Skyborne lore note: Zephras Isle wind-elf heritage (sky-blue high side-ponytail, "
                "pointed elf ears, tilted blue wizard hat with cloud-wing badge, Polymorph Sheep charm)."
            )
    return "\n".join(lines)
