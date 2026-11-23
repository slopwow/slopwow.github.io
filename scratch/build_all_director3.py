# -*- coding: utf-8 -*-
"""Complete overhaul script for Director-3 (ep035 through ep046)."""

import json
from pathlib import Path
from wow_sloptoon.models import EpisodeScript, ComicCut, ItemTooltipSpec
from wow_sloptoon.artist import build_cut_image_prompt
from wow_sloptoon.writer import audit_script_quality

EPISODES = {}

# ---------------------------------------------------------------------------
# EP035: 성기사 이새끼들은 뉴비까지 등쳐먹으려드네ㅋㅋㅋ
# ---------------------------------------------------------------------------
EPISODES[35] = {
    "episode_number": 35,
    "source_post_no": "72269",
    "source_title": "성기사 이새끼들은 뉴비까지 등쳐먹으려드네ㅋㅋㅋ",
    "source_url": "https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=72269&exception_mode=recommend&page=5",
    "subtitle": "뉴비 사제 힐반지에 입찰 누른 징기와 곰왕 탱커의 사이다 저지 — 인던 상황극",
    "item_tooltip": None,
    "cuts": [
        {
            "cut_index": 1,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["나이트엘프 사제", "언데드 성기사"],
            "speaker": "나이트엘프 사제",
            "tail_target": "left",
            "dialogue": "우와! 치유량 반지 떴다!\n뉴비 첫 파템이에요!!",
            "wordless": False,
            "visual_prompt": (
                "Over-the-shoulder diagonal shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). Framed over the large foreground shoulder and back of the head of "
                "the Undead Paladin girl on the lower-right (round white cartoon skull cap, silver-white bob hair with icy tips, "
                "golden warhammer neatly stowed across her back). In the background on the lower-left, the Night Elf Priest girl "
                "(long silky lavender-silver hair, pointed elf ears, golden crescent circlet, lilac eyes, white-and-gold robe) "
                "clasps both hands happily beneath her chin with starry-eyed obsession and a joyful radiant smile (crescent staff "
                "leaned behind her), gazing up at a delicate silver-and-sapphire fantasy healing ring radiating bright rare-blue loot sparkles. "
                "Keep characters strictly in the lower two-thirds of the 4:3 frame at a consistent medium 2.5-to-3-head waist-up chibi scale, "
                "leaving generous completely empty pure #FFFFFF white headroom across the entire top 38%."
            ),
        },
        {
            "cut_index": 2,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["언데드 성기사"],
            "speaker": "언데드 성기사",
            "tail_target": "right",
            "dialogue": "어차피 뉴비라 모르겠지?\n징기지만…\n슬쩍 입찰 딸깍.",
            "wordless": False,
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). Positioned cleanly on the right half facing left, the Undead Paladin girl "
                "(round white skull cap, silver-white bob hair, crisp white-and-gold cloak, golden warhammer stowed on her back so "
                "both hands are completely free) tiptoes forward in stealthy creeping motion with a sly smug sneer and sinister "
                "shadow over her golden eyes, sneaking and tossing a chunky 6-sided fantasy loot cube die with dynamic motion blur; "
                "the die faces show ONLY simple classic round black dot pips (strictly ZERO digits, ZERO letters). "
                "Consistent medium 2.5-to-3-head waist-up chibi scale filling ~65% of canvas height, leaving the entire left 48% "
                "completely empty pure #FFFFFF white space for an external speech bubble."
            ),
        },
        {
            "cut_index": 3,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["타우렌 드루이드", "언데드 성기사"],
            "speaker": "타우렌 드루이드",
            "tail_target": "left",
            "dialogue": "어딜 감히!!\n징기가 뉴비 사제\n힐반지에 입찰을 눌러?!",
            "wordless": False,
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the heroic Tauren Druid girl on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). On the lower-left, the Tauren Druid girl (fluffy warm-brown plush tauren cow hood with curved ivory horns, "
                "golden nose ring, chestnut bangs, watery brown eyes, leafy green foliage mantle, gnarled staff stowed on back) lunges forward "
                "with a ferocious bear-spirit roar, slamming her heavy clawed hands down to shield the loot, surrounded by blazing emerald-green "
                "spirit bear aura flames! On the lower-right, the Undead Paladin tumbles backward in comic shock with jaw-drop and flying sweat drops. "
                "Medium 2.5-to-3-head chibi scale in the lower two-thirds, leaving generous pure #FFFFFF white headroom across the entire top 38%."
            ),
        },
        {
            "cut_index": 4,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["타우렌 드루이드"],
            "speaker": "타우렌 드루이드",
            "tail_target": "right",
            "dialogue": "주사위 졌으니 다행이지!\n뉴비 등쳐먹는 기사는\n곰왕이 못 봐준다!!",
            "wordless": False,
            "visual_prompt": (
                "Tilted dutch-tilt diagonal composition on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). Positioned cleanly on the right half facing left, the Tauren Druid girl (fluffy plush cow hood with horns, "
                "golden nose ring, leafy green foliage mantle, staff stowed on back) stands with puffed sulky cheeks, holding the glowing "
                "blue healing ring safely aloft in one protective palm while swinging her other fist sternly with swirling green nature leaves "
                "and tiny bear-king sparkles. Consistent medium 2.5-to-3-head waist-up chibi scale filling ~65% of canvas height, "
                "leaving the entire left 48% completely empty pure #FFFFFF white space for an external speech bubble."
            ),
        },
        {
            "cut_index": 5,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["언데드 성기사"],
            "speaker": None,
            "tail_target": "center",
            "dialogue": None,
            "wordless": True,
            "visual_prompt": (
                "High-angle shot looking down at the Undead Paladin girl kneeling on the ground in guilty speechless defeat, on a 100% pure "
                "solid #FFFFFF white borderless background (no scenery, no floor shading, no gray backdrop, no panel borders, zero text, "
                "zero letters, zero digits, zero speech bubbles, zero UI frames). Squarely centered and filling ~80% of canvas height. "
                "Caught-red-handed freeze-frame: deep ominous blue-gray gloom shadow cast across her white skull cap, golden eyes shrunk to "
                "blank trembling pinpoint pupils, jaw hanging open with a tiny pale cartoon soul puff floating up out of her parted mouth, "
                "both empty gloved hands frozen mid-air in total humiliation, golden warhammer stowed on her back."
            ),
        },
        {
            "cut_index": 6,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["나이트엘프 사제", "타우렌 드루이드"],
            "speaker": "나이트엘프 사제",
            "tail_target": "right",
            "dialogue": "곰왕 탱커님 최고예요!!\n다음부턴 성기사 빼고\n파티 가요♪",
            "wordless": False,
            "visual_prompt": (
                "Dynamic back-view shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). Positioned on the right half facing left: the Night Elf Priest girl turns her back partially to the defeated paladin, "
                "hugging the proud Tauren Druid's arm and looking back over her shoulder with a cheeky wink, sparkling lilac eyes, and relieved "
                "waterfall anime tears, joyfully flashing the glowing blue healing ring on her finger; beside her, the Tauren Druid crosses her arms "
                "with a blushing warm grin. Medium 2.5-to-3-head chibi scale, leaving the entire left 46% completely empty pure #FFFFFF white space."
            ),
        },
    ],
}

