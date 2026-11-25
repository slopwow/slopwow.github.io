"""Comic cut illustrator powered by Google GenAI Interactions API (`gemini-nano-banana-2.1`).

Generates Draft C cute pop-gag chibi cuts and V4 5-act 2K multi-panel pages using the official
Draft C cast sheet, the sloptoon style reference, exact layout blueprints, and per-character
3-view turnaround blueprints (ZERO fixed expression sheets) with strict Identity-vs-Acting
decoupling, unleashed expressive acting, bold cinematic cameras, 3-Tier Smart Backgrounds,
and WoW Forever visual anti-hallucination guardrails.
"""

from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor
import io
import mimetypes
from pathlib import Path
from typing import Any

from google import genai
from PIL import Image, ImageDraw

from wow_sloptoon.cast import build_character_anchors_block, get_turnaround_paths
from wow_sloptoon.config import (
    DEFAULT_IMAGE_MODEL,
    SUPPORTED_IMAGE_MODELS,
    Settings,
    load_settings,
)
from wow_sloptoon.layouts import (
    V4_ASPECT_RATIO,
    get_page_layout,
    render_layout_blueprint,
)
from wow_sloptoon.models import ActPage, BackgroundStyle, ComicCut, EpisodeScript
from wow_sloptoon.wow_lore import build_cut_visual_lore_hints


