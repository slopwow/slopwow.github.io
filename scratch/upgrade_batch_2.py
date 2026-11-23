import json
from pathlib import Path
from wow_sloptoon.models import EpisodeScript, ComicCut
from wow_sloptoon.writer import audit_script_quality
from wow_sloptoon.artist import build_cut_image_prompt


def upgrade_ep027():
    ep = "ep027"
    path = Path(f"data/episodes/{ep}/script.json")
    old = json.loads(path.read_text(encoding="utf-8"))
    
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
                "Over-the-shoulder (OTS) diagonal shot. In the foreground right, the large shoulder and back of the green plush hood of "
                "the Orc Warrior girl (top-row #1: black ponytail, spiky red pauldrons, carrying a sturdy steel shield on her arm) frames the scene, "
                "frowning with a twitching eyebrow in utter exasperation. In the background left, the Troll Shaman girl (middle-row #1: blue skin, "
                "voodoo skull mask with red feathers, wild pink hair) frantically spams a floating glowing yellow crosshair target ping icon in mid-air "
                "with rapid cartoon shockwave rings and multiple after-image hands. Generous pure #FFFFFF white headroom across top 35%."
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
    
    script = EpisodeScript(
        episode_number=old["episode_number"],
        source_post_no=old["source_post_no"],
        source_title=old["source_title"],
        source_url=old["source_url"],
        subtitle=old["subtitle"],
        cuts=cuts
    )
    return ep, script


def upgrade_ep028():
    ep = "ep028"
    path = Path(f"data/episodes/{ep}/script.json")
    old = json.loads(path.read_text(encoding="utf-8"))
    
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
                "Dynamic side-profile 90-degree action shot. Across the lower frame, five agile dark cartoon shadow raptor silhouettes with glowing "
                "yellow eyes rush past. On the lower-left, the Human Warlock girl (bottom-row #3: purple hood, black pigtails, violet eyes) flees "
                "sideways in utter panic, clutching her plump red plush imp doll with waterfall cartoon tears streaming and mouth open screaming for help. "
                "Generous pure #FFFFFF white headroom across top 35%."
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
                "Dramatic low-angle shot looking up. On the lower-left, the Human Warlock girl frantically waves an unrolled Dalaran scholarly scroll "
                "with furious pleading eyes, dark purple arcane sparkles, and dramatic comic sweat drops. On the lower-right in the background, the Orc "
                "Warrior tank unconcernedly polishes her sturdy steel shield with a deaf ear. Generous pure #FFFFFF white headroom top 35%."
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
    
    script = EpisodeScript(
        episode_number=old["episode_number"],
        source_post_no=old["source_post_no"],
        source_title=old["source_title"],
        source_url=old["source_url"],
        subtitle=old["subtitle"],
        cuts=cuts
    )
    return ep, script


def upgrade_ep029():
    ep = "ep029"
    path = Path(f"data/episodes/{ep}/script.json")
    old = json.loads(path.read_text(encoding="utf-8"))
    
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
                "swords and ring-mesh mail armor under her arm, casually tossing a savage boomer burn back over her shoulder with an unbothered smirk. "
                "On the lower-right, the Undead Paladin freezes in shocked stone stillness with jaw dropping. Generous pure white headroom top 35%."
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


def upgrade_ep030():
    ep = "ep030"
    path = Path(f"data/episodes/{ep}/script.json")
    old = json.loads(path.read_text(encoding="utf-8"))
    
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
                "Over-the-shoulder (OTS) diagonal shot. In the foreground right, the large shoulder and aqua-tipped hair of the Skyborne Mage "
                "frames the view, pointing with starry sparkling sapphire eyes toward a glowing azure intellect gemstone necklace hovering "
                "in mid-air with bright blue magic sparkles. In the background left, the Dwarf Hunter watches closely. Generous pure white headroom top 35%."
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
                "(simple black dot pips only, ZERO digits) onto the ground with a greedy mischievous toothy grin, snatching the glowing necklace into her paws. "
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
                "Dramatic low-angle shot looking up. The Dwarf Hunter girl stands tall tossing a chunky leather pouch overflowing with shiny silver "
                "coins up and down in her hand, grinning with cheeky carefree satisfaction and closed eyes, completely unapologetic for vendoring "
                "the intellect necklace for quick pocket money. Generous pure #FFFFFF white headroom across top 35%."
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
                "Dynamic back-view shot. On the lower-left, the Dwarf Hunter is seen from behind standing completely alone in the cold empty center, "
                "clutching her hunting musket as a tumbleweed rolls past. On the lower-right, the Troll Shaman girl walks away into the distance, "
                "waving a snarky goodbye back over her shoulder with a sharp toothy grin. Generous pure #FFFFFF white headroom top 35%."
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
    script_path = Path(f"data/episodes/{ep}/script.json")
    script_path.write_text(script.model_dump_json(indent=2), encoding="utf-8")
    
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
    for func in [upgrade_ep027, upgrade_ep028, upgrade_ep029, upgrade_ep030]:
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
    print("\nALL 4 BATCH 2 EPISODES SAVED & AUDITED SUCCESSFULLY!")