# ---------------------------------------------------------------------------
# EP036: 기사혐오는 당해야 생긴다
# ---------------------------------------------------------------------------
EPISODES[36] = {
    "episode_number": 36,
    "source_post_no": "75174",
    "source_title": "기사혐오는 당해야 생긴다",
    "source_url": "https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=75174&exception_mode=recommend&page=5",
    "subtitle": "가시덩굴 구릉 주특입 힐 목걸이 보기 입찰과 순수 뉴비 사제 — 인던 상황극",
    "item_tooltip": None,
    "cuts": [
        {
            "cut_index": 1,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["트롤 주술사", "언데드 성기사"],
            "speaker": "트롤 주술사",
            "tail_target": "left",
            "dialogue": "구릉 시작 전 확인!\n오늘 룰은 확실히\n주특입 맞죠?",
            "wordless": False,
            "visual_prompt": (
                "Over-the-shoulder diagonal shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). Framed over the large foreground back and shoulder of the Undead Paladin "
                "Protection tank on the lower-right (round white skull cap, silver-white bob hair, golden crest shield on left arm, "
                "compact one-handed mace in right hand, zero 2H weapon). In the background on the lower-left, the Troll Shaman girl "
                "(sky-blue plush troll onesie hood with spiky red mohawk crest, floppy pierced ears, mint-teal bob hair, bright green eyes) "
                "raises one index finger checking party rules with an earnest eager grin, her carved rustic wooden totem planted on the ground beside her. "
                "Medium 2.5-to-3-head chibi scale in the lower two-thirds, leaving generous pure #FFFFFF white headroom across the entire top 38%."
            ),
        },
        {
            "cut_index": 2,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["트롤 주술사"],
            "speaker": "트롤 주술사",
            "tail_target": "right",
            "dialogue": "오, 첫 넴 힐 목걸이네.\n난 고술이니까 양심껏\n차비 눌러야지~",
            "wordless": False,
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). Positioned cleanly on the right half facing left, the Troll Shaman girl "
                "(sky-blue troll hood with red mohawk, mint-teal hair, green eyes, tribal scarf) smiles with saintly closed-eye "
                "virtuous pride and tiny angelic sparkles, politely folding her hands as she uses her foot to roll a pass/greed cube die "
                "with black dot pips only (zero digits) beside a hovering glowing blue fantasy healing amulet, small wooden totem standing nearby. "
                "Consistent medium 2.5-to-3-head waist-up chibi scale filling ~65% of canvas height, leaving the entire left 48% "
                "completely empty pure #FFFFFF white space for an external speech bubble."
            ),
        },
        {
            "cut_index": 3,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["언데드 성기사", "트롤 주술사"],
            "speaker": "언데드 성기사",
            "tail_target": "left",
            "dialogue": "보기 특 템이네.\n바로 입찰.",
            "wordless": False,
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the Undead Paladin Protection tank on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). On the lower-left, the Undead Paladin tank (golden crest shield strapped on left arm, one-handed mace sheathed at hip) "
                "lunges forward with a completely shameless deadpan smirk, snatching the glowing blue healing amulet straight out of the air while tossing "
                "a chunky need die with black dot pips only; on the lower-right, the Troll Shaman girl flings both arms up in horrified jaw-drop with flying sweat drops! "
                "Medium 2.5-to-3-head chibi scale in the lower two-thirds, leaving generous pure #FFFFFF white headroom across the entire top 38%."
            ),
        },
        {
            "cut_index": 4,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["트롤 주술사"],
            "speaker": None,
            "tail_target": "center",
            "dialogue": None,
            "wordless": True,
            "visual_prompt": (
                "Tilted dutch-tilt diagonal angle comedic close-up freeze-frame of the Troll Shaman girl on a 100% pure solid #FFFFFF "
                "white borderless background (no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, "
                "zero digits, zero speech bubbles, zero UI frames). Squarely centered and filling ~80% of canvas height; silent reaction panel. "
                "Speechless shock freeze-frame: deep ominous dark blue gloom shadow across her sky-blue troll hood, bright green eyes shrunk "
                "to tiny quivering spiral pupils, mint-teal bob hair frizzed with crackling cyan static sparks, mouth wide agape in petrified disbelief."
            ),
        },
        {
            "cut_index": 5,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["트롤 주술사", "나이트엘프 사제"],
            "speaker": "트롤 주술사",
            "tail_target": "left",
            "dialogue": "사제님! 저거 힐 목걸이예요!\n탱 보기가 주특입 어기고\n먹었잖아요!!",
            "wordless": False,
            "visual_prompt": (
                "High-angle shot looking down at the dramatic confrontation on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). On the lower-left, the Troll Shaman girl leans frantically toward the Priest, pointing wildly off-panel with "
                "steaming cartoon fury, anger veins on her hood, and waterfall anime tears; on the lower-right, the Night Elf Priest girl "
                "(lavender-silver hair, pointed ears, golden circlet, white-and-gold robe, staff stowed behind) blinks up slowly with big innocent "
                "clueless lilac eyes and a puzzled head tilt. Medium 2.5-to-3-head chibi scale, leaving generous pure #FFFFFF white headroom across the top 38%."
            ),
        },
        {
            "cut_index": 6,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["나이트엘프 사제", "트롤 주술사"],
            "speaker": "나이트엘프 사제",
            "tail_target": "right",
            "dialogue": "어… 저기요,\n근데 주특입이\n뭐예요…?",
            "wordless": False,
            "visual_prompt": (
                "Dynamic slapstick shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). On the far-right, the Troll Shaman girl faceplants flat onto the white floor in total soul-crushed defeat, "
                "sprawled with dizzy spiral eyes and tiny cartoon wisps rising from her red mohawk; right beside her, the Night Elf Priest girl "
                "stands with her back partially turned, looking back over her shoulder with starry clueless lilac eyes, clasping both hands "
                "innocently asking her question. Medium 2.5-to-3-head chibi scale, leaving the entire left 46% completely empty pure #FFFFFF white space."
            ),
        },
    ],
}

# ---------------------------------------------------------------------------
# EP037: 진짜 개또라이 많네
# ---------------------------------------------------------------------------
EPISODES[37] = {
    "episode_number": 37,
    "source_post_no": "72196",
    "source_title": "진짜 개또라이 많네",
    "source_url": "https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=72196&exception_mode=recommend&page=5",
    "subtitle": "붉은십자군 수도원 2·3번 무고지 탱힐 투클라 발각 대참사 — 인던 상황극",
    "item_tooltip": None,
    "cuts": [
        {
            "cut_index": 1,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["노움 도적", "언데드 성기사"],
            "speaker": "노움 도적",
            "tail_target": "left",
            "dialogue": "수도원 2·3번인데\n왜 이렇게 느리지?\n보기님 또 멈췄네…",
            "wordless": False,
            "visual_prompt": (
                "Over-the-shoulder diagonal shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). Framed over the large foreground shoulder and back of the head of "
                "the Gnome Rogue girl on the lower-left (blonde twin pigtails with pink-blue tips, aviator goggles on forehead, "
                "poison daggers neatly sheathed at belt). In the background on the lower-right, the Undead Paladin Protection tank "
                "(round white skull cap, silver-white bob hair, golden crest shield on left arm, compact 1H mace in right hand, zero 2H weapon) "
                "stands completely frozen rigid mid-stride like a wooden statue with blank hollow unfocused eyes. "
                "Medium 2.5-to-3-head chibi scale in lower two-thirds, leaving generous pure #FFFFFF white headroom across top 38%."
            ),
        },
        {
            "cut_index": 2,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["언데드 성기사", "트롤 주술사"],
            "speaker": "트롤 주술사",
            "tail_target": "right",
            "dialogue": "아, 보기 멈췄다.\n이번엔 복술 차례~\n토템 톡.",
            "wordless": False,
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). On the left, the Undead Paladin tank remains frozen totally stiff like a mannequin; "
                "on the right half, the Troll Shaman girl (sky-blue troll hood with red mohawk, mint-teal bob hair, green eyes) suddenly springs "
                "into bouncy mechanical action with a manic robotic smile, slamming a carved rustic wooden totem down on the floor with dynamic "
                "speed lines. Consistent medium 2.5-to-3-head chibi scale filling ~62% of canvas height, leaving the entire top 35% completely empty "
                "pure #FFFFFF white space for a speech bubble."
            ),
        },
        {
            "cut_index": 3,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["노움 도적", "트롤 주술사"],
            "speaker": "노움 도적",
            "tail_target": "left",
            "dialogue": "잠깐만요!!\n보기랑 복술 둘이서\n무고지 투클라였어요?!",
            "wordless": False,
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the Gnome Rogue girl on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). On the lower-left, the Gnome Rogue girl leaps forward in outraged discovery, pointing an accusing finger with "
                "shouting jaw-drop and flying sweat drops (daggers sheathed at belt); on the lower-right, the Troll Shaman girl has instantly frozen "
                "stiff mid-step like an unmoving statue with blank hollow eyes (tabbed back to tank). "
                "Medium 2.5-to-3-head chibi scale, leaving generous pure #FFFFFF white headroom across top 38%."
            ),
        },
        {
            "cut_index": 4,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["언데드 성기사"],
            "speaker": "언데드 성기사",
            "tail_target": "right",
            "dialogue": "전멸 안 했잖아.\n그래서 님이\n피해 본 거 있냐?",
            "wordless": False,
            "visual_prompt": (
                "Dynamic back-view shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). Positioned on the right half facing left: the Undead Paladin tank (golden crest shield on left arm, 1H mace sheathed at hip) "
                "is seen from behind, walking away casually, turning her head with a dismissive side-eye sneer and looking back over her shoulder "
                "while waving one gloved hand dismissively. Consistent medium 2.5-to-3-head waist-up chibi scale filling ~65% of canvas height, "
                "leaving the entire left 48% completely empty pure #FFFFFF white space for an external speech bubble."
            ),
        },
        {
            "cut_index": 5,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["노움 도적"],
            "speaker": None,
            "tail_target": "center",
            "dialogue": None,
            "wordless": True,
            "visual_prompt": (
                "High-angle shot looking down at the Gnome Rogue girl kneeling on the ground in stunned speechless defeat, on a 100% pure "
                "solid #FFFFFF white borderless background (no scenery, no floor shading, no gray backdrop, no panel borders, zero text, "
                "zero letters, zero digits, zero speech bubbles, zero UI frames). Squarely centered and filling ~80% of canvas height. "
                "Speechless shock freeze-frame: green aviator goggles knocked crooked on her forehead, deep dark blue gloom shadow across her face, "
                "blue eyes shrunk to trembling pinpoint pupils, mouth agape, steam puffing silently from her pink-blue twin pigtails."
            ),
        },
        {
            "cut_index": 6,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["노움 도적", "트롤 주술사"],
            "speaker": "노움 도적",
            "tail_target": "right",
            "dialogue": "남의 시간 다 뺏어놓고\n피해가 없대…\n아, 복술 또 멈췄네.",
            "wordless": False,
            "visual_prompt": (
                "Tilted dutch-tilt diagonal composition on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). Positioned on the right half facing left: the Gnome Rogue girl flings both hands in the air in theatrical "
                "exasperated defeat with drooping half-lidded eyes and a giant sweat drop; in the background, the Troll Shaman stands frozen solid "
                "like a museum mannequin with a tiny comic cobweb forming on her nose. Medium 2.5-to-3-head chibi scale, leaving the left 46% pure white."
            ),
        },
    ],
}

