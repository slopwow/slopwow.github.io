# 와우 포에버 슬롭툰 (`wow-forever-sloptoon`)

> **디시인사이드 WOW 포에버 마이너 갤러리** 개념글을 **공식 시안 C 귀염뽀짝 9종족×9직업 미소녀 4~6컷 순수 상황극 웹툰**으로 자동 생성하고, 순백색(`#FFFFFF`) 초고속 정적 웹 아카이브로 연재하는 올인원 파이프라인입니다.

- **초기 수록 에피소드 (바로 감상 가능)**:
  - **EP.1** `흑마법사가 물을 어케 줌? (#92059)` — 5컷 순수 상황극
  - **EP.2** `방금 만난 기사님의 명언 (#96849)` — 6컷 순수 상황극
- **AI 엔진 (`google-genai >= 3.2.0` Interactions API)**:
  - 대본·콘티 생성: `gemini-4-hydrogen`
  - 시안 C 원화 생성: `gemini-nano-banana-2.1` (옵션: `gemini-3-pro-image`, `gemini-3.1-flash-lite-image`)

---

## 1. 빠른 시작 (활성 워크스페이스 권장)

Antigravity 또는 IDE에서 아래 프로젝트 폴더를 **활성 워크스페이스(Active Workspace)**로 열어 작업하시는 것을 권장합니다.

```text
C:\Users\kbu39\.gemini\antigravity\scratch\wow-forever-sloptoon
```

### 설치 및 로컬 웹 아카이브 즉시 실행

```powershell
# 1) 프로젝트 폴더로 이동
cd C:\Users\kbu39\.gemini\antigravity\scratch\wow-forever-sloptoon

# 2) 개발 모드 패키지 설치
pip install -e ".[dev]"

# 3) 정적 웹 아카이브 빌드 & 로컬 서버 실행 (EP.1, EP.2 바로 감상!)
sloptoon build-site
sloptoon serve --port 8765
```

브라우저에서 `http://127.0.0.1:8765/`를 열면 **EP.1·EP.2 웹툰 뷰어**, **캐릭터 검색·필터**, **시안 C 9×9 캐스트 도감**을 바로 확인할 수 있습니다.

---

## 2. `GEMINI_API_KEY` 발급 및 설정

