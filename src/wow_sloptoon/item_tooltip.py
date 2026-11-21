"""Authentic Korean Classic / Turtle WoW item tooltip card renderer and Wowhead resolver.

Supports two rendering modes for `ComicCut.item_tooltip` (`ItemTooltipSpec`):
1. Cropped in-game tooltip screenshot framing (`image_path`, e.g. `assets/items/scepter_of_the_librarian.png`)
   preserving crisp native Korean pixel typography at ~260-310px readable width.
2. Programmatic Classic WoW dark tooltip card (`#0B0D16` dark navy interior, 4x-supersampled 2px
   metallic gold/silver-grey rounded border, authentic WoW quality colors `#A335EE` / `#0070DD` /
   `#1EFF00` / `#FFFFFF`, green `#1EFF00` `착용 효과:` lines, and optional `wow.zamimg.com` icon badge),
   auto-populated live from Korean Classic Era Wowhead (`dataEnv=4&locale=1`) with deterministic
   offline/Turtle-WoW fallbacks.
"""

from __future__ import annotations

import html
import io
import json
import os
import re
import urllib.request
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from wow_sloptoon.models import ItemTooltipSpec, TooltipCorner, TooltipQuality

__all__ = [
    "EQUIP_GREEN",
    "ItemTooltipSpec",
    "ParsedWowheadItem",
    "QUALITY_COLORS",
    "STAT_WHITE",
    "TOOLTIP_BG_DARK",
    "TOOLTIP_BORDER_GOLD",
    "TooltipCorner",
    "TooltipQuality",
    "fetch_wowhead_classic_item",
    "fetch_wowhead_icon",
    "parse_wowhead_tooltip_html",
    "render_item_tooltip",
    "resolve_tooltip_spec",
]

# Authentic Classic WoW UI tooltip color palette
TOOLTIP_BG_DARK: tuple[int, int, int] = (11, 13, 22)          # #0B0D16 deep translucent-style navy
TOOLTIP_BG_TOP: tuple[int, int, int] = (18, 21, 35)           # Subtle upper-card dark slate sheen
TOOLTIP_BORDER_GOLD: tuple[int, int, int] = (198, 176, 138)   # #C6B08A Classic metallic gold/grey rim
TOOLTIP_BORDER_OUTER: tuple[int, int, int] = (20, 20, 24)     # Crisp dark outer hairline on #FFFFFF
TOOLTIP_BORDER_INNER: tuple[int, int, int] = (4, 5, 10)       # Inner bevel shadow

QUALITY_COLORS: dict[str, tuple[int, int, int]] = {
    "epic": (163, 53, 238),       # #A335EE Epic purple
    "rare": (0, 112, 221),        # #0070DD Rare blue
    "uncommon": (30, 255, 0),     # #1EFF00 Uncommon green
    "common": (255, 255, 255),    # #FFFFFF Common white
}
STAT_WHITE: tuple[int, int, int] = (255, 255, 255)            # #FFFFFF stats / binding / slot
EQUIP_GREEN: tuple[int, int, int] = (30, 255, 0)              # #1EFF00 착용/발동/사용 효과

WOWHEAD_CLASSIC_ERA_URL = "https://nether.wowhead.com/tooltip/item/{item_id}?dataEnv=4&locale=1"
WOWHEAD_CLASSIC_FALLBACK_URL = (
    "https://nether.wowhead.com/classic/tooltip/item/{item_id}?dataEnv=1&locale=1"
)
WOWHEAD_ICON_URL = "https://wow.zamimg.com/images/wow/icons/large/{icon}.jpg"
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) WowForeverSloptoon/1.0"

_WOWHEAD_QUALITY_MAP: dict[int, TooltipQuality] = {
    5: "epic",
    4: "epic",
    3: "rare",
    2: "uncommon",
    1: "common",
    0: "common",
}


@dataclass(frozen=True)
class ParsedWowheadItem:
    """Normalized Korean Classic WoW item tooltip data."""

    item_name: str
    quality: TooltipQuality
    slot_left: str = ""
    slot_right: str = ""
    lines: tuple[str, ...] = ()
    equip_effects: tuple[str, ...] = ()
    icon_name: str | None = None


