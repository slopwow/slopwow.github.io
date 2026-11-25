"""Archive-wide real-data integrity tests for WOW Forever Sloptoon (Route A).

Verifies every published episode in `data/episodes.json`:
1. `data/episodes/<id>/record.json` matches `data/episodes.json` 100% field-for-field.
2. `data/episodes/<id>/script.json` matches `record.cut_count` & `record.title`, passes
   `audit_script_quality` with 0 errors (zero Imp+Voidwalker conflict, zero 3-line brick
   walls, zero modern slang, zero dual-speaker hacks), and contains zero harsh profanity
   or copy-paste aegyo clichés in dialogue.
3. `data/episodes/<id>/audit.json` passed with `total_overlap_px == 0` and
   `total_tooltip_overlap_px == 0` across all cuts.
4. `site/assets/episodes/<id>/` contains zero orphan `page_*.png`/`.jpg` files, and
   `site/` contains zero orphan episode folders/HTML or `publish.html`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from wow_sloptoon.config import load_settings
from wow_sloptoon.models import EpisodeScript
from wow_sloptoon.site_builder import load_episodes
from wow_sloptoon.writer import audit_script_quality

PROJECT_ROOT = Path(__file__).resolve().parents[1]

_DIALOGUE_PROFANITY_RE = re.compile(
    r"(?:씨발|시발|ㅅㅂ|병신|ㅂㅅ|개새끼|새끼야|좆같|존나|ㅈㄴ|미친년|지랄)",
    re.IGNORECASE,
)
_COPYPASTE_AEGYO_TOKENS: tuple[str, ...] = (
    "옴뇸뇸~",
    "으, 으엣?!",
    "후훗…",
    "~해야징~♪",
    "~♡",
)


def test_all_episodes_record_json_matches_episodes_json_100_percent() -> None:
    settings = load_settings(PROJECT_ROOT)
    records = load_episodes(settings.episodes_json)
    assert len(records) >= 20, f"Expected >= 20 episodes in data/episodes.json, got {len(records)}"

    mismatches: list[str] = []
    for rec in records:
        ep_dir = settings.episodes_dir / rec.episode_id
        record_path = ep_dir / "record.json"
        if not record_path.exists():
            mismatches.append(f"{rec.episode_id}: missing {record_path.relative_to(PROJECT_ROOT)}")
            continue

        disk_record = json.loads(record_path.read_text(encoding="utf-8"))
        index_record = rec.model_dump(mode="json")
        if disk_record != index_record:
            diff_keys = sorted(
                k for k in set(disk_record) | set(index_record) if disk_record.get(k) != index_record.get(k)
            )
            mismatches.append(f"{rec.episode_id}: record.json != episodes.json keys={diff_keys}")

        for rel in [rec.full_image_rel, rec.thumb_image_rel, *rec.page_images_rel]:
            if not (PROJECT_ROOT / rel).exists():
                mismatches.append(f"{rec.episode_id}: missing referenced asset '{rel}'")

    assert not mismatches, "Metadata sync failures:\n" + "\n".join(mismatches)


def test_all_episodes_scripts_pass_route_a_quality_audit_and_zero_profanity() -> None:
    settings = load_settings(PROJECT_ROOT)
    records = load_episodes(settings.episodes_json)
    assert len(records) >= 20

    failures: list[str] = []
    for rec in records:
        script_path = settings.episodes_dir / rec.episode_id / "script.json"
        if not script_path.exists():
            failures.append(f"{rec.episode_id}: missing script.json")
            continue

        script = EpisodeScript.model_validate_json(script_path.read_text(encoding="utf-8"))
        if len(script.cuts) != rec.cut_count:
            failures.append(
                f"{rec.episode_id}: script cuts ({len(script.cuts)}) != record.cut_count ({rec.cut_count})"
            )
        if script.source_title != rec.title:
            failures.append(
                f"{rec.episode_id}: script.source_title ({script.source_title!r}) != record.title ({rec.title!r})"
            )

        audit = audit_script_quality(script)
        if not audit["passed"] or audit["errors"]:
            failures.append(f"{rec.episode_id}: audit_script_quality errors={audit['errors']}")

        for cut in script.cuts:
            dlg = (cut.dialogue or "").strip()
            if not dlg:
                continue
            m_prof = _DIALOGUE_PROFANITY_RE.search(dlg)
            if m_prof:
                failures.append(
                    f"{rec.episode_id} cut #{cut.cut_index}: harsh profanity '{m_prof.group(0)}' in dialogue"
                )
            for cliche in _COPYPASTE_AEGYO_TOKENS:
                if cliche in dlg:
                    failures.append(
                        f"{rec.episode_id} cut #{cut.cut_index}: copy-paste aegyo '{cliche}' in dialogue"
                    )

    assert not failures, "Script quality failures:\n" + "\n".join(failures)


def test_all_episodes_compose_audit_passed_and_zero_overlap() -> None:
    settings = load_settings(PROJECT_ROOT)
    records = load_episodes(settings.episodes_json)
    assert len(records) >= 20

    failures: list[str] = []
    for rec in records:
        audit_path = settings.episodes_dir / rec.episode_id / "audit.json"
        if not audit_path.exists():
            failures.append(f"{rec.episode_id}: missing audit.json")
            continue

        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        if audit.get("passed") is not True:
            failures.append(f"{rec.episode_id}: audit.json passed={audit.get('passed')}")
        if audit.get("total_overlap_px") != 0:
            failures.append(f"{rec.episode_id}: total_overlap_px={audit.get('total_overlap_px')}")
        if audit.get("total_tooltip_overlap_px", 0) != 0:
            failures.append(
                f"{rec.episode_id}: total_tooltip_overlap_px={audit.get('total_tooltip_overlap_px')}"
            )
        if audit.get("cut_count") != rec.cut_count:
            failures.append(
                f"{rec.episode_id}: audit.json cut_count ({audit.get('cut_count')}) != record ({rec.cut_count})"
            )

        for cut_audit in audit.get("cuts", []):
            c_idx = cut_audit.get("cut_index")
            if cut_audit.get("overlap_px", 0) != 0:
                failures.append(f"{rec.episode_id} cut #{c_idx}: overlap_px={cut_audit.get('overlap_px')}")
            if cut_audit.get("tooltip_overlap_px", 0) != 0:
                failures.append(
                    f"{rec.episode_id} cut #{c_idx}: tooltip_overlap_px={cut_audit.get('tooltip_overlap_px')}"
                )

    assert not failures, "Compose audit failures:\n" + "\n".join(failures)


def test_site_assets_zero_orphan_pages_and_episodes() -> None:
    settings = load_settings(PROJECT_ROOT)
    records = load_episodes(settings.episodes_json)
    site_dir = settings.site_dir
    assert site_dir.exists(), "site/ directory missing"
    assert not (site_dir / "publish.html").exists(), "site/publish.html must not exist"

    expected_ids = {rec.episode_id for rec in records}
    failures: list[str] = []

    site_ep_assets_root = site_dir / "assets" / "episodes"
    if site_ep_assets_root.exists():
        actual_dirs = {p.name for p in site_ep_assets_root.iterdir() if p.is_dir()}
        orphan_dirs = sorted(actual_dirs - expected_ids)
        if orphan_dirs:
            failures.append(f"Orphan episode asset folders in site/assets/episodes/: {orphan_dirs}")

    site_ep_html_root = site_dir / "episodes"
    if site_ep_html_root.exists():
        actual_htmls = {p.stem for p in site_ep_html_root.glob("*.html")}
        orphan_htmls = sorted(actual_htmls - expected_ids)
        if orphan_htmls:
            failures.append(f"Orphan episode HTML pages in site/episodes/: {orphan_htmls}")

    for rec in records:
        ep_site_dir = site_ep_assets_root / rec.episode_id
        if not ep_site_dir.exists():
            failures.append(f"{rec.episode_id}: missing {ep_site_dir.relative_to(PROJECT_ROOT)}")
            continue

        expected_pages = {
            f"page_{idx}{Path(p).suffix.lower() or '.png'}"
            for idx, p in enumerate(rec.page_images_rel, start=1)
        }
        actual_pages = {
            p.name
            for p in ep_site_dir.iterdir()
            if p.is_file() and re.match(r"^page_\d+\.(?:png|jpe?g|webp)$", p.name, re.IGNORECASE)
        }
        orphan_pages = sorted(actual_pages - expected_pages)
        missing_pages = sorted(expected_pages - actual_pages)
        if orphan_pages:
            failures.append(f"{rec.episode_id}: orphan page file(s) in site/: {orphan_pages}")
        if missing_pages:
            failures.append(f"{rec.episode_id}: missing page file(s) in site/: {missing_pages}")

    assert not failures, "Site orphan/sync failures:\n" + "\n".join(failures)
