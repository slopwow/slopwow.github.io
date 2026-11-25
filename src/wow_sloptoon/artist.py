"""Comic illustrator powered by Google GenAI Interactions API (`gemini-nano-banana-2.1`).

Style-First architecture targeting sleek 3-to-3.5 head Korean anime gag webtoon art:
- Reference Image 1 is ALWAYS `assets/sloptoon_style_ref.jpg` (master art style, 3–3.5 head
  proportions, thin ink linework, crisp 2-tier cel shading, and lively manga expressions).
- Active character 3-view turnaround sheets (`assets/turnarounds/<id>.jpg`) follow strictly
  as COSTUME, HAIR & COLOR references only — re-proportioned into Reference Image 1's sleek
  webtoon build (never copying stubby 2-head SD sheets or stiff neutral standing poses).
- Supports both primary cut-by-cut generation (`generate_episode_cuts`, 4~8 cuts) and V4
  5-act 2K page-batch generation (`generate_v4_episode_pages`).
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

from wow_sloptoon.cast import (
    build_character_anchors_block,
    get_companion_turnaround_paths,
    get_turnaround_paths,
)
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
    attached_companions: list[str] | None = None,
    has_cast_sheet_fallback: bool = False,
) -> str:
    """Construct a compact, Style-First 3–3.5 head webtoon prompt for a single comic cut."""
    anchors = build_character_anchors_block(cut.characters)
    lore_hints = build_cut_visual_lore_hints(cut.visual_prompt, cut.characters)

    ref_lines = [
        "- Reference Image 1 (`assets/sloptoon_style_ref.jpg`): MASTER ART STYLE & PROPORTIONS — "
        "match its sleek 3-to-3.5 head Korean anime gag webtoon body proportions, tapered chin, "
        "slender limbs, thin crisp dark ink linework, fine hair strands, natural clothing folds, "
        "vibrant 2-tier cel shading, and expressive faces."
    ]
    next_idx = 2
    if attached_turnarounds:
        for label in attached_turnarounds:
            ref_lines.append(
                f"- Reference Image {next_idx}: Costume & Color Sheet for {label} — match sleek 3.5-head "
                "build, hair strands, cloth folds, headgear, outfit & colors with dynamic scene acting."
            )
            next_idx += 1
    elif has_cast_sheet_fallback:
        ref_lines.append(
            f"- Reference Image {next_idx}: Cast Costume Sheet — use for outfit/hair color identity only, "
            "in Reference Image 1's sleek 3-to-3.5 head webtoon style."
        )
        next_idx += 1
    if attached_companions:
        for comp_label in attached_companions:
            ref_lines.append(
                f"- Reference Image {next_idx}: Cute Round Companion Mascot Sheet for {comp_label} — "
                "keep its ultra-cute plump round proportions, colors, and adorable face; draw it naturally "
                "accompanying and reacting beside its owner."
            )
            next_idx += 1
    refs_block = "\n".join(ref_lines)

    if cut.wordless:
        framing_note = (
            "COMPOSITION: Silent comedic close-up or freeze-frame filling ~75–85% of canvas height "
            "with vivid anime shock/deadpan acting. No speech-bubble headroom needed."
        )
    elif cut.layout_slot == "top":
        framing_note = (
            "COMPOSITION: Open top 4:3 webtoon cut. Keep the top ~32% pure solid white (#FFFFFF) "
            "empty for external speech-bubble placement; stage characters boldly in the lower two-thirds "
            "with expressive waist-up or thigh-up 3-to-3.5 head webtoon framing matching Reference Image 1 "
            "(prefer close expressive framing over zoomed-out tiny full-body figures). "
            f"Speaker side: {cut.tail_target}."
        )
    else:
        framing_note = (
            "COMPOSITION: Wide 16:9 reaction/action cut. Keep the upper or opposite-side pure solid white "
            "(#FFFFFF) space clear for external speech-bubble placement; frame character(s) boldly with "
            "expressive waist-up or thigh-up 3-to-3.5 head webtoon framing matching Reference Image 1 "
            "(avoid zoomed-out stubby full-body figures). "
            f"Speaker side: {cut.tail_target}."
        )

    return (
        "Draw a single crisp Korean anime gag webtoon comic cut in sleek 3-to-3.5 head proportions "
        "matching Reference Image 1.\n\n"
        f"REFERENCE IMAGES:\n{refs_block}\n\n"
        f"{anchors}\n\n"
        f"SCENE ACTION (Cut #{cut.cut_index}):\n{cut.visual_prompt.strip()}\n\n"
        f"{framing_note}\n\n"
        f"{lore_hints}\n\n"
        "TECHNICAL REQUIREMENTS:\n"
        "- Pure solid white (#FFFFFF) outer background and bubble headroom; minimal grounded props/floor "
        "touches attached to the action are welcome, with no full room walls, gray washes, or panel borders.\n"
        "- Zero text, zero letters, zero digits/numbers, zero speech bubbles, zero SFX, zero watermarks.\n"
        "- Keep characters natural, lively, and expressive in sleek 3-to-3.5 head webtoon proportions "
        "(avoid stubby 2-head chibi dolls or stiff front passport poses)."
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
    """Generate a single pure-#FFFFFF sleek 3–3.5 head comic cut via Gemini Interactions API."""
    cfg = settings or load_settings()
    target_model = resolve_image_model(model, cfg)

    if client is None:
        if not cfg.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Configure GEMINI_API_KEY in .env or environment."
            )
        client = genai.Client(api_key=cfg.gemini_api_key)

    style_b64, style_mime = _encode_image_base64(cfg.style_ref_path)
    turnaround_pairs = get_turnaround_paths(cut.characters, cfg.turnarounds_dir)
    companion_pairs = get_companion_turnaround_paths(cut.characters, cfg.turnarounds_dir)
    use_cast_fallback = len(turnaround_pairs) == 0

    prompt = build_cut_image_prompt(
        cut,
        attached_turnarounds=[f"{m.name} ({m.id})" for m, _ in turnaround_pairs],
        attached_companions=[
            f"{m.companion_name} ({m.companion_id}, companion of {m.name})"
            for m, _ in companion_pairs
        ],
        has_cast_sheet_fallback=use_cast_fallback,
    )

    # Style-First attachment order: [text, style_ref, *active_turnarounds, *companion_turnarounds]
    input_items: list[dict[str, Any]] = [
        {"type": "text", "text": prompt},
        {"type": "image", "data": style_b64, "mime_type": style_mime},
    ]
    if turnaround_pairs:
        for _member, turnaround_path in turnaround_pairs:
            t_b64, t_mime = _encode_image_base64(turnaround_path)
            input_items.append({"type": "image", "data": t_b64, "mime_type": t_mime})
    else:
        cast_b64, cast_mime = _encode_image_base64(cfg.cast_sheet_path)
        input_items.append({"type": "image", "data": cast_b64, "mime_type": cast_mime})
    for _owner, comp_path in companion_pairs:
        c_b64, c_mime = _encode_image_base64(comp_path)
        input_items.append({"type": "image", "data": c_b64, "mime_type": c_mime})

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
    max_workers: int = 1,
) -> dict[int, Path]:
    """Generate raw cut images for all 4~8 cuts in an `EpisodeScript` (parallel when max_workers > 1)."""
    cfg = settings or load_settings()
    target_model = resolve_image_model(model, cfg)

    if client is None:
        if not cfg.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Configure GEMINI_API_KEY in .env or environment."
            )
        client = genai.Client(api_key=cfg.gemini_api_key)

    output_dir.mkdir(parents=True, exist_ok=True)
    worker_count = max(1, min(int(max_workers), len(script.cuts)))

    def _run_cut(cut: ComicCut) -> tuple[int, Path]:
        out_path = output_dir / f"cut_{cut.cut_index:02d}.png"
        saved = generate_cut_image(
            cut,
            out_path,
            client=client,
            settings=cfg,
            model=target_model,
            image_size=image_size,
        )
        return cut.cut_index, saved

    if worker_count == 1:
        cut_paths: dict[int, Path] = {}
        for cut in script.cuts:
            idx, saved = _run_cut(cut)
            cut_paths[idx] = saved
        return cut_paths

    results: dict[int, Path] = {}
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        futures = [pool.submit(_run_cut, cut) for cut in script.cuts]
        for fut in futures:
            idx, saved = fut.result()
            results[idx] = saved
    return {k: results[k] for k in sorted(results.keys())}


