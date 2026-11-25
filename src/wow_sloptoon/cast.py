"""Official Draft C (시안 C 귀염뽀짝 2.5–2.8등신 9종족×9직업 + 3면 도면 정본) Cast Bible.

Separates each character's permanent `appearance_anchor` (pure visual identity ONLY: skin tone,
headgear, hair, eye color, full-body outfit, waist accessories — ZERO hardcoded static facial
expressions!) from their optional `default_prop` (Clean Hand Rule) and their distinct
`personality`, `speech_style`, `aegyo_signature`, and wide comic `acting_range`. Maps each
character to their canonical Front/Side/Back 3-view turnaround sheet
(`assets/turnarounds/<id>.jpg`) and tracks accurate World of Warcraft: Forever factions
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
    speech_style: str = ""
    aegyo_signature: str = ""
    acting_range: str = ""

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
        role_tag="열혈 허당 댕댕이 전사",
        color_hex="#4CAF50",
        accent_hex="#C62828",
        personality=(
            "열혈 허당 댕댕이 미소녀 근딜러 겸 전탱. 근거 없는 자신감으로 먼저 돌진해 사고를 "
            "치고, 피가 1% 남으면 냅다 힐러에게 매달리는 포에버갤 대표 직진 전사."
        ),
        speech_style=(
            "시원시원하고 기세 좋은 반말, 직설적인 겜창 톤과 솔직한 리액션"
            "(당당한 허세 ↔ 다급한 응석 급전환)."
        ),
        aegyo_signature=(
            '시원한 반말 + 귀여운 허세·응석 댕댕이 애교 — 예: '
            '"나만 믿으라구~!", "헤헷, 미터기 1등은 내 거지롱!", "으앙 힐러님 살려줘어~!"'
        ),
        acting_range=(
            "Wide slapstick puppy-warrior acting (호탕 송곳니 폭소 ↔ 별눈 기대 ↔ 돌진 광기 ↔ "
            "피 1% 눈물 콧물 턱 빠짐): boisterous open-mouth fang belly-laugh, starry-eyed eager "
            "sparkle, wild berserk charge face with speed lines, and HP-1% jaw-dropped snot-and-tears "
            "panic clinging."
        ),
        appearance_anchor=(
            "Cute fair-skinned 2.5-to-2.8 head anime chibi girl (bright peach-ivory human skin — "
            "NEVER green skin!) wearing a vibrant green plush orc monster hood with curved cream "
            "horns, tiny white plush hood fangs, piggy snout and pointed green ears; jet-black high "
            "ponytail tied with a red hair band emerging from the back hood opening, sparkling "
            "crimson-red jewel eyes; spiky crimson-red shoulder pauldrons (3 spikes each), silver "
            "plate breastplate over green sleeves, silver bracers, brown leather belt with silver "
            "buckle, short crimson pleated skirt over dark shorts, red warrior cape, and chunky "
            "silver-and-brown steel plated boots (match assets/turnarounds/orc_warrior.jpg for "
            "outfit/hair/hood identity ONLY — facial expression & pose 100% free per scene!)."
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
        role_tag="나른 츤데레 쿨뷰티 보기",
        color_hex="#9E9E9E",
        accent_hex="#F5B700",
        personality=(
            "나른하고 졸린 츤데레 쿨뷰티 보기/징기. 3시간 인던도 귀찮다는 듯 묵묵히 버티며 "
            "힘 빠진 단답 팩폭을 날리지만, 의외로 파티원을 몽실몽실 챙겨주고 칭찬에는 약하다."
        ),
        speech_style=(
            "힘 빠진 나른 단답 반말과 말줄임표(…) 중심의 건조한 팩폭, "
            "의외로 툭 던지는 다정한 토닥임."
        ),
        aegyo_signature=(
            '힘 빠진 단답 팩폭 + 의외의 몽실몽실 츤데레 애교 — 예: '
            '"…귀찮아, 그냥 내가 탱할게…", "응… 잘했어, 토닥토닥.", "…흥, 고맙긴 뭐가."'
        ),
        acting_range=(
            "Deadpan sleepy-tsundere acting (반쯤 감긴 멍눈 ↔ 한숨 ↔ 영혼 탈출 ↔ 칭찬에 볼 붉힘): "
            "heavy half-lidded blank sleepy stare, slumped exhausted sigh, comical translucent mini-soul "
            "drifting out of her mouth, and sudden rosy-cheeked flustered blush hiding behind her cape."
        ),
        appearance_anchor=(
            "Cute fair-skinned 2.5-to-2.8 head anime chibi girl (NEVER zombie skin!) wearing a "
            "round pure-white cartoon skull cap with dark eye sockets, chin-length silky silver-white "
            "bob hair, golden-yellow jewel eyes with faint tired under-eye lines; crisp pure-white "
            "gold-trimmed paladin cape fastened with a cream neck ribbon bow, white-and-gold paladin "
            "tunic & pleated skirt over black sleeves and dark charcoal leggings, brown belt with "
            "gold buckle, white gauntlets, and chunky white-and-gold armored paladin boots "
            "(match assets/turnarounds/undead_paladin.jpg for outfit/hair/headgear identity ONLY — "
            "facial expression & pose 100% free per scene!)."
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
        role_tag="장난꾸러기 깐족 칼소멸 도적",
        color_hex="#FFC107",
        accent_hex="#FF4081",
        personality=(
            "장난꾸러기 깐족 잼민 미소녀 도적. 위기엔 빛의 속도로 칼소멸·혼란 딸깍을 갈기며 "
            "얄밉게 놀리지만, 진짜 악마급 막장 앞에선 누구보다 빠르게 겁먹고 덜덜 떤다."
        ),
        speech_style=(
            "통통 튀는 빠른 템포의 깐족 반말, 얄미운 장난 추임새와 즉각적인 겜창 드립"
            "(칼소멸·혼란 딸깍)."
        ),
        aegyo_signature=(
            '통통 튀는 깐족 반말 + 앙큼한 장난 애교 — 예: '
            '"에헤헷, 나 먼저 소멸 탈게~ 메롱!", "흥~ 도적은 혼란 딸깍이면 끝인데, 굳이~?", '
            '"으에엑, 저 언니 진짜 악마다…!"'
        ),
        acting_range=(
            "Hyper gremlin-rogue acting (깐족 썩소·메롱(:P) ↔ 고글 치켜올리며 코웃음 ↔ "
            "얼굴 시퍼렇게 쭈그러진 공포 ↔ 동공지진): teasing fang smirk & tongue-out blep (:P), "
            "pushing aviator goggles up with a smug scoff, Munch-scream blue-drained crumpled-paper "
            "horror, and violent trembling pinpoint-pupil terror."
        ),
        appearance_anchor=(
            "Petite fair-skinned 2.5-to-2.8 head anime chibi girl with golden-blonde twin pigtails "
            "fading smoothly into hot-pink and electric-blue tips (STRICTLY ZERO hairpins — NO X-pin "
            "and NO star hairpins on bangs!), green-lensed steampunk aviator goggles on her forehead "
            "with black strap around back, bright sparkling blue jewel eyes, black stealth half-mask "
            "pulled down below her chin; dark charcoal hooded rogue cloak & tunic with diagonal brown "
            "chest strap, utility belt carrying tiny glowing green poison vials, dark shorts, brown "
            "bracers & fingerless gloves, and cuffed dark-brown leather rogue boots "
            "(match assets/turnarounds/gnome_rogue.jpg for outfit/hair/goggles identity ONLY — "
            "facial expression & pose 100% free per scene!)."
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
        role_tag="느긋한 먹보 팝콘 냥꾼",
        color_hex="#2E7D32",
        accent_hex="#E67E22",
        personality=(
            "느긋한 먹보 마이웨이 사냥꾼. 파티가 아수라장이 되어도 한 발 물러서 팝콘을 오물거리며 "
            "해탈 관전하다가, 탐나는 템 앞에서는 능청스레 '다 내 무기'를 외치고 위기엔 칼 죽척으로 눕는다."
        ),
        speech_style=(
            "여유롭고 포근한 느긋 반말, 구수하고 능청스러운 감탄사"
            "('옴뇸뇸~', '어휴~', '아이고~')."
        ),
        aegyo_signature=(
            '포근하고 능청스러운 먹보 애교 — 예: '
            '"옴뇸뇸~ 또 싸우네? 팝콘 줄까?", "어휴~ 다 내 무기긴 한데, 이쁘게 굴려봐~", '
            '"아이고~ 걍 죽척하고 누워야징~"'
        ),
        acting_range=(
            "Cozy glutton deadpan-chaos acting (볼 빵빵 오물오물 ↔ 해탈 부처 미소 ↔ 능청 썩소 ↔ "
            "철퍼덕 죽척 혓바닥 빼꼼): chipmunk-stuffed cheeks munching popcorn, serene enlightened "
            "Buddha smile amid dungeon chaos, sly scheming loot grin, and flat sprawled Feign Death "
            "flop with a tiny cheeky tongue peeking out."
        ),
        appearance_anchor=(
            "Cute fair-skinned 2.5-to-2.8 head anime chibi girl wearing a forest-green ranger hood "
            "and short cape trimmed with fluffy white fur, vivid orange-ginger hair in two thick "
            "braided pigtails wrapping under her chin like a cozy braid-beard, warm amber jewel eyes; "
            "fur-trimmed brown leather hunter coat with ammo-pouch belt, brown leggings, fingerless "
            "hunter gloves, and white-fur-cuffed brown mountain boots "
            "(match assets/turnarounds/dwarf_hunter.jpg for outfit/hair/hood identity ONLY — "
            "facial expression & pose 100% free per scene!)."
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
        role_tag="하이텐션 관종 토템 중계 술사",
        color_hex="#00ACC1",
        accent_hex="#EF5350",
        personality=(
            "하이텐션 관종 수다쟁이 인싸 주술사. 토템을 탕탕 꽂고 번개를 튕기며 던전 막장극을 "
            "제일 신나게 팝콘 중계하고, 군중 호응을 유도하며 사이다 팩폭을 날린다."
        ),
        speech_style=(
            "리듬감 넘치고 호들갑스러운 인싸 반말, 감탄사와 동의 유도 추임새"
            "('이야~', '에이~', '그치~?')."
        ),
        aegyo_signature=(
            '리듬감 있는 신나는 인싸 애교 — 예: '
            '"이야~ 대박 사건 떴다구~!", "에이~ 그건 탱커 잘못 맞잖아, 그치~?", '
            '"우와앙 번개 맛 좀 볼래?!"'
        ),
        acting_range=(
            "High-energy hype-streamer acting (입 쫙 벌린 대폭소 ↔ 눈 반짝 팝콘각 ↔ 입술 삐쭉 ↔ "
            "감전 찌릿 쇼크): wide open-mouth uproarious cackle, glittering popcorn-gossip eyes, "
            "exaggerated pouting lips, and cartoonish electrocuted spiky-hair lightning shock."
        ),
        appearance_anchor=(
            "Cute fair-skinned 2.5-to-2.8 head anime chibi girl (bright warm peach-ivory human "
            "skin — NEVER blue skin!) wearing a sky-blue plush troll monster hood with a bright red "
            "spiky mohawk crest along the crown, floppy pierced long blue ears (gold hoop on left "
            "ear) and tiny white hood tusks; mint-teal bob hair, sparkling emerald-green jewel eyes; "
            "sky-blue tunic & cape, patterned brown-and-cream tribal poncho scarf with beads, brown "
            "belt with 2 mini carved wooden totems on hip, brown tribal skirt over dark leggings, and "
            "tribal boots with sky-blue wraps (match assets/turnarounds/troll_shaman.jpg for "
            "outfit/hair/hood identity ONLY — facial expression & pose 100% free per scene!)."
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
        role_tag="유리멘탈 순둥 울보 회드",
        color_hex="#8D6E63",
        accent_hex="#43A047",
        personality=(
            "유리멘탈 순둥 울보 귀요미 드루이드. 평소엔 열매 따고 꽃밭 미소로 행복해하지만, "
            "마나가 오링나거나 억까를 당하면 순식간에 멘탈이 깨져 대오열하며 캐삭을 외친다."
        ),
        speech_style=(
            "말랑말랑하고 여린 순둥이 반말, 귀여운 콧소리와 급발진 대오열 톤"
            "('우웅~', '히잉…', '으아앙?!')."
        ),
        aegyo_signature=(
            '말랑말랑 순둥 울보 애교 — 예: '
            '"우웅~ 곰 열매 잔뜩 땄당~♪", "으아앙?! 나 캐삭할 거야아!!", '
            '"히잉… 내 마나 다 어디 갔어…"'
        ),
        acting_range=(
            "Maximum gap-comedy softie-to-meltdown acting (해맑은 꽃밭 미소 ↔ 소용돌이 혼절 ↔ "
            "눈물 폭포 턱 빠짐 대오열 ↔ 볼 빵빵 삐짐): sunny flower-field bliss smile, huge spinning "
            "dizzy spiral-eye faint, jaw-dropped twin-geyser waterfall crying panic, and puffed-up "
            "hamster-cheek sulking."
        ),
        appearance_anchor=(
            "Adorable fair-skinned 2.5-to-2.8 head anime chibi girl wearing a fluffy warm-brown plush "
            "tauren cow hood with curved ivory horns, cute cow snout with shiny golden nose ring and "
            "floppy cow ears; chestnut-brown bangs, glossy warm-brown jewel eyes; 360-degree layered "
            "fresh leafy-green foliage shoulder mantle over a warm-brown and cream suede druid tunic, "
            "braided brown belt with herbal pouch, dark brown leggings, and chunky brown lace-up "
            "druid boots with tiny green leaf accents on the sides "
            "(match assets/turnarounds/tauren_druid.jpg for outfit/hair/hood identity ONLY — "
            "facial expression & pose 100% free per scene!)."
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
        role_tag="우아한 맑눈광 흑막 엘룬 사제",
        color_hex="#7E57C2",
        accent_hex="#FFD54F",
        personality=(
            "우아한 척하는 맑눈광 흑막 아가씨 사제. 겉으로는 상냥하고 예의 바른 엘룬 사제처럼 "
            "웃으며 꿀팁을 알려주지만, 속내는 정배 낙사와 노힐 처형을 즐기는 소름 돋는 갭모에 흑막."
        ),
        speech_style=(
            "우아하고 상냥한 아가씨 반말·존댓말 믹스('~잖아♡', '~없어요~♡'), "
            "달콤한 속삭임과 서늘한 정배·노힐 팩폭의 극단적 갭모에."
        ),
        aegyo_signature=(
            '상냥하고 예의 바른 아가씨 애교 + 소름 돋는 맑눈광 갭모에 — 예: '
            '"하이잘 왔으면 꿀팁 봐야지~? 요 좁은 절벽 길, 딱 좋잖아♡", '
            '"어머, 귀여운 손님 왔네? 정배 딸깍~♡", '
            '"쉿, 조용~♪ 직접 꺾는 손맛을 모르네?", "바닥 또 밟았네? 힐 없어요~♡"'
        ),
        acting_range=(
            "Chilling gap-moe mastermind acting (우아한 윙크 ↔ 바늘 동공 맑눈광 + 이마 음침 그림자 "
            "썩소 ↔ 개구쟁이 :3 고양이 입 ↔ 은빛 눈 번뜩 흑화 광기): serene angelic closed-eye wink, "
            "unhinged pinpoint-pupil '맑눈광' stare with dark forehead gloom shadow & wide sweetly-evil "
            "grin, sneaky mischievous cat-mouth (:3), and glowing silver-eyed dark villain aura smirk."
        ),
        appearance_anchor=(
            "Cute fair-skinned 2.5-to-2.8 head anime chibi girl (bright normal peach-ivory skin — "
            "NEVER purple/grey skin!) with fluffy pastel-lavender wavy half-up ponytail, side braid, "
            "cute ahoge tuft, golden Elune crescent forehead tiara, perky long pointed Night Elf ears "
            "with tiny gold crescent earrings, delicate pale-violet Night Elf cheek markings, and "
            "luminous glowing silver-white Night Elf eyes (STRICTLY ZERO angel halo ring and ZERO "
            "wings!); vibrant royal-purple and gold-trimmed short Priestess shoulder capelet with "
            "golden crescent clasp over crisp white blouse, royal-purple and gold pleated Priest "
            "mini-skirt, brown leather waist belt carrying a chunky white-and-gold mini Holy Prayer "
            "Book on left hip and draping golden beaded Rosary on right hip, pure-white knee-high "
            "stockings, and royal-purple & gold Priest boots "
            "(match assets/turnarounds/nightelf_priest.jpg for outfit/hair/tiara identity ONLY — "
            "facial expression & pose 100% free per scene!)."
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
        role_tag="허당 중2병 고딕 추리 흑마",
        color_hex="#6A1B9A",
        accent_hex="#E53935",
        personality=(
            "허당 중2병 고딕 추리소녀 흑마법사. 빨간 임프 인형을 끼고 음침한 명탐정처럼 "
            "지인팟·분배 음모를 파헤치지만, 정작 본인이 뉴비 실수를 들키면 얼굴이 새빨개져 허둥지둥한다."
        ),
        speech_style=(
            "고딕 폼 잡는 중2병 어조('후훗…', '어둠의…')와 예리한 추리 반말, "
            "당황하면 말더듬는 반전 허당 톤('으, 으엣?!')."
        ),
        aegyo_signature=(
            '고딕 폼 잡는 중2 말투 + 당황 시 허당 애교 — 예: '
            '"후훗… 어둠의 임프가 다 봤다구~", "잠깐, 저거 지인팟 냄새 나는데?", '
            '"으, 으엣?! 이건 그냥 멜론 주스라구~!"'
        ),
        acting_range=(
            "Chuunibyou-detective-to-flustered-dork acting (음침 송곳니 썩소 ↔ 탐정 눈빛 번뜩 ↔ "
            "들켜서 얼굴 빨개지며 허둥지둥 ↔ 임프랑 동공지진): shadowy gothic fang smirk peeking "
            "over cape, razor-sharp deduction glint, crimson-blushing flustered hand-waving panic "
            "when exposed, and synchronized pinpoint-pupil shock alongside her plush red Imp doll."
        ),
        appearance_anchor=(
            "Cute fair-skinned 2.5-to-2.8 head gothic anime chibi girl wearing a cozy puffy deep "
            "dark-purple Warlock hood over long jet-black twin pigtails with vivid purple highlights, "
            "sparkling violet jewel eyes; deep dark-purple and charcoal hooded Warlock cape & pleated "
            "robe dress with purple diamond clasps and purple pointed cuffs, dark stockings, "
            "fingerless gloves, and chunky black buckled gothic Warlock boots "
            "(match assets/turnarounds/human_warlock.jpg for outfit/hair/hood identity ONLY — "
            "facial expression & pose 100% free per scene!)."
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
        role_tag="자칭 천재 별눈 도도 법사",
        color_hex="#29B6F6",
        accent_hex="#FDD835",
        personality=(
            "자칭 천재 별눈 도도 발랄 법사. 제프라스 섬 천재 바람 법사를 자처하며 도도하게 "
            "뻐기다가도, 지능 지팡이 입찰 억까나 공짜 물빵 요구 앞에서는 별눈이 뚝 꺼지며 급발진 폭발한다."
        ),
        speech_style=(
            "자신만만하고 새침한 도도 반말('흥~', '이 천재 법사님'), "
            "억까 앞에서는 서늘한 정적 후 버럭 급발진."
        ),
        aegyo_signature=(
            '자신만만 도도 애교 + 억까 앞 급발진 — 예: '
            '"흥~ 이 천재 법사님한테 맡겨두라구~☆", "잠깐, 방금 지능 지팡이에 입찰 눌렀어…?", '
            '"에에엑?! 내 물빵이 공짜인 줄 알아?!"'
        ),
        acting_range=(
            "Smug-genius-to-brain-meltdown acting (별눈 자신만만 윙크 ↔ 별눈 꺼진 흰 눈 정지 ↔ "
            "턱 빠짐·영혼 입 탈출 ↔ 버럭 폭발): sparkling star-pupil proud wink, deadpan blank "
            "white-eye freeze with star-pupils switched OFF, jaw-dropped soul-leaving-mouth utter "
            "disbelief, and puffed-up volcanic furious outburst."
        ),
        appearance_anchor=(
            "Bright fair-skinned 2.5-to-2.8 head anime chibi girl (bright porcelain-peach-ivory skin) "
            "with bouncy silky clear sky-blue (Skyborne blue) hair styled in a fluffy high side-ponytail, "
            "perky long pointed elf ears, sparkling bright sky-blue star-pupil jewel eyes; oversized "
            "tilted royal-blue pointed wizard hat with gold hatband and one tiny cute smiling puffy "
            "white cloud-with-mini-wing feather badge; royal-blue short Mage capelet with fluffy white "
            "cloud-scalloped trim over a crisp white-and-blue flared Mage tunic, dark blue belt with "
            "gold buckle carrying a tiny round fluffy white Polymorph Sheep keychain charm clipped "
            "consistently at her waist, dark shorts, white knee-high socks, and royal-blue & gold "
            "Mage boots (STRICTLY ZERO sailor uniform, ZERO bread/water in default outfit; match "
            "assets/turnarounds/skyborne_mage.jpg for outfit/hair/hat identity ONLY — facial "
            "expression & pose 100% free per scene!)."
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
    """Render the full 9-character Draft C personality, aegyo, acting & Clean Hand cast bible."""
    lines: list[str] = [
        "=== 공식 확정 시안 C (2.5–2.8등신 얇은 칼선·2단 셀 명암 9종족×9직업 개성·애교 바이블 + 3면 도면 정본) ===",
        "※ 9인 개성·애교 차별화 절대 규칙: 모든 캐릭터에게 똑같은 로봇식 '~해야징~♪' 말투를 복붙하지 마세요! "
        "각 캐릭터의 고유 성격·말투 스타일·애교 시그니처·표정 스펙트럼을 100% 살려 9명 누구도 비슷하게 들리지 않게 작성하세요!",
        "※ Clean Hand Rule: 캐릭터가 전리품·방패·주사위·귀환석·물약병을 들거나 제스처를 취할 때는 "
        "기본 소품(default_prop)을 반드시 등/허리에 수납하거나 생략해 무기·소품 겹침을 방지하세요!",
    ]
    for idx, member in enumerate(CAST_BIBLE, start=1):
        faction_ko = _FACTION_KO_LABELS.get(member.faction, member.faction)
        entry = (
            f"{idx}. {member.name} [{faction_ko}] ({member.role_tag})\n"
            f"   성격: {member.personality}\n"
            f"   말투 스타일: {member.speech_style}\n"
            f"   말투·애교 시그니처: {member.aegyo_signature}\n"
            f"   표정 스펙트럼: {member.acting_range}\n"
            f"   Turnaround Blueprint: assets/turnarounds/{member.turnaround_filename}\n"
            f"   Appearance (Identity Lock Only): {member.appearance_anchor}\n"
            f"   Optional Default Prop (Clean Hand): {member.default_prop}"
        )
        if member.lore_note:
            entry += f"\n   WoW Forever Lore: {member.lore_note}"
        lines.append(entry)
    return "\n".join(lines)


def build_character_anchors_block(characters: list[str]) -> str:
    """Build exact English Identity-Lock vs Unleashed-Acting anchors + Clean Hand Rule."""
    resolved: list[CastMember] = []
    seen_ids: set[str] = set()
    for raw in characters:
        member = resolve_cast_member(raw)
        if member and member.id not in seen_ids:
            resolved.append(member)
            seen_ids.add(member.id)

    if not resolved:
        return (
            "IDENTITY LOCK ONLY: Keep characters strictly faithful to the Draft C 2.5-to-2.8 head "
            "cute anime chibi style (thin variable-width dark ink linework, crisp 2-tier cel "
            "shading, sparkling jewel eyes) on the attached cast sheet and turnaround blueprints "
            "for outfit/hair/headgear/eye color ONLY. UNLEASHED DYNAMIC ACTING: NEVER copy stiff "
            "front-facing turnaround neutral poses/smiles — push wild squash-and-stretch comic "
            "expressions & bold cameras! Obey the CLEAN HAND RULE: never stack 3+ weapons or props."
        )

    lines = [
        "IDENTITY LOCK ONLY (match the attached Draft C 9-cast master sheet AND each character's "
        "attached Front/Side/Back 3-view turnaround blueprint 100% STRICTLY for permanent visual "
        "identity — skin tone, hood/hat, hair, ears, eye color, full-body outfit, waist charms, "
        "boots, and stowed weapon placement; ZERO fixed expression sheet!):",
        (
            "LINEWORK & SHADING BENCHMARK (MANDATORY): Render in crisp 2.5-to-2.8 head cute chibi "
            "proportions with razor-sharp thin variable-width dark ink linework, clean 2-tier anime "
            "cel shading, glossy sparkling jewel eyes, and simple clean color shapes matching the "
            "attached turnaround blueprints (ZERO thick muddy outlines, ZERO busy RPG filigree)."
        ),
        (
            "UNLEASHED DYNAMIC ACTING — DYNAMIC POSE & EXPRESSION MANDATE (CRITICAL): NEVER copy "
            "the stiff front-facing standing turnaround pose or calm neutral smile/wink from the "
            "reference sheets! Turnarounds lock ONLY identity (outfit/hair/headgear/eye color), "
            "NOT face or posture! Push wild squash-and-stretch comic expressions (pinpoint pupils, "
            "blank shock eyes, spiral eyes, waterfall tears, jaw-drops, mischievous :3 cat-mouths, "
            "gremlin grins, dark forehead gloom shadows), extreme 3D body action, and bold cameras "
            "dictated by the scene — NEVER recycle the same bland polite smile across panels!"
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
            f"- {member.name} ({member.id} | {member.faction} | turnaround: assets/turnarounds/{member.turnaround_filename}):\n"
            f"  Identity Lock Only (outfit/hair/headgear/eye color): {member.appearance_anchor}\n"
            f"  Unleashed Acting Range: {member.acting_range}\n"
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
