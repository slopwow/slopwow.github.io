"""Unit tests for wow_sloptoon.scout (parsing, filtering, deduplication, ranking, block handling)."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from wow_sloptoon.models import GalleryPost
from wow_sloptoon.scout import (
    GalleryAccessBlockedError,
    GalleryScout,
    filter_unproduced,
    load_produced_post_nos,
    parse_post_detail,
    parse_recommend_list,
    rank_candidates,
    score_post,
)

SAMPLE_LIST_HTML = """
<html>
<body>
<table class="gall_list">
  <tbody>
    <tr class="ub-content notice" data-no="1" data-type="icon_notice">
      <td class="gall_num">공지</td>
      <td class="gall_subject">공지</td>
      <td class="gall_tit"><a href="/mgallery/board/view/?id=wowforever&no=1"><b>[공지]</b> 갤러리 이용 규칙</a></td>
      <td class="gall_writer" data-nick="주딱">주딱</td>
      <td class="gall_date" title="2026-11-01 00:00:00">11.01</td>
      <td class="gall_count">9999</td>
      <td class="gall_recommend">100</td>
    </tr>
    <tr class="ub-content" data-no="2" data-type="icon_survey">
      <td class="gall_num">설문</td>
      <td class="gall_subject">설문</td>
      <td class="gall_tit"><a href="/mgallery/board/view/?id=wowforever&no=2">설문조사 참여</a></td>
      <td class="gall_writer" data-nick="운영자">운영자</td>
      <td class="gall_date">11.02</td>
      <td class="gall_count">500</td>
      <td class="gall_recommend">0</td>
    </tr>
    <tr class="ub-content ad" data-no="3" data-type="icon_ad">
      <td class="gall_num">AD</td>
      <td class="gall_subject">광고</td>
      <td class="gall_tit"><a href="https://example.com/ad">스폰서 광고</a></td>
      <td class="gall_writer" data-nick="AD">AD</td>
      <td class="gall_date">11.03</td>
      <td class="gall_count">-</td>
      <td class="gall_recommend">0</td>
    </tr>
    <tr class="ub-content us-post" data-no="92059">
      <td class="gall_num">92059</td>
      <td class="gall_subject">일반</td>
      <td class="gall_tit">
        <a href="/mgallery/board/view/?id=wowforever&no=92059&exception_mode=recommend">흑마법사가 물을 어케 줌?</a>
        <a class="reply_numbox" href="#cmt"><span class="reply_num">[42]</span></a>
      </td>
      <td class="gall_writer" data-nick="멜론주스흑마">멜론주스흑마</td>
      <td class="gall_date" title="2026-11-20 21:10:00">11.20</td>
      <td class="gall_count">3,420</td>
      <td class="gall_recommend">88</td>
    </tr>
    <tr class="ub-content us-post" data-no="97101">
      <td class="gall_num">97101</td>
      <td class="gall_subject">썰</td>
      <td class="gall_tit">
        <a href="/mgallery/board/view/?id=wowforever&no=97101&exception_mode=recommend">던전 탱커 묵언수행하다가 막넴에서 터진 레전드 썰 ㅋㅋ</a>
        <a class="reply_numbox" href="#cmt"><span class="reply_num">[61]</span></a>
      </td>
      <td class="gall_writer" data-nick="회드눈물">회드눈물</td>
      <td class="gall_date" title="2026-11-21 12:30:00">12:30</td>
      <td class="gall_count">2,810</td>
      <td class="gall_recommend">74</td>
    </tr>
    <tr class="ub-content us-post" data-no="97102">
      <td class="gall_num">97102</td>
      <td class="gall_subject">질문</td>
      <td class="gall_tit">
        <a href="/mgallery/board/view/?id=wowforever&no=97102&exception_mode=recommend">애드온 매크로 질문드립니다</a>
        <a class="reply_numbox" href="#cmt"><span class="reply_num">[3]</span></a>
      </td>
      <td class="gall_writer" data-nick="질문자">질문자</td>
      <td class="gall_date" title="2026-11-21 13:00:00">13:00</td>
      <td class="gall_count">180</td>
      <td class="gall_recommend">10</td>
    </tr>
  </tbody>
