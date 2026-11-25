"""Tests for Route A static web archive builder, orphan cleanup, turnaround portraits,
40-episode scaling, link integrity, and docs/CI hygiene.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image

from wow_sloptoon.cast import CAST_BIBLE
from wow_sloptoon.config import DEFAULT_ARCHIVE_BASE_URL, load_settings
from wow_sloptoon.site_builder import (
    LEGAL_NOTICE,
    SITE_TAGLINE,
    build_static_site,
    generate_episode_thumbnail,
    load_episodes,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_HREF_SRC_RE = re.compile(r"""(?:href|src)=["']([^"']+)["']""")
_FORBIDDEN_DC_WRITE_URL = "gall.dcinside.com/mgallery/board/write"


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
    assert len(records) >= 20

    by_id = {r.episode_id: r for r in records}
    assert "ep001" in by_id
    assert "ep002" in by_id
    assert "ep020" in by_id

    ep1 = by_id["ep001"]
    assert ep1.source_post_no == "92059"
    assert 4 <= ep1.cut_count <= 7
    assert "흑마법사" in ep1.title

    ep2 = by_id["ep002"]
    assert ep2.source_post_no == "96849"
    assert 4 <= ep2.cut_count <= 7
    assert "기사님" in ep2.title

    for rec in records:
        assert 4 <= rec.cut_count <= 7, f"{rec.episode_id} expected 4..7 cuts, got {rec.cut_count}"
        assert (PROJECT_ROOT / rec.full_image_rel).exists(), f"Missing {rec.full_image_rel}"
        assert (PROJECT_ROOT / rec.thumb_image_rel).exists(), f"Missing {rec.thumb_image_rel}"
        assert 2 <= len(rec.page_images_rel) <= 4, f"{rec.episode_id} expected 2..4 pages, got {len(rec.page_images_rel)}"
        for page_rel in rec.page_images_rel:
            assert (PROJECT_ROOT / page_rel).exists(), f"Missing {page_rel}"


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


def test_build_static_site_end_to_end_route_a_copy_and_link_integrity(tmp_path: Path) -> None:
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
        out_site / "assets" / "cast" / "cast_sheet_c.jpg",
    ]
    for path in required_files:
        assert path.exists(), f"Missing generated file: {path}"
    assert not (out_site / "publish.html").exists(), "publish.html must not be exposed publicly"
    assert not (out_site / "assets" / "cast" / "cast_sheet_c_labeled.png").exists()

    all_html_pages = [
        out_site / "index.html",
        out_site / "episode.html",
        out_site / "cast.html",
        *(out_site / "episodes" / f"{rec.episode_id}.html" for rec in records),
    ]
    for page in all_html_pages:
        _assert_internal_links_resolve(page)

    for page in all_html_pages:
        text = page.read_text(encoding="utf-8")
        assert LEGAL_NOTICE in text, f"Legal notice missing in {page.name}"
        assert "publish.html" not in text, f"Admin publish link leaked in {page.name}"
        assert "업로드 큐 관리" not in text, f"Admin queue text leaked in {page.name}"
        assert "디시 포에버갤 업로드 도우미" not in text, f"Admin helper leaked in {page.name}"
        assert _FORBIDDEN_DC_WRITE_URL not in text, f"DC write URL leaked in {page.name}"
        assert "시안 C" not in text, f"Legacy V1 '시안 C' copy leaked in {page.name}"
        assert "미소녀" not in text, f"Legacy V1 '미소녀' copy leaked in {page.name}"
        assert "🎲 랜덤 화 보기" in text, f"Top-nav random button missing in {page.name}"

    index_html = (out_site / "index.html").read_text(encoding="utf-8")
    assert "와우 포에버 슬롭툰" in index_html
    assert SITE_TAGLINE in index_html
    assert "2~2.5등신" in index_html
    assert "흑마법사가 물을 어케 줌?" in index_html
    assert "기사님" in index_html
    assert 'id="searchInput"' in index_html
    assert 'id="castFilterBar"' in index_html
    assert 'class="slop-sponsor-slot" data-slot="home-feed-bottom" aria-label="스폰서 영역"></aside>' in index_html

    ep_html = (out_site / "episode.html").read_text(encoding="utf-8")
    assert 'id="dcOneClickBtn"' not in ep_html
    assert _FORBIDDEN_DC_WRITE_URL not in ep_html
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

    # Verify cast.html has all 9 Route A SD members, 360x360 portraits, turnarounds & 2 pets
    cast_html = (out_site / "cast.html").read_text(encoding="utf-8")
    for member in CAST_BIBLE:
        assert member.name in cast_html
        assert member.role_tag in cast_html
        portrait_path = out_site / "assets" / "cast" / f"{member.id}.jpg"
        assert portrait_path.exists()
        with Image.open(portrait_path) as im:
            assert im.size == (360, 360)
        turnaround_path = out_site / "assets" / "cast" / "turnarounds" / member.turnaround_filename
        assert turnaround_path.exists(), f"Missing synced turnaround sheet: {turnaround_path}"
        assert f"assets/cast/turnarounds/{member.turnaround_filename}" in cast_html
        if member.companion_turnaround_filename:
            comp_path = out_site / "assets" / "cast" / "turnarounds" / member.companion_turnaround_filename
            assert comp_path.exists(), f"Missing synced companion sheet: {comp_path}"
            assert f"assets/cast/turnarounds/{member.companion_turnaround_filename}" in cast_html
            assert member.companion_name in cast_html

    css_text = (out_site / "assets" / "style.css").read_text(encoding="utf-8")
    assert "--bg: #ffffff;" in css_text
    assert "--sky: #0ea5e9;" in css_text
    assert ".slop-sponsor-slot:empty" in css_text
    assert "display: none;" in css_text
    assert "overflow-x: clip;" in css_text
    assert "minmax(min(310px, 100%), 1fr)" in css_text
    assert "minmax(min(260px, 100%), 1fr)" in css_text
    assert ".episode-pager { grid-template-columns: minmax(0, 1fr); }" in css_text
    assert "overflow-wrap: anywhere;" in css_text
    assert re.search(r'href="assets/style\.css\?v=[0-9a-f]{8}"', index_html)
    assert re.search(r'src="assets/app\.js\?v=[0-9a-f]{8}"', index_html)
    assert re.search(r'href="\.\./assets/style\.css\?v=[0-9a-f]{8}"', ep1_html)

    for generated in out_site.rglob("*"):
        if generated.is_file() and generated.suffix.lower() in {".html", ".css", ".js", ".xml", ".txt", ".json"}:
            body = generated.read_text(encoding="utf-8")
            assert "인벤" not in body, f"Forbidden Inven reference in {generated}"
            assert "inven" not in body.lower(), f"Forbidden inven reference in {generated}"

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


def test_build_static_site_cleans_orphan_pages_and_stale_files(tmp_path: Path) -> None:
    settings = load_settings(PROJECT_ROOT)
    out_site = tmp_path / "clean_site"

    # Pre-seed stale/orphan artifacts from retired V4 & DC workflows
    orphan_page = out_site / "assets" / "episodes" / "ep001" / "page_5.png"
    orphan_page.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (64, 64), (255, 255, 255)).save(orphan_page)

    stale_ep_dir = out_site / "assets" / "episodes" / "ep999"
    stale_ep_dir.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (64, 64), (255, 255, 255)).save(stale_ep_dir / "page_1.png")

    stale_ep_html = out_site / "episodes" / "ep999.html"
    stale_ep_html.parent.mkdir(parents=True, exist_ok=True)
    stale_ep_html.write_text("<html>stale</html>", encoding="utf-8")

    stale_publish = out_site / "publish.html"
    stale_publish.write_text("<html>forbidden</html>", encoding="utf-8")

    stale_labeled = out_site / "assets" / "cast" / "cast_sheet_c_labeled.png"
    stale_labeled.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (64, 64), (255, 255, 255)).save(stale_labeled)

    build_static_site(settings.episodes_json, out_site, settings.assets_dir)

    assert not orphan_page.exists()
    assert not stale_ep_dir.exists()
    assert not stale_ep_html.exists()
    assert not stale_publish.exists()
    assert not stale_labeled.exists()


def test_seo_og_twitter_sitemap_robots_and_relative_fallback(tmp_path: Path) -> None:
    settings = load_settings(PROJECT_ROOT)
    records = load_episodes(settings.episodes_json)
    assert len(records) >= 2
    latest_ep = records[-1]

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

    ep1_default = (default_site / "episodes" / "ep001.html").read_text(encoding="utf-8")
    assert f'data-share-url="{DEFAULT_ARCHIVE_BASE_URL}/episodes/ep001.html"' in ep1_default
    assert _FORBIDDEN_DC_WRITE_URL not in ep1_default

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
    assert '<link rel="canonical"' not in (rel_site / "index.html").read_text(encoding="utf-8")


def test_five_episode_recommendations_and_clean_app_js(tmp_path: Path) -> None:
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
    assert _FORBIDDEN_DC_WRITE_URL not in app_js
    assert "initPublishPage" not in app_js

    ep3_html = (out_site / "episodes" / "ep003.html").read_text(encoding="utf-8")
    rec_match = re.search(
        r'<div class="recommend-grid" id="epRecommendGrid">(.*?)</div>\s*</section>',
        ep3_html,
        re.DOTALL,
    )
    assert rec_match is not None
    rec_hrefs = re.findall(r'href="\.\./episodes/(ep\d{3})\.html"', rec_match.group(1))
    assert len(rec_hrefs) == 3
    assert "ep003" not in rec_hrefs
    assert len(set(rec_hrefs)) == 3


def test_site_builder_scales_cleanly_to_40_episodes(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    episodes_payload = []
    for n in range(1, 41):
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
                "title": f"포에버갤 레전드 인던 사건 {n}화",
                "subtitle": f"{n}화 상황극 한줄 요약",
                "source_post_no": str(100000 + n),
                "source_url": f"https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no={100000 + n}",
                "created_at": f"2026-11-{(n % 28) + 1:02d}T12:00:00+09:00",
                "cut_count": 5,
                "cast_used": ["오크 전사", "스카이본 마법사"],
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
    assert not (out_site / "publish.html").exists()

    index_html = (out_site / "index.html").read_text(encoding="utf-8")
    assert 'id="loadMoreWrap"' in index_html
    assert 'id="loadMoreBtn"' in index_html
    assert 'id="showAllBtn"' in index_html
    assert 'id="backToTopBtn"' in index_html
    assert 'width="800" height="500" loading="lazy" decoding="async"' in index_html
    assert "총 <strong>40</strong>화 아카이브" in index_html

    cast_html = (out_site / "cast.html").read_text(encoding="utf-8")
    assert "+ 외 35화 더 있음" in cast_html
    assert "오크 · 전사 · 호드" in cast_html
    assert "스카이본 · 마법사 · 스카이본" in cast_html
    assert "출연 에피소드 (40화)" in cast_html

    ep40_html = (out_site / "episodes" / "ep040.html").read_text(encoding="utf-8")
    assert 'id="epJumpSelect"' in ep40_html
    assert len(re.findall(r'<option value="ep\d{3}"', ep40_html)) == 40
    m_data = re.search(r"window\.__SLOPTOON_DATA__\s*=\s*(\{.*?\});</script>", ep40_html)
    assert m_data is not None
    embedded = json.loads(m_data.group(1))
    by_id = {e["episode_id"]: e for e in embedded["episodes"]}
    assert "page_images" in by_id["ep040"]
    assert "page_images" not in by_id["ep001"]

    for generated in out_site.rglob("*"):
        if generated.is_file() and generated.suffix.lower() in {".html", ".css", ".js", ".xml", ".txt", ".json"}:
            body = generated.read_text(encoding="utf-8")
            assert _FORBIDDEN_DC_WRITE_URL not in body
            assert "publish.html" not in body
            assert "인벤" not in body
            assert "inven" not in body.lower()


def test_auto_thumbnail_generation_and_dict_json_format(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    ep_dir = data_dir / "episodes" / "ep999"
    ep_dir.mkdir(parents=True)

    page_img = Image.new("RGB", (900, 1320), (255, 255, 255))
    for y in range(380, 760):
        for x in range(180, 720):
            page_img.putpixel((x, y), (120, 180, 240))
    page_path = ep_dir / "page_1.png"
    page_img.save(page_path)
    page_img.save(ep_dir / "episode_full.jpg", format="JPEG")

    episodes_json = data_dir / "episodes.json"
    episodes_json.write_text(
        json.dumps(
            {
                "episodes": [
                    {
                        "episode_id": "ep999",
                        "episode_number": 999,
                        "title": "자동 썸네일 테스트 에피소드",
                        "subtitle": "썸네일 미존재 시 자동 생성 확인",
                        "source_post_no": "99999",
                        "source_url": "https://gall.dcinside.com/mgallery/board/view/?id=wowforever&no=99999",
                        "created_at": "2026-11-21T15:00:00+09:00",
                        "cut_count": 4,
                        "cast_used": ["오크 전사", "트롤 주술사"],
                        "full_image_rel": "data/episodes/ep999/episode_full.jpg",
                        "thumb_image_rel": "data/episodes/ep999/thumb.jpg",
                        "page_images_rel": ["data/episodes/ep999/page_1.png"],
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

    auto_thumb = site_dir / "assets" / "episodes" / "ep999" / "thumb.jpg"
    assert auto_thumb.exists()
    with Image.open(auto_thumb) as im:
        assert im.size == (800, 500)

    extra_thumb = tmp_path / "direct_thumb.jpg"
    generate_episode_thumbnail(page_path, extra_thumb)
    assert extra_thumb.exists()
    with Image.open(extra_thumb) as im:
        assert im.size == (800, 500)


def test_checked_in_site_workflow_and_docs_route_a_hygiene() -> None:
    settings = load_settings(PROJECT_ROOT)
    records = load_episodes(settings.episodes_json)
    site_dir = PROJECT_ROOT / "site"
    assert not (site_dir / "publish.html").exists(), "publish.html must not exist in public site/"
    for page in (
        site_dir / "index.html",
        site_dir / "episode.html",
        site_dir / "cast.html",
        *(site_dir / "episodes" / f"{rec.episode_id}.html" for rec in records),
    ):
        assert page.exists(), f"Checked-in site page missing: {page}"
        _assert_internal_links_resolve(page)
        assert _FORBIDDEN_DC_WRITE_URL not in page.read_text(encoding="utf-8")
    assert (site_dir / "sitemap.xml").exists()
    assert (site_dir / "robots.txt").exists()

    workflow_path = PROJECT_ROOT / ".github" / "workflows" / "auto-sloptoon.yml"
    assert workflow_path.exists()
    wf_text = workflow_path.read_text(encoding="utf-8")
    assert "cron:" not in wf_text, "Paid API auto-schedule cron must stay disabled"
    assert "SLOPTOON_ALLOW_PAID_API" in wf_text
    assert "workflow_dispatch" in wf_text
    assert "GEMINI_API_KEY" in wf_text
    assert "SLOPTOON_IMAGE_MODEL" in wf_text
    assert "python -m wow_sloptoon.cli autopilot" in wf_text
    assert "python -m wow_sloptoon.cli build-site" in wf_text
    assert "HYGIENE OK" in wf_text
    assert "deploy-pages" in wf_text
    for retired in ("run-once", "pack-dc", "--layout v4", "sloptoon queue"):
        assert retired not in wf_text

    # Public docs & PowerShell helpers must stay Route A clean with 0 retired DC/V4 guides and 0 local paths
    for doc_name in ("README.md", "AUTOMATION.md", "run-factory.ps1"):
        txt = (PROJECT_ROOT / doc_name).read_text(encoding="utf-8")
        for forbidden in ("publish.html", "pack-dc", "upload_pack", "--layout v4", "run-once", "publish_queue"):
            assert forbidden not in txt, f"Retired reference '{forbidden}' leaked into {doc_name}"

    readme_text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "GEMINI_API_KEY" in readme_text
    assert "diorama_style_ref.jpg" in readme_text
    assert "2~2.5등신" in readme_text
    assert "slopwow.github.io" in readme_text

    # Zero local user absolute paths or Google API keys across all SSOT/docs/scripts
    path_secret_pats = (
        re.compile(r"[A-Za-z]:[\\/]Users[\\/]"),
        re.compile(r"/Users/[A-Za-z0-9._-]+/"),
        re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    )
    for rel in (
        "AGENTS.md",
        "CLAUDE.md",
        "GEMINI.md",
        "README.md",
        "AUTOMATION.md",
        "run-factory.ps1",
        "setup-automation.ps1",
        "deploy-pages.ps1",
        ".github/workflows/auto-sloptoon.yml",
    ):
        txt = (PROJECT_ROOT / rel).read_text(encoding="utf-8")
        for pat in path_secret_pats:
            assert not pat.search(txt), f"Absolute path/secret leaked in {rel}"
