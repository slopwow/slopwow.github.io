import json
from pathlib import Path
from wow_sloptoon.models import EpisodeScript, ComicCut
from wow_sloptoon.writer import audit_script_quality
from wow_sloptoon.artist import build_cut_image_prompt

def upgrade_ep023():
    ep = "ep023"
    path = Path(f"data/episodes/{ep}/script.json")
    old = json.loads(path.read_text(encoding="utf-8"))
    
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
                "On the lower-left, dynamic action motion shot: the Skyborne Mage girl (bottom-row #4: pointed elf ears, long golden-blonde "
                "hair fading into aqua tips, sapphire eyes, blue-and-white sailor-collar mage uniform with teal ribbon) is dashing forward "
                "in high spirits with flying comic dust puffs, holding her gnarled wooden staff outward and smiling with wide sparkling eyes. "
                "On the lower-right, the Orc Warrior girl (top-row #1: green plush orc hood with fangs, black high ponytail, crimson eyes, "
                "spiky red pauldrons, silver plate armor, carrying a sturdy steel shield on her left arm and one-handed axe at her hip) "
                "reaches one hand forward in alarm. Generous pure #FFFFFF white headroom across the top 35%."
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
                "Dynamic side-profile 90-degree action shot arranged across the lower frame. On the right, the Skyborne Mage girl "
                "is sprinting frantically away to the left with wide panicked spiral eyes and waterfall cartoon tears streaming from her cheeks, "
                "robes fluttering as dark cartoon shadow mob silhouettes with glowing red eyes chase closely behind her. On the lower-left, "
                "the Night Elf Priest girl (top-row #2: long lavender hair, pointed ears, silver tiara, white-and-gold clergy vestments) "
                "points in absolute terror with mouth wide open screaming. Generous pure #FFFFFF white headroom across the top 35%."
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
                "Dramatic low-angle shot looking up at the heroic tank. On the lower-left, the Orc Warrior girl (top-row #1: green plush orc hood, "
                "black high ponytail, crimson eyes flashing with fierce resolve, spiky red pauldrons) charges forward lunging into battle, "
                "firmly brandishing a sturdy heavy steel tower shield in her left hand and a one-handed silver battle axe in her right hand, "
                "roaring Challenging Shout with dynamic red battle cry shockwaves and comic speed lines. On the lower-right in the background, "
                "the Skyborne Mage crouches low in relief. Generous pure #FFFFFF white headroom across the top 35%."
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
                "High-angle shot looking down at the aftermath. On the lower-left, the Orc Warrior girl is comically collapsed faceplant "
                "on the ground in exhaustion with little spinning spiral stars above her green plush hood, her sturdy steel shield and one-handed "
                "axe resting safely beside her. On the lower-right, the Night Elf Priest girl kneels desperately holding an empty overturned "
                "fantasy glass mana potion flask with blue mana sparks empty, clutching her head with waterfall anime tears and pale shock lines. "
                "Generous pure #FFFFFF white space across the top 35%."
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
    
    script = EpisodeScript(
        episode_number=old["episode_number"],
        source_post_no=old["source_post_no"],
        source_title=old["source_title"],
        source_url=old["source_url"],
        subtitle=old["subtitle"],
        cuts=cuts
    )
    return ep, script


def upgrade_ep024():
    ep = "ep024"
    path = Path(f"data/episodes/{ep}/script.json")
    old = json.loads(path.read_text(encoding="utf-8"))
    
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
                "Over-the-shoulder (OTS) diagonal shot from behind the Skyborne Mage. In the foreground right, the large back and shoulder of "
                "the Skyborne Mage girl (golden hair fading to aqua tips, sailor collar) frames the scene. In the background left facing forward, "
                "the petite Gnome Rogue girl (top-row #3: blonde pigtails with pink/blue tips, steampunk aviator goggles, cross hairpins, black cloak, "
                "daggers sheathed at waist) tiptoes forward with a cheeky wheedling smile, rubbing her gloved hands together eagerly demanding water. "
                "Generous pure #FFFFFF white headroom across the top 35%."
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
    
    script = EpisodeScript(
        episode_number=old["episode_number"],
        source_post_no=old["source_post_no"],
        source_title=old["source_title"],
        source_url=old["source_url"],
        subtitle=old["subtitle"],
        cuts=cuts
    )
    return ep, script


