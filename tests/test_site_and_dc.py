"""Tests for static web archive builder, seed assets, link integrity, and DC upload packager."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from PIL import Image

from wow_sloptoon.cast import CAST_BIBLE
from wow_sloptoon.config import DEFAULT_ARCHIVE_BASE_URL, load_settings
from wow_sloptoon.dc_packager import (
    DEFAULT_MAX_FILE_BYTES,
    build_dc_write_url,
    create_dc_upload_pack,
)
from wow_sloptoon.site_builder import (
    DC_GALLERY_WRITE_URL,
    LEGAL_NOTICE,
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


def _extract_meta_map(html_text: str) -> dict[str, str]:
    """Extract `<meta property|name="..." content="...">` values into a dictionary."""
    result: dict[str, str] = {}
    pattern = re.compile(
        r"""<meta\s+(?:property|name)=["']([^"']+)["']\s+content=["']([^"']*)["']""",
        re.IGNORECASE,
    )
    for key, val in pattern.findall(html_text):
        result[key.lower()] = val
    return result


def test_build_static_site_end_to_end_and_link_integrity(tmp_path: Path) -> None:
    settings = load_settings(PROJECT_ROOT)
    records = load_episodes(settings.episodes_json)
    assert len(records) >= 2
    out_site = tmp_path / "site"
    base_url = "https://example.github.io/wow-forever-sloptoon"

    index_path = build_static_site(
        settings.episodes_json,
        out_site,
        settings.assets_dir,
        archive_base_url=base_url,
    )

    assert index_path == out_site / "index.html"
    required_files = [
        out_site / ".nojekyll",
        out_site / "index.html",
        out_site / "episode.html",
        out_site / "cast.html",
        out_site / "sitemap.xml",
        out_site / "robots.txt",
        *(out_site / "episodes" / f"{rec.episode_id}.html" for rec in records),
        out_site / "assets" / "style.css",
        out_site / "assets" / "app.js",
        out_site / "data" / "episodes.json",
        out_site / "assets" / "cast" / "cast_sheet_c_labeled.png",
        out_site / "assets" / "cast" / "cast_sheet_c.jpg",
    ]
    for path in required_files:
        assert path.exists(), f"Missing generated file: {path}"
    assert not (out_site / "publish.html").exists(), "Creator publish.html must not be exposed publicly"

    # Verify ALL HTML pages have zero broken local links/assets and ZERO creator upload links
    all_html_pages = [
        out_site / "index.html",
        out_site / "episode.html",
        out_site / "cast.html",
        *(out_site / "episodes" / f"{rec.episode_id}.html" for rec in records),
    ]
    for page in all_html_pages:
        _assert_internal_links_resolve(page)

    # Verify shared footer legal notice, top-nav random button, and ZERO admin/write links on every HTML page
    for page in all_html_pages:
        text = page.read_text(encoding="utf-8")
        assert LEGAL_NOTICE in text, f"Legal notice missing in {page.name}"
        assert "publish.html" not in text, f"Admin publish link leaked in {page.name}"
        assert "업로드 큐 관리" not in text, f"Admin queue text leaked in {page.name}"
        assert "디시 포에버갤 업로드 도우미" not in text, f"Admin helper leaked in {page.name}"
        assert DC_GALLERY_WRITE_URL not in text, f"DC write URL leaked in {page.name}"
        assert "🎲 랜덤 화 보기" in text, f"Top-nav random button missing in {page.name}"

    # Verify index.html content: header, search, cast filter, all episodes, empty sponsor slot
    index_html = (out_site / "index.html").read_text(encoding="utf-8")
    assert "와우 포에버 슬롭툰" in index_html
    assert "디시 WOW 포에버 마이너 갤러리 개념글 상황극 봇" in index_html
    assert "흑마법사가 물을 어케 줌?" in index_html
    assert "방금 만난 기사님의 명언" in index_html
    assert 'id="searchInput"' in index_html
    assert 'id="castFilterBar"' in index_html
    assert 'class="slop-sponsor-slot" data-slot="home-feed-bottom" aria-label="스폰서 영역"></aside>' in index_html

    # Verify episode.html & episodes/ep001.html: reader, share button, random button, binge cards, recommended grid (no admin helper)
    ep_html = (out_site / "episode.html").read_text(encoding="utf-8")
    assert 'id="dcOneClickBtn"' not in ep_html
    assert DC_GALLERY_WRITE_URL not in ep_html
    assert "디시 포에버갤 업로드 도우미" not in ep_html
    assert 'id="shareCopyBtn"' in ep_html
    assert "링크 복사" in ep_html
    assert 'id="bottomRandomBtn"' in ep_html
    assert "다른 레전드 념글 만화" in ep_html
    assert 'class="slop-sponsor-slot" data-slot="episode-strip-bottom" aria-label="스폰서 영역"></aside>' in ep_html

    ep1_html = (out_site / "episodes" / "ep001.html").read_text(encoding="utf-8")
    assert f'data-share-url="{base_url}/episodes/ep001.html"' in ep1_html
    assert "다른 레전드 념글 만화" in ep1_html
    assert "nav-ep-thumb" in ep1_html

    # Verify cast.html has all 9 Draft C members and valid cropped portraits
    cast_html = (out_site / "cast.html").read_text(encoding="utf-8")
    for member in CAST_BIBLE:
        assert member.name in cast_html
        assert member.role_tag in cast_html
        portrait_path = out_site / "assets" / "cast" / f"{member.id}.jpg"
        assert portrait_path.exists()
        with Image.open(portrait_path) as im:
            assert im.size == (360, 360)

    # Verify CSS pure-white aesthetic, #0ea5e9 accent, and collapsible :empty sponsor slot rule
    css_text = (out_site / "assets" / "style.css").read_text(encoding="utf-8")
    assert "--bg: #ffffff;" in css_text
    assert "--sky: #0ea5e9;" in css_text
    assert ".slop-sponsor-slot:empty" in css_text
    assert "display: none;" in css_text

    # Verify zero WoW Inven mentions across ALL generated text files
    for generated in out_site.rglob("*"):
        if generated.is_file() and generated.suffix.lower() in {".html", ".css", ".js", ".xml", ".txt", ".json"}:
            body = generated.read_text(encoding="utf-8")
            assert "인벤" not in body, f"Forbidden Inven reference in {generated}"
            assert "inven" not in body.lower(), f"Forbidden inven reference in {generated}"

    # Verify episode images in site/assets/episodes/ are valid non-empty images for all episodes
    for rec in records:
        ep_dir = out_site / "assets" / "episodes" / rec.episode_id
        expected_imgs = ["episode_full.jpg", "thumb.jpg"] + [
            f"page_{idx}{Path(p).suffix.lower() or '.png'}"
            for idx, p in enumerate(rec.page_images_rel, start=1)
        ]
        for img_name in expected_imgs:
            img_path = ep_dir / img_name
            assert img_path.exists(), f"Missing {img_path}"
            with Image.open(img_path) as im:
                assert im.width >= 400
                assert im.height >= 200


def test_seo_og_twitter_sitemap_robots_and_relative_fallback(tmp_path: Path) -> None:
    settings = load_settings(PROJECT_ROOT)
    records = load_episodes(settings.episodes_json)
    assert len(records) >= 2
    latest_ep = records[-1]

    # 1. Default build (uses DEFAULT_ARCHIVE_BASE_URL = https://slopwow.github.io)
    default_site = tmp_path / "default_site"
    build_static_site(settings.episodes_json, default_site, settings.assets_dir)

    robots = (default_site / "robots.txt").read_text(encoding="utf-8")
    assert "User-agent: *" in robots
    assert "Allow: /" in robots
    assert f"Sitemap: {DEFAULT_ARCHIVE_BASE_URL}/sitemap.xml" in robots

    sitemap_text = (default_site / "sitemap.xml").read_text(encoding="utf-8")
    root = ET.fromstring(sitemap_text)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [el.text for el in root.findall("sm:url/sm:loc", ns)]
    assert f"{DEFAULT_ARCHIVE_BASE_URL}/" in locs
    assert f"{DEFAULT_ARCHIVE_BASE_URL}/cast.html" in locs
    for rec in records:
        assert f"{DEFAULT_ARCHIVE_BASE_URL}/episodes/{rec.episode_id}.html" in locs
    assert all("publish.html" not in (loc or "") for loc in locs)

    # Check complete Open Graph & Twitter Card tags on all public pages (dynamically matching latest episode)
    public_pages = [
        (default_site / "index.html", "website", f"{DEFAULT_ARCHIVE_BASE_URL}/"),
        (default_site / "cast.html", "website", f"{DEFAULT_ARCHIVE_BASE_URL}/cast.html"),
        (
            default_site / "episode.html",
            "article",
            f"{DEFAULT_ARCHIVE_BASE_URL}/episodes/{latest_ep.episode_id}.html",
        ),
        *(
            (
                default_site / "episodes" / f"{rec.episode_id}.html",
                "article",
                f"{DEFAULT_ARCHIVE_BASE_URL}/episodes/{rec.episode_id}.html",
            )
            for rec in records
        ),
    ]
    for page_path, expected_type, expected_url in public_pages:
        meta = _extract_meta_map(page_path.read_text(encoding="utf-8"))
        for req_key in (
            "og:title",
            "og:description",
            "og:image",
            "og:url",
            "og:type",
            "og:site_name",
            "twitter:card",
        ):
            assert meta.get(req_key), f"Missing {req_key} in {page_path.name}"
        assert meta["og:type"] == expected_type
        assert meta["og:url"] == expected_url
        assert meta["og:site_name"] == "와우 포에버 슬롭툰"
        assert meta["og:image"].startswith(f"{DEFAULT_ARCHIVE_BASE_URL}/assets/")
        assert meta["twitter:card"] == "summary_large_image"

    # Verify canonical public URLs appear without exposing creator upload helpers
    ep1_default = (default_site / "episodes" / "ep001.html").read_text(encoding="utf-8")
    assert f'data-share-url="{DEFAULT_ARCHIVE_BASE_URL}/episodes/ep001.html"' in ep1_default
    assert DC_GALLERY_WRITE_URL not in ep1_default

    # 2. Explicit empty archive_base_url="" -> clean relative fallback for OG tags
    rel_site = tmp_path / "rel_site"
    build_static_site(settings.episodes_json, rel_site, settings.assets_dir, archive_base_url="")
    idx_meta = _extract_meta_map((rel_site / "index.html").read_text(encoding="utf-8"))
    ep1_meta = _extract_meta_map((rel_site / "episodes" / "ep001.html").read_text(encoding="utf-8"))
    cast_meta = _extract_meta_map((rel_site / "cast.html").read_text(encoding="utf-8"))

    assert idx_meta["og:url"] == "index.html"
    assert idx_meta["og:image"].startswith("assets/")
    assert ep1_meta["og:url"] == "ep001.html"
    assert ep1_meta["og:image"] == "../assets/episodes/ep001/thumb.jpg"
    assert cast_meta["og:url"] == "cast.html"
    assert cast_meta["og:image"].startswith("assets/cast/")
    assert "<link rel=\"canonical\"" not in (rel_site / "index.html").read_text(encoding="utf-8")


def test_publish_queue_page_and_five_episode_recommendations(tmp_path: Path) -> None:
    # Build a synthetic 5-episode archive to verify newest-first publish queue AND
    # up-to-3 recommended episodes cap + non-self exclusion.
    data_dir = tmp_path / "data"
    episodes_payload = []
    for n in range(1, 6):
        ep_id = f"ep{n:03d}"
        ep_dir = data_dir / "episodes" / ep_id
        ep_dir.mkdir(parents=True)
        img = Image.new("RGB", (800, 500), (255, 255, 255))
        img.save(ep_dir / "episode_full.jpg", format="JPEG")
        img.save(ep_dir / "thumb.jpg", format="JPEG")
        img.save(ep_dir / "page_1.png", format="PNG")
        episodes_payload.append(
            {
                "episode_id": ep_id,
                "episode_number": n,
                "title": f"포에버갤 레전드 에피소드 {n}화",
                "subtitle": f"{n}화 상황극 한줄 요약",
                "source_post_no": str(90000 + n),
                "source_url": f"https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no={90000 + n}",
                "created_at": f"2026-11-2{n}T12:00:00+09:00",
                "cut_count": 5,
                "cast_used": ["오크 전사", "인간 흑마법사"],
                "full_image_rel": f"data/episodes/{ep_id}/episode_full.jpg",
                "thumb_image_rel": f"data/episodes/{ep_id}/thumb.jpg",
                "page_images_rel": [f"data/episodes/{ep_id}/page_1.png"],
            }
        )

    episodes_json = data_dir / "episodes.json"
    episodes_json.write_text(json.dumps(episodes_payload, ensure_ascii=False), encoding="utf-8")
    empty_assets = tmp_path / "assets"
    empty_assets.mkdir()
    out_site = tmp_path / "site"

    build_static_site(episodes_json, out_site, empty_assets)

    # Verify all generated HTML files pass link integrity and exclude publish.html
    assert not (out_site / "publish.html").exists()
    for html_file in [
        out_site / "index.html",
        out_site / "episode.html",
        out_site / "cast.html",
        *(out_site / "episodes" / f"ep{n:03d}.html" for n in range(1, 6)),
    ]:
        _assert_internal_links_resolve(html_file)

    app_js = (out_site / "assets" / "app.js").read_text(encoding="utf-8")
    assert "initRandomButtons" in app_js
    assert DC_GALLERY_WRITE_URL not in app_js
    assert "initPublishPage" not in app_js

    # Verify recommended episode grid on ep003 shows exactly 3 other episodes (excluding ep003)
    ep3_html = (out_site / "episodes" / "ep003.html").read_text(encoding="utf-8")
    rec_match = re.search(
        r'<div class="recommend-grid" id="epRecommendGrid">(.*?)</div>\s*</section>',
        ep3_html,
        re.DOTALL,
    )
    assert rec_match is not None
    rec_block = rec_match.group(1)
    rec_hrefs = re.findall(r'href="\.\./episodes/(ep\d{3})\.html"', rec_block)
    assert len(rec_hrefs) == 3
    assert "ep003" not in rec_hrefs
    assert len(set(rec_hrefs)) == 3


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
    assert pack.title_text == f"[와포슬롭툰]{rec.title.strip()}"
    assert "EP." not in pack.title_text
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
    settings = load_settings(PROJECT_ROOT)
    records = load_episodes(settings.episodes_json)
    site_dir = PROJECT_ROOT / "site"
    for page in (
        site_dir / "index.html",
        site_dir / "episode.html",
        site_dir / "cast.html",
        site_dir / "publish.html",
        *(site_dir / "episodes" / f"{rec.episode_id}.html" for rec in records),
    ):
        assert page.exists(), f"Checked-in site page missing: {page}"
        _assert_internal_links_resolve(page)
    assert (site_dir / "sitemap.xml").exists()
    assert (site_dir / "robots.txt").exists()

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
