# NEET 콘텐츠 수집기 — 대시보드 설계서

> 버전 1.0 · 2026-07-21  
> 대상 독자: 프론트엔드·백엔드 구현 담당자

---

## 1. 목표 및 사용자 스토리

| 우선순위 | 사용자 목표 |
|---------|-----------|
| P0 | 오늘 새로 수집된 NEET 관련 기사를 한눈에 확인한다 |
| P0 | 관련도 점수·감성·태그 기준으로 기사를 빠르게 필터링한다 |
| P1 | 피드 소스별 수집 상태(성공/실패)를 모니터링한다 |
| P1 | 수동으로 새 수집을 트리거하고 결과를 즉시 확인한다 |
| P2 | AI 분석 현황(미분석 건수, 감성 분포)을 파악한다 |
| P2 | 기사를 CSV/JSON으로 내보낸다 |

---

## 2. 정보 아키텍처(IA)

```
대시보드
├── 상단 헤더
│   ├── 로고 / 서비스명
│   ├── 마지막 수집 시각 + 새로고침 버튼
│   └── (설정 아이콘)
├── KPI 요약 카드 (4개)
├── 피드 상태 패널
├── 필터 / 검색 바
├── 기사 목록 패널
│   └── 기사 카드 (확장 가능)
└── 내보내기 / 액션 바
```

---

## 3. 로우파이 와이어프레임 명세

### 3-A 데스크탑 (≥1280px) — 12컬럼 그리드

```
┌──────────────────────────────────────────────────────────────────┐
│  HEADER  [로고] NEET 콘텐츠 수집기  [마지막 수집: 10분 전] [🔄]  │
├──────────────────────────────────────────────────────────────────┤
│ [KPI-1 총 기사] [KPI-2 오늘 수집] [KPI-3 AI 미분석] [KPI-4 감성] │
│  col 3           col 3             col 3              col 3      │
├───────────────────────────────┬──────────────────────────────────┤
│  피드 상태 패널 (col 4)        │  기사 목록 패널 (col 8)          │
│  ┌──────────────────────┐    │  ┌────────────────────────────┐   │
│  │ 피드1 ✅ 23건        │    │  │ 검색바 + 필터 드롭다운      │   │
│  │ 피드2 ✅ 11건        │    │  ├────────────────────────────┤   │
│  │ 피드3 ⚠️  0건        │    │  │ 기사 카드 (페이지네이션)   │   │
│  │ 피드4 ❌ 오류        │    │  │ 기사 카드                  │   │
│  └──────────────────────┘    │  │ 기사 카드                  │   │
│                               │  └────────────────────────────┘   │
├───────────────────────────────┴──────────────────────────────────┤
│  내보내기 바: [CSV 다운로드] [JSON 다운로드] [필터 적용 내보내기]  │
└──────────────────────────────────────────────────────────────────┘
```

### 3-B 태블릿 (768px–1279px) — 8컬럼 그리드

- KPI 카드: 2×2 배치
- 피드 상태 패널: 기사 목록 위로 이동 (accordion 접힘)
- 기사 목록: 전체 너비(8컬럼)

### 3-C 모바일 (< 768px) — 4컬럼 그리드

- 헤더: 로고 + 🔄 아이콘만 노출
- KPI 카드: 스크롤 가능한 수평 스크롤 트레이 (2개씩 보임)
- 피드 상태: 접힌 accordion
- 기사 목록: 전체 너비, 카드 1열

---

## 4. 컴포넌트 명세

### 4-1 `KpiCard` — KPI 요약 카드

| 항목 | 내용 |
|------|------|
| **목적** | 핵심 지표 숫자를 한눈에 보여 줌 |
| **인스턴스** | 총 기사 수 / 오늘 수집 수 / AI 미분석 수 / 감성 분포 |
| **필수 데이터** | `label: string`, `value: number\|string`, `delta?: number`, `trend?: "up"\|"down"\|"flat"`, `color?: token` |
| **비어있음** | 숫자 자리에 `—` 표시 |
| **로딩** | Skeleton shimmer (width 60%, height 1rem) |
| **오류** | 주황 경고 아이콘 + "데이터를 불러올 수 없습니다" |
| **인터랙션** | 클릭 시 해당 지표 기준 기사 목록으로 필터 이동 |

**KPI 항목 상세**