# Offline / CI / custom Turtle WoW presets so iconic Scarlet Monastery & custom items
# always render 100% authentic Classic Korean stats even without internet access.
_BUILTIN_ITEMS_BY_ID: dict[int, ParsedWowheadItem] = {
    7722: ParsedWowheadItem(
        item_name="삼위일체의 아뮬렛",
        quality="rare",
        slot_left="목",
        slot_right="",
        lines=("획득 시 귀속", "체력 +7", "지능 +7", "정신력 +7", "요구 레벨 39"),
        equip_effects=(),
        icon_name="inv_jewelry_amulet_01",
    ),
    7720: ParsedWowheadItem(
        item_name="화이트메인의 모자",
        quality="rare",
        slot_left="머리",
        slot_right="천",
        lines=("획득 시 귀속", "방어도 52", "체력 +9", "지능 +14", "정신력 +14", "요구 레벨 39"),
        equip_effects=(),
        icon_name="inv_helmet_12",
    ),
    7721: ParsedWowheadItem(
        item_name="정의의 망치",
        quality="rare",
        slot_left="주장비",
        slot_right="둔기",
        lines=("획득 시 귀속", "공격력 56 - 105\t속도 2.70", "(초당 공격력 29.81)", "정신력 +8", "요구 레벨 39"),
        equip_effects=("착용 효과: 모든 주문 및 효과에 의한 치유량이 최대 15만큼 증가합니다.",),
        icon_name="inv_hammer_02",
    ),
    7717: ParsedWowheadItem(
        item_name="폭풍의 눈",
        quality="rare",
        slot_left="양손 장비",
        slot_right="도끼",
        lines=("획득 시 귀속", "공격력 104 - 157\t속도 3.50", "(초당 공격력 37.29)", "요구 레벨 37"),
        equip_effects=("발동 효과: 9초 동안 주위 모든 적을 공격하여 매 3초마다 무기 피해와 추가로 5의 피해를 입힙니다.",),
        icon_name="inv_weapon_halberd_05",
    ),
}

_BUILTIN_ITEMS_BY_NAME: dict[str, ParsedWowheadItem] = {
    "삼위일체의 아뮬렛": _BUILTIN_ITEMS_BY_ID[7722],
    "삼위일체 아뮬렛": _BUILTIN_ITEMS_BY_ID[7722],
    "화이트메인의 모자": _BUILTIN_ITEMS_BY_ID[7720],
    "화이트메인의 수놓인 모자": ParsedWowheadItem(
        item_name="화이트메인의 수놓인 모자",
        quality="rare",
        slot_left="머리",
        slot_right="천",
        lines=("획득 시 귀속", "방어도 52", "체력 +9", "지능 +14", "정신력 +14", "요구 레벨 39"),
        equip_effects=(),
        icon_name="inv_helmet_12",
    ),
    "사서의 홀": ParsedWowheadItem(
        item_name="사서의 홀",
        quality="uncommon",
        slot_left="주장비",
        slot_right="둔기",
        lines=("귀속 아이템", "공격력 21 - 39\t속도 2.30", "(초당 공격력 13.0)", "지능 +6"),
        equip_effects=("착용 효과: 마법 주문 및 효과로 입히는 피해와 치유량이 최대 30만큼 증가합니다.",),
        icon_name="inv_mace_01",
    ),
}

_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_EXTRA_TAG_RE = re.compile(r'<b[^>]*class="[^"]*whtt-extra[^"]*"[^>]*>.*?</b>', re.DOTALL | re.IGNORECASE)
_SELLPRICE_RE = re.compile(r'<div[^>]*class="[^"]*whtt-sellprice[^"]*"[^>]*>.*?</div>', re.DOTALL | re.IGNORECASE)
_ILVL_SPAN_RE = re.compile(r'<span[^>]*class="q"[^>]*>\s*(?:<br\s*/?>)?\s*아이템 레벨.*?</span>', re.DOTALL)
_TWO_COL_TABLE_RE = re.compile(
    r'<table\s+width="100%"[^>]*>\s*<tr>\s*<td>(.*?)</td>\s*<th>(.*?)</th>\s*</tr>\s*</table>',
    re.DOTALL | re.IGNORECASE,
)
_Q2_SPAN_RE = re.compile(
    r'<span[^>]*class="q2"[^>]*>(?:(?!<span).)*?</span>',
    re.DOTALL | re.IGNORECASE,
)