def upgrade_ep025():
    ep = "ep025"
    path = Path(f"data/episodes/{ep}/script.json")
    old = json.loads(path.read_text(encoding="utf-8"))
    
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
                "Over-the-shoulder (OTS) diagonal shot. In the foreground right, the large shoulder and back of the head of the Skyborne Mage "
                "(blonde hair with aqua tips) frames the view. In the background left, the Undead Paladin girl (top-row #2: pale lilac skin, "
                "stitched skull hood, silver armor, glowing yellow eyes) leans forward with a smug sneer and toothy grin, triumphantly holding "
                "up an unrolled fantasy parchment meter scroll with a dramatic flourish. Generous pure #FFFFFF white headroom across top 35%."
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
                "Dutch-tilt dynamic angle shot. On the lower-left, the Troll Shaman girl (middle-row #1: blue skin, wooden voodoo mask with red feathers, "
                "wild pink hair, shamanistic bone mantle) lunges forward snatching the edge of the meter parchment, pointing an accusatory clawed finger "
                "with sharp narrowed orange eyes and a wicked grin. On the lower-right, the Undead Paladin recoils slightly with sudden nervous sweat drops. "
                "Generous pure #FFFFFF white headroom across the top 35%."
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
    
    script = EpisodeScript(
        episode_number=old["episode_number"],
        source_post_no=old["source_post_no"],
        source_title=old["source_title"],
        source_url=old["source_url"],
        subtitle=old["subtitle"],
        cuts=cuts
    )
    return ep, script


def upgrade_ep026():
    ep = "ep026"
    path = Path(f"data/episodes/{ep}/script.json")
    old = json.loads(path.read_text(encoding="utf-8"))
    
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
                "Over-the-shoulder (OTS) diagonal shot beside a minimalist campfire vignette. In the foreground right, the large back and shoulder "
                "of the Skyborne Mage frames the view. In the background left, the Undead Paladin girl (top-row #2: stitched skull hood, silver plate armor) "
                "leans back comfortably beside crackling orange campfire embers, gesturing with one bony hand and a nostalgic, worldly smile as she tells "
                "veteran war stories. Generous pure #FFFFFF white headroom across top 35%."
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
                "pupils shrunk to tiny dots and blue sweat drops flying, surrounded by dramatic dark shadow mob silhouettes of three looming Paladins "
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
                "Dynamic side-profile 90-degree action shot arranged across the lower frame. On the lower-left, the Skyborne Mage girl stares "
                "deadpan to the right with narrowed unamused eyes and a flat mouth, pointing her finger directly at the holy silver libram and "
                "holy warhammer strapped to the Paladin's belt. On the lower-right, the Undead Paladin flinches sideways with an awkward nervous sweat drop. "
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
    
    script = EpisodeScript(
        episode_number=old["episode_number"],
        source_post_no=old["source_post_no"],
        source_title=old["source_title"],
        source_url=old["source_url"],
        subtitle=old["subtitle"],
        cuts=cuts
    )
    return ep, script


def save_and_regenerate(ep: str, script: EpisodeScript):
    # Save script.json
    script_path = Path(f"data/episodes/{ep}/script.json")
    script_path.write_text(script.model_dump_json(indent=2), encoding="utf-8")
    
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
    print(f"Saved {ep} script.json and prompts.json")


if __name__ == "__main__":
    for func in [upgrade_ep023, upgrade_ep024, upgrade_ep025, upgrade_ep026]:
        ep, script = func()
        res = audit_script_quality(script, strict_cinematic=True)
        print(f"=== {ep} ===")
        print(f"Passed: {res['passed']}")
        print(f"Errors: {res['errors']}")
        print(f"Metrics: {res['cinematic_metrics']}")
        if not res["passed"]:
            print(f"Audit failed for {ep}!")
            exit(1)
        save_and_regenerate(ep, script)
    print("\nALL 4 BATCH 1 EPISODES SAVED & AUDITED SUCCESSFULLY!")