# ---------------------------------------------------------------------------
# EP038: 길 잃은 뉴비한테 와우 알려줬다
# ---------------------------------------------------------------------------
EPISODES[38] = {
    "episode_number": 38,
    "source_post_no": "67419",
    "source_title": "길 잃은 뉴비한테 와우 알려줬다",
    "source_url": "https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=67419&exception_mode=recommend&page=5",
    "subtitle": "가시덤불 골짜기 길 잃은 쪼렙에게 도적이 가르쳐 준 와우 — 필드 PvP 상황극",
    "item_tooltip": None,
    "cuts": [
        {
            "cut_index": 1,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["타우렌 드루이드", "노움 도적"],
            "speaker": "노움 도적",
            "tail_target": "right",
            "dialogue": "가덤골에서 길 잃은\n쪼렙 뉴비 발견~\n두리번거리는 거 봐.",
            "wordless": False,
            "visual_prompt": (
                "Over-the-shoulder diagonal shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). Framed over the foreground back and shoulder of the Gnome Rogue girl "
                "crouching in faint translucent stealth shimmer on the lower-right (aviator goggles, pink-blue pigtails, daggers at belt). "
                "In the background on the lower-left, adorable low-level Tauren Druid girl (fluffy cow hood, ivory horns, golden nose ring, "
                "chestnut bangs, watery brown eyes, staff stowed on back) peers around in lost confusion holding an upside-down rustic parchment map "
                "(blank wavy lines only, zero text). Medium 2.5-to-3-head chibi scale, leaving generous pure #FFFFFF white headroom across top 38%."
            ),
        },
        {
            "cut_index": 2,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["타우렌 드루이드", "노움 도적"],
            "speaker": "노움 도적",
            "tail_target": "right",
            "dialogue": "물속 정예 퀘였나?\n다시 헤엄쳐 나오네.\n지도 보는 거 귀엽다♪",
            "wordless": False,
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). On the left half, the dripping-wet Tauren Druid girl tiptoes shivering "
                "out of the water with cute water droplets and a green water lily on her cow hood, staring at her damp map with a confused pout; "
                "on the right half, the crouching stealth Gnome Rogue rests her chin dreamily on both hands with fond sparkling eyes. "
                "Consistent medium 2.5-to-3-head chibi scale filling ~62% of canvas height, leaving top 35% empty pure #FFFFFF white space."
            ),
        },
        {
            "cut_index": 3,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["타우렌 드루이드", "노움 도적"],
            "speaker": "노움 도적",
            "tail_target": "right",
            "dialogue": "어디로 가야 할지\n모르겠지?\n내가 알려줄게~",
            "wordless": False,
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the ambush on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). On the lower-left, the clueless Tauren Druid stands peering at her map; on the lower-right, the Gnome Rogue girl "
                "drops out of stealth right behind the Druid's back with crisp cartoon smoke wisps, lunging forward with a wicked sinister grin "
                "and dark shadow over her eyes while drawing her dual glowing poison-green daggers! "
                "Medium 2.5-to-3-head chibi scale, leaving generous pure #FFFFFF white headroom across the entire top 38%."
            ),
        },
        {
            "cut_index": 4,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["타우렌 드루이드"],
            "speaker": None,
            "tail_target": "center",
            "dialogue": None,
            "wordless": True,
            "visual_prompt": (
                "High-angle shot looking down at the Tauren Druid girl in stunned ambush terror, on a 100% pure solid #FFFFFF white borderless "
                "background (no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles). "
                "Squarely centered and filling ~80% of canvas height; silent ambush panel. Terror freeze-frame: big glossy brown eyes blown wide with "
                "tiny trembling pinpoint pupils, blank parchment map flying upward out of her startled hands, deep blue gloom shadow across her cow hood, "
                "and a sharp poison-green dagger glint flashing menacingly just behind her floppy ear."
            ),
        },
        {
            "cut_index": 5,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["노움 도적", "타우렌 드루이드"],
            "speaker": "노움 도적",
            "tail_target": "left",
            "dialogue": "일단 무덤으로\n가보자!!",
            "wordless": False,
            "visual_prompt": (
                "Tilted dutch-tilt diagonal composition on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). On the lower-left, the Gnome Rogue girl lands in a flashy dynamic ninja pose crossing her glowing poison-green daggers "
                "with dynamic cartoon speed lines and a cheeky triumphant wink (cute slapstick only, zero blood); on the lower-right, the Tauren Druid girl "
                "faceplants flat onto the white floor with spiral dizzy eyes and circling cartoon stars. Medium 2.5-to-3-head chibi scale, top 38% pure white."
            ),
        },
        {
            "cut_index": 6,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["노움 도적", "타우렌 드루이드"],
            "speaker": "노움 도적",
            "tail_target": "right",
            "dialogue": "이게 와우다.\n오늘 하나 배웠지?♪",
            "wordless": False,
            "visual_prompt": (
                "Dynamic back-view shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). Positioned on the right half: the Gnome Rogue girl is seen from behind, walking away casually with dual daggers "
                "sheathed at her belt, looking back over her shoulder with a cheerful thumbs-up and proud mentor wink; on the left, the Tauren Druid "
                "floats as a pale translucent bluish spirit ghost with wispy tail, crying comical waterfall anime tears while holding her damp map. "
                "Medium 2.5-to-3-head chibi scale, leaving the left 46% pure white."
            ),
        },
    ],
}