def _strip_html(fragment: str) -> str:
    no_comments = _COMMENT_RE.sub("", fragment)
    no_tags = _TAG_RE.sub("", no_comments)
    text = html.unescape(no_tags)
    return re.sub(r"[ \t\r\f\v]+", " ", text).strip()


def parse_wowhead_tooltip_html(payload: dict[str, Any]) -> ParsedWowheadItem:
    """Parse a Korean Classic Wowhead JSON tooltip payload into structured Classic fields."""
    raw_name = str(payload.get("name") or "").strip()
    q_int = int(payload.get("quality", 3))
    quality: TooltipQuality = _WOWHEAD_QUALITY_MAP.get(q_int, "rare")
    icon_raw = str(payload.get("icon") or "").strip().lower() or None
    raw_html = str(payload.get("tooltip") or "")

    if not raw_html:
        return ParsedWowheadItem(
            item_name=raw_name or "알 수 없는 아이템",
            quality=quality,
            icon_name=icon_raw,
        )

    work = _EXTRA_TAG_RE.sub("", raw_html)
    work = _SELLPRICE_RE.sub("", work)
    work = _ILVL_SPAN_RE.sub("", work)

    slot_left = ""
    slot_right = ""

    def _replace_two_col(match: re.Match[str]) -> str:
        nonlocal slot_left, slot_right
        left_txt = _strip_html(match.group(1))
        right_txt = _strip_html(match.group(2))
        if not left_txt and not right_txt:
            return ""
        is_weapon_dmg = ("공격력" in left_txt) or ("속도" in right_txt)
        if not is_weapon_dmg and not slot_left:
            slot_left = left_txt
            slot_right = right_txt
            return "\n"
        if right_txt:
            return f"\n{left_txt}\t{right_txt}\n"
        return f"\n{left_txt}\n"

    work = _TWO_COL_TABLE_RE.sub(_replace_two_col, work)

    equip_effects: list[str] = []

    def _extract_q2(match: re.Match[str]) -> str:
        txt = _strip_html(match.group(0))
        if txt:
            equip_effects.append(txt)
        return "\n"

    work = _Q2_SPAN_RE.sub(_extract_q2, work)

    work = re.sub(r"<br\s*/?>", "\n", work, flags=re.IGNORECASE)
    work = re.sub(r"</(?:tr|table|div|p)>", "\n", work, flags=re.IGNORECASE)
    work = _COMMENT_RE.sub("", work)
    work = _TAG_RE.sub("", work)
    work = html.unescape(work)

    stat_lines: list[str] = []
    for raw_ln in work.splitlines():
        if "\t" in raw_ln:
            parts = [re.sub(r"\s+", " ", p).strip() for p in raw_ln.split("\t", 1)]
            cleaned_ln = f"{parts[0]}\t{parts[1]}" if parts[1] else parts[0]
        else:
            cleaned_ln = re.sub(r"\s+", " ", raw_ln).strip()

        if not cleaned_ln:
            continue
        if raw_name and cleaned_ln == raw_name:
            continue
        if cleaned_ln.startswith(("아이템 레벨", "내구도 ", "판매 가격:")):
            continue
        stat_lines.append(cleaned_ln)

    return ParsedWowheadItem(
        item_name=raw_name or "알 수 없는 아이템",
        quality=quality,
        slot_left=slot_left,
        slot_right=slot_right,
        lines=tuple(stat_lines),
        equip_effects=tuple(equip_effects),
        icon_name=icon_raw,
    )


def _http_get_bytes(url: str, timeout: float) -> bytes | None:
    if os.environ.get("SLOPTOON_OFFLINE_TOOLTIPS", "").strip() == "1":
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if getattr(resp, "status", 200) == 200:
                return resp.read()
    except Exception:
        return None
    return None


