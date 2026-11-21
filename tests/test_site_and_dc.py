"""Tests for static web archive builder, seed assets, link integrity, and DC upload packager."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from PIL import Image

from wow_sloptoon.cast import CAST_BIBLE
from wow_sloptoon.config import load_settings
from wow_sloptoon.dc_packager import (
    DEFAULT_MAX_FILE_BYTES,
    build_dc_write_url,
    create_dc_upload_pack,
)
from wow_sloptoon.site_builder import (
    DC_GALLERY_WRITE_URL,
    build_static_site,
    generate_episode_thumbnail,
    load_episodes,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_HREF_SRC_RE = re.compile(r"""(?:href|src)=["']([^"']+)["']""")


def _assert_internal_links_resolve(html_path: Path) -> None:
    """Assert every local href/src attribute in an HTML file resolves to an existing file."""
    content = html_path.read_text(encoding="utf-8")
    matches = _HREF_SRC_RE.findall(content)
    assert matches, f"No href/src attributes found in {html_path}"

    for raw_ref in matches:
        ref = raw_ref.strip()
        if (
            not ref
            or ref.startswith("#")
            or ref.startswith("http://")
            or ref.startswith("https://")
            or ref.startswith("mailto:")
            or ref.startswith("data:")
        ):
            continue
        clean_path = urlsplit(ref).path
        if not clean_path:
            continue
        target = (html_path.parent / clean_path).resolve()
        assert target.exists(), f"Broken local reference '{raw_ref}' in {html_path} -> {target}"
        assert target.is_file(), f"Local reference is not a file: '{raw_ref}' -> {target}"
        assert target.stat().st_size > 0, f"Referenced file is empty: {target}"


def test_seed_episodes_json_valid_and_files_exist() -> None:
    settings = load_settings(PROJECT_ROOT)
    records = load_episodes(settings.episodes_json)
    assert len(records) >= 2

    by_id = {r.episode_id: r for r in records}
    assert "ep001" in by_id
    assert "ep002" in by_id

    ep1 = by_id["ep001"]
    assert ep1.source_post_no == "92059"
    assert ep1.cut_count == 5
    assert "흑마법사" in ep1.title

    ep2 = by_id["ep002"]
    assert ep2.source_post_no == "96849"
    assert ep2.cut_count == 6
    assert "기사님" in ep2.title

    for rec in (ep1, ep2):
        assert (PROJECT_ROOT / rec.full_image_rel).exists()
        assert (PROJECT_ROOT / rec.thumb_image_rel).exists()
        assert len(rec.page_images_rel) == 3
        for page_rel in rec.page_images_rel:
            assert (PROJECT_ROOT / page_rel).exists()


def test_build_static_site_end_to_end_and_link_integrity(tmp_path: Path) -> None:
    settings = load_settings(PROJECT_ROOT)
    out_site = tmp_path / "site"

    index_path = build_static_site(
        settings.episodes_json,
        out_site,
        settings.assets_dir,
        archive_base_url="https://example.github.io/wow-forever-sloptoon",
    )

    assert index_path == out_site / "index.html"
    required_files = [
        out_site / ".nojekyll",
        out_site / "index.html",
        out_site / "episode.html",
        out_site / "cast.html",
        out_site / "episodes" / "ep001.html",
        out_site / "episodes" / "ep002.html",
        out_site / "assets" / "style.css",
        out_site / "assets" / "app.js",
        out_site / "data" / "episodes.json",
        out_site / "assets" / "cast" / "cast_sheet_c_labeled.png",
        out_site / "assets" / "cast" / "cast_sheet_c.jpg",
    ]
    for path in required_files:
        assert path.exists(), f"Missing generated file: {path}"

    # Verify all HTML pages have zero broken local links/assets
    for page in (
        out_site / "index.html",
        out_site / "episode.html",
        out_site / "cast.html",
        out_site / "episodes" / "ep001.html",
        out_site / "episodes" / "ep002.html",
    ):
        _assert_internal_links_resolve(page)

    # Verify index.html content: header, search, cast filter, EP.1 & EP.2
    index_html = (out_site / "index.html").read_text(encoding="utf-8")
    assert "와우 포에버 슬롭툰" in index_html
    assert "디시 WOW 포에버 마이너 갤러리 개념글 상황극 봇" in index_html
    assert "흑마법사가 물을 어케 줌?" in index_html
    assert "방금 만난 기사님의 명언" in index_html
    assert 'id="searchInput"' in index_html
    assert 'id="castFilterBar"' in index_html

    # Verify episode.html content: reader + 1-click DC upload helper (no CAPTCHA bypass)
    ep_html = (out_site / "episode.html").read_text(encoding="utf-8")
    assert 'id="dcOneClickBtn"' in ep_html
    assert DC_GALLERY_WRITE_URL in ep_html
    assert "디시 포에버갤 업로드 도우미" in ep_html

    # Verify cast.html has all 9 Draft C members and valid cropped portraits
    cast_html = (out_site / "cast.html").read_text(encoding="utf-8")
    for member in CAST_BIBLE:
        assert member.name in cast_html
        assert member.role_tag in cast_html
        portrait_path = out_site / "assets" / "cast" / f"{member.id}.jpg"
        assert portrait_path.exists()
        with Image.open(portrait_path) as im:
            assert im.size == (360, 360)

    # Verify episode images in site/assets/episodes/ are valid non-empty images
    for ep_id in ("ep001", "ep002"):
        ep_dir = out_site / "assets" / "episodes" / ep_id
        for img_name in ("episode_full.jpg", "thumb.jpg", "page_1.png", "page_2.png", "page_3.png"):
            img_path = ep_dir / img_name
            assert img_path.exists(), f"Missing {img_path}"
            with Image.open(img_path) as im:
                assert im.width >= 400
                assert im.height >= 200


def test_auto_thumbnail_generation_and_dict_json_format(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    ep_dir = data_dir / "episodes" / "ep009"
    ep_dir.mkdir(parents=True)

    # Create a synthetic 900x1320 comic page with white background and middle artwork
    page_img = Image.new("RGB", (900, 1320), (255, 255, 255))
    for y in range(380, 760):
        for x in range(180, 720):
            page_img.putpixel((x, y), (120, 180, 240))
    page_path = ep_dir / "page_1.png"
    page_img.save(page_path)

    full_path = ep_dir / "episode_full.jpg"
    page_img.save(full_path, format="JPEG")

    # Save episodes.json using the alternative {"episodes": [...]} format, without thumb on disk
    episodes_json = data_dir / "episodes.json"
    episodes_json.write_text(
        json.dumps(
            {
                "episodes": [
                    {
                        "episode_id": "ep009",
                        "episode_number": 9,
                        "title": "자동 썸네일 테스트 에피소드",
                        "subtitle": "썸네일 미존재 시 자동 생성 확인",
                        "source_post_no": "99999",
                        "source_url": "https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=99999",
                        "created_at": "2026-11-21T15:00:00+09:00",
                        "cut_count": 4,
                        "cast_used": ["오크 전사", "트롤 주술사"],
                        "full_image_rel": "data/episodes/ep009/episode_full.jpg",
                        "thumb_image_rel": "data/episodes/ep009/thumb.jpg",
                        "page_images_rel": ["data/episodes/ep009/page_1.png"],
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    site_dir = tmp_path / "built_site"
    assets_dir = tmp_path / "empty_assets"
    assets_dir.mkdir()

    index_path = build_static_site(episodes_json, site_dir, assets_dir)
    assert index_path.exists()

    auto_thumb = site_dir / "assets" / "episodes" / "ep009" / "thumb.jpg"
    assert auto_thumb.exists()
    with Image.open(auto_thumb) as im:
        assert im.size == (800, 500)

    # Also verify direct generate_episode_thumbnail call
    extra_thumb = tmp_path / "direct_thumb.jpg"
    generate_episode_thumbnail(page_path, extra_thumb)
    assert extra_thumb.exists()
    with Image.open(extra_thumb) as im:
        assert im.size == (800, 500)


@pytest.mark.parametrize("episode_id,expected_post_no", [("ep001", "92059"), ("ep002", "96849")])
def test_dc_upload_pack_for_seed_episodes(
    tmp_path: Path, episode_id: str, expected_post_no: str
) -> None:
    settings = load_settings(PROJECT_ROOT)
    records = {r.episode_id: r for r in load_episodes(settings.episodes_json)}
    rec = records[episode_id]

    full_img = PROJECT_ROOT / rec.full_image_rel
    pack_dir = tmp_path / f"upload_pack_{episode_id}"
    pack = create_dc_upload_pack(
        rec,
        full_img,
        pack_dir,
        archive_base_url="https://example.github.io/wow-forever-sloptoon",
    )

    assert pack.pack_dir == pack_dir
    assert pack.write_url == build_dc_write_url("wowforever")
    assert pack.write_url == "https://gall.dcinside.com/mgallery/board/write/?id=wowforever"
    assert pack.title_text.startswith(f"[만화] 와우 포에버 슬롭툰 EP.{rec.episode_number}")
    assert expected_post_no in pack.body_text
    assert f"episode.html?id={episode_id}" in pack.body_text

    assert (pack_dir / "post_title.txt").read_text(encoding="utf-8") == pack.title_text
    assert (pack_dir / "post_body.txt").read_text(encoding="utf-8") == pack.body_text
    assert (pack_dir / "upload_guide.txt").exists()
    assert len(pack.image_paths) >= 1
    for img_path in pack.image_paths:
        assert img_path.exists()
        assert img_path.stat().st_size <= DEFAULT_MAX_FILE_BYTES
        with Image.open(img_path) as im:
            assert im.width > 0 and im.height > 0


def test_checked_in_site_workflow_and_readme_integrity() -> None:
    site_dir = PROJECT_ROOT / "site"
    for page in (
        site_dir / "index.html",
        site_dir / "episode.html",
        site_dir / "cast.html",
        site_dir / "episodes" / "ep001.html",
        site_dir / "episodes" / "ep002.html",
    ):
        assert page.exists(), f"Checked-in site page missing: {page}"
        _assert_internal_links_resolve(page)

    workflow_path = PROJECT_ROOT / ".github" / "workflows" / "auto-sloptoon.yml"
    assert workflow_path.exists()
    wf_text = workflow_path.read_text(encoding="utf-8")
    assert 'cron: "15 */6 * * *"' in wf_text
    assert "workflow_dispatch" in wf_text
    assert "GEMINI_API_KEY" in wf_text
    assert "sloptoon run-once" in wf_text
    assert "deploy-pages" in wf_text

    readme_path = PROJECT_ROOT / "README.md"
    assert readme_path.exists()
    readme_text = readme_path.read_text(encoding="utf-8")
    assert "GEMINI_API_KEY" in readme_text
    assert "sloptoon" in readme_text
    assert "GitHub Pages" in readme_text
    assert "Vercel" in readme_text
    assert "디시 포에버갤" in readme_text