def _guess_mime_type(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(str(path))
    if guessed:
        return guessed
    if path.suffix.lower() == ".png":
        return "image/png"
    return "image/jpeg"


def _encode_image_base64(path: Path) -> tuple[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"Reference image asset not found: {path}")
    raw = path.read_bytes()
    return base64.b64encode(raw).decode("ascii"), _guess_mime_type(path)


def _encode_pil_image_png_base64(im: Image.Image) -> tuple[str, str]:
    """Encode an in-memory PIL image as lossless PNG base64 for Gemini Interactions input."""
    buf = io.BytesIO()
    im.convert("RGB").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii"), "image/png"


def build_cut_image_prompt(
    cut: ComicCut,
    *,
    attached_turnarounds: list[str] | None = None,
) -> str:
    """Construct the exact image-generation prompt with Draft C Clean Hand anchors & 3-view turnaround refs."""
    anchors = build_character_anchors_block(cut.characters)
    lore_hints = build_cut_visual_lore_hints(cut.visual_prompt, cut.characters)

    turnaround_ref_note = ""
    if attached_turnarounds:
        ref_lines = [
            f"- Reference Image {idx}: 3-View Front/Side/Back Turnaround Blueprint for {label} — "
            "IDENTITY & COSTUME LOCK ONLY (match ONLY hair, headgear, outfit, waist charms, boots, "
            "eye color, Clean Hand weapon stowing, thin variable-width ink linework, and 2-tier cel "
            "shading; STRICTLY IGNORE the sheet's calm neutral standing pose and generic polite smile/wink!)"
            for idx, label in enumerate(attached_turnarounds, start=3)
        ]
        turnaround_ref_note = "\nATTACHED CHARACTER 3-VIEW TURNAROUND BLUEPRINTS:\n" + "\n".join(ref_lines) + "\n"

    if cut.wordless:
        framing_note = (
            "COMPOSITION & CAMERA: Expressive solo comedic close-up or dramatic gag freeze-frame "
            "(silent panel; character fills ~72-88% of canvas height). Actively honor extreme cameras "
            "requested in Scene Action (extreme face close-up, fisheye forced-perspective lunging "
            "toward camera, dizzying bird's-eye top-down, low-angle loom, 30° Dutch tilt) — break stiff "
            "symmetry with jaw-drop, soul-leaving-body, pinpoint pupils, or crumpled despair. "
            "No room needed for speech bubbles."
        )
    elif cut.layout_slot == "top":
        framing_note = (
            "COMPOSITION & CAMERA: Open top-slot 4:3 comic panel inspired by Reference Image 2's dynamic "
            "webtoon energy! Actively honor bold cameras in Scene Action (extreme face close-up, fisheye "
            "forced-perspective lunging toward camera, dizzying bird's-eye top-down, low-angle loom, "
            "30° Dutch tilt, over-the-shoulder, or physical slapstick — NEVER stiff flat front-facing "
            "standing talk-show dolls!). Keep ONLY the top 30-35% pure solid white (#FFFFFF) headroom "
            "uncluttered for external speech-bubble placement while letting the character(s) fill the "
            "lower two-thirds boldly at expressive 2.5-to-3-head chibi scale (do NOT shrink dramatic "
            "close-ups or tilted action into tiny distant full-body micro-chibis!). "
            f"Primary speaker position cue: {cut.tail_target}."
        )
    elif len(cut.characters) >= 2:
        framing_note = (
            "COMPOSITION & CAMERA: Wide bottom-slot 16:9 two-character reaction or action panel. "
            "Actively honor bold cameras in Scene Action (over-the-shoulder, fisheye forced perspective, "
            "diagonal chase, 30° Dutch tilt, low-angle loom, crouching/sprawling slapstick, or back-view "
            "— NEVER flat identical front-facing standing mannequins!). Frame BOTH characters boldly at "
            "expressive 2.5-to-3-head chibi scale (NEVER zoom out into tiny distant full-body "
            "micro-chibis!) in the lower two-thirds or speaker-side half while keeping ONLY the upper "
            "or opposite-side pure solid white (#FFFFFF) bubble headroom uncluttered. "
            f"Primary speaker position cue: {cut.tail_target}."
        )
    else:
        framing_note = (
            "COMPOSITION & CAMERA: Wide bottom-slot 16:9 solo action or expressive reaction panel. "
            "Actively honor bold cameras in Scene Action (extreme face close-up, fisheye lunge toward "
            "camera, low-angle loom, 30° Dutch tilt, bird's-eye top-down, leaning, dashing, crouching, "
            "sprawling — NEVER a static front passport pose!). Frame boldly at expressive 2.5-to-3-head "
            "chibi scale (do NOT shrink dramatic close-ups into tiny stiff full-body micro-chibis!) "
            "positioned cleanly toward the speaker side while keeping ONLY the upper or opposite-side "
            "pure solid white (#FFFFFF) bubble headroom uncluttered. "
            f"Primary speaker position cue: {cut.tail_target}."
        )

    return (
        "Draw a single lively, cinematic Korean pop-gag 2.5-to-2.8 head anime chibi comic cut "
        "with STRICT IDENTITY vs UNLEASHED ACTING DECOUPLING: match ONLY character design identity "
        "(hair, headgear, outfit, waist charms, boots, eye color, Clean Hand weapon stowing, thin "
        "variable-width ink linework, and crisp 2-tier cel shading) from Reference Image 1 (Draft C "
        "9-Cast Master Sheet) and any attached individual 3-view character turnaround blueprints "
        "(Reference Images 3+), while unleashing the bold webtoon camera energy, wild manga gag "
        "acting, and crisp white-canvas punch of Reference Image 2 (Sloptoon Style Reference).\n"
        f"{turnaround_ref_note}\n"
        f"{anchors}\n\n"
        f"SCENE ACTION, EXPRESSION & CAMERA (Cut #{cut.cut_index}):\n{cut.visual_prompt.strip()}\n\n"
        f"{lore_hints}\n\n"
        f"{framing_note}\n\n"
        "CINEMATIC ACTING, FAITHFUL SCENE RECREATION & EXTRAS:\n"
        "- STRICT IDENTITY vs UNLEASHED ACTING DECOUPLING (BREAK THE PRETTY-FACE SAFETY ZONE!): "
        "Reference images lock IDENTITY ONLY (costume/hair/headgear/eye color/linework) — NEVER copy "
        "Reference Image 1's or the turnaround sheet's calm neutral standing pose or generic polite "
        "smile/wink! Push wild, infinitely varied, scene-specific anime gag acting: dramatic eye-size "
        "shifts (pinpoint psychotic pupils, huge sparkling jewel eyes, empty white shock eyes, spiral "
        "dizzy eyes, crying waterfalls, unimpressed deadpan half-lids), extreme mouths (jaw-dropped "
        "screaming, smug cat `:3`, mischievous gremlin grin, shaky panic squiggle), forehead gloom "
        "shadows, comedic squash-and-stretch body distortion, dynamic leaning/lunging/crouching/"
        "sprawling/mid-air motion, and expressive hand acting!\n"
        "- FAITHFUL IN-GAME RECREATION (EXTRAS, CROWDS, CORPSES & MOBS WELCOME): Do NOT restrict a "
        "scene to only 1–2 starring characters talking in a void! Whenever the scene action calls for "
        "extra players, crowds, comedic cartoon skeletons/knocked-out lowbie corpses piled on the "
        "ground (cute manga/chibi gag style ONLY, zero realistic blood/gore), dungeon mobs, bosses, "
        "NPCs, guards, pets, or mounts, draw them vividly in the same cute Draft C anime art style!\n"
        "- Keep the outer canvas edges 100% pure solid #FFFFFF white (NO full-bleed sky/room walls "
        "blocking bubble headroom), WHILE rendering crisp minimalist in-game action vignette props "
        "and ground details attached directly to the characters' action (e.g., pile of cartoon "
        "skeletons/fallen players, wooden loot chest, campfire embers, glowing hearthstone vortex, "
        "ship rail edge, tavern table, flying dust puffs, comic speed lines, spell arcs, dungeon mobs) "
        "so the scene faithfully recreates the real WoW Forever moment!\n\n"
        "ABSOLUTE TECHNICAL REQUIREMENTS:\n"
        "- 100% PURE SOLID WHITE (#FFFFFF) OUTER BACKGROUND ONLY — zero room backdrops, zero gray "
        "shading gradients, zero full-bleed scenery, zero ground shadows outside tiny contact lines.\n"
        "- ZERO HORIZONTAL DIVIDER LINES, ZERO STRAIGHT BLACK RULES, ZERO PANEL BORDERS OR BOXES "
        "ANYWHERE ON THE CANVAS — characters and any minimal ground/prop vignette must float "
        "organically inside pure #FFFFFF white space with NO black line separating top headroom!\n"
        "- ZERO TEXT, ZERO KOREAN/ENGLISH LETTERS, ZERO DIGITS/NUMBERS, ZERO SPEECH BUBBLES, "
        "ZERO SOUND EFFECTS, ZERO WATERMARKS.\n"
        "- Match every character's exact hood, horns/ears, hair color/gradient, eye color, and "
        "outfit from Reference Image 1 with 100% visual consistency; HOWEVER, obey the CLEAN HAND "
        "RULE — sheath/stow on back or waist, or omit a character's default weapon/prop whenever "
        "holding scene-specific loot, a tank shield, a loot die, a hearthstone, a potion flask, "
        "or gesturing (NEVER draw 3+ weapons/props in one character's hands).\n"
        "- CONSISTENT EXPRESSIVE CHIBI SCALE: Maintain 2.5-to-3-head chibi proportions across both "
        "4:3 and 16:9 cuts — honor bold close-ups and tilted angles freely, and NEVER shrink "
        "characters into tiny stiff distant micro-chibis."
    )


def _extract_image_bytes(interaction: Any) -> bytes:
    """Extract raw image bytes from a google-genai Interactions API image response."""
    output_image = getattr(interaction, "output_image", None)
    if output_image is not None:
        data = getattr(output_image, "data", None)
        if isinstance(data, bytes):
            return data
        if isinstance(data, str) and data.strip():
            return base64.b64decode(data)

    outputs = getattr(interaction, "outputs", None)
    if outputs:
        for item in reversed(outputs):
            item_type = getattr(item, "type", None) or (
                item.get("type") if isinstance(item, dict) else None
            )
            data = getattr(item, "data", None) or (
                item.get("data") if isinstance(item, dict) else None
            )
            if item_type == "image" and data:
                return data if isinstance(data, bytes) else base64.b64decode(data)

    raise ValueError("Gemini Interactions API response did not contain image output data.")


def _save_image_bytes(img_bytes: bytes, target_path: Path) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(img_bytes)
    return target_path


def resolve_image_model(model: str | None, settings: Settings) -> str:
    """Resolve and validate the selected Gemini image generation model."""
    selected = (model or settings.image_model or DEFAULT_IMAGE_MODEL).strip()
    if selected not in SUPPORTED_IMAGE_MODELS:
        allowed = ", ".join(SUPPORTED_IMAGE_MODELS)
        raise ValueError(
            f"Unsupported image model '{selected}'. Supported models: {allowed}"
        )
    return selected


def generate_cut_image(
    cut: ComicCut,
    output_path: Path,
    *,
    client: Any | None = None,
    settings: Settings | None = None,
    model: str | None = None,
    image_size: str = "1K",
) -> Path:
    """Generate a single pure-#FFFFFF comic cut image via Gemini Interactions API."""
    cfg = settings or load_settings()
    target_model = resolve_image_model(model, cfg)

    if client is None:
        if not cfg.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Configure GEMINI_API_KEY in .env or environment."
            )
        client = genai.Client(api_key=cfg.gemini_api_key)

    cast_b64, cast_mime = _encode_image_base64(cfg.cast_sheet_path)
    style_b64, style_mime = _encode_image_base64(cfg.style_ref_path)
    turnaround_pairs = get_turnaround_paths(cut.characters, cfg.turnarounds_dir)
    prompt = build_cut_image_prompt(
        cut,
        attached_turnarounds=[f"{m.name} ({m.id})" for m, _ in turnaround_pairs],
    )

    input_items: list[dict[str, Any]] = [
        {"type": "text", "text": prompt},
        {"type": "image", "data": cast_b64, "mime_type": cast_mime},
        {"type": "image", "data": style_b64, "mime_type": style_mime},
    ]
    for _member, turnaround_path in turnaround_pairs:
        t_b64, t_mime = _encode_image_base64(turnaround_path)
        input_items.append({"type": "image", "data": t_b64, "mime_type": t_mime})

    interaction = client.interactions.create(
        model=target_model,
        input=input_items,
        response_format={
            "type": "image",
            "aspect_ratio": cut.aspect_ratio,
            "image_size": image_size,
        },
    )

    img_bytes = _extract_image_bytes(interaction)
    return _save_image_bytes(img_bytes, output_path)