@lru_cache(maxsize=128)
def fetch_wowhead_classic_item(item_id: int, timeout: float = 4.5) -> ParsedWowheadItem | None:
    """Query Korean Classic Era Wowhead for `item_id`, falling back cleanly if offline."""
    for template in (WOWHEAD_CLASSIC_ERA_URL, WOWHEAD_CLASSIC_FALLBACK_URL):
        raw = _http_get_bytes(template.format(item_id=int(item_id)), timeout=timeout)
        if raw:
            try:
                payload = json.loads(raw.decode("utf-8"))
                if isinstance(payload, dict) and (payload.get("name") or payload.get("tooltip")):
                    return parse_wowhead_tooltip_html(payload)
            except Exception:
                continue
    return _BUILTIN_ITEMS_BY_ID.get(int(item_id))


@lru_cache(maxsize=128)
def _fetch_wowhead_icon_bytes(icon_slug: str, timeout: float = 3.5) -> bytes | None:
    clean_slug = re.sub(r"[^a-z0-9_-]", "", icon_slug.strip().lower())
    if not clean_slug:
        return None
    return _http_get_bytes(WOWHEAD_ICON_URL.format(icon=clean_slug), timeout=timeout)


def fetch_wowhead_icon(icon_name: str | None, timeout: float = 3.5) -> Image.Image | None:
    """Download and decode a `wow.zamimg.com` item icon, returning None gracefully if offline."""
    if not icon_name:
        return None
    raw = _fetch_wowhead_icon_bytes(icon_name, timeout=timeout)
    if not raw:
        return None
    try:
        with Image.open(io.BytesIO(raw)) as im:
            return im.convert("RGB")
    except Exception:
        return None


def _default_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_tooltip_image_path(image_path: str, project_root: Path | None = None) -> Path | None:
    root = Path(project_root) if project_root is not None else _default_project_root()
    p = Path(image_path)
    candidates = [p] if p.is_absolute() else [Path.cwd() / p, root / p, root / "assets" / p]
    for cand in candidates:
        if cand.exists() and cand.is_file():
            return cand
    return None


def resolve_tooltip_spec(
    spec: ItemTooltipSpec,
    *,
    fetch_network: bool = True,
) -> ItemTooltipSpec:
    """Populate missing Korean Classic tooltip fields from Wowhead or built-in presets."""
    fetched: ParsedWowheadItem | None = None
    if spec.wowhead_item_id is not None:
        if fetch_network:
            fetched = fetch_wowhead_classic_item(spec.wowhead_item_id)
        else:
            fetched = _BUILTIN_ITEMS_BY_ID.get(spec.wowhead_item_id)

    if fetched is None and spec.item_name:
        fetched = _BUILTIN_ITEMS_BY_NAME.get(spec.item_name.strip())

    if fetched is None:
        return spec

    has_manual_stats = bool(spec.lines or spec.equip_effects or spec.slot_left or spec.slot_right)
    merged_name = (spec.item_name or "").strip() or fetched.item_name
    merged_icon = spec.icon_name or fetched.icon_name

    if has_manual_stats:
        return spec.model_copy(
            update={
                "item_name": merged_name,
                "icon_name": merged_icon,
            }
        )

    # Use Wowhead quality unless caller explicitly specified non-default quality without wowhead_item_id
    merged_quality: TooltipQuality = fetched.quality if spec.wowhead_item_id is not None or spec.quality == "rare" else spec.quality
    return spec.model_copy(
        update={
            "item_name": merged_name,
            "quality": merged_quality,
            "slot_left": fetched.slot_left,
            "slot_right": fetched.slot_right,
            "lines": list(fetched.lines),
            "equip_effects": list(fetched.equip_effects),
            "icon_name": merged_icon,
        }
    )


