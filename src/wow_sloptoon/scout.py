"""Public DCInside WOW Forever minor gallery scout, parser, deduplicator, and ranker.

Policy note:
- Reads only publicly accessible gallery pages via standard HTTP GET requests.
- Never attempts to solve, bypass, or evade CAPTCHAs or anti-bot gates. If access is
  blocked, raises `GalleryAccessBlockedError` immediately.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Iterable, Sequence
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag

from wow_sloptoon.config import DEFAULT_GALLERY_ID
from wow_sloptoon.models import GalleryPost

DC_BASE_URL = "https://gall.dcinside.com"

DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

EXCLUDED_SUBJECT_TOKENS: tuple[str, ...] = (
    "공지",
    "설문",
    "운영",
    "광고",
    "이슈",
    "뉴스",
    "홍보",
    "AD",
)

EXCLUDED_ROW_TYPES: set[str] = {
    "icon_notice",
    "icon_survey",
    "icon_ad",
    "icon_issue",
}

COMIC_STORY_KEYWORDS: tuple[str, ...] = (
    "던전",
    "인던",
    "레이드",
    "공대",
    "파티",
    "지인팟",
    "막공",
    "탱커",
    "힐러",
    "근딜",
    "원딜",
    "물빵",
    "주사위",
    "닌자",
    "어그로",
    "전멸",
    "리셋",
    "명언",
    "뉴비",
    "고인물",
    "마나",
    "캐삭",
    "전사",
    "성기사",
    "기사",
    "보기",
    "도적",
    "사냥꾼",
    "냥꾼",
    "주술사",
    "술사",
    "드루이드",
    "회드",
    "사제",
    "흑마법사",
    "흑마",
    "마법사",
    "법사",
    "ㅋㅋ",
    "레전드",
    "썰",
    "억까",
    "사건",
)

UTILITY_PENALTY_KEYWORDS: tuple[str, ...] = (
    "애드온",
    "매크로",
    "위크오라",
    "견적",
    "구인",
    "모집",
    "길드원",
    "공대원",
    "판매",
    "구매",
    "패치노트",
    "서버점검",
    "질문드립니다",
)

BLOCKED_MARKERS: tuple[str, ...] = (
    "captcha",
    "recaptcha",
    "hcaptcha",
    "cf-turnstile",
    "verify you are human",
    "비정상적인 접근",
)


class GalleryAccessBlockedError(RuntimeError):
    """Raised when the gallery returns an anti-bot/CAPTCHA gate or HTTP block."""


def _parse_int(raw: str | None) -> int:
    if not raw:
        return 0
    match = re.search(r"\d[\d,]*", raw)
    if not match:
        return 0
    return int(match.group(0).replace(",", ""))


def _clean_whitespace(text: str) -> str:
    text = text.replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    cleaned_lines: list[str] = []
    blank_streak = 0
    for line in lines:
        if not line:
            blank_streak += 1
            if blank_streak <= 1 and cleaned_lines:
                cleaned_lines.append("")
        else:
            blank_streak = 0
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def _check_not_blocked(html: str, status_code: int = 200) -> None:
    if status_code in (403, 429, 503):
        raise GalleryAccessBlockedError(
            f"Gallery request returned HTTP {status_code}; stopping without bypass."
        )
    lowered = html.lower()
    if any(marker in lowered for marker in BLOCKED_MARKERS) and "ub-content" not in lowered and "write_div" not in lowered:
        raise GalleryAccessBlockedError(
            "Gallery page appears gated by CAPTCHA or anti-bot protection; stopping without bypass."
        )


def _is_excluded_row(row: Tag) -> bool:
    row_classes = set(row.get("class") or [])
    if row_classes & {"notice", "ad", "survey", "us-notice"}:
        return True

    data_type = (row.get("data-type") or "").strip().lower()
    if data_type in EXCLUDED_ROW_TYPES:
        return True

    num_cell = row.find("td", class_="gall_num")
    num_text = num_cell.get_text(strip=True) if num_cell else ""
    if num_text and not num_text.isdigit():
        return True

    subject_cell = row.find("td", class_="gall_subject")
    if subject_cell:
        subject_text = subject_cell.get_text(" ", strip=True)
        if any(token.lower() in subject_text.lower() for token in EXCLUDED_SUBJECT_TOKENS):
            return True

    tit_cell = row.find("td", class_="gall_tit")
    if tit_cell:
        if tit_cell.find(class_=re.compile(r"icon_(notice|survey|ad|issue)", re.I)):
            return True
        bold_tag = tit_cell.find("b")
        if bold_tag and any(
            token in bold_tag.get_text(strip=True) for token in ("공지", "설문", "AD")
        ):
            return True

    return False


def build_list_url(gallery_id: str = DEFAULT_GALLERY_ID, page: int = 1, recommend_only: bool = True) -> str:
    """Build a public DCInside minor gallery list URL."""
    base = f"{DC_BASE_URL}/mgallery/board/lists/?id={gallery_id}"
    if recommend_only:
        base += "&exception_mode=recommend"
    if page > 1:
        base += f"&page={page}"
    return base


def build_post_url(post_no: str, gallery_id: str = DEFAULT_GALLERY_ID) -> str:
    """Build a canonical public DCInside minor gallery post view URL."""
    clean_no = re.sub(r"\D+", "", str(post_no))
    return f"{DC_BASE_URL}/mgallery/board/view/?id={gallery_id}&no={clean_no}"


def parse_recommend_list(html: str, gallery_id: str = DEFAULT_GALLERY_ID) -> list[GalleryPost]:
    """Parse DCInside minor gallery recommend list HTML into `GalleryPost` entries.

    Automatically filters out notices, surveys, ads, and non-numeric rows.
    """
    _check_not_blocked(html)
    soup = BeautifulSoup(html, "html.parser")
    posts: list[GalleryPost] = []
    seen_nos: set[str] = set()

    rows = soup.select("tr.ub-content")
    if not rows:
        rows = soup.select("tbody tr")

    for row in rows:
        if _is_excluded_row(row):
            continue

        num_cell = row.find("td", class_="gall_num")
        raw_no = (row.get("data-no") or (num_cell.get_text(strip=True) if num_cell else "")).strip()
        if not raw_no.isdigit():
            continue
        if raw_no in seen_nos:
            continue

        tit_cell = row.find("td", class_="gall_tit")
        if not tit_cell:
            continue

        title_link: Tag | None = None
        for anchor in tit_cell.find_all("a", href=True):
            anchor_classes = set(anchor.get("class") or [])
            if "reply_numbox" in anchor_classes:
                continue
            href = str(anchor["href"])
            if "javascript:" in href.lower():
                continue
            title_link = anchor
            break

        if title_link is None:
            continue

        title = _clean_whitespace(title_link.get_text(" ", strip=True))
        if not title:
            continue
        if any(title.startswith(f"[{tok}]") for tok in ("공지", "설문", "AD", "광고")):
            continue

        href = str(title_link["href"])
        if "/board/view/" in href:
            url = urljoin(DC_BASE_URL, href)
        else:
            url = build_post_url(raw_no, gallery_id=gallery_id)

        reply_span = tit_cell.find(class_="reply_num")
        comments_count = _parse_int(reply_span.get_text(strip=True)) if reply_span else 0

        writer_cell = row.find("td", class_="gall_writer")
        author = ""
        if writer_cell:
            author = str(writer_cell.get("data-nick") or "").strip()
            if not author:
                author = _clean_whitespace(writer_cell.get_text(" ", strip=True))
        author = author or "익명"

        date_cell = row.find("td", class_="gall_date")
        date_str = ""
        if date_cell:
            date_str = str(date_cell.get("title") or date_cell.get_text(strip=True)).strip()

        views_cell = row.find("td", class_="gall_count")
        views = _parse_int(views_cell.get_text(strip=True)) if views_cell else 0

        rec_cell = row.find("td", class_="gall_recommend")
        recommends = _parse_int(rec_cell.get_text(strip=True)) if rec_cell else 0

        seen_nos.add(raw_no)
        posts.append(
            GalleryPost(
                post_no=raw_no,
                title=title,
                url=url,
                author=author,
                date_str=date_str,
                views=views,
                recommends=recommends,
                comments_count=comments_count,
            )
        )

    return posts


def parse_post_detail(
    html: str,
    post_no: str,
    gallery_id: str = DEFAULT_GALLERY_ID,
    base_post: GalleryPost | None = None,
    max_comments: int = 15,
) -> GalleryPost:
    """Parse a DCInside post view page to extract body text, stats, and reader comments."""
    _check_not_blocked(html)
    soup = BeautifulSoup(html, "html.parser")

    title_node = soup.select_one(".title_subject") or soup.select_one("h3.title")
    title = (
        _clean_whitespace(title_node.get_text(" ", strip=True))
        if title_node
        else (base_post.title if base_post else f"게시글 #{post_no}")
    )

    writer_node = soup.select_one(".gallview_head .gall_writer") or soup.select_one(".gall_writer")
    author = ""
    if writer_node:
        author = str(writer_node.get("data-nick") or "").strip()
        if not author:
            nick_node = writer_node.select_one(".nickname")
            author = _clean_whitespace(
                (nick_node or writer_node).get_text(" ", strip=True)
            )
    if not author:
        author = base_post.author if base_post else "익명"

    date_node = soup.select_one(".gallview_head .gall_date") or soup.select_one(".gall_date")
    date_str = ""
    if date_node:
        date_str = str(date_node.get("title") or date_node.get_text(strip=True)).strip()
    if not date_str:
        date_str = base_post.date_str if base_post else ""

    views_node = soup.select_one(".gallview_head .gall_count") or soup.select_one(".gall_count")
    views = _parse_int(views_node.get_text(strip=True)) if views_node else (base_post.views if base_post else 0)

    rec_node = soup.select_one(".up_num") or soup.select_one(".gallview_head .gall_recommend")
    recommends = (
        _parse_int(rec_node.get_text(strip=True))
        if rec_node
        else (base_post.recommends if base_post else 0)
    )

    comment_cnt_node = soup.select_one(".gallview_head .gall_comment") or soup.select_one(".gall_reply_num")
    comments_count = (
        _parse_int(comment_cnt_node.get_text(strip=True))
        if comment_cnt_node
        else (base_post.comments_count if base_post else 0)
    )

    body_node = soup.select_one(".write_div") or soup.select_one(".writing_view_box")
    body = ""
    if body_node is not None:
        # Remove scripts/styles without mutating callers' expectations
        for junk in body_node.select("script, style, .og-div, .dc_allim"):
            junk.decompose()
        body = _clean_whitespace(body_node.get_text("\n", strip=True))
    elif base_post is not None:
        body = base_post.body

    comments: list[str] = []
    for cmt in soup.select(".cmt_txtbox .usertxt, p.usertxt"):
        text = _clean_whitespace(cmt.get_text(" ", strip=True))
        if not text:
            continue
        if text not in comments:
            comments.append(text)
        if len(comments) >= max_comments:
            break

    if not comments and base_post is not None:
        comments = list(base_post.comments)

    if comments and comments_count < len(comments):
        comments_count = len(comments)

    url = base_post.url if base_post else build_post_url(post_no, gallery_id=gallery_id)

    return GalleryPost(
        post_no=str(post_no),
        title=title,
        url=url,
        author=author,
        date_str=date_str,
        views=views,
        recommends=recommends,
        comments_count=comments_count,
        body=body,
        comments=comments,
    )


def load_produced_post_nos(episodes_json: Path) -> set[str]:
    """Read already-produced `source_post_no` values from `data/episodes.json`."""
    if not episodes_json.exists():
        return set()
    raw = json.loads(episodes_json.read_text(encoding="utf-8"))
    items = raw.get("episodes", []) if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        return set()
    produced: set[str] = set()
    for item in items:
        if isinstance(item, dict) and item.get("source_post_no") is not None:
            produced.add(str(item["source_post_no"]).strip())
    return produced


def filter_unproduced(
    posts: Iterable[GalleryPost],
    existing_post_nos: set[str],
) -> list[GalleryPost]:
    """Exclude posts whose `post_no` has already been turned into an episode."""
    return [post for post in posts if str(post.post_no).strip() not in existing_post_nos]


def score_post(post: GalleryPost) -> float:
    """Compute a comedic/skit suitability score for a gallery post.

    Rewards strong recommendations, active comment banter, WoW dungeon/class skit
    keywords, and readable story text length while penalizing utility/recruitment posts.
    """
    score = 0.0

    # Engagement signal (sublinear dampened views + strong recommend/comment weight)
    score += post.recommends * 3.0
    score += post.comments_count * 1.8
    if post.views > 0:
        score += min(math.log1p(post.views) * 2.5, 25.0)

    combined = f"{post.title}\n{post.body}"
    lowered_title = post.title.lower()
    lowered_combined = combined.lower()

    # Comedy & WoW dungeon skit richness
    keyword_hits = sum(1 for kw in COMIC_STORY_KEYWORDS if kw in lowered_combined)
    score += min(keyword_hits * 4.5, 36.0)

    # Dialogue / laughter markers indicate punchy comic timing
    if "?" in post.title or "!" in post.title:
        score += 3.0
    if "ㅋㅋ" in combined or "ㅎㅎ" in combined:
        score += 4.0
    if any(q in combined for q in ('"', "'", "“", "”", ":", "->")):
        score += 4.0

    # Narrative text-length sweet spot (when body has been fetched)
    body_len = len(post.body.strip())
    if body_len > 0:
        if 60 <= body_len <= 1200:
            score += 18.0
        elif 25 <= body_len < 60:
            score += 7.0
        elif 1200 < body_len <= 2500:
            score += 10.0
        elif body_len < 25:
            score -= 8.0
        else:
            score += 2.0

    # Comment context bonus
    if post.comments:
        score += min(len(post.comments) * 1.5, 12.0)

    # Penalize dry technical/recruitment/trade posts
    penalty_hits = sum(1 for kw in UTILITY_PENALTY_KEYWORDS if kw in lowered_title)
    score -= penalty_hits * 18.0

    return round(score, 2)


def rank_candidates(
    posts: Sequence[GalleryPost],
    existing_post_nos: set[str] | None = None,
) -> list[tuple[GalleryPost, float]]:
    """Deduplicate against produced episodes and rank candidates best-first."""
    remaining = (
        filter_unproduced(posts, existing_post_nos)
        if existing_post_nos
        else list(posts)
    )
    scored = [(post, score_post(post)) for post in remaining]
    scored.sort(key=lambda pair: (pair[1], pair[0].recommends, pair[0].comments_count), reverse=True)
    return scored


class GalleryScout:
    """HTTP scout for publicly reading DCInside WOW Forever minor gallery posts."""

    def __init__(
        self,
        gallery_id: str = DEFAULT_GALLERY_ID,
        timeout: float = 15.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.gallery_id = gallery_id
        self.timeout = timeout
        self._external_client = client

    def _get_html(self, url: str, referer: str | None = None) -> str:
        headers = dict(DEFAULT_HEADERS)
        if referer:
            headers["Referer"] = referer

        if self._external_client is not None:
            response = self._external_client.get(url, headers=headers)
            _check_not_blocked(response.text, status_code=response.status_code)
            response.raise_for_status()
            return response.text

        with httpx.Client(
            timeout=self.timeout,
            follow_redirects=True,
            headers=headers,
        ) as client:
            response = client.get(url)
            _check_not_blocked(response.text, status_code=response.status_code)
            response.raise_for_status()
            return response.text

    def fetch_recommend_posts(self, page: int = 1) -> list[GalleryPost]:
        """Fetch and parse one page of the gallery's recommend (개념글) list."""
        url = build_list_url(self.gallery_id, page=page, recommend_only=True)
        html = self._get_html(url, referer=f"{DC_BASE_URL}/mgallery/board/lists/?id={self.gallery_id}")
        return parse_recommend_list(html, gallery_id=self.gallery_id)

    def fetch_post_detail(
        self,
        post_no: str,
        base_post: GalleryPost | None = None,
    ) -> GalleryPost:
        """Fetch and parse a single post's full text and comments."""
        url = base_post.url if base_post else build_post_url(post_no, gallery_id=self.gallery_id)
        referer = build_list_url(self.gallery_id, recommend_only=True)
        html = self._get_html(url, referer=referer)
        return parse_post_detail(
            html,
            post_no=str(post_no),
            gallery_id=self.gallery_id,
            base_post=base_post,
        )

    def scout_candidates(
        self,
        existing_post_nos: set[str] | None = None,
        pages: int = 1,
        limit: int = 10,
        fetch_bodies_for_top: int = 5,
    ) -> list[tuple[GalleryPost, float]]:
        """Fetch recommend pages, deduplicate, enrich top candidates with bodies, and rank."""
        collected: list[GalleryPost] = []
        seen: set[str] = set()
        for page in range(1, max(1, pages) + 1):
            for post in self.fetch_recommend_posts(page=page):
                if post.post_no not in seen:
                    seen.add(post.post_no)
                    collected.append(post)

        preliminary = rank_candidates(collected, existing_post_nos=existing_post_nos)
        enriched: list[GalleryPost] = []

        for idx, (post, _score) in enumerate(preliminary[: max(limit, fetch_bodies_for_top)]):
            if idx < fetch_bodies_for_top and not post.body:
                try:
                    enriched.append(self.fetch_post_detail(post.post_no, base_post=post))
                except GalleryAccessBlockedError:
                    raise
                except Exception:
                    enriched.append(post)
            else:
                enriched.append(post)

        reranked = rank_candidates(enriched, existing_post_nos=existing_post_nos)
        return reranked[:limit]