def generate_episode_cuts(
    script: EpisodeScript,
    output_dir: Path,
    *,
    client: Any | None = None,
    settings: Settings | None = None,
    model: str | None = None,
    image_size: str = "1K",
) -> dict[int, Path]:
    """Generate raw cut images for all 4~6 cuts in an `EpisodeScript`."""
    cfg = settings or load_settings()
    target_model = resolve_image_model(model, cfg)

    if client is None:
        if not cfg.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Configure GEMINI_API_KEY in .env or environment."
            )
        client = genai.Client(api_key=cfg.gemini_api_key)

    output_dir.mkdir(parents=True, exist_ok=True)
    cut_paths: dict[int, Path] = {}
    for cut in script.cuts:
        out_path = output_dir / f"cut_{cut.cut_index:02d}.png"
        cut_paths[cut.cut_index] = generate_cut_image(
            cut,
            out_path,
            client=client,
            settings=cfg,
            model=target_model,
            image_size=image_size,
        )
    return cut_paths


def render_dry_run_cuts(script: EpisodeScript, output_dir: Path) -> dict[int, Path]:
    """Create clean pure-#FFFFFF placeholder cut images for offline `--dry-run` testing."""
    output_dir.mkdir(parents=True, exist_ok=True)
    cut_paths: dict[int, Path] = {}
    for cut in script.cuts:
        size = (1024, 768) if cut.aspect_ratio == "4:3" else (1280, 720)
        img = Image.new("RGB", size, (255, 255, 255))
        draw = ImageDraw.Draw(img)
        w, h = size
        # Draw a neat minimal character silhouette placeholder in the lower-center area
        cx = w // 2
        if cut.tail_target == "left" and not cut.wordless:
            cx = int(w * 0.35)
        elif cut.tail_target == "right" and not cut.wordless:
            cx = int(w * 0.65)
        cy = int(h * 0.68) if not cut.wordless else int(h * 0.52)
        r = min(w, h) // 6
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(224, 242, 254), outline=(30, 41, 59), width=4)
        out_path = output_dir / f"cut_{cut.cut_index:02d}.png"
        img.save(out_path, format="PNG")
        cut_paths[cut.cut_index] = out_path
    return cut_paths


# ---------------------------------------------------------------------------
# V4 5-Act Page-Batch Illustration Pipeline (2:3 multi-panel 2K pages)
# ---------------------------------------------------------------------------

def _collect_act_characters(act: ActPage) -> list[str]:
    """Return unique character names appearing across all cuts in `act` in first-seen order."""
    seen: set[str] = set()
    ordered: list[str] = []
    for cut in act.cuts:
        for ch in cut.characters:
            key = ch.strip()
            if key and key not in seen:
                seen.add(key)
                ordered.append(key)
    return ordered


def _resolve_effective_background_style(
    background_style: BackgroundStyle | None,
    full_bleed_bg: bool | None = None,
    *,
    fallback: BackgroundStyle = "clean_white",
) -> BackgroundStyle:
    """Resolve effective V4 background style while preserving `full_bleed_bg` compatibility."""
    if background_style is not None:
        return background_style
    if full_bleed_bg is True:
        return "full_bleed"
    if full_bleed_bg is False:
        return "clean_white"
    return fallback


def _resolve_act_cut_full_bleed_flags(
    act: ActPage,
    eff_style: BackgroundStyle,
) -> list[bool]:
    """Return per-cut full-bleed boolean flags for `act` under `eff_style`.

    In `full_bleed` mode every panel is forced full-bleed. In both `clean_white`
    (3-tier smart background mode) and `selective_mix`, honor per-cut `cut.full_bleed_bg`
    so Tier 1 zone-establishing cuts render 100% edge-to-edge full-bleed while remaining
    cuts render as Tier 2 (natural ground + `#FFFFFF` sky) or Tier 3 (pure `#FFFFFF`).
    """
    if eff_style == "full_bleed":
        return [True for _ in act.cuts]
    return [bool(cut.full_bleed_bg) for cut in act.cuts]


