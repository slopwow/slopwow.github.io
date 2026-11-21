/* 와우 포에버 슬롭툰 — 정적 웹 아카이브 인터랙션 */
(function () {
  "use strict";

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

  /* ---------------- HOME PAGE (SEARCH / FILTER / SORT) ---------------- */
  function initHomePage() {
    var grid = document.getElementById("episodeGrid");
    var searchInput = document.getElementById("searchInput");
    var filterBar = document.getElementById("castFilterBar");
    var sortToggle = document.getElementById("sortToggle");
    var resultCount = document.getElementById("resultCount");
    var emptyFilter = document.getElementById("emptyFilter");
    var resetBtn = document.getElementById("resetFiltersBtn");
    if (!grid) return;

    var cards = Array.prototype.slice.call(grid.querySelectorAll(".ep-card"));
    var activeCast = "";
    var sortOrder = "desc";

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

    function applyFilters() {
      var q = (searchInput ? searchInput.value : "").trim().toLowerCase();
      var visible = 0;

      cards.sort(function (a, b) {
        var na = parseInt(a.getAttribute("data-num") || "0", 10);
        var nb = parseInt(b.getAttribute("data-num") || "0", 10);
        return sortOrder === "desc" ? nb - na : na - nb;
      });
      cards.forEach(function (card) {
        grid.appendChild(card);
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
          post.indexOf(q.replace(/^#/, "")) !== -1 ||
          castStr.toLowerCase().indexOf(q) !== -1;

        var show = matchesCast && matchesQuery;
        card.hidden = !show;
        if (show) visible += 1;
      });

      if (resultCount) {
        resultCount.textContent = "총 " + visible + "개의 에피소드";
      }
      if (emptyFilter) {
        emptyFilter.hidden = visible > 0;
      }
    }

    if (searchInput) {
      searchInput.addEventListener("input", applyFilters);
    }
    if (filterBar) {
      filterBar.addEventListener("click", function (ev) {
        var btn = ev.target.closest(".filter-chip");
        if (!btn) return;
        activeCast = btn.getAttribute("data-cast") || "";
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
        applyFilters();
      });
    }
    if (resetBtn) {
      resetBtn.addEventListener("click", function () {
        activeCast = "";
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

  /* ---------------- EPISODE READER & 1-CLICK DC HELPER ---------------- */
  function initEpisodePage() {
    var data = window.__SLOPTOON_DATA__;
    if (!data || !Array.isArray(data.episodes) || data.episodes.length === 0) return;

    var episodes = data.episodes;
    var rootPrefix = data.rootPrefix || "";
    var dcWriteUrl = data.dcWriteUrl || "https://gall.dcinside.com/mgallery/board/write/?id=wowforever";

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
    var prevEp = currentIndex > 0 ? episodes[currentIndex - 1] : null;
    var nextEp = currentIndex + 1 < episodes.length ? episodes[currentIndex + 1] : null;

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

    // Update pager cards
    var pager = document.getElementById("epPager");
    if (pager) {
      pager.innerHTML = "";
      if (prevEp) {
        var prevA = document.createElement("a");
        prevA.className = "nav-ep-card";
        prevA.href = rootPrefix + "episode.html?id=" + encodeURIComponent(prevEp.episode_id);
        prevA.innerHTML =
          '<span class="nav-ep-dir">← 이전 화</span><strong class="nav-ep-title"></strong>';
        prevA.querySelector(".nav-ep-title").textContent =
          "EP." + prevEp.episode_number + " " + prevEp.title;
        pager.appendChild(prevA);
      } else {
        var prevD = document.createElement("div");
        prevD.className = "nav-ep-card is-disabled";
        prevD.innerHTML =
          '<span class="nav-ep-dir">← 이전 화</span><span class="nav-ep-title">첫 번째 에피소드입니다</span>';
        pager.appendChild(prevD);
      }

      if (nextEp) {
        var nextA = document.createElement("a");
        nextA.className = "nav-ep-card nav-ep-next";
        nextA.href = rootPrefix + "episode.html?id=" + encodeURIComponent(nextEp.episode_id);
        nextA.innerHTML =
          '<span class="nav-ep-dir">다음 화 →</span><strong class="nav-ep-title"></strong>';
        nextA.querySelector(".nav-ep-title").textContent =
          "EP." + nextEp.episode_number + " " + nextEp.title;
        pager.appendChild(nextA);
      } else {
        var nextD = document.createElement("div");
        nextD.className = "nav-ep-card nav-ep-next is-disabled";
        nextD.innerHTML =
          '<span class="nav-ep-dir">다음 화 →</span><span class="nav-ep-title">가장 최신 에피소드입니다</span>';
        pager.appendChild(nextD);
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

    // 1-Click DCInside Upload Helper (Clipboard + Image Download + Official Write Tab)
    var oneClickBtn = document.getElementById("dcOneClickBtn");
    if (oneClickBtn) {
      oneClickBtn.addEventListener("click", function () {
        var combined = ep.dc_title + "\n\n" + ep.dc_body;
        copyText(combined).then(function () {
          // Trigger JPG download
          var link = document.createElement("a");
          link.href = fullSrc;
          link.download = dlFileName;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);

          // Open official DCInside write page in new tab (user signs in & posts manually)
          window.open(dcWriteUrl, "_blank", "noopener,noreferrer");
          showToast("제목·본문 복사 완료 + JPG 저장 시작 + 포에버갤 글쓰기창을 열었습니다!");
        });
      });
    }

    var copyTitleBtn = document.getElementById("dcCopyTitleBtn");
    if (copyTitleBtn) {
      copyTitleBtn.addEventListener("click", function () {
        copyText(ep.dc_title).then(function () {
          showToast("글 제목을 클립보드에 복사했습니다!");
        });
      });
    }

    var copyBodyBtn = document.getElementById("dcCopyBodyBtn");
    if (copyBodyBtn) {
      copyBodyBtn.addEventListener("click", function () {
        copyText(ep.dc_body).then(function () {
          showToast("본문 및 원본 출처 링크를 클립보드에 복사했습니다!");
        });
      });
    }

    // Keyboard prev/next navigation
    document.addEventListener("keydown", function (ev) {
      if (ev.target && /INPUT|TEXTAREA/.test(ev.target.tagName)) return;
      if (ev.key === "ArrowLeft" && prevEp) {
        window.location.href = rootPrefix + "episode.html?id=" + encodeURIComponent(prevEp.episode_id);
      } else if (ev.key === "ArrowRight" && nextEp) {
        window.location.href = rootPrefix + "episode.html?id=" + encodeURIComponent(nextEp.episode_id);
      }
    });
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
  });
})();
