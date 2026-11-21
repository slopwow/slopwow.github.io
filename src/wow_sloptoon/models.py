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
        description="Direction the speech-bubble tail points toward the speaker.",
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
    source_title: str = Field(..., description="Origin post title (or polished episode title).")
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
