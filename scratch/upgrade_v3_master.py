import json
from pathlib import Path
from wow_sloptoon.models import EpisodeScript, ComicCut
from wow_sloptoon.writer import audit_script_quality
from wow_sloptoon.artist import build_cut_image_prompt


def get_ep023(old):
    cuts = [
        ComicCut(
            cut_index=1,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="스카이본 마법사",
            dialogue="탱님! 수도원\n처음이에요!\n먼저 날아가볼게요~",
            tail_target="left",
            characters=["스카이본 마법사", "오크 전사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic action motion shot. On the lower-left, the newbie Skyborne Mage girl (bottom-row #4: pointed elf ears, long golden-blonde "
                "hair fading to aqua tips, sailor collar with teal ribbon) dashes eagerly ahead down a stone corridor with flying comic dust puffs, "
                "holding her wooden staff outward with wide sparkling sapphire eyes and an innocent beaming smile. On the lower-right, the Orc Warrior "
                "girl (top-row #1: green plush orc hood, high ponytail, silver plate armor, carrying a sturdy steel shield on her arm and one-handed "
                "axe at her belt) reaches an armored hand forward in sudden alarm. Generous pure #FFFFFF white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=2,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="나이트엘프 사제",
            dialogue="마법사님 뒤!!\n순찰대 한 무리가\n통째로 따라와요!!",
            tail_target="left",
            characters=["나이트엘프 사제", "스카이본 마법사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic side-profile 90-degree action shot arranged across the lower frame. On the right, the Skyborne Mage girl sprints frantically "
                "to the left with wide panicked spiral eyes and waterfall cartoon tears streaming, robes fluttering as a whole crowd of dark cartoon "
                "Scarlet Crusade patrol mob silhouettes with glowing red eyes, red tabards, and raised swords chase closely behind her. On the lower-left, "
                "the Night Elf Priest girl (top-row #2: lavender hair, white clergy vestments) points in utter terror with mouth wide open screaming. "
                "Generous pure #FFFFFF white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=3,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="오크 전사",
            dialogue="도전의 외침!\n어그로 다 내 거임.\n님은 뒤로 빠지셈.",
            tail_target="left",
            characters=["오크 전사", "스카이본 마법사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dramatic low-angle shot looking up at the heroic protection tank. On the lower-left, the Orc Warrior girl (green plush orc hood, "
                "black high ponytail, crimson eyes blazing with heroic fury, spiky red pauldrons) charges forward lunging into battle, firmly planting "
                "her sturdy heavy steel tower shield in her left hand and brandishing a one-handed silver battle axe in her right hand, roaring "
                "Challenging Shout with dynamic red battle cry shockwaves pulling the swarming mob silhouettes toward herself. On the lower-right in "
                "the background, the Skyborne Mage crouches low in relief. Generous pure #FFFFFF white headroom across top 35%."
            )
        ),
        ComicCut(
            cut_index=4,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="나이트엘프 사제",
            dialogue="마나 바닥…!!\n전사님 혼자 다\n맞고 누우셨어요!",
            tail_target="right",
            characters=["오크 전사", "나이트엘프 사제"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "High-angle shot looking down at the comedic aftermath. On the lower-left, the Orc Warrior girl is comically collapsed faceplant "
                "on the ground in total exhaustion with spinning spiral stars above her green hood, having tanked every single mob strike; her sturdy "
                "steel shield and one-handed axe rest safely beside her. On the lower-right, the Night Elf Priest girl kneels desperately holding an "
                "empty overturned fantasy glass mana potion flask with blue mana sparks empty, clutching her head in tears. Generous pure white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=5,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker=None,
            dialogue=None,
            tail_target="center",
            characters=["스카이본 마법사"],
            wordless=True,
            visual_prompt=(
                "Solo cute anime chibi girl from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dutch-tilt dramatic comedic chest-up close-up freeze-frame of the Skyborne Mage girl (bottom-row #4: pointed elf ears, "
                "long golden-blonde hair with aqua tips, sailor-collar robe). Her huge sapphire-blue eyes are glittering with enormous golden "
                "stars and deep emotional awe, cheeks intensely flushed pink, both hands clasped reverently to her chest in absolute "
                "hero-worship veneration, completely captivated and forever won over by the tank's sacrifice."
            )
        ),
        ComicCut(
            cut_index=6,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="오크 전사",
            dialogue="님 살았으면\n됐음ㅇㅇ",
            tail_target="left",
            characters=["오크 전사", "스카이본 마법사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic back-view shot arranged cleanly in the lower frame. On the lower-left, the Orc Warrior girl is depicted as a "
                "translucent glowing cyan spirit ghost floating slightly above the floor, seen from behind walking away with her high ponytail "
                "swaying, casually tossing a nonchalant thumbs-up back over her shoulder with an unbothered smirk. On the lower-right, "
                "the Skyborne Mage kneels gazing up at the floating ghost in eternal gratitude. Generous pure #FFFFFF white headroom across the top 35%."
            )
        )
    ]
    return EpisodeScript(
        episode_number=old["episode_number"],
        source_post_no=old["source_post_no"],
        source_title=old["source_title"],
        source_url=old["source_url"],
        subtitle=old["subtitle"],
        cuts=cuts
    )


def get_ep024(old):
    cuts = [
        ComicCut(
            cut_index=1,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="노움 도적",
            dialogue="법사님~ 물빵\n좀 주세요오~\n거래 걸게요!",
            tail_target="left",
            characters=["노움 도적", "스카이본 마법사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Over-the-shoulder (OTS) diagonal shot. In the foreground right, the large back and shoulder of the Skyborne Mage girl "
                "(golden hair fading to aqua tips, sailor collar) frames the scene. In the background left, the petite Gnome Rogue girl "
                "(top-row #3: blonde pigtails with pink/blue tips, steampunk aviator goggles, cross hairpins, black cloak, daggers sheathed at waist) "
                "tiptoes forward with a cheeky wheedling smile, rubbing her gloved hands together eagerly demanding water and bread. "
                "Generous pure #FFFFFF white headroom across top 35%."
            )
        ),
        ComicCut(
            cut_index=2,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="스카이본 마법사",
            dialogue="그럼요~ 방금 만든\n최고급 결정수\n20개 드릴게요!",
            tail_target="right",
            characters=["스카이본 마법사"],
            wordless=False,
            item_tooltip=old["cuts"][1].get("item_tooltip"),
            visual_prompt=(
                "Solo cute anime chibi girl from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic action motion shot positioned cleanly on the right half of the wide 16:9 canvas (leaving left 48% pure white for tooltip). "
                "The Skyborne Mage girl (bottom-row #4: pointed elf ears, aqua-tipped blonde hair, sapphire eyes) cheerfully conjures water, "
                "proudly presenting two ornate fantasy corked glass flasks filled with sparkling azure-blue Created Crystal Water radiating "
                "cyan arcane magic circles and glowing sparkles, beaming with a bright hospitable smile. Generous pure white headroom across top 35%."
            )
        ),
        ComicCut(
            cut_index=3,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="노움 도적",
            dialogue="아니 이거 말고\n레벨 높은 거요ㅡㅡ",
            tail_target="left",
            characters=["노움 도적", "스카이본 마법사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dutch-tilt dynamic angle comic cut. On the lower-left, the Gnome Rogue girl arrogantly pushes away the glowing blue crystal water flask "
                "with the back of her hand, puffing her sulky cheeks with narrowed condescending side-eye disgust and an entitled frown. "
                "On the lower-right, the Skyborne Mage recoils in sheer disbelief, her cheerful smile instantly freezing with a massive question mark "
                "and cold sweat drops forming on her temple. Generous pure #FFFFFF white headroom across the top 35%."
            )
        ),
        ComicCut(
            cut_index=4,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker=None,
            dialogue=None,
            tail_target="center",
            characters=["스카이본 마법사"],
            wordless=True,
            visual_prompt=(
                "Solo cute anime chibi girl from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dramatic low-angle shot looking up at the snapping Mage. Centered waist-up freeze-frame of the Skyborne Mage girl: "
                "a heavy sinister dark-purple shadow cast over her forehead and eyes, her sapphire eyes turned into glowing blank white circles of "
                "unfathomable rage, twitching eyelid, holding a wooden Duel Banner flag in one hand ready to slam it down, surrounded by eerie "
                "crackling arcane sparks."
            )
        ),
        ComicCut(
            cut_index=5,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="스카이본 마법사",
            dialogue="결투 신청\n보냈어요.\n수락하세요.",
            tail_target="left",
            characters=["스카이본 마법사", "노움 도적"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic side-profile 90-degree action shot. On the lower-left, the Skyborne Mage girl slams a chunky wooden and brass Duel Banner "
                "violently into the ground with dynamic comic speed lines, flying rock dust puffs, and a chillingly polite dead-eyed smile, "
                "pointing her glowing wooden wand directly at the Rogue. On the lower-right, the Gnome Rogue stumbles backward in sudden shock, "
                "goggles rattling and jaw dropping in panic. Generous pure #FFFFFF white headroom across the top 35%."
            )
        ),
        ComicCut(
            cut_index=6,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="나이트엘프 사제",
            dialogue="도적님… 그거\n55레벨 최고급\n물이었어요…",
            tail_target="right",
            characters=["노움 도적", "나이트엘프 사제"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "High-angle shot looking down at the comedic aftermath. On the lower-left, the Gnome Rogue has been polymorphed into a fluffy white "
                "sheep with spiraling dizzy eyes and steampunk goggles drooping over its woolly head, bleating helplessly in a small patch of grass. "
                "On the lower-right, the Night Elf Priest girl (top-row #2: lavender hair, white clergy robe) kneels beside the sheep facepalming with "
                "an exhausted sigh and sweat drops. Generous pure #FFFFFF white headroom across the top 35%."
            )
        )
    ]
    return EpisodeScript(
        episode_number=old["episode_number"],
        source_post_no=old["source_post_no"],
        source_title=old["source_title"],
        source_url=old["source_url"],
        subtitle=old["subtitle"],
        cuts=cuts
    )


def get_ep025(old):
    cuts = [
        ComicCut(
            cut_index=1,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="언데드 성기사",
            dialogue="마법사님 딜 꼴찌.\n길드창에\n박제했음ㅋ",
            tail_target="left",
            characters=["언데드 성기사", "스카이본 마법사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Over-the-shoulder (OTS) diagonal shot recreating the original post screenshot. In the foreground right, the large shoulder and "
                "aqua-tipped hair of the Skyborne Mage frames the view. In the background left, the Undead Paladin girl (top-row #2: pale lilac skin, "
                "stitched skull hood, silver armor, yellow eyes) leans forward with a smug sneer, triumphantly holding up an unrolled damage meter "
                "parchment displaying a large glowing timer icon reading 32 minutes of unreset combat data, snickering maliciously. Generous pure white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=2,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="스카이본 마법사",
            dialogue="앗 죄송해요ㅠㅠ\n더 열심히\n칠게요…",
            tail_target="left",
            characters=["스카이본 마법사"],
            wordless=False,
            visual_prompt=(
                "Solo cute anime chibi girl from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "High-angle shot looking down at the dejected Mage. Positioned cleanly on the left half of the wide 16:9 canvas, the Skyborne Mage "
                "girl is collapsed and kneeling on the floor in utter remorse, clutching her wooden wand to her chest with huge anime waterfall "
                "tears gushing from her trembling sapphire eyes, weeping apologetically with flushed red cheeks. Generous pure white space on the right."
            )
        ),
        ComicCut(
            cut_index=3,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="트롤 주술사",
            dialogue="잠깐, 전투 시간\n47분…?\n초기화 안 했죠?",
            tail_target="left",
            characters=["트롤 주술사", "언데드 성기사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dutch-tilt dynamic angle shot recreating the screenshot call-out. On the lower-left, the Troll Shaman girl (middle-row #1: blue skin, "
                "voodoo mask, wild pink hair) lunges forward snatching the edge of the meter parchment, pointing an accusatory clawed finger directly "
                "at the unreset 32-minute combat timer with sharp narrowed orange eyes and a wicked grin. On the lower-right, the Undead Paladin recoils "
                "with sudden nervous sweat drops. Generous pure #FFFFFF white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=4,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="트롤 주술사",
            dialogue="필드 딜 합산ㅋ\n이번 넴만 보면\n법사님이 1등~",
            tail_target="left",
            characters=["트롤 주술사", "스카이본 마법사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic side-profile 90-degree action shot arranged across the lower frame. On the lower-left, the Troll Shaman girl holds up "
                "the revealed combat scroll sideways, laughing uproariously with head thrown back and sharp tusks showing, pointing behind her. "
                "On the lower-right, the Skyborne Mage girl leaps to her feet with starry eyes sparkling with immense joy, pumping her fist in victory. "
                "Generous pure #FFFFFF white headroom across top 35%."
            )
        ),
        ComicCut(
            cut_index=5,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker=None,
            dialogue=None,
            tail_target="center",
            characters=["언데드 성기사"],
            wordless=True,
            visual_prompt=(
                "Solo cute anime chibi girl from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dramatic low-angle shot looking up at the humiliated Paladin. Centered comedic chest-up freeze-frame of the Undead Paladin girl: "
                "her lower jaw has literally dropped completely open in horrified disbelief, yellow eye orbs dilated into tiny shaking dots, "
                "ghostly soul vapor floating out of her open mouth, paralyzed in frozen mortification at her own self-own."
            )
        ),
        ComicCut(
            cut_index=6,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="트롤 주술사",
            dialogue="무적귀환ㅋㅋ\n근데 길드창 박제는\n이미 다 봤음~",
            tail_target="right",
            characters=["언데드 성기사", "트롤 주술사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic back-view shot in action. On the lower-left, the Undead Paladin is seen from behind stepping into a glowing golden "
                "Divine Shield bubble and swirling cyan Hearthstone vortex, frantically channeling escape with holy sparkles flaring. "
                "On the lower-right, the Troll Shaman girl leans on her wooden totem staff, waving snarkily with a smug teasing smile and side-eye. "
                "Generous pure #FFFFFF white headroom across the top 35%."
            )
        )
    ]
    return EpisodeScript(
        episode_number=old["episode_number"],
        source_post_no=old["source_post_no"],
        source_title=old["source_title"],
        source_url=old["source_url"],
        subtitle=old["subtitle"],
        cuts=cuts
    )


def get_ep026(old):
    cuts = [
        ComicCut(
            cut_index=1,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="언데드 성기사",
            dialogue="옛날 언데드는\n양변·공포·혼절\n다 면역이었단다…",
            tail_target="left",
            characters=["언데드 성기사", "스카이본 마법사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Over-the-shoulder (OTS) diagonal shot recreating the screenshot's scholarly storytelling. In the foreground right, the large "
                "back and shoulder of the Skyborne Mage frames the view. In the background left, the Undead Paladin girl (top-row #2: stitched skull "
                "hood, silver plate armor) leans back comfortably beside crackling orange campfire embers, comically adjusting round Pepe-scholar "
                "reading glasses with one bony finger and a nostalgic, worldly smile as she recounts ancient beta lore. Generous pure white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=2,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="인간 흑마법사",
            dialogue="에이 그럼 무적\n사기 종족이잖아요?\n얼라는 맨날 털림?",
            tail_target="left",
            characters=["인간 흑마법사", "스카이본 마법사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dramatic low-angle shot looking up. On the lower-left, the Human Warlock girl (bottom-row #3: purple warlock hood, black pigtails, "
                "sharp violet eyes) leaps forward in enthusiastic fascination, clutching her plump red plush imp doll tightly to her chest with "
                "starry sparkling eyes and an intrigued grin. Beside her on the right, the Skyborne Mage nods attentively. Generous pure white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=3,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="언데드 성기사",
            dialogue="성기사 셋이\n언더시티에 와서\n퇴마술로 다 지웠지…",
            tail_target="left",
            characters=["언데드 성기사"],
            wordless=False,
            visual_prompt=(
                "Solo cute anime chibi girl from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dutch-tilt dynamic angle shot. The Undead Paladin girl cringes backward in comic dread, clutching her skull hood with trembling hands, "
                "pupils shrunk to tiny dots and blue sweat drops flying, surrounded by dramatic dark shadow mob silhouettes of three towering Paladins "
                "casting blinding beams of holy Exorcism light, reliving her ultimate historical trauma. Generous pure white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=4,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="스카이본 마법사",
            dialogue="근데 선배님…\n지금 본인 직업이\n성기사잖아요?",
            tail_target="left",
            characters=["스카이본 마법사", "언데드 성기사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic side-profile 90-degree action shot recreating the screenshot's confused Pepe shrug. On the lower-left, the Skyborne Mage "
                "girl stares deadpan sideways with narrowed unamused eyes, surrounded by comical floating red question mark icons, pointing directly "
                "at the holy silver libram and holy warhammer strapped to the Paladin's belt. On the lower-right, the Undead Paladin flinches with an awkward sweat drop. "
                "Generous pure #FFFFFF white headroom across top 35%."
            )
        ),
        ComicCut(
            cut_index=5,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker=None,
            dialogue=None,
            tail_target="center",
            characters=["언데드 성기사"],
            wordless=True,
            visual_prompt=(
                "Solo cute anime chibi girl from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "High-angle shot looking down at the guilty Paladin. Comedic chest-up close-up freeze-frame of the Undead Paladin girl: "
                "blank soulless white eyes, nervous guilty sweat waterfall pouring down her face, mouth twisted into an awkward zigzag grimace, "
                "frozen solid under the undeniable hypocritical reality."
            )
        ),
        ComicCut(
            cut_index=6,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="언데드 성기사",
            dialogue="이길 수 없으면\n합류하라\n했단다.",
            tail_target="left",
            characters=["언데드 성기사", "인간 흑마법사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic back-view shot. On the lower-left, the Undead Paladin girl is seen from behind walking away into the distance with her cape "
                "fluttering, resting her holy one-handed hammer over her shoulder and coolly tossing a carefree two-finger salute back over her shoulder "
                "with an unbothered smirk. On the lower-right, the Human Warlock girl sweatdrops in stunned exasperation. Generous pure white headroom top 35%."
            )
        )
    ]
    return EpisodeScript(
        episode_number=old["episode_number"],
        source_post_no=old["source_post_no"],
        source_title=old["source_title"],
        source_url=old["source_url"],
        subtitle=old["subtitle"],
        cuts=cuts
    )


def get_ep027(old):
    cuts = [
        ComicCut(
            cut_index=1,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="오크 전사",
            dialogue="주술사님…\n핑만 50번째임.\n말로 하셈…",
            tail_target="left",
            characters=["오크 전사", "트롤 주술사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Over-the-shoulder (OTS) diagonal shot. In the foreground right, the large shoulder and green plush hood of the Orc Warrior girl "
                "(top-row #1: black ponytail, spiky red pauldrons, carrying a sturdy steel shield on her arm) frames the scene, frowning with a twitching "
                "eyebrow in utter exasperation. In the background left, the Troll Shaman girl (middle-row #1: blue skin, voodoo skull mask with red feathers, "
                "wild pink hair) frantically spams a floating glowing yellow crosshair target ping icon in mid-air with rapid cartoon shockwave rings "
                "and multiple after-image hands. Generous pure #FFFFFF white headroom across top 35%."
            )
        ),
        ComicCut(
            cut_index=2,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="트롤 주술사",
            dialogue="법사 개못하네!\n골렘한테 양변을\n왜 안 거냐고!!",
            tail_target="left",
            characters=["트롤 주술사", "스카이본 마법사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic side-profile 90-degree action shot arranged across the lower frame. On the lower-left, the Troll Shaman girl stomps forward "
                "sideways shouting with sharp tusks bared, furious scowling orange eyes, pointing her clawed hand violently toward a bulky cartoon "
                "dark shadow golem silhouette. On the lower-right, the Skyborne Mage girl flinches backward in bewildered surprise, clutching her wooden "
                "wand with sweat drops on her brow. Generous pure #FFFFFF white headroom across top 35%."
            )
        ),
        ComicCut(
            cut_index=3,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="스카이본 마법사",
            dialogue="저기… 골렘은\n양변 면역인데요…?",
            tail_target="left",
            characters=["스카이본 마법사", "트롤 주술사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dutch-tilt dynamic angle comic cut. On the lower-left, the Skyborne Mage girl (bottom-row #4: pointed elf ears, aqua-tipped blonde "
                "hair, sailor collar) tilts her head innocently with a puzzled, cute smile, holding up an open thick leather fantasy spellbook with a "
                "glowing blue arcane glyph icon while pointing a tiny finger at it. On the lower-right, the Troll Shaman freezes mid-stride with sudden "
                "constricted pupils. Generous pure #FFFFFF white headroom across top 35%."
            )
        ),
        ComicCut(
            cut_index=4,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="트롤 주술사",
            dialogue="나 본캐가\n20년차 법사임!\n내 말대로 해!!",
            tail_target="left",
            characters=["트롤 주술사"],
            wordless=False,
            visual_prompt=(
                "Solo cute anime chibi girl from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dramatic low-angle shot looking up at the pompous veteran. Positioned cleanly on the left half of the wide 16:9 canvas, "
                "the Troll Shaman girl puffs her chest out arrogantly, holding her head high in the air with a haughty, pompous sneer and closed eyes, "
                "slamming the base of her wooden totem staff into the ground with dramatic golden comic shockwaves, shamelessly lecturing the party. "
                "Generous pure #FFFFFF white space across top and right."
            )
        ),
        ComicCut(
            cut_index=5,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker=None,
            dialogue=None,
            tail_target="center",
            characters=["스카이본 마법사"],
            wordless=True,
            visual_prompt=(
                "Solo cute anime chibi girl from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "High-angle shot looking down at the dumbfounded Mage. Centered comedic chest-up freeze-frame of the Skyborne Mage girl: "
                "her huge sapphire eyes have turned completely blank into solid white soulless ovals, a tiny pale cartoon ghost soul escaping "
                "from her half-open mouth, frozen completely numb at the sheer boomer logic."
            )
        ),
        ComicCut(
            cut_index=6,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="오크 전사",
            dialogue="그 20년 동안\n'왼쪽 벽 붙어요'\n한 마디를 못 배움?",
            tail_target="left",
            characters=["오크 전사", "트롤 주술사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic back-view shot. On the lower-left, the Orc Warrior girl (equipped with sturdy steel kite shield on her arm and one-handed "
                "axe at her belt) is seen from behind walking away dismissively, tossing a deadpan savage remark back over her shoulder with an "
                "unimpressed smirk. On the lower-right, the Troll Shaman girl stands completely petrified into gray stone shock lines. "
                "Generous pure #FFFFFF white headroom across top 35%."
            )
        )
    ]
    return EpisodeScript(
        episode_number=old["episode_number"],
        source_post_no=old["source_post_no"],
        source_title=old["source_title"],
        source_url=old["source_url"],
        subtitle=old["subtitle"],
        cuts=cuts
    )


def get_ep028(old):
    cuts = [
        ComicCut(
            cut_index=1,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="인간 흑마법사",
            dialogue="탱님! 랩터 다섯\n마리 다 흩어져요!\n천벼 좀요!!",
            tail_target="left",
            characters=["오크 전사", "인간 흑마법사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic side-profile 90-degree action shot recreating the Wetlands beta raptor pack. Across the lower frame, a swarm of five "
                "agile dark cartoon shadow raptor mob silhouettes with glowing yellow eyes rush past through swamp puddles. On the lower-left, the "
                "Human Warlock girl (bottom-row #3: purple hood, black pigtails, violet eyes) flees sideways in utter panic, clutching her plump red "
                "plush imp doll with waterfall cartoon tears streaming and mouth open screaming for help. Generous pure white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=2,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="오크 전사",
            dialogue="탱은 방가\n5중첩이 국룰.\n한 땀 한 땀 간다.",
            tail_target="left",
            characters=["오크 전사"],
            wordless=False,
            visual_prompt=(
                "Solo cute anime chibi girl from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Over-the-shoulder (OTS) diagonal shot. Positioned in the lower-left, the Orc Warrior girl (top-row #1: green plush orc hood, "
                "spiky red pauldrons, silver plate armor) acts as protection tank, firmly planting her sturdy steel kite shield forward while "
                "swinging her one-handed silver battle axe with slow, meticulous precision against a single tiny target, sporting an obstinate, "
                "self-righteous smirk and ignoring the chaos around her. Generous pure #FFFFFF white headroom across top 35%."
            )
        ),
        ComicCut(
            cut_index=3,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="스카이본 마법사",
            dialogue="으아악 랩터가\n전부 캐스터한테\n와요오!!",
            tail_target="left",
            characters=["스카이본 마법사", "인간 흑마법사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dutch-tilt dynamic slapstick angle. On the lower-left, the Skyborne Mage girl (bottom-row #4: blonde hair with aqua tips, sailor robe) "
                "is sprinting frantically with flailing limbs and spinning spiral eyes, robes flying as two snarling cartoon raptor silhouettes snap at "
                "her heels with flying dust puffs. Beside her, the Human Warlock scrambles desperately in terror. Generous pure #FFFFFF white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=4,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="인간 흑마법사",
            dialogue="달라란 학자들도\n광역엔 방가가\n불리하댔다고요!!",
            tail_target="left",
            characters=["인간 흑마법사", "오크 전사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dramatic low-angle shot looking up recreating the screenshot's Dalaran scholarly scroll punchline. On the lower-left, the Human "
                "Warlock girl frantically waves an unrolled ancient Dalaran scholarly scroll with furious pleading eyes, dark purple arcane sparkles, "
                "and dramatic comic sweat drops. On the lower-right in the background, the Orc Warrior tank unconcernedly polishes her sturdy steel "
                "shield with a deaf ear. Generous pure #FFFFFF white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=5,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker=None,
            dialogue=None,
            tail_target="center",
            characters=["오크 전사"],
            wordless=True,
            visual_prompt=(
                "Solo cute anime chibi girl from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "High-angle shot looking down at the oblivious tank. Centered comedic chest-up freeze-frame of the Orc Warrior girl: "
                "raising her sturdy steel shield proudly in victory with gleaming golden stars around her, grinning with huge toothy self-satisfaction "
                "and bright rosy cheeks, totally unaware that the entire party behind her has been wiped out."
            )
        ),
        ComicCut(
            cut_index=6,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="오크 전사",
            dialogue="봐봐, 방가\n5중첩 완성!\n…다들 어디 감?",
            tail_target="left",
            characters=["오크 전사", "스카이본 마법사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic back-view shot. On the lower-left, the Orc Warrior girl (sturdy steel shield on arm, one-handed axe resting over shoulder) "
                "is seen from behind scratching her green plush hood in confusion looking at the empty floor. On the lower-right, two translucent glowing "
                "cyan spirit ghosts of the Skyborne Mage and Human Warlock hover in the air glaring down with dead white eyes and cold glares. "
                "Generous pure #FFFFFF white headroom top 35%."
            )
        )
    ]
    return EpisodeScript(
        episode_number=old["episode_number"],
        source_post_no=old["source_post_no"],
        source_title=old["source_title"],
        source_url=old["source_url"],
        subtitle=old["subtitle"],
        cuts=cuts
    )


def get_ep029(old):
    cuts = [
        ComicCut(
            cut_index=1,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="노움 도적",
            dialogue="기사님 또 입찰?!\n천 가죽 사슬\n다 굴리네!!",
            tail_target="left",
            characters=["노움 도적", "언데드 성기사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Over-the-shoulder (OTS) diagonal shot. In the foreground right, the large shoulder and stitched skull hood of the Undead Paladin "
                "frames the view. In the background left, the Gnome Rogue girl (top-row #3: blonde pigtails with pink/blue tips, steampunk aviator goggles, "
                "black stealth cloak, daggers sheathed at waist) stomps her feet in furious outrage, shaking both fists with sharp shark teeth and popping "
                "comic anger veins. Generous pure #FFFFFF white headroom across top 35%."
            )
        ),
        ComicCut(
            cut_index=2,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="드워프 사냥꾼",
            dialogue="도적은 깨끗해?\n필비도 성검도\n다 도적 꺼라며!",
            tail_target="left",
            characters=["드워프 사냥꾼", "노움 도적"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic side-profile 90-degree action shot arranged across the lower frame. On the lower-left, the Dwarf Hunter girl (top-row #4: "
                "fluffy snowy bear hood, braided crimson hair, holding her wooden hunting musket) steps into frame sideways, wagging an accusatory "
                "gloved finger with a sly mocking grin. On the lower-right, the Gnome Rogue flinches sideways with puffed sulky cheeks and narrow side-eye. "
                "Generous pure #FFFFFF white headroom across top 35%."
            )
        ),
        ComicCut(
            cut_index=3,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="노움 도적",
            dialogue="냥꾼은 랩터크리\n한다고 근접무기\n다 굴리잖아!",
            tail_target="left",
            characters=["노움 도적", "드워프 사냥꾼"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dutch-tilt dynamic angle comic cut. The Gnome Rogue and Dwarf Hunter lean aggressively forward nose-to-nose in a fiery slapstick feud, "
                "sparks flying between their glaring eyes with comical red anger lightning and clenched teeth, bickering over dungeon loot priority. "
                "Generous pure #FFFFFF white headroom across top 35%."
            )
        ),
        ComicCut(
            cut_index=4,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="언데드 성기사",
            dialogue="2005년에도 이랬지.\n싸움 끝엔 늘\n무분 전사가 웃었어.",
            tail_target="left",
            characters=["언데드 성기사", "오크 전사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dramatic low-angle shot looking up. On the lower-left, the Undead Paladin girl (stitched skull hood, silver plate armor) leans back "
                "with arms crossed, chuckling cynical veteran wisdom with half-closed eyes and a knowing smirk beside a minimalist dungeon stone vignette. "
                "On the lower-right in the background, the Orc Warrior stands watching. Generous pure #FFFFFF white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=5,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker=None,
            dialogue=None,
            tail_target="center",
            characters=["오크 전사"],
            wordless=True,
            visual_prompt=(
                "Solo cute anime chibi girl from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "High-angle shot looking down at the scheming Warrior. Centered comedic chest-up freeze-frame of the Orc Warrior girl (top-row #1: "
                "green plush orc hood, crimson eyes, spiky pauldrons): rubbing her armored gauntlets together with a sneaky, greedy villainous grin, "
                "crimson eyes glittering with shameless delight as she plots to claim every single contested weapon."
            )
        ),
        ComicCut(
            cut_index=6,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="오크 전사",
            dialogue="근데 기사님...\n2005년 얘기면\n관짝에 몇 년 계셨어요?",
            tail_target="left",
            characters=["오크 전사", "언데드 성기사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic back-view shot. On the lower-left, the Orc Warrior girl is seen from behind walking away carrying a bundle of looted "
                "swords and interlocking ring-mesh mail armor under her arm, casually tossing a savage boomer burn back over her shoulder with an unbothered smirk. "
                "On the lower-right, the Undead Paladin freezes in shocked stone stillness with jaw dropping. Generous pure white headroom top 35%."
            )
        )
    ]
    return EpisodeScript(
        episode_number=old["episode_number"],
        source_post_no=old["source_post_no"],
        source_title=old["source_title"],
        source_url=old["source_url"],
        subtitle=old["subtitle"],
        cuts=cuts
    )


def get_ep030(old):
    cuts = [
        ComicCut(
            cut_index=1,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="스카이본 마법사",
            dialogue="와 목걸이 떴다!\n지능 붙은 거니까\n법사 거죠?",
            tail_target="left",
            characters=["스카이본 마법사", "드워프 사냥꾼"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Over-the-shoulder (OTS) diagonal shot recreating the screenshot's Triune Amulet drop. In the foreground right, the large shoulder "
                "and aqua-tipped hair of the Skyborne Mage frames the view, pointing with starry sparkling sapphire eyes toward the glowing blue "
                "Triune Amulet gemstone necklace hovering in mid-air with bright rare loot sparkles. In the background left, the Dwarf Hunter watches greedily. "
                "Generous pure white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=2,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="드워프 사냥꾼",
            dialogue="입찰 꾹~!\n목걸이는 냥꾼도\n찰 수 있거든~",
            tail_target="left",
            characters=["드워프 사냥꾼"],
            wordless=False,
            visual_prompt=(
                "Solo cute anime chibi girl from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic action motion shot positioned cleanly in the lower frame. The Dwarf Hunter girl (top-row #4: fluffy snowy bear hood, "
                "braided crimson hair) lunges forward with dynamic comic speed lines, tossing and slamming a chunky white-and-gold fantasy loot die "
                "(simple black dot pips only, ZERO digits) onto the ground with a greedy mischievous toothy grin, snatching the glowing Triune Amulet necklace into her paws. "
                "Generous pure #FFFFFF white space across top 35%."
            )
        ),
        ComicCut(
            cut_index=3,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="트롤 주술사",
            dialogue="잠깐, 그 목걸이\n상점에 팔았다고?!",
            tail_target="left",
            characters=["트롤 주술사", "드워프 사냥꾼"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dutch-tilt dynamic angle comic cut. On the lower-left, the Troll Shaman girl (voodoo mask, wild pink hair) lunges forward in utter shock, "
                "gripping the Hunter's bear hood with wide trembling orange eyes and dropped jaw, screaming in disbelief. On the lower-right, the Dwarf "
                "Hunter sweats nervously with an unrepentant toothy smirk. Generous pure #FFFFFF white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=4,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="드워프 사냥꾼",
            dialogue="먹어보니 달라란\n퀘템 목보다 구려서~\n바로 팔았지 ㅋㅋ",
            tail_target="left",
            characters=["드워프 사냥꾼"],
            wordless=False,
            visual_prompt=(
                "Solo cute anime chibi girl from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dramatic low-angle shot looking up recreating the screenshot character sheet. The Dwarf Hunter girl stands tall proudly tapping "
                "her equipped Dalaran quest necklace (faceted green gemstone pendant) on her chest, while tossing a chunky pouch of shiny vendor gold "
                "coins up and down in her hand with cheeky carefree satisfaction and closed eyes, completely unapologetic. Generous pure white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=5,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker=None,
            dialogue=None,
            tail_target="center",
            characters=["스카이본 마법사"],
            wordless=True,
            visual_prompt=(
                "Solo cute anime chibi girl from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "High-angle shot looking down at the devastated Mage. Centered comedic chest-up freeze-frame of the Skyborne Mage girl: "
                "her huge sapphire eyes have turned into hollow blank white circles, faint ghostly soul vapors drifting from her open mouth, "
                "frozen in utterly shattered disbelief at the vendor ninja."
            )
        ),
        ComicCut(
            cut_index=6,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="트롤 주술사",
            dialogue="사격 32 고독한 늑대?\n축하해, 전원 차단이라\n이제 진짜 고독한 늑대야.",
            tail_target="right",
            characters=["드워프 사냥꾼", "트롤 주술사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic back-view shot recreating the 32-point Lone Wolf talent screenshot. On the lower-left, the Dwarf Hunter is seen from behind "
                "standing completely isolated in an empty cold field with a stylized cartoon howling lone wolf shadow silhouette and a tumbleweed rolling past. "
                "On the lower-right, the Troll Shaman girl walks away into the distance, waving a snarky goodbye back over her shoulder with a sharp toothy grin. "
                "Generous pure #FFFFFF white headroom top 35%."
            )
        )
    ]
    return EpisodeScript(
        episode_number=old["episode_number"],
        source_post_no=old["source_post_no"],
        source_title=old["source_title"],
        source_url=old["source_url"],
        subtitle=old["subtitle"],
        cuts=cuts
    )


def get_ep031(old):
    cuts = [
        ComicCut(
            cut_index=1,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="오크 전사",
            dialogue="언기사 성능 최고지?\n오그리마 입성\n환영한다!!",
            tail_target="left",
            characters=["오크 전사", "언데드 성기사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Over-the-shoulder (OTS) diagonal shot. In the foreground right, the large shoulder and stitched skull hood of the Undead Paladin "
                "girl (top-row #2: pale lilac skin, silver armor) frames the view. In the background left, the Orc Warrior girl (top-row #1: "
                "green plush orc hood, crimson eyes, spiky red pauldrons) spreads both arms wide in enthusiastic welcome with a huge toothy grin "
                "beside a crude wooden spiked Horde barricade vignette. Generous pure #FFFFFF white headroom across top 35%."
            )
        ),
        ComicCut(
            cut_index=2,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="언데드 성기사",
            dialogue="근데 땅이 왜 다 빨개...\n움막에서 퀘하니까\n겜 하는 기분이 안 나.",
            tail_target="left",
            characters=["언데드 성기사"],
            wordless=False,
            visual_prompt=(
                "Solo cute anime chibi girl from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic side-profile 90-degree action shot. Positioned cleanly in the lower frame, the Undead Paladin girl trudges dejectedly "
                "to the right with slumped shoulders, dragging her one-handed mace on the ground, looking down at dusty red ground with dull lifeless "
                "yellow eyes and deep melancholic blue sweat drops beside a crude thatched mud hut vignette. Generous pure white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=3,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="언데드 성기사",
            dialogue="스톰윈드 그 웅장한\n브금이 그리워...\n언기사랑 흑마 다 지울래.",
            tail_target="left",
            characters=["언데드 성기사", "오크 전사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dutch-tilt dynamic angle comic cut. On the lower-left, the Undead Paladin girl dramatically clutches both hands to her chest "
                "with anime waterfall tears streaming from her eyes, imagining majestic brass orchestra horns with glowing golden musical notes. "
                "On the lower-right, the Orc Warrior girl stumbles backward in absolute disbelief with popping eyes. Generous pure white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=4,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker=None,
            dialogue=None,
            tail_target="center",
            characters=["오크 전사"],
            wordless=True,
            visual_prompt=(
                "Solo cute anime chibi girl from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dramatic low-angle shot looking up at the betrayed Warrior. Centered comedic chest-up freeze-frame of the Orc Warrior girl: "
                "jaw dropped completely open in horrified disbelief, crimson pupils shrunk to tiny dots, soul vapor drifting from her fangs, "
                "frozen in utter shock at her comrade abandoning the Horde for background music."
            )
        ),
        ComicCut(
            cut_index=5,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="인간 흑마법사",
            dialogue="언기사 지우고\n인간 흑마로 왔어요!\n아 이 브금 미쳤다...",
            tail_target="left",
            characters=["인간 흑마법사", "나이트엘프 사제"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "High-angle shot looking down at the joyous arrival. On the lower-left, the Human Warlock girl (bottom-row #3: purple warlock hood, "
                "black pigtails, sharp violet eyes) hugs her plump red imp plushie tightly, eyes glistening with golden stars and tears of pure bliss "
                "beside a pristine white marble cathedral pillar vignette. On the lower-right, the Night Elf Priest smiles warmly. Generous pure white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=6,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="인간 흑마법사",
            dialogue="성능 1티어 언기사보다\n스톰윈드 브금이\n찐 1티어예요!!",
            tail_target="left",
            characters=["인간 흑마법사", "나이트엘프 사제"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic back-view shot. On the lower-left, the Human Warlock girl is seen from behind skipping joyfully into the distance, "
                "throwing both arms up in triumph toward golden orchestral rays and sparkles, casually tossing a radiant smile back over her shoulder. "
                "Beside her, the Night Elf Priest giggles with hands clasped. Generous pure #FFFFFF white headroom across top 35%."
            )
        )
    ]
    return EpisodeScript(
        episode_number=old["episode_number"],
        source_post_no=old["source_post_no"],
        source_title=old["source_title"],
        source_url=old["source_url"],
        subtitle=old["subtitle"],
        cuts=cuts
    )


def get_ep032(old):
    cuts = [
        ComicCut(
            cut_index=1,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="드워프 사냥꾼",
            dialogue="와 양손도끼 떴다!\n전탱님은 방패 쓰니까\n이건 제가 먹을게요~",
            tail_target="left",
            characters=["드워프 사냥꾼", "오크 전사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Over-the-shoulder (OTS) diagonal shot. In the foreground right, the large shoulder and green hood of the Orc Warrior tank "
                "(carrying a sturdy steel kite shield strapped to her left arm) frames the scene. In the background left, the Dwarf Hunter girl "
                "(top-row #4: snowy bear hood, braided crimson hair) points slyly with a scheming toothy grin at a massive two-handed battle axe "
                "radiating bright blue rare loot sparkles hovering in mid-air. Generous pure #FFFFFF white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=2,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="오크 전사",
            dialogue="누가 안 쓴대?!\n솔플할 땐 양손\n든다고 내가!!",
            tail_target="left",
            characters=["오크 전사", "노움 도적"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic side-profile 90-degree action shot arranged across the lower frame. On the lower-left, the Orc Warrior girl stomps forward "
                "sideways, brandishing her one-handed battle axe with bared fangs, furious crimson glare, and comic red steam puffing from her ears. "
                "On the lower-right, the Gnome Rogue giggles quietly behind her hand. Generous pure #FFFFFF white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=3,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="드워프 사냥꾼",
            dialogue="에이~ 탱은 방패죠!\n민첩도 붙었으니\n이건 냥꾼 스탯봉~",
            tail_target="left",
            characters=["드워프 사냥꾼", "오크 전사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dutch-tilt dynamic angle comic cut. On the lower-left, the Dwarf Hunter girl leans into the frame with an infuriatingly smug "
                "closed-eye smile, tapping her wooden hunting musket with one finger while gesturing toward the two-handed axe. On the lower-right, "
                "the Orc Warrior tank grits her teeth in outraged protest. Generous pure #FFFFFF white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=4,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="오크 전사",
            dialogue="재미로 쓰든 어디 쓰든\n전사님 맘이야!\n입찰 간다!!",
            tail_target="left",
            characters=["오크 전사", "드워프 사냥꾼"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dramatic low-angle shot looking up. On the lower-left, the Orc Warrior girl slams a chunky white-and-gold fantasy loot cube die "
                "(showing simple black dot pips only, strictly ZERO digits) violently into the ground with dynamic comic speed lines and blazing red eyes. "
                "On the lower-right, the Dwarf Hunter recoils in shock. Generous pure #FFFFFF white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=5,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker=None,
            dialogue=None,
            tail_target="center",
            characters=["오크 전사"],
            wordless=True,
            visual_prompt=(
                "Solo cute anime chibi girl from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "High-angle shot looking down at the petrified contenders. Centered comedic chest-up freeze-frame of the Orc Warrior girl: "
                "her jaw dropped to the floor, eyes spinning in frantic spirals, frozen in dead silence looking at the winning loot roll result."
            )
        ),
        ComicCut(
            cut_index=6,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="노움 도적",
            dialogue="둘이 싸우길래\n나도 입찰했지~\n상점가 짭짤하네♡",
            tail_target="left",
            characters=["노움 도적", "드워프 사냥꾼"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic back-view shot. On the lower-left, the petite Gnome Rogue girl is seen from behind walking away stealthily, proudly carrying "
                "the massive glowing two-handed battle axe horizontally over her tiny shoulders, playfully winking back over her shoulder with a shiny "
                "pouch of gold coins. On the lower-right in the background, the Dwarf Hunter collapses in tears. Generous pure white headroom top 35%."
            )
        )
    ]
    return EpisodeScript(
        episode_number=old["episode_number"],
        source_post_no=old["source_post_no"],
        source_title=old["source_title"],
        source_url=old["source_url"],
        subtitle=old["subtitle"],
        cuts=cuts
    )


def get_ep033(old):
    cuts = [
        ComicCut(
            cut_index=1,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="노움 도적",
            dialogue="노움 사제 초상화 봤어?\n완전 요정이더라!\n나 당장 부캐 판다!",
            tail_target="left",
            characters=["노움 도적", "스카이본 마법사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Over-the-shoulder (OTS) diagonal shot recreating the screenshot's AI fairy gnome portrait. In the foreground right, the large "
                "shoulder and golden-aqua hair of the Skyborne Mage frames the view. In the background left, the Gnome Rogue girl (top-row #3: "
                "blonde pigtails with pink/blue tips, goggles, black cloak) holds up a glowing fantasy parchment portrait of a gorgeous ethereal fairy "
                "gnome priestess with golden halo and holy staff, jumping with starry sparkling blue eyes and rosy cheeks. Generous pure white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=2,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="나이트엘프 사제",
            dialogue="그 그림 믿지 마...\n나도 노움 사제 했다가\n나엘로 도망쳤어.",
            tail_target="left",
            characters=["나이트엘프 사제", "노움 도적"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic side-profile 90-degree action shot arranged across the lower frame. On the lower-left, the Night Elf Priest girl (top-row #2: "
                "lavender hair, white clergy robe) steps in sideways, waving her hands in grim warning with a deadpan traumatized stare and heavy "
                "dark blue shadow over her eyes. On the lower-right, the Gnome Rogue brushes it off with a cheerful careless giggle. Generous white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=3,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="노움 도적",
            dialogue="에이 설마~\n노움 사제 생성 완료!\n얼굴 확인 간다!",
            tail_target="left",
            characters=["노움 도적"],
            wordless=False,
            visual_prompt=(
                "Solo cute anime chibi girl from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic action motion shot positioned cleanly in the lower frame. The Gnome Rogue girl leaps into the air with enthusiastic energy, "
                "slamming her hands onto a glowing fantasy character-creation crystal podium with cyan magic swirls and sparkling dust puffs, grinning "
                "with innocent excitement to inspect her new character. Generous pure #FFFFFF white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=4,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker=None,
            dialogue=None,
            tail_target="center",
            characters=["노움 도적"],
            wordless=True,
            visual_prompt=(
                "Solo cute anime chibi girl from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dramatic low-angle shot looking up recreating the original screenshot's in-game reality. Centered comedic chest-up freeze-frame of "
                "the Gnome Rogue girl staring in horror at a female gnome model in a white wedding dress wearing a ridiculous propeller tin helmet "
                "with a bulldog scowl: her aviator goggles droop crookedly, eyes turned into dizzying multi-ring spirals of sheer horror, lower jaw unhinged "
                "and dropping to her chest, a pale cartoon ghost soul floating from her open mouth in frozen buyer's remorse."
            )
        ),
        ComicCut(
            cut_index=5,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="스카이본 마법사",
            dialogue="어... 초상화엔\n그런 코 없었는데?",
            tail_target="left",
            characters=["스카이본 마법사", "노움 도적"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dutch-tilt dynamic angle comic cut. On the lower-left, the Skyborne Mage girl leans forward with a giant cartoon magnifying glass, "
                "inspecting the propeller helmet and bulbous nose with an awkward, sympathetic grimace and sweat drop. On the lower-right, the Gnome "
                "Rogue girl is on her knees clutching her face in agonizing despair. Generous pure #FFFFFF white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=6,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="나이트엘프 사제",
            dialogue="어서 와.\n나도 당했다 모임\n오늘만 백 명째야.",
            tail_target="left",
            characters=["나이트엘프 사제", "노움 도적"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic back-view shot. On the lower-left, the Night Elf Priest girl is seen from behind resting a comforting hand on the sobbing "
                "Gnome Rogue's shoulder, guiding her gently toward a distant cartoon support group campfire vignette, tossing a worldly dry remark "
                "back over her shoulder with an understanding smirk. Generous pure #FFFFFF white headroom top 35%."
            )
        )
    ]
    return EpisodeScript(
        episode_number=old["episode_number"],
        source_post_no=old["source_post_no"],
        source_title=old["source_title"],
        source_url=old["source_url"],
        subtitle=old["subtitle"],
        cuts=cuts
    )


def get_ep034(old):
    cuts = [
        ComicCut(
            cut_index=1,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="오크 전사",
            dialogue="마나 확인? 그런 거 없다!\n쫄 4팩 한 번에 간다!!",
            tail_target="right",
            characters=["나이트엘프 사제", "오크 전사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dramatic low-angle shot looking up at the charging reckless tank. On the lower-right, the Orc Warrior girl (top-row #1: "
                "green plush orc hood, spiky red pauldrons, silver armor) charges forward recklessly into the dungeon, brandishing a sturdy "
                "steel tower shield in her left hand and a one-handed silver axe in her right hand with flying dust puffs and blazing red battle eyes. "
                "On the lower-left, the Night Elf Priest girl gasps in horror clutching an empty mana flask. Generous white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=2,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="오크 전사",
            dialogue="힐러 뭐 함?!\n탱 죽는 거 안 보여?!",
            tail_target="right",
            characters=["오크 전사"],
            wordless=False,
            visual_prompt=(
                "Solo cute anime chibi girl from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "High-angle shot looking down at the blame-shifting tank. Positioned cleanly in the lower frame, the Orc Warrior girl is comically "
                "collapsed faceplant on the floor with her sturdy steel shield resting beside her, suddenly lifting her head with waterfall anime tears "
                "and pointing an armored finger furiously upward with jagged shark teeth, screaming at the healer. Generous white space top 35%."
            )
        ),
        ComicCut(
            cut_index=3,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="오크 전사",
            dialogue="어글 튀었잖아!\n딜러들 어글 관리\n안 하냐고!!",
            tail_target="left",
            characters=["오크 전사", "노움 도적"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dutch-tilt dynamic angle comic cut. On the lower-left, the Orc Warrior jumps to her feet stomping angrily, shaking her sturdy "
                "steel shield in rage while four dark cartoon shadow mob silhouettes swarm around the party. On the lower-right, the Gnome Rogue "
                "dodges frantically sideways with wide alarmed eyes and flying sweat drops. Generous pure #FFFFFF white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=4,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker=None,
            dialogue=None,
            tail_target="center",
            characters=["나이트엘프 사제"],
            wordless=True,
            visual_prompt=(
                "Solo cute anime chibi girl from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "High-angle shot looking down at the traumatized healer. Centered comedic chest-up freeze-frame of the Night Elf Priest girl: "
                "her lavender hair drooping limp, eyes turned completely into blank white soulless ovals, a dark gloomy purple cloud raining "
                "cartoon tears over her head, paralyzed in deadpan emotional exhaustion."
            )
        ),
        ComicCut(
            cut_index=5,
            layout_slot="top",
            aspect_ratio="4:3",
            speaker="노움 도적",
            dialogue="탱님... 도발\n한 번도 안 누르셨는데요?",
            tail_target="left",
            characters=["노움 도적", "오크 전사"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Over-the-shoulder (OTS) diagonal shot. In the foreground right, the large shoulder and green plush hood of the Orc Warrior tank "
                "frames the view, frozen stiff. In the background left, the Gnome Rogue crosses her arms deadpan with half-closed eyes and points "
                "a tiny gloved finger directly forward with a flat, unamused poker face. Generous pure #FFFFFF white headroom top 35%."
            )
        ),
        ComicCut(
            cut_index=6,
            layout_slot="bottom",
            aspect_ratio="16:9",
            speaker="오크 전사",
            dialogue="지금 탱한테 반박?\n반박 시 거름!!",
            tail_target="left",
            characters=["오크 전사", "노움 도적"],
            wordless=False,
            visual_prompt=(
                "Two cute anime chibi girls from the Draft C cast sheet on a 100% pure solid #FFFFFF white borderless background "
                "(no scenery, no floor shading, no gray backdrop, no panel borders, zero text, zero speech bubbles). "
                "Dynamic back-view shot. On the lower-left, the Orc Warrior girl (sturdy steel shield on arm, one-handed axe at hip) is seen from behind "
                "walking away in a stubborn huff, head turned back tossing a childish entitled tantrum with puffed red cheeks and closed eyes. "
                "On the lower-right, the Gnome Rogue watches with an exasperated facepalm. Generous pure #FFFFFF white headroom top 35%."
            )
        )
    ]
    return EpisodeScript(
        episode_number=old["episode_number"],
        source_post_no=old["source_post_no"],
        source_title=old["source_title"],
        source_url=old["source_url"],
        subtitle=old["subtitle"],
        cuts=cuts
    )


GETTERS = {
    "ep023": get_ep023,
    "ep024": get_ep024,
    "ep025": get_ep025,
    "ep026": get_ep026,
    "ep027": get_ep027,
    "ep028": get_ep028,
    "ep029": get_ep029,
    "ep030": get_ep030,
    "ep031": get_ep031,
    "ep032": get_ep032,
    "ep033": get_ep033,
    "ep034": get_ep034,
}


def process_all():
    all_passed = True
    for ep_num in range(23, 35):
        ep = f"ep{ep_num:03d}"
        path = Path(f"data/episodes/{ep}/script.json")
        old = json.loads(path.read_text(encoding="utf-8"))
        getter = GETTERS[ep]
        script = getter(old)
        
        # Verify model validation
        EpisodeScript.model_validate(script)
        
        # Verify audit quality
        res = audit_script_quality(script, strict_cinematic=True)
        print(f"=== {ep} #{script.source_post_no} ===")
        print(f"Passed: {res['passed']}, Errors: {res['errors']}, Warnings: {res['warnings']}")
        print(f"Cinematic Metrics: {res['cinematic_metrics']}")
        if not res["passed"]:
            all_passed = False
            print(f"ERROR: Audit failed for {ep}!")
            continue
        
        # Save script.json
        path.write_text(script.model_dump_json(indent=2), encoding="utf-8")
        
        # Save prompts.json
        raw_cuts_dir = Path(f"data/raw_cuts/{ep}")
        raw_cuts_dir.mkdir(parents=True, exist_ok=True)
        prompt_pack = []
        for cut in script.cuts:
            target_path = str((raw_cuts_dir / f"cut_{cut.cut_index:02d}.png").resolve())
            prompt = build_cut_image_prompt(cut)
            prompt_pack.append({
                "cut_index": cut.cut_index,
                "aspect_ratio": cut.aspect_ratio,
                "target_path": target_path,
                "prompt": prompt,
            })
        (raw_cuts_dir / "prompts.json").write_text(json.dumps(prompt_pack, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved {ep} script.json and prompts.json successfully.")
        
    if not all_passed:
        exit(1)
    print("\nALL 12 EPISODES SUCCESSFULLY PROCESSED, AUDITED, AND SAVED!")


if __name__ == "__main__":
    process_all()
