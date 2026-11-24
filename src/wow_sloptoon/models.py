"""Shared Pydantic v2 data models for wow-forever-sloptoon."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    """A single panel/cut inside a 4~6 cut sloptoon episode."""

    model_config = ConfigDict(extra="ignore")

    cut_index: int = Field(..., ge=0, description="1-based (or 0-based) cut index in order.")
    aspect_ratio: Literal["4:3", "16:9"] = Field(
        ..., description="Target image aspect ratio ('4:3' for top open cut, '16:9' for bottom box)."
    )
    layout_slot: Literal["top", "bottom"] = Field(
        ..., description="Slot position on a 2-tier sloptoon page."
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
        if self.wordless:
            self.speaker = None
            self.dialogue = None
        return self


class EpisodeScript(BaseModel):
    """Complete 4~6 cut live-action dungeon/game skit script for one episode."""

    model_config = ConfigDict(extra="ignore")

    episode_number: int = Field(..., ge=1, description="Sequential episode number (e.g. 1, 2, 3).")
    source_post_no: str = Field(..., description="Origin DCInside wowforever post number.")
    source_title: str = Field(
        ..., description="Exact verbatim original DCInside wowforever concept post title."
    )
    source_url: str = Field(..., description="Origin DCInside wowforever post URL.")
    subtitle: str = Field(..., description="Witty short Korean subtitle shown in the episode header.")
    cuts: list[ComicCut] = Field(
        ...,
        min_length=4,
        max_length=6,
        description="Ordered list of 4 to 6 comic cuts.",
    )

    @model_validator(mode="after")
    def validate_episode_rules(self) -> "EpisodeScript":
        if not (4 <= len(self.cuts) <= 6):
            raise ValueError(
                f"EpisodeScript must have between 4 and 6 cuts, got {len(self.cuts)}."
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
