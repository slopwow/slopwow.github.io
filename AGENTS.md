# 와우 포에버 슬롭툰 (`sloptoon`) 프로젝트 전용 컨텍스트 및 규칙

본 문서는 Antigravity 프로젝트 `sloptoon` (`C:\Users\kbu39\Desktop\antigravity\sloptoon`)에서 새 대화를 시작할 때 이전 작업 맥락을 100퍼센트 복원하기 위한 프로젝트 전용 규칙 파일입니다.

---

## 1. 핵심 운영 규칙 (절대 준수)

1. **외장 Chrome MCP 최우선 사용** – 모든 브라우저 확인·조작·업로드 작업은 내장 브라우저(`browser` 서브에이전트)가 아니라 **외장 Chrome MCP(`chrome-devtools`, `chrome-devtools-mcp@latest --autoConnect`)**를 사용합니다.
2. **디시 포에버갤 전용 브랜딩 및 소재·익명성 규칙** – 오직 디시인사이드 **WOW 포에버 마이너 갤러리(`wowforever`)** 개념글만 다루며, 와우 인벤은 일절 언급하지 않습니다. **자극적이고 공감이 큰 실제 인게임 사건·사고(닌자, 먹튀, 입찰 분쟁, 억까, 파티 참사 등) 위주로만 선정**하며, 지루한 일반론·진영 비교글 및 **`🎬RP` 말머리·장문 RP 연재/편지 글은 웹툰화를 영구 금지**합니다(`scout.py` 자동 필터 적용). **명예훼손·고소 방지를 위해 사고 친 당사자의 실제 아이디·닉네임·길드명은 대본·말풍선·본문·크롭 이미지 어디에도 절대 적지 않으며**, 오직 직업 호칭(`도적`, `징기`, `보기`, `흑마`, `사제` 등)으로만 100퍼센트 익명 처리합니다. 신규 웹툰화 전에는 후보를 먼저 병욱님께 추려 보여드리고 허락받은 편만 제작합니다.
3. **디시 등록 제목 및 원본 제목 100% 일치 규칙** – 웹툰 제목(`script.source_title`, `EpisodeRecord.title`)은 반드시 **원본 개념글 제목 토씨 하나 바꾸지 않은 원문 그대로** 사용하며, 디시 등록 제목은 **`[와포슬롭툰]{원본념글제목}`**으로 고정합니다 (`EP.{N} — ` 및 `[만화]` 표기 금지).
4. **디시 계정 및 업로드 규칙** – 외장 Chrome에 고정닉 **`와포슬롭툰`** 계정이 로그인되어 있습니다 (`mcp_config.json`에 `--workspace C:\Users\kbu39\Desktop\antigravity\sloptoon` 등록 완료; 기존 실행 세션에서 경로 제한이 뜨면 `$env:TEMP`에 임시 스테이징 후 `upload_file` 수행 뒤 즉시 삭제). `이미지 업로드 하기` 팝업 업로드 → `적용` → 본문 최상단 이미지 보존(`img[data-tempno]` 유지) 및 하단 정주행 링크 입력 → `등록`(`#alarm` 실시간 댓글 토스트 가림 방지를 위해 `evaluate_script` `(el) => el.click()` 사용) → `mark-published`까지 수행합니다. 단, 캡차(자동등록방지)가 뜨면 절대 우회·자동 풀이하지 않고 즉시 멈춰 병욱님께 인계합니다.
5. **하단 주소 유인 워터마크 필수** – 모든 에피소드 통합본(`episode_full.jpg`) 최하단에는 `slopwow.github.io` 유인 배너(900×132 순백 카드)를 반드시 포함합니다 (`episode_full_raw.jpg` 원본 별도 보관, 중복 찍힘 방지).
6. **Gemini API 2026 표준** – `google-genai >= 3.2.0` Interactions API만 사용합니다 (`gemini-4-hydrogen` 대본, `gemini-nano-banana-2.1` 기본 작화 / 옵션 `gemini-3-pro-image`, `gemini-3.1-flash-lite-image`). 구형 `google-generativeai` 및 `gemini-2.5-*` 절대 금지.

---

## 2. 확정 비주얼 및 편집 바이블 (시안 C)

- **공식 캐스트 시트**: `assets/cast_sheet_c.jpg` (클린), `assets/cast_sheet_c_labeled.png` (라벨본) — **시안 C 초귀염 팝·개그 미소녀 9종족×9직업 (몬스터 가죽·해골 후드 코스튬)**.
- **공식 화풍 레퍼런스**: `assets/sloptoon_style_ref.jpg` — 100퍼센트 순백색(`#FFFFFF`) 무경계 배경, 얇은 웹툰 셀 채색, 1컷당 1–2명 집중 구도.
- **스토리 포맷**: **4–6컷 100퍼센트 인게임 라이브 상황극** (억지 갤러리 메타 댓글 컷 금지), 필수 **무언 충격 정지 클로즈업 1컷(`wordless=True`)**, 4배 슈퍼샘플링 타원 말풍선(`overlap_px == 0`).
- **실제 와우 아이템 툴팁 오버레이 (`src/wow_sloptoon/item_tooltip.py`)**: 특정 와우 아이템이 등장하는 컷에는 `ComicCut.item_tooltip`(`ItemTooltipSpec`: 원본 툴팁 스샷 `assets/items/*.png` 또는 한국어 클래식 와우헤드 `wowhead_item_id` 조회)을 통해 다크 네이비 와우 툴팁 카드를 무겹침(`tooltip_overlap_px == 0`)으로 합성합니다 (유저 닉네임 절대 제외).

