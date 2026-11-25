"""Shared Pydantic v2 data models for wow-forever-sloptoon."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from wow_sloptoon.layouts import get_page_layout


PageLayoutId = Literal[
    "open_top_split_bottom",
    "split_top_wide_bottom",
    "diagonal_tempo_2cut",
    "impact_freeze_2cut",
    "wide_reaction_wide",
    "four_beat_gag",
]

BackgroundStyle = Literal["clean_white", "full_bleed", "selective_mix"]


class GalleryPost(BaseModel):
    """A scraped post from the DCInside wowforever minor gallery."""

    model_config = ConfigDict(extra="ignore")

    post_no: str = Field(..., description="Unique DCInside post number.")
    title: str = Field(..., description="Post title text.")
    url: str = Field(..., description="Canonical view URL for the post.")
    author: str = Field(..., description="Author nickname or identifier.")
    date_str: str = Field(..., description="Displayed creation timestamp string.")
    views: int = Field(default=0, ge=0, description="View count.")
    recommends: int = Field(default=0, ge=0, description="Recommend (upvote) count.")
    comments_count: int = Field(default=0, ge=0, description="Comment count.")
    body: str = Field(default="", description="Cleaned plain-text body of the post.")
    comments: list[str] = Field(
        default_factory=list,
        description="Selected top reader comments (plain text).",
    )


TooltipQuality = Literal["epic", "rare", "uncommon", "common"]
TooltipCorner = Literal["auto", "top_left", "top_right", "bottom_left", "bottom_right"]


class ItemTooltipSpec(BaseModel):
    """Authentic Korean Classic/Turtle WoW item tooltip overlay specification for a comic cut."""

    model_config = ConfigDict(extra="ignore")

    image_path: Optional[str] = Field(
        default=None,
        description=(
            "Optional path to a cropped WoW item tooltip screenshot "
            "(e.g. 'assets/items/scepter_of_the_librarian.png')."
        ),
    )
    item_name: Optional[str] = Field(
        default=None,
        description="Korean item display name (e.g. '삼위일체의 아뮬렛', '사서의 홀').",
    )
    wowhead_item_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="Korean Classic Wowhead item ID (e.g. 7722 for Triune Amulet, 7720 for Whitemane's Chapeau).",
    )
    quality: TooltipQuality = Field(
        default="rare",
        description="WoW item quality tier ('epic', 'rare', 'uncommon', 'common').",
    )
    slot_left: str = Field(
        default="",
        description="Equipment slot label on left (e.g. '목', '머리', '주장비').",
    )
    slot_right: str = Field(
        default="",
        description="Subtype label on right (e.g. '천', '둔기', '도끼').",
    )
    lines: list[str] = Field(
        default_factory=list,
        description="White stat/binding lines (use 'left\\tright' for two-column weapon damage/speed).",
    )
    equip_effects: list[str] = Field(
        default_factory=list,
        description="Green (#1EFF00) equip/use/proc effect lines (e.g. '착용 효과: ...').",
    )
    icon_name: Optional[str] = Field(
        default=None,
        description="Optional Wowhead/zamimg icon name (e.g. 'inv_jewelry_amulet_01').",
    )
    preferred_corner: TooltipCorner = Field(
        default="auto",
        description="Optional placement hint ('auto', 'top_left', 'top_right', 'bottom_left', 'bottom_right').",
    )
    target_width: int = Field(
        default=288,
        ge=180,
        le=420,
        description="Target rendered width in pixels (~260-310px).",
    )


class ComicCut(BaseModel):
    """A single panel/cut inside a classic (4~6 cut) or V4 5-act (10~14 cut) sloptoon episode."""

    model_config = ConfigDict(extra="ignore")

    cut_index: int = Field(..., ge=0, description="1-based (or 0-based) cut index in order.")
    aspect_ratio: Literal["4:3", "16:9", "2:3", "3:4", "1:1", "auto"] = Field(
        default="auto",
        description=(
            "Target image aspect ratio ('4:3' for classic top open cut, '16:9' for classic bottom box, "
            "or 'auto'/'2:3'/'3:4'/'1:1' for V4 variable-layout panels)."
        ),
    )
    layout_slot: Literal["top", "bottom", "panel"] = Field(
        default="panel",
        description="Slot position on a classic 2-tier page ('top'/'bottom') or V4 page ('panel').",
    )
    act_number: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Optional 1-based act number (1..5) for V4 5-act episodes.",
    )
    panel_index: Optional[int] = Field(
        default=None,
        ge=1,
        le=4,
        description="Optional 1-based panel slot index (1..4) inside a V4 ActPage.",
    )
    characters: list[str] = Field(
        ...,
        min_length=1,
        max_length=2,
        description="1 to 2 canonical cast names appearing in this cut.",
    )
    speaker: Optional[str] = Field(
        default=None,
        description="Speaking character name (None when wordless=True).",
    )
    dialogue: Optional[str] = Field(
        default=None,
        description="Korean speech-bubble text (None when wordless=True).",
    )
    wordless: bool = Field(
        default=False,
        description="True for signature silent deadpan/shocked freeze-frame reaction cuts.",
    )
    visual_prompt: str = Field(
        ...,
        min_length=1,
        description="Detailed English visual scene prompt for image generation (pure #FFFFFF background).",
    )
    tail_target: Literal["left", "right", "center"] = Field(
        default="left",
        description="Speaker side inside the cut ('left', 'right', or 'center') that the speech-bubble tail points toward.",
    )
    bubble_side: Optional[Literal["left", "right", "center"]] = Field(
        default=None,
        description=(
            "Optional explicit horizontal side for placing the speech bubble inside a cut "
            "('left', 'right', or 'center'). Overrides auto side selection when needed."
        ),
    )
    full_bleed_bg: bool = Field(
        default=False,
        description=(
            "True to fill panel edge-to-edge with full-bleed background and overlay "
            "speech bubble on open background area."
        ),
    )
    speaker_anchor_xy: Optional[tuple[float, float]] = Field(
        default=None,
        description=(
            "Optional normalized (x_ratio, y_ratio) in [0.05..0.95] pointing directly to "
            "the speaker's head/mouth inside the panel for pinpoint speech-bubble tail aiming."
        ),
    )
    bubble_center_xy: Optional[tuple[float, float]] = Field(
        default=None,
        description=(
            "Optional normalized (x_ratio, y_ratio) override for exact speech-bubble "
            "placement inside full-bleed panels."
        ),
    )
    item_tooltip: Optional[ItemTooltipSpec] = Field(
        default=None,
        description="Optional authentic WoW item tooltip card overlay displayed in an open corner of this cut.",
    )

    @model_validator(mode="after")
    def validate_cut_rules(self) -> "ComicCut":
        if not (1 <= len(self.characters) <= 2):
            raise ValueError(
                f"Cut {self.cut_index} must feature 1 to 2 characters, got {len(self.characters)}."
            )
        for field_name, coords in (
            ("speaker_anchor_xy", self.speaker_anchor_xy),
            ("bubble_center_xy", self.bubble_center_xy),
        ):
            if coords is not None:
                x_r, y_r = coords
                if not (0.0 <= float(x_r) <= 1.0 and 0.0 <= float(y_r) <= 1.0):
                    raise ValueError(
                        f"Cut {self.cut_index} {field_name} ratios must be within [0.0, 1.0], got {coords}."
                    )
        if self.wordless:
            self.speaker = None
            self.dialogue = None
        return self


class ActPage(BaseModel):
    """A single variable-layout page representing one act (1..5) in a V4 5-act episode."""

    model_config = ConfigDict(extra="ignore")

    act_number: int = Field(..., ge=1, le=5, description="1-based act number (1..5).")
    act_title: str = Field(..., min_length=1, description="Short Korean title for this act.")
    layout_id: PageLayoutId = Field(..., description="Variable 900x1350 page layout identifier.")
    cuts: list[ComicCut] = Field(
        ...,
        min_length=1,
        max_length=4,
        description="Ordered comic panels filling every slot of `layout_id`.",
    )

    @model_validator(mode="after")
    def validate_act_layout(self) -> "ActPage":
        spec = get_page_layout(self.layout_id)
        if len(self.cuts) != spec.panel_count:
            raise ValueError(
                f"Act {self.act_number} with layout_id='{self.layout_id}' requires exactly "
                f"{spec.panel_count} cuts, got {len(self.cuts)}."
            )
        for p_idx, cut in enumerate(self.cuts, start=1):
            cut.act_number = self.act_number
            cut.panel_index = p_idx
        return self


class EpisodeScript(BaseModel):
    """Complete live-action dungeon/game skit script for one episode (classic 2-tier or V4 5-act)."""

    model_config = ConfigDict(extra="ignore")

    episode_number: int = Field(..., ge=1, description="Sequential episode number (e.g. 1, 2, 3).")
    source_post_no: str = Field(..., description="Origin DCInside wowforever post number.")
    source_title: str = Field(
        ..., description="Exact verbatim original DCInside wowforever concept post title."
    )
    source_url: str = Field(..., description="Origin DCInside wowforever post URL.")
    subtitle: str = Field(..., description="Witty short Korean subtitle shown in the episode header.")
    layout_mode: Literal["classic_2tier", "v4_five_act"] = Field(
        default="classic_2tier",
        description="Page layout mode: 'classic_2tier' (4~8 cuts) or 'v4_five_act' (5 acts, 10~14 cuts).",
    )
    background_style: BackgroundStyle = Field(
        default="clean_white",
        description=(
            "Panel background mode ('clean_white' for pure #FFFFFF cuts, "
            "'full_bleed' for edge-to-edge colored comic backgrounds on every panel, "
            "'selective_mix' for per-cut mix of 100% full-bleed boxed cuts and 100% pure #FFFFFF cuts)."
        ),
    )
    acts: Optional[list[ActPage]] = Field(
        default=None,
        description="5 ordered variable-layout ActPage objects when layout_mode='v4_five_act'.",
    )
    cuts: list[ComicCut] = Field(
        default_factory=list,
        description="Ordered list of comic cuts (4~8 in classic_2tier, 10~14 flattened in v4_five_act).",
    )

    @model_validator(mode="after")
    def validate_episode_rules(self) -> "EpisodeScript":
        if self.acts is not None or self.layout_mode == "v4_five_act":
            self.layout_mode = "v4_five_act"
            if self.acts is None or len(self.acts) != 5:
                actual = 0 if self.acts is None else len(self.acts)
                raise ValueError(
                    f"V4 EpisodeScript must have exactly 5 acts, got {actual}."
                )
            act_numbers = [act.act_number for act in self.acts]
            if act_numbers != [1, 2, 3, 4, 5]:
                raise ValueError(
                    f"V4 EpisodeScript act_numbers must be [1, 2, 3, 4, 5], got {act_numbers}."
                )

            flattened: list[ComicCut] = []
            seq = 1
            for act in self.acts:
                for p_idx, cut in enumerate(act.cuts, start=1):
                    cut.act_number = act.act_number
                    cut.panel_index = p_idx
                    cut.cut_index = seq
                    flattened.append(cut)
                    seq += 1
            self.cuts = flattened

            if not (10 <= len(self.cuts) <= 14):
                raise ValueError(
                    f"V4 EpisodeScript must have between 10 and 14 total cuts, got {len(self.cuts)}."
                )
        else:
            if not (4 <= len(self.cuts) <= 8):
                raise ValueError(
                    f"EpisodeScript must have between 4 and 8 cuts, got {len(self.cuts)}."
                )

        for cut in self.cuts:
            if not (1 <= len(cut.characters) <= 2):
                raise ValueError(
                    f"Cut {cut.cut_index} must have 1 to 2 characters, got {len(cut.characters)}."
                )
        if not any(cut.wordless for cut in self.cuts):
            raise ValueError(
                "EpisodeScript must contain at least one wordless freeze-frame cut (wordless=True)."
            )
        return self


class EpisodeRecord(BaseModel):
    """Archive index metadata persisted in data/episodes.json."""

    model_config = ConfigDict(extra="ignore")

    episode_id: str = Field(..., description="Zero-padded identifier such as 'ep001'.")
    episode_number: int = Field(..., ge=1, description="Sequential episode number.")
    title: str = Field(..., description="Display episode title.")
    subtitle: str = Field(..., description="Short episode subtitle.")
    source_post_no: str = Field(..., description="Origin DCInside wowforever post number.")
    source_url: str = Field(..., description="Origin DCInside wowforever post URL.")
    created_at: str = Field(..., description="ISO-8601 timestamp or YYYY-MM-DD creation date.")
    cut_count: int = Field(..., ge=1, description="Number of comic cuts in the episode.")
    cast_used: list[str] = Field(
        default_factory=list,
        description="Canonical names of cast members appearing in this episode.",
    )
    full_image_rel: str = Field(
        ..., description="Relative path to the stitched full-length episode JPG."
    )
    thumb_image_rel: str = Field(
        ..., description="Relative path to the episode card thumbnail JPG."
    )
    page_images_rel: list[str] = Field(
        default_factory=list,
        description="Relative paths to individual composed page PNG/JPG files.",
    )