def render_dry_run_cuts(script: EpisodeScript, output_dir: Path) -> dict[int, Path]:
    """Create clean pure-#FFFFFF placeholder cut images for offline `--dry-run` testing."""
    output_dir.mkdir(parents=True, exist_ok=True)
    cut_paths: dict[int, Path] = {}
    for cut in script.cuts:
        size = (1024, 768) if cut.aspect_ratio == "4:3" else (1280, 720)
        img = Image.new("RGB", size, (255, 255, 255))
        draw = ImageDraw.Draw(img)
        w, h = size
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
    """Return per-cut full-bleed boolean flags for `act` under `eff_style`."""
    if eff_style == "full_bleed":
        return [True for _ in act.cuts]
    return [bool(cut.full_bleed_bg) for cut in act.cuts]


def build_page_batch_prompt(
    act: ActPage,
    *,
    attached_turnarounds: list[str] | None = None,
    attached_companions: list[str] | None = None,
    full_bleed_bg: bool = False,
    background_style: BackgroundStyle | None = None,
    has_cast_sheet_fallback: bool = False,
) -> str:
    """Construct a compact, Style-First 3–3.5 head webtoon prompt for a V4 2:3 multi-panel page."""
    eff_style = _resolve_effective_background_style(background_style, full_bleed_bg)
    cut_fb_flags = _resolve_act_cut_full_bleed_flags(act, eff_style)
    all_fb = all(cut_fb_flags)
    any_fb = any(cut_fb_flags)

    layout = get_page_layout(act.layout_id)
    act_chars = _collect_act_characters(act)
    anchors = build_character_anchors_block(act_chars)
    combined_visual = " ".join(c.visual_prompt for c in act.cuts)
    lore_hints = build_cut_visual_lore_hints(combined_visual, act_chars)

    ref_lines = [
        "- Reference Image 1 (`assets/sloptoon_style_ref.jpg`): MASTER ART STYLE & PROPORTIONS — "
        "sleek 3-to-3.5 head Korean anime gag webtoon proportions, slender limbs, thin clean dark ink "
        "linework, fine hair strands, natural clothing folds, crisp 2-tier cel shading, and vivid manga expressions.",
        f"- Reference Image 2: Exact 2:3 Layout Blueprint (`{act.layout_id}`) — solid `#141414` black "
        "rectangles mark boxed panels; light-gray guides mark borderless open panels (keep outer page "
        "margins and gutters pure `#FFFFFF`; do not paint gray guide lines or panel numbers).",
    ]
    next_idx = 3
    if attached_turnarounds:
        for label in attached_turnarounds:
            ref_lines.append(
                f"- Reference Image {next_idx}: Costume & Color Sheet for {label} — match its sleek "
                "3.5-head proportions, hair strands, clothing folds, headgear, outfit, and colors."
            )
            next_idx += 1
    elif has_cast_sheet_fallback:
        ref_lines.append(
            f"- Reference Image {next_idx}: Cast Costume Sheet — outfit/color identity only, "
            "in Reference Image 1's sleek 3-to-3.5 head webtoon style."
        )
        next_idx += 1
    if attached_companions:
        for comp_label in attached_companions:
            ref_lines.append(
                f"- Reference Image {next_idx}: Cute Round Companion Mascot Sheet for {comp_label} — "
                "keep its ultra-cute plump round proportions, colors, and adorable face beside its owner."
            )
            next_idx += 1
    refs_block = "\n".join(ref_lines)

    panel_blocks: list[str] = []
    for slot, cut, cut_is_fb in zip(layout.slots, act.cuts, cut_fb_flags):
        chars_str = ", ".join(cut.characters)
        if cut_is_fb:
            border_tag = "FULL-BLEED BOX"
            if cut.wordless:
                bg_rule = (
                    "Fill edge-to-edge inside the black frame with WoW scenery; silent dramatic close-up "
                    "or freeze-frame (~75% height), no bubble headroom needed."
                )
            else:
                zone = "top ~35%" if slot.is_narrow else "top ~32% or opposite ~44% side"
                bg_rule = (
                    f"Fill edge-to-edge inside the black frame with WoW scenery; keep {zone} as open "
                    f"unobstructed sky/background for bubble placement (speaker: {cut.tail_target})."
                )
        else:
            border_tag = "BORDERLESS OPEN" if slot.border_style == "open" else "CLEAN-WHITE BOX"
            if cut.wordless:
                bg_rule = (
                    "Pure solid `#FFFFFF` upper sky/background (minimal grounded floor/props flush to bottom "
                    "allowed when scripted, no floating islands or blurry vignettes); silent dramatic shot."
                )
            else:
                zone = "top ~36%" if slot.is_narrow else "top ~32% or opposite ~44% side"
                bg_rule = (
                    f"Pure solid `#FFFFFF` background with {zone} completely empty for speech bubble "
                    f"(speaker: {cut.tail_target}); minimal grounded floor/props allowed when scripted."
                )

        panel_blocks.append(
            f"### PANEL {slot.slot_index} ({slot.position_label} | {border_tag})\n"
            f"- Cast: {chars_str}\n"
            f"- Action: {cut.visual_prompt.strip()}\n"
            f"- Framing & BG: {bg_rule}"
        )

    panels_section = "\n\n".join(panel_blocks)

    if all_fb:
        bg_summary = "BACKGROUND MODE (FULL-BLEED): Fill every boxed panel edge-to-edge with cohesive WoW scenery, keeping bubble areas unobstructed and outer margins/gutters pure `#FFFFFF`."
    elif any_fb:
        bg_summary = (
            f"BACKGROUND MODE ({eff_style.upper()}): Panels marked FULL-BLEED BOX fill edge-to-edge with WoW "
            "scenery (open sky for bubbles); all other panels use crisp pure `#FFFFFF` backgrounds "
            "(optional natural bottom ground flush to border, no floating miniature islands or blurry vignettes)."
        )
    else:
        bg_summary = (
            "BACKGROUND MODE (CLEAN WHITE): Keep all panel skies, margins, and gutters pure solid `#FFFFFF` "
            "(optional natural bottom ground/props flush to border when scripted; no floating islands or blurry vignettes)."
        )

    return (
        f"Draw a crisp 2:3 Korean anime gag webtoon page (Act {act.act_number}: {act.act_title} | "
        f"`{act.layout_id}`, {layout.panel_count} panels) in sleek 3-to-3.5 head proportions matching "
        "Reference Image 1.\n\n"
        f"REFERENCE IMAGES:\n{refs_block}\n\n"
        f"{anchors}\n\n"
        f"PANELS:\n\n{panels_section}\n\n"
        f"{bg_summary}\n\n"
        f"{lore_hints}\n\n"
        "TECHNICAL REQUIREMENTS:\n"
        "- Align strictly to Reference Image 2's 2:3 panel geometry with 100% pure `#FFFFFF` outer margins and gutters.\n"
        "- Vary camera angles and expressions cleanly across every panel on the page; avoid stubby 2-head dolls or duplicate clone extras.\n"
        "- Zero text, zero Korean/English letters, zero digits/panel numbers, zero speech bubbles, zero SFX, zero watermarks."
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
    companion_pairs = get_companion_turnaround_paths(act_characters, cfg.turnarounds_dir)
    use_cast_fallback = len(turnaround_pairs) == 0

    prompt = build_page_batch_prompt(
        act,
        attached_turnarounds=[f"{m.name} ({m.id})" for m, _ in turnaround_pairs],
        attached_companions=[
            f"{m.companion_name} ({m.companion_id}, companion of {m.name})"
            for m, _ in companion_pairs
        ],
        full_bleed_bg=(eff_style == "full_bleed"),
        background_style=eff_style,
        has_cast_sheet_fallback=use_cast_fallback,
    )

    # Style-First attachment order: [text, style_ref, layout_blueprint, *active_turnarounds, *companion_turnarounds]
    input_items: list[dict[str, Any]] = [
        {"type": "text", "text": prompt},
        {"type": "image", "data": style_b64, "mime_type": style_mime},
        {"type": "image", "data": bp_b64, "mime_type": bp_mime},
    ]
    if turnaround_pairs:
        for _member, turnaround_path in turnaround_pairs:
            t_b64, t_mime = _encode_image_base64(turnaround_path)
            input_items.append({"type": "image", "data": t_b64, "mime_type": t_mime})
    else:
        cast_b64, cast_mime = _encode_image_base64(cfg.cast_sheet_path)
        input_items.append({"type": "image", "data": cast_b64, "mime_type": cast_mime})
    for _owner, comp_path in companion_pairs:
        c_b64, c_mime = _encode_image_base64(comp_path)
        input_items.append({"type": "image", "data": c_b64, "mime_type": c_mime})

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
        (186, 230, 253),
        (221, 214, 254),
        (187, 247, 208),
        (254, 240, 138),
        (254, 205, 211),
    )
    bg_palette: tuple[tuple[int, int, int], ...] = (
        (126, 178, 224),
        (168, 146, 198),
        (134, 184, 152),
        (218, 182, 128),
        (158, 174, 196),
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

            draw.ellipse(
                (cx - r, cy - r, cx + r, cy + r),
                fill=fill_col,
                outline=(30, 41, 59),
                width=4,
            )
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
