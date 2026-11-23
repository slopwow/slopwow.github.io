"""Comic cut illustrator powered by Google GenAI Interactions API (`gemini-nano-banana-2.1`).

Generates pure `#FFFFFF` borderless Draft C cute pop-gag chibi cuts using the official
Draft C cast sheet, the sloptoon layout/linework reference image, Clean Hand anchors,
consistent medium chibi framing, and WoW Forever visual anti-hallucination guardrails.
"""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import Any

from google import genai
from PIL import Image, ImageDraw

from wow_sloptoon.cast import build_character_anchors_block
from wow_sloptoon.config import (
    DEFAULT_IMAGE_MODEL,
    SUPPORTED_IMAGE_MODELS,
    Settings,
    load_settings,
)
from wow_sloptoon.models import ComicCut, EpisodeScript
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


def build_cut_image_prompt(cut: ComicCut) -> str:
    """Construct the exact image-generation prompt with Draft C Clean Hand anchors & WoW Forever rules."""
    anchors = build_character_anchors_block(cut.characters)
    lore_hints = build_cut_visual_lore_hints(cut.visual_prompt, cut.characters)

    if cut.wordless:
        framing_note = (
            "COMPOSITION & SCALE: Centered solo comedic chest-up close-up freeze-frame reaction shot "
            "(silent panel; character fills ~75-85% of canvas height). Place the character squarely in "
            "the center with expressive deadpan/shocked trembling pupils and crisp comedic impact. "
            "No room needed for speech bubbles."
        )
    elif cut.layout_slot == "top":
        framing_note = (
            "COMPOSITION & SCALE: Open top-slot 4:3 comic panel. Frame the character(s) at a consistent "
            "medium 2.5-to-3-head waist-up or knee-up chibi scale (filling ~55-68% of canvas height) "
            "in the lower two-thirds of the canvas, leaving generous pure white (#FFFFFF) headroom at "
            "the top 30-35% for external speech-bubble placement. NEVER shrink characters into tiny "
            f"distant full-body micro-chibis. Primary speaker position cue: {cut.tail_target}."
        )
    elif len(cut.characters) >= 2:
        framing_note = (
            "COMPOSITION & SCALE: Wide bottom-slot 16:9 two-character reaction panel. Frame BOTH "
            "characters prominently at a consistent medium 2.5-to-3-head waist-up/knee-up chibi scale "
            "(filling ~55-68% of canvas height, matching the 4:3 panel character size — NEVER zoom out "
            "into tiny distant full-body micro-chibis!). Arrange them snugly in the lower two-thirds or "
            "speaker-side half with generous pure white (#FFFFFF) space near the upper/opposite side "
            f"for external speech-bubble placement. Primary speaker position cue: {cut.tail_target}."
        )
    else:
        framing_note = (
            "COMPOSITION & SCALE: Wide bottom-slot 16:9 solo reaction panel. Frame the character "
            "prominently at a consistent medium 2.5-to-3-head waist-up/knee-up chibi scale "
            "(filling ~58-70% of canvas height, matching the 4:3 panel character size) positioned cleanly "
            "toward the speaker side with generous pure white (#FFFFFF) space near the upper/opposite "
            f"side for external speech-bubble placement. Primary speaker position cue: {cut.tail_target}."
        )

    return (
        "Draw a single Korean pop-gag anime chibi comic cut in the exact cute cel-shaded "
        "style of Reference Image 1 (Draft C Cast Sheet) and crisp minimalist white-canvas "
        "linework feel of Reference Image 2 (Sloptoon Style Reference).\n\n"
        f"{anchors}\n\n"
        f"SCENE ACTION (Cut #{cut.cut_index}):\n{cut.visual_prompt.strip()}\n\n"
        f"{lore_hints}\n\n"
        f"{framing_note}\n\n"
        "ABSOLUTE TECHNICAL REQUIREMENTS:\n"
        "- 100% PURE SOLID WHITE (#FFFFFF) BACKGROUND ONLY — zero scenery, zero gray shading, "
        "zero gradient backdrop, zero ground shadows outside tiny contact lines.\n"
        "- ZERO TEXT, ZERO KOREAN/ENGLISH LETTERS, ZERO DIGITS/NUMBERS, ZERO SPEECH BUBBLES, "
        "ZERO SOUND EFFECTS, ZERO PANEL BORDERS, ZERO WATERMARKS.\n"
        "- Match every character's exact hood, horns/ears, hair color/gradient, eye color, and "
        "outfit from Reference Image 1 with 100% visual consistency; HOWEVER, obey the CLEAN HAND "
        "RULE — sheath/stow on back or waist, or omit a character's default weapon/prop whenever "
        "holding scene-specific loot, a tank shield, a loot die, a hearthstone, a potion flask, "
        "or gesturing (NEVER draw 3+ weapons/props in one character's hands).\n"
        "- CONSISTENT MEDIUM CHIBI SCALE: Maintain consistent 2.5-to-3-head waist-up/knee-up chibi "
        "proportions across both 4:3 and 16:9 cuts (never shrink characters to tiny micro-chibis)."
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
    prompt = build_cut_image_prompt(cut)

    interaction = client.interactions.create(
        model=target_model,
        input=[
            {"type": "text", "text": prompt},
            {"type": "image", "data": cast_b64, "mime_type": cast_mime},
            {"type": "image", "data": style_b64, "mime_type": style_mime},
        ],
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
