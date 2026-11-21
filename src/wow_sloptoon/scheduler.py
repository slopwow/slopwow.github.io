"""Policy-compliant DCInside publish queue and local automation notification helpers.

IMPORTANT POLICY GUARANTEE:
- This module tracks which episodes have been manually published to DCInside
  (`pending` -> `packed` -> `published`) and dispatches optional local notifications
  to remind the user when a new episode is ready for human review/upload.
- It NEVER automates DCInside login, CAPTCHA solving, anti-bot evasion, or form POSTing.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Sequence
from xml.sax.saxutils import escape as xml_escape

from pydantic import BaseModel, ConfigDict, Field

from wow_sloptoon.config import DEFAULT_ARCHIVE_BASE_URL, Settings, load_settings
from wow_sloptoon.models import EpisodeRecord

PublishStatus = Literal["pending", "packed", "published"]

DEFAULT_QUEUE_FILENAME = "publish_queue.json"
_EP_SHORT_RE = re.compile(r"^ep(\d+)$", re.IGNORECASE)


class PublishQueueItem(BaseModel):
    """Per-episode DCInside manual publishing status tracked in `data/publish_queue.json`."""

    model_config = ConfigDict(extra="ignore")

    episode_id: str = Field(..., description="Zero-padded episode identifier such as 'ep001'.")
    episode_number: int = Field(..., ge=1, description="Sequential episode number.")
    title: str = Field(..., description="Episode display title.")
    source_post_no: str = Field(default="", description="Origin DCInside wowforever post number.")
    status: PublishStatus = Field(
        default="pending",
        description="Manual DCInside publish lifecycle: pending -> packed -> published.",
    )
    queued_at: str = Field(..., description="ISO-8601 timestamp when episode entered the queue.")
    packed_at: str | None = Field(
        default=None,
        description="ISO-8601 timestamp when upload_pack/<ep> was last built.",
    )
    published_at: str | None = Field(
        default=None,
        description="ISO-8601 timestamp when the user confirmed manual DCInside publication.",
    )
    dc_post_url: str = Field(
        default="",
        description="Optional published DCInside post URL recorded after manual upload.",
    )
    pack_dir: str = Field(
        default="",
        description="Local upload pack path prepared for manual drag-and-drop upload.",
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def normalize_episode_id(episode_id: str) -> str:
    """Normalize episode identifiers like '1', 'ep1', 'EP001' into canonical 'ep001'."""
    key = (episode_id or "").strip().lower()
    if key.isdigit():
        return f"ep{int(key):03d}"
    m = _EP_SHORT_RE.match(key)
    if m:
        return f"ep{int(m.group(1)):03d}"
    return key


def default_queue_path(settings: Settings | None = None) -> Path:
    """Return canonical path to `data/publish_queue.json`."""
    resolved = settings or load_settings()
    return resolved.data_dir / DEFAULT_QUEUE_FILENAME


def _load_episode_records_raw(episodes_json: Path) -> list[EpisodeRecord]:
    if not episodes_json.exists():
        return []
    raw_text = episodes_json.read_text(encoding="utf-8").strip()
    if not raw_text:
        return []
    payload = json.loads(raw_text)
    items = payload.get("episodes", []) if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        return []
    records = [EpisodeRecord.model_validate(item) for item in items]
    records.sort(key=lambda r: (r.episode_number, r.episode_id))
    return records


def load_publish_queue(queue_path: Path | None = None) -> list[PublishQueueItem]:
    """Load persisted publish queue items from `data/publish_queue.json`."""
    target = Path(queue_path) if queue_path is not None else default_queue_path()
    if not target.exists():
        return []
    raw_text = target.read_text(encoding="utf-8").strip()
    if not raw_text:
        return []
    payload = json.loads(raw_text)
    raw_items = payload.get("episodes", []) if isinstance(payload, dict) else payload
    if not isinstance(raw_items, list):
        return []
    items = [PublishQueueItem.model_validate(item) for item in raw_items]
    items.sort(key=lambda item: (item.episode_number, item.episode_id))
    return items


def save_publish_queue(
    items: Sequence[PublishQueueItem],
    queue_path: Path | None = None,
) -> Path:
    """Persist publish queue items as structured UTF-8 JSON."""
    target = Path(queue_path) if queue_path is not None else default_queue_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(items, key=lambda item: (item.episode_number, item.episode_id))
    payload = {
        "version": 1,
        "updated_at": _now_iso(),
        "episodes": [item.model_dump(mode="json") for item in ordered],
    }
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target


def sync_publish_queue(
    episodes_json: Path | None = None,
    queue_path: Path | None = None,
) -> list[PublishQueueItem]:
    """Synchronize `data/publish_queue.json` from `data/episodes.json` while preserving status."""
    if episodes_json is None:
        settings = load_settings()
        ep_json = settings.episodes_json
        q_path = Path(queue_path) if queue_path is not None else default_queue_path(settings)
    else:
        ep_json = Path(episodes_json)
        q_path = (
            Path(queue_path)
            if queue_path is not None
            else (ep_json.parent / DEFAULT_QUEUE_FILENAME)
        )

    existing_items = load_publish_queue(q_path)
    by_id: dict[str, PublishQueueItem] = {
        normalize_episode_id(item.episode_id): item for item in existing_items
    }

    records = _load_episode_records_raw(ep_json)
    now = _now_iso()

    for rec in records:
        key = normalize_episode_id(rec.episode_id)
        if key in by_id:
            prev = by_id[key]
            by_id[key] = prev.model_copy(
                update={
                    "episode_id": rec.episode_id,
                    "episode_number": rec.episode_number,
                    "title": rec.title,
                    "source_post_no": rec.source_post_no,
                }
            )
        else:
            by_id[key] = PublishQueueItem(
                episode_id=rec.episode_id,
                episode_number=rec.episode_number,
                title=rec.title,
                source_post_no=rec.source_post_no,
                status="pending",
                queued_at=now,
            )

    synced = sorted(by_id.values(), key=lambda item: (item.episode_number, item.episode_id))
    save_publish_queue(synced, q_path)
    return synced


def get_next_unpublished(
    queue_path: Path | None = None,
    episodes_json: Path | None = None,
) -> PublishQueueItem | None:
    """Return the earliest episode whose DCInside status is not yet `published`."""
    if episodes_json is not None:
        items = sync_publish_queue(episodes_json=episodes_json, queue_path=queue_path)
    elif queue_path is not None:
        items = load_publish_queue(queue_path)
    else:
        settings = load_settings()
        items = sync_publish_queue(
            episodes_json=settings.episodes_json,
            queue_path=default_queue_path(settings),
        )

    for item in items:
        if item.status != "published":
            return item
    return None


def mark_episode_packed(
    episode_id: str,
    pack_dir: Path | str = "",
    *,
    queue_path: Path | None = None,
    episodes_json: Path | None = None,
) -> PublishQueueItem:
    """Record that an episode's DCInside manual upload pack has been prepared (`packed`)."""
    if episodes_json is not None:
        items = sync_publish_queue(episodes_json=episodes_json, queue_path=queue_path)
        target_q = (
            Path(queue_path)
            if queue_path is not None
            else (Path(episodes_json).parent / DEFAULT_QUEUE_FILENAME)
        )
    elif queue_path is not None:
        target_q = Path(queue_path)
        items = load_publish_queue(target_q)
    else:
        settings = load_settings()
        target_q = default_queue_path(settings)
        items = sync_publish_queue(episodes_json=settings.episodes_json, queue_path=target_q)

    target_key = normalize_episode_id(episode_id)
    now = _now_iso()
    updated_item: PublishQueueItem | None = None
    new_items: list[PublishQueueItem] = []

    for item in items:
        if normalize_episode_id(item.episode_id) == target_key:
            next_status: PublishStatus = "published" if item.status == "published" else "packed"
            updated_item = item.model_copy(
                update={
                    "status": next_status,
                    "packed_at": now,
                    "pack_dir": str(pack_dir) if pack_dir else item.pack_dir,
                }
            )
            new_items.append(updated_item)
        else:
            new_items.append(item)

    if updated_item is None:
        raise KeyError(f"Episode '{episode_id}' not found in publish queue ({target_q}).")

    save_publish_queue(new_items, target_q)
    return updated_item