# ---------------------------------------------------------------------------
# EP039: 오늘 수도원에서본 레전드 사건..JPG
# ---------------------------------------------------------------------------
EPISODES[39] = {
    "episode_number": 39,
    "source_post_no": "70711",
    "source_title": "오늘 수도원에서본 레전드 사건..JPG",
    "source_url": "https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=70711&exception_mode=recommend&page=5",
    "subtitle": "붉은십자군 수도원 '화이트메인의 모자' 인던 가이드북 맹신 법사 대참사 — 인던 상황극",
    "item_tooltip": None,
    "cuts": [
        {
            "cut_index": 1,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["나이트엘프 사제", "스카이본 마법사"],
            "speaker": "나이트엘프 사제",
            "tail_target": "left",
            "dialogue": "드디어 화이트메인의\n모자 떴다…!!\n힐러 졸업템이에요!",
            "wordless": False,
            "item_tooltip": {
                "item_name": "화이트메인의 모자",
                "wowhead_item_id": 7720,
                "quality": "rare",
                "slot_left": "머리",
                "slot_right": "천",
                "lines": [
                    "획득 시 귀속",
                    "방어도 52",
                    "체력 +9",
                    "지능 +14",
                    "정신력 +14",
                    "요구 레벨 39",
                ],
                "equip_effects": [],
                "icon_name": "inv_helmet_12",
                "preferred_corner": "top_right",
                "target_width": 288,
            },
            "visual_prompt": (
                "Over-the-shoulder diagonal shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). Framed over the large foreground shoulder and back of the head of "
                "the Skyborne Mage girl on the lower-right (blonde hair with aqua tips, feather charm, sailor collar, bread and flask put away). "
                "In the background on the lower-left, the Night Elf Priest girl (lavender-silver hair, pointed ears, golden circlet, white robe, "
                "staff stowed behind) clasps both hands with joyful tearful lilac eyes, gazing up at an ornate crimson-and-gold cloth bishop miter hat "
                "radiating rare-blue loot sparkles hovering between them. Keep characters in lower two-thirds, leaving generous pure #FFFFFF white "
                "headroom across top 38% and keeping the top-right corner completely empty for an item tooltip."
            ),
        },
        {
            "cut_index": 2,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["스카이본 마법사"],
            "speaker": "스카이본 마법사",
            "tail_target": "right",
            "dialogue": "오~ 인던 가이드북에\n캐스터템이라 써있네!\n바로 입찰해서 먹음♪",
            "wordless": False,
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). Positioned cleanly on the right half facing left, the Skyborne Mage girl "
                "(golden-blonde hair with airy pastel sky-blue tips, sailor collar, bread and flask put away) sprints forward "
                "clutching a thick blank leather fantasy guidebook under her left arm while enthusiastically tossing a chunky 6-sided "
                "loot cube die with black dot pips only (strictly ZERO digits, ZERO letters), beaming with a starry-eyed greedy grin. "
                "Medium 2.5-to-3-head chibi scale filling ~65% of canvas height, leaving the left 48% empty pure #FFFFFF white space."
            ),
        },
        {
            "cut_index": 3,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["나이트엘프 사제", "스카이본 마법사"],
            "speaker": "나이트엘프 사제",
            "tail_target": "left",
            "dialogue": "법사님!! 지금 낀 모자가\n주문력 훨씬 더 높은데\n왜 굴리셨어요?!",
            "wordless": False,
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the confrontation on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). On the lower-left, the Night Elf Priest girl lunges forward pointing at the Mage's head with trembling "
                "outraged lilac eyes, shouting jaw-drop, and flying sweat drops (staff stowed behind); on the lower-right, the Skyborne Mage girl "
                "stands totally unbothered with a breezy smug smile, casually balancing the crimson bishop miter hat right on top of her glowing "
                "wizard circlet. Medium 2.5-to-3-head chibi scale, leaving generous pure #FFFFFF white headroom across top 38%."
            ),
        },
        {
            "cut_index": 4,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["스카이본 마법사"],
            "speaker": "스카이본 마법사",
            "tail_target": "right",
            "dialogue": "그런 건 모르겠고\n가이드북에 써있다고요!\n님이 가이드북보다 잘 앎?!",
            "wordless": False,
            "visual_prompt": (
                "Tilted dutch-tilt diagonal angle on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). Positioned on the right half facing left, the Skyborne Mage girl (wearing the crimson-and-gold bishop miter hat "
                "perched proudly on her head) slams her thick blank leather fantasy guidebook against her chest with puffed sulky cheeks, "
                "pointing her other finger forward in righteous lecture with haughty closed eyes and golden sparkles. "
                "Consistent medium 2.5-to-3-head chibi scale filling ~65% of canvas height, leaving the left 48% pure white."
            ),
        },
        {
            "cut_index": 5,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["나이트엘프 사제"],
            "speaker": None,
            "tail_target": "center",
            "dialogue": None,
            "wordless": True,
            "visual_prompt": (
                "High-angle shot looking down at the Night Elf Priest girl slumped kneeling on the ground in total speechless despair, "
                "on a 100% pure solid #FFFFFF white borderless background (no scenery, no floor shading, no gray backdrop, no panel borders, "
                "zero text, zero letters, zero digits, zero speech bubbles, zero UI frames). Squarely centered and filling ~80% of canvas height. "
                "Soul-leaving deadpan horror freeze-frame: deep ominous dark blue gloom shadow across her crescent circlet, heavy dark eye bags, "
                "lilac eyes blown wide with trembling pinpoint pupils, and a pale wispy cartoon soul puff floating up out of her parted mouth."
            ),
        },
        {
            "cut_index": 6,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["오크 전사", "나이트엘프 사제"],
            "speaker": "오크 전사",
            "tail_target": "right",
            "dialogue": "사제님 진정해…\n가이드북 신도랑은\n대화하는 거 아냐.",
            "wordless": False,
            "visual_prompt": (
                "Dynamic back-view shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). Positioned on the right half facing left: the Orc Warrior girl (green orc onesie hood, silver battle axe strapped "
                "across her back) is seen partially from behind, leaning down to pat the slumped Priest's shoulder, looking back over her shoulder "
                "with a wry sympathetic sweat-drop grimace; beside her, the Priest sits motionless with hollow dead-fish eyes. "
                "Medium 2.5-to-3-head chibi scale, leaving the left 46% pure white."
            ),
        },
    ],
}

# ---------------------------------------------------------------------------
# EP040: "틀딱 씨, 우리 파티에서 나가주세요."
# ---------------------------------------------------------------------------
EPISODES[40] = {
    "episode_number": 40,
    "source_post_no": "104746",
    "source_title": "\"틀딱 씨, 우리 파티에서 나가주세요.\"",
    "source_url": "https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=104746&exception_mode=recommend&page=5",
    "subtitle": "죽음의 폐광 뉴비 낭만팟 vs 40인 공대장 출신 틀딱의 효율 훈수 — 인던 상황극",
    "item_tooltip": None,
    "cuts": [
        {
            "cut_index": 1,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["오크 전사", "스카이본 마법사"],
            "speaker": "오크 전사",
            "tail_target": "left",
            "dialogue": "와~ 죽음의 폐광\n퀘스트 지문 재밌다!\n천천히 구경하며 가요♪",
            "wordless": False,
            "visual_prompt": (
                "Over-the-shoulder diagonal shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). Framed over the large foreground shoulder and back of the head of "
                "the Skyborne Mage girl on the lower-right (blonde hair with aqua tips, feather charm, sailor collar). "
                "In the background on the lower-left, newbie Orc Warrior girl (green orc onesie hood, silver battle axe on back) "
                "holds open a rolled rustic parchment quest scroll (blank wavy lines, zero text) with wide starry adventurous crimson eyes "
                "and an excited smile. Medium 2.5-to-3-head chibi scale, leaving generous pure #FFFFFF white headroom across top 38%."
            ),
        },
        {
            "cut_index": 2,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["언데드 성기사"],
            "speaker": "언데드 성기사",
            "tail_target": "right",
            "dialogue": "시간 낭비죠.\n화약 주워 대포로 문 땄음.\n바로 밴클리프 가죠.",
            "wordless": False,
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). Positioned cleanly on the right half facing left, the Undead Paladin girl "
                "(round white skull cap, silver-white bob hair, golden warhammer stowed on back) sprints ahead beside a small smoking "
                "rustic iron pirate cannon with dynamic speed lines and a huge cartoon puff of smoke, dusting off her gloves with a smug sneer "
                "of speedrun efficiency. Consistent medium 2.5-to-3-head chibi scale filling ~65% of canvas height, leaving the left 48% pure white."
            ),
        },
        {
            "cut_index": 3,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["오크 전사", "언데드 성기사"],
            "speaker": "오크 전사",
            "tail_target": "left",
            "dialogue": "틀딱 씨, 제발\n우리 파티에서\n나가주세요…",
            "wordless": False,
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the confrontation on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). On the lower-left, the newbie Orc Warrior girl stands tall with both hands on her hips, glaring with a dead-serious "
                "fed-up frown and tired sweat drop; on the lower-right, the Undead Paladin girl tilts her head with a self-absorbed smug smirk, "
                "completely failing to read the room. Medium 2.5-to-3-head chibi scale, leaving generous pure #FFFFFF white headroom across top 38%."
            ),
        },
        {
            "cut_index": 4,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["언데드 성기사"],
            "speaker": "언데드 성기사",
            "tail_target": "right",
            "dialogue": "내가 오리 40인 공대장 출신인데!\n전사할 거면 성기사 하지~\n법사가 진짜 사긴데…",
            "wordless": False,
            "visual_prompt": (
                "Tilted dutch-tilt diagonal angle on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). Positioned on the right half facing left, the Undead Paladin girl raises one lecturing finger high in unstoppable "
                "veteran raid-leader mode, flinging her arms with eyes half-closed in smug preaching bliss as golden lecture aura sparkles swirl "
                "endlessly around her. Consistent medium 2.5-to-3-head chibi scale filling ~65% of canvas height, leaving the left 48% pure white."
            ),
        },
        {
            "cut_index": 5,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["스카이본 마법사"],
            "speaker": None,
            "tail_target": "center",
            "dialogue": None,
            "wordless": True,
            "visual_prompt": (
                "High-angle shot looking down at the newbie Skyborne Mage girl crouching low on the ground in silent horror, on a 100% pure "
                "solid #FFFFFF white borderless background (no scenery, no floor shading, no gray backdrop, no panel borders, zero text, "
                "zero letters, zero digits, zero speech bubbles, zero UI frames). Squarely centered and filling ~80% of canvas height. "
                "Sensory overload freeze-frame: sapphire eyes blown wide with trembling pinpoint pupils, deep blue gloom shadow across her forehead, "
                "both hands clapped tightly over her pointed elf ears in silent agony, quivering mouth and flying cold sweat drops."
            ),
        },
        {
            "cut_index": 6,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["언데드 성기사", "오크 전사"],
            "speaker": "언데드 성기사",
            "tail_target": "right",
            "dialogue": "어머, 왜 화내세요?\n와우는 만렙부터\n시작이란 말입니다…",
            "wordless": False,
            "visual_prompt": (
                "Dynamic back-view shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). On the left half, the Orc Warrior girl turns her back to the camera, clenching both trembling fists with cartoon steam "
                "shooting from her green hood ears in explosive fury; on the right half, the Undead Paladin looks back over her shoulder with an innocent "
                "clueless deadpan blink, folding her gloved hands politely. Medium 2.5-to-3-head chibi scale, leaving the left 46% pure white."
            ),
        },
    ],
}

