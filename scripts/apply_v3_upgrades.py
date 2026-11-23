"""
V3 Directing Upgrade for slice ep011 to ep022.
Faithfully recreates original concept posts & screenshots:
- Extras, crowds, corpse piles, mobs, bosses, and authentic in-game situations.
- Eliminates forced 2-person standing talk-show banter.
- Dynamic cinematic camera variety (OTS, low-angle, high-angle, dutch-tilt, side-profile, back-view, slapstick).
- Clean hand rule, tank shield rule, 100% pure white outer background, strict anonymity.
"""

import json
from pathlib import Path
from wow_sloptoon.models import EpisodeScript
from wow_sloptoon.writer import audit_script_quality
from wow_sloptoon.artist import build_cut_image_prompt

V3_UPGRADES = {}

# ---------------------------------------------------------------------------
# EP011: 호드 쪼렙새끼들 싸가지없노 (Post #110173)
# Original screenshot: A stone mountain passage littered with multiple dead lowbie
# corpses/skeletons lying face down on the ground!
# ---------------------------------------------------------------------------
V3_UPGRADES["ep011"] = [
    {
        "cut_index": 1,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["드워프 사냥꾼"],
        "speaker": "드워프 사냥꾼",
        "dialogue": "오, 호드 쪼렙들\n침낭 메고 가네~\n귀여우니 봐준다.",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Over-the-shoulder (OTS) diagonal shot from behind the forest-green hood and shoulder of the Dwarf Hunter "
            "girl in the foreground-left, looking down along the Thandol Span stone bridge corridor where a line of tiny distant "
            "Horde travelers with quilted bedrolls stroll past. Dwarf Hunter (forest-green hood, orange braided pigtails like a "
            "beard, amber eyes) sits munching popcorn from a blank red-striped bucket with a warm benevolent veteran smile, "
            "wooden blunderbuss slung across her back. Lower two-thirds framing, top 35% pure white (#FFFFFF) headroom. "
            "100% pure solid #FFFFFF white borderless background, zero text, zero UI, medium 2.5-3 head chibi scale."
        ),
    },
    {
        "cut_index": 2,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["드워프 사냥꾼"],
        "speaker": "드워프 사냥꾼",
        "dialogue": "/인사 /인사~\n반가워 쪼렙들!\n조심히 지나가렴♪",
        "wordless": False,
        "tail_target": "right",
        "visual_prompt": (
            "Side-profile 90-degree action shot of the Dwarf Hunter girl standing on the right half of the Thandol Span stone bridge, "
            "leaning forward with lively momentum and waving one hand high enthusiastically in a friendly /wave emote. Her face beams "
            "with a wide closed-eye anime smile, cute pink blushing cheeks, and tiny floating heart sparkles. Her wooden blunderbuss "
            "rifle is sheathed on her back, hands free. Positioned cleanly on the right half, leaving generous pure white (#FFFFFF) "
            "space across the entire left 48% for dialogue bubble. 100% pure solid #FFFFFF white borderless background, zero text, "
            "zero UI, medium chibi scale."
        ),
    },
    {
        "cut_index": 3,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["오크 전사", "타우렌 드루이드"],
        "speaker": "오크 전사",
        "dialogue": "흥, 얼라 고렙이\n손 흔드네?\n씹고 침낭퀘 가자~",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Low-angle shot looking up at the two lowbie Horde girls marching arrogantly toward the right through the stone corridor, "
            "leading a column of lowbie travelers with quilted tan wool bedrolls strapped on their backs. On the left, the Orc Warrior girl "
            "(green onesie hood, piggy snout, black ponytail, crimson eyes) tilts her nose up with a smug sneer and waves dismissively "
            "sideways. On the right, the Tauren Druid girl (cow hood with horns and golden nose ring) sticks her tongue out "
            "childishly. Axe and staff stowed on backs. Lower two-thirds framing, top 35% pure white (#FFFFFF) headroom. "
            "100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 4,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["드워프 사냥꾼"],
        "speaker": None,
        "dialogue": None,
        "wordless": True,
        "tail_target": "center",
        "visual_prompt": (
            "Dutch-tilt dramatic close-up comedic freeze-frame of the Dwarf Hunter girl, completely wordless and frozen in shock. "
            "A deep sinister purple shadow falls over her amber eyes, which have turned into blank unblinking pinpoint white dots. "
            "Her mouth is frozen in an eerie polite smile with a twitching eyebrow, while dark purple cartoon aura sparks crackle "
            "around her. Her hands slowly grip the blunderbuss rifle from her back. Centered framing filling ~78% of canvas height, "
            "tilted dynamic angle. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 5,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["드워프 사냥꾼", "오크 전사"],
        "speaker": "드워프 사냥꾼",
        "dialogue": "인사만 받아줬어도\n너네들은 무사히\n침낭퀘 했을 텐데…",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "High-angle shot looking down directly recreating the author's real screenshot: inside the Thandol Span stone bridge corridor, "
            "the cobblestone floor is completely littered with a sprawling comic pile of 6-7 defeated lowbie Horde corpses and cute cartoon "
            "skeletons! Knocked-out lowbies lie face down and sprawled flat in slapstick postures with swirling spiral eyes, their tan "
            "wool bedrolls knocked loose and scattered everywhere across the stone corridor. Standing above the bridge corridor carnage "
            "on the left, Dwarf Hunter rests the smoking barrel of her wooden blunderbuss on her shoulder with a cold, sarcastic smirk. "
            "Lower two-thirds framing, top 35% pure white (#FFFFFF) headroom. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 6,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["드워프 사냥꾼", "타우렌 드루이드"],
        "speaker": "드워프 사냥꾼",
        "dialogue": "근데 인사를\n안 받아줬잖아?\n/인사~♪",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Back-view shot seen from behind of the Dwarf Hunter girl walking away toward the left along the Thandol Span cobblestone corridor, "
            "turning her back to the knocked-out Tauren Druid and scattered lowbie skeletons in the background. The Dwarf Hunter looks back "
            "over her shoulder with a cheerful closed-eye wink, tossing a playful peace sign /wave emote, blunderbuss slung on her back. "
            "Cleanly framed with generous pure white (#FFFFFF) space on the right 46% for dialogue bubble. 100% pure solid #FFFFFF white "
            "borderless background, zero text, zero UI."
        ),
    },
]