| # | 레이블 | 계산식 | 색 토큰 |
|---|--------|--------|---------|
| 1 | 총 기사 수 | `COUNT(*)` | `--color-primary` |
| 2 | 오늘 수집 | `COUNT(*) WHERE collected_at >= today` | `--color-success` |
| 3 | AI 미분석 | `COUNT(*) WHERE ai_summary IS NULL` | `--color-warning` |
| 4 | 감성 분포 | positive % / neutral % / negative % (미니 도넛) | `--color-info` |

---

### 4-2 `FeedStatusPanel` — 피드 상태 패널

| 항목 | 내용 |
|------|------|
| **목적** | 각 RSS 피드의 마지막 수집 건수·상태를 표시 |
| **필수 데이터** | `feeds: Array<{ name, url, lastRun: ISO8601, articleCount, status: "ok"\|"warn"\|"error", errorMsg? }>` |
| **상태 아이콘** | ✅ ok (초록) / ⚠️ warn – 0건 (주황) / ❌ error – 요청 실패 (빨강) |
| **비어있음** | "피드가 설정되지 않았습니다" |
| **로딩** | Skeleton 4행 |
| **오류** | 전체 패널에 빨강 배너 "피드 상태를 가져오지 못했습니다" |
| **인터랙션** | 피드 행 클릭 → 해당 source로 기사 목록 필터링 |

> 현재 백엔드는 피드별 상태를 DB에 저장하지 않습니다.  
> 구현 시 `collect.yml` 워크플로의 마지막 실행 로그 또는 별도의 `feed_runs` 테이블을 추가하세요.

---

### 4-3 `SearchFilterBar` — 검색 및 필터 바

| 항목 | 내용 |
|------|------|
| **목적** | 기사 목록을 실시간 좁히기 |
| **컨트롤** | 검색 입력(텍스트) / 소스 드롭다운 / 감성 체크박스 / 관련도 슬라이더(0–100) / 날짜 범위 피커 / 초기화 버튼 |
| **필수 데이터** | `sources: string[]` (DB에서 DISTINCT source), 기타 필터값은 로컬 상태 |
| **비어있음** | 필터 미적용 상태 (모든 기사 표시) |
| **로딩** | 드롭다운 옵션만 skeleton |
| **오류** | 필터 적용 실패 시 기사 목록에 표시 (자체 오류 없음) |
| **인터랙션** | debounce 300ms 검색 / 필터 변경 시 목록 즉시 갱신 / URL 쿼리스트링 동기화 |

---

### 4-4 `ArticleList` / `ArticleCard` — 기사 목록

| 항목 | 내용 |
|------|------|
| **목적** | 수집된 기사를 카드 형태로 나열 |
| **필수 데이터** | `id`, `title`, `url`, `source`, `published_at`, `collected_at`, `relevance_score`, `ai_summary?`, `ai_tags?: string[]`, `ai_sentiment?`, `image_url?` |
| **정렬** | 기본: `collected_at DESC` / 옵션: `relevance_score DESC`, `published_at DESC` |
| **페이지네이션** | 기본 20건/페이지 또는 무한 스크롤 |
| **비어있음** | 빈 상태 일러스트 + "조건에 맞는 기사가 없습니다" |
| **로딩** | Skeleton 카드 3개 |
| **오류** | 빨강 인라인 배너 |
| **인터랙션** | 카드 클릭 → 원문 URL 새 탭 열기 / 카드 확장 → AI 요약·태그·감성 표시 / 태그 클릭 → 해당 태그 검색 필터 적용 |

**ArticleCard 레이아웃**

```
┌─────────────────────────────────────────────────────┐
│  [썸네일 이미지]  제목 (최대 2줄)          [점수 뱃지]│
│                  출처 · 발행일 · 수집일               │
│                  [태그1] [태그2]  [감성: 긍정 🙂]     │
│  ▼ 펼치기                                            │
│    AI 요약 텍스트...                                  │
└─────────────────────────────────────────────────────┘
```

**관련도 점수 뱃지 색상**

| 점수 | 레이블 | 색 |
|------|--------|----|
| 80–100 | 매우 관련 | `--color-success` |
| 50–79 | 관련 | `--color-info` |
| 30–49 | 약관련 | `--color-warning` |
| 0–29 | 미달 | `--color-neutral` |

---

### 4-5 `RefreshButton` — 수동 새로고침

