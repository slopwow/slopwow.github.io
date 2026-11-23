# AGENTS.md — 와우 포에버 슬롭툰 (`sloptoon`)

> **운영 모드**: 디시인사이드 업로드는 영구 중단(미게시) 상태이며, 자체 정적 웹 아카이브([slopwow.github.io](https://slopwow.github.io/)) 전용으로 제작·배포합니다.

## 1. 콘텐츠·익명성·제목 규칙 (절대 준수)
- **포에버갤 전용·소재 기준** – 디시인사이드 WOW 포에버 마이너 갤러리(`wowforever`) **2026-11 정식 출시 이후** 실제 인게임 사건·사고(닌자, 먹튀, 입찰 분쟁, 억까, 파티 참사 등) 개념글만 다룹니다. 와우 인벤은 일절 언급하지 않습니다.
- **영구 금지 소재** – 베타 시절(2026-10 이전) 게시글, `🎬RP` 말머리 및 장문 RP 연재/편지 글, 제목에 특정 닉네임·길드명이 직접 박힌 저격글, 일반론·진영 비교글은 웹툰화 영구 금지입니다(`scout.py` 자동 필터 + `audit_script_quality()` 적용).
- **100% 익명화** – 명예훼손·신상 노출 방지를 위해 당사자의 실제 아이디·닉네임·길드명은 대본·말풍선·본문·툴팁·크롭 이미지 어디에도 절대 적지 않으며, 오직 직업 호칭(`도적`, `징기`, `보기`, `흑마`, `사제` 등)으로만 표기합니다.
- **원본 제목 100% 일치** – `script.source_title` 및 `EpisodeRecord.title`은 원본 개념글 제목을 토씨 하나 바꾸지 않은 원문 그대로 사용합니다(`EP.{N} — ` 및 `[만화]` 임의 치환 금지).
- **디시 미게시·사이트 전용** – 모든 신규 제작분은 `slopwow.github.io` 정적 아카이브 전용으로 자동 빌드·배포합니다. 외부 커뮤니티 신규 게시는 명시적 사전 승인 없이는 금지하며 CAPTCHA는 절대 우회하지 않습니다.

## 2. 비주얼·편집 바이블 (시안 C)
- **캐스트·화풍 정본** – `assets/cast_sheet_c.jpg`(클린) · `assets/cast_sheet_c_labeled.png`(라벨본, 9종족×9직업 시안 C 2.5–3등신 통일·Clean Hand), `assets/sloptoon_style_ref.jpg`, `src/wow_sloptoon/wow_lore.py`(Classic+ 고증 바이블)를 따릅니다.
- **컷 구성** – 100% 순백색(`#FFFFFF`) 무경계 배경, 얇은 웹툰 셀 채색, 1컷당 1–2명 집중 구도, **4–6컷 100% 인게임 라이브 상황극**(갤러리 메타 댓글 컷 금지), 필수 **무언 충격 정지 클로즈업 1컷(`wordless=True`)**, 4배 슈퍼샘플링 타원 말풍선(`overlap_px == 0`).
- **와우 아이템 툴팁** – `src/wow_sloptoon/item_tooltip.py`(`ComicCut.item_tooltip`)로 다크 네이비 와우 툴팁 카드를 무겹침(`tooltip_overlap_px == 0`) 합성합니다(유저 닉네임 제외).
- **하단 주소 유인 워터마크** – 모든 통합본(`episode_full.jpg`) 최하단에 `slopwow.github.io` 900×132 순백 유인 배너를 필수 포함합니다(`episode_full_raw.jpg` 원본 별도 보관, 중복 찍힘 방지).

## 3. Gemini API 표준·명령·배포
- **Gemini API 표준** – `google-genai >= 3.2.0` Interactions API만 사용합니다(`gemini-4-hydrogen` 대본, `gemini-nano-banana-2.1` 기본 작화 / 옵션 `gemini-3-pro-image`, `gemini-3.1-flash-lite-image`). 구형 `google-generativeai` 및 `gemini-2.5-*` 금지.
- **공개 웹 클린 원칙** – 원격 배포는 `slopwow/slopwow.github.io`(`main`: 소스, `gh-pages`: 정적 사이트, 도감 `https://slopwow.github.io/cast.html`)입니다. `site/`에 `publish.html`, 업로드 도우미, 외부 글쓰기 링크, 관리/디버그 UI를 절대 노출하지 않습니다.
- **실행·검증·배포 명령**
  - 테스트: `python -m pytest -v`
  - 사이트 빌드: `python -m wow_sloptoon.cli build-site`
  - 파이프라인 CLI: `python -m wow_sloptoon.cli <scout|generate|build-site|watermark|queue|autopilot>`
  - 원클릭 배포: `powershell -ExecutionPolicy Bypass -File .\deploy-pages.ps1` (배치 실행: `.\run-factory.ps1`)

## 4. 크로스-AI 공통 응답·실물검증·안전선
- **응답 스타일** – 항상 자연스러운 한국어 존댓말로 답하고 **설명 → `### 결론` → `### 다음 확인 사항`(2개, 종결 시 생략 가능)** 구조를 유지합니다. 1단락 1–2문장, `**키워드** – 요약`, 3개 이상 비교는 표, URL·파일은 마크다운 링크를 사용합니다(한글 기울임꼴·취소선·과도한 느낌표 금지).
- **자율 완결 및 실물 검증** – 수동 작업으로 떠넘기지 않고 CLI·스크립트로 구현·테스트·배포·임시 산출물 정리까지 완결합니다. Exit Code 0만으로 완료 선언하지 않고 `pytest` 통과·실제 산출물 무겹침·실서버 HTTP 200 등 실물 검증 후 보고합니다.
- **보안·안전선** – API 키·토큰(`.env`의 `GEMINI_API_KEY` 등), 개인정보, 로컬 절대경로는 커밋·로그·응답에 절대 노출하지 않으며, 유료 과금·외부 게시 변경은 반드시 사전 확인합니다.