# ---------------------------------------------------------------------------
# EP041: 도시괴담 성기사 첨봄 ㅋㅋㅋㅋ
# ---------------------------------------------------------------------------
EPISODES[41] = {
    "episode_number": 41,
    "source_post_no": "73199",
    "source_title": "도시괴담 성기사 첨봄 ㅋㅋㅋㅋ",
    "source_url": "https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=73199&exception_mode=recommend&page=5",
    "subtitle": "줄파락 출발 직전 신성 성기사의 '장트라제 도검 입찰' 선언",
    "item_tooltip": None,
    "cuts": [
        {
            "cut_index": 1,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["오크 전사", "노움 도적"],
            "speaker": "오크 전사",
            "tail_target": "left",
            "dialogue": "줄파락 풀파 완료!\n힐러 신기님도 왔으니\n쾌적하게 출발하자~",
            "wordless": False,
            "visual_prompt": (
                "Over-the-shoulder diagonal shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). Framed over the large foreground shoulder and back of the head of "
                "the Gnome Rogue girl on the lower-right (blonde twin pigtails with pink-blue tips, aviator goggles, daggers sheathed at belt). "
                "In the background on the lower-left, the Orc Warrior Protection tank (green orc onesie hood, sturdy steel kite shield on left arm, "
                "compact 1H steel sword in right hand, zero 2H weapon) grins cheerfully, ready for the dungeon. "
                "Medium 2.5-to-3-head chibi scale in lower two-thirds, leaving generous pure #FFFFFF white headroom across top 38%."
            ),
        },
        {
            "cut_index": 2,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["언데드 성기사"],
            "speaker": "언데드 성기사",
            "tail_target": "right",
            "dialogue": "출발 전에 하나만요.\n저 술트라제 만들 거라\n장트라제 뜨면 굴릴게요.",
            "wordless": False,
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). Positioned cleanly on the right half facing left, the Undead Paladin healer girl "
                "(round white skull cap, silver-white bob hair with icy tips, white-and-gold cloak, hands clean with default weapon omitted) "
                "steps forward raising one gloved finger matter-of-factly with a completely stoic deadpan expression, making her outrageous "
                "sword reservation announcement. Medium 2.5-to-3-head chibi scale filling ~65% of canvas height, leaving left 48% pure white."
            ),
        },
        {
            "cut_index": 3,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["언데드 성기사", "오크 전사"],
            "speaker": "언데드 성기사",
            "tail_target": "left",
            "dialogue": "힐러지만 합체 검\n낭만은 못 참잖아요?\n뜨면 골드 좀 돌릴게요~",
            "wordless": False,
            "item_tooltip": {
                "image_path": None,
                "item_name": "보호의 장트라제",
                "wowhead_item_id": 11086,
                "quality": "rare",
                "slot_left": "주장비",
                "slot_right": "검",
                "lines": [
                    "획득 시 귀속",
                    "고유 아이템",
                    "공격력 44 - 83\t속도 1.90",
                    "(초당 공격력 33.42)",
                    "요구 레벨 45",
                ],
                "equip_effects": [
                    "사용 효과: 장트라제와 상트라제를 결합하여 강력한 검 술트라제를 만듭니다.",
                    "발동 효과: 사용자를 보호막으로 감싸 55 에서 85의 물리 피해를 흡수합니다. 20초 동안 지속됩니다.",
                ],
                "icon_name": "inv_sword_43",
                "preferred_corner": "top_right",
                "target_width": 288,
            },
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the Undead Paladin on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). On the lower-left, the Undead Paladin girl holds a compact ONE-HANDED curved troll sword (보호의 장트라제, "
                "strictly compact 1H chibi scale, NOT a giant greatsword) with a soft blue rare loot glow in one hand and a plump coin pouch in the other, "
                "starry-eyed with dreamy golden sparkles; on the lower-right, the Orc Warrior tank freezes in horror, drooping her 1H sword. "
                "Medium 2.5-to-3-head chibi scale, leaving generous pure #FFFFFF white headroom across top 38% and keeping top-right corner clear."
            ),
        },
        {
            "cut_index": 4,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["노움 도적", "오크 전사"],
            "speaker": "노움 도적",
            "tail_target": "left",
            "dialogue": "잠깐, 골팟도 아닌데\n풀파 되자마자 신기가\n도검 입찰 예고...?",
            "wordless": False,
            "visual_prompt": (
                "Tilted dutch-tilt diagonal composition on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). Positioned on the left half: the Gnome Rogue girl tiptoes in alarm, pointing a trembling finger sideways "
                "toward the Paladin with wide sweat-dropping eyes (daggers at belt); beside her, the Orc Warrior clutches her steel kite shield "
                "tightly to her chest in chilled shock. Medium 2.5-to-3-head chibi scale, leaving the right 48% completely empty pure white space."
            ),
        },
        {
            "cut_index": 5,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["오크 전사"],
            "speaker": None,
            "tail_target": "center",
            "dialogue": None,
            "wordless": True,
            "visual_prompt": (
                "High-angle shot looking down at the Orc Warrior tank girl kneeling on the ground in icy shock, on a 100% pure solid #FFFFFF "
                "white borderless background (no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, "
                "zero digits, zero speech bubbles, zero UI frames). Squarely centered and filling ~80% of canvas height. "
                "Petrified shock freeze-frame: crimson eyes shrunk to tiny pinpoint pupils, deep dark blue gloom shadow across her green orc hood, "
                "jaw frozen open, top rim of her steel kite shield resting on the floor in front of her."
            ),
        },
        {
            "cut_index": 6,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["노움 도적", "언데드 성기사"],
            "speaker": "노움 도적",
            "tail_target": "left",
            "dialogue": "도시괴담 성기사...\n실제로 처음 봤다...\n분위기 싸해진 거 봐...'
            "wordless": False,
            "visual_prompt": (
                "Dynamic back-view shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). Positioned on the left half: the Gnome Rogue girl turns her back partially to the paladin, looking back over her shoulder "
                "with dead-fish deadpan eyes and cold sweat drops; on the right, the Undead Paladin stands peacefully seen in 3/4 angle with dreamy "
                "golden sparkles around her skull hood, oblivious to the silence. Medium 2.5-to-3-head chibi scale, leaving the right 48% pure white."
            ),
        },
    ],
}