| 항목 | 내용 |
|------|------|
| **목적** | GitHub Actions 워크플로 `collect.yml` 수동 트리거 |
| **필수 데이터** | GitHub API `POST /repos/{owner}/{repo}/actions/workflows/collect.yml/dispatches` (PAT 필요) |
| **비어있음** | — |
| **로딩** | 버튼 비활성화 + 스피너 + "수집 중..." |
| **오류** | 토스트 "수집 트리거 실패: {message}" |
| **성공** | 토스트 "수집이 시작되었습니다. 1–2분 후 결과를 확인하세요." |
| **인터랙션** | 클릭 → 확인 modal → API 호출 → 토스트 / 완료 후 KPI 카드 자동 폴링(30초 간격) |

---

### 4-6 `ExportBar` — 내보내기 바

| 항목 | 내용 |
|------|------|
| **목적** | 현재 필터가 적용된 기사를 CSV 또는 JSON으로 다운로드 |
| **필수 데이터** | 현재 필터 상태 / DB 조회 결과 |
| **인터랙션** | [CSV 다운로드] / [JSON 다운로드] → Blob 다운로드 또는 서버 엔드포인트 호출 |
| **로딩** | 버튼 비활성화 + 스피너 |
| **오류** | 토스트 오류 메시지 |

---

## 5. 반응형 동작 요약

| 구역 | 데스크탑 ≥1280 | 태블릿 768–1279 | 모바일 <768 |
|------|--------------|----------------|------------|
| KPI 카드 | 1행 4열 | 2행 2열 | 수평 스크롤 |
| 피드 상태 | 좌측 사이드 패널 | 기사 목록 위 accordion | 접힌 accordion |
| 기사 목록 | 우측 col-8 | 전체 너비 | 전체 너비 |
| 검색 필터 | 기사 목록 상단 인라인 | 전체 너비 | 전체 너비, 일부 필터 drawer로 이동 |
| 내보내기 바 | 하단 고정 | 하단 고정 | 하단 고정, 아이콘만 |

---

## 6. 최소 비주얼 디자인 시스템

### 6-1 색상 토큰

모든 색상은 **WCAG 2.1 AA** (대비 4.5:1 이상)를 만족해야 합니다.

```css
:root {
  /* 브랜드 */
  --color-primary:   #2563EB; /* Blue-600 – 주요 액션, 링크 */
  --color-primary-lt:#EFF6FF; /* Blue-50  – 배경 강조 */

  /* 시맨틱 */
  --color-success:   #16A34A; /* Green-600 */
  --color-warning:   #D97706; /* Amber-600 */
  --color-error:     #DC2626; /* Red-600 */
  --color-info:      #0891B2; /* Cyan-600 */

  /* 중립 */
  --color-neutral-900: #111827;
  --color-neutral-700: #374151;
  --color-neutral-400: #9CA3AF;
  --color-neutral-100: #F3F4F6;
  --color-neutral-50:  #F9FAFB;

  /* 배경 */
  --color-bg:        #FFFFFF;
  --color-surface:   #F9FAFB;
  --color-border:    #E5E7EB;
}
```

> 감성 색상: positive → `--color-success`, neutral → `--color-info`, negative → `--color-error`

### 6-2 타이포그래피 스케일

```css
/* 기반: Inter 또는 Noto Sans KR (한국어 지원 필수) */
--font-family-base: "Noto Sans KR", "Inter", system-ui, sans-serif;

--text-xs:   0.75rem / 1rem;    /* 12px – 뱃지, 레이블 */
--text-sm:   0.875rem / 1.25rem; /* 14px – 본문 보조 */
--text-base: 1rem / 1.5rem;     /* 16px – 본문 기본 */
--text-lg:   1.125rem / 1.75rem;/* 18px – 카드 제목 */
--text-xl:   1.25rem / 1.75rem; /* 20px – 섹션 제목 */
--text-2xl:  1.5rem / 2rem;     /* 24px – KPI 숫자 */
--text-3xl:  1.875rem / 2.25rem;/* 30px – 페이지 제목 */

--font-weight-normal:  400;
--font-weight-medium:  500;
--font-weight-bold:    700;
```

### 6-3 간격 시스템 (4px 베이스)

```css
--space-1:  0.25rem;  /* 4px */
--space-2:  0.5rem;   /* 8px */
--space-3:  0.75rem;  /* 12px */
--space-4:  1rem;     /* 16px */
--space-6:  1.5rem;   /* 24px */
--space-8:  2rem;     /* 32px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
```

### 6-4 재사용 UI 컴포넌트 목록