def mark_episode_published(
    episode_id: str,
    dc_post_url: str = "",
    *,
    queue_path: Path | None = None,
    episodes_json: Path | None = None,
) -> PublishQueueItem:
    """Mark an episode as manually published to DCInside with an optional `dc_post_url`."""
    if episodes_json is not None:
        items = sync_publish_queue(episodes_json=episodes_json, queue_path=queue_path)
        target_q = (
            Path(queue_path)
            if queue_path is not None
            else (Path(episodes_json).parent / DEFAULT_QUEUE_FILENAME)
        )
    elif queue_path is not None:
        target_q = Path(queue_path)
        items = load_publish_queue(target_q)
    else:
        settings = load_settings()
        target_q = default_queue_path(settings)
        items = sync_publish_queue(episodes_json=settings.episodes_json, queue_path=target_q)

    target_key = normalize_episode_id(episode_id)
    now = _now_iso()
    clean_url = (dc_post_url or "").strip()
    updated_item: PublishQueueItem | None = None
    new_items: list[PublishQueueItem] = []

    for item in items:
        if normalize_episode_id(item.episode_id) == target_key:
            updated_item = item.model_copy(
                update={
                    "status": "published",
                    "published_at": now,
                    "dc_post_url": clean_url or item.dc_post_url,
                }
            )
            new_items.append(updated_item)
        else:
            new_items.append(item)

    if updated_item is None:
        raise KeyError(f"Episode '{episode_id}' not found in publish queue ({target_q}).")

    save_publish_queue(new_items, target_q)
    return updated_item