# ---------------------------------------------------------------------------
# EP042: 호드 갤길 영포티 전탱 길드추방당함 ㅋㅋ
# ---------------------------------------------------------------------------
EPISODES[42] = {
    "episode_number": 42,
    "source_post_no": "87387",
    "source_title": "호드 갤길 영포티 전탱 길드추방당함 ㅋㅋ",
    "source_url": "https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=87387&exception_mode=recommend&page=4",
    "subtitle": "줄파락 대장 도안 실수 루팅 → '후회하게 해줌' 협박 파탈 → 길드 추방 엔딩",
    "item_tooltip": None,
    "cuts": [
        {
            "cut_index": 1,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["인간 흑마법사", "오크 전사"],
            "speaker": "인간 흑마법사",
            "tail_target": "left",
            "dialogue": "앗, 안투술 대장 도안이\n획귀인지 몰랐어요!\n2시간 거래 되니까 드릴게요!",
            "wordless": False,
            "visual_prompt": (
                "Over-the-shoulder diagonal shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). Framed over the large foreground shoulder and back of the head of "
                "the furious Orc Warrior tank on the lower-right (steel kite shield on left arm, 1H sword at hip). "
                "In the background on the lower-left, the Human Warlock girl (dark purple hood, jet-black twintails, violet eyes, "
                "imp doll sitting on floor) bows frantically with waterfall anime tears, holding out a rolled cream parchment blueprint scroll "
                "with both hands. Medium 2.5-to-3-head chibi scale, leaving generous pure #FFFFFF white headroom across top 38%."
            ),
        },
        {
            "cut_index": 2,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["오크 전사"],
            "speaker": "오크 전사",
            "tail_target": "right",
            "dialogue": "빨리 내놔라.\n안 그러면 진짜\n후회하게 해줌.",
            "wordless": False,
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). Positioned cleanly on the right half facing left, the Orc Warrior tank "
                "(green orc hood, crimson eyes, spiky red pauldrons) stomps forward aggressively, pointing a compact 1H steel sword "
                "forward and slamming her sturdy steel kite shield with a menacing scowl, dark heavy brow shadows, and dark speed lines. "
                "Medium 2.5-to-3-head chibi scale filling ~65% of canvas height, leaving the left 48% empty pure white space."
            ),
        },
        {
            "cut_index": 3,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["인간 흑마법사", "오크 전사"],
            "speaker": "인간 흑마법사",
            "tail_target": "left",
            "dialogue": "드린다는데 말이 좀...\n어, 진짜 파탈해요?!\n30분 기다려서 왔는데!!",
            "wordless": False,
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the rage-quitting tank on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). On the lower-right, the Orc Warrior tank turns away with an arrogant petulant huff, channeling a glowing "
                "cyan-blue Hearthstone vortex pillar that swirls around her boots (steel kite shield and 1H sword strapped to her back); "
                "on the lower-left, the Warlock clutches her blueprint in horrified disbelief! "
                "Medium 2.5-to-3-head chibi scale, leaving generous pure #FFFFFF white headroom across top 38%."
            ),
        },
        {
            "cut_index": 4,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["트롤 주술사", "오크 전사"],
            "speaker": "트롤 주술사",
            "tail_target": "left",
            "dialogue": "외부인도 모셔놓고 뭐냐!\n당장 돌아와서 진행해!\n...아니 거기서 접종을?!",
            "wordless": False,
            "visual_prompt": (
                "Tilted dutch-tilt diagonal angle on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). On the left half, the Troll Shaman Guild Master leaps forward shouting with crackling blue lightning sparks "
                "flying from her red mohawk hood; on the right half, the Orc Warrior tank fades into a semi-transparent logout poof with crossed arms "
                "and eyes squeezed shut. Medium 2.5-to-3-head chibi scale, leaving the right 48% empty pure white space."
            ),
        },
        {
            "cut_index": 5,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["트롤 주술사"],
            "speaker": None,
            "tail_target": "center",
            "dialogue": None,
            "wordless": True,
            "visual_prompt": (
                "High-angle shot looking down at the Troll Shaman girl trembling in speechless fury, on a 100% pure solid #FFFFFF white borderless "
                "background (no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles). "
                "Squarely centered and filling ~80% of canvas height. Pure speechless rage freeze-frame: wide blazing green eyes with tiny pinpoint pupils, "
                "huge throbbing cartoon anger vein on her sky-blue troll hood, dark gloom shadow across her forehead, clenched jaw and crackling blue sparks."
            ),
        },
        {
            "cut_index": 6,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["나이트엘프 사제", "트롤 주술사"],
            "speaker": "나이트엘프 사제",
            "tail_target": "left",
            "dialogue": "길마님이 전탱 추방하고\n겜할 맛 안 난다며\n같이 접종하셨네요...",
            "wordless": False,
            "visual_prompt": (
                "Dynamic back-view shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). On the right half, the Troll Shaman Guild Master is seen from behind, walking away into a semi-transparent "
                "logout smoke puff, waving one limp hand over her shoulder; on the left half, the Night Elf Priest girl slumps with drooping shoulders "
                "and dead-fish eyes, sighing deeply at the ruined party. Medium 2.5-to-3-head chibi scale, leaving the right 48% pure white."
            ),
        },
    ],
}

# ---------------------------------------------------------------------------
# EP043: 오늘자 새로생긴 룰 잡템은 탱차비라함
# ---------------------------------------------------------------------------
EPISODES[43] = {
    "episode_number": 43,
    "source_post_no": "91005",
    "source_title": "오늘자 새로생긴 룰 잡템은 탱차비라함",
    "source_url": "https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=91005&exception_mode=recommend&page=4",
    "subtitle": "녹템 잡템에 차비 눌렀더니 '잡템은 탱차비' 신종 룰 & 칼추방",
    "item_tooltip": None,
    "cuts": [
        {
            "cut_index": 1,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["타우렌 드루이드", "오크 전사"],
            "speaker": "타우렌 드루이드",
            "tail_target": "left",
            "dialogue": "오~ 녹템 잡템 떴네!\n다들 안 쓰니까\n평범하게 차비 눌러야지~",
            "wordless": False,
            "visual_prompt": (
                "Over-the-shoulder diagonal shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). Framed over the large foreground shoulder and back of the head of "
                "the Orc Warrior tank on the lower-right (green hood, silver pauldrons, steel kite shield on left arm). "
                "In the background on the lower-left, the Tauren Druid girl (fluffy plush cow hood, ivory horns, golden nose ring, staff on back) "
                "cheerfully tosses a glossy loot cube die with black dot pips only (zero digits) beside a small glowing green uncommon leather bracer. "
                "Medium 2.5-to-3-head chibi scale, leaving generous pure #FFFFFF white headroom across top 38%."
            ),
        },
        {
            "cut_index": 2,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["오크 전사", "노움 도적"],
            "speaker": "오크 전사",
            "tail_target": "right",
            "dialogue": "잠깐만요 회드님!!\n잡템은 원래 탱차비인데\n왜 차비를 눌러요?!",
            "wordless": False,
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). Positioned on the right half facing left, the Orc Warrior tank lunges forward "
                "pointing an accusing finger while bracing her steel kite shield on her left arm (1H sword sheathed at hip), shouting indignantly "
                "with a pulsing anger vein; beside her, the Gnome Rogue nods smugly with crossed arms. "
                "Medium 2.5-to-3-head chibi scale filling ~65% of canvas height, leaving the left 48% empty pure white space."
            ),
        },
        {
            "cut_index": 3,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["타우렌 드루이드", "노움 도적"],
            "speaker": "타우렌 드루이드",
            "tail_target": "left",
            "dialogue": "네?! 녹템 잡템까지\n탱차비 룰이 어딨어요?\n힐러도 수리비 나오는데...",
            "wordless": False,
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the protesting Druid on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). On the lower-left, the Tauren Druid girl holds both hands out in indignant protest with puffed sulky cheeks "
                "and watery brown eyes (staff on back); on the lower-right, the Gnome Rogue girl wags one finger smugly with a cheeky know-it-all smirk "
                "and daggers sheathed at belt. Medium 2.5-to-3-head chibi scale, leaving generous pure #FFFFFF white headroom across top 38%."
            ),
        },
        {
            "cut_index": 4,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["타우렌 드루이드"],
            "speaker": "타우렌 드루이드",
            "tail_target": "left",
            "dialogue": "그런 억지 룰이면\n저 그냥 나갈게요!\n힐러는 귀하다고요!",
            "wordless": False,
            "visual_prompt": (
                "Dynamic back-view shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). Positioned on the left half: the Tauren Druid girl is seen from behind, turning her back with hands firmly on her hips "
                "and ears perked up, walking away proudly with her wooden staff stowed on her back, looking back over her shoulder with an offended pout. "
                "Medium 2.5-to-3-head chibi scale filling ~65% of canvas height, leaving the right 48% empty pure white space."
            ),
        },
        {
            "cut_index": 5,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["타우렌 드루이드"],
            "speaker": None,
            "tail_target": "center",
            "dialogue": None,
            "wordless": True,
            "visual_prompt": (
                "High-angle shot looking down at the Tauren Druid girl caught in mid-stride, on a 100% pure solid #FFFFFF white borderless "
                "background (no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles). "
                "Squarely centered and filling ~80% of canvas height. Party-kick shock freeze-frame: big watery brown eyes wide with tiny trembling "
                "pinpoint pupils, golden nose ring glinting, mouth frozen open in disbelief as swirling cyan dungeon-kick teleport sparkles suddenly "
                "rise around her shoulders, dark gloom shadow across her cow hood."
            ),
        },
        {
            "cut_index": 6,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["노움 도적", "오크 전사"],
            "speaker": "노움 도적",
            "tail_target": "left",
            "dialogue": "어, 나가기 전에\n칼추방 성공!\n...근데 힐러 언제 구하냐?",
            "wordless": False,
            "visual_prompt": (
                "Tilted dutch-tilt diagonal composition on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). On the left half, the Gnome Rogue girl brushes her hands together with a smug smirk that abruptly freezes into "
                "a nervous sweat drop (daggers at belt); beside her, the Orc Warrior tank scratches her green hood with a giant cartoon sweat drop, "
                "staring blankly at the empty white space where the healer vanished. Medium 2.5-to-3-head chibi scale, leaving right 48% pure white."
            ),
        },
    ],
}