| 컴포넌트 | 설명 |
|---------|------|
| `Button` | variant: primary / secondary / ghost / danger; size: sm / md / lg; loading 상태 |
| `Badge` | 감성·점수·태그 뱃지, 색 토큰 연동 |
| `Card` | 기본 흰 배경, border-radius 8px, shadow-sm |
| `Skeleton` | shimmer 애니메이션 Placeholder |
| `Toast` | success / warning / error / info, 3초 자동 사라짐 |
| `Modal` | 확인 다이얼로그 (RefreshButton 사용) |
| `Accordion` | 피드 상태, 모바일 필터 패널 |
| `Select` | 기본 드롭다운 (소스 필터) |
| `RangeSlider` | 관련도 점수 필터 (0–100) |
| `DateRangePicker` | 기간 필터 |
| `Spinner` | 로딩 인디케이터 |
| `EmptyState` | 일러스트 + 메시지 + 선택적 CTA 버튼 |

---

## 7. 백엔드 API 엔드포인트 제안

현재 프로젝트는 CLI + 파일 기반입니다. 대시보드 구현을 위해 아래 REST 엔드포인트를 추가하길 권장합니다 (FastAPI 또는 Flask 기준).

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/api/stats` | KPI 통계 (총 기사, 오늘 수집, 미분석, 감성 분포) |
| `GET` | `/api/articles` | 기사 목록 (query params: `q`, `source`, `sentiment`, `min_score`, `from`, `to`, `page`, `limit`, `sort`) |
| `GET` | `/api/feeds` | 피드 상태 목록 |
| `POST` | `/api/collect` | 수집 트리거 (GitHub Actions dispatch 래퍼) |
| `GET` | `/api/export/csv` | CSV 다운로드 (동일 필터 파라미터 지원) |
| `GET` | `/api/export/json` | JSON 다운로드 |

### `/api/stats` 응답 예시

```json
{
  "total": 1024,
  "today": 42,
  "ai_pending": 18,
  "sentiment": {
    "positive": 0.35,
    "neutral": 0.48,
    "negative": 0.17
  },
  "last_collected_at": "2026-07-21T05:10:00Z"
}
```

### `/api/articles` 응답 예시

```json
{
  "items": [
    {
      "id": 1,
      "title": "니트족 청년 지원 정책 확대",
      "url": "https://...",
      "source": "Google News – 니트족",
      "published_at": "2026-07-21T03:00:00",
      "collected_at": "2026-07-21T05:10:00Z",
      "relevance_score": 80,
      "ai_summary": "정부가 구직단념청년 지원 프로그램을 확대한다...",
      "ai_tags": ["청년정책", "구직단념", "취업지원"],
      "ai_sentiment": "positive",
      "image_url": "https://..."
    }
  ],
  "total": 1024,
  "page": 1,
  "limit": 20
}
```

---

## 8. 데이터 신선도 / 상태 표시 규칙

| 경과 시간 | 표시 | 색상 |
|-----------|------|------|
| < 1시간 | "방금 수집" | `--color-success` |
| 1–6시간 | "N시간 전" | `--color-neutral-700` |
| 6–24시간 | "N시간 전" | `--color-warning` |
| > 24시간 | "N일 전 — 새로고침 권장" | `--color-error` |

---

## 9. 구현 우선순위 로드맵

| 단계 | 범위 | 예상 난이도 |
|------|------|------------|
| 1 | `/api/stats` + `/api/articles` 엔드포인트 추가 (FastAPI) | 낮음 |
| 2 | KpiCard + ArticleList + SearchFilterBar 구현 (React/Vue) | 중간 |
| 3 | FeedStatusPanel + RefreshButton (GitHub API 연동) | 중간 |
| 4 | ExportBar + 반응형 레이아웃 완성 | 낮음 |
| 5 | 폴링/웹소켓으로 실시간 업데이트 | 높음 |

---

## 10. 접근성 체크리스트

- [ ] 모든 인터랙티브 요소에 `aria-label` 또는 가시적 레이블 제공
- [ ] 색상 대비 4.5:1 이상 (WCAG AA)
- [ ] 키보드 탐색 가능 (Tab, Enter, Space, Escape)
- [ ] 스크린 리더 호환 (`role`, `aria-live` 리전 — 로딩/오류/새 기사)
- [ ] 감성 아이콘은 텍스트 대체 제공 (`aria-label="긍정"` 등)
- [ ] 모바일 터치 타겟 최소 44×44px
