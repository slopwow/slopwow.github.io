/* 와우 포에버 슬롭툰 — 정적 웹 아카이브 인터랙션 */
(function () {
  "use strict";

  var HOME_PAGE_SIZE = 24;

  function showToast(msg) {
    var toast = document.getElementById("toast");
    if (!toast) return;
    toast.textContent = msg;
    toast.hidden = false;
    clearTimeout(showToast._timer);
    showToast._timer = setTimeout(function () {
      toast.hidden = true;
    }, 3200);
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).catch(function () {
        return fallbackCopy(text);
      });
    }
    return Promise.resolve(fallbackCopy(text));
  }

  function fallbackCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand("copy");
    } catch (_err) {
      /* ignore */
    }
    document.body.removeChild(ta);
  }

  function episodeHref(rootPrefix, episodeId) {
    return (rootPrefix || "") + "episodes/" + encodeURIComponent(episodeId) + ".html";
  }

  /* ---------------- GLOBAL RANDOM EPISODE NAVIGATION ---------------- */
  function initRandomButtons() {
    var buttons = document.querySelectorAll(".js-random-ep");
    if (!buttons.length) return;

    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var data = window.__SLOPTOON_DATA__ || {};
        var episodes = Array.isArray(data.episodes) ? data.episodes : [];
        var rootPrefix = data.rootPrefix || "";
        if (episodes.length === 0) {
          showToast("아직 등록된 에피소드가 없습니다.");
          return;
        }
        var currentId = window.__SLOPTOON_CURRENT_EP__ || "";
        var pool = episodes.filter(function (item) {
          return item.episode_id !== currentId;
        });
        if (pool.length === 0) {
          if (currentId) {
            showToast("현재 1화만 등록되어 있어요! 곧 새로운 념글 만화가 추가됩니다.");
            return;
          }
          pool = episodes;
        }
        var picked = pool[Math.floor(Math.random() * pool.length)];
        window.location.href = episodeHref(rootPrefix, picked.episode_id);
      });
    });
  }

  /* ---------------- HOME PAGE (SEARCH / FILTER / SORT / PAGINATION) ---------------- */
  function initHomePage() {
    var grid = document.getElementById("episodeGrid");
    var searchInput = document.getElementById("searchInput");
    var filterBar = document.getElementById("castFilterBar");
    var sortToggle = document.getElementById("sortToggle");
    var resultCount = document.getElementById("resultCount");
    var emptyFilter = document.getElementById("emptyFilter");
    var resetBtn = document.getElementById("resetFiltersBtn");
    var loadMoreWrap = document.getElementById("loadMoreWrap");
    var loadMoreBtn = document.getElementById("loadMoreBtn");
    var showAllBtn = document.getElementById("showAllBtn");
    if (!grid) return;

    var cards = Array.prototype.slice.call(grid.querySelectorAll(".ep-card"));
    var totalAll = cards.length;
    var activeCast = "";
    var sortOrder = "desc";
    var renderedOrder = "desc";
    var visibleLimit = HOME_PAGE_SIZE;

    // Sync initial ?cast= query parameter if linked from cast.html
    var params = new URLSearchParams(window.location.search);
    var initCast = params.get("cast");
    if (initCast && filterBar) {
      activeCast = initCast;
      var btns = filterBar.querySelectorAll(".filter-chip");
      btns.forEach(function (btn) {
        btn.classList.toggle("is-active", btn.getAttribute("data-cast") === activeCast);
      });
    }

    function reorderDomIfNeeded() {
      if (renderedOrder === sortOrder) return;
      cards.sort(function (a, b) {
        var na = parseInt(a.getAttribute("data-num") || "0", 10);
        var nb = parseInt(b.getAttribute("data-num") || "0", 10);
        return sortOrder === "desc" ? nb - na : na - nb;
      });
      var frag = document.createDocumentFragment();
      cards.forEach(function (card) {
        frag.appendChild(card);
      });
      grid.appendChild(frag);
      renderedOrder = sortOrder;
    }

    function applyFilters() {
      var q = (searchInput ? searchInput.value : "").trim().toLowerCase();
      var qNoHash = q.replace(/^#/, "");
      var matched = [];

      reorderDomIfNeeded();

      cards.forEach(function (card) {
        var epId = (card.getAttribute("data-id") || "").toLowerCase();
        var epNum = (card.getAttribute("data-num") || "").toLowerCase();
        var title = card.getAttribute("data-title") || "";
        var sub = card.getAttribute("data-sub") || "";
        var post = card.getAttribute("data-post") || "";
        var castStr = card.getAttribute("data-cast") || "";
        var castList = castStr ? castStr.split("|") : [];

        var matchesCast = !activeCast || castList.indexOf(activeCast) !== -1;
        var matchesQuery =
          !q ||
          title.indexOf(q) !== -1 ||
          sub.indexOf(q) !== -1 ||
          post.indexOf(qNoHash) !== -1 ||
          epId.indexOf(q) !== -1 ||
          ("ep." + epNum).indexOf(q) !== -1 ||
          (epNum + "화").indexOf(q) !== -1 ||
          castStr.toLowerCase().indexOf(q) !== -1;

        if (matchesCast && matchesQuery) {
          matched.push(card);
        } else {
          card.hidden = true;
        }
      });

      var totalMatched = matched.length;
      var shownCount = 0;
      for (var i = 0; i < totalMatched; i++) {
        var showCard = i < visibleLimit;
        matched[i].hidden = !showCard;
        if (showCard) shownCount += 1;
      }

      if (resultCount) {
        if (q || activeCast) {
          resultCount.textContent = "검색 결과 " + totalMatched + "화 (전체 " + totalAll + "화)";
        } else if (shownCount < totalMatched) {
          resultCount.textContent = "총 " + totalMatched + "개의 에피소드 중 " + shownCount + "화 표시 중";
        } else {
          resultCount.textContent = "총 " + totalMatched + "개의 에피소드";
        }
      }
      if (emptyFilter) {
        emptyFilter.hidden = totalMatched > 0;
      }
      if (loadMoreWrap) {
        var remaining = totalMatched - shownCount;
        loadMoreWrap.hidden = remaining <= 0;
        if (loadMoreBtn && remaining > 0) {
          loadMoreBtn.textContent = "더 보기 (남은 " + remaining + "화)";
        }
      }
    }

    if (searchInput) {
      searchInput.addEventListener("input", function () {
        visibleLimit = HOME_PAGE_SIZE;
        applyFilters();
      });
    }
    if (filterBar) {
      filterBar.addEventListener("click", function (ev) {
        var btn = ev.target.closest(".filter-chip");
        if (!btn) return;
        activeCast = btn.getAttribute("data-cast") || "";
        visibleLimit = HOME_PAGE_SIZE;
        filterBar.querySelectorAll(".filter-chip").forEach(function (b) {
          b.classList.toggle("is-active", b === btn);
        });
        applyFilters();
      });
    }
    if (sortToggle) {
      sortToggle.addEventListener("click", function () {
        sortOrder = sortOrder === "desc" ? "asc" : "desc";
        sortToggle.setAttribute("data-order", sortOrder);
        sortToggle.textContent = sortOrder === "desc" ? "최신순 ↓" : "1화부터 ↑";
        visibleLimit = HOME_PAGE_SIZE;
        applyFilters();
      });
    }
    if (loadMoreBtn) {
      loadMoreBtn.addEventListener("click", function () {
        visibleLimit += HOME_PAGE_SIZE;
        applyFilters();
      });
    }
    if (showAllBtn) {
      showAllBtn.addEventListener("click", function () {
        visibleLimit = Math.max(totalAll, HOME_PAGE_SIZE);
        applyFilters();
      });
    }
    if (resetBtn) {
      resetBtn.addEventListener("click", function () {
        activeCast = "";
        visibleLimit = HOME_PAGE_SIZE;
        if (searchInput) searchInput.value = "";
        if (filterBar) {
          filterBar.querySelectorAll(".filter-chip").forEach(function (b) {
            b.classList.toggle("is-active", (b.getAttribute("data-cast") || "") === "");
          });
        }
        applyFilters();
      });
    }

    applyFilters();
  }

  /* ---------------- EPISODE READER, SHARE, BINGE & DC HELPER ---------------- */
  function selectRecommended(episodes, currentIndex, limit) {
    var currentId = episodes[currentIndex].episode_id;
    var adjacent = {};
    if (currentIndex > 0) adjacent[episodes[currentIndex - 1].episode_id] = true;
    if (currentIndex + 1 < episodes.length) adjacent[episodes[currentIndex + 1].episode_id] = true;

    var nonAdjacent = [];
    var adjList = [];
    for (var i = episodes.length - 1; i >= 0; i--) {
      var item = episodes[i];
      if (item.episode_id === currentId) continue;
      if (adjacent[item.episode_id]) {
        adjList.push(item);
      } else {
        nonAdjacent.push(item);
      }
    }
    return nonAdjacent.concat(adjList).slice(0, limit);
  }

  function buildRecommendCardEl(rec, rootPrefix) {
    var article = document.createElement("article");
    article.className = "ep-card";

    var link = document.createElement("a");
    link.className = "ep-card-link";
    link.href = episodeHref(rootPrefix, rec.episode_id);

    var thumbWrap = document.createElement("div");
    thumbWrap.className = "ep-thumb-wrap";
    var img = document.createElement("img");
    img.src = rootPrefix + rec.thumb_image;
    img.alt = "EP." + rec.episode_number + " " + rec.title;
    img.className = "ep-thumb";
    img.loading = "lazy";
    var cuts = document.createElement("span");
    cuts.className = "thumb-cuts";
    cuts.textContent = rec.cut_count + "컷";
    thumbWrap.appendChild(img);
    thumbWrap.appendChild(cuts);

    var body = document.createElement("div");
    body.className = "ep-card-body";
    var metaRow = document.createElement("div");
    metaRow.className = "meta-row";
    var pill = document.createElement("span");
    pill.className = "ep-pill ep-pill-sm";
    pill.textContent = "EP." + rec.episode_number;
    var postNo = document.createElement("span");
    postNo.className = "post-no";
    postNo.textContent = "#" + rec.source_post_no;
    var dt = document.createElement("span");
    dt.className = "meta-date";
    dt.textContent = rec.date_short || "";
    metaRow.appendChild(pill);
    metaRow.appendChild(postNo);
    metaRow.appendChild(dt);

    var h3 = document.createElement("h3");
    h3.className = "ep-card-title";
    h3.textContent = rec.title;

    var sub = document.createElement("p");
    sub.className = "ep-card-sub";
    sub.textContent = rec.subtitle || "";

    var chipRow = document.createElement("div");
    chipRow.className = "mini-chip-row";
    (rec.cast_chips || []).forEach(function (chip) {
      var sp = document.createElement("span");
      sp.className = "mini-chip";
      var dot = document.createElement("span");
      dot.className = "cast-dot";
      dot.style.background = chip.color || "#111111";
      sp.appendChild(dot);
      sp.appendChild(document.createTextNode(chip.name));
      chipRow.appendChild(sp);
    });

    body.appendChild(metaRow);
    body.appendChild(h3);
    body.appendChild(sub);
    body.appendChild(chipRow);
    link.appendChild(thumbWrap);
    link.appendChild(body);
    article.appendChild(link);
    return article;
  }

  function buildBingeCardEl(targetEp, isNext, rootPrefix) {
    if (!targetEp) {
      var disabled = document.createElement("div");
      disabled.className = isNext ? "nav-ep-card nav-ep-next is-disabled" : "nav-ep-card is-disabled";
      var info = document.createElement("div");
      info.className = "nav-ep-info";
      var dir = document.createElement("span");
      dir.className = "nav-ep-dir";
      dir.textContent = isNext ? "다음 화 →" : "← 이전 화";
      var ttl = document.createElement("span");
      ttl.className = "nav-ep-title";
      ttl.textContent = isNext ? "가장 최신 에피소드입니다" : "첫 번째 에피소드입니다";
      var hint = document.createElement("span");
      hint.className = "nav-ep-sub";
      hint.textContent = isNext ? "랜덤 화 보기로 다른 명장면도 즐겨보세요!" : "지금 1화부터 정주행 중이에요!";
      info.appendChild(dir);
      info.appendChild(ttl);
      info.appendChild(hint);
      disabled.appendChild(info);
      return disabled;
    }

    var a = document.createElement("a");
    a.className = isNext ? "nav-ep-card nav-ep-next" : "nav-ep-card";
    a.href = episodeHref(rootPrefix, targetEp.episode_id);

    var thumbWrap = document.createElement("div");
    thumbWrap.className = "nav-ep-thumb-wrap";
    var img = document.createElement("img");
    img.src = rootPrefix + targetEp.thumb_image;
    img.alt = "EP." + targetEp.episode_number + " " + targetEp.title;
    img.className = "nav-ep-thumb";
    img.loading = "lazy";
    thumbWrap.appendChild(img);

    var infoBox = document.createElement("div");
    infoBox.className = "nav-ep-info";
    var dirSpan = document.createElement("span");
    dirSpan.className = isNext ? "nav-ep-dir nav-ep-dir-accent" : "nav-ep-dir";
    dirSpan.textContent = isNext ? "다음 화 바로 보기 →" : "← 이전 화 정주행";
    var titleStrong = document.createElement("strong");
    titleStrong.className = "nav-ep-title";
    titleStrong.textContent = "EP." + targetEp.episode_number + " " + targetEp.title;
    var subSpan = document.createElement("span");
    subSpan.className = "nav-ep-sub";
    subSpan.textContent = targetEp.subtitle || "";
    infoBox.appendChild(dirSpan);
    infoBox.appendChild(titleStrong);
    infoBox.appendChild(subSpan);

    if (isNext) {
      a.appendChild(infoBox);
      a.appendChild(thumbWrap);
    } else {
      a.appendChild(thumbWrap);
      a.appendChild(infoBox);
    }
    return a;
  }

  function initEpisodePage() {
    var data = window.__SLOPTOON_DATA__;
    if (!data || !Array.isArray(data.episodes) || data.episodes.length === 0) return;

    var episodes = data.episodes;
    var rootPrefix = data.rootPrefix || "";

    var params = new URLSearchParams(window.location.search);
    var requestedId = data.pinnedEpisodeId || params.get("id") || "";
    var currentIndex = episodes.length - 1;
    if (requestedId) {
      for (var i = 0; i < episodes.length; i++) {
        if (episodes[i].episode_id === requestedId || String(episodes[i].episode_number) === requestedId) {
          currentIndex = i;
          break;
        }
      }
    }
    var ep = episodes[currentIndex];
    window.__SLOPTOON_CURRENT_EP__ = ep.episode_id;

    var prevEp = currentIndex > 0 ? episodes[currentIndex - 1] : null;
    var nextEp = currentIndex + 1 < episodes.length ? episodes[currentIndex + 1] : null;
    var canonicalShareUrl =
      ep.canonical_url || ((data.archiveBaseUrl || "https://slopwow.github.io").replace(/\/+$/, "") + "/episodes/" + ep.episode_id + ".html");

    // Update DOM dynamically when ?id= differs from default SSR episode
    document.title = "EP." + ep.episode_number + " " + ep.title + " — 와우 포에버 슬롭툰";
    var badgeEl = document.getElementById("epBadge");
    if (badgeEl) badgeEl.textContent = "EP." + ep.episode_number + " · #" + ep.source_post_no;
    var dateEl = document.getElementById("epDate");
    if (dateEl) dateEl.textContent = ep.date_short || "";
    var cutsEl = document.getElementById("epCuts");
    if (cutsEl) cutsEl.textContent = ep.cut_count + "컷 상황극";
    var titleEl = document.getElementById("epTitle");
    if (titleEl) titleEl.textContent = ep.title;
    var subEl = document.getElementById("epSub");
    if (subEl) subEl.textContent = ep.subtitle;

    var sourceEl = document.getElementById("epSourceLink");
    if (sourceEl) {
      sourceEl.href = ep.source_url;
      sourceEl.textContent =
        "원본 디시 WOW 포에버 마이너 갤러리 개념글 (#" + ep.source_post_no + ") 바로가기 ↗";
    }
    var bottomSourceEl = document.getElementById("epBottomSourceLink");
    if (bottomSourceEl) {
      bottomSourceEl.href = ep.source_url;
    }

    var castRow = document.getElementById("epCastRow");
    if (castRow && Array.isArray(ep.cast_chips)) {
      castRow.innerHTML = "";
      ep.cast_chips.forEach(function (chip) {
        var a = document.createElement("a");
        a.className = "cast-chip";
        a.href = rootPrefix + "cast.html#" + encodeURIComponent(chip.id || "");
        var dot = document.createElement("span");
        dot.className = "cast-dot";
        dot.style.background = chip.color || "#111111";
        a.appendChild(dot);
        a.appendChild(document.createTextNode(chip.name));
        castRow.appendChild(a);
      });
    }

    var fullImg = document.getElementById("epFullImg");
    var fullSrc = rootPrefix + ep.full_image;
    if (fullImg) {
      fullImg.src = fullSrc;
      fullImg.alt = "와우 포에버 슬롭툰 EP." + ep.episode_number + " " + ep.title + " 통합본";
    }

    var pagesView = document.getElementById("readerPagesView");
    if (pagesView && Array.isArray(ep.page_images)) {
      pagesView.innerHTML = "";
      ep.page_images.forEach(function (rel, idx) {
        var img = document.createElement("img");
        img.src = rootPrefix + rel;
        img.alt = "EP." + ep.episode_number + " 페이지 " + (idx + 1);
        img.className = "reader-page-img";
        img.loading = "lazy";
        pagesView.appendChild(img);
      });
    }

    var titlePreview = document.getElementById("dcTitlePreview");
    if (titlePreview) titlePreview.textContent = ep.dc_title;
    var bodyPreview = document.getElementById("dcBodyPreview");
    if (bodyPreview) bodyPreview.textContent = ep.dc_body;

    var dlBtn = document.getElementById("dcDownloadBtn");
    var dlFileName = "wow_sloptoon_" + ep.episode_id + "_full.jpg";
    if (dlBtn) {
      dlBtn.href = fullSrc;
      dlBtn.setAttribute("download", dlFileName);
    }

    // Wire Share URL ("링크 복사") buttons
    document.querySelectorAll(".js-share-url").forEach(function (btn) {
      btn.setAttribute("data-share-url", canonicalShareUrl);
      btn.addEventListener("click", function () {
        var origText = btn.textContent;
        copyText(canonicalShareUrl).then(function () {
          showToast("링크가 복사되었습니다! " + canonicalShareUrl);
          btn.textContent = "✓ 링크 복사됨";
          clearTimeout(btn._copyTimer);
          btn._copyTimer = setTimeout(function () {
            btn.textContent = origText;
          }, 1800);
        });
      });
    });

    // Update sleek Prev / Next binge cards
    var pager = document.getElementById("epPager");
    if (pager) {
      pager.innerHTML = "";
      pager.appendChild(buildBingeCardEl(prevEp, false, rootPrefix));
      pager.appendChild(buildBingeCardEl(nextEp, true, rootPrefix));
    }

    // Update "다른 레전드 념글 만화" recommended episode grid (up to 3)
    var recSection = document.getElementById("epRecommendSection");
    var recGrid = document.getElementById("epRecommendGrid");
    if (recSection && recGrid) {
      var recs = selectRecommended(episodes, currentIndex, 3);
      recGrid.innerHTML = "";
      if (recs.length > 0) {
        recs.forEach(function (rec) {
          recGrid.appendChild(buildRecommendCardEl(rec, rootPrefix));
        });
        recSection.hidden = false;
      } else {
        recSection.hidden = true;
      }
    }

    // View mode switch (full vertical scroll vs page-by-page)
    var fullView = document.getElementById("readerFullView");
    document.querySelectorAll(".mode-btn[data-mode]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var mode = btn.getAttribute("data-mode");
        document.querySelectorAll(".mode-btn[data-mode]").forEach(function (b) {
          b.classList.toggle("is-active", b === btn);
        });
        if (fullView) fullView.hidden = mode !== "full";
        if (pagesView) pagesView.hidden = mode !== "pages";
      });
    });

    // Wire quick episode jump dropdown
    var jumpSelect = document.getElementById("epJumpSelect");
    if (jumpSelect) {
      jumpSelect.value = ep.episode_id;
      jumpSelect.addEventListener("change", function () {
        if (jumpSelect.value && jumpSelect.value !== ep.episode_id) {
          window.location.href = episodeHref(rootPrefix, jumpSelect.value);
        }
      });
    }

    // Keyboard prev/next navigation
    document.addEventListener("keydown", function (ev) {
      if (ev.target && /INPUT|TEXTAREA|SELECT/.test(ev.target.tagName)) return;
      if (ev.key === "ArrowLeft" && prevEp) {
        window.location.href = episodeHref(rootPrefix, prevEp.episode_id);
      } else if (ev.key === "ArrowRight" && nextEp) {
        window.location.href = episodeHref(rootPrefix, nextEp.episode_id);
      }
    });
  }

  /* ---------------- GLOBAL BACK TO TOP ---------------- */
  function initBackToTop() {
    var btn = document.getElementById("backToTopBtn");
    if (!btn) return;
    function toggleBtn() {
      btn.hidden = window.scrollY < 420;
    }
    window.addEventListener("scroll", toggleBtn, { passive: true });
    btn.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
    toggleBtn();
  }

  /* ---------------- CAST PAGE (SHEET SWITCH + LIGHTBOX) ---------------- */
  function initCastPage() {
    var sheetImg = document.getElementById("castSheetImg");
    var lightbox = document.getElementById("lightbox");
    var lightboxImg = document.getElementById("lightboxImg");
    var lightboxClose = document.getElementById("lightboxClose");

    document.querySelectorAll(".mode-btn[data-sheet]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var src = btn.getAttribute("data-sheet");
        if (sheetImg && src) sheetImg.src = src;
        document.querySelectorAll(".mode-btn[data-sheet]").forEach(function (b) {
          b.classList.toggle("is-active", b === btn);
        });
      });
    });

    if (sheetImg && lightbox && lightboxImg) {
      sheetImg.addEventListener("click", function () {
        lightboxImg.src = sheetImg.src;
        lightbox.hidden = false;
      });
      var closeLightbox = function () {
        lightbox.hidden = true;
      };
      if (lightboxClose) lightboxClose.addEventListener("click", closeLightbox);
      lightbox.addEventListener("click", function (ev) {
        if (ev.target === lightbox) closeLightbox();
      });
      document.addEventListener("keydown", function (ev) {
        if (ev.key === "Escape" && !lightbox.hidden) closeLightbox();
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    var page = document.body.getAttribute("data-page");
    if (page === "home") initHomePage();
    if (page === "episode") initEpisodePage();
    if (page === "cast") initCastPage();
    initRandomButtons();
    initBackToTop();
  });
})();