def _is_headless_or_ci() -> bool:
    for var in ("CI", "GITHUB_ACTIONS", "SLOPTOON_HEADLESS", "PYTEST_CURRENT_TEST"):
        if os.environ.get(var, "").strip():
            return True
    return False


def _dispatch_windows_toast(toast_title: str, toast_body: str) -> bool:
    """Fire a non-blocking Windows toast notification via PowerShell WinRT API."""
    if sys.platform != "win32":
        return False

    ps_exe = shutil.which("powershell") or shutil.which("pwsh")
    if not ps_exe:
        return False

    safe_title = xml_escape(toast_title).replace("'", "''")
    safe_body = xml_escape(toast_body).replace("'", "''")
    ps_script = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, "
        "ContentType = WindowsRuntime] > $null; "
        "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, "
        "ContentType = WindowsRuntime] > $null; "
        "$xml = New-Object Windows.Data.Xml.Dom.XmlDocument; "
        f"$xml.LoadXml('<toast><visual><binding template=\"ToastText02\">"
        f"<text id=\"1\">{safe_title}</text>"
        f"<text id=\"2\">{safe_body}</text>"
        "</binding></visual></toast>'); "
        "$toast = [Windows.UI.Notifications.ToastNotification]::new($xml); "
        "$notifier = [Windows.UI.Notifications.ToastNotificationManager]::"
        "CreateToastNotifier('WowForeverSloptoon'); "
        "$notifier.Show($toast)"
    )

    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        subprocess.Popen(
            [ps_exe, "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", ps_script],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )
        return True
    except Exception:
        return False


def notify_new_episode_ready(
    episode_id: str,
    title: str,
    *,
    site_url: str = DEFAULT_ARCHIVE_BASE_URL,
    pack_dir: Path | None = None,
    use_toast: bool = True,
) -> bool:
    """Emit a non-blocking console + optional Windows toast notification for a ready episode.

    Never raises or blocks in headless/CI environments. Returns True if a Windows toast
    notification was dispatched, False when console-only fallback was used.
    """
    base = (site_url or DEFAULT_ARCHIVE_BASE_URL).strip().rstrip("/")
    ep_url = f"{base}/episodes/{episode_id}.html"

    console_lines = [
        f"[SLOPTOON READY] {episode_id}: {title}",
        f"  Archive URL : {ep_url}",
    ]
    if pack_dir is not None:
        console_lines.append(f"  Upload Pack : {pack_dir}")
    console_lines.append(
        "  Next Step   : python -m wow_sloptoon.cli publish-next --open-folder --open-browser --copy-body"
    )
    print("\n".join(console_lines))

    if not use_toast or _is_headless_or_ci() or sys.platform != "win32":
        return False

    toast_title = f"와우 포에버 슬롭툰 {episode_id.upper()} 업로드 준비 완료"
    toast_body = f"{title} | {ep_url}"
    return _dispatch_windows_toast(toast_title, toast_body)