# ---------------------------------------------------------------------------
# EP044: 속보) 탱커 인던 데뷔전 완료ㅠㅠㅠㅠㅠㅠㅠ
# ---------------------------------------------------------------------------
EPISODES[44] = {
    "episode_number": 44,
    "source_post_no": "69245",
    "source_title": "속보) 탱커 인던 데뷔전 완료ㅠㅠㅠㅠㅠㅠㅠ",
    "source_url": "https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=69245&exception_mode=recommend&page=4",
    "subtitle": "해골 찍고 골렘 양변 요청 → '안 된대요!!' 대패닉 → 도적 혼절 구원 데뷔전",
    "item_tooltip": None,
    "cuts": [
        {
            "cut_index": 1,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["오크 전사", "스카이본 마법사"],
            "speaker": "오크 전사",
            "tail_target": "left",
            "dialogue": "생애 첫 탱커 데뷔전!\n해골 찍은 거 점사하고\n옆 골렘은 양변해 주세요!",
            "wordless": False,
            "visual_prompt": (
                "Over-the-shoulder diagonal shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). Framed over the large foreground shoulder and back of the head of "
                "the Skyborne Mage girl on the lower-right (blonde hair with aqua tips, feather charm, sailor collar). "
                "In the background on the lower-left, the newbie Orc Warrior tank holds a sturdy steel kite shield on her left arm "
                "and points a compact 1H steel sword forward with a small floating cartoon skull mark above it, determined sparkling crimson eyes. "
                "Medium 2.5-to-3-head chibi scale, leaving generous pure #FFFFFF white headroom across top 38%."
            ),
        },
        {
            "cut_index": 2,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["스카이본 마법사"],
            "speaker": "스카이본 마법사",
            "tail_target": "right",
            "dialogue": "양변 있어요! 시전 중...\n어?! 골렘은 양변이\n안 된대요!! 비상!!",
            "wordless": False,
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). Positioned on the right half facing left, the Skyborne Mage girl dashes back "
                "in adorable panic as a blue arcane fizzle turns into a harmless fluffy white sheep-shaped puff of smoke, waving both hands "
                "with swirling spiral sapphire eyes and flying sweat drops (bread and flask put away). "
                "Medium 2.5-to-3-head chibi scale filling ~65% of canvas height, leaving the left 48% empty pure white space."
            ),
        },
        {
            "cut_index": 3,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["오크 전사", "스카이본 마법사"],
            "speaker": "오크 전사",
            "tail_target": "left",
            "dialogue": "에엑?! 면역이에요?!\n골렘 두 마리 다 오면\n나 데뷔전 전멸인데!!",
            "wordless": False,
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the panic on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). On the lower-left, the newbie Orc Warrior girl ducks frantically behind her raised steel kite shield, trembling "
                "wildly with streaming waterfall anime tears and clutched 1H steel sword; on the lower-right, the Mage flails both hands in matching panic! "
                "Medium 2.5-to-3-head chibi scale, leaving generous pure #FFFFFF white headroom across top 38%."
            ),
        },
        {
            "cut_index": 4,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["오크 전사"],
            "speaker": None,
            "tail_target": "center",
            "dialogue": None,
            "wordless": True,
            "visual_prompt": (
                "High-angle shot looking down at the Orc Warrior girl crouching low on the ground, on a 100% pure solid #FFFFFF white borderless "
                "background (no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles). "
                "Squarely centered and filling ~80% of canvas height. Terror peek freeze-frame: peeking just her green plush orc hood and wide trembling "
                "pinpoint crimson eyes over the top rim of her sturdy steel kite shield clutched up to her nose, waterfall of cold sweat drops, "
                "heavy blue gloom shadow across her forehead."
            ),
        },
        {
            "cut_index": 5,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["노움 도적", "오크 전사"],
            "speaker": "노움 도적",
            "tail_target": "left",
            "dialogue": "걱정 마요 새싹 탱커님!\n은신으로 몰래 들어가서\n25초 혼절 걸고 올게요!",
            "wordless": False,
            "visual_prompt": (
                "Tilted dutch-tilt diagonal angle on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). On the lower-left, the Gnome Rogue girl steps out of a swirling stealth vanish smoke puff, flashing a cool wink "
                "and a thumbs-up (daggers at belt), dashing forward to cast Sap; on the lower-right, the Orc Warrior peeks from behind her shield with starry hopeful eyes! "
                "Medium 2.5-to-3-head chibi scale, leaving generous pure #FFFFFF white headroom across top 38%."
            ),
        },
        {
            "cut_index": 6,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["오크 전사", "스카이본 마법사"],
            "speaker": "오크 전사",
            "tail_target": "left",
            "dialogue": "막넴까지 깼다!!\n진짜 개무서웠어ㅠㅠ\n근데 리딩 개재밌네!",
            "wordless": False,
            "visual_prompt": (
                "Dynamic back-view shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). Positioned on the left half: the Orc Warrior girl leaps high into the air, seen partially from behind swinging "
                "her steel kite shield and 1H sword up in tearful joyful triumph, looking back over her shoulder with a radiant smile; beside her, "
                "the Skyborne Mage claps happily with sparkles. Medium 2.5-to-3-head chibi scale, leaving the right 48% pure white."
            ),
        },
    ],
}

# ---------------------------------------------------------------------------
# EP045: 다짜고짜 '마나약' 달라는 냥꾼은 어떻게 해야함?
# ---------------------------------------------------------------------------
EPISODES[45] = {
    "episode_number": 45,
    "source_post_no": "92646",
    "source_title": "다짜고짜 '마나약' 달라는 냥꾼은 어떻게 해야함?",
    "source_url": "https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=92646&exception_mode=recommend&page=3",
    "subtitle": "'마나약' 달라는 냥꾼 → 아이언포지 저격 → '얼라라고 안 했는데?' 2단 자폭",
    "item_tooltip": None,
    "cuts": [
        {
            "cut_index": 1,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["드워프 사냥꾼", "스카이본 마법사"],
            "speaker": "스카이본 마법사",
            "tail_target": "right",
            "dialogue": "냥꾼님이 마나약 달래서\n포션 없다고 했더니\n아이언포지 공개창에 욕하네...",
            "wordless": False,
            "visual_prompt": (
                "Over-the-shoulder diagonal shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). Framed over the large foreground shoulder and back of the head of "
                "the confused Skyborne Mage girl holding a corked blue glass mana-water flask in one hand and bread bun in the other. "
                "In the background on the lower-left, the Dwarf Hunter girl stomps away angrily, cupping both hands to shout into the distance "
                "with angry comic shout lines (blunderbuss slung on back). Medium 2.5-to-3-head chibi scale, leaving generous pure #FFFFFF headroom across top 38%."
            ),
        },
        {
            "cut_index": 2,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["노움 도적", "스카이본 마법사"],
            "speaker": "노움 도적",
            "tail_target": "left",
            "dialogue": "물빵을 마나약이라니...\n그게 얼라 평균이니까\n그냥 받아들이세요~",
            "wordless": False,
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). Positioned on the left half facing right, the Gnome Rogue girl shrugs with a cheeky "
                "smug sneer and palms upturned (daggers sheathed at belt), teasing the Mage who stands with puffed cheeks and hands on hips "
                "(flask and bread put away). Medium 2.5-to-3-head chibi scale filling ~65% of canvas height, leaving the right 48% empty pure white space."
            ),
        },
        {
            "cut_index": 3,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["스카이본 마법사", "노움 도적"],
            "speaker": "스카이본 마법사",
            "tail_target": "left",
            "dialogue": "잠깐만요!\n저 얼라라고 말한 적\n한 번도 없는데?!",
            "wordless": False,
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the Skyborne Mage girl on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). On the lower-left, the Mage leans forward pointing one triumphant righteous finger in fierce rebuttal with sparkling "
                "sapphire eyes (bread and flask put away); on the lower-right, the Gnome Rogue stares back with flat unimpressed deadpan eyes and crossed arms. "
                "Medium 2.5-to-3-head chibi scale, leaving generous pure #FFFFFF white headroom across top 38%."
            ),
        },
        {
            "cut_index": 4,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["노움 도적"],
            "speaker": "노움 도적",
            "tail_target": "right",
            "dialogue": "방금 본인 입으로\n'아이언포지 공개창'\n이라고 하셨잖아요.",
            "wordless": False,
            "visual_prompt": (
                "Dynamic back-view shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). Positioned on the right half: the Gnome Rogue girl is seen from behind, walking slowly toward the left, "
                "turning her back and looking back over her shoulder to point a calm finger at the Mage saying her rebuttal, daggers sheathed at belt. "
                "Medium 2.5-to-3-head chibi scale filling ~65% of canvas height, leaving the left 48% pure white."
            ),
        },
        {
            "cut_index": 5,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["스카이본 마법사"],
            "speaker": None,
            "tail_target": "center",
            "dialogue": None,
            "wordless": True,
            "visual_prompt": (
                "High-angle shot looking down at the Skyborne Mage girl kneeling on the ground in total intellectual collapse, on a 100% pure "
                "solid #FFFFFF white borderless background (no scenery, no floor shading, no gray backdrop, no panel borders, zero text, "
                "zero letters, zero digits, zero speech bubbles, zero UI frames). Squarely centered and filling ~80% of canvas height. "
                "Brain-crash freeze-frame: sapphire eyes blown wide with trembling pinpoint pupils, jaw dropped, giant cartoon sweat drop sliding down "
                "her temple, heavy dark gloom shadow across her forehead, sky-blue hair tips drooping limply."
            ),
        },
        {
            "cut_index": 6,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["스카이본 마법사", "노움 도적"],
            "speaker": "스카이본 마법사",
            "tail_target": "left",
            "dialogue": "어... 맞네.\n...냥꾼님이 물빵 달란\n거였구나... 무개념 맞네...",
            "wordless": False,
            "visual_prompt": (
                "Tilted dutch-tilt diagonal composition on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). Positioned on the left half: the Skyborne Mage girl slumps collapsed on the white floor cradling her blue glass flask "
                "in sheer humiliation with dizzy spiral eyes and blushing cheeks; beside her, the Gnome Rogue girl pats her shoulder with a teasing smirk. "
                "Medium 2.5-to-3-head chibi scale, leaving the right 48% empty pure white space."
            ),
        },
    ],
}

