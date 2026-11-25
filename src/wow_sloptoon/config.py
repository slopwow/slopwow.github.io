"""Runtime configuration and canonical project paths for wow-forever-sloptoon."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_TEXT_MODEL = "gemini-4-hydrogen"
DEFAULT_IMAGE_MODEL = "gemini-nano-banana-2.1"
SUPPORTED_IMAGE_MODELS: tuple[str, ...] = (
    "gemini-nano-banana-2.1",
    "gemini-3-pro-image",
    "gemini-3.1-flash-lite-image",
)
DEFAULT_GALLERY_ID = "wowforever"
DEFAULT_ARCHIVE_BASE_URL = "https://slopwow.github.io"
PAID_API_OPT_IN_ENV = "SLOPTOON_ALLOW_PAID_API"


def require_paid_api_opt_in(caller: str) -> None:
    """Hard-lock paid Gemini API calls unless explicitly opted in via `SLOPTOON_ALLOW_PAID_API=1`.

    Prevents accidental credit/billing spend when `GEMINI_API_KEY` happens to be present
    in the user environment. Default illustration workflow uses built-in `image-generator`
    (zero API billing) + local `cli compose` / `build-site`.
    """
    flag = os.getenv(PAID_API_OPT_IN_ENV, "").strip().lower()
    if flag not in {"1", "true", "yes"}:
        raise RuntimeError(
            f"Paid Gemini API call blocked in {caller}: set {PAID_API_OPT_IN_ENV}=1 "
            "ONLY after explicit user approval. Default workflow uses built-in "
            "image-generator + local `cli compose` (zero API billing)."
        )


def resolve_project_root(start: Path | None = None) -> Path:
    """Resolve the wow-forever-sloptoon project root directory."""
    env_root = os.getenv("SLOPTOON_PROJECT_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    if start is not None:
        candidate = start.expanduser().resolve()
        if (candidate / "pyproject.toml").exists():
            return candidate

    # Package lives at <root>/src/wow_sloptoon/config.py
    pkg_root = Path(__file__).resolve().parents[2]
    if (pkg_root / "pyproject.toml").exists():
        return pkg_root

    cwd = Path.cwd().resolve()
    if (cwd / "pyproject.toml").exists():
        return cwd

    return pkg_root


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables and project paths."""

    project_root: Path
    assets_dir: Path
    data_dir: Path
    episodes_json: Path
    episodes_dir: Path
    site_dir: Path
    cast_sheet_path: Path
    turnarounds_dir: Path
    style_ref_path: Path
    gemini_api_key: str
    text_model: str
    image_model: str
    gallery_id: str
    archive_base_url: str

    @property
    def gallery_recommend_url(self) -> str:
        return (
            f"https://gall.dcinside.com/mgallery/board/lists/"
            f"?id={self.gallery_id}&exception_mode=recommend"
        )


def load_settings(project_root: Path | None = None) -> Settings:
    """Load `.env` (if present) and construct immutable `Settings`."""
    root = resolve_project_root(project_root)
    env_file = root / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=False)
    else:
        load_dotenv(override=False)

    assets_dir = root / "assets"
    data_dir = root / "data"
    episodes_dir = data_dir / "episodes"
    site_dir = root / "site"

    text_model = os.getenv("SLOPTOON_TEXT_MODEL", DEFAULT_TEXT_MODEL).strip() or DEFAULT_TEXT_MODEL
    image_model = (
        os.getenv("SLOPTOON_IMAGE_MODEL", DEFAULT_IMAGE_MODEL).strip() or DEFAULT_IMAGE_MODEL
    )
    gallery_id = os.getenv("SLOPTOON_GALLERY_ID", DEFAULT_GALLERY_ID).strip() or DEFAULT_GALLERY_ID
    archive_base_url = (
        os.getenv("SLOPTOON_ARCHIVE_BASE_URL", DEFAULT_ARCHIVE_BASE_URL).strip().rstrip("/")
        or DEFAULT_ARCHIVE_BASE_URL
    )
    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()

    return Settings(
        project_root=root,
        assets_dir=assets_dir,
        data_dir=data_dir,
        episodes_json=data_dir / "episodes.json",
        episodes_dir=episodes_dir,
        site_dir=site_dir,
        cast_sheet_path=assets_dir / "cast_sheet_c.jpg",
        turnarounds_dir=assets_dir / "turnarounds",
        style_ref_path=assets_dir / "diorama_style_ref.jpg",
        gemini_api_key=gemini_api_key,
        text_model=text_model,
        image_model=image_model,
        gallery_id=gallery_id,
        archive_base_url=archive_base_url,
    )
