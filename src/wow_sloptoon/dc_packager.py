"""Policy-compliant DCInside WOW Forever Gallery manual upload packager.

IMPORTANT POLICY GUARANTEE:
- This module NEVER solves, bypasses, or automates CAPTCHAs or anti-bot challenges.
- This module NEVER performs automated POST submissions or headless form posting.
- It ONLY prepares local upload-ready JPG files + title/body text files, copies text
  to the user's clipboard on request, and opens the official DCInside write page in
  the user's default web browser so the user manually logs in, passes CAPTCHA,
  attaches images, and submits the post.
"""

from __future__ import annotations

import ctypes
import io
import os
import re
import shutil
import subprocess
import sys
import webbrowser
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from wow_sloptoon.config import DEFAULT_ARCHIVE_BASE_URL
from wow_sloptoon.models import EpisodeRecord

DEFAULT_GALLERY_ID: str = "wowforever"
DC_WRITE_URL_TEMPLATE: str = "https://gall.dcinside.com/mgallery/board/write/?id={gallery_id}"

# Safe attachment limits for DCInside minor gallery uploads
DEFAULT_MAX_FILE_BYTES: int = int(4.5 * 1024 * 1024)  # 4.5 MiB safe ceiling
DEFAULT_MAX_SLICE_HEIGHT: int = 6000                  # Safe vertical height per image

_GALLERY_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


@dataclass
class DcUploadPack:
    """Bundle of local upload-ready files and copy-paste metadata for DCInside manual upload."""

    pack_dir: Path
    image_paths: list[Path]
    title_text: str
    body_text: str
    write_url: str


def build_dc_write_url(gallery_id: str = DEFAULT_GALLERY_ID) -> str:
    """Return the official DCInside minor gallery write page URL."""
    gid = (gallery_id or DEFAULT_GALLERY_ID).strip()
    if not gid or not _GALLERY_ID_RE.match(gid):
        raise ValueError(f"Invalid DCInside gallery_id: {gallery_id!r}")
    return DC_WRITE_URL_TEMPLATE.format(gallery_id=gid)


def open_dc_write_page(gallery_id: str = DEFAULT_GALLERY_ID) -> str:
    """Open the official DCInside gallery write page in the user's default browser.

    Login, CAPTCHA verification, image attachment, and final submission are always
    performed directly by the user in their visible browser window.
    """
    url = build_dc_write_url(gallery_id)
    try:
        webbrowser.open(url, new=2)
    except Exception:
        pass
    return url


def _is_headless_or_ci() -> bool:
    """Return True when running in CI or a non-GUI headless environment."""
    for env_key in ("CI", "GITHUB_ACTIONS", "SLOPTOON_HEADLESS"):
        if os.environ.get(env_key, "").strip():
            return True
    if sys.platform.startswith("linux") and not (
        os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
    ):
        return True
    return False