새 개념글을 자동으로 웹툰화하려면 Google AI Studio에서 API 키를 발급받아 `.env` 파일에 설정하세요.

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
# 선택: 공개 배포 후 웹 아카이브 주소 입력 (디시 업로드 본문에 자동 링크 삽입)
SLOPTOON_ARCHIVE_BASE_URL=https://<github-username>.github.io/<repo-name>
```

> **보안 안내**: `.env` 파일은 `.gitignore`에 등록되어 있어 Git에 커밋되지 않습니다. GitHub 자동 연재에는 Repository Secrets를 사용하세요.

---

## 3. CLI 명령어 가이드 (`sloptoon`)

| 명령어 | 설명 |
| :--- | :--- |
| `sloptoon scout` | 디시 WOW 포에버 마이너 갤러리 개념글 중 아직 제작하지 않은 후보 글 탐색·랭킹 |
| `sloptoon generate --post-no 92059 --dry-run` | API 호출 없이 콘티 JSON 생성 파이프라인만 미리 테스트 |
| `sloptoon generate --post-no <글번호>` | 특정 포에버갤 개념글 번호로 4~6컷 상황극 1화 생성 + 아카이브 재빌드 |
| `sloptoon generate --auto` | 최상위 미제작 개념글 자동 선택 후 1화 생성 |
| `sloptoon generate --auto --image-model gemini-3-pro-image` | 이미지 모델을 지정해 생성 (`gemini-nano-banana-2.1` / `gemini-3-pro-image` / `gemini-3.1-flash-lite-image`) |
| `sloptoon run-once` | 개념글 정찰 → 대본 → 원화 → 식자·합성 → 웹 아카이브 재빌드까지 1회 완주 |
| `sloptoon build-site` | `data/episodes.json` 기준으로 `site/` 정적 웹 아카이브 빌드 |
| `sloptoon serve --port 8765` | `site/` 정적 아카이브를 로컬 HTTP 서버로 즉시 열기 |
| `sloptoon pack-dc ep001 --open-browser` | 디시 포에버갤 업로드 패키지(`upload_pack/ep001/`) 생성 + 공식 글쓰기 페이지 열기 |

---

## 4. 무료 배포 가이드 (GitHub Pages / Vercel / Cloudflare Pages)

`site/` 폴더는 순수 HTML·CSS·JS·JPG 정적 파일로만 구성되어 어디서나 0원·초고속으로 호스팅할 수 있습니다.

### A. GitHub Pages + 6시간 자동 연재 (추천)

`.github/workflows/auto-sloptoon.yml`이 이미 구성되어 있습니다.

1. 이 프로젝트 폴더를 GitHub 저장소(`main` 브랜치)에 푸시합니다.
2. GitHub 저장소 **Settings → Pages → Build and deployment → Source**를 **GitHub Actions**로 변경합니다.
3. **Settings → Secrets and variables → Actions → Repository secrets**에 `GEMINI_API_KEY`를 추가합니다.
   - *(선택)* **Variables** 탭에 `SLOPTOON_ARCHIVE_BASE_URL`을 등록하면 업로드 본문에 아카이브 링크가 자동 포함됩니다.
4. 이후 **매 6시간(`15 */6 * * *`)**마다 자동으로 새 개념글 1화를 생성해 `data/`·`site/`를 커밋하고 GitHub Pages에 배포합니다.
5. **Actions → Auto Sloptoon & Deploy Pages → Run workflow** 버튼으로 언제든 수동 실행할 수 있습니다.

### B. Vercel / Cloudflare Pages

- **Output Directory / Build output directory**: `site`
- **Build Command**: *(비워두거나 `pip install -e . && sloptoon build-site`)*
- 정적 파일만 배포하므로 추가 서버 설정 없이 즉시 열립니다.

---

## 5. 디시 포에버갤 1클릭 업로드 도우미 사용법

본 프로젝트는 디시인사이드 정책을 준수하며, **CAPTCHA 우회나 무단 자동 글쓰기를 일절 수행하지 않습니다.** 대신 클릭 한 번으로 수동 업로드를 10초 만에 끝낼 수 있는 도우미를 제공합니다.

### 방법 1 — 웹 아카이브 화면에서 1클릭
1. `episode.html?id=ep001` 등 원하는 화를 열고 하단의 **디시 포에버갤 업로드 도우미** 카드로 이동합니다.
2. **「디시 포에버갤 업로드 도우미 실행 (복사 + 저장 + 글쓰기 열기)」** 버튼을 클릭합니다.
   - `[만화] 와우 포에버 슬롭툰 EP.N — 제목` + 본문·원본 개념글 출처가 클립보드에 자동 복사됩니다.
   - `wow_sloptoon_ep001_full.jpg` 파일이 PC로 다운로드됩니다.
   - 공식 디시 WOW 포에버 마이너 갤러리 글쓰기창이 새 탭으로 열립니다.
3. 열린 공식 페이지에서 직접 로그인·붙여넣기·이미지 첨부·캡차 입력 후 등록 버튼을 누르면 완료!

### 방법 2 — 터미널 CLI로 업로드 패키지 생성
```powershell
sloptoon pack-dc ep001 --copy-title --open-browser
```
- `upload_pack/ep001/` 폴더에 4.5MB 이하로 최적화(또는 안전 분할)된 JPG 파일, `post_title.txt`, `post_body.txt`, `upload_guide.txt`가 생성되고 공식 글쓰기 페이지가 브라우저로 열립니다.

---

## 6. 프로젝트 구조

```text
wow-forever-sloptoon/
├── assets/                     # 공식 시안 C 캐스트 시트 & 화풍 레퍼런스
├── data/
│   ├── episodes.json           # 에피소드 메타데이터 인덱스
│   └── episodes/ep001..ep002/  # 시드 에피소드 통합본·페이지·썸네일
├── site/                       # 빌드된 정적 순백(#FFFFFF) 웹 아카이브
│   ├── index.html              # 최신화 히어로 + 검색·캐릭터 필터 그리드
│   ├── episode.html            # 풀스크린 세로 웹툰 뷰어 + 1클릭 디시 업로드 도우미
│   ├── cast.html               # 시안 C 9종족×9직업 귀염뽀짝 미소녀 도감
│   └── episodes/               # 에피소드별 정적 HTML 페이지
├── src/wow_sloptoon/           # 핵심 파이프라인 (scout/writer/artist/composer/dc_packager/site_builder/cli)
├── tests/                      # pytest 단위·통합 테스트
└── .github/workflows/
    └── auto-sloptoon.yml       # 6시간 자동 연재 + GitHub Pages 배포 CI/CD
```

## 7. 테스트 실행

```powershell
pytest -v
```
