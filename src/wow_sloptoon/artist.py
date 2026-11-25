"""Single-cut SD comic illustrator powered by Google GenAI Interactions API (`gemini-nano-banana-2.1`).

Route A Single Canonical Art Style (2-to-2.5 head cute plump Korean anime SD chibi):
- Reference Image 1 is ALWAYS `assets/diorama_style_ref.jpg` (STYLE ONLY: 2-2.5 head round
  soft SD chibi proportions, thin crisp ink, clean 2-tier cel shading, lively gag faces,
  pure #FFFFFF background — never copy the characters from Ref 1).
- Active character 2.5-head turnaround sheets (`assets/turnarounds/<id>.jpg`) follow as
  COSTUME/HAIR/COLOR references only with lively dynamic scene poses (never stiff front A-pose).
- Fixed round companion mascot sheets (`hunter_bear.jpg`, `warlock_voidwalker.jpg`) attach
  automatically when Dwarf Hunter or Human Warlock appears.
"""

from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor
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


def build_cut_image_prompt(
    cut: ComicCut,
    *,
    attached_turnarounds: list[str] | None = None,
    attached_companions: list[str] | None = None,
    has_cast_sheet_fallback: bool = False,
) -> str:
    """Construct a compact (1,200~1,800 char) 2-to-2.5 head cute SD comic cut prompt."""
    anchors = build_character_anchors_block(cut.characters)
    lore_hints = build_cut_visual_lore_hints(cut.visual_prompt, cut.characters)

    ref_lines = [
        "- Ref 1 (`diorama_style_ref.jpg`): STYLE ONLY — cute plump 2-to-2.5 head round soft SD chibi, "
        "thin crisp ink, 2-tier cel shading, lively gag faces, pure #FFFFFF. DO NOT copy Ref 1's characters!"
    ]
    next_idx = 2
    if attached_turnarounds:
        for label in attached_turnarounds:
            ref_lines.append(
                f"- Ref {next_idx} — {label}: COSTUME/HAIR/COLOR ONLY, lively dynamic pose (NO stiff A-pose)."
            )
            next_idx += 1
    elif has_cast_sheet_fallback:
        ref_lines.append(
            f"- Ref {next_idx} — cast sheet: COSTUME/HAIR/COLOR ONLY in cute 2-to-2.5 head SD style, dynamic pose."
        )
        next_idx += 1
    if attached_companions:
        for comp_label in attached_companions:
            ref_lines.append(
                f"- Ref {next_idx} — {comp_label}: cute round SD mascot reacting beside owner."
            )
            next_idx += 1
    refs_block = "\n".join(ref_lines)

    if cut.wordless:
        framing_note = (
            "FRAME: Silent big bust-up/close-up filling 75-85% canvas height with exaggerated gag face "
            "on pure #FFFFFF (no bubble space needed)."
        )
    elif cut.layout_slot == "top":
        framing_note = (
            "FRAME (4:3 top): Top 30% pure #FFFFFF empty for bubble; lower 70% large 2-to-2.5 head SD "
            f"cast (58-68% height). Speaker: {cut.tail_target}."
        )
    else:
        framing_note = (
            "FRAME (16:9): Large 2-to-2.5 head SD cast (62-75% height) with pure #FFFFFF bubble space "
            f"at top or opposite side. Speaker: {cut.tail_target}."
        )

    return (
        "Draw 1 Korean anime gag comic cut in cute plump 2-to-2.5 head SD chibi style (Ref 1).\n"
        f"REFS:\n{refs_block}\n"
        f"{anchors}\n"
        f"SCENE (#{cut.cut_index}): {cut.visual_prompt.strip()}\n"
        f"{framing_note}\n"
        f"{lore_hints}\n"
        "RULES: All extras, mobs, bosses, NPCs, mounts, animals, or bodies MUST match cute 2-to-2.5 head SD style. "
        "Pure #FFFFFF bg (optional minimal natural floor/prop touch under feet; NO rectangular bg blocks, gray washes, "
        "or borders). Zero text, letters, digits, speech bubbles, SFX, watermarks."
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
    """Generate a single pure-#FFFFFF 2-to-2.5 head cute SD comic cut via Gemini Interactions API."""
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

    # Attachment order: [prompt_text, Ref1=diorama_style_ref.jpg, Ref2..=active turnarounds (or cast_sheet fallback), Ref_pet=companions]
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

    aspect_ratio = cut.aspect_ratio if cut.aspect_ratio in ("4:3", "16:9") else (
        "4:3" if cut.layout_slot == "top" else "16:9"
    )

    interaction = client.interactions.create(
        model=target_model,
        input=input_items,
        response_format={
            "type": "image",
            "aspect_ratio": aspect_ratio,
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
    max_workers: int = 3,
) -> dict[int, Path]:
    """Generate raw cut images for all 4~7 cuts in an `EpisodeScript` (parallel when max_workers > 1)."""
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
