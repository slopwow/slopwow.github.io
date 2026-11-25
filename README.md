# 와우 포에버 슬롭툰 (`wow-forever-sloptoon`)

> 디시인사이드 **WOW 포에버 마이너 갤러리(`wowforever`, 2026-11 정식 출시 이후)** 실제 인게임 사건·사고 개념글을 **2~2.5등신 동글동글 말랑 귀염뽀짝 SD 4~7컷(권장 5~6컷) 완결 개그 웹툰**으로 제작하고, 순백색(`#FFFFFF`) 초고속 정적 웹 아카이브([slopwow.github.io](https://slopwow.github.io/)) 전용으로 연재하는 파이프라인입니다.

> **운영 정책**: 디시인사이드 업로드는 영구 중단(자동 게시 금지·외부 글쓰기 링크 없음) 상태이며, 본 프로젝트는 정적 웹 아카이브([slopwow.github.io](https://slopwow.github.io/)) 전용으로 제작·배포합니다.

- **단일 비주얼 정본 (노선 A — 2~2.5등신 귀염뽀짝 SD)**:
  - 화풍 마스터: `assets/diorama_style_ref.jpg` (얇은 펜선, 2단 셀 채색, 순백 `#FFFFFF` 여백 감성)
  - 고정 9인 캐스트: `assets/turnarounds/<cast_id>.jpg` (2.5등신 3면 턴어라운드 정본)
  - 고정 동행 펫 2종: `드워프 사냥꾼` 동행 **아기 곰**(`assets/turnarounds/hunter_bear.jpg`), `인간 흑마법사` 동행 **공허방랑자**(`assets/turnarounds/warlock_voidwalker.jpg`)
  - 모든 몹·보스·NPC·엑스트라까지 동일한 2~2.5등신 SD 화풍으로 통일합니다.
- **서사·대사 원칙**:
  - 원글을 읽지 않아도 100% 이해되는 **4~7컷(권장 5~6컷)** 완결 구성 + **무언 대왕 클로즈업 정지 컷 최소 1컷**
  - **말풍선당 1~2줄(16~30자) 찰진 와우 구어체**, 100% 익명화(직업 호칭만 사용), 원본 개념글 제목 100% 원문 일치
  - 4배 슈퍼샘플링 타원 말풍선(`overlap_px == 0`), 실제 와우 아이템 툴팁(`tooltip_overlap_px == 0`), 하단 `slopwow.github.io` 900×132 순백 유인 배너
- **AI 엔진 (`google-genai >= 3.2.0` Interactions API)**:
  - 대본·콘티 생성: `gemini-4-hydrogen`
  - SD 원화 생성: `gemini-nano-banana-2.1` (옵션: `gemini-3-pro-image`, `gemini-3.1-flash-lite-image`)

---

## 1. 빠른 시작

```powershell
# 1) 프로젝트 폴더로 이동
cd <REPO_ROOT>

# 2) 개발 모드 패키지 설치
pip install -e ".[dev]"

# 3) 정적 웹 아카이브 빌드 & 로컬 미리보기
python -m wow_sloptoon.cli build-site
python -m http.server 8765 --directory site
```

브라우저에서 `http://127.0.0.1:8765/`를 열면 **최신 에피소드 웹툰 뷰어**, **검색·캐릭터 필터**, **2.5등신 SD 9인 캐스트 & 파트너 도감**을 바로 확인할 수 있습니다.

---

## 2. `GEMINI_API_KEY` 발급 및 설정

새 개념글을 웹툰화하려면 Google AI Studio에서 API 키를 발급받아 `.env` 파일에 설정하세요.

1. [Google AI Studio](https://aistudio.google.com/apikey) 접속 → **Create API key** 클릭 후 키 복사
2. 프로젝트 루트에서 `.env.example`을 복사해 `.env` 생성:

```powershell
Copy-Item .env.example .env
```

3. `.env` 파일에 키 입력:

```env
GEMINI_API_KEY=여기에_발급받은_API_키_입력
SLOPTOON_TEXT_MODEL=gemini-4-hydrogen
SLOPTOON_IMAGE_MODEL=gemini-nano-banana-2.1
SLOPTOON_GALLERY_ID=wowforever
SLOPTOON_ARCHIVE_BASE_URL=https://slopwow.github.io
```

> **보안 안내**: `.env` 파일은 `.gitignore`에 등록되어 있어 Git에 커밋되지 않습니다. GitHub Actions 자동 연재에는 Repository Secrets를 사용하세요.

---

## 3. CLI 명령어 가이드 (`python -m wow_sloptoon.cli`)

| 명령어 | 설명 |
| :--- | :--- |
| `python -m wow_sloptoon.cli scout` | 포에버갤(`wowforever`) 2026-11 정식 출시 이후 미제작 개념글 후보 탐색·랭킹 |
| `python -m wow_sloptoon.cli generate --post-no <글번호> --dry-run` | API 호출 없이 콘티 JSON 생성 파이프라인만 미리 테스트 |
| `python -m wow_sloptoon.cli generate --post-no <글번호>` | 특정 포에버갤 개념글 번호로 4~7컷 SD 웹툰 1화 생성 + 아카이브 재빌드 |
| `python -m wow_sloptoon.cli generate --auto` | 최상위 미제작 개념글 자동 선택 후 1화 생성 (`audit_script_quality` 실게이트 포함) |
| `python -m wow_sloptoon.cli compose <ep_id>` | 기존 `script.json` + `raw_cuts`만 재조판(말풍선·아이템 툴팁 무겹침 `0px` + 워터마크) |
| `python -m wow_sloptoon.cli build-site` | `data/episodes.json` 기준으로 `site/` 순백(`#FFFFFF`) 정적 웹 아카이브 빌드(고아 파일 자동 청소) |
| `python -m wow_sloptoon.cli watermark` | 전체 에피소드 통합본(`episode_full.jpg`) 최하단 `slopwow.github.io` 유인 배너 일괄 적용 |
| `python -m wow_sloptoon.cli autopilot` | 정찰 → 생성 → 조판 → 정적 사이트 빌드 1회 완주 (`--dry-run` 프리뷰, `--deploy` 원클릭 배포) |

---

## 4. 정적 웹 아카이브 배포 가이드 (`slopwow.github.io`)

`site/` 폴더는 순수 HTML·CSS·JS·JPG/PNG 정적 파일로만 구성되어 외부 서버 없이 0원·초고속으로 호스팅할 수 있습니다.

### A. 로컬 원클릭 배포 (`deploy-pages.ps1` / `run-factory.ps1`)

```powershell
# 정적 사이트 빌드 + main & gh-pages (https://slopwow.github.io/) 원클릭 배포
powershell -ExecutionPolicy Bypass -File .\deploy-pages.ps1

# 운영 상태 점검 및 정찰·빌드·배포 도우미
powershell -ExecutionPolicy Bypass -File .\run-factory.ps1
```

### B. GitHub Actions 6시간 자동 연재 (`.github/workflows/auto-sloptoon.yml`)

1. GitHub 저장소 **Settings → Pages → Build and deployment → Source**를 **GitHub Actions** 또는 `gh-pages` 브랜치로 구성합니다.
2. **Settings → Secrets and variables → Actions → Repository secrets**에 `GEMINI_API_KEY`를 등록합니다.
3. **매 6시간(`15 */6 * * *`)**마다 `autopilot` + `build-site` + 공개 아카이브 보안·PII 0바이트 검증을 거쳐 `data/`·`site/`를 갱신하고 GitHub Pages에 자동 배포합니다.
4. **Actions → Auto Sloptoon & Deploy Pages → Run workflow** 버튼으로 언제든 수동 실행할 수 있습니다.

자세한 자동화 운영 방법은 [`AUTOMATION.md`](./AUTOMATION.md)를 참고하세요.

---

## 5. 프로젝트 구조

```text
wow-forever-sloptoon/
├── AGENTS.md                   # Cross-AI 단일 정본(SSOT) 지시서
├── AUTOMATION.md               # 6시간 정적 아카이브 자동 양산·배포 가이드
├── deploy-pages.ps1            # main & gh-pages 원클릭 배포 스크립트
├── run-factory.ps1             # 자동화 상태 점검·정찰·빌드·배포 운영 도우미
├── assets/
│   ├── diorama_style_ref.jpg   # 노선 A 2~2.5등신 SD 화풍 마스터
│   ├── cast_sheet_c.jpg        # 2.5등신 9인 캐스트 fallback 시트
│   ├── items/                  # 와우 아이템 툴팁 오버레이 에셋
│   └── turnarounds/            # 9인 2.5등신 3면 정본 + 고정 펫 2종(아기 곰·공허방랑자)
├── data/
│   ├── episodes.json           # 에피소드 메타데이터 정본 인덱스
│   └── episodes/ep001../       # 에피소드별 대본·페이지·통합본·썸네일·감사 리포트
├── site/                       # 빌드된 순백(#FFFFFF) 정적 웹 아카이브 (관리/업로드 UI 0개)
│   ├── index.html              # 최신화 히어로 + 검색·캐릭터 필터 그리드
│   ├── episode.html            # 풀스크린 세로 웹툰 뷰어
│   ├── cast.html               # 2.5등신 SD 9인 캐스트 & 파트너 도감
│   └── episodes/               # 에피소드별 정적 HTML 페이지
├── src/wow_sloptoon/           # 핵심 파이프라인 (config/models/cast/wow_lore/scout/writer/artist/item_tooltip/composer/site_builder/cli)
├── tests/                      # pytest 단위·통합·아카이브 무결성 테스트
└── .github/workflows/
    └── auto-sloptoon.yml       # 6시간 자동 연재 + PII 검증 + GitHub Pages 배포 CI/CD
```

---

## 6. 테스트 및 실물 검증

```powershell
python -m pytest -v
```

배포 전에는 테스트 통과와 함께 실제 렌더링 이미지의 **2~2.5등신 SD 화풍 일관성**, **말풍선·아이템 툴팁 무겹침(`0px`)**, **공개 아카이브 PII·절대경로 0바이트**, **라이브 URL(`https://slopwow.github.io/`) HTTP 200**을 직접 확인합니다.