def _load_tooltip_font(size: int, weight: str = "Bold") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load crisp Korean UI font for WoW tooltips (delegates to composer font search)."""
    from wow_sloptoon.composer import load_font

    return load_font(size, weight=weight)


def _wrap_pixel_line(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_w: float,
) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []
    if float(draw.textlength(cleaned, font=font)) <= max_w:
        return [cleaned]

    words = cleaned.split(" ")
    lines: list[str] = []
    cur = ""
    for word in words:
        cand = f"{cur} {word}".strip() if cur else word
        if float(draw.textlength(cand, font=font)) <= max_w:
            cur = cand
            continue
        if cur:
            lines.append(cur)
            cur = ""
        if float(draw.textlength(word, font=font)) <= max_w:
            cur = word
        else:
            buf = ""
            for ch in word:
                if buf and float(draw.textlength(buf + ch, font=font)) > max_w:
                    lines.append(buf)
                    buf = ch
                else:
                    buf += ch
            cur = buf
    if cur:
        lines.append(cur)
    return lines


def _draw_shadowed_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: tuple[int, int, int],
) -> None:
    x, y = xy
    draw.text((x + 1, y + 1), text, font=font, fill=(0, 0, 0, 235))
    draw.text((x, y), text, font=font, fill=(*fill, 255))


def _frame_screenshot_tooltip(
    src_path: Path,
    target_width: int,
) -> Image.Image:
    """Frame a real cropped WoW tooltip screenshot cleanly at ~260-310px width."""
    with Image.open(src_path) as im:
        rgba = im.convert("RGBA")

    sw, sh = rgba.size
    # Preserve razor-sharp 1:1 pixel glyphs when screenshot is already in ~260-310px range
    if 256 <= sw <= 312 and abs(sw - target_width) <= 14:
        scaled = rgba
    else:
        nw = max(180, int(round(target_width)))
        nh = max(48, int(round(sh * (nw / max(1, sw)))))
        scaled = rgba.resize((nw, nh), Image.Resampling.LANCZOS)

    iw, ih = scaled.size
    pad = 3
    cw, ch = iw + pad * 2, ih + pad * 2

    S = 4
    frame_4x = Image.new("RGBA", (cw * S, ch * S), (0, 0, 0, 0))
    d4 = ImageDraw.Draw(frame_4x)
    rad4 = 6 * S
    d4.rounded_rectangle(
        [0, 0, cw * S - 1, ch * S - 1],
        radius=rad4,
        fill=(*TOOLTIP_BORDER_OUTER, 255),
    )
    d4.rounded_rectangle(
        [S, S, (cw - 1) * S - 1, (ch - 1) * S - 1],
        radius=max(2, rad4 - S),
        fill=(*TOOLTIP_BORDER_GOLD, 255),
    )
    d4.rounded_rectangle(
        [3 * S, 3 * S, (cw - 3) * S - 1, (ch - 3) * S - 1],
        radius=max(2, rad4 - 3 * S),
        fill=(*TOOLTIP_BG_DARK, 255),
    )
    card = frame_4x.resize((cw, ch), Image.Resampling.BOX)

    # Apply rounded corner mask to screenshot so corners stay anti-aliased
    mask_4x = Image.new("L", (iw * S, ih * S), 0)
    ImageDraw.Draw(mask_4x).rounded_rectangle(
        [0, 0, iw * S - 1, ih * S - 1],
        radius=3 * S,
        fill=255,
    )
    mask_1x = mask_4x.resize((iw, ih), Image.Resampling.BOX)
    clipped = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))
    clipped.paste(scaled, (0, 0), mask=mask_1x)
    card.alpha_composite(clipped, dest=(pad, pad))
    return card


def render_item_tooltip(
    spec: ItemTooltipSpec | None,
    *,
    project_root: Path | None = None,
    fetch_network: bool = True,
) -> Image.Image | None:
    """Render an `ItemTooltipSpec` into an authentic RGBA WoW tooltip card (`~260-310px` wide)."""
    if spec is None:
        return None

    # Mode 1: Direct cropped WoW tooltip screenshot (e.g. scepter_of_the_librarian.png)
    if spec.image_path:
        resolved_img = _resolve_tooltip_image_path(spec.image_path, project_root=project_root)
        if resolved_img is not None:
            return _frame_screenshot_tooltip(resolved_img, target_width=spec.target_width)
        if not spec.item_name and spec.wowhead_item_id is None:
            raise FileNotFoundError(f"Tooltip screenshot image_path not found: {spec.image_path}")

    resolved = resolve_tooltip_spec(spec, fetch_network=fetch_network)
    title_text = (resolved.item_name or "").strip()
    if not title_text and resolved.wowhead_item_id is not None:
        title_text = f"아이템 #{resolved.wowhead_item_id}"
    if not title_text:
        return None

    icon_im = fetch_wowhead_icon(resolved.icon_name) if fetch_network else None

    card_w = int(np.clip(resolved.target_width, 256, 320))
    pad_x = 13
    pad_y = 11
    inner_w = card_w - pad_x * 2

    f_title = _load_tooltip_font(16, weight="Bold")
    f_body = _load_tooltip_font(13, weight="Medium")
    f_equip = _load_tooltip_font(13, weight="Medium")
    dummy = ImageDraw.Draw(Image.new("RGBA", (16, 16), (0, 0, 0, 0)))

    icon_box = 36 if icon_im is not None else 0
    header_text_x = pad_x + (icon_box + 9 if icon_box else 0)
    header_max_w = float(card_w - pad_x - header_text_x)

    title_lines = _wrap_pixel_line(dummy, title_text, f_title, header_max_w)
    title_col = QUALITY_COLORS.get(resolved.quality, QUALITY_COLORS["rare"])

    # Separate optional first binding line to sit neatly beside the icon under the title
    remaining_lines = list(resolved.lines)
    sub_header_line: str | None = None
    if icon_box and remaining_lines and "\t" not in remaining_lines[0] and len(remaining_lines[0]) <= 16:
        sub_header_line = remaining_lines.pop(0)

    def _line_h(fnt: Any, sample: str = "가Ag") -> int:
        bb = dummy.textbbox((0, 0), sample, font=fnt)
        return max(12, int(bb[3] - bb[1]))

    th_title = _line_h(f_title)
    th_body = _line_h(f_body)
    th_equip = _line_h(f_equip)
    line_gap = 4

    # Pre-calculate layout instructions: list of (kind, y, payload)
    ops: list[tuple[str, int, Any]] = []
    cur_y = pad_y
    for t_ln in title_lines:
        ops.append(("title", cur_y, (header_text_x, t_ln)))
        cur_y += th_title + 3

    if sub_header_line:
        ops.append(("single", cur_y, (header_text_x, sub_header_line, STAT_WHITE, f_body)))
        cur_y += th_body + 3

    if icon_box:
        cur_y = max(cur_y, pad_y + icon_box + 5)
    else:
        cur_y += 1

    if resolved.slot_left or resolved.slot_right:
        ops.append(("twocol", cur_y, (resolved.slot_left.strip(), resolved.slot_right.strip())))
        cur_y += th_body + line_gap

    for raw_ln in remaining_lines:
        if "\t" in raw_ln:
            left_s, right_s = raw_ln.split("\t", 1)
            ops.append(("twocol", cur_y, (left_s.strip(), right_s.strip())))
            cur_y += th_body + line_gap
        else:
            for w_ln in _wrap_pixel_line(dummy, raw_ln, f_body, float(inner_w)):
                ops.append(("single", cur_y, (pad_x, w_ln, STAT_WHITE, f_body)))
                cur_y += th_body + line_gap

    if resolved.equip_effects:
        cur_y += 1
        for eff in resolved.equip_effects:
            for w_ln in _wrap_pixel_line(dummy, eff, f_equip, float(inner_w)):
                ops.append(("single", cur_y, (pad_x, w_ln, EQUIP_GREEN, f_equip)))
                cur_y += th_equip + 3

    card_h = max(62, cur_y - line_gap + pad_y + 2)

    # Render 4x-supersampled dark navy card + 2px metallic Classic WoW gold/grey rounded border
    S = 4
    layer_4x = Image.new("RGBA", (card_w * S, card_h * S), (0, 0, 0, 0))
    d4 = ImageDraw.Draw(layer_4x)
    rad4 = 7 * S
    outer_w = S                  # 1px crisp dark outer edge
    gold_w = round(2.0 * S)      # 2px metallic Classic WoW tooltip rim
    inner_bevel = S              # 1px dark inner bevel

    d4.rounded_rectangle(
        [0, 0, card_w * S - 1, card_h * S - 1],
        radius=rad4,
        fill=(*TOOLTIP_BORDER_OUTER, 255),
    )
    d4.rounded_rectangle(
        [outer_w, outer_w, card_w * S - 1 - outer_w, card_h * S - 1 - outer_w],
        radius=max(3, rad4 - outer_w),
        fill=(*TOOLTIP_BORDER_GOLD, 255),
    )
    in_pad = outer_w + gold_w
    d4.rounded_rectangle(
        [in_pad, in_pad, card_w * S - 1 - in_pad, card_h * S - 1 - in_pad],
        radius=max(2, rad4 - in_pad),
        fill=(*TOOLTIP_BORDER_INNER, 255),
    )
    bg_pad = in_pad + inner_bevel
    d4.rounded_rectangle(
        [bg_pad, bg_pad, card_w * S - 1 - bg_pad, card_h * S - 1 - bg_pad],
        radius=max(2, rad4 - bg_pad),
        fill=(*TOOLTIP_BG_DARK, 248),
    )

    card = layer_4x.resize((card_w, card_h), Image.Resampling.BOX)

    # Subtle top-to-bottom Classic WoW tooltip sheen inside the dark interior
    arr = np.asarray(card).copy()
    interior_mask = (
        (arr[:, :, 0] == TOOLTIP_BG_DARK[0])
        & (arr[:, :, 1] == TOOLTIP_BG_DARK[1])
        & (arr[:, :, 2] == TOOLTIP_BG_DARK[2])
    )
    t_grad = np.linspace(1.0, 0.0, card_h, dtype=np.float32)[:, None]
    for c_idx in range(3):
        blended = np.round(
            TOOLTIP_BG_DARK[c_idx] + (TOOLTIP_BG_TOP[c_idx] - TOOLTIP_BG_DARK[c_idx]) * (t_grad ** 1.6)
        ).astype(np.uint8)
        ch_plane = arr[:, :, c_idx]
        arr[:, :, c_idx] = np.where(interior_mask, blended, ch_plane)
    card = Image.fromarray(arr, mode="RGBA")

    draw = ImageDraw.Draw(card)

    # Optional zamimg icon badge in top-left
    if icon_im is not None and icon_box > 0:
        ix, iy = pad_x, pad_y
        draw.rounded_rectangle(
            [ix - 1, iy - 1, ix + icon_box, iy + icon_box],
            radius=4,
            fill=(*TOOLTIP_BORDER_GOLD, 255),
            outline=(0, 0, 0, 255),
            width=1,
        )
        icon_resized = icon_im.resize((icon_box - 2, icon_box - 2), Image.Resampling.LANCZOS).convert("RGBA")
        card.alpha_composite(icon_resized, dest=(ix + 1, iy + 1))
        draw = ImageDraw.Draw(card)

    # Render crisp WoW Korean typography
    for kind, y_pos, payload in ops:
        if kind == "title":
            tx, txt = payload
            bb = draw.textbbox((0, 0), txt, font=f_title)
            _draw_shadowed_text(draw, (tx, y_pos - bb[1]), txt, f_title, title_col)
        elif kind == "single":
            tx, txt, col, fnt = payload
            bb = draw.textbbox((0, 0), txt, font=fnt)
            _draw_shadowed_text(draw, (tx, y_pos - bb[1]), txt, fnt, col)
        elif kind == "twocol":
            left_s, right_s = payload
            if left_s:
                bb_l = draw.textbbox((0, 0), left_s, font=f_body)
                _draw_shadowed_text(draw, (pad_x, y_pos - bb_l[1]), left_s, f_body, STAT_WHITE)
            if right_s:
                bb_r = draw.textbbox((0, 0), right_s, font=f_body)
                rw = float(draw.textlength(right_s, font=f_body))
                rx = round(card_w - pad_x - rw)
                _draw_shadowed_text(draw, (rx, y_pos - bb_r[1]), right_s, f_body, STAT_WHITE)

    return card