def build_page_batch_prompt(
    act: ActPage,
    *,
    attached_turnarounds: list[str] | None = None,
    full_bleed_bg: bool = False,
    background_style: BackgroundStyle | None = None,
) -> str:
    """Construct the V4 2:3 multi-panel page-batch prompt referencing cast sheet, style ref,
    exact layout blueprint, and every active character's 3-view turnaround sheet.

    In default `clean_white` 3-tier smart background mode:
    - Tier 1 (`full_bleed_bg=True`, establishing/location cuts): 100% edge-to-edge full-bleed
      WoW zone scenery inside a crisp `#141414` black box frame with uncluttered bubble sky.
    - Tier 2 (`full_bleed_bg=False`, grounded action/climax/ending cuts): natural full-width
      ground/road/cliff/floor flush to bottom & side edges + 100% pure `#FFFFFF` upper sky.
    - Tier 3 (`full_bleed_bg=False`, character-only close-up/reaction cuts): 100% pure
      `#FFFFFF` white background + character acting & minimal manga FX only.
    """
    eff_style = _resolve_effective_background_style(background_style, full_bleed_bg)
    cut_fb_flags = _resolve_act_cut_full_bleed_flags(act, eff_style)
    all_fb = all(cut_fb_flags)
    any_fb = any(cut_fb_flags)

    layout = get_page_layout(act.layout_id)
    act_chars = _collect_act_characters(act)
    anchors = build_character_anchors_block(act_chars)
    combined_visual = " ".join(c.visual_prompt for c in act.cuts)
    lore_hints = build_cut_visual_lore_hints(combined_visual, act_chars)

    turnaround_ref_note = ""
    if attached_turnarounds:
        ref_lines = [
            f"- Reference Image {idx}: 3-View Front/Side/Back Turnaround Blueprint for {label} — "
            "IDENTITY & COSTUME LOCK ONLY (match ONLY hair, headgear, outfit, waist charms, boots, "
            "eye color, Clean Hand weapon stowing, thin variable-width ink linework, and 2-tier cel "
            "shading; STRICTLY IGNORE the turnaround's calm neutral standing pose and generic polite "
            "smile/wink — unleash wild scene-specific acting & distortion!)"
            for idx, label in enumerate(attached_turnarounds, start=4)
        ]
        turnaround_ref_note = (
            "\nATTACHED CHARACTER 3-VIEW TURNAROUND BLUEPRINTS (IDENTITY LOCK ONLY — ZERO POSE/EXPRESSION LOCK):\n"
            + "\n".join(ref_lines)
            + "\n"
        )

    panel_blocks: list[str] = []
    for slot, cut, cut_is_fb in zip(layout.slots, act.cuts, cut_fb_flags):
        chars_str = ", ".join(cut.characters)
        if cut_is_fb:
            if cut.wordless:
                headroom_rule = (
                    "TIER 1 WORDLESS FULL-BLEED BOX (NO SPEECH BUBBLE): Fill 100% edge-to-edge inside "
                    "all 4 dark `#141414` black border lines with rich cohesive WoW zone/dungeon scenery "
                    "& dramatic atmosphere (STRICTLY ZERO white gaps or vignettes!). Unleash MAXIMUM "
                    "camera drama (~72-88% panel height; honor extreme face close-ups, fisheye lunges, "
                    "bird's-eye views, or 30° Dutch tilts — ZERO doll-shrinking!). Keep ZERO TEXT, ZERO "
                    "speech bubbles, and 100% pure solid `#FFFFFF` outer page margins & gutters."
                )
            elif slot.is_narrow:
                headroom_rule = (
                    f"TIER 1 NARROW FULL-BLEED BOX ({slot.width}x{slot.height}px): Fill 100% edge-to-edge "
                    "inside all 4 dark `#141414` black border lines with vivid WoW zone landmarks & atmosphere "
                    "(ZERO white gaps or vignettes!). Keep ONLY the UPPER 34-38% as UNOBSTRUCTED open "
                    "sky/ceiling scenery (ZERO faces/heads in the bubble zone) while filling the active "
                    "LOWER 62-66% boldly with the exact camera & acting requested in Scene Action (NEVER "
                    "shrink dramatic close-ups or tilted angles into tiny stiff full-body dolls!). "
                    f"Speaker cue: {cut.tail_target}."
                )
            elif slot.height < 540:
                headroom_rule = (
                    f"TIER 1 WIDE SLIM FULL-BLEED BOX ({slot.width}x{slot.height}px): Fill 100% edge-to-edge "
                    "inside all 4 dark `#141414` black border lines with vivid WoW zone landmarks & atmosphere "
                    "(ZERO white gaps or vignettes!). Keep ONLY the OPPOSITE 44% SIDE or UPPER 34% as "
                    "UNOBSTRUCTED open sky/ceiling scenery (ZERO faces/heads in the bubble zone) while "
                    "filling the active zone boldly with the exact camera & acting requested in Scene Action "
                    f"(NEVER flatten dramatic shots into stiff eye-level standing dolls!). Speaker cue: {cut.tail_target}."
                )
            else:
                headroom_rule = (
                    f"TIER 1 ESTABLISHING FULL-BLEED BOX ({slot.width}x{slot.height}px): Fill 100% edge-to-edge "
                    "inside all 4 dark `#141414` black border lines with rich, iconic WoW zone/dungeon scenery, "
                    "landmarks & atmospheric sky (ZERO white gaps or vignettes!). Keep ONLY the UPPER 30-35% "
                    "as UNOBSTRUCTED open sky/ceiling scenery (ZERO faces/heads in the bubble zone) while "
                    "staging dynamic leaning/gesturing characters & exact Scene Action camera boldly in the "
                    f"active zone (ZERO stiff mannequin standing poses!). Speaker cue: {cut.tail_target}."
                )

            border_note = (
                "CRISP `#141414` BLACK-BORDERED FULL-BLEED BOX PANEL (Tier 1: fill 100% edge-to-edge inside "
                "Reference Image 3's exact black frame with rich WoW zone scenery & ZERO white gaps!)"
            )
        elif eff_style == "clean_white":
            if cut.wordless:
                headroom_rule = (
                    "TIER 2/3 WORDLESS CLIMAX — NATURAL GROUND + 100% PURE SOLID `#FFFFFF` WHITE SKY "
                    "(NO SPEECH BUBBLE): Unleash MAXIMUM full-panel cinematic scale & acting (~72-88% "
                    "panel height — honor extreme face close-up, Munch-scream horror, dizzying bird's-eye "
                    "drop, fisheye lunge, or 30° Dutch tilt with ZERO doll-shrinking!). Tier 2 (scenic/"
                    "grounded action): anchor full-width ground, road, cliff, floor, deck, lower props, "
                    "mobs, or mounts NATURALLY flush across the bottom & frame edges while keeping the "
                    "ENTIRE upper sky 100% pure solid `#FFFFFF` white (ZERO floating miniature toy islands, "
                    "ZERO beveled floating slabs, ZERO painted sky walls, ZERO blurry vignettes!). Tier 3 "
                    "(character-only shock): draw ONLY the character + minimal manga FX on 100% pure "
                    "`#FFFFFF`. ZERO text, ZERO bubbles."
                )
            elif slot.is_narrow:
                headroom_rule = (
                    f"TIER 2/3 NARROW PANEL ({slot.width}x{slot.height}px — TOP 36-40% 100% PURE SOLID "
                    "`#FFFFFF` WHITE SKY HEADROOM, LOWER 60-64% BOLD CAMERA/ACTING ZONE): Keep ONLY the "
                    "TOP 36-40% uncluttered pure `#FFFFFF` sky for the speech bubble, and fill the LOWER "
                    "60-64% BOLDLY with the exact camera requested in Scene Action (extreme face close-up, "
                    "fisheye lunge, low floor-level angle, 30° Dutch tilt — NEVER shrink a bold close-up or "
                    "tilted shot into a tiny stiff full-body doll!). Tier 2 (Grounded Scene — when Scene "
                    "Action specifies terrain/road/cliff/floor/deck/props/mobs/mounts) -> draw full-width "
                    "natural ground & lower props flush to bottom & side borders with 100% pure `#FFFFFF` "
                    "upper sky (ZERO floating miniature toy islands, ZERO painted sky/walls, ZERO blurry "
                    "vignettes!). Tier 3 (Character-Only Close-Up / Reaction) -> draw ONLY the character(s) "
                    f"+ minimal manga gag FX on 100% pure solid `#FFFFFF` white! Speaker cue: {cut.tail_target}."
                )
            else:
                headroom_rule = (
                    f"TIER 2/3 WIDE PANEL ({slot.width}x{slot.height}px — TOP 34% OR OPPOSITE 46% 100% PURE "
                    "SOLID `#FFFFFF` WHITE SKY HEADROOM): Keep ONLY the designated bubble headroom pure "
                    "`#FFFFFF`, and fill the active art zone BOLDLY with the exact camera requested in Scene "
                    "Action (extreme face close-up, fisheye forced-perspective lunge, dizzying extreme "
                    "bird's-eye top-down cliff view, low-angle loom, 30° Dutch tilt, over-the-shoulder — "
                    "NEVER shrink bold close-ups or extreme angles into tiny stiff eye-level full-body dolls!). "
                    "Tier 2 (Grounded Scene — when Scene Action specifies terrain/road/cliff/floor/deck/props/"
                    "mobs/mounts) -> draw full-width natural ground & lower props flush to bottom & side "
                    "borders with 100% pure `#FFFFFF` upper sky (ZERO floating miniature toy islands, ZERO "
                    "painted sky/walls, ZERO blurry vignettes!). Tier 3 (Character-Only Close-Up / Reaction) "
                    "-> draw ONLY the character(s) + minimal manga gag FX on 100% pure solid `#FFFFFF` white! "
                    f"Speaker cue: {cut.tail_target}."
                )

            border_note = (
                "BORDERLESS OPEN TIER 2/3 PANEL (100% pure solid `#FFFFFF` upper sky & outer edges — NO black box!)"
                if slot.border_style == "open"
                else "CRISP `#141414` BLACK-BORDERED TIER 2/3 BOX (Tier 2 flush natural lower ground + pure `#FFFFFF` upper sky OR Tier 3 pure `#FFFFFF` character-only; ZERO floating miniature islands, ZERO painted sky/walls, ZERO blurry vignettes!)"
            )
        else:
            if cut.wordless:
                headroom_rule = (
                    "WORDLESS CLIMAX 100% PURE SOLID `#FFFFFF` CLEAN BACKGROUND PANEL (NO SPEECH BUBBLE): "
                    "Draw a massive, hyper-expressive comedic close-up or theatrical freeze-frame (character "
                    "fills ~72-88% of panel height — honor extreme close-ups, fisheye lunges, or 30° Dutch "
                    "tilts with ZERO doll-shrinking!) on a 100% PURE SOLID `#FFFFFF` CLEAN BACKGROUND with "
                    "punchy minimal manga gag FX ONLY (ZERO painted scenery, ZERO partial vignette cutouts, "
                    "ZERO floating scenic rectangles). ZERO TEXT, ZERO bubbles."
                )
            elif slot.is_narrow:
                headroom_rule = (
                    f"NARROW VERTICAL 100% PURE SOLID `#FFFFFF` CLEAN PANEL ({slot.width}x{slot.height}px): "
                    "Reserve ONLY the TOP 36-40% as pure `#FFFFFF` speech-bubble headroom and fill the LOWER "
                    "60-64% BOLDLY with the exact camera & acting requested in Scene Action (do NOT shrink "
                    "bold close-ups into tiny stiff full-body dolls!) on 100% PURE SOLID `#FFFFFF` CLEAN "
                    "BACKGROUND with minimal manga gag FX ONLY (ZERO partial vignette cutouts, ZERO painted "
                    f"walls/sky). Speaker cue: {cut.tail_target}."
                )
            else:
                headroom_rule = (
                    f"WIDE 100% PURE SOLID `#FFFFFF` CLEAN PANEL ({slot.width}x{slot.height}px): "
                    "Reserve ONLY the TOP 32% or opposite 46% side as pure `#FFFFFF` headroom and fill the "
                    "active zone BOLDLY with the exact camera & acting requested in Scene Action (do NOT "
                    "shrink bold close-ups or tilted action into tiny stiff full-body dolls!) on 100% PURE "
                    "SOLID `#FFFFFF` CLEAN BACKGROUND with minimal manga gag FX ONLY (ZERO partial vignette "
                    f"cutouts, ZERO painted walls/sky). Speaker cue: {cut.tail_target}."
                )

            border_note = (
                "BORDERLESS OPEN CLEAN-WHITE PANEL (100% pure solid `#FFFFFF` fading into margins — NO black box!)"
                if slot.border_style == "open"
                else "CRISP BLACK-BORDERED CLEAN-WHITE BOX PANEL (exact `#141414` frame, 100% pure solid `#FFFFFF` inside — ZERO floating scenic cutouts!)"
            )

        panel_blocks.append(
            f"### PANEL {slot.slot_index} — {slot.position_label} [{border_note}]\n"
            f"- Starring Cast: {chars_str}\n"
            f"- Scene Action, Expression & Camera (Cut #{cut.cut_index}): {cut.visual_prompt.strip()}\n"
            f"- Background & Headroom Rule: {headroom_rule}\n"
            f"- Clean Hand Rule: Stow/sheathe default weapons on back or belt whenever holding scene loot, "
            "shields, dice, hearthstones, potions, or gesturing (never 3+ items at once)."
        )

    panels_section = "\n\n".join(panel_blocks)

    if all_fb:
        blueprint_ref_line = (
            f"- Reference Image 3: Exact 2:3 All-Boxed Layout Blueprint (`layout_blueprint.png` for `{act.layout_id}`) — "
            "match its exact `#141414` black panel frames and pure `#FFFFFF` outer margins & gutters (NEVER paint numbers/labels!)."
        )
        bg_section = (
            "100% FULL-BLEED COLORED BACKGROUNDS EDGE-TO-EDGE INSIDE EVERY PANEL BOX:\n"
            "- Fill EVERY box 100% edge-to-edge with rich cohesive WoW zone/dungeon/comic-gag backgrounds "
            "(STRICTLY ZERO white gaps, ZERO white fade-outs, ZERO floating vignette cutouts!).\n"
            "- Keep the bubble zone (upper 30-38% or opposite 44% side) filled with UNOBSTRUCTED OPEN "
            "BACKGROUND SCENERY (zero character faces/heads in the bubble zone) and keep all outer page "
            "margins & inter-panel gutters 100% pure solid `#FFFFFF` white."
        )
        tech_constraints = (
            "ABSOLUTE TECHNICAL CONSTRAINTS:\n"
            "- Outer page margins & inter-panel gutters: 100% pure solid `#FFFFFF` white (ZERO smudges/tint); "
            "every boxed panel interior: 100% edge-to-edge colored art with ZERO white gaps.\n"
            "- ZERO TEXT, ZERO KOREAN/ENGLISH LETTERS, ZERO DIGITS/PANEL NUMBERS, ZERO SPEECH BUBBLES, ZERO SFX, ZERO WATERMARKS.\n"
            "- STRICT 2:3 GEOMETRY aligned to Reference Image 3; NO duplicate clone extras of starring cast."
        )
    elif any_fb and eff_style == "clean_white":
        blueprint_ref_line = (
            f"- Reference Image 3: Exact 2:3 3-Tier Page Layout Blueprint (`layout_blueprint.png` for `{act.layout_id}`) — "
            "solid `#141414` black rectangles mark boxed panels (including EVERY Tier 1 full-bleed establishing box and "
            "boxed Tier 2/3 panel); subtle light-gray guides mark borderless `open` Tier 2/3 panels (NEVER paint gray guides or numbers!)."
        )
        bg_section = (
            "3-TIER SMART BACKGROUND DIRECTIVE (STRICT PER-PANEL ROLE — ZERO FLOATING MINIATURE ISLANDS, ZERO BLURRY VIGNETTES!):\n"
            "- **TIER 1 — ZONE ESTABLISHING SHOT (panels marked `FULL-BLEED BOX` above)**: Fill 100% edge-to-edge inside "
            "its crisp `#141414` black frame with rich iconic WoW zone landmarks, terrain, & atmospheric sky, keeping the "
            "upper bubble sky UNOBSTRUCTED and uncluttered for speech-bubble readability (ZERO white gaps inside that box!).\n"
            "- **TIER 2 — GROUNDED ACTION / CLIMAX / ENDING (non-full-bleed cuts with terrain/road/cliff/floor/props)**: "
            "Draw NATURAL GROUNDED SCENERY (ground/road/cliff/floor/deck/lower props) flush across the full bottom & side "
            "borders in real comic perspective while keeping the ENTIRE upper sky 100% PURE SOLID `#FFFFFF` WHITE SKY "
            "(STRICTLY ZERO floating miniature toy islands, ZERO beveled floating rock slabs, ZERO blurry rectangular vignettes!).\n"
            "- **TIER 3 — CHARACTER-ONLY CLOSE-UP / REACTION (non-full-bleed banter/gag cuts)**: Render ONLY expressive "
            "Draft C character(s) + minimal manga gag FX (sweatdrops, anger veins, speed lines, shock lines) on 100% PURE "
            "SOLID `#FFFFFF` WHITE (ZERO unnecessary background clutter!).\n"
            "- Keep ALL outer page margins & inter-panel gutters 100% pure solid `#FFFFFF` white."
        )
        tech_constraints = (
            "ABSOLUTE TECHNICAL CONSTRAINTS:\n"
            "- Outer page margins, inter-panel gutters, Tier 3 reaction backgrounds, and Tier 2 upper skies MUST stay "
            "100% pure solid `#FFFFFF` white (ZERO floating miniature toy islands, ZERO hovering stone pancakes, ZERO "
            "blurry rectangular vignettes), while Tier 1 full-bleed establishing boxes fill 100% edge-to-edge inside "
            "their `#141414` black frames with ZERO white gaps.\n"
            "- ZERO TEXT, ZERO KOREAN/ENGLISH LETTERS, ZERO DIGITS/PANEL NUMBERS, ZERO SPEECH BUBBLES, ZERO SFX, ZERO WATERMARKS.\n"
            "- STRICT 2:3 GEOMETRY aligned to Reference Image 3; NO duplicate clone extras of starring cast."
        )
    elif any_fb:
        blueprint_ref_line = (
            f"- Reference Image 3: Exact 2:3 Selective-Mix Page Layout Blueprint (`layout_blueprint.png` for `{act.layout_id}`) — "
            "solid black rectangles mark boxed panels (including EVERY full-bleed panel and boxed clean-white panel); "
            "subtle light-gray rectangles mark borderless `open` clean-white panels (NEVER paint gray guides or panel numbers!)."
        )
        bg_section = (
            "SELECTIVE-MIX PER-CUT BACKGROUND RHYTHM (STRICT ALL-OR-NOTHING — ZERO HALF-BAKED VIGNETTES!):\n"
            "- FOR FULL-BLEED PANELS (marked FULL-BLEED BOX above): Fill 100% edge-to-edge inside all 4 black "
            "frame lines with rich cohesive WoW scenery with ZERO white gaps, keeping the bubble zone UNOBSTRUCTED.\n"
            "- FOR CLEAN-WHITE PANELS (marked 100% PURE SOLID `#FFFFFF` CLEAN PANEL above): Render characters "
            "on a 100% PURE SOLID `#FFFFFF` CLEAN BACKGROUND with minimal manga gag FX ONLY — STRICTLY ZERO "
            "partial vignette cutouts, ZERO floating scenic rectangles, and ZERO painted walls/sky!\n"
            "- KEEP ALL OUTER PAGE MARGINS & INTER-PANEL GUTTERS 100% PURE SOLID `#FFFFFF` WHITE!"
        )
        tech_constraints = (
            "ABSOLUTE TECHNICAL CONSTRAINTS:\n"
            "- Keep outer page margins, inter-panel gutters, open-panel edges, and clean-white panels 100% pure solid "
            "`#FFFFFF` (ZERO partial vignette cutouts), while full-bleed panels fill 100% edge-to-edge with ZERO white gaps.\n"
            "- ZERO TEXT, ZERO KOREAN/ENGLISH LETTERS, ZERO DIGITS/PANEL NUMBERS, ZERO SPEECH BUBBLES, ZERO SFX, ZERO WATERMARKS.\n"
            "- STRICT 2:3 GEOMETRY aligned to Reference Image 3; NO duplicate clone extras of starring cast."
        )
    else:
        blueprint_ref_line = (
            f"- Reference Image 3: Exact 2:3 Page Layout Blueprint (`layout_blueprint.png` for `{act.layout_id}`) — "
            "solid `#141414` black rectangles mark `box` panels; subtle light-gray rectangles mark borderless `open` "
            "panels (leave `open` panels borderless on `#FFFFFF`; NEVER paint gray guides or panel numbers!)."
        )
        if eff_style == "clean_white":
            bg_section = (
                "NATURAL GROUNDED SCENERY + 100% PURE SOLID `#FFFFFF` WHITE SKY HARMONY (TIER 2 + TIER 3):\n"
                "- **TIER 2 — GROUNDED ACTION / CLIMAX / ENDING (cuts with terrain/road/cliff/floor/deck/props/mobs/mounts)**: "
                "Draw full-width ground, road, cliff, floor, deck, & lower props NATURALLY flush across the bottom & side "
                "frame edges in real comic perspective (thin ink linework + 2-tier cel shading), while keeping the ENTIRE "
                "upper sky 100% PURE SOLID `#FFFFFF` WHITE SKY!\n"
                "- **TIER 3 — CHARACTER-ONLY CLOSE-UP / REACTION (fast banter/gag cuts)**: Render ONLY expressive Draft C "
                "character(s) + minimal manga gag FX (sweatdrops, anger veins, speed lines, shock bursts) on 100% pure "
                "solid `#FFFFFF` white — zero unnecessary scenery clutter.\n"
                "- STRICTLY ZERO floating miniature toy islands, ZERO hovering beveled stone slabs, ZERO painted blue/sunset "
                "sky walls on Tier 2/3 cuts, ZERO pastel wallpaper fills, and ZERO blurry rectangular vignette cutouts!\n"
                "- Reserve 100% pure `#FFFFFF` white-sky speech-bubble headroom (top 36-40% narrow, top 34% or opposite 46% "
                "wide, and open `#FFFFFF` upper sky even on wordless climax cuts) + 100% pure `#FFFFFF` margins & gutters."
            )
            tech_constraints = (
                "ABSOLUTE TECHNICAL CONSTRAINTS:\n"
                "- Outer page margins, inter-panel gutters, Tier 3 reaction backgrounds, and Tier 2 upper skies MUST stay "
                "100% pure solid `#FFFFFF` white (ZERO painted sky/walls, ZERO pastel wallpaper, ZERO floating miniature "
                "toy islands or beveled rock slabs, ZERO blurry rectangular vignettes — ground/road/cliff/floor anchors "
                "naturally flush across bottom & side edges when called for!).\n"
                "- ZERO TEXT, ZERO KOREAN/ENGLISH LETTERS, ZERO DIGITS/PANEL NUMBERS, ZERO SPEECH BUBBLES, ZERO SFX, ZERO WATERMARKS.\n"
                "- STRICT 2:3 GEOMETRY aligned to Reference Image 3; NO duplicate clone extras of starring cast."
            )
        else:
            bg_section = (
                "100% PURE SOLID `#FFFFFF` CLEAN BACKGROUNDS (ZERO PARTIAL VIGNETTE CUTOUTS!):\n"
                "- Render every panel on 100% PURE SOLID `#FFFFFF` CLEAN BACKGROUND with expressive Draft C "
                "characters and minimal manga gag FX ONLY (ZERO partial vignette cutouts, ZERO painted room/sky walls).\n"
                "- Reserve 100% pure `#FFFFFF` empty speech-bubble headroom + pure `#FFFFFF` outer margins & gutters."
            )
            tech_constraints = (
                "ABSOLUTE TECHNICAL CONSTRAINTS:\n"
                "- Keep outer page margins, inter-panel gutters, open-panel edges, and every panel background 100% pure "
                "solid `#FFFFFF` (ZERO partial vignette cutouts or floating scenic rectangles).\n"
                "- ZERO TEXT, ZERO KOREAN/ENGLISH LETTERS, ZERO DIGITS/PANEL NUMBERS, ZERO SPEECH BUBBLES, ZERO SFX, ZERO WATERMARKS.\n"
                "- STRICT 2:3 GEOMETRY aligned to Reference Image 3; NO duplicate clone extras of starring cast."
            )

    return (
        f"Draw a crisp 2:3 vertical Korean pop-gag anime chibi comic page (Act {act.act_number}: "
        f"{act.act_title} | layout `{act.layout_id}`, {layout.panel_count} panels) with STRICT "
        "IDENTITY vs UNLEASHED ACTING DECOUPLING — match the exact 2.5-to-2.8 head chibi proportions, "
        "thin variable-width ink linework, crisp 2-tier cel shading, and character costumes of the "
        "attached references while UNLEASHING wildly varied anime gag acting and bold cinematic cameras!\n\n"
        "ATTACHED REFERENCE IMAGES (FOLLOW EXACT ORDER — ZERO FIXED EXPRESSION SHEETS!):\n"
        "- Reference Image 1: Draft C 9-Cast Master Sheet (`assets/cast_sheet_c.jpg`) — IDENTITY & STYLE "
        "LOCK ONLY (2.5-to-2.8 head proportions, hair/costume identity, thin ink & 2-tier cel finish; "
        "NEVER copy its calm standing poses or default polite smiles/winks!).\n"
        "- Reference Image 2: Sloptoon Style Reference (`assets/sloptoon_style_ref.jpg`) — dynamic "
        "webtoon camera energy, exaggerated manga gag acting & crisp cel finish.\n"
        f"{blueprint_ref_line}\n"
        f"{turnaround_ref_note}\n"
        f"{anchors}\n\n"
        f"=== PANEL-BY-PANEL PAGE DIRECTIVES ({layout.panel_count} PANELS) ===\n\n"
        f"{panels_section}\n\n"
        f"{lore_hints}\n\n"
        f"{bg_section}\n\n"
        "STRICT IDENTITY vs UNLEASHED ACTING DECOUPLING (BREAK THE PRETTY-FACE SAFETY ZONE!):\n"
        "- **IDENTITY LOCK ONLY**: Reference images (`cast_sheet`, `turnarounds`) lock ONLY hair, "
        "headgear, outfit, waist charms, boots, eye color, Clean Hand weapon stowing, and thin-ink "
        "2-tier cel shading. Expressions and poses are 100% UNLOCKED and driven solely by Scene Action!\n"
        "- **BREAK THE PRETTY-FACE SAFETY ZONE (UNLEASHED EXPRESSIVE ACTING)**: NEVER copy the calm/"
        "neutral standing pose or generic polite smile/wink from the reference sheets! Push wild, "
        "infinitely varied, scene-specific anime gag acting across every panel:\n"
        "  * **Dramatic eye-size & shape shifts**: pinpoint psychotic pupils (`맑눈광`), huge sparkling "
        "jewel eyes, empty white shock eyes, spiral dizzy eyes, crying geyser waterfalls, unimpressed "
        "deadpan half-lids, sinister gleaming glint.\n"
        "  * **Extreme mouths & facial comedy**: jaw-dropped screaming, smug cat `:3`, mischievous "
        "gremlin grin, cheeky fang smirk / `:P`, shaky panic squiggle, wide sweetly-evil grin, "
        "crumpled Munch-scream horror, forehead gloom shadows, pale-blue drained terror cheeks.\n"
        "  * **Squash-and-stretch body & hand acting**: comedic squash-and-stretch body distortion, "
        "dynamic leaning, lunging, crouching, sprawling, slipping mid-air, claw-like fingers, "
        "steering-wheel cranking, facepalm, cheek-clutching panic, and index-finger `shhh!`.\n\n"
        "ANTI-REPETITION & CINEMATIC CAMERA VARIETY (ZERO BLAND DOLL REPEATS!):\n"
        "- **STRICT ANTI-REPETITION ACROSS THIS PAGE**: NEVER repeat the same facial expression, head "
        "angle, or eye-level medium shot across panels on the same page! Every panel MUST contrast "
        "sharply in both emotion and camera framing.\n"
        "- **HONOR BOLD CAMERAS 100%**: Actively execute extreme cameras requested in Scene Action — "
        "**extreme face close-up, fisheye forced-perspective lunging toward camera, dizzying extreme "
        "bird's-eye top-down cliff view, low-angle loom, 30° Dutch tilt, over-the-shoulder, low "
        "floor-level stealth angle** — keeping ONLY the designated speech-bubble sky/side headroom "
        "uncluttered (NEVER shrink bold close-ups or tilted action shots into tiny stiff full-body dolls!).\n"
        "- **EXTRAS, MOBS, MOUNTS & FX**: Draw any scripted dungeon mobs, bosses, extras, guards, "
        "pets, mounts, spell FX, or cute non-gore cartoon skeletons vividly in the same crisp Draft C "
        "anime style.\n\n"
        f"{tech_constraints}"
    )