---

## 3. 인프라 및 배포 현황

- **로컬 정규 경로**: `C:\Users\kbu39\Desktop\antigravity\sloptoon`
- **GitHub 원격 저장소**: `https://github.com/slopwow/slopwow.github.io` (`main`: 전체 코드, `gh-pages`: 정적 사이트 배포)
- **실서버 라이브 URL**: `https://slopwow.github.io/`
  - 9×9 캐스트 도감: `https://slopwow.github.io/cast.html`
  - **방문자 사이트 클린 원칙**: 퍼블릭 웹(`site/`)에는 `publish.html`, `디시 업로드 도우미`, `gall.dcinside.com/mgallery/board/write` 글쓰기 링크 등 운영자 전용 업로드 UI를 일절 노출하지 않음.
- **원클릭 재배포**: `powershell -ExecutionPolicy Bypass -File .\deploy-pages.ps1`
- **6시간 자동 양산 봇 (권장 주력)**: `C:\Users\kbu39\.gemini\config\sidecars\wow-sloptoon-factory\sidecar.json` (`WOW 포에버 슬롭툰 6시간 자동 양산 봇`, `CRON_TZ=Asia/Seoul 0 */6 * * *`) + 운영 도우미 `run-factory.ps1` + 가이드 `AUTOMATION.md` (보조: `setup-automation.ps1` Windows 작업 스케줄러 `WowForeverSloptoonAuto`)
- **Python 실행 명령**: `python -m wow_sloptoon.cli <명령>` / `python -m pytest -v`

---

## 4. 완료 에피소드 현황

- **EP.1 (`ep001`)**: 흑마법사가 물을 어케 줌? (`#92059`, 5컷, 워터마크 적용 · 디시 게시 완료 `#107655`)
- **EP.2 (`ep002`)**: 방금 만난 기사님의 명언 (`#96849`, 6컷, 워터마크 적용 · 디시 게시 완료 `#107679`)
- **EP.3 (`ep003`)**: 놈리건 천장 압사 사건 (`#89934`, 6컷, 워터마크 적용 · 디시 게시 완료 `#107689`)
- **EP.4 (`ep004`)**: 침낭퀘 1시간 반 돌라나르 대참사 (`#105596`, 6컷, 워터마크 적용 · 디시 게시 완료 `#107701`)
- **EP.5 (`ep005`)**: 방금 길드에서 레전드 사건 일어남 (`#94979`, 6컷, `삼위일체의 아뮬렛` 툴팁 · 워터마크 적용 · 디시 게시 완료 `#107782`)
- **EP.6 (`ep006`)**: 와뉴비 다들 왜 사제 안키우는 지 알거같다 (`#78596`, 6컷, `화이트메인의 모자` & `사서의 홀` 툴팁 · 워터마크 적용 · 디시 게시 완료 `#107796`)
- **EP.7 (`ep007`)**: 장트라제 처먹고 파탈한 도둑놈ㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋ (`#105798`, 6컷, `보호의 장트라제` & `질풍의 술트라제` 툴팁 · 워터마크 적용 · 디시 업로드 대기)
- **EP.8 (`ep008`)**: 실시간 던전 파티.... 분노의 흑마 ㅋㅋㅋㅋㅋㅋ (`#68582`, 6컷, `모드레쉬의 이글거리는 눈` 툴팁 · 워터마크 적용 · 디시 업로드 대기)
- **영구 금지 소재**: `🎬RP` 말머리 및 장문 RP 연재/편지 글(예: `#80851` 삭제 처리)은 웹툰화 및 업로드 영구 금지.

---

## 5. 이전 전체 대화 기록 복원 포인터

- **원본 대화 ID**: `a2fc44ce-b491-4e60-b88a-5485ade2be86`
- **원본 전체 로그**: `C:\Users\kbu39\.gemini\antigravity\brain\a2fc44ce-b491-4e60-b88a-5485ade2be86\.system_generated\logs\transcript.jsonl`
- **초기 스토리 후보 문서**: `C:\Users\kbu39\.gemini\antigravity\brain\a2fc44ce-b491-4e60-b88a-5485ade2be86\wow_sloptoon_story_candidates.md`
- 세부 의사결정·과거 프롬프트 이력이 필요하면 위 `transcript.jsonl`을 먼저 조회해 맥락을 복구합니다.