# ---------------------------------------------------------------------------
# EP012: 마라우돈 흑석반지 흑마가 입찰함 ㅋㅋ (Post #109482)
# Original screenshot: Party chat log showing Warlock rolling Need on Blackstone Ring,
# Hunter asking why, then Warlock & Shaman leaving party together ("...님이 파티를 떠났습니다")!
# ---------------------------------------------------------------------------
V3_UPGRADES["ep012"] = [
    {
        "cut_index": 1,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["드워프 사냥꾼", "인간 흑마법사"],
        "speaker": "드워프 사냥꾼",
        "dialogue": "흑석 반지 떴다!\n냥꾼이랑 고술님\n둘이 굴리면 되겠네~",
        "wordless": False,
        "tail_target": "left",
        "item_tooltip": {"item_name": "흑석 반지", "wowhead_item_id": 17713},
        "visual_prompt": (
            "Over-the-shoulder (OTS) diagonal shot from behind the green-hooded shoulder of the Dwarf Hunter girl in foreground-left, "
            "pointing eagerly toward a rustic wooden dungeon chest on the right. Above the chest hovers the gleaming golden "
            "Blackstone Ring. In the background-right, the Human Warlock girl (dark purple horned cowl, black twintails, violet eyes) "
            "leans forward with starry-eyed obsession and a cunning smile, lantern staff stowed on her back. Lower two-thirds "
            "framing, top 35% pure white (#FFFFFF) headroom for tooltip and bubble. 100% pure solid #FFFFFF white borderless background, "
            "zero text, zero UI."
        ),
    },
    {
        "cut_index": 2,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["인간 흑마법사"],
        "speaker": "인간 흑마법사",
        "dialogue": "어머~ 저도 눌렀는데\n제가 먹었네요?\n반지 잘 쓸게요~",
        "wordless": False,
        "tail_target": "right",
        "visual_prompt": (
            "Low-angle shot looking up at the Human Warlock girl standing proudly on the right half, holding the glowing golden "
            "Blackstone Ring pinched between her thumb and index finger. She rests her other hand against her cheek with an "
            "exaggerated innocent smug sneer and fluttering eyelashes, pretending it was an honest accident. Dark purple robe "
            "flowing, soul staff sheathed on back. Positioned cleanly on the right half, leaving generous pure white (#FFFFFF) "
            "space across the left 48% for dialogue bubble. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 3,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["드워프 사냥꾼", "인간 흑마법사"],
        "speaker": "드워프 사냥꾼",
        "dialogue": "캐스터 흑마님이\n전투력 반지를\n왜 굴려요??",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Dutch-tilt slapstick action camera with dramatic diagonal composition. Dwarf Hunter girl on the left slams both hands "
            "onto a floating stone pedestal in utter outrage, her jaw dropping open in a cartoon scream with sharp jagged teeth and "
            "flying sweat drops, blunderbuss on back. On the right, Human Warlock casually polishes the golden ring against her "
            "sleeve with closed eyes and a smug hum. Lower two-thirds framing, top 35% pure white (#FFFFFF) headroom. 100% pure "
            "solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 4,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["드워프 사냥꾼", "트롤 주술사"],
        "speaker": "드워프 사냥꾼",
        "dialogue": "둘이 같은 길드였어?!\n고술님 살펴보기...\n반지 칸 하나 비었네?!",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Side-profile 90-degree action shot of Dwarf Hunter girl tiptoeing sneaking right up behind the Troll Shaman girl "
            "(teal hood, tusks, spiky blue hair). Hunter inspects her with an oversized magnifying glass, eyes narrowed in sharp "
            "detective suspicion. Troll Shaman flinches with giant cartoon sweat droplets spraying from her head, clutching her "
            "empty finger in panic, totem staff stowed on back. Positioned on the left and center, leaving generous pure white "
            "(#FFFFFF) space on the right 46% for dialogue bubble. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 5,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["트롤 주술사"],
        "speaker": None,
        "dialogue": None,
        "wordless": True,
        "tail_target": "center",
        "visual_prompt": (
            "High-angle shot looking down at the Troll Shaman girl in a signature comedic freeze-frame, completely wordless. "
            "Caught dead red-handed, she is kneeling on the floor with her hands rigidly clamped behind her back, her face drained "
            "pale blue, eyes turned into chaotic spinning spirals with waterfall anime sweat gushing down her cheeks. Totem staff "
            "propped on the ground beside her. Centered dramatic framing filling ~78% of canvas height. 100% pure solid #FFFFFF "
            "white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 6,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["드워프 사냥꾼", "인간 흑마법사"],
        "speaker": "드워프 사냥꾼",
        "dialogue": "반지 넘겨주고 둘 다\n동시에 파탈하네…\n와 진짜 레전드다 ㅋ",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Back-view shot seen from behind of the Human Warlock and Troll Shaman sneaking away together into a swirling cyan "
            "Hearthstone vortex on the right, seen from behind with smug giggles and ring pocketed. On the left, Dwarf Hunter "
            "stands alone in front of the empty dungeon chest, arms dropped limp, staring in disbelief at the empty party list. "
            "Clean framing with generous pure white (#FFFFFF) space on the left 48% for dialogue bubble. 100% pure solid #FFFFFF "
            "white borderless background, zero text, zero UI."
        ),
    },
]

# ---------------------------------------------------------------------------
# EP013: 팁) 병신 냥꾼 거르는 방법 (Post #23385)
# Original post: Lowbie pet aggro + Multi-shot pulls entire room, party wipes,
# Hunter survives alone with Feign Death, sits and eats conjured food among corpses!
# ---------------------------------------------------------------------------
V3_UPGRADES["ep013"] = [
    {
        "cut_index": 1,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["오크 전사", "드워프 사냥꾼"],
        "speaker": "오크 전사",
        "dialogue": "냥꾼님...\n펫 레벨이 왜\n이렇게 낮아요?",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Over-the-shoulder (OTS) diagonal shot from behind the spiky red pauldron of the Orc Warrior tank in foreground-left, "
            "holding a 1H broadsword and sturdy round iron shield. Looking toward the Dwarf Hunter girl in the background who "
            "cheerfully pets a ridiculously tiny, knee-high baby boar pet with a warm blissful grin. Blunderbuss slung on Hunter's "
            "back. Lower two-thirds framing, top 35% pure white (#FFFFFF) headroom. 100% pure solid #FFFFFF white borderless background, "
            "zero text, zero UI."
        ),
    },
    {
        "cut_index": 2,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["드워프 사냥꾼"],
        "speaker": "드워프 사냥꾼",
        "dialogue": "방금 길들였어요~\n렙업 귀찮아서\n인던에서 키우려고!",
        "wordless": False,
        "tail_target": "right",
        "visual_prompt": (
            "Side-profile 90-degree action shot of the Dwarf Hunter girl standing on the right half, puffing her cheeky cheeks "
            "and pointing proudly to herself with her thumb. She beams with an unbothered, cheerful closed-eye grin and sparkling "
            "yellow stars around her head, blunderbuss on back, little baby boar napping at her feet. Positioned cleanly on the "
            "right half, leaving generous pure white (#FFFFFF) space across the left 48% for dialogue bubble. 100% pure solid "
            "#FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 3,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["오크 전사", "드워프 사냥꾼"],
        "speaker": "오크 전사",
        "dialogue": "펫이 애드 냈잖아요!\n일제 사격은 또 왜?!\n다 몰려온다!!",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Dutch-tilt slapstick action camera with explosive comedic panic! Dark cartoon monster silhouette mobs swarming in "
            "from the right edge! In the foreground-left, Orc Warrior screams in terror with a massive jaw-drop, frantically raising "
            "her sturdy round shield. In the background, Dwarf Hunter fires her wooden blunderbuss wildly in a chaotic spray of sparks "
            "and dynamic speed lines (Multi-Shot disaster)! Lower two-thirds framing, top 35% pure white (#FFFFFF) headroom. 100% pure "
            "solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 4,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["나이트엘프 사제", "드워프 사냥꾼"],
        "speaker": "나이트엘프 사제",
        "dialogue": "파티 다 누웠는데…\n혼자 죽척 풀고\n물빵 드세요…?",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "High-angle shot looking down at the disastrous wipe scene: the entire party (Orc Warrior tank and party extra dps) "
            "lies dead and sprawled across the stone floor in comical slapstick defeat with curly ghost wisps rising. Dwarf Hunter "
            "sits cross-legged right among the corpses, having canceled Feign Death, casually chewing conjured bread and sipping "
            "from a fantasy corked glass potion flask! Floating above the bodies on the left is the translucent glowing blue ghost "
            "of the Night Elf Priest, jaw dropped in total shock. Clean framing leaving pure white (#FFFFFF) space on left 46% for bubble. "
            "100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 5,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["나이트엘프 사제"],
        "speaker": None,
        "dialogue": None,
        "wordless": True,
        "tail_target": "center",
        "visual_prompt": (
            "Low-angle shot looking up at the translucent ghost of the Night Elf Priest in a signature comedic freeze-frame, "
            "completely wordless. Her soul is literally escaping out of her open mouth as a tiny wispy ghost, her eyes blank "
            "unblinking white voids of total existential shock, crescent staff fading into wisps behind her, cracking dark cartoon "
            "lines of despair radiating around her head. Centered dramatic framing filling ~78% of canvas height. 100% pure solid "
            "#FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 6,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["드워프 사냥꾼", "오크 전사"],
        "speaker": "드워프 사냥꾼",
        "dialogue": "냥꾼이 왜 욕먹냐고?\n잘 알지~\n내가 해봤으니까!",
        "wordless": False,
        "tail_target": "right",
        "visual_prompt": (
            "Back-view shot seen from behind of the Dwarf Hunter girl walking away toward the right, turning her back to the "
            "kneeling defeated ghosts of the wiped party in the background. The Dwarf Hunter turns her head back over her shoulder "
            "with a shameless smug wink and a proud thumbs-up, blunderbuss slung across her back. Cleanly positioned leaving generous "
            "pure white (#FFFFFF) space on the left 48% for dialogue bubble. 100% pure solid #FFFFFF white borderless background, "
            "zero text, zero UI."
        ),
    },
]

# ---------------------------------------------------------------------------
# EP014: 내가 징기로 골드 버는 법 공유함 (Post #109167)
# Original screenshot: '9골드 95실버 23쿠퍼를 얻었습니다.' vendor sell gold message!
# Ret paladin begs for unused heal/tank gear then vendor sells to NPC for nearly 10g!
# ---------------------------------------------------------------------------
V3_UPGRADES["ep014"] = [
    {
        "cut_index": 1,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["언데드 성기사", "나이트엘프 사제"],
        "speaker": "언데드 성기사",
        "dialogue": "아무도 입찰 안 하면…\n힐템으로 써도\n될까요?",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Over-the-shoulder (OTS) diagonal shot from behind the mooncloth cowl and pointed ears of the Night Elf Priest in "
            "foreground-right. Looking toward the Undead Paladin girl on the left (ragged cowl, grey skin, gold eyes, black-and-gold "
            "plate armor) who is kneeling on one knee, clasping her hands beneath her chin with enormous shimmering puppy-dog "
            "anime eyes and waterfall tears, pleading desperately for the dropped healer cloth gear hovering on a stone pedestal. "
            "Holy hammer sheathed at her hip. Lower two-thirds framing, top 35% pure white (#FFFFFF) headroom. 100% pure solid "
            "#FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 2,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["언데드 성기사"],
        "speaker": "언데드 성기사",
        "dialogue": "진짜 꿀단지는 탱템.\n전탱님 안 쓰는 부위\n미리 다 조사해 뒀지.",
        "wordless": False,
        "tail_target": "right",
        "visual_prompt": (
            "Low-angle shot looking up at the Undead Paladin girl on the right half, grinning with a sinister vampire-like sneer "
            "and glowing yellow eyes. She holds a small leather-bound notepad and charcoal pencil, flipping through detailed "
            "armor checklists, her heavy holy hammer resting against her waist. Positioned cleanly on the right half, leaving generous "
            "pure white (#FFFFFF) space across the left 48% for dialogue bubble. 100% pure solid #FFFFFF white borderless background, "
            "zero text, zero UI."
        ),
    },
    {
        "cut_index": 3,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["언데드 성기사", "오크 전사"],
        "speaker": "언데드 성기사",
        "dialogue": "이 탱템… 부특으로\n먹어도 될까요 ㅠㅠ",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Dutch-tilt slapstick action camera. Undead Paladin dramatically lunging down onto the floor, clutching the bottom rim "
            "of the Orc Warrior tank's sturdy steel tower shield with both hands, sobbing melodramatically with fountain anime tears. "
            "The Orc Warrior tank (holding a 1H sword and shield) flinches backward in bewildered shock with giant sweat drops popping "
            "above her helmet. Lower two-thirds framing, top 35% pure white (#FFFFFF) headroom. 100% pure solid #FFFFFF white borderless "
            "background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 4,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["언데드 성기사"],
        "speaker": "언데드 성기사",
        "dialogue": "상점에 쫙 팔면\n한 바퀴에 10골드~\n징기는 꿀통이야♪",
        "wordless": False,
        "tail_target": "right",
        "visual_prompt": (
            "Side-profile 90-degree action shot recreating the screenshot's vendor loot sell! Undead Paladin girl stands at a rustic "
            "wooden vendor merchant counter, gleefully dumping an armful of heavy armor and shields onto the table, while the merchant "
            "hands over a giant leather pouch bursting with gold and silver coins (nearly 10 gold!). Paladin's eyes sparkle with pure "
            "greed, hammer slung on back. Positioned on the right half, leaving generous pure white (#FFFFFF) space across left 48% "
            "for dialogue bubble. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 5,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["오크 전사"],
        "speaker": None,
        "dialogue": None,
        "wordless": True,
        "tail_target": "center",
        "visual_prompt": (
            "High-angle shot looking down at the Orc Warrior tank in a signature comedic freeze-frame, completely wordless. "
            "Still holding her 1H sword and round shield, she is petrified in stone-gray shock with jaw dropped to her chest, "
            "pupils reduced to trembling white dots, and her soul literally escaping her mouth like a wispy phantom upon realizing "
            "she was farmed as a free vendor trash scout! Centered dramatic framing filling ~78% of canvas height. 100% pure solid "
            "#FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 6,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["언데드 성기사", "오크 전사"],
        "speaker": "언데드 성기사",
        "dialogue": "그래도 양심은\n있어요.\n물어는 봤잖아요?",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Back-view shot seen from behind of the Undead Paladin girl walking away toward the dungeon portal arch on the left, "
            "turning her back to the stunned Orc Warrior who remains slumped in the background. The Paladin looks back over her "
            "shoulder with an innocent angel halo gesture above her ragged hood and a sly cheeky wink. Cleanly framed with generous "
            "pure white (#FFFFFF) space on the right 46% for dialogue bubble. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
]

# ---------------------------------------------------------------------------
# EP015: 새벽 나락팟 개염병났네 (Post #109555)
# Original screenshots: Party frames & whisper chat showing rogue breaking party,
# relisting party in LFG at 7:46 AM, and answering whisper with a blank 'yes'!
# ---------------------------------------------------------------------------
V3_UPGRADES["ep015"] = [
    {
        "cut_index": 1,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["스카이본 마법사", "노움 도적"],
        "speaker": "스카이본 마법사",
        "dialogue": "파장님, 나락\n풀퀘팟 맞죠?\n윈저 호위퀘까지요!",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Over-the-shoulder (OTS) diagonal shot from behind the blonde aqua-tipped sailor collar of the Skyborne Mage girl in "
            "foreground-left, leaning forward with clasped hands and eager starry eyes. Looking toward the Gnome Rogue party leader "
            "(blonde pigtails with pink/blue tips, aviator goggles, rogue cloak) who stands rigidly with an eerily frozen doll-like "
            "smile and empty dot eyes, giving a stiff wooden thumbs-up. Daggers sheathed at belt. Lower two-thirds framing, top 35% "
            "pure white (#FFFFFF) headroom. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 2,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["노움 도적"],
        "speaker": "노움 도적",
        "dialogue": "yes",
        "wordless": False,
        "tail_target": "right",
        "visual_prompt": (
            "Low-angle shot looking up at the Gnome Rogue girl standing alone on the right half, aviator goggles on her forehead, "
            "wooden robotic mannequin smile, holding up a stiff rigid thumbs-up with comic speed lines radiating around her. "
            "Absolutely unblinking doll eyes, daggers sheathed at belt. Cleanly framed on the right half, leaving generous pure "
            "white (#FFFFFF) space across the left 48% for the speech bubble. 100% pure solid #FFFFFF white borderless background, "
            "zero text, zero UI."
        ),
    },
    {
        "cut_index": 3,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["스카이본 마법사", "드워프 사냥꾼"],
        "speaker": "스카이본 마법사",
        "dialogue": "냥꾼님 호위퀘 싫다고\n중탈했어요!\n다시 구해요? 접어요?",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Side-profile 90-degree action shot. On the right, the Dwarf Hunter girl is sprinting away toward the dungeon exit with "
            "blunderbuss on back, kicking up clouds of flying dust puffs and tossing a careless wave over her shoulder. On the left, "
            "Skyborne Mage flails both arms in frantic panic with flying sweat drops and tears, staff bouncing on her back. Lower "
            "two-thirds framing, top 35% pure white (#FFFFFF) headroom. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 4,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["노움 도적"],
        "speaker": "노움 도적",
        "dialogue": "yes",
        "wordless": False,
        "tail_target": "right",
        "visual_prompt": (
            "Dutch-tilt slapstick action camera with a tilted diagonal composition. The Gnome Rogue still maintains the frozen stiff "
            "smile and thumbs-up, but her lower body is now actively dissolving into a swirling white-gray cartoon Vanish smoke puff, "
            "stepping backward into a stealth vortex while posting a brand new party listing in the air! Clean framing on the right "
            "half, leaving generous pure white (#FFFFFF) space on left 48% for dialogue bubble. 100% pure solid #FFFFFF white "
            "borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 5,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["스카이본 마법사"],
        "speaker": None,
        "dialogue": None,
        "wordless": True,
        "tail_target": "center",
        "visual_prompt": (
            "High-angle shot looking down at the Skyborne Mage girl in a signature comedic freeze-frame, completely wordless. "
            "She has collapsed on her knees in the dirt, clutching both sides of her head with her hands, anime spiral eyes leaking "
            "massive comical waterfall tears that puddle on the floor, mouth agape in hollow existential ruin at 3 AM. Centered "
            "dramatic framing filling ~78% of canvas height. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 6,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["스카이본 마법사", "노움 도적"],
        "speaker": "스카이본 마법사",
        "dialogue": "외국인이었어?! 아니 뭔\n예스야 파티 터뜨리고\n양심 터졌냐고!!",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Back-view shot seen from behind recreating the whisper chat explosion: Skyborne Mage girl furious, stamping her feet "
            "seen from behind waving a magic whisper scroll toward the ceiling with cartoon anger veins. In the far background, the "
            "vanished Gnome Rogue's translucent silhouette floats casually humming, giving one last wooden thumbs-up. Cleanly positioned "
            "leaving generous pure white (#FFFFFF) space on right 46% for dialogue bubble. 100% pure solid #FFFFFF white borderless "
            "background, zero text, zero UI."
        ),
    },
]

# ---------------------------------------------------------------------------
# EP016: 진짜 병신겜 씨발 좆같은거 접는다 (Post #97410)
# Original screenshot: Priest perched on a cliff slope soloing Baron Vardus camp;
# layer changes, Baron resets/despawns, full pack of Syndicate mobs respawns around her!
# ---------------------------------------------------------------------------
V3_UPGRADES["ep016"] = [
    {
        "cut_index": 1,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["나이트엘프 사제"],
        "speaker": "나이트엘프 사제",
        "dialogue": "바르두스 남작 현상수배…\n절벽 위에서 한 땀 한 땀\n풀링해서 잡는다.",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Side-profile 90-degree action shot recreating the author's real screenshot: Night Elf Priest girl (lavender-silver hair, "
            "dark eye circles, mooncloth robe) perches carefully on a steep rocky cliff slope, aiming a slender wooden wand down toward "
            "a bandit tent camp below where a large syndicate mob boss stands beside a campfire. Golden Power Word: Shield glowing around "
            "her, staff on back. Lower two-thirds framing, top 35% pure white (#FFFFFF) headroom. 100% pure solid #FFFFFF white "
            "borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 2,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["나이트엘프 사제"],
        "speaker": "나이트엘프 사제",
        "dialogue": "15분 만에 남작 처치!!\n이제 머리카락만\n루팅하면 완료야 ㅠㅠ",
        "wordless": False,
        "tail_target": "right",
        "visual_prompt": (
            "Over-the-shoulder (OTS) diagonal shot from behind the shoulder of the Night Elf Priest in foreground-right, leaning "
            "forward on her knees reaching both hands with happy crying anime tears toward a sparkling golden quest loot bag on the "
            "ground. Staff sheathed on back. Positioned on the right half, leaving generous pure white (#FFFFFF) space across left "
            "48% for dialogue bubble. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 3,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["나이트엘프 사제", "노움 도적"],
        "speaker": "노움 도적",
        "dialogue": "어? 언니 방금\n위상 바뀌었는데?\n여기 몹 다 리젠됨~",
        "wordless": False,
        "tail_target": "right",
        "visual_prompt": (
            "Dutch-tilt slapstick action camera with a tilted diagonal composition. The loot pile ripples and dissolves into shimmering "
            "rainbow server phase sparkles, vanishing! Night Elf Priest on the left freezes mid-reach, eyes bulging in utter confusion. "
            "On the right, Gnome Rogue pops into view with a cheeky grin, pointing at a freshly respawned full pack of dark cartoon "
            "syndicate mob silhouettes surrounding them! Lower two-thirds framing, top 35% pure white (#FFFFFF) headroom. 100% pure "
            "solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 4,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["나이트엘프 사제"],
        "speaker": None,
        "dialogue": None,
        "wordless": True,
        "tail_target": "center",
        "visual_prompt": (
            "High-angle shot looking down at the Night Elf Priest girl in a signature comedic freeze-frame, completely wordless. "
            "She is frozen stiff in petrified horror, her golden shield bubble shattering into sharp glass fragments, eyes wide with "
            "pinpoint trembling pupils, a pitch-black gloom shadow over her forehead, surrounded by six menacing red-eyed cartoon "
            "bandit silhouettes closing in with clubs and daggers. Centered dramatic framing filling ~78% of canvas height. 100% pure "
            "solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 5,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["나이트엘프 사제"],
        "speaker": "나이트엘프 사제",
        "dialogue": "한 땀 한 땀 잡은\n남작이었는데!!\n이 겜 진짜 접는다!!",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Low-angle shot looking up at the translucent blue ghost form of the Night Elf Priest girl, floating in mid-air and "
            "throwing a furious temper tantrum, bawling comedic waterfall tears and flailing both fists wildly with cartoon steam puffs "
            "blowing from her ears (matching the screaming Pepe in the original post!). Wispy ghost tail fluttering. Lower two-thirds "
            "framing, top 35% pure white (#FFFFFF) headroom. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 6,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["노움 도적", "나이트엘프 사제"],
        "speaker": "노움 도적",
        "dialogue": "접을 거면\n골드 주고 가요~♪",
        "wordless": False,
        "tail_target": "right",
        "visual_prompt": (
            "Back-view shot seen from behind of the sobbing ghost Priestess floating away toward the graveyard, seen from behind "
            "with slumped ethereal shoulders. In the foreground-right, Gnome Rogue leans forward with a shameless sweet grin, "
            "extending an open palm asking for quitting gold, daggers sheathed at belt. Positioned cleanly leaving generous pure "
            "white (#FFFFFF) space on the left 48% for dialogue bubble. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
]

# ---------------------------------------------------------------------------
# EP017: <한국성기사협회> 로데론 정화 원정대 (Post #108678)
# Original screenshots: A massive army of dozens of paladins marching single-file
# across Tirisfal Glades, hunting the 'heretic' Undead Paladin, then getting wiped in Lordaeron!
# ---------------------------------------------------------------------------
V3_UPGRADES["ep017"] = [
    {
        "cut_index": 1,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["나이트엘프 사제"],
        "speaker": "나이트엘프 사제",
        "dialogue": "한국성기사협회 원정대!\n언더시티 옆 언덕\n야영지 구축 완료!",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Low-angle shot looking up recreating the original post's screenshot: an impressive single-file marching column of a dozen "
            "chibi paladins with glowing golden banners, warhammers, and shining armor marching along a hillside road! At the front, "
            "the Night Elf Priestess plants a glowing silver banner beside a crackling campfire with an inspiring heroic smile, staff "
            "on back. Lower two-thirds framing, top 35% pure white (#FFFFFF) headroom. 100% pure solid #FFFFFF white borderless background, "
            "zero text, zero UI."
        ),
    },
    {
        "cut_index": 2,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["나이트엘프 사제", "언데드 성기사"],
        "speaker": "나이트엘프 사제",
        "dialogue": "기사님들! 이단\n언데드 성기사 발견!\n심판 날려요!!",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Over-the-shoulder (OTS) diagonal shot from behind the shoulder of the Undead Paladin in foreground-right, who has just "
            "wandered onto the Brill road with an innocent head tilt. Looking toward the Night Elf Priest on the left who points her "
            "glowing staff forward with righteous fury, while background paladins raise hammers ready to cast Judgement! Positioned "
            "cleanly leaving generous pure white (#FFFFFF) space on right 46% for dialogue bubble. 100% pure solid #FFFFFF white "
            "borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 3,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["나이트엘프 사제", "언데드 성기사"],
        "speaker": "나이트엘프 사제",
        "dialogue": "심판 완료~\n이제 로데론까지\n평화롭게 정화 행진♪",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Side-profile 90-degree action shot of the Night Elf Priest and her paladin army marching cheerfully toward the right "
            "with bouncy steps, eyes closed in bliss, making cute peace signs. In the background-left, the Undead Paladin lies sprawled "
            "on the ground with comical spiral eyes. Lower two-thirds framing, top 35% pure white (#FFFFFF) headroom. 100% pure solid "
            "#FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 4,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["언데드 성기사", "트롤 주술사"],
        "speaker": "언데드 성기사",
        "dialogue": "이단의 반격이다.\n…쪼렙이라도\n무적은 있다.",
        "wordless": False,
        "tail_target": "right",
        "visual_prompt": (
            "Dutch-tilt slapstick action camera with a tilted dynamic composition! The Undead Paladin suddenly leaps back up on the "
            "right, encased inside a blazing golden spherical Divine Shield (Paladin bubble)! Beside her, Troll Shaman plants a wooden "
            "totem into the ground with crackling lightning, backed by cartoon Horde reinforcement silhouettes charging! Clean framing "
            "on right half, leaving generous pure white (#FFFFFF) space on left 48% for dialogue bubble. 100% pure solid #FFFFFF white "
            "borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 5,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["나이트엘프 사제"],
        "speaker": None,
        "dialogue": None,
        "wordless": True,
        "tail_target": "center",
        "visual_prompt": (
            "High-angle shot looking down at the Night Elf Priest girl in a signature comedic freeze-frame, completely wordless. "
            "Caught entirely off guard, she has tumbled backward onto her rear, eyes spinning in frantic spiral shock, hands flailing "
            "in mid-air, seeing the invincible golden bubbles and Horde horde charging straight at her! Centered dramatic framing "
            "filling ~78% of canvas height. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 6,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["언데드 성기사", "나이트엘프 사제"],
        "speaker": "언데드 성기사",
        "dialogue": "원정대 정화당함 완료.\n영혼의 치유사는\n저쪽이다.",
        "wordless": False,
        "tail_target": "right",
        "visual_prompt": (
            "Back-view shot seen from behind recreating the author's real punchline ('정화당함 완료'): Undead Paladin rests her heavy "
            "holy hammer over her shoulder, seen from behind walking away toward the left, pointing with her thumb over her shoulder "
            "toward the graveyard. In the background-right, the entire paladin expedition and Night Elf Priest sit or lie slumped as "
            "translucent blue ghosts in the Lordaeron courtyard, sulking with puffed cheeks! Clean framing leaving generous pure white "
            "(#FFFFFF) space on left 48% for dialogue bubble. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
]

# ---------------------------------------------------------------------------
# EP018: 탱커없다길래 가서 폐광에서 길따라 몹잡는데 냥꾼이 (Post #7793)
# Deadmines dungeon run: nice warrior tanks with 1H sword + shield, hunter backseat
# drives on skip routes, tank snaps 'you tank then!', hunter says 'too tiring'.
# ---------------------------------------------------------------------------
V3_UPGRADES["ep018"] = [
    {
        "cut_index": 1,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["오크 전사", "나이트엘프 사제"],
        "speaker": "오크 전사",
        "dialogue": "탱커 없다길래\n방패 들고 왔어!\n폐광 바로 가자~",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Over-the-shoulder (OTS) diagonal shot from behind the Night Elf Priest's silver cowl in foreground-right, looking at "
            "the Orc Warrior tank in foreground-left standing beside a wooden minecart on iron rails. The Orc Warrior cheerfully presents "
            "her sturdy round iron shield and 1H broadsword, beaming with proud hero enthusiasm and a bright toothy grin. Lower two-thirds "
            "framing, top 35% pure white (#FFFFFF) headroom. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 2,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["드워프 사냥꾼"],
        "speaker": "드워프 사냥꾼",
        "dialogue": "아 그렇게 가는 거\n아닌데요? 거긴\n스킵해야 되는데;",
        "wordless": False,
        "tail_target": "right",
        "visual_prompt": (
            "Low-angle shot looking up at the Dwarf Hunter girl standing on the right half, leaning against her wooden blunderbuss "
            "like a cane with a smug, patronizing smirk and half-closed eyes. She wags an index finger sideways in a lecturing gesture "
            "with little sweatdrop annoyance lines. Cleanly positioned on the right half, leaving generous pure white (#FFFFFF) space "
            "on the left 48% for dialogue bubble. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 3,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["오크 전사", "드워프 사냥꾼"],
        "speaker": "오크 전사",
        "dialogue": "그렇게 잘 아시면\n냥꾼님이 탱커\n하시면 되겠네요!",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Dutch-tilt slapstick action camera with a tilted diagonal composition. Orc Warrior tank steps forward aggressively, "
            "thrusting her sturdy round shield right into Dwarf Hunter's face with furious sharp teeth and anime anger vein popping, "
            "1H sword held low. Dwarf Hunter stumbles backward in shock, hands flying up. Lower two-thirds framing, top 35% pure white "
            "(#FFFFFF) headroom. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 4,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["드워프 사냥꾼"],
        "speaker": "드워프 사냥꾼",
        "dialogue": "탱이요?\n피곤해서 싫은데요?",
        "wordless": False,
        "tail_target": "right",
        "visual_prompt": (
            "Side-profile 90-degree action shot of the Dwarf Hunter girl on the right half, shrugging with both palms turned up in the air, "
            "puffing her cheeks with a nonchalant cheeky face, eyes rolling upward. Her blunderbuss is slung across her back, hands "
            "completely free. Positioned cleanly on the right half, leaving generous pure white (#FFFFFF) space on the left 48% for "
            "dialogue bubble. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 5,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["오크 전사"],
        "speaker": None,
        "dialogue": None,
        "wordless": True,
        "tail_target": "center",
        "visual_prompt": (
            "High-angle shot looking down at the Orc Warrior tank in a signature comedic freeze-frame, completely wordless. Completely "
            "dumbfounded and exasperated, her 1H sword slips from her fingers, she drops her sturdy shield onto the ground with a heavy "
            "clatter, her jaw dropping open with empty white hollow eyes and dark purple vertical gloom lines over her forehead. Centered "
            "dramatic framing filling ~78% of canvas height. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 6,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["나이트엘프 사제", "오크 전사"],
        "speaker": "나이트엘프 사제",
        "dialogue": "네~ 그럼 냥꾼님도\n깔끔하게 스킵하고\n출발할게요~",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Back-view shot seen from behind of the Night Elf Priest and Orc Warrior tank marching away together toward the dungeon door "
            "on the left, turning their backs to the Dwarf Hunter. The Priest gives a polite wave goodbye over her shoulder with a sweet, "
            "lethal smile, while Dwarf Hunter in the background is shown being kicked out in a cartoon flying boot puff! Clean framing "
            "leaving generous pure white (#FFFFFF) space on the right 46% for dialogue bubble. 100% pure solid #FFFFFF white borderless "
            "background, zero text, zero UI."
        ),
    },
]

# ---------------------------------------------------------------------------
# EP019: 와우 뉴비인데 가끔 충격받음 (feat.파티찾기) (Post #96439)
# Original screenshots: DC comment '정 그런게 싫으면 위치 확인후 초대하면되지'
# and NatGeo meme '사고방식 자체가 우리와는 다릅니다'!
# ---------------------------------------------------------------------------
V3_UPGRADES["ep019"] = [
    {
        "cut_index": 1,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["오크 전사", "스카이본 마법사"],
        "speaker": "오크 전사",
        "dialogue": "줄파락 파티 완성!\n흑마님만 오면\n바로 출발이다!",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Over-the-shoulder (OTS) diagonal shot from behind Skyborne Mage's blue sailor collar in foreground-right, looking at Orc Warrior "
            "tank in foreground-left standing under a scorching desert sun outside the sand-duned Zul'Farrak entrance. Orc Warrior raises "
            "her 1H sword and sturdy round shield high with eager excitement, toothy smile, ready to dive in. Lower two-thirds framing, "
            "top 35% pure white (#FFFFFF) headroom. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 2,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["인간 흑마법사"],
        "speaker": "인간 흑마법사",
        "dialogue": "저 스톰윈드 여관~\n배 타고 그리핀 타고\n30분이면 가요!",
        "wordless": False,
        "tail_target": "right",
        "visual_prompt": (
            "Low-angle shot looking up at the Human Warlock girl on the right half, leaning back comfortably in a rustic wooden tavern chair "
            "in the distant Stormwind inn on the other continent, sipping casually from a fantasy corked glass potion flask. She has a "
            "carefree, unbothered smile, soul lantern staff resting beside her chair, chatting through whispers while the party waits "
            "across the world! Positioned on the right half, leaving generous pure white (#FFFFFF) space on left 48% for dialogue bubble. "
            "100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 3,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["오크 전사", "스카이본 마법사"],
        "speaker": "오크 전사",
        "dialogue": "30분?! 다른 대륙에서\n파티 신청을\n왜 넣는 건데!!",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Dutch-tilt slapstick action camera with a tilted diagonal angle! In the desert heat, Orc Warrior violently slams her sturdy "
            "shield against the ground in sheer rage, screaming with a massive jagged jaw-drop and flying spit drops! Beside her, Skyborne "
            "Mage clutches her head with both hands in despair, crystal staff bouncing. Lower two-thirds framing, top 35% pure white "
            "(#FFFFFF) headroom. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 4,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["인간 흑마법사"],
        "speaker": "인간 흑마법사",
        "dialogue": "그럼 님이 제 위치\n미리 확인하고\n초대했어야죠~",
        "wordless": False,
        "tail_target": "right",
        "visual_prompt": (
            "Side-profile 90-degree action shot recreating the screenshot's exact punchline quote! Human Warlock girl on the right half, "
            "folding her arms haughtily with a smug sneer, tilting her nose up into the air with total audacity, staff stowed on her back. "
            "Positioned cleanly on the right half, leaving generous pure white (#FFFFFF) space across left 48% for dialogue bubble. "
            "100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 5,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["스카이본 마법사"],
        "speaker": None,
        "dialogue": None,
        "wordless": True,
        "tail_target": "center",
        "visual_prompt": (
            "High-angle shot looking down at the Skyborne Mage girl recreating the famous meme pose ('사고방식 자체가 우리와는 다릅니다')! "
            "Forty minutes later under the desert sun, she is sitting slumped on the ground like a melting candle, hollow unblinking white "
            "void eyes, a tiny tumbleweed rolling past her, completely drained of life and hope at the cultural shock. Centered dramatic "
            "framing filling ~78% of canvas height. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 6,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["인간 흑마법사", "오크 전사"],
        "speaker": "인간 흑마법사",
        "dialogue": "40분 걸렸네요~\n근데 다들 계속\n기다리신 거예요?",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Back-view shot seen from behind of the Human Warlock girl finally strolling into the desert portal, seen from behind walking away "
            "with a breezy little wave, turning her head back over her shoulder with an innocent oblivious smile. In the background-right, "
            "the Orc Warrior tank stands shaking with demonic anime rage veins, gripping her 1H sword with steam whistling from her ears! "
            "Clean framing leaving generous pure white (#FFFFFF) space on right 46% for dialogue bubble. 100% pure solid #FFFFFF white "
            "borderless background, zero text, zero UI."
        ),
    },
]

# ---------------------------------------------------------------------------
# EP020: 여기 걸쳐지는구나 (Post #110883)
# Booty Bay to Ratchet ship: Gnome Rogue misses the departing ship, reckless jump
# clinging to the outer wooden ship rail edge, survives loading screen, arrives!
# ---------------------------------------------------------------------------
V3_UPGRADES["ep020"] = [
    {
        "cut_index": 1,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["노움 도적", "드워프 사냥꾼"],
        "speaker": "노움 도적",
        "dialogue": "아아아 배 떠난다!!\n잠깐만요오오!!",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Side-profile 90-degree action shot. Gnome Rogue girl (aviator goggles, blonde twin pigtails with pink/blue tips, rogue cloak) "
            "sprinting desperately along a wooden harbor dock toward the right, arms flailing, face full of comedic anime tears and gaping "
            "scream, daggers at belt. Behind her on the dock, Dwarf Hunter watches with hands on hips, laughing. Lower two-thirds framing, "
            "top 35% pure white (#FFFFFF) headroom. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 2,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["노움 도적"],
        "speaker": "노움 도적",
        "dialogue": "에라 모르겠다!\n웃기라고 그냥\n뛰어보자아!!",
        "wordless": False,
        "tail_target": "right",
        "visual_prompt": (
            "Low-angle shot looking up at the Gnome Rogue girl leaping heroically through mid-air toward the right edge with a wide reckless "
            "grin, goggles pushed up, cape flapping violently, diving over open water with comic speed lines radiating around her! "
            "Positioned on the right half, leaving generous pure white (#FFFFFF) space on the left 48% for dialogue bubble. 100% pure "
            "solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 3,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["노움 도적", "드워프 사냥꾼"],
        "speaker": "노움 도적",
        "dialogue": "어...?\n여기 걸쳐지는구나?!",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Dutch-tilt slapstick action camera with a tilted diagonal composition. Against all odds, the Gnome Rogue has landed clinging "
            "desperately by her fingertips to the outer wooden ship rail edge, her little legs dangling over empty air, eyes wide in shocked "
            "amazement and disbelief! On the ship deck above, Dwarf Hunter leans over the rail in astonishment. Lower two-thirds framing, "
            "top 35% pure white (#FFFFFF) headroom. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 4,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["드워프 사냥꾼", "노움 도적"],
        "speaker": "드워프 사냥꾼",
        "dialogue": "미친... 근데 대륙\n넘어가서 로딩되면\n바로 떨어질걸?",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Over-the-shoulder (OTS) diagonal shot from behind the green hood of the Dwarf Hunter in foreground-left, peering down at the "
            "Gnome Rogue who is still hanging on by her chin and elbows to the wooden ship rail on the right, sweating profusely with an "
            "uneasy nervous smile. Clean framing leaving generous pure white (#FFFFFF) space on the right 46% for dialogue bubble. 100% pure "
            "solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 5,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["노움 도적"],
        "speaker": None,
        "dialogue": None,
        "wordless": True,
        "tail_target": "center",
        "visual_prompt": (
            "High-angle shot looking down at the Gnome Rogue girl in a signature comedic freeze-frame, completely wordless. As the ship "
            "enters the ocean loading zone, she realizes her fate: her fingers are slipping from the wooden rail, eyes dilated into wild "
            "spinning spirals, jaw dropped down to her knees, screaming in silent terror with giant anime tear fountains spraying into "
            "the sky! Centered dramatic framing filling ~78% of canvas height. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 6,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["노움 도적", "드워프 사냥꾼"],
        "speaker": "노움 도적",
        "dialogue": "무사히 도착함!\n다음 배 안 기다림!\n이게 족고수지 ㅋ",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Back-view shot seen from behind of the drenched Gnome Rogue girl striding proudly off the harbor dock on the new continent "
            "seen from behind, shaking water droplets from her twin pigtails and giving a triumphant two-handed V-sign. In the background-right, "
            "Dwarf Hunter sits on a wooden crate shaking her head with an incredulous smirk. Clean framing leaving generous pure white "
            "(#FFFFFF) space on the right 46% for dialogue bubble. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
]

# ---------------------------------------------------------------------------
# EP021: 늒네 겜후기 (Post #109397)
# Original screenshots: Newbie Druid discovering aquatic seal form in cave pool,
# fighting quest mob, dance battle on Booty Bay ship, crowd of gnomes at cave!
# ---------------------------------------------------------------------------
V3_UPGRADES["ep021"] = [
    {
        "cut_index": 1,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["타우렌 드루이드"],
        "speaker": "타우렌 드루이드",
        "dialogue": "물개로 변신하면\n물속에서 숨도\n쉬어진다고?! 대박!",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Side-profile 90-degree action shot recreating the screenshot's cave pool: Tauren Druid girl (fluffy cow hood, golden nose "
            "ring, leaf mantle) splashing playfully in knee-deep water, holding up a cute plush aquatic seal form hood with glistening "
            "starry eyes and flushed pink cheeks, wooden staff stowed on her back. Little cartoon water splashes and air bubbles flying "
            "around. Lower two-thirds framing, top 35% pure white (#FFFFFF) headroom. 100% pure solid #FFFFFF white borderless background, "
            "zero text, zero UI."
        ),
    },
    {
        "cut_index": 2,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["타우렌 드루이드"],
        "speaker": "타우렌 드루이드",
        "dialogue": "20렙 표범 폼?!\n조화 접고 전재산\n털어서 초기화!!",
        "wordless": False,
        "tail_target": "right",
        "visual_prompt": (
            "Low-angle shot looking up at the Tauren Druid girl standing on the right half, fiercely posing with cute feline claw gestures, "
            "pretending to be a ferocious cat with a determined toothy grin and sparkling amber eyes, having dumped all her copper coins "
            "at the class trainer! Staff on back. Positioned on the right half, leaving generous pure white (#FFFFFF) space on left 48% "
            "for dialogue bubble. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 3,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["타우렌 드루이드", "노움 도적"],
        "speaker": "타우렌 드루이드",
        "dialogue": "저 빨간 이름...\n네임드 몹이다!\n첫 보스전 두근..!",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Over-the-shoulder (OTS) diagonal shot from behind the cow-eared hood of the Tauren Druid in foreground-left, crouching low "
            "in cat stealth and peeking nervously toward the background-right. Standing there is an Alliance player, the Gnome Rogue girl, "
            "with a red hostile faction name indicator, stretching her arms casually. Lower two-thirds framing, top 35% pure white "
            "(#FFFFFF) headroom. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 4,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["타우렌 드루이드", "노움 도적"],
        "speaker": "타우렌 드루이드",
        "dialogue": "무법항 배 위에서\n얼라랑 댄스 배틀!\n말은 안 통해도 춤!",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Dutch-tilt slapstick action camera with a tilted dynamic dance party frame recreating the author's ship dance battle! On the deck "
            "of the Booty Bay ship, Tauren Druid and Gnome Rogue are having an epic cartoon dance battle, kicking their legs high, spinning "
            "around with musical notes and disco sparkles bursting everywhere, staff and daggers sheathed on backs! Clean framing on left "
            "and center, leaving generous pure white (#FFFFFF) space on right 46% for dialogue bubble. 100% pure solid #FFFFFF white "
            "borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 5,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["노움 도적"],
        "speaker": None,
        "dialogue": None,
        "wordless": True,
        "tail_target": "center",
        "visual_prompt": (
            "High-angle shot looking down at the Gnome Rogue girl in a signature comedic freeze-frame, completely wordless. Completely "
            "exhausted from the 20-minute endless dance battle, she has collapsed faceplant onto the deck planks, limbs splayed out like "
            "a starfish, anime swirl eyes, little white soul ghost floating out of her mouth. Centered dramatic framing filling ~78% of "
            "canvas height. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 6,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["타우렌 드루이드", "노움 도적"],
        "speaker": "타우렌 드루이드",
        "dialogue": "동굴 앞 노움 무리랑\n같이 퀘 밀기~\n와우 진짜 갓겜이다!",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Back-view shot seen from behind recreating the author's final sweet memory: Tauren Druid seen from behind marching happily "
            "into a cave entrance alongside a cheerful cluster of three extra little gnome adventurers (one carrying a wrench, one with a "
            "lantern), waving goodbye over her shoulder to the defeated dance rival Gnome Rogue. Clean framing leaving generous pure white "
            "(#FFFFFF) space on right 46% for dialogue bubble. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
]

# ---------------------------------------------------------------------------
# EP022: 개꿀팁) 하이잘 도착하면 사제들 꼭 해야할 일....TIP (Post #107884)
# Hyjal cliff Mind Control: Priest mind controls enemy, forces polite /bow,
# walks victim off sheer vertical precipice, rogue in stealth watches in horror!
# ---------------------------------------------------------------------------
V3_UPGRADES["ep022"] = [
    {
        "cut_index": 1,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["나이트엘프 사제", "노움 도적"],
        "speaker": "나이트엘프 사제",
        "dialogue": "하이잘 도착하면\n사제가 꼭 해야 할\n개꿀팁 알려줄게~",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Over-the-shoulder (OTS) diagonal shot from behind the aviator goggles and pigtails of the Gnome Rogue in foreground-right. "
            "Looking toward the Night Elf Priest girl on the left, who holds her glowing crescent staff upright, smiling serenely with "
            "closed eyes and holding up one finger to share a secret tip beside the dizzying height of the Hyjal mountain peak. Lower "
            "two-thirds framing, top 35% pure white (#FFFFFF) headroom. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 2,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["나이트엘프 사제", "오크 전사"],
        "speaker": "나이트엘프 사제",
        "dialogue": "정신 지배~\n자, 예의 바르게\n인사부터 해야지?",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Low-angle shot looking up at the Night Elf Priest girl casting Mind Control, hands outstretched with hypnotic swirly "
            "pink-and-purple psychic rings radiating from her glowing eyes and palms, wearing an innocent sweet yet terrifying smile. "
            "In front of her, the Orc Warrior stands with eyes swirling in a hypnotic trance, woodenly raising one hand to /bow. Staff "
            "stowed on Priest's back. Positioned on the left, leaving generous pure white (#FFFFFF) space on right 46% for dialogue bubble. "
            "100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 3,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["오크 전사"],
        "speaker": "오크 전사",
        "dialogue": "어... 어어...?\n몸이 멋대로...\n발밑이 없는데?!",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Dutch-tilt slapstick action camera with a dizzying steep cliff angle! The Orc Warrior is mind-controlled into walking right "
            "off the edge of a floating stone cliff, one foot stepping into empty air! Her jaw drops in hysterical terror, eyes bulging "
            "with tears, arms flailing frantically while her legs keep marching forward robotically! Lower two-thirds framing, top 35% "
            "pure white (#FFFFFF) headroom. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 4,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["노움 도적"],
        "speaker": None,
        "dialogue": None,
        "wordless": True,
        "tail_target": "center",
        "visual_prompt": (
            "High-angle shot looking down at the Gnome Rogue girl in a signature comedic freeze-frame, completely wordless. Watching the "
            "mind-controlled victim plummet from the cliff, her aviator goggles slide down her nose, jaw unhinged to the floor in horrified "
            "disbelief, cold sweat drops pouring down like a shower, shivering uncontrollably at the Priest's cruelty. Centered dramatic "
            "framing filling ~78% of canvas height. 100% pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 5,
        "aspect_ratio": "4:3",
        "layout_slot": "top",
        "characters": ["나이트엘프 사제"],
        "speaker": "나이트엘프 사제",
        "dialogue": "잘 가요~\n인사까지 했으니\n매너 플레이 맞죠?",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Side-profile 90-degree action shot of the Night Elf Priest girl standing at the cliff edge on the left, leaning forward "
            "gracefully and waving a delicate white handkerchief goodbye into the abyss with a radiant angelic smile and sparkling halos. "
            "Lunar crescent staff resting beside her on the ground. Lower two-thirds framing, top 35% pure white (#FFFFFF) headroom. 100% "
            "pure solid #FFFFFF white borderless background, zero text, zero UI."
        ),
    },
    {
        "cut_index": 6,
        "aspect_ratio": "16:9",
        "layout_slot": "bottom",
        "characters": ["노움 도적", "나이트엘프 사제"],
        "speaker": "노움 도적",
        "dialogue": "악마를 보았다...\n근데 도적은 혼란\n딸깍이면 되는데?",
        "wordless": False,
        "tail_target": "left",
        "visual_prompt": (
            "Back-view shot seen from behind of the Gnome Rogue backing away in slow stealth toward the left, turning her back to the serene "
            "Priest, whispering sideways with wide traumatized eyes and sweatdrops. In the background-right, the Priest calmly dusts her robes "
            "off. Clean framing leaving generous pure white (#FFFFFF) space on the right 46% for dialogue bubble. 100% pure solid #FFFFFF "
            "white borderless background, zero text, zero UI."
        ),
    },
]


def apply_v3():
    for i in range(11, 23):
        ep = f"ep{i:03d}"
        script_path = Path(f"data/episodes/{ep}/script.json")
        raw_data = json.loads(script_path.read_text(encoding="utf-8"))

        upgraded_cuts_data = V3_UPGRADES[ep]
        raw_data["cuts"] = upgraded_cuts_data

        script = EpisodeScript.model_validate(raw_data)
        audit_res = audit_script_quality(script, strict_cinematic=True)
        if not audit_res["passed"] or audit_res["errors"]:
            print(f"FAILED AUDIT FOR {ep}: {audit_res['errors']}")
            raise ValueError(f"Audit failed for {ep}")

        # Save script.json
        script_path.write_text(
            script.model_dump_json(indent=2, by_alias=True),
            encoding="utf-8"
        )

        # Regenerate data/raw_cuts/<ep>/prompts.json
        raw_cuts_dir = Path(f"data/raw_cuts/{ep}")
        raw_cuts_dir.mkdir(parents=True, exist_ok=True)
        prompts = []
        for cut in script.cuts:
            target_path = raw_cuts_dir / f"cut_{cut.cut_index:02d}.png"
            prompt_text = build_cut_image_prompt(cut)
            prompts.append({
                "cut_index": cut.cut_index,
                "aspect_ratio": cut.aspect_ratio,
                "target_path": str(target_path.resolve()),
                "prompt": prompt_text,
            })
        (raw_cuts_dir / "prompts.json").write_text(
            json.dumps(prompts, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"V3 UPGRADE COMPLETE for {ep} ({script.source_title}) -> 6 cuts, strict_cinematic passed!")


if __name__ == "__main__":
    apply_v3()