</table>
</body>
</html>
"""

SAMPLE_DETAIL_HTML = """
<html>
<body>
  <div class="gallview_head">
    <span class="title_subject">던전 탱커 묵언수행하다가 막넴에서 터진 레전드 썰 ㅋㅋ</span>
    <span class="gall_writer" data-nick="회드눈물">회드눈물</span>
    <span class="gall_date" title="2026-11-21 12:30:00">2026-11-21 12:30:00</span>
    <span class="gall_count">조회 2,900</span>
    <span class="gall_comment">댓글 61</span>
  </div>
  <div class="up_num">76</div>
  <div class="write_div">
    <script>console.log("ignore me");</script>
    <p>3시간 동안 한마디도 안 하던 언데드 성기사 탱커가 막넴 앞에서 갑자기 멈춤.</p>
    <p>파티원들 다 긴장했는데 "마나 좀 채우시죠 힐러님" 딱 한 마디 치고 보스 풀링함 ㅋㅋ</p>
    <p>그때 나엘 사제 마나 0%였고 스카이본 법사는 호빵만 들고 멍때리고 있었음.</p>
  </div>
  <div class="comment_box">
    <div class="cmt_txtbox"><p class="usertxt">진짜 묵언수행 보기가 제일 무섭다 ㅋㅋㅋ</p></div>
    <div class="cmt_txtbox"><p class="usertxt">법사 동공지진 상상되네</p></div>
    <div class="cmt_txtbox"><p class="usertxt">   </p></div>
  </div>
</body>
</html>
"""


def test_parse_recommend_list_filters_notice_survey_and_ad() -> None:
    posts = parse_recommend_list(SAMPLE_LIST_HTML)
    post_nos = [p.post_no for p in posts]
    assert post_nos == ["92059", "97101", "97102"]

    first = posts[0]
    assert first.title == "흑마법사가 물을 어케 줌?"
    assert first.author == "멜론주스흑마"
    assert first.views == 3420
    assert first.recommends == 88
    assert first.comments_count == 42
    assert first.url.startswith("https://gall.dcinside.com/mgallery/board/view/")


def test_parse_post_detail_extracts_clean_body_and_comments() -> None:
    post = parse_post_detail(SAMPLE_DETAIL_HTML, post_no="97101")
    assert post.post_no == "97101"
    assert post.recommends == 76
    assert post.views == 2900
    assert "ignore me" not in post.body
    assert "언데드 성기사 탱커" in post.body
    assert post.comments == [
        "진짜 묵언수행 보기가 제일 무섭다 ㅋㅋㅋ",
        "법사 동공지진 상상되네",
    ]


def test_deduplication_and_ranking(tmp_path: Path) -> None:
    episodes_json = tmp_path / "episodes.json"
    episodes_json.write_text(
        json.dumps([{"episode_id": "ep001", "source_post_no": "92059"}]),
        encoding="utf-8",
    )

    produced = load_produced_post_nos(episodes_json)
    assert produced == {"92059"}

    posts = parse_recommend_list(SAMPLE_LIST_HTML)
    unproduced = filter_unproduced(posts, produced)
    assert [p.post_no for p in unproduced] == ["97101", "97102"]

    # Enrich 97101 with body and confirm it clearly outranks utility question 97102
    enriched_story = parse_post_detail(SAMPLE_DETAIL_HTML, post_no="97101", base_post=unproduced[0])
    ranked = rank_candidates([unproduced[1], enriched_story], existing_post_nos=produced)
    assert ranked[0][0].post_no == "97101"
    assert score_post(enriched_story) > score_post(unproduced[1])


def test_gallery_scout_end_to_end_with_mock_transport() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "/lists/" in str(request.url):
            return httpx.Response(200, text=SAMPLE_LIST_HTML)
        if "no=97101" in str(request.url):
            return httpx.Response(200, text=SAMPLE_DETAIL_HTML)
        return httpx.Response(200, text="<html><body><div class='write_div'>짧음</div></body></html>")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    scout = GalleryScout(gallery_id="wowforever", client=client)

    candidates = scout.scout_candidates(existing_post_nos={"92059"}, pages=1, limit=5)
    assert len(candidates) == 2
    best_post, best_score = candidates[0]
    assert best_post.post_no == "97101"
    assert "언데드 성기사" in best_post.body
    assert best_score > candidates[1][1]


def test_scout_stops_cleanly_on_captcha_or_http_block() -> None:
    captcha_html = "<html><body>Please complete reCAPTCHA to verify you are human</body></html>"
    with pytest.raises(GalleryAccessBlockedError):
        parse_recommend_list(captcha_html)

    def blocked_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="Forbidden")

    client = httpx.Client(transport=httpx.MockTransport(blocked_handler))
    scout = GalleryScout(gallery_id="wowforever", client=client)
    with pytest.raises(GalleryAccessBlockedError):
        scout.fetch_recommend_posts()
