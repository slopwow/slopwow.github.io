"""Cinematic upgrade generator for ep047 through ep058 (12 episodes).
Eliminates flat side-by-side talking heads; applies rich cinematic camera angles,
diverse facial expressions, minimal vignette action props, and WoW Forever lore.
"""

from __future__ import annotations

import json
from pathlib import Path
from wow_sloptoon import artist
from wow_sloptoon.models import EpisodeScript
from wow_sloptoon.writer import audit_script_quality

EPISODES_UPGRADES: dict[str, dict] = {}

# ===========================================================================
# EP047: 양형들이랑 영주의전당 다녀왔는데 싸움구경 하고 옴 ㅋㅋㅋ
# ===========================================================================
EPISODES_UPGRADES["ep047"] = {
    "cuts": [
        {
            "cut_index": 1,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "스카이본 마법사",
            "characters": ["오크 전사", "스카이본 마법사"],
            "tail_target": "right",
            "dialogue": "신규 인던 영주의 전당…\n전사님 시작하자마자\n벌써 누움?!",
            "visual_prompt": (
                "High-angle shot looking down at the dungeon floor on a 100% pure solid #FFFFFF white borderless "
                "background. On the lower-left, the Orc Warrior girl (top-row #1 on Draft C cast sheet) is sprawled "
                "face-down on the ground after an early dungeon wipe, one 1H axe knocked aside, tiny cartoon dust puff "
                "rising around her limp form with comedic spiral eyes visible beneath her helmet. On the lower-right, "
                "the Skyborne Mage girl (bottom-row #4) stands leaning forward in disbelief with a dramatic jaw-drop, "
                "hands pressed to her face, two floating blue sweat drops. Medium 2.5-to-3-head chibi scale in the "
                "lower two-thirds, leaving the top 35% pure white (#FFFFFF) headroom for speech bubbles. Zero text, "
                "zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 2,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "타우렌 드루이드",
            "characters": ["타우렌 드루이드", "오크 전사"],
            "tail_target": "left",
            "dialogue": "주문력+치유 템을\n힐러가 왜 먹냐고?!\n무조건 딜템이지!!",
            "visual_prompt": (
                "Over-the-shoulder (OTS) diagonal shot on a 100% pure solid #FFFFFF white borderless background. "
                "In the right foreground, the bulky armored back and foreground shoulder of the Orc Warrior girl frame the cut. "
                "In the left background, the Tauren Druid girl (bottom-row #8 on Draft C cast sheet) angrily slams her open "
                "hand against the edge of a rustic wooden dungeon loot chest, puffing out sulky red cheeks with cartoon steam "
                "squirting from her ears, pointing an accusing finger with fiery anime eyes. Stowed staff on back. Medium "
                "2.5-to-3-head chibi scale, leaving the upper-right 46% pure white (#FFFFFF) space for speech bubbles. "
                "Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 3,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "오크 전사",
            "characters": ["오크 전사", "타우렌 드루이드"],
            "tail_target": "left",
            "dialogue": "이거 포에버 신규 템이잖아!\n너도 나도 다 뉴비인데\n누가 누굴 가르쳐!!",
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the Orc Warrior girl (top-row #1 on Draft C cast sheet) on the lower-left, "
                "wielding a 1H war axe and a sturdy spiked metal shield, leaning aggressively forward in a fierce shouting stance "
                "with jagged shark-teeth yell, vein popping on forehead with dynamic comic speed lines. On the lower-right, the "
                "Tauren Druid girl flinches backward in shock, clutching her horned hood with round spiral eyes. 100% pure solid "
                "#FFFFFF white borderless background, medium 2.5-to-3-head chibi scale in lower two-thirds, top 35% clear headroom. "
                "Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 4,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "언데드 성기사",
            "characters": ["언데드 성기사", "스카이본 마법사"],
            "tail_target": "left",
            "dialogue": "…싸우든 말든,\n법사님 물 한 병만\n더 주실래요?",
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background. On the left, "
                "the Undead Paladin girl (bottom-row #3 on Draft C cast sheet) is tiptoeing sneaking sideways while holding an empty "
                "fantasy corked glass flask in both hands (1H mace sheathed on belt), totally deadpan emotionless face with dark comic "
                "shadow over her hollow eyes, tapping the shoulder of the Skyborne Mage girl on the right. The mage turns around with "
                "a baffled side-eye expression. Medium 2.5-to-3-head chibi scale, generous pure white upper-right space for dialogue. "
                "Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 5,
            "layout_slot": "top",
            "wordless": True,
            "speaker": None,
            "characters": ["스카이본 마법사"],
            "tail_target": "center",
            "dialogue": None,
            "visual_prompt": (
                "Dynamic Dutch-tilt diagonal frame comedic freeze-frame on a 100% pure solid #FFFFFF white borderless background. "
                "Centered dramatic waist-up close-up of ONLY the Skyborne Mage girl (bottom-row #4 on Draft C cast sheet). She is "
                "frozen in utter blank white-eyed petrified disbelief, her jaw dropped wide open in an exaggerated comic gasp, a tiny "
                "semi-transparent ghost soul floating out of her mouth, two large blue teardrop sweat bubbles hovering beside her head. "
                "Dynamic diagonal tilted camera angle. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 6,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "스카이본 마법사",
            "characters": ["언데드 성기사", "스카이본 마법사"],
            "tail_target": "right",
            "dialogue": "싸우는 틈에 초록 판금템\n혼자 싹쓸이하고 귀환?!\n네가 진짜 흑막이었냐!!",
            "visual_prompt": (
                "Back-view shot on a 100% pure solid #FFFFFF white borderless background. In the lower-left, the Undead Paladin girl "
                "is seen from behind stepping into a glowing cyan Hearthstone magical vortex, a sack stuffed with green plate armor "
                "heaved over her back, casually waving goodbye over her shoulder with an unrepentant smirk. On the lower-right, the "
                "Skyborne Mage girl screams in comical fury with waterfall anime tears shooting from both eyes, waving her wooden staff "
                "wildly! Medium 2.5-to-3-head chibi scale, top 34% pure white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
    ]
}

# ===========================================================================
# EP048: 2026년에도 키오스크 거부하는 새끼들.jpg
# ===========================================================================
EPISODES_UPGRADES["ep048"] = {
    "cuts": [
        {
            "cut_index": 1,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "스카이본 마법사",
            "characters": ["스카이본 마법사", "오크 전사"],
            "tail_target": "left",
            "dialogue": "2026 파티찾기 게시판\n업데이트 됐어요!\n클릭 한 번이면 출발~",
            "visual_prompt": (
                "Over-the-shoulder (OTS) diagonal shot on a 100% pure solid #FFFFFF white borderless background. "
                "Foreground shoulder and spiky helmet edge of the Orc Warrior girl on the lower-right. In the center-left, "
                "the Skyborne Mage girl (bottom-row #4 on Draft C cast sheet) stands cheerfully presenting a floating parchment "
                "bulletin board mockup with starry sparkle eyes, both hands gesturing excitedly (staff sheathed on back). "
                "Medium 2.5-to-3-head chibi scale in lower two-thirds, top 35% pure white headroom for speech bubbles. "
                "Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 2,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "오크 전사",
            "characters": ["오크 전사"],
            "tail_target": "right",
            "dialogue": "기계 게시판 따위 안 써!!\n10초마다 공개창에\n외쳐야 참맛이지!!",
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the veteran Orc Warrior girl (top-row #1 on Draft C cast sheet) "
                "on a 100% pure solid #FFFFFF white borderless background. She stands stubbornly with thick arms crossed over "
                "her chest, 1H battleaxe and round buckler shield strapped securely to her waist, chin jutting out in a proud "
                "smug sneer with dark comic shadow over eyes, snorting cartoon steam puffs with dynamic comic speed lines. "
                "Medium 2.5-to-3-head chibi scale, positioned on right, leaving left 46% clear white space. Zero text, zero digits."
            ),
        },
        {
            "cut_index": 3,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "노움 도적",
            "characters": ["노움 도적", "오크 전사"],
            "tail_target": "left",
            "dialogue": "전사님… 거기 게시판에\n지금 탱커 자리만\n텅 비어 있는데요?!",
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background. From the left, "
                "the tiny Gnome Rogue girl (top-row #2 on Draft C cast sheet) comes running in and skidding to a sudden halt "
                "with flying dust puffs, pointing an accusing little finger toward the right with deadpan squinting side-eye. "
                "On the right, the Orc Warrior turns sideways with an irritated grimace. Medium 2.5-to-3-head chibi scale, "
                "top 35% pure white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 4,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "오크 전사",
            "characters": ["오크 전사"],
            "tail_target": "right",
            "dialogue": "어차피 나중엔 다들\n공개창 다시 켜게 돼 있어!\n통곡의 동굴 전탱 모셔라!!",
            "visual_prompt": (
                "Dynamic Dutch tilt diagonal angle frame with tilted camera on a 100% pure solid #FFFFFF white borderless background. "
                "The Orc Warrior girl cups both armored gauntlets around her roaring mouth, shouting at the top of her lungs "
                "toward the heavens with bulging forehead veins, flying comical saliva droplets and explosive comic sound effect "
                "rays (pure visual lines, no letters). Medium 2.5-to-3-head chibi scale, right-biased, left 46% clear headroom. "
                "Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 5,
            "layout_slot": "top",
            "wordless": True,
            "speaker": None,
            "characters": ["스카이본 마법사"],
            "tail_target": "center",
            "dialogue": None,
            "visual_prompt": (
                "High-angle shot looking down at the Skyborne Mage girl (bottom-row #4 on Draft C cast sheet) on a 100% pure solid "
                "#FFFFFF white borderless background. She has collapsed onto her knees, hands clutching her temples in sheer "
                "mental exhaustion, eyes spinning in dizzy spiral circles, a tiny ghostly soul floating out of her open mouth into "
                "the air with comic sweat drops. Expressive solo comedic close-up filling 75% height. Zero text, zero digits."
            ),
        },
        {
            "cut_index": 6,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "노움 도적",
            "characters": ["스카이본 마법사", "노움 도적"],
            "tail_target": "right",
            "dialogue": "편하라고 만든 시스템인데\n게시판이랑 공개창 둘 다\n감시하느라 두 배로 피곤해…",
            "visual_prompt": (
                "Back-view shot on a 100% pure solid #FFFFFF white borderless background. The Gnome Rogue girl and Skyborne Mage girl "
                "are seen from behind with slumped shoulders, walking away from the shouting warrior into the distance, both turning "
                "their heads slightly to look back over their shoulders with weary deadpan expressions and comic sweat drops hanging. "
                "Medium 2.5-to-3-head chibi scale, top 34% pure white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
    ]
}

# ===========================================================================
# EP049: 탱커하는 뉴비새끼들 아구창 돌려버리고싶네
# ===========================================================================
EPISODES_UPGRADES["ep049"] = {
    "cuts": [
        {
            "cut_index": 1,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "오크 전사",
            "characters": ["오크 전사", "언데드 성기사"],
            "tail_target": "left",
            "dialogue": "탱커 잡은 뉴비들 진짜\n아구창 돌려버리고\n싶네 답답해 죽겠다!!",
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the veteran Orc Warrior tank girl (top-row #1 on Draft C cast sheet) "
                "on a 100% pure solid #FFFFFF white borderless background. Looming above with a furious red-faced grimace, "
                "wielding a 1H mace and heavy spiked shield, furrowed brow with fiery anime eyes venting pure rage, dramatic "
                "comic speed lines radiating behind her. In the lower-right background, the Undead Paladin shrinks in terror. "
                "Medium 2.5-to-3-head chibi scale, top 35% pure white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 2,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "언데드 성기사",
            "characters": ["언데드 성기사"],
            "tail_target": "right",
            "dialogue": "죄, 죄송해요 흑흑…\n초행이라 파티 전멸할까 봐\n한 마리씩만 데려온 건데…",
            "visual_prompt": (
                "High-angle shot looking down at the timid newbie Undead Paladin girl (bottom-row #3 on Draft C cast sheet) "
                "crouching on the floor on a 100% pure solid #FFFFFF white borderless background. She is clinging tightly behind "
                "her paladin shield, trembling violently with anime waterfall tears gushing from her hollow eyes, her skull hood "
                "quivering with anxiety. Positioned on the lower-right, leaving opposite left 46% clear white space for dialogue. "
                "Medium 2.5-to-3-head chibi scale. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 3,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "오크 전사",
            "characters": ["오크 전사", "언데드 성기사"],
            "tail_target": "left",
            "dialogue": "누가 쫄보처럼 한 마리만 잡아?!\n죽더라도 화끈하게 세 마리 몰아!\n힐은 내가 사제 멱살 잡고 시킨다!",
            "visual_prompt": (
                "Over-the-shoulder (OTS) diagonal shot from behind the Undead Paladin's trembling shoulder and skull hood on right. "
                "In the center-left, the Orc Warrior girl (top-row #1) leans forward aggressively, pointing an armored gauntlet right "
                "into the frame with an unexpected fierce grin and raised eyebrow, 1H weapon sheathed, inspiring rough battlefield "
                "mentorship! 100% pure solid #FFFFFF white borderless background, top 35% pure white headroom. Zero text, zero digits."
            ),
        },
        {
            "cut_index": 4,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "언데드 성기사",
            "characters": ["언데드 성기사", "오크 전사"],
            "tail_target": "right",
            "dialogue": "어…? 욕하면서 응원해 주는\n진짜 고인물 츤데레 형…?!",
            "visual_prompt": (
                "Dynamic Dutch tilt diagonal angle frame with tilted camera on a 100% pure solid #FFFFFF white borderless background. "
                "The Orc Warrior girl vigorously slams a heavy encouraging gauntlet onto the Undead Paladin's back, knocking up flying "
                "dust puffs and comic impact shockwaves! The paladin tumbles forward a step in shock, her eyes transforming into sparkling "
                "starry anime revelation with a blushing skeletal grin. Medium 2.5-to-3-head chibi scale, top 34% clear space. Zero text, zero digits."
            ),
        },
        {
            "cut_index": 5,
            "layout_slot": "top",
            "wordless": True,
            "speaker": None,
            "characters": ["언데드 성기사"],
            "tail_target": "center",
            "dialogue": None,
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the Undead Paladin girl (bottom-row #3 on Draft C cast sheet) in an intense "
                "heroic comedic freeze-frame on a 100% pure solid #FFFFFF white borderless background. Her face is glowing with golden "
                "holy energy sparks, a resolute smirk on her lips, one fist clenched tightly to her chest, brimming with newborn "
                "tanking courage! Expressive close-up filling ~78% height. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 6,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "언데드 성기사",
            "characters": ["언데드 성기사", "오크 전사"],
            "tail_target": "left",
            "dialogue": "형님 말대로 이번엔\n다섯 마리 몰아옵니다!!\n성스러운 빛으로 나를 치유하라!!",
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background. On the left, the Undead "
                "Paladin girl is dashing sprinting boldly forward across the frame with shield raised and 1H mace held high, kicking up "
                "a cloud of dust puffs! In the right background, the Orc Warrior watches her charge with arms crossed and a proud, "
                "smug older-sister smirk. Medium 2.5-to-3-head chibi scale, top 34% pure white headroom. Zero text, zero digits."
            ),
        },
    ]
}

# ===========================================================================
# EP050: 이글쓴 사람 상대방인데 얘기좀하자
# ===========================================================================
EPISODES_UPGRADES["ep050"] = {
    "cuts": [
        {
            "cut_index": 1,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "오크 전사",
            "characters": ["드워프 사냥꾼", "오크 전사"],
            "tail_target": "right",
            "dialogue": "어… 사냥꾼님?\n한손검이랑 사슬 갑옷까지\n전부 주사위 굴리셨네…?",
            "visual_prompt": (
                "Over-the-shoulder (OTS) diagonal shot from behind the armored shoulder and helmet of the Orc Warrior girl on the "
                "lower-right. In the lower-left, the Dwarf Hunter girl (middle-row #5 on Draft C cast sheet) is diving into an open "
                "wooden dungeon loot chest with greedy starry eyes, snatching both a 1H sword and a ring-mesh mail armor vest into her "
                "arms! 100% pure solid #FFFFFF white borderless background, medium 2.5-to-3-head chibi scale, top 35% pure white headroom. "
                "Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 2,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "나이트엘프 사제",
            "characters": ["나이트엘프 사제"],
            "tail_target": "right",
            "dialogue": "파티창에 쓰면 민망하실 테니\n던전 끝나고 조용히\n귓말로 매너 알려드리자~",
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background. The Night Elf Priest "
                "girl (bottom-row #2 on Draft C cast sheet) is tiptoeing sideways toward the right with hands folded over a small "
                "fantasy parchment scroll, wearing a gentle angelic smile and a tiny glowing halo above her head, looking thoughtful "
                "and kind. Positioned on the right, leaving the left 46% clear white space. Medium 2.5-to-3-head chibi scale. "
                "Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 3,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "나이트엘프 사제",
            "characters": ["나이트엘프 사제", "드워프 사냥꾼"],
            "tail_target": "left",
            "dialogue": "사냥꾼님~ 안 쓰는 장비는\n차비나 포기 누르는 게\n와우 암묵의 룰이에요^^",
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the Night Elf Priest girl on the lower-left, politely bending down with a "
                "cordial sweat drop and hands clasped together in gentle guidance. On the lower-right, the Dwarf Hunter girl stands "
                "clutching a bulky loot bag, looking sideways with a suspicious furrowed brow. 100% pure solid #FFFFFF white borderless "
                "background, medium 2.5-to-3-head chibi scale, top 35% clear headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 4,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "드워프 사냥꾼",
            "characters": ["드워프 사냥꾼"],
            "tail_target": "right",
            "dialogue": "누르는 주사위 버튼이\n있길래 눌렀는데 왜요?!\n안 누르면 잡혀가는 법 있어요?!",
            "visual_prompt": (
                "Dynamic Dutch-tilt diagonal frame with tilted camera on a 100% pure solid #FFFFFF white borderless background. "
                "The Dwarf Hunter girl (middle-row #5) stomps both feet aggressively, hands planted firmly on her hips, chin thrust "
                "out in a brazen smug sneer, roaring back with jagged teeth and flying comical spit droplets! Two 6-sided dice with "
                "black dot pips only bounce in the air. Medium 2.5-to-3-head chibi scale, right-biased, left 46% clear space. "
                "Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 5,
            "layout_slot": "top",
            "wordless": True,
            "speaker": None,
            "characters": ["나이트엘프 사제"],
            "tail_target": "center",
            "dialogue": None,
            "visual_prompt": (
                "High-angle shot looking down at the Night Elf Priest girl (bottom-row #2 on Draft C cast sheet) in an expressive "
                "comedic shock freeze-frame on a 100% pure solid #FFFFFF white borderless background. She is frozen stiff in mid-step, "
                "her halo cracked into crooked jagged halves, her eyes blank white soulless voids, jaw dropped wide open in utter "
                "speechlessness. Expressive solo close-up filling ~76% height. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 6,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "오크 전사",
            "characters": ["오크 전사", "나이트엘프 사제"],
            "tail_target": "left",
            "dialogue": "착하게 팁 알려줬더니\n적반하장 법 타령 실화냐…\n그냥 조용히 차단 박으시죠.",
            "visual_prompt": (
                "Back-view shot on a 100% pure solid #FFFFFF white borderless background. In the center-left, the Orc Warrior girl "
                "is seen from behind turning her back on the hunter, waving a dismissive hand over her shoulder while gently pulling "
                "the petrified Night Elf Priest girl away by her robe sleeve, both walking away with heavy deadpan sighs. Medium "
                "2.5-to-3-head chibi scale, top 34% pure white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
    ]
}

# ===========================================================================
# EP051: 딜템 다 양보하고 힐템입고 만렙찍으면 이렇게됨
# ===========================================================================
EPISODES_UPGRADES["ep051"] = {
    "cuts": [
        {
            "cut_index": 1,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "나이트엘프 사제",
            "characters": ["나이트엘프 사제", "스카이본 마법사"],
            "tail_target": "left",
            "dialogue": "주문력 반지요?\n전 힐러니까 딜러님\n먼저 드시라고 양보할게요!",
            "visual_prompt": (
                "Over-the-shoulder (OTS) diagonal shot from behind the shoulder and feathered hood of the Skyborne Mage girl on the right. "
                "On the lower-left, the Night Elf Priest girl (bottom-row #2 on Draft C cast sheet) bows politely with an angelic halo, "
                "gently sliding a glowing blue magical ring across the flat top of a wooden dungeon loot chest with a pure sweet smile. "
                "100% pure solid #FFFFFF white borderless background, medium 2.5-to-3-head chibi scale, top 35% pure white headroom. "
                "Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 2,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "나이트엘프 사제",
            "characters": ["나이트엘프 사제", "인간 흑마법사"],
            "tail_target": "left",
            "dialogue": "필드 퀘스트 보상 녹템도\n생각보다 튼튼해요!\n전 파티 힐만 열심히~",
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background. On the left, the Night Elf "
                "Priest girl is skipping cheerfully past with puffed proud cheeks, clutching a patched low-level cloth robe to her chest, "
                "wearing a bright innocent grin. On the right, the Human Warlock girl (middle-row #1 on Draft C cast sheet) stands "
                "watching with arms crossed and an incredulous squinting side-eye. Medium 2.5-to-3-head chibi scale, generous white headroom. "
                "Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 3,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "나이트엘프 사제",
            "characters": ["나이트엘프 사제"],
            "tail_target": "left",
            "dialogue": "드디어 감격의 60 만렙 달성!!\n고생한 내 캐릭터 장비창\n어디 한번 구경해 볼까~♪",
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the Night Elf Priest girl (bottom-row #2 on Draft C cast sheet) on a 100% pure "
                "solid #FFFFFF white borderless background. She is leaping into the air with golden celebration sparkle rays surrounding "
                "her, both arms raised high in triumphant victory, ecstatic blushing smile with tears of joy! Medium 2.5-to-3-head chibi "
                "scale in lower two-thirds, top 35% pure white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 4,
            "layout_slot": "bottom",
            "wordless": True,
            "speaker": None,
            "characters": ["나이트엘프 사제"],
            "tail_target": "center",
            "dialogue": None,
            "visual_prompt": (
                "Dynamic Dutch-tilt diagonal frame comic shock freeze-frame on a 100% pure solid #FFFFFF white borderless background. "
                "The Night Elf Priest girl holds an open parchment character stats sheet, staring down in absolute horror! Her jaw drops "
                "all the way down, eyes spinning in dizzy black-and-white whirlpool spirals, her body tilted sideways in paralyzed "
                "disbelief, cartoon shock impact lines bursting around her head. Tilted diagonal camera. Zero text, zero digits."
            ),
        },
        {
            "cut_index": 5,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "나이트엘프 사제",
            "characters": ["나이트엘프 사제", "스카이본 마법사"],
            "tail_target": "left",
            "dialogue": "손목이 24렙 초록템에\n전체 주문력이 30렙 수준?!\n착하게 살았는데 이게 뭐야!!",
            "visual_prompt": (
                "High-angle shot looking down at the Night Elf Priest girl collapsed on the ground, clutching her head in agony with "
                "waterfall anime tears flooding the floor on a 100% pure solid #FFFFFF white borderless background. Beside her, the "
                "Skyborne Mage girl kneels down awkwardly, scratching her cheek with an embarrassed, guilty sweat drop. Medium "
                "2.5-to-3-head chibi scale, top 35% pure white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 6,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "인간 흑마법사",
            "characters": ["인간 흑마법사", "나이트엘프 사제"],
            "tail_target": "left",
            "dialogue": "잠깐… 저기 가슴 부위에 있는\n하얀색 아이템은 대체 뭐예요?\n…어머, 그냥 기본 속옷이잖아?!",
            "visual_prompt": (
                "Back-view shot on a 100% pure solid #FFFFFF white borderless background. In the foreground, the Human Warlock girl "
                "stands seen from behind with her demonic horned hood, turning her head back over her shoulder with an impish smirk, "
                "pointing a finger at the priest's empty chest gear slot. In the background, the Night Elf Priest girl covers her face "
                "in blushing mortification! Medium 2.5-to-3-head chibi scale, top 34% pure white headroom. Zero text, zero digits."
            ),
        },
    ]
}

# ===========================================================================
# EP052: 물을 씨발 6덩이를 달라고하냐
# ===========================================================================
EPISODES_UPGRADES["ep052"] = {
    "cuts": [
        {
            "cut_index": 1,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "나이트엘프 사제",
            "characters": ["나이트엘프 사제", "스카이본 마법사"],
            "tail_target": "left",
            "dialogue": "법사님 반가워요!\n인던 출발하기 전에\n시원한 물 6덩이만 주세요~",
            "visual_prompt": (
                "Over-the-shoulder (OTS) diagonal shot from behind the shoulder and back of the Skyborne Mage girl on the right. "
                "On the lower-left, the Night Elf Priest girl (bottom-row #2 on Draft C cast sheet) extends both open hands forward "
                "cheerfully with a bright beaming smile and sparkling eyes, asking innocently. 100% pure solid #FFFFFF white borderless "
                "background, medium 2.5-to-3-head chibi scale, top 35% pure white headroom for dialogue. Zero text, zero digits."
            ),
        },
        {
            "cut_index": 2,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "스카이본 마법사",
            "characters": ["스카이본 마법사"],
            "tail_target": "right",
            "dialogue": "물 6덩이면 120병이야…\n마나탐 다섯 번 하면서\n서서 물만 뽑으라고?!",
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the Skyborne Mage girl (bottom-row #4 on Draft C cast sheet) on a 100% pure "
                "solid #FFFFFF white borderless background. She stands rigidly with dark crosshatched comic shadow cast over her eyes, "
                "a huge angry vein pulsing on her temple, holding a single fantasy corked glass flask with trembling white knuckles, "
                "radiating an ominous aura. Positioned on the right, left 46% clear space. Medium 2.5-to-3-head chibi scale. Zero text, zero digits."
            ),
        },
        {
            "cut_index": 3,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "스카이본 마법사",
            "characters": ["스카이본 마법사", "나이트엘프 사제"],
            "tail_target": "left",
            "dialogue": "내가 무슨 걸어 다니는\n정수기 기계냐고?!\n물 뽑다 인던 끝나겠다!!",
            "visual_prompt": (
                "Dynamic Dutch-tilt diagonal frame with tilted camera on a 100% pure solid #FFFFFF white borderless background. "
                "The Skyborne Mage girl flings her arms high in the air with an explosive yell, kicking up dust puffs as she stomps "
                "her foot, flying sweat drops and jagged manga teeth in furious exasperation! Across from her, the Night Elf Priest "
                "blinks with an innocent question mark. Medium 2.5-to-3-head chibi scale, top 35% clear headroom. Zero text, zero digits."
            ),
        },
        {
            "cut_index": 4,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "오크 전사",
            "characters": ["오크 전사", "스카이본 마법사"],
            "tail_target": "right",
            "dialogue": "저기 법사님… 화내지 말고…\n혹시 빵도 6덩이 정도\n비벼주실 수 있나요…?",
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background. From the right, the Orc "
                "Warrior girl is tiptoeing sneaking in with an awkward apologetic grin and nervous sweat beads, holding an empty wooden "
                "bowl in both hands, peeking sideways at the furious mage. The Skyborne Mage glares back with fiery red pupils. "
                "Medium 2.5-to-3-head chibi scale, top 34% pure white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 5,
            "layout_slot": "top",
            "wordless": True,
            "speaker": None,
            "characters": ["스카이본 마법사"],
            "tail_target": "center",
            "dialogue": None,
            "visual_prompt": (
                "High-angle shot looking down at the Skyborne Mage girl (bottom-row #4 on Draft C cast sheet) in an expressive comedic "
                "freeze-frame on a 100% pure solid #FFFFFF white borderless background. She is petrified in pure murderous silence, her "
                "eyes blazing with bright yellow comic flames, mouth a flat razor-thin line, trembling with restrained fury! Solo "
                "waist-up close-up filling ~77% height. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 6,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "스카이본 마법사",
            "characters": ["오크 전사", "스카이본 마법사"],
            "tail_target": "right",
            "dialogue": "오늘부로 영업 종료다!!\n파티고 인던이고 다 때려치우고\n귀환석 탈 테니 알아서 해!!",
            "visual_prompt": (
                "Back-view shot on a 100% pure solid #FFFFFF white borderless background. In the lower-right, the Skyborne Mage girl is "
                "seen from behind walking away toward the distance, turning her back on the party while tossing a glowing cyan Hearthstone "
                "into the air to summon a spiraling vortex! In the lower-left, the Orc Warrior reaches out a hand in desperate pleading. "
                "Medium 2.5-to-3-head chibi scale, top 34% pure white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
    ]
}

print("Loaded EP047-EP052 upgrade definitions.")

# ===========================================================================
# EP053: 탱거카 길을 알아야돼? 내가 가는 길이 곧 길이다
# ===========================================================================
EPISODES_UPGRADES["ep053"] = {
    "cuts": [
        {
            "cut_index": 1,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "나이트엘프 사제",
            "characters": ["나이트엘프 사제", "오크 전사"],
            "tail_target": "left",
            "dialogue": "전탱님, 이번 인던\n길 잘 아시죠?\n앞장서서 이끌어 주세요~",
            "visual_prompt": (
                "Over-the-shoulder (OTS) diagonal shot from behind the bulky armored shoulder and spiked pauldron of the Orc "
                "Warrior girl on the right. On the lower-left, the Night Elf Priest girl (bottom-row #2 on Draft C cast sheet) "
                "politely tilts her head with hands folded over her staff, pointing a slender finger toward the dark dungeon path "
                "with an earnest trusting smile. 100% pure solid #FFFFFF white borderless background, medium 2.5-to-3-head chibi "
                "scale, top 35% pure white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 2,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "오크 전사",
            "characters": ["오크 전사"],
            "tail_target": "right",
            "dialogue": "탱커가 꼭 길을 알아야 돼?!\n상남자 탱커가 가는 곳이\n곧 길이고 역사다!!",
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the Orc Warrior tank girl (top-row #1 on Draft C cast sheet) on a 100% pure "
                "solid #FFFFFF white borderless background. She stands proudly with 1H axe rested over one shoulder and sturdy spiked "
                "shield strapped to her arm, puffing out her chest with boundless smug arrogance, head thrown back in booming laughter "
                "with bold comic speed lines! Medium 2.5-to-3-head chibi scale, right-biased, left 46% clear space. Zero text, zero digits."
            ),
        },
        {
            "cut_index": 3,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "노움 도적",
            "characters": ["노움 도적", "오크 전사"],
            "tail_target": "left",
            "dialogue": "그리핀 탔는데 조종사가\n길 모르면 추락하는 거잖아요!\n지도 보고 가시라고요!!",
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background. The tiny Gnome Rogue "
                "girl (top-row #2 on Draft C cast sheet) is sprinting alongside the Orc Warrior, waving both arms frantically in the "
                "air with sweat beads flying, shouting in protest at the warrior who marches forward heedlessly. Medium 2.5-to-3-head "
                "chibi scale, top 35% pure white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 4,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "오크 전사",
            "characters": ["오크 전사"],
            "tail_target": "right",
            "dialogue": "수리비 한 푼 안 보태면서\n마차 기사 비유 보소?!\n꼬우면 네가 앞에서 걸어가든가!!",
            "visual_prompt": (
                "Dynamic Dutch-tilt diagonal frame with tilted camera on a 100% pure solid #FFFFFF white borderless background. "
                "The Orc Warrior girl slams her heavy metal shield edge aggressively against a rough dungeon wall with flying sparks "
                "and stone chips, spinning around to snarl with furious jagged teeth and comic steam venting from her nostrils! "
                "Medium 2.5-to-3-head chibi scale, right-biased, left 46% clear white space. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 5,
            "layout_slot": "top",
            "wordless": True,
            "speaker": None,
            "characters": ["오크 전사"],
            "tail_target": "center",
            "dialogue": None,
            "visual_prompt": (
                "High-angle shot looking down at the Orc Warrior girl (top-row #1 on Draft C cast sheet) in an expressive comedic "
                "freeze-frame on a 100% pure solid #FFFFFF white borderless background. She has faceplanted straight into a solid "
                "gray dungeon dead-end wall, stuck flat with little cartoon spiral stars circling around her helmet, completely silent "
                "and motionless in comedic humiliation. Expressive solo close-up filling ~78% height. Zero text, zero digits."
            ),
        },
        {
            "cut_index": 6,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "나이트엘프 사제",
            "characters": ["나이트엘프 사제", "노움 도적"],
            "tail_target": "left",
            "dialogue": "…당당하게 벽으로 직진하셨네.\n이게 바로 길치 탱커의 패기인가.\n그냥 벽 파고 들어갑시다…",
            "visual_prompt": (
                "Back-view shot on a 100% pure solid #FFFFFF white borderless background. In the lower-left, the Night Elf Priest "
                "girl and tiny Gnome Rogue girl are seen from behind standing side-by-side, heads tilted in a synchronized facepalm "
                "sigh, watching the warrior stuck in the wall ahead with comic sweat drops hanging. Medium 2.5-to-3-head chibi scale, "
                "top 34% pure white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
    ]
}

# ===========================================================================
# EP054: 내인생 가장황당한이유로 길드추방당햇다
# ===========================================================================
EPISODES_UPGRADES["ep054"] = {
    "cuts": [
        {
            "cut_index": 1,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "노움 도적",
            "characters": ["노움 도적", "오크 전사"],
            "tail_target": "left",
            "dialogue": "미접속 추방 기준이요?\n어제 길마님 공지대로\n이틀 미접속이면 칼추방이래요~",
            "visual_prompt": (
                "Over-the-shoulder (OTS) diagonal shot from behind the broad armored shoulder of the Orc Warrior guild master on the "
                "right. On the lower-left, the tiny Gnome Rogue girl (top-row #2 on Draft C cast sheet) stands on tiptoes holding an "
                "official guild parchment scroll, smiling cheerfully as she explains the policy with an innocent helpful expression. "
                "100% pure solid #FFFFFF white borderless background, medium 2.5-to-3-head chibi scale, top 35% pure white headroom. "
                "Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 2,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "오크 전사",
            "characters": ["오크 전사"],
            "tail_target": "right",
            "dialogue": "누가 그런 헛소리를 해?!\n내가 언제 이틀이랬어?\n그럼 주말에 여행도 못 가냐?!",
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the authoritarian Orc Warrior guild master (top-row #1 on Draft C cast sheet) "
                "looming above on a 100% pure solid #FFFFFF white borderless background. Arms folded tightly over her chest, terrifying "
                "dark comic shadow cast across her eyes, snarling with deep displeasure and furrowed brows, surrounded by dynamic comic "
                "pressure lines! Medium 2.5-to-3-head chibi scale, right-biased, left 46% clear space. Zero text, zero digits."
            ),
        },
        {
            "cut_index": 3,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "노움 도적",
            "characters": ["노움 도적", "오크 전사"],
            "tail_target": "left",
            "dialogue": "헉… ‘너요’ 하려다가…\n제가 다른 길드랑 착각했나 봐요!\n실수했습니다 진짜 죄송해요!!",
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background. The tiny Gnome Rogue "
                "girl steps backward in terror with both hands waving frantically in front of her, sweat droplets flying, bowing in "
                "an exaggerated apologetic cringe before the stern Orc Warrior who looks down coldly. Medium 2.5-to-3-head chibi "
                "scale, top 35% pure white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 4,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "오크 전사",
            "characters": ["오크 전사"],
            "tail_target": "right",
            "dialogue": "우리 길드에서\n실수는 용납 못 합니다.\n[길드에서 추방되었습니다].",
            "visual_prompt": (
                "Dynamic Dutch-tilt diagonal frame with tilted camera on a 100% pure solid #FFFFFF white borderless background. "
                "The Orc Warrior dramatically thrusts one heavy gauntleted index finger forward like an executioner, her eyes "
                "narrowed into cold merciless slits with an unyielding scowl! Cartoon lightning sparks crackle around her finger. "
                "Medium 2.5-to-3-head chibi scale, right-biased, left 46% clear space. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 5,
            "layout_slot": "top",
            "wordless": True,
            "speaker": None,
            "characters": ["노움 도적"],
            "tail_target": "center",
            "dialogue": None,
            "visual_prompt": (
                "High-angle shot looking down at the tiny Gnome Rogue girl (top-row #2 on Draft C cast sheet) in an expressive "
                "comedic freeze-frame on a 100% pure solid #FFFFFF white borderless background. She is sprawled flat on her stomach "
                "on the ground outside the guild hall, blank white hollow eyes, a translucent cartoon ghost soul escaping out of her "
                "mouth in utter disbelief, tiny dust puff around her. Solo close-up filling ~75% height. Zero text, zero digits."
            ),
        },
        {
            "cut_index": 6,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "트롤 주술사",
            "characters": ["트롤 주술사", "노움 도적"],
            "tail_target": "left",
            "dialogue": "대화 시작하고 1분 컷 추방 실화냐 ㅋㅋㅋ\n근데 저런 꼰대 길드에서 탈출한 게\n오히려 인생 최대 이득이다!",
            "visual_prompt": (
                "Back-view shot on a 100% pure solid #FFFFFF white borderless background. In the lower-left foreground, the Troll "
                "Shaman girl (middle-row #8 on Draft C cast sheet) is seen from behind walking away with staff on back, turning her "
                "head to look back over her shoulder with an amused smirk and offering an encouraging thumbs-up to the sprawled rogue. "
                "Medium 2.5-to-3-head chibi scale, top 34% pure white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
    ]
}

# ===========================================================================
# EP055: 와우 첨하는데 시발 미친겜이네
# ===========================================================================
EPISODES_UPGRADES["ep055"] = {
    "cuts": [
        {
            "cut_index": 1,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "스카이본 마법사",
            "characters": ["스카이본 마법사", "드워프 사냥꾼"],
            "tail_target": "left",
            "dialogue": "맵은 무슨 대륙급으로 넓은데\n40렙까지 두 발로 뚜벅뚜벅\n걸어 다니라고?! 미친 게임 아냐?!",
            "visual_prompt": (
                "Over-the-shoulder (OTS) diagonal shot from behind the shoulder and hood of the Dwarf Hunter girl on the right. "
                "On the lower-left, the newbie Skyborne Mage girl (bottom-row #4 on Draft C cast sheet) clutches a wide-open parchment "
                "world map, red puffed cheeks of pure indignation, shaking her little fists with angry cartoon cat-mouth! 100% pure "
                "solid #FFFFFF white borderless background, medium 2.5-to-3-head chibi scale, top 35% pure white headroom. "
                "Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 2,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "스카이본 마법사",
            "characters": ["스카이본 마법사"],
            "tail_target": "right",
            "dialogue": "스킬도 상급자 직접 찾아가야 하고\n퀘스트 위치도 안 알려주고…\n뭐야 이 20년 전 구렁내 겜은!!",
            "visual_prompt": (
                "Dynamic Dutch-tilt diagonal frame with tilted camera on a 100% pure solid #FFFFFF white borderless background. "
                "The Skyborne Mage girl is stumbling backward in theatrical rage, kicking up little comic dust clouds, waving her wooden "
                "staff toward the heavens with jagged shouting mouth and flying sweat droplets! Positioned on the right, leaving "
                "the left 46% clear white space. Medium 2.5-to-3-head chibi scale. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 3,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "드워프 사냥꾼",
            "characters": ["드워프 사냥꾼", "스카이본 마법사"],
            "tail_target": "left",
            "dialogue": "구렁내 난다면서 밥도 안 먹고\n한 번도 안 쉬더니 벌써 15렙 찍었냐? ㅋㅋㅋ",
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background. The Dwarf Hunter girl "
                "(middle-row #5 on Draft C cast sheet) leans casually against a wooden trail signpost with arms crossed, pointing her "
                "thumb sideways with a teasing sly smirk at the panting Skyborne Mage who sits catching her breath. Medium "
                "2.5-to-3-head chibi scale, top 35% pure white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 4,
            "layout_slot": "bottom",
            "wordless": True,
            "speaker": None,
            "characters": ["스카이본 마법사"],
            "tail_target": "center",
            "dialogue": None,
            "visual_prompt": (
                "High-angle shot looking down at the Skyborne Mage girl (bottom-row #4 on Draft C cast sheet) on a 100% pure solid "
                "#FFFFFF white borderless background. She freezes mid-step, looking down at a small fantasy pocket sundial clock in "
                "sheer horror, her eyes transformed into giant dizzy spiral whirlpools, jaw dropped to her collarbone in disbelief! "
                "Expressive solo close-up filling ~76% height. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 5,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "스카이본 마법사",
            "characters": ["스카이본 마법사", "드워프 사냥꾼"],
            "tail_target": "left",
            "dialogue": "헉 벌써 밤 9시라고?!\n나 아직 저기 지하 창고에 숨겨진\n99년 된 와인 찾으러 가야 해!!",
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the Skyborne Mage girl on the lower-left, eyes sparkling with sudden wild mania, "
                "gripping her staff with both hands and pivoting into high sprint gear, kicking up dust puffs! On the right, the Dwarf "
                "Hunter laughs into her hand. 100% pure solid #FFFFFF white borderless background, medium 2.5-to-3-head chibi scale, "
                "top 35% pure white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 6,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "스카이본 마법사",
            "characters": ["스카이본 마법사", "드워프 사냥꾼"],
            "tail_target": "left",
            "dialogue": "이 마약 같은 청국장 겜\n절대 아무도 발 들이지 마라!!\n중독은 나 혼자만 될 거니까!!",
            "visual_prompt": (
                "Back-view shot on a 100% pure solid #FFFFFF white borderless background. The Skyborne Mage girl is seen from behind "
                "sprinting full speed toward the distant horizon with massive comic dust clouds billowing behind her feet, turning "
                "her head back over her shoulder to shake a fiery fist at the viewer! In the background, Dwarf Hunter waves farewell. "
                "Medium 2.5-to-3-head chibi scale, top 34% pure white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
    ]
}

# ===========================================================================
# EP056: 인게임으로 블리자드가 사과함 ㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋ
# ===========================================================================
EPISODES_UPGRADES["ep056"] = {
    "cuts": [
        {
            "cut_index": 1,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "드워프 사냥꾼",
            "characters": ["드워프 사냥꾼", "스카이본 마법사"],
            "tail_target": "left",
            "dialogue": "어어?! 몹이 제자리에서 굳었어!\n스킬 단축키도 안 눌리는데\n서버 또 폭발한 거 아냐?!",
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background. The Dwarf Hunter girl "
                "and Skyborne Mage girl suddenly freeze mid-attack with speed lines coming to an abrupt halt; in front of them stands "
                "a dark cartoon mob silhouette frozen like an unmoving stone statue! Both characters have wide panicked anime eyes. "
                "Medium 2.5-to-3-head chibi scale, top 35% pure white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 2,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "노움 도적",
            "characters": ["노움 도적"],
            "tail_target": "right",
            "dialogue": "막보스 체력 5% 남겼는데\n서버 멈춤 실화냐고?!\n당장 블리자드 GM 나와라!!",
            "visual_prompt": (
                "Dynamic Dutch-tilt diagonal frame with tilted camera on a 100% pure solid #FFFFFF white borderless background. "
                "The tiny Gnome Rogue girl (top-row #2 on Draft C cast sheet) flings both daggers onto the floor, stomping both feet "
                "in furious rage, hair standing on end, roaring at the heavens with tears of sheer frustration and fiery comic aura! "
                "Medium 2.5-to-3-head chibi scale, right-biased, left 46% clear space. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 3,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "스카이본 마법사",
            "characters": ["스카이본 마법사", "노움 도적"],
            "tail_target": "left",
            "dialogue": "잠깐 다들 위를 봐봐!\n하늘에서 황금색으로\n공식 GM 공지가 떴어!!",
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the Skyborne Mage girl pointing upward toward the ceiling, where a brilliant "
                "golden aura is illuminating the air with gentle divine sparkles. Beside her, the Gnome Rogue looks up with wide curious "
                "round eyes. 100% pure solid #FFFFFF white borderless background, medium 2.5-to-3-head chibi scale, top 35% pure "
                "white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 4,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "스카이본 마법사",
            "characters": ["스카이본 마법사"],
            "tail_target": "right",
            "dialogue": "‘방금 서버 끊긴 거 미안하다.\n기술자들이 안전하댔거든.\n근데 아니더라고.’ …이게 끝?!",
            "visual_prompt": (
                "Over-the-shoulder (OTS) diagonal shot from behind the hooded shoulder of the Gnome Rogue on the lower-left. In the "
                "center-right, the Skyborne Mage girl holds up a glowing golden fantasy proclamation parchment, squinting at it with "
                "a twitching eyebrow and deadpan mouth in total surreal bewilderment. 100% pure solid #FFFFFF white borderless "
                "background, medium 2.5-to-3-head chibi scale, top 34% pure white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 5,
            "layout_slot": "top",
            "wordless": True,
            "speaker": None,
            "characters": ["노움 도적"],
            "tail_target": "center",
            "dialogue": None,
            "visual_prompt": (
                "High-angle shot looking down at the Gnome Rogue girl (top-row #2 on Draft C cast sheet) in an expressive comedic "
                "freeze-frame on a 100% pure solid #FFFFFF white borderless background. She is kneeling on the floor, holding her belly "
                "and roaring with uncontrollable laughter, tears shooting out from both eyes like water fountains, kicking her little "
                "boots in the air in pure hilarity! Expressive solo close-up filling ~77% height. Zero text, zero digits."
            ),
        },
        {
            "cut_index": 6,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "드워프 사냥꾼",
            "characters": ["드워프 사냥꾼", "노움 도적"],
            "tail_target": "left",
            "dialogue": "기술자 탓하고 쿨하게 끝?!\n진짜 너무 솔직하게 인정해서\n화내려다 빵 터졌네 ㅋㅋㅋㅋ",
            "visual_prompt": (
                "Back-view shot on a 100% pure solid #FFFFFF white borderless background. The Dwarf Hunter girl is seen from behind "
                "leaning backward with hands on hips, guffawing heartily at the dungeon ceiling, alongside the Gnome Rogue tumbling on "
                "the floor beside her in laughter. Medium 2.5-to-3-head chibi scale, top 34% pure white headroom. Zero text, zero digits."
            ),
        },
    ]
}

# ===========================================================================
# EP057: 전딜은진짜 인던데리고가는게아니구나.txt
# ===========================================================================
EPISODES_UPGRADES["ep057"] = {
    "cuts": [
        {
            "cut_index": 1,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "타우렌 드루이드",
            "characters": ["타우렌 드루이드", "오크 전사"],
            "tail_target": "left",
            "dialogue": "새벽 통곡의 동굴 클리어!\n드디어 내 야드용 가죽템\n코브라 장갑이 떴다~♡",
            "visual_prompt": (
                "Over-the-shoulder (OTS) diagonal shot from behind the bulky pauldron of the Orc Warrior girl on the right. On the "
                "lower-left, the Tauren Druid girl (bottom-row #8 on Draft C cast sheet) lovingly cradles a pair of sleek green reptile-leather "
                "gloves against her cheek with sparkling anime eyes and happy blushing cheeks. 100% pure solid #FFFFFF white borderless "
                "background, medium 2.5-to-3-head chibi scale, top 35% pure white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 2,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "오크 전사",
            "characters": ["오크 전사", "타우렌 드루이드"],
            "tail_target": "left",
            "dialogue": "민첩이랑 힘 붙은 가죽이네?\n딜전사도 당연히 써야지~\n입찰 버튼 꿀꺽!",
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background. On the left, the Orc "
                "Warrior girl comes lunging across the frame with a brazen toothy grin, snatching a rolling 6-sided die with black dot "
                "pips right out of the air! In the right background, the Tauren Druid girl gasps in frozen horror with round spiral eyes. "
                "Medium 2.5-to-3-head chibi scale, top 34% pure white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 3,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "언데드 성기사",
            "characters": ["언데드 성기사", "오크 전사"],
            "tail_target": "left",
            "dialogue": "성채 보스 방패 드롭!\n이번엔 내가 보기 탱인데\n전딜이 방패를 또 굴려?!",
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the Undead Paladin tank girl (bottom-row #3 on Draft C cast sheet) on the lower-left, "
                "holding 1H mace and sturdy shield, pointing an outraged armored finger at the Orc Warrior on the lower-right who is "
                "shamelessly tossing a newly looted shield into her overflowing backpack! 100% pure solid #FFFFFF white borderless "
                "background, medium 2.5-to-3-head chibi scale, top 35% clear headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 4,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "언데드 성기사",
            "characters": ["언데드 성기사"],
            "tail_target": "right",
            "dialogue": "주사위 져서 뺏겼으면\n그 자리에서 바로 파탈각이었다…\n전딜은 왜 탐욕이 끝이 없어?!",
            "visual_prompt": (
                "Dynamic Dutch-tilt diagonal frame with tilted camera on a 100% pure solid #FFFFFF white borderless background. "
                "The Undead Paladin girl trembles violently with clenched fists, dark sinister shadows crossing her face, cartoon "
                "steam jetting out from her skull hood in raging fury! Positioned on the right, leaving the left 46% clear white space. "
                "Medium 2.5-to-3-head chibi scale. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 5,
            "layout_slot": "top",
            "wordless": True,
            "speaker": None,
            "characters": ["타우렌 드루이드"],
            "tail_target": "center",
            "dialogue": None,
            "visual_prompt": (
                "High-angle shot looking down at the Tauren Druid girl (bottom-row #8 on Draft C cast sheet) in an expressive comedic "
                "freeze-frame on a 100% pure solid #FFFFFF white borderless background. She is sitting cross-legged on the floor like "
                "an enlightened monk, staring vacantly forward with soulless blank white eyes and a faint enlightened Buddha smile, "
                "transcending all earthly desires. Solo close-up filling ~76% height. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 6,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "타우렌 드루이드",
            "characters": ["타우렌 드루이드", "언데드 성기사"],
            "tail_target": "left",
            "dialogue": "밤새 깊이 반성해 봤는데요…\n전딜을 파티에 데려간\n제 자신이 만악의 근원이더군요.",
            "visual_prompt": (
                "Back-view shot on a 100% pure solid #FFFFFF white borderless background. The Tauren Druid girl and Undead Paladin girl "
                "are seen from behind walking away side-by-side toward a distant campfire with slumped, sorrowful shoulders, nodding in "
                "melancholy unison. Medium 2.5-to-3-head chibi scale, top 34% pure white headroom. Zero text, zero digits, zero bubbles."
            ),
        },
    ]
}

# ===========================================================================
# EP058: 포에버 던전 가보니까 힐러 할 자신이 사라짐…
# ===========================================================================
EPISODES_UPGRADES["ep058"] = {
    "cuts": [
        {
            "cut_index": 1,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "타우렌 드루이드",
            "characters": ["타우렌 드루이드", "오크 전사"],
            "tail_target": "left",
            "dialogue": "포에버 초반 던전…\n도트힐 하나 감아두고 나니\n할 게 없어서 너무 졸리네…",
            "visual_prompt": (
                "Over-the-shoulder (OTS) diagonal shot from behind the shoulder of the Orc Warrior girl on the lower-right. On the "
                "lower-left, the Tauren Druid girl (bottom-row #8 on Draft C cast sheet) sits comfortably on a wooden camp stool, gently "
                "flicking a single green healing leaf spell into the air with one hand while covering a lazy yawn with the other. "
                "100% pure solid #FFFFFF white borderless background, medium 2.5-to-3-head chibi scale, top 35% pure white headroom. "
                "Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 2,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "타우렌 드루이드",
            "characters": ["타우렌 드루이드"],
            "tail_target": "right",
            "dialogue": "인던 돌면서 강아지\n쓰다듬다 보면 저절로\n잠들겠는데… 냐암…",
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background. The Tauren Druid girl "
                "leans back comfortably in a side-profile view, softly petting a cute fluffy cartoon wolf pup curled on her lap, "
                "eyes half-closed in sleepy bliss with a tiny floating snot bubble from her nose. Positioned on the right, leaving "
                "the left 46% clear white space. Medium 2.5-to-3-head chibi scale. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 3,
            "layout_slot": "top",
            "wordless": False,
            "speaker": "트롤 주술사",
            "characters": ["트롤 주술사", "타우렌 드루이드"],
            "tail_target": "left",
            "dialogue": "아니 회드님!\n파티원들 피는 안 닳아도\n남는 마나로 근접 평타라도 치쇼!!",
            "visual_prompt": (
                "Dynamic Dutch-tilt diagonal frame with tilted camera on a 100% pure solid #FFFFFF white borderless background. "
                "The Troll Shaman girl (middle-row #8 on Draft C cast sheet) is flinging her arms in frantic exasperation, clutching "
                "her wooden healing totem in one hand while yelling with sharp jagged shark teeth and flying sweat drops at the "
                "unperturbed druid! Medium 2.5-to-3-head chibi scale, top 35% pure white headroom. Zero text, zero digits."
            ),
        },
        {
            "cut_index": 4,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "타우렌 드루이드",
            "characters": ["타우렌 드루이드"],
            "tail_target": "right",
            "dialogue": "어째서 고귀한 힐러인 내가\n그런 천하고 야만스러운 행동을\n직접 해야 하는 것이지..?",
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the Tauren Druid girl (bottom-row #8 on Draft C cast sheet) on a 100% pure "
                "solid #FFFFFF white borderless background. She looks down her snout with supreme aristocrat disdain, a small folding "
                "fan delicately covering her mouth, eyes narrowed in pure noble contempt and royal haughtiness! Positioned on the right, "
                "left 46% clear space. Medium 2.5-to-3-head chibi scale. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 5,
            "layout_slot": "top",
            "wordless": True,
            "speaker": None,
            "characters": ["트롤 주술사"],
            "tail_target": "center",
            "dialogue": None,
            "visual_prompt": (
                "High-angle shot looking down at the Troll Shaman girl (middle-row #8 on Draft C cast sheet) in an expressive comedic "
                "freeze-frame on a 100% pure solid #FFFFFF white borderless background. She is falling backward in utter shock, her "
                "totem dropping to the floor, eyes spinning in dizzy spiral circles, completely struck dumb by the unbelievable "
                "noble arrogance! Expressive solo close-up filling ~78% height. Zero text, zero digits, zero speech bubbles."
            ),
        },
        {
            "cut_index": 6,
            "layout_slot": "bottom",
            "wordless": False,
            "speaker": "오크 전사",
            "characters": ["오크 전사", "타우렌 드루이드"],
            "tail_target": "left",
            "dialogue": "와… 기세에 완전히 눌렸다.\n저분이야말로 이 험한 아제로스의\n진정한 황족 귀족 힐러다…!",
            "visual_prompt": (
                "Back-view shot on a 100% pure solid #FFFFFF white borderless background. In the lower-left, the Orc Warrior girl is "
                "seen from behind with 1H axe and sturdy shield on back, bowing slightly with hands clasped in awe-struck starry-eyed "
                "reverence toward the queenly Tauren Druid on the right who poses with serene elegance. Medium 2.5-to-3-head chibi scale, "
                "top 34% pure white headroom. Zero text, zero digits, zero speech bubbles."
            ),
        },
    ]
}


def apply_and_verify_all():
    print("=" * 60)
    print("UPGRADING AND AUDITING EP047 THROUGH EP058")
    print("=" * 60)

    all_passed = True

    for ep_id, upgrade_data in sorted(EPISODES_UPGRADES.items()):
        script_path = Path("data/episodes") / ep_id / "script.json"
        if not script_path.exists():
            print(f"ERROR: {script_path} does not exist!")
            all_passed = False
            continue

        raw = json.loads(script_path.read_text(encoding="utf-8"))

        # Verify cuts length
        assert len(upgrade_data["cuts"]) == len(raw["cuts"]), f"{ep_id}: cut count mismatch"

        # Apply upgraded cuts
        for i, new_cut in enumerate(upgrade_data["cuts"]):
            old_cut = raw["cuts"][i]
            assert new_cut["cut_index"] == old_cut["cut_index"]
            old_cut["visual_prompt"] = new_cut["visual_prompt"]
            old_cut["dialogue"] = new_cut["dialogue"]
            old_cut["characters"] = new_cut["characters"]
            old_cut["speaker"] = new_cut["speaker"]
            old_cut["tail_target"] = new_cut["tail_target"]
            old_cut["wordless"] = new_cut["wordless"]
            old_cut["layout_slot"] = new_cut["layout_slot"]

        # Validate with EpisodeScript
        script = EpisodeScript.model_validate(raw)

        # Audit script quality with strict_cinematic=True
        audit_res = audit_script_quality(script, strict_cinematic=True)

        if not audit_res["passed"]:
            print(f"FAILED AUDIT: {ep_id}")
            for err in audit_res["errors"]:
                print(f"  ERR: {err}")
            all_passed = False
            continue

        # Save upgraded script.json
        script_path.write_text(
            json.dumps(script.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Regenerate data/raw_cuts/<ep>/prompts.json
        raw_cuts_dir = Path("data/raw_cuts") / ep_id
        raw_cuts_dir.mkdir(parents=True, exist_ok=True)
        prompts_list = []
        for cut in script.cuts:
            aspect = "4:3" if cut.layout_slot == "top" else "16:9"
            target_file = raw_cuts_dir / f"cut_{cut.cut_index:02d}.png"
            prompt_str = artist.build_cut_image_prompt(cut)
            prompts_list.append({
                "cut_index": cut.cut_index,
                "aspect_ratio": aspect,
                "target_path": str(target_file.resolve()),
                "prompt": prompt_str,
            })

        prompts_path = raw_cuts_dir / "prompts.json"
        prompts_path.write_text(
            json.dumps(prompts_list, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        metrics = audit_res.get("cinematic_metrics", {})
        print(
            f"SUCCESS: {ep_id} ({script.source_post_no}) - "
            f"tags={metrics.get('camera_tags')} (count={len(metrics.get('camera_tags', []))}), "
            f"dynamic={metrics.get('dynamic_cuts')}/6, flat={metrics.get('flat_two_shot_cuts')}"
        )

    if all_passed:
        print("\nALL 12 EPISODES SUCCESSFULLY UPGRADED AND VERIFIED!")
    else:
        print("\nSOME EPISODES FAILED AUDIT. SEE ABOVE.")


if __name__ == "__main__":
    apply_and_verify_all()
