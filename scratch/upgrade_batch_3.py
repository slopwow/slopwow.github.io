import json
from pathlib import Path
from wow_sloptoon.models import EpisodeScript, ComicCut
from wow_sloptoon.writer import audit_script_quality
from wow_sloptoon.artist import build_cut_image_prompt


def upgrade_ep031():
    ep = "ep031"
    path = Path(f"data/episodes/{ep}/script.json")
    old = json.loads(path.read_text(encoding="utf-8"))
    
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
    
    script = EpisodeScript(
        episode_number=old["episode_number"],
        source_post_no=old["source_post_no"],
        source_title=old["source_title"],
        source_url=old["source_url"],
        subtitle=old["subtitle"],
        cuts=cuts
    )
    return ep, script


def upgrade_ep032():
    ep = "ep032"
    path = Path(f"data/episodes/{ep}/script.json")
    old = json.loads(path.read_text(encoding="utf-8"))
    
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
    
    script = EpisodeScript(
        episode_number=old["episode_number"],
        source_post_no=old["source_post_no"],
        source_title=old["source_title"],
        source_url=old["source_url"],
        subtitle=old["subtitle"],
        cuts=cuts
    )
    return ep, script


def upgrade_ep033():
    ep = "ep033"
    path = Path(f"data/episodes/{ep}/script.json")
    old = json.loads(path.read_text(encoding="utf-8"))
    
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
                "Over-the-shoulder (OTS) diagonal shot. In the foreground right, the large shoulder and golden-aqua hair of the Skyborne Mage "
                "frames the view. In the background left, the Gnome Rogue girl (top-row #3: blonde pigtails with pink/blue tips, goggles, black cloak) "
                "holds up a glowing fantasy parchment portrait of a gorgeous ethereal fairy gnome priestess with golden halo sparkles, jumping with "
                "starry sparkling blue eyes and rosy cheeks. Generous pure #FFFFFF white headroom top 35%."
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
                "Dramatic low-angle shot looking up at the horrified Rogue. Centered comedic chest-up freeze-frame of the Gnome Rogue girl: "
                "her aviator goggles drooping crookedly, eyes turned into dizzying multi-ring spirals of sheer horror, lower jaw unhinged and "
                "dropping to her chest, a pale cartoon ghost soul floating from her open mouth in frozen buyer's remorse."
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
                "squinting with an awkward, sympathetic grimace and sweat drop. On the lower-right, the Gnome Rogue girl is on her knees clutching "
                "her face in agonizing despair. Generous pure #FFFFFF white headroom top 35%."
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
    
    script = EpisodeScript(
        episode_number=old["episode_number"],
        source_post_no=old["source_post_no"],
        source_title=old["source_title"],
        source_url=old["source_url"],
        subtitle=old["subtitle"],
        cuts=cuts
    )
    return ep, script


def upgrade_ep034():
    ep = "ep034"
    path = Path(f"data/episodes/{ep}/script.json")
    old = json.loads(path.read_text(encoding="utf-8"))
    
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
    for func in [upgrade_ep031, upgrade_ep032, upgrade_ep033, upgrade_ep034]:
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
    print("\nALL 4 BATCH 3 EPISODES SAVED & AUDITED SUCCESSFULLY!")
