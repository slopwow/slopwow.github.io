"""Unit tests for WoW Forever (2026 Classic+) lore bible, Clean Hand cast anchors,
artist/writer prompt upgrades, `audit_script_quality()`, and 40-episode site scaling.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image

from wow_sloptoon.artist import build_cut_image_prompt
from wow_sloptoon.cast import (
    CAST_BIBLE,
    CAST_BY_ID,
    build_character_anchors_block,
    format_cast_bible_for_writer,
    get_cast_by_faction,
)
from wow_sloptoon.models import ComicCut, EpisodeScript, GalleryPost, ItemTooltipSpec
from wow_sloptoon.site_builder import DC_GALLERY_WRITE_URL, build_static_site
from wow_sloptoon.wow_lore import (
    CLASSIC_DUNGEONS,
    WOW_FOREVER_NEW_DUNGEONS,
    build_cut_visual_lore_hints,
    build_wow_lore_guidance,
    detect_mentioned_dungeons,
    find_modern_slang_violations,
)
from wow_sloptoon.writer import audit_script_quality, build_dry_run_script, build_writer_prompt


def _make_clean_script(
    *,
    cuts: list[ComicCut] | None = None,
    subtitle: str = "크롤도크 보루 주문력 사슬 분쟁 — 100% 인던 상황극",
) -> EpisodeScript:
    default_cuts = [
        ComicCut(
            cut_index=1,
            aspect_ratio="4:3",
            layout_slot="top",
            characters=["트롤 주술사", "언데드 성기사"],
            speaker="트롤 주술사",
            dialogue="어? 주문력 붙은 사슬 허리띠 떴다!\n정술한테 딱인데!",
            wordless=False,
            visual_prompt=(
                "Medium waist-up 2.5-head chibi framing. Left: Troll Shaman smiling eagerly "
                "with empty hands reaching toward an ornate silver interlocking ring-mesh mail "
                "armor waist belt (NOT prison chains). Right: Undead Paladin eyeing the belt "
                "with her warhammer stowed on her back. Pure solid white #FFFFFF background."
            ),
            tail_target="left",
            item_tooltip=ItemTooltipSpec(item_name="속박의 사슬", quality="rare"),
        ),
        ComicCut(
            cut_index=2,
            aspect_ratio="16:9",
            layout_slot="bottom",
            characters=["언데드 성기사", "오크 전사"],
            speaker="언데드 성기사",
            dialogue="이중특성으로 신기 키우려고\n제가 입찰 눌렀습니다.",
            wordless=False,
            visual_prompt=(
                "Medium waist-up chibi framing. Left: Undead Paladin tossing a chunky white-and-gold "
                "6-sided loot die with classic round dot pips only (zero digits, zero letters). "
                "Right: Orc Warrior tanking with a 1H sword and sturdy steel kite shield blinking in disbelief. "
                "Pure solid white #FFFFFF background."
            ),
            tail_target="left",
        ),
        ComicCut(
            cut_index=3,
            aspect_ratio="4:3",
            layout_slot="top",
            characters=["트롤 주술사"],
            speaker=None,
            dialogue=None,
            wordless=True,
            visual_prompt=(
                "Centered chest-up close-up freeze-frame of Troll Shaman with trembling pinpoint "
                "pupils and cold sweat drop, speechless in comedic shock. Pure solid white #FFFFFF background."
            ),
            tail_target="center",
        ),
        ComicCut(
            cut_index=4,
            aspect_ratio="16:9",
            layout_slot="bottom",
            characters=["오크 전사", "트롤 주술사"],
            speaker="오크 전사",
            dialogue="무덤 이동 눌러야 되나...\n다음엔 전탱·정술끼리만 가자!",
            wordless=False,
            visual_prompt=(
                "Medium waist-up chibi framing. Left: Orc Warrior holding a sturdy steel shield and "
                "1H sword sighing with a sweat drop. Right: Troll Shaman slumping beside her with "
                "tiny crackling blue lightning sparks. Pure solid white #FFFFFF background."
            ),
            tail_target="left",
        ),
    ]
    return EpisodeScript(
        episode_number=11,
        source_post_no="108500",
        source_title="크롤도크 보루 사슬 허리띠 입찰 실화냐",
        source_url="https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=108500",
        subtitle=subtitle,
        cuts=cuts if cuts is not None else default_cuts,
    )


def test_wow_lore_covers_all_9_new_dungeons_classic_dungeons_and_core_systems() -> None:
    assert len(WOW_FOREVER_NEW_DUNGEONS) == 9
    new_names = {d.name for d in WOW_FOREVER_NEW_DUNGEONS}
    assert new_names == {
        "영주의 전당",
        "로데론의 폐허",
        "발굴 현장",
        "달라란",
        "가라앉은 도시",
        "크롤도크 보루",
        "알카즈 감옥",
        "검은아귀 요새",
        "구체자의 정원",
    }
    classic_names = {d.name for d in CLASSIC_DUNGEONS}
    for required in (
        "죽음의 폐광",
        "통곡의 동굴",
        "그림자송곳니 성채",
        "놈리건",
        "붉은십자군 수도원",
        "가시덩굴 구릉",
        "울다만",
        "줄파락",
        "마라우돈",
        "가라앉은 사원",
        "검은바위 나락",
        "검은바위 첨탑",
        "혈투의 전장",
        "스트라솔름",
        "스칼로맨스",
    ):
        assert required in classic_names

    guidance = build_wow_lore_guidance("크롤도크 보루에서 속박의 사슬이랑 상큼한 멜론 주스 썰")
    # Core WoW Forever systems
    for expected in (
        "스카이본",
        "Zephras Isle",
        "Walk on Air",
        "언데드 성기사",
        "오크 마법사",
        "트롤 흑마법사",
        "인간 사냥꾼",
        "드워프 주술사",
        "노움 사제",
        "이중 특성",
        "침낭퀘",
        "야영",
        "Legacy",
        "FindParty Forever",
        "MessageQueue Forever",
        "10인 공격대",
        "진영 통합",
    ):
        assert expected in guidance

    # Context-triggered dungeon & anti-hallucination warnings
    assert "크롤도크 보루" in guidance
    assert "링메일" in guidance
    assert "코르크 마개 유리 물약병" in guidance

    # Outdoor zone faction detection
    dolanaar_guidance = build_wow_lore_guidance("침낭퀘 하다가 돌라나르 귀환석 탔음")
    assert "얼라이언스 전용 야외/대도시 감지" in dolanaar_guidance
    assert "돌라나르" in dolanaar_guidance

    barrens_guidance = build_wow_lore_guidance("불모의 땅 십자로 귀환석 타고 오그리마 갔음")
    assert "호드 전용 야외/대도시 감지" in barrens_guidance

    # Dungeon detection helper
    found_dungeons = [d.name for d in detect_mentioned_dungeons("알카즈 감옥이랑 구체자의 정원 돌았음")]
    assert "알카즈 감옥" in found_dungeons
    assert "구체자의 정원" in found_dungeons


def test_build_cut_visual_lore_hints_injects_targeted_anti_hallucination_rules() -> None:
    mail_hints = build_cut_visual_lore_hints(
        "Paladin snatches Chain of Binding mail waist belt while rolling loot dice.",
        ["언데드 성기사", "트롤 주술사"],
    )
    assert "MAIL ARMOR RULE" in mail_hints
    assert "NEVER draw literal metal prison chains" in mail_hints
    assert "LOOT DIE RULE" in mail_hints
    assert "ZERO Arabic digits" in mail_hints

    drink_hints = build_cut_visual_lore_hints(
        "Warlock hands over refreshing melon juice to the exhausted priest.",
        ["인간 흑마법사", "나이트엘프 사제"],
    )
    assert "FANTASY DRINK & POTION RULE" in drink_hints
    assert "juice cartons" in drink_hints

    tank_hints = build_cut_visual_lore_hints(
        "Orc Warrior protection tank blocking the boss.",
        ["오크 전사"],
    )
    assert "TANK SHIELD RULE" in tank_hints
    assert "ONE-HANDED weapon" in tank_hints

    skyborne_hints = build_cut_visual_lore_hints(
        "Skyborne Mage casting polymorph sheep next to a glowing hearthstone.",
        ["스카이본 마법사"],
    )
    assert "SKYBORNE HERITAGE ACCENT" in skyborne_hints
    assert "POLYMORPH EFFECT" in skyborne_hints
    assert "HEARTHSTONE RULE" in skyborne_hints


def test_cast_clean_hand_anchors_and_factions_backward_compatible() -> None:
    assert len(CAST_BIBLE) == 9
    assert {m.id for m in get_cast_by_faction("Horde")} == {
        "orc_warrior",
        "undead_paladin",
        "troll_shaman",
        "tauren_druid",
    }
    assert {m.id for m in get_cast_by_faction("Alliance")} == {
        "gnome_rogue",
        "dwarf_hunter",
        "nightelf_priest",
        "human_warlock",
    }
    assert {m.id for m in get_cast_by_faction("Neutral-Skyborne")} == {"skyborne_mage"}

    for member in CAST_BIBLE:
        assert member.appearance_anchor.strip()
        assert member.default_prop.strip()
        # Permanent appearance anchor must NOT hardcode permanently holding weapons/drinks/dolls
        lower_app = member.appearance_anchor.lower()
        assert "holding a" not in lower_app, f"{member.id} appearance_anchor still hardcodes holding prop"
        assert "hugging a" not in lower_app, f"{member.id} appearance_anchor still hardcodes hugging prop"
        assert "dual glowing" not in lower_app, f"{member.id} appearance_anchor still hardcodes dual daggers"
        # Backward-compatible visual_anchor still works
        assert member.appearance_anchor in member.visual_anchor
        assert member.default_prop in member.visual_anchor

    # Skyborne Mage default prop is separated & includes feather lore note + crystal staff
    sky = CAST_BY_ID["skyborne_mage"]
    assert "feather" in sky.appearance_anchor.lower() or "feather" in sky.lore_note.lower()
    assert "sky-blue diamond crystal" in sky.default_prop.lower()
    assert "polymorph sheep" in sky.appearance_anchor.lower()
    # Night Elf Priest uses purple vestments, Holy Tome & Rosary, and zero halo/wings
    priest = CAST_BY_ID["nightelf_priest"]
    assert "mini holy prayer book" in priest.appearance_anchor.lower()
    assert "rosary" in priest.appearance_anchor.lower()
    assert "holy cross" in priest.default_prop.lower()

    anchors = build_character_anchors_block(["스카이본 마법사", "오크 전사"])
    assert "CLEAN HAND RULE" in anchors
    assert "Optional default prop" in anchors
    assert "Skyborne lore note" in anchors
    assert "Zephras Isle" in anchors

    writer_bible = format_cast_bible_for_writer()
    assert "Clean Hand Rule" in writer_bible
    assert "얼라이언스" in writer_bible
    assert "호드" in writer_bible


def test_writer_and_artist_prompts_enforce_scale_clean_hand_and_lore() -> None:
    post = GalleryPost(
        post_no="109001",
        title="크롤도크 보루 전탱 방패 어디감?",
        url="https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=109001",
        author="포에버갤러",
        date_str="2026-11-23",
        body="전탱이 방패 안 끼고 속박의 사슬까지 입찰함 ㅋㅋ",
        comments=["보기였으면 방패라도 들었지"],
    )
    w_prompt = build_writer_prompt(post, episode_number=11)
    assert "핵심 1~4명" in w_prompt
    assert "괄호 다중 화자 편법 절대 금지" in w_prompt
    assert "3~3.5등신" in w_prompt
    assert "념글을 안 읽고도" in w_prompt
    assert "크롤도크 보루" in w_prompt
    assert "119" in w_prompt  # cited as forbidden modern phrasing rule

    # 16:9 2-character panel prompt enforces sleek 3-to-3.5 head scale, Clean Hand & WoW lore rules
    two_char_16_9_cut = ComicCut(
        cut_index=2,
        aspect_ratio="16:9",
        layout_slot="bottom",
        characters=["오크 전사", "노움 도적"],
        speaker="오크 전사",
        dialogue="한손검 장트라제는 전탱 1티어지!",
        wordless=False,
        visual_prompt=(
            "Orc Warrior protection tank equipping a steel shield and 1H sword while "
            "Gnome Rogue eyes a compact one-handed sword."
        ),
        tail_target="left",
    )
    art_prompt = build_cut_image_prompt(two_char_16_9_cut)
    assert "CLEAN HAND RULE" in art_prompt
    assert "3-to-3.5 head" in art_prompt
    assert "TANK SHIELD RULE" in art_prompt
    assert "WEAPON SCALE & CLEAN HAND RULE" in art_prompt
    assert "zero digits/numbers" in art_prompt.lower()


def test_audit_script_quality_passes_clean_script_and_dry_run() -> None:
    clean = _make_clean_script()
    report = audit_script_quality(clean, forbidden_names=["악질유저닉", "먹튀길드"])
    assert report["passed"] is True, f"Unexpected errors: {report['errors']}"
    assert report["errors"] == []
    assert all(report["checks"].values())
    assert report["unique_cast_count"] == 3

    post = GalleryPost(
        post_no="99002",
        title="포에버갤 드라이런 테스트",
        url="https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=99002",
        author="테스터",
        date_str="2026-11-23",
        body="던전 상황극 테스트 본문입니다.",
    )
    dry_report = audit_script_quality(build_dry_run_script(post, episode_number=12))
    assert dry_report["passed"] is True


def test_audit_script_quality_catches_all_ep1_to_ep10_flaws() -> None:
    # 1. Parenthetical dual-speaker hack `(도적: ...)` & `(사제: ...)` (while allowing `(20:06)` timestamp)
    base = _make_clean_script()
    dual_cuts = list(base.cuts)
    dual_cuts[0] = dual_cuts[0].model_copy(
        update={
            "dialogue": "주시면 안 되나요 ㅠㅠ\n(도적: 저도 이거 보고 온 거라서 지송지송~)"
        }
    )
    rep_dual = audit_script_quality(base.model_copy(update={"cuts": dual_cuts}))
    assert rep_dual["passed"] is False
    assert rep_dual["checks"]["no_dual_speaker_hack"] is False

    # Timestamp `(20:06)` must NOT false-positive as a dual-speaker hack
    ts_cuts = list(base.cuts)
    ts_cuts[0] = ts_cuts[0].model_copy(update={"dialogue": "아까 (20:06) 로그 보니까 다 찍혔네!"})
    rep_ts = audit_script_quality(base.model_copy(update={"cuts": ts_cuts}))
    assert rep_ts["checks"]["no_dual_speaker_hack"] is True

    # 2. Cast sprawl (5 unique cast members across 4 cuts -> > 4 max)
    sprawl_cuts = [
        base.cuts[0].model_copy(update={"characters": ["오크 전사", "언데드 성기사"], "speaker": "오크 전사"}),
        base.cuts[1].model_copy(update={"characters": ["노움 도적", "드워프 사냥꾼"], "speaker": "노움 도적"}),
        base.cuts[2].model_copy(update={"characters": ["스카이본 마법사"]}),
        base.cuts[3].model_copy(update={"characters": ["타우렌 드루이드"], "speaker": "타우렌 드루이드"}),
    ]
    rep_sprawl = audit_script_quality(base.model_copy(update={"cuts": sprawl_cuts}))
    assert rep_sprawl["passed"] is False
    assert rep_sprawl["checks"]["cast_focus_ok"] is False
    assert rep_sprawl["unique_cast_count"] == 6

    # 3. Modern slang (`119 불러야 되나`)
    assert find_modern_slang_violations("119 불러야 되나 ㅋㅋ")
    slang_cuts = list(base.cuts)
    slang_cuts[3] = slang_cuts[3].model_copy(update={"dialogue": "이거 119 불러야 되나?!"})
    rep_slang = audit_script_quality(base.model_copy(update={"cuts": slang_cuts}))
    assert rep_slang["passed"] is False
    assert rep_slang["checks"]["no_modern_slang"] is False

    # 4. Faction / outdoor zone mismatch (Tauren Druid Horde claiming Dolanaar Alliance hearthstone!)
    faction_cuts = list(base.cuts)
    faction_cuts[0] = faction_cuts[0].model_copy(
        update={
            "characters": ["타우렌 드루이드", "언데드 성기사"],
            "speaker": "타우렌 드루이드",
            "dialogue": "어? 귀환석 탔는데 저 귀환지가 돌라나르예요!",
        }
    )
    rep_faction = audit_script_quality(base.model_copy(update={"cuts": faction_cuts}))
    assert rep_faction["passed"] is False
    assert rep_faction["checks"]["faction_zone_ok"] is False

    # 5. Tanking Warrior holding 2H battle axe with NO shield
    tank_cuts = list(base.cuts)
    tank_cuts[1] = tank_cuts[1].model_copy(
        update={
            "characters": ["오크 전사"],
            "speaker": "오크 전사",
            "dialogue": "제가 전탱인데 어글 다 잡아요!",
            "visual_prompt": "Orc Warrior tanking boldly while holding a giant battle axe on pure #FFFFFF white background.",
        }
    )
    rep_tank = audit_script_quality(base.model_copy(update={"cuts": tank_cuts}))
    assert rep_tank["passed"] is False
    assert rep_tank["checks"]["tank_shield_ok"] is False

    # 6. Anonymity leaks (forbidden nickname + `<길드명>` tag + forbidden community `인벤`)
    anon_cuts = list(base.cuts)
    anon_cuts[0] = anon_cuts[0].model_copy(
        update={"dialogue": "<전설길드> 철수전사님 인벤 사사게 갑니다!"}
    )
    rep_anon = audit_script_quality(
        base.model_copy(update={"cuts": anon_cuts}),
        forbidden_names=["철수전사"],
    )
    assert rep_anon["passed"] is False
    assert rep_anon["checks"]["anonymity_ok"] is False
    assert rep_anon["checks"]["no_forbidden_community"] is False

    # 7. Literal visual anti-hallucination trap (`juice box` requested affirmatively vs negated)
    trap_cuts = list(base.cuts)
    trap_cuts[0] = trap_cuts[0].model_copy(
        update={"visual_prompt": "Warlock holding a convenience-store juice box with a plastic straw."}
    )
    rep_trap = audit_script_quality(base.model_copy(update={"cuts": trap_cuts}))
    assert rep_trap["passed"] is False
    assert rep_trap["checks"]["visual_prompt_clean"] is False

    negated_cuts = list(base.cuts)
    negated_cuts[0] = negated_cuts[0].model_copy(
        update={"visual_prompt": "Warlock holding a fantasy glass potion vial (NOT a juice box, NO plastic straw)."}
    )
    rep_neg = audit_script_quality(base.model_copy(update={"cuts": negated_cuts}))
    assert rep_neg["checks"]["visual_prompt_clean"] is True


def test_site_builder_scales_cleanly_to_40_episodes(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    episodes_payload = []
    for n in range(1, 41):
        ep_id = f"ep{n:03d}"
        ep_dir = data_dir / "episodes" / ep_id
        ep_dir.mkdir(parents=True)
        img = Image.new("RGB", (800, 500), (255, 255, 255))
        img.save(ep_dir / "episode_full.jpg", format="JPEG")
        img.save(ep_dir / "thumb.jpg", format="JPEG")
        img.save(ep_dir / "page_1.png", format="PNG")
        episodes_payload.append(
            {
                "episode_id": ep_id,
                "episode_number": n,
                "title": f"포에버갤 레전드 인던 사건 {n}화",
                "subtitle": f"{n}화 상황극 한줄 요약",
                "source_post_no": str(100000 + n),
                "source_url": f"https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no={100000 + n}",
                "created_at": f"2026-11-{(n % 28) + 1:02d}T12:00:00+09:00",
                "cut_count": 5,
                "cast_used": ["오크 전사", "스카이본 마법사"],
                "full_image_rel": f"data/episodes/{ep_id}/episode_full.jpg",
                "thumb_image_rel": f"data/episodes/{ep_id}/thumb.jpg",
                "page_images_rel": [f"data/episodes/{ep_id}/page_1.png"],
            }
        )

    episodes_json = data_dir / "episodes.json"
    episodes_json.write_text(json.dumps(episodes_payload, ensure_ascii=False), encoding="utf-8")
    empty_assets = tmp_path / "assets"
    empty_assets.mkdir()
    out_site = tmp_path / "site"

    build_static_site(episodes_json, out_site, empty_assets)

    assert not (out_site / "publish.html").exists()

    # Home page: pagination controls, lazy + async decoding + explicit dimensions, back-to-top
    index_html = (out_site / "index.html").read_text(encoding="utf-8")
    assert 'id="loadMoreWrap"' in index_html
    assert 'id="loadMoreBtn"' in index_html
    assert 'id="showAllBtn"' in index_html
    assert 'id="backToTopBtn"' in index_html
    assert 'width="800" height="500" loading="lazy" decoding="async"' in index_html
    assert "총 <strong>40</strong>화 아카이브" in index_html

    # Cast page: inline appearance list capped to 5 + '+ 외 35화 더 있음' badge + faction labels
    cast_html = (out_site / "cast.html").read_text(encoding="utf-8")
    assert "+ 외 35화 더 있음" in cast_html
    assert "오크 · 전사 · 호드" in cast_html
    assert "스카이본 · 마법사 · 스카이본" in cast_html
    assert "출연 에피소드 (40화)" in cast_html

    # Episode reader page: quick jump dropdown has all 40 options & embedded JSON trims non-active page_images
    ep40_html = (out_site / "episodes" / "ep040.html").read_text(encoding="utf-8")
    assert 'id="epJumpSelect"' in ep40_html
    assert len(re.findall(r"<option value=\"ep\d{3}\"", ep40_html)) == 40
    m_data = re.search(r"window\.__SLOPTOON_DATA__\s*=\s*(\{.*?\});</script>", ep40_html)
    assert m_data is not None
    embedded = json.loads(m_data.group(1))
    by_id = {e["episode_id"]: e for e in embedded["episodes"]}
    assert "page_images" in by_id["ep040"]
    assert "page_images" not in by_id["ep001"]

    # Zero DC write URLs, zero admin UI, zero Inven mentions across ALL generated files
    for generated in out_site.rglob("*"):
        if generated.is_file() and generated.suffix.lower() in {".html", ".css", ".js", ".xml", ".txt", ".json"}:
            body = generated.read_text(encoding="utf-8")
            assert DC_GALLERY_WRITE_URL not in body
            assert "publish.html" not in body
            assert "인벤" not in body
            assert "inven" not in body.lower(), f"Forbidden 'inven' substring in {generated}"


def test_cinematic_variety_rules_and_strict_audit() -> None:
    # Artist prompt and cast anchors enforce sleek 3–3.5 head style-first re-proportioning & dynamic acting
    anchors = build_character_anchors_block(["언데드 성기사", "드워프 사냥꾼"])
    assert "PROPORTIONS & STYLE FIRST" in anchors
    assert "3-to-3.5 head" in anchors
    assert "COSTUME, HAIR, HEADGEAR & COLOR IDENTITY ONLY" in anchors

    sample_cut = ComicCut(
        cut_index=1,
        aspect_ratio="4:3",
        layout_slot="top",
        characters=["오크 전사", "노움 도적"],
        speaker="노움 도적",
        dialogue="전탱님 뒤 좀 보세요!",
        wordless=False,
        visual_prompt=(
            "Dynamic over-the-shoulder diagonal shot: foreground back of Orc Warrior's shoulder with "
            "steel shield, background Gnome Rogue crouching low on a dungeon crate grinning smugly."
        ),
        tail_target="right",
    )
    art_prompt = build_cut_image_prompt(sample_cut)
    assert "3-to-3.5 head" in art_prompt
    assert "over-the-shoulder" in art_prompt.lower()

    # Flat side-by-side talking-heads script fails strict_cinematic=True
    flat_script = _make_clean_script()
    flat_cuts = [
        c.model_copy(
            update={
                "visual_prompt": (
                    "On the lower-left Troll Shaman stands smiling. On the lower-right Undead Paladin stands talking."
                    if not c.wordless
                    else "Centered face close-up."
                )
            }
        )
        for c in flat_script.cuts
    ]
    rep_flat = audit_script_quality(flat_script.model_copy(update={"cuts": flat_cuts}), strict_cinematic=True)
    assert rep_flat["passed"] is False
    assert rep_flat["checks"]["cinematic_variety_ok"] is False

    # Varied cinematic script passes strict_cinematic=True
    cinematic_prompts = [
        "Dynamic over-the-shoulder diagonal shot: foreground shoulder of Undead Paladin, background Troll Shaman leaning forward over an open loot chest reaching for a silver interlocking ring-mesh mail armor waist belt (NOT prison chains).",
        "Low-angle dramatic shot looking up at Undead Paladin tossing a dot-pip loot die while Orc Warrior tank with 1H sword and steel shield dives sideways in panic.",
        "Dutch-tilt tight freeze-frame close-up of Troll Shaman jaw-dropped with soul floating out of her mouth.",
        "High-angle view looking down at Troll Shaman kneeling on the floor in despair while Orc Warrior tank (shield + 1H sword) walks away seen from behind waving goodbye.",
    ]
    dyn_cuts = [c.model_copy(update={"visual_prompt": vp}) for c, vp in zip(flat_script.cuts, cinematic_prompts)]
    rep_dyn = audit_script_quality(flat_script.model_copy(update={"cuts": dyn_cuts}), strict_cinematic=True)
    assert rep_dyn["passed"] is True, f"Unexpected strict cinematic errors: {rep_dyn['errors']}"
    assert rep_dyn["checks"]["cinematic_variety_ok"] is True

