# 와우 포에버 슬롭툰 (`sloptoon`) 프로젝트 전용 컨텍스트 및 규칙

본 문서는 Antigravity 프로젝트 `sloptoon` (`C:\Users\kbu39\Desktop\antigravity\sloptoon`)에서 새 대화를 시작할 때 이전 작업 맥락을 100퍼센트 복원하기 위한 프로젝트 전용 규칙 파일입니다.

---

## 1. 핵심 운영 규칙 (절대 준수)

1. **외장 Chrome MCP 최우선 사용** – 모든 브라우저 확인·조작·업로드 작업은 내장 브라우저(`browser` 서브에이전트)가 아니라 **외장 Chrome MCP(`chrome-devtools`, `chrome-devtools-mcp@latest --autoConnect`)**를 사용합니다.
2. **디시 포에버갤 전용 브랜딩** – 오직 디시인사이드 **WOW 포에버 마이너 갤러리(`wowforever`)** 개념글만 다루며, 와우 인벤은 일절 언급하지 않습니다.
3. **디시 등록 제목 규칙** – 제목 접두사는 반드시 **`[와포슬롭툰]`**으로 고정합니다 (`[와포슬롭툰] EP.{N} — {제목}`). `[만화]` 표기 금지.
4. **디시 계정 및 업로드 규칙** – 외장 Chrome에 고정닉 **`와포슬롭툰`** 계정이 로그인되어 있습니다. 이 프로젝트 폴더가 활성 워크스페이스로 열려 있으므로 `chrome-devtools` MCP의 `upload_file`로 `upload_pack/<ep>/epXXX_full.jpg`를 `이미지 업로드 하기` 팝업에 직접 업로드 → `적용` → 본문 입력까지 수행합니다. 단, 캡차(자동등록방지)가 뜨면 절대 우회·자동 풀이하지 않고 즉시 멈춰 병욱님께 인계합니다.
5. **하단 주소 유인 워터마크 필수** – 모든 에피소드 통합본(`episode_full.jpg`) 최하단에는 `slopwow.github.io` 유인 배너(900×132 순백 카드)를 반드시 포함합니다 (`episode_full_raw.jpg` 원본 별도 보관, 중복 찍힘 방지).
6. **Gemini API 2026 표준** – `google-genai >= 3.2.0` Interactions API만 사용합니다 (`gemini-4-hydrogen` 대본, `gemini-nano-banana-2.1` 기본 작화 / 옵션 `gemini-3-pro-image`, `gemini-3.1-flash-lite-image`). 구형 `google-generativeai` 및 `gemini-2.5-*` 절대 금지.

---

## 2. 확정 비주얼 및 편집 바이블 (시안 C)

- **공식 캐스트 시트**: `assets/cast_sheet_c.jpg` (클린), `assets/cast_sheet_c_labeled.png` (라벨본) — **시안 C 초귀염 팝·개그 미소녀 9종족×9직업 (몬스터 가죽·해골 후드 코스튬)**.
- **공식 화풍 레퍼런스**: `assets/sloptoon_style_ref.jpg` — 100퍼센트 순백색(`#FFFFFF`) 무경계 배경, 얇은 웹툰 셀 채색, 1컷당 1–2명 집중 구도.
- **스토리 포맷**: **4–6컷 100퍼센트 인게임 라이브 상황극** (억지 갤러리 메타 댓글 컷 금지), 필수 **무언 충격 정지 클로즈업 1컷(`wordless=True`)**, 4배 슈퍼샘플링 타원 말풍선(`overlap_px == 0`).

---

## 3. 인프라 및 배포 현황

- **로컬 정규 경로**: `C:\Users\kbu39\Desktop\antigravity\sloptoon`
- **GitHub 원격 저장소**: `https://github.com/slopwow/slopwow.github.io` (`main`: 전체 코드, `gh-pages`: 정적 사이트 배포)
- **실서버 라이브 URL**: `https://slopwow.github.io/`
  - 관리자 업로드 큐: `https://slopwow.github.io/publish.html`
  - 9×9 캐스트 도감: `https://slopwow.github.io/cast.html`
- **원클릭 재배포**: `powershell -ExecutionPolicy Bypass -File .\deploy-pages.ps1`
- **6시간 자동 스케줄러**: `setup-automation.ps1` (Windows 작업 스케줄러 `WowForeverSloptoonAuto`)
- **Python 실행 명령**: `python -m wow_sloptoon.cli <명령>` / `python -m pytest -v`

---

## 4. 완료 에피소드 및 다음 후보

- **EP.1 (`ep001`)**: 흑마법사가 물을 어케 줌? (`#92059`, 5컷, 워터마크 적용 완료)
- **EP.2 (`ep002`)**: 방금 만난 기사님의 명언 (`#96849`, 6컷, 워터마크 적용 완료)
- **EP.3 (`ep003`)**: 놈리건 천장 압사 사건 (`#89934`, 6컷, 워터마크 적용 완료)
- **EP.4 (`ep004`)**: 침낭퀘 1시간 반 돌라나르 대참사 (`#105596`, 6컷, 워터마크 적용 완료)
- **대기 중 레전드 후보**: `#94979` 방금 길드에서 레전드 사건 일어남 (마스터 루터 사건, 조회 8,816 · 추천 94)

---

## 5. 이전 전체 대화 기록 복원 포인터

- **원본 대화 ID**: `a2fc44ce-b491-4e60-b88a-5485ade2be86`
- **원본 전체 로그**: `C:\Users\kbu39\.gemini\antigravity\brain\a2fc44ce-b491-4e60-b88a-5485ade2be86\.system_generated\logs\transcript.jsonl`
- **초기 스토리 후보 문서**: `C:\Users\kbu39\.gemini\antigravity\brain\a2fc44ce-b491-4e60-b88a-5485ade2be86\wow_sloptoon_story_candidates.md`
- 세부 의사결정·과거 프롬프트 이력이 필요하면 위 `transcript.jsonl`을 먼저 조회해 맥락을 복구합니다.