# ---------------------------------------------------------------------------
# EP046: 유입 필독) 흑마 고르면 겪을 일들jpg
# ---------------------------------------------------------------------------
EPISODES[46] = {
    "episode_number": 46,
    "source_post_no": "6229",
    "source_title": "유입 필독) 흑마 고르면 겪을 일들jpg",
    "source_url": "https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=6229&exception_mode=recommend&page=13",
    "subtitle": "3시간 조각 파밍 → 소환·생명석 수발 → 정작 딜 체급은 평균 B티어 비애",
    "item_tooltip": None,
    "cuts": [
        {
            "cut_index": 1,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["인간 흑마법사"],
            "speaker": "인간 흑마법사",
            "tail_target": "center",
            "dialogue": "레이드 3시간 전...\n가방 싹 비우고 혼자\n영혼의 조각 풀파밍 중...",
            "wordless": False,
            "visual_prompt": (
                "High-angle shot looking down at the exhausted Human Warlock girl on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). In the lower-center, the Warlock girl (dark purple hood, jet-black twintails, violet eyes) crouches on the floor, "
                "stuffing glowing violet crystal soul shards into a bulging brown leather backpack with tired droopy violet eyes and streaming sweat drops "
                "(grumpy red plush imp doll sitting on the floor beside her). Medium 2.5-to-3-head chibi scale, leaving generous pure #FFFFFF headroom across top 38%."
            ),
        },
        {
            "cut_index": 2,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["오크 전사", "스카이본 마법사"],
            "speaker": "오크 전사",
            "tail_target": "right",
            "dialogue": "마을 수다 재밌었다~\n이제 레이드 가볼까?\n흑마님! 나 소환 좀~",
            "wordless": False,
            "visual_prompt": (
                "Side-profile 90-degree action shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, "
                "zero speech bubbles, zero UI frames). Positioned on the right half facing left, the Orc Warrior girl lounges back "
                "raising a rustic wooden tavern mug with a carefree grin (chunky silver battle axe strapped on back), while the Skyborne Mage "
                "relaxes happily nibbling a warm round conjured bread bun, yelling across the frame for a summon. "
                "Medium 2.5-to-3-head chibi scale filling ~65% of canvas height, leaving the left 48% empty pure white space."
            ),
        },
        {
            "cut_index": 3,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["인간 흑마법사", "스카이본 마법사"],
            "speaker": "스카이본 마법사",
            "tail_target": "right",
            "dialogue": "소환 감사해요 흑마님!\n아, 생명석 사탕도\n하나만 거래해 주세요~",
            "wordless": False,
            "visual_prompt": (
                "Dramatic low-angle shot looking up at the portal on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). On the lower-left, the sweaty exhausted Human Warlock channels a swirling violet-purple summoning vortex rift "
                "with one hand and extends an emerald-green crystal healthstone in the other (imp doll on floor); on the lower-right, the Mage "
                "steps cheerfully out of the glowing portal with an outstretched hand! Medium 2.5-to-3-head chibi scale, top 38% pure white."
            ),
        },
        {
            "cut_index": 4,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["오크 전사", "인간 흑마법사"],
            "speaker": "오크 전사",
            "tail_target": "left",
            "dialogue": "수발 다 끝났지?\n자, 이제 레이드 시작!\n근데 흑마 딜 체급은... B티어?",
            "wordless": False,
            "visual_prompt": (
                "Tilted dutch-tilt diagonal angle on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). Positioned on the left half: the Orc Warrior girl leans casually on her battle axe with a cheeky teasing smirk, "
                "tapping her chin and dropping the B-tier DPS remark; beside her, the Human Warlock freezes in utter horror, dropping her empty "
                "soul shard pouch. Medium 2.5-to-3-head chibi scale filling ~65% of canvas height, leaving the right 48% pure white."
            ),
        },
        {
            "cut_index": 5,
            "aspect_ratio": "4:3",
            "layout_slot": "top",
            "characters": ["인간 흑마법사"],
            "speaker": None,
            "tail_target": "center",
            "dialogue": None,
            "wordless": True,
            "visual_prompt": (
                "High-angle shot looking down at the Human Warlock girl kneeling on the ground, completely drained of life, on a 100% pure "
                "solid #FFFFFF white borderless background (no scenery, no floor shading, no gray backdrop, no panel borders, zero text, "
                "zero letters, zero digits, zero speech bubbles, zero UI frames). Squarely centered and filling ~80% of canvas height. "
                "Soul-leaving freeze-frame: blank white soulless eyes, slack parted mouth with a tiny pale cartoon soul puff floating upward, "
                "dark purple hood drooping, heavy vertical gloom lines."
            ),
        },
        {
            "cut_index": 6,
            "aspect_ratio": "16:9",
            "layout_slot": "bottom",
            "characters": ["인간 흑마법사", "오크 전사"],
            "speaker": "인간 흑마법사",
            "tail_target": "left",
            "dialogue": "3시간 조각 캐고\n소환·사탕 다 바쳤는데...\n흑마는 대체 누가 하냐...",
            "wordless": False,
            "visual_prompt": (
                "Dynamic back-view shot on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero letters, zero digits, zero speech bubbles, "
                "zero UI frames). Positioned on the left half: the Human Warlock girl turns her back to the world, walking away slumped and hunched over, "
                "hugging her grumpy red plush imp doll tightly against her chest with gloomy dark comic swirls, looking back over her shoulder with "
                "empty dead-fish eyes; on the right, the Orc Warrior pats her back awkwardly with a sheepish sweat drop. Medium 2.5-to-3-head chibi scale, right 48% pure white."
            ),
        },
    ],
}


def main():
    print(f"Loaded {len(EPISODES)} episodes to upgrade.")
    all_passed = True

    for ep_num in sorted(EPISODES.keys()):
        data = EPISODES[ep_num]
        ep_id = f"ep{ep_num:03d}"
        script = EpisodeScript.model_validate(data)

        # Audit quality with strict_cinematic=True
        audit = audit_script_quality(script, strict_cinematic=True)
        passed = audit["passed"]
        errors = audit["errors"]
        warnings = audit["warnings"]
        metrics = audit.get("cinematic_metrics", {})

        print(f"[{ep_id}] passed={passed}, errs={len(errors)}, warns={len(warnings)}, metrics={metrics}")
        if not passed or errors or warnings:
            all_passed = False
            for e in errors:
                print(f"  ERR: {e}")
            for w in warnings:
                print(f"  WARN: {w}")

    if not all_passed:
        print("\nFix errors above before saving!")
        return

    print("\nAll 12 episodes passed strict audit! Saving scripts and raw prompt packs...")

    for ep_num in sorted(EPISODES.keys()):
        data = EPISODES[ep_num]
        ep_id = f"ep{ep_num:03d}"
        script = EpisodeScript.model_validate(data)

        # 1. Save data/episodes/<ep>/script.json
        ep_dir = Path(f"data/episodes/{ep_id}")
        ep_dir.mkdir(parents=True, exist_ok=True)
        script_path = ep_dir / "script.json"
        script_path.write_text(json.dumps(script.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")

        # 2. Regenerate data/raw_cuts/<ep>/prompts.json
        raw_dir = Path(f"data/raw_cuts/{ep_id}")
        raw_dir.mkdir(parents=True, exist_ok=True)
        prompt_list = []
        for cut in script.cuts:
            target_path = raw_dir / f"cut_{cut.cut_index:02d}.png"
            prompt_text = build_cut_image_prompt(cut)
            prompt_list.append({
                "cut_index": cut.cut_index,
                "aspect_ratio": cut.aspect_ratio,
                "target_path": str(target_path.resolve()),
                "prompt": prompt_text,
            })
        (raw_dir / "prompts.json").write_text(json.dumps(prompt_list, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  Saved {script_path} and {raw_dir / 'prompts.json'}")

    print("\nSuccessfully updated all 12 episodes and regenerated prompts.json!")


if __name__ == "__main__":
    main()