def generate_act_page_image(
    act: ActPage,
    output_path: Path,
    *,
    client: Any | None = None,
    settings: Settings | None = None,
    model: str | None = None,
    image_size: str = "2K",
    full_bleed_bg: bool = False,
    background_style: BackgroundStyle | None = None,
) -> Path:
    """Generate a single V4 2:3 multi-panel act page image via Gemini Interactions API."""
    cfg = settings or load_settings()
    target_model = resolve_image_model(model, cfg)
    eff_style = _resolve_effective_background_style(background_style, full_bleed_bg)
    cut_fb_flags = _resolve_act_cut_full_bleed_flags(act, eff_style)

    if client is None:
        if not cfg.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Configure GEMINI_API_KEY in .env or environment."
            )
        client = genai.Client(api_key=cfg.gemini_api_key)

    cast_b64, cast_mime = _encode_image_base64(cfg.cast_sheet_path)
    style_b64, style_mime = _encode_image_base64(cfg.style_ref_path)

    layout = get_page_layout(act.layout_id)
    if eff_style == "full_bleed":
        blueprint_im = render_layout_blueprint(act.layout_id, all_boxed=True)
    elif eff_style == "selective_mix" or any(cut_fb_flags):
        slot_boxed = [
            cut_is_fb or slot.border_style == "box"
            for slot, cut_is_fb in zip(layout.slots, cut_fb_flags)
        ]
        blueprint_im = render_layout_blueprint(act.layout_id, slot_boxed=slot_boxed)
    else:
        blueprint_im = render_layout_blueprint(act.layout_id, all_boxed=False)
    bp_b64, bp_mime = _encode_pil_image_png_base64(blueprint_im)

    act_characters = _collect_act_characters(act)
    turnaround_pairs = get_turnaround_paths(act_characters, cfg.turnarounds_dir)

    prompt = build_page_batch_prompt(
        act,
        attached_turnarounds=[f"{m.name} ({m.id})" for m, _ in turnaround_pairs],
        full_bleed_bg=(eff_style == "full_bleed"),
        background_style=eff_style,
    )

    input_items: list[dict[str, Any]] = [
        {"type": "text", "text": prompt},
        {"type": "image", "data": cast_b64, "mime_type": cast_mime},
        {"type": "image", "data": style_b64, "mime_type": style_mime},
        {"type": "image", "data": bp_b64, "mime_type": bp_mime},
    ]
    for _member, turnaround_path in turnaround_pairs:
        t_b64, t_mime = _encode_image_base64(turnaround_path)
        input_items.append({"type": "image", "data": t_b64, "mime_type": t_mime})

    interaction = client.interactions.create(
        model=target_model,
        input=input_items,
        response_format={
            "type": "image",
            "aspect_ratio": V4_ASPECT_RATIO,
            "image_size": image_size,
        },
    )

    img_bytes = _extract_image_bytes(interaction)
    return _save_image_bytes(img_bytes, output_path)


