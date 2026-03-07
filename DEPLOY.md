# Vercel + GitHub 배포 가이드

## 1. Vercel로 배포하기

이 프로젝트는 **Vercel**에 올리면 그대로 배포할 수 있습니다.

### 전제 조건

- **GitHub**에 저장소가 있어야 합니다. (예: `whizsavvy/evergreen_church`)
- **EvergreenSlideMaker** 폴더가 저장소 루트에 포함되어 있어야 합니다.  
  (`EvergreenSlideMaker/setting.py`, `EvergreenSlideMaker/bible/`, `EvergreenSlideMaker/Hymn/`, `EvergreenSlideMaker/image/` 등)

### 배포 절차

1. [Vercel](https://vercel.com)에 로그인 후 **Add New Project** 선택.
2. **Import Git Repository**에서 해당 GitHub 저장소(`evergreen_church`) 선택.
3. **Root Directory**는 비워 두고(프로젝트 루트 그대로), **Framework Preset**은 "Other"로 두고 배포.
4. 배포가 끝나면 `https://프로젝트명.vercel.app` 형태의 URL로 앱에 접속할 수 있습니다.

### 프로젝트 구조 (Vercel 기준)

- `public/` — 정적 파일 (index.html, PROMPT_SERMON.md) → 루트 경로에서 제공
- `api/` — 서버리스 함수 (parse_docx.py, generate_pptx.py) → `/api/parse_docx`, `/api/generate_pptx`
- `lib/` — 공통 코드 (docx_parser, slide_runner)
- `EvergreenSlideMaker/` — 기존 슬라이드 제작용 리소스 (성경, 찬송, 이미지 등)

---

## 2. GitHub 연동 — “파일 추가되면 연동되는 느낌”

저장소를 **GitHub**에 두고 **Vercel**과 연결해 두면:

- **저장소가 곧 소스**입니다.  
  찬송가(`EvergreenSlideMaker/Hymn/hymn.txt`), 이미지(`EvergreenSlideMaker/image/`), 성경 텍스트(`EvergreenSlideMaker/bible/`) 등은 **전부 GitHub 저장소 안에** 두고 관리합니다.
- **파일을 추가/수정한 뒤 GitHub에 push**하면:
  - Vercel이 자동으로 새 커밋을 감지하고 **재배포**합니다.
  - 재배포가 끝나면 **배포된 앱에는 항상 최신 파일**이 반영됩니다.
- 즉, “로컬/다른 도구에서 파일 추가 → GitHub에 push → 자동으로 앱에 반영”되는 구조입니다.

### 정리

| 하고 싶은 일 | 하는 방법 |
|-------------|-----------|
| 찬송가 목록/내용 수정 | `EvergreenSlideMaker/Hymn/hymn.txt` 등 수정 후 GitHub에 push |
| 이미지 교체/추가 | `EvergreenSlideMaker/image/` 에 파일 추가·수정 후 push |
| 성경 텍스트 수정 | `EvergreenSlideMaker/bible/` 수정 후 push |
| 앱 코드/UI 수정 | `api/`, `lib/`, `public/` 수정 후 push |

push만 하면 Vercel이 자동으로 다시 빌드·배포하므로, **GitHub에 올라온 내용 = 앱에 반영되는 내용**이라고 보면 됩니다.

---

## 3. 주의사항

- **Body 크기 제한**: Vercel 서버리스는 요청 본문에 제한(예: 4.5MB)이 있을 수 있습니다. 매우 큰 DOCX는 잘라서 쓰거나, 필요한 구간만 업로드하는 방식으로 조정할 수 있습니다.
- **실행 시간**: `generate_pptx`는 슬라이드 수가 많으면 시간이 걸릴 수 있어, `vercel.json`에서 `maxDuration: 60`으로 두었습니다. (팀/플랜에 따라 상한이 다를 수 있습니다.)
- **EvergreenSlideMaker 없이 배포하면** PPTX 생성 API(`/api/generate_pptx`)는 동작하지 않습니다. 반드시 저장소에 `EvergreenSlideMaker` 폴더를 포함한 채로 배포하세요.
