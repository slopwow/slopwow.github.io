# -*- coding: utf-8 -*-
"""Director-3: Upgrade ep035 through ep046 with cinematic angles, rich motions, and varied expressions."""

import json
from pathlib import Path
from wow_sloptoon.models import EpisodeScript, ComicCut, ItemTooltipSpec
from wow_sloptoon.artist import build_cut_image_prompt
from wow_sloptoon.writer import audit_script_quality

EPISODES_DATA = {}

# ---------------------------------------------------------------------------
# EP035: 성기사 이새끼들은 뉴비까지 등쳐먹으려드네ㅋㅋㅋ
# ---------------------------------------------------------------------------
EPISODES_DATA[35] = {
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
                "the Undead Paladin girl on the lower-right (round white skull cap, silver-white bob hair with icy tips, "
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

print("EP035 loaded.")