def generate_v4_episode_pages(
    script: EpisodeScript,
    output_dir: Path,
    *,
    client: Any | None = None,
    settings: Settings | None = None,
    model: str | None = None,
    image_size: str = "2K",
    max_workers: int = 5,
    full_bleed_bg: bool | None = None,
    background_style: BackgroundStyle | None = None,
) -> dict[int, Path]:
    """Generate all 5 V4 act page images in parallel (`raw_page_01.png` .. `raw_page_05.png`)."""
    if not script.acts:
        raise ValueError("generate_v4_episode_pages requires a V4 EpisodeScript with `acts` populated.")

    cfg = settings or load_settings()
    target_model = resolve_image_model(model, cfg)
    eff_style = _resolve_effective_background_style(
        background_style,
        full_bleed_bg,
        fallback=script.background_style,
    )

    if client is None:
        if not cfg.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Configure GEMINI_API_KEY in .env or environment."
            )
        client = genai.Client(api_key=cfg.gemini_api_key)

    output_dir.mkdir(parents=True, exist_ok=True)
    worker_count = max(1, min(int(max_workers), len(script.acts)))

    def _run_one(act: ActPage) -> tuple[int, Path]:
        out_path = output_dir / f"raw_page_{act.act_number:02d}.png"
        saved = generate_act_page_image(
            act,
            out_path,
            client=client,
            settings=cfg,
            model=target_model,
            image_size=image_size,
            full_bleed_bg=(eff_style == "full_bleed"),
            background_style=eff_style,
        )
        return act.act_number, saved

    results: dict[int, Path] = {}
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        futures = [pool.submit(_run_one, act) for act in script.acts]
        for fut in futures:
            act_num, saved_path = fut.result()
            results[act_num] = saved_path

    return {k: results[k] for k in sorted(results.keys())}