def open_pack_folder(pack_dir: Path) -> bool:
    """Open the local DCInside upload pack folder in the OS file explorer safely.

    Uses `os.startfile` on Windows so the user can drag-and-drop watermarked JPGs
    into the official DCInside editor. Safe no-op in headless/CI environments; never raises.
    """
    target = Path(pack_dir).expanduser().resolve()
    if not target.exists() or _is_headless_or_ci():
        return False

    try:
        if sys.platform == "win32" and hasattr(os, "startfile"):
            os.startfile(str(target))  # type: ignore[attr-defined]
            return True
        if sys.platform == "darwin":
            subprocess.Popen(
                ["open", str(target)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        opener = shutil.which("xdg-open")
        if opener:
            subprocess.Popen(
                [opener, str(target)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
    except Exception:
        return False
    return False


def _copy_windows_ctypes(text: str) -> bool:
    """Copy Unicode text losslessly to the Windows clipboard via Win32 CF_UNICODETEXT."""
    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.restype = ctypes.c_int
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.restype = ctypes.c_void_p

    user32.OpenClipboard.argtypes = [ctypes.c_void_p]
    user32.OpenClipboard.restype = ctypes.c_int
    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = ctypes.c_int
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = ctypes.c_int

    data = (text + "\x00").encode("utf-16-le")
    h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
    if not h_mem:
        return False

    ptr = kernel32.GlobalLock(h_mem)
    if not ptr:
        kernel32.GlobalFree(h_mem)
        return False

    try:
        ctypes.memmove(ptr, data, len(data))
    finally:
        kernel32.GlobalUnlock(h_mem)

    if not user32.OpenClipboard(None):
        kernel32.GlobalFree(h_mem)
        return False

    try:
        user32.EmptyClipboard()
        if not user32.SetClipboardData(CF_UNICODETEXT, h_mem):
            kernel32.GlobalFree(h_mem)
            return False
        # Clipboard now owns h_mem; do not free it
        return True
    finally:
        user32.CloseClipboard()


def _copy_tkinter(text: str) -> bool:
    """Fallback clipboard copy using Python's built-in tkinter module."""
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        try:
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
        finally:
            root.destroy()
        return True
    except Exception:
        return False


def copy_to_clipboard(text: str) -> bool:
    """Safely copy UTF-8/Korean text to the OS clipboard with cross-platform fallbacks.

    Never raises; returns True if a clipboard backend succeeded, False otherwise.
    """
    if sys.platform == "win32":
        try:
            if _copy_windows_ctypes(text):
                return True
        except Exception:
            pass
        if _copy_tkinter(text):
            return True
        try:
            proc = subprocess.run(
                ["clip"],
                input=text.encode("utf-16-le"),
                check=False,
                capture_output=True,
                timeout=5,
            )
            if proc.returncode == 0:
                return True
        except Exception:
            pass
        return False

    if sys.platform == "darwin":
        try:
            proc = subprocess.run(
                ["pbcopy"],
                input=text.encode("utf-8"),
                check=False,
                capture_output=True,
                timeout=5,
            )
            if proc.returncode == 0:
                return True
        except Exception:
            pass
        return _copy_tkinter(text)

    # Linux / BSD clipboard backends
    for cmd in (
        ["wl-copy"],
        ["xclip", "-selection", "clipboard"],
        ["xsel", "--clipboard", "--input"],
    ):
        if shutil.which(cmd[0]):
            try:
                proc = subprocess.run(
                    cmd,
                    input=text.encode("utf-8"),
                    check=False,
                    capture_output=True,
                    timeout=5,
                )
                if proc.returncode == 0:
                    return True
            except Exception:
                continue

    return _copy_tkinter(text)


def _encode_jpeg_under_limit(
    im: Image.Image,
    max_file_bytes: int,
    qualities: tuple[int, ...] = (93, 88, 84, 78, 72),
) -> bytes | None:
    """Encode an RGB PIL image to JPEG bytes trying progressively lower quality levels."""
    rgb = im.convert("RGB")
    for q in qualities:
        buf = io.BytesIO()
        subsampling = 0 if q >= 90 else 2
        rgb.save(buf, format="JPEG", quality=q, optimize=True, subsampling=subsampling)
        raw = buf.getvalue()
        if len(raw) <= max_file_bytes:
            return raw
    return None


def _find_white_gutter_y(
    rgb_arr: np.ndarray,
    ideal_y: int,
    min_y: int,
    max_y: int,
    search_radius: int = 360,
) -> int:
    """Find the center of the widest pure-white horizontal gutter near `ideal_y`."""
    lo = max(min_y, ideal_y - search_radius)
    hi = min(max_y, ideal_y + search_radius)
    if hi <= lo:
        return max(min_y, min(max_y, ideal_y))

    band = rgb_arr[lo:hi, :, :]
    is_white_row = np.all(band >= 250, axis=(1, 2))
    if not np.any(is_white_row):
        return max(min_y, min(max_y, ideal_y))

    # Find longest contiguous run of white rows (break ties by proximity to ideal_y)
    best_start = -1
    best_len = 0
    best_dist = 10**9
    run_start = -1
    for i, flag in enumerate(is_white_row):
        if flag:
            if run_start == -1:
                run_start = i
        else:
            if run_start != -1:
                run_len = i - run_start
                mid = lo + run_start + run_len // 2
                dist = abs(mid - ideal_y)
                if run_len > best_len or (run_len == best_len and dist < best_dist):
                    best_len = run_len
                    best_start = run_start
                    best_dist = dist
                run_start = -1
    if run_start != -1:
        run_len = len(is_white_row) - run_start
        mid = lo + run_start + run_len // 2
        dist = abs(mid - ideal_y)
        if run_len > best_len or (run_len == best_len and dist < best_dist):
            best_len = run_len
            best_start = run_start
            best_dist = dist

    if best_start == -1 or best_len == 0:
        return max(min_y, min(max_y, ideal_y))
    return lo + best_start + best_len // 2


def _prepare_upload_images(
    full_image_path: Path,
    pack_dir: Path,
    episode_id: str,
    max_file_bytes: int,
    max_slice_height: int,
) -> list[Path]:
    """Optimize or safely split `full_image_path` into DCInside-compliant JPG files."""
    if not full_image_path.exists():
        raise FileNotFoundError(f"Full episode image not found: {full_image_path}")

    with Image.open(full_image_path) as src_im:
        rgb_im = src_im.convert("RGB")

    w, h = rgb_im.size
    src_size = full_image_path.stat().st_size
    is_already_jpeg = full_image_path.suffix.lower() in {".jpg", ".jpeg"}

    # Fast path: fits both height and file-size limits in a single crisp JPG
    if h <= max_slice_height:
        single_path = pack_dir / f"{episode_id}_full.jpg"
        if is_already_jpeg and src_size <= max_file_bytes:
            shutil.copy2(full_image_path, single_path)
            return [single_path]
        encoded = _encode_jpeg_under_limit(rgb_im, max_file_bytes=max_file_bytes)
        if encoded is not None:
            single_path.write_bytes(encoded)
            return [single_path]

    # Split vertically along pure-white gutters until every slice fits both height and byte limits
    rgb_arr = np.asarray(rgb_im)
    min_slices_by_height = max(2, int(np.ceil(h / max(1, max_slice_height))))
    min_slices_by_bytes = max(1, int(np.ceil(src_size / max(1, int(max_file_bytes * 0.85)))))
    n_slices = max(min_slices_by_height, min_slices_by_bytes)

    while n_slices <= 20:
        cuts = [0]
        min_slice_h = max(64, h // (n_slices * 3))
        for k in range(1, n_slices):
            ideal_y = int(round(h * k / n_slices))
            min_y = cuts[-1] + min_slice_h
            max_y = h - min_slice_h * (n_slices - k)
            if max_y <= min_y:
                cut_y = ideal_y
            else:
                cut_y = _find_white_gutter_y(rgb_arr, ideal_y, min_y, max_y)
            cuts.append(cut_y)
        cuts.append(h)

        # Ensure every slice respects max_slice_height and max_file_bytes
        slice_blobs: list[bytes] = []
        all_ok = True
        for y0, y1 in zip(cuts[:-1], cuts[1:]):
            if (y1 - y0) > max_slice_height:
                all_ok = False
                break
            part_im = rgb_im.crop((0, y0, w, y1))
            blob = _encode_jpeg_under_limit(part_im, max_file_bytes=max_file_bytes)
            if blob is None:
                all_ok = False
                break
            slice_blobs.append(blob)

        if all_ok:
            # Remove any stale single-file output before writing slices
            stale_single = pack_dir / f"{episode_id}_full.jpg"
            if stale_single.exists():
                stale_single.unlink()

            out_paths: list[Path] = []
            for idx, blob in enumerate(slice_blobs, start=1):
                part_path = pack_dir / f"{episode_id}_part_{idx:02d}.jpg"
                part_path.write_bytes(blob)
                out_paths.append(part_path)
            return out_paths

        n_slices += 1

    raise RuntimeError(
        f"Unable to compress/split {full_image_path} under {max_file_bytes} bytes per image."
    )


def format_post_title(record: EpisodeRecord) -> str:
    """Format canonical DCInside WOW Forever Gallery comic post title (`[와포슬롭툰]{원본념글제목}`)."""
    return f"[와포슬롭툰]{record.title.strip()}"


def format_post_body(
    record: EpisodeRecord,
    archive_base_url: str = DEFAULT_ARCHIVE_BASE_URL,
) -> str:
    """Format canonical DCInside WOW Forever Gallery post body with prominent archive links."""
    base = (archive_base_url or DEFAULT_ARCHIVE_BASE_URL).strip().rstrip("/")
    if not base:
        base = DEFAULT_ARCHIVE_BASE_URL

    lines: list[str] = []
    if record.subtitle.strip():
        lines.append(record.subtitle.strip())
        lines.append("")

    lines.extend(
        [
            f"전편 정주행 아카이브: {base}/episodes/{record.episode_id}.html",
            f"전체 목록: {base}",
            f"웹 뷰어 바로가기: {base}/episode.html?id={record.episode_id}",
            "",
        ]
    )

    if record.cast_used:
        cast_str = " · ".join(record.cast_used)
        lines.append(f"등장 캐릭터 (시안 C): {cast_str}")

    lines.append(f"원본 개념글 (#{record.source_post_no}): {record.source_url}")

    lines.extend(
        [
            "",
            "---",
            "와우 포에버 슬롭툰 — 디시 WOW 포에버 마이너 갤러리 개념글 상황극 봇 (시안 C)",
        ]
    )
    return "\n".join(lines) + "\n"


def create_dc_upload_pack(
    record: EpisodeRecord,
    full_image_path: Path,
    output_dir: Path,
    archive_base_url: str = DEFAULT_ARCHIVE_BASE_URL,
    *,
    gallery_id: str = DEFAULT_GALLERY_ID,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    max_slice_height: int = DEFAULT_MAX_SLICE_HEIGHT,
) -> DcUploadPack:
    """Build a local manual-upload package for DCInside WOW Forever Gallery.

    Produces inside `output_dir`:
    - Optimized single JPG (`{episode_id}_full.jpg`) or cleanly white-gutter-split
      JPG parts (`{episode_id}_part_01.jpg`, ...) strictly within DCInside size/height limits
    - `post_title.txt`: ready-to-paste title (`[와포슬롭툰]{원본념글제목}`)
    - `post_body.txt`: ready-to-paste body with concept post attribution, archive link, and bot credit
    - `upload_guide.txt`: 3-step manual posting reminder (no CAPTCHA bypass or auto-submit)
    """
    pack_dir = Path(output_dir)
    pack_dir.mkdir(parents=True, exist_ok=True)

    image_paths = _prepare_upload_images(
        full_image_path=Path(full_image_path),
        pack_dir=pack_dir,
        episode_id=record.episode_id,
        max_file_bytes=max_file_bytes,
        max_slice_height=max_slice_height,
    )

    title_text = format_post_title(record)
    body_text = format_post_body(record, archive_base_url=archive_base_url)
    write_url = build_dc_write_url(gallery_id)

    (pack_dir / "post_title.txt").write_text(title_text, encoding="utf-8")
    (pack_dir / "post_body.txt").write_text(body_text, encoding="utf-8")

    img_list = "\n".join(f"  - {p.name}" for p in image_paths)
    guide_text = (
        "=== 디시 WOW 포에버 마이너 갤러리 수동 업로드 안내 ===\n"
        f"공식 글쓰기 URL: {write_url}\n\n"
        "1. 브라우저에서 공식 글쓰기 페이지를 열고 직접 로그인하세요.\n"
        "2. post_title.txt 내용을 제목 칸에 붙여넣으세요.\n"
        "3. 아래 이미지 파일을 순서대로 본문에 첨부하세요:\n"
        f"{img_list}\n"
        "4. post_body.txt 내용을 본문 하단에 붙여넣고, 캡차(자동등록방지)를 직접 입력한 뒤 등록 버튼을 클릭하세요.\n"
    )
    (pack_dir / "upload_guide.txt").write_text(guide_text, encoding="utf-8")

    return DcUploadPack(
        pack_dir=pack_dir,
        image_paths=image_paths,
        title_text=title_text,
        body_text=body_text,
        write_url=write_url,
    )