def render_dry_run_v4_pages(
    script: EpisodeScript,
    output_dir: Path,
    *,
    full_bleed_bg: bool | None = None,
    background_style: BackgroundStyle | None = None,
) -> dict[int, Path]:
    """Render clean deterministic pure-#FFFFFF 900x1350 V4 act pages for offline dry-run & testing."""
    if not script.acts:
        raise ValueError("render_dry_run_v4_pages requires a V4 EpisodeScript with `acts` populated.")

    output_dir.mkdir(parents=True, exist_ok=True)
    eff_style = _resolve_effective_background_style(
        background_style,
        full_bleed_bg,
        fallback=script.background_style,
    )
    is_full_bleed = eff_style == "full_bleed"
    palette: tuple[tuple[int, int, int], ...] = (
        (186, 230, 253),  # Skyborne sky-blue
        (221, 214, 254),  # Night Elf Priest lavender
        (187, 247, 208),  # Orc Warrior green
        (254, 240, 138),  # Gnome Rogue gold
        (254, 205, 211),  # Accent coral
    )
    bg_palette: tuple[tuple[int, int, int], ...] = (
        (126, 178, 224),  # Dungeon twilight blue
        (168, 146, 198),  # Arcane cave lavender
        (134, 184, 152),  # Forest / mine moss
        (218, 182, 128),  # Warm tavern / torch amber
        (158, 174, 196),  # Stormy harbor slate
    )

    page_paths: dict[int, Path] = {}
    for act in script.acts:
        layout = get_page_layout(act.layout_id)
        cut_fb_flags = _resolve_act_cut_full_bleed_flags(act, eff_style)
        if is_full_bleed:
            img = render_layout_blueprint(act.layout_id, all_boxed=True)
        elif eff_style == "selective_mix" or any(cut_fb_flags):
            slot_boxed = [
                cut_is_fb or slot.border_style == "box"
                for slot, cut_is_fb in zip(layout.slots, cut_fb_flags)
            ]
            img = render_layout_blueprint(act.layout_id, slot_boxed=slot_boxed)
        else:
            img = render_layout_blueprint(act.layout_id, all_boxed=False)
        draw = ImageDraw.Draw(img)

        for idx, (slot, cut, cut_is_fb) in enumerate(zip(layout.slots, act.cuts, cut_fb_flags)):
            x0, y0, x1, y1 = slot.rect
            sw, sh = slot.width, slot.height
            fill_col = palette[(act.act_number + idx) % len(palette)]

            if cut_is_fb:
                bg_col = bg_palette[(act.act_number + idx) % len(bg_palette)]
                draw.rectangle([x0 + 4, y0 + 4, x1 - 4, y1 - 4], fill=bg_col)

            if cut.wordless:
                cx = x0 + sw // 2
                cy = y0 + int(sh * 0.52)
                r = min(sw, sh) // 4
            else:
                if cut.tail_target == "left" and not slot.is_narrow:
                    cx = x0 + int(sw * 0.34)
                elif cut.tail_target == "right" and not slot.is_narrow:
                    cx = x0 + int(sw * 0.66)
                else:
                    cx = x0 + sw // 2
                cy = y0 + int(sh * (0.72 if slot.is_narrow else 0.68))
                r = max(28, min(sw // 4, sh // 5))

            # Draw cute minimal chibi silhouette well inside panel margins
            draw.ellipse(
                (cx - r, cy - r, cx + r, cy + r),
                fill=fill_col,
                outline=(30, 41, 59),
                width=4,
            )
            # Cute sparkling eyes
            eye_r = max(4, r // 7)
            draw.ellipse(
                (cx - r // 3 - eye_r, cy - eye_r, cx - r // 3 + eye_r, cy + eye_r),
                fill=(30, 41, 59),
            )
            draw.ellipse(
                (cx + r // 3 - eye_r, cy - eye_r, cx + r // 3 + eye_r, cy + eye_r),
                fill=(30, 41, 59),
            )

            if cut_is_fb:
                draw.rectangle([x0, y0, x1, y1], outline=(20, 20, 20), width=4)

        out_path = output_dir / f"raw_page_{act.act_number:02d}.png"
        img.save(out_path, format="PNG")
        page_paths[act.act_number] = out_path

    return page_paths
