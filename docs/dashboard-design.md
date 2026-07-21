# NEET 콘텐츠 수집기 대시보드 설계서

> 버전 1.1 · 2026-07-21  
> 대상: 프론트엔드·백엔드 구현 담당자  
> 범위: 현재 저장소(`CLI + SQLite + GitHub Actions`)를 기반으로 한 운영용 대시보드 MVP

---

## 1. 설계 목표

이 문서는 현재 저장소 구조를 기준으로 **바로 구현 가능한 대시보드 명세**를 정리합니다.

### 핵심 목표

1. 수집 결과를 한 화면에서 빠르게 확인한다.
2. 기사 목록을 검색·필터·정렬해 운영 판단에 바로 사용한다.
3. GitHub Actions 기반 수집 실행 상태를 운영자가 확인하고 필요 시 재실행한다.
4. 현재 저장소의 SQLite 스키마와 export 기능을 최대한 재사용한다.

### 대상 사용자

- **운영자**: 오늘 수집 결과, 실패 여부, 관련도 높은 기사 확인
- **분석 사용자**: 태그·감성·키워드 기준 기사 탐색 및 내보내기
- **개발자**: 현재 CLI/DB 구조를 웹 UI/API로 확장 구현

---

## 2. 현재 저장소 기준 제약과 전제

### 이미 존재하는 자산

- 기사 저장소: `data/neet_articles.db`
- 핵심 테이블: `articles`
- 기사 조회 메서드: `Database.all_articles()`
- 기사 총계 메서드: `Database.count()`
- 수동/예약 수집 워크플로: `.github/workflows/collect.yml`
- 내보내기 기능: `python -m neet_collector export --format csv|json`

### 현재 `articles` 테이블 필드

| 필드 | 설명 |
|---|---|
| `id` | 내부 ID |
| `url` | 원문 URL |
| `url_hash` | URL 해시 |
| `content_hash` | 본문 해시 |
| `title` | 기사 제목 |
| `body` | 본문/요약 텍스트 |
| `source` | 피드 이름 |
| `published_at` | 기사 발행시각 |
| `image_url` | 대표 이미지 |
| `collected_at` | 수집시각 |
| `relevance_score` | 관련도 점수 |
| `ai_summary` | AI 요약 |
| `ai_tags` | AI 태그 JSON 문자열 |
| `ai_sentiment` | 감성(`positive`/`neutral`/`negative`) |

### 현재 없는 것

아래 항목은 대시보드에서 필요하지만 현재 저장소에는 별도 저장 구조가 없습니다.

- 수집 실행 이력(run 단위 상태)
- 피드별 성공/실패/수집 건수
- 워크플로 실행 상태의 API 레이어
- 페이지네이션/필터링용 웹 API

따라서 MVP 구현 시:

1. **기사 목록/통계는 SQLite 기반으로 바로 구현**하고,
2. **실행 상태와 피드 상태는 GitHub Actions API 또는 신규 테이블로 보강**합니다.

---

## 3. 화면 정보 구조(IA)

```
대시보드
├── 헤더
│   ├── 서비스명
│   ├── 마지막 수집 시각
│   ├── 새로고침 버튼
│   └── 수집 실행 버튼
├── 상태 요약 영역
│   ├── 총 기사 수
│   ├── 오늘 수집 수
│   ├── AI 미분석 수
│   └── 감성 분포
├── 운영 상태 영역
│   ├── 최근 실행 상태 패널
│   └── 피드 상태 패널
├── 기사 탐색 영역
│   ├── 검색/필터 바
│   ├── 정렬/건수 제어
│   └── 기사 목록
└── 하단 액션 바
    ├── CSV 다운로드
    ├── JSON 다운로드
    └── 현재 필터 공유/초기화
```

### 내비게이션 원칙

- 단일 화면 MVP를 기준으로 한다.
- 첫 릴리스에서는 별도 사이드바 없이 한 페이지 구성으로 충분하다.
- URL 쿼리스트링으로 현재 필터 상태를 유지한다.

---

## 4. 레이아웃 명세

### 4-1 데스크탑 (≥ 1280px, 12컬럼)

- 헤더: 12컬럼 전체
- KPI 카드: 4개 × 각 3컬럼
- 운영 상태: 최근 실행 상태 4컬럼 + 피드 상태 4컬럼 + 기사 목록 4컬럼 확장 대신,
  **실사용성 기준으로 기사 목록을 넓게 가져가야 하므로** 다음 구성을 권장
  - 좌측 4컬럼: 최근 실행 상태 + 피드 상태
  - 우측 8컬럼: 검색/필터 + 기사 목록
- 하단 액션 바: sticky footer 또는 목록 상단 보조 액션 바

### 4-2 태블릿 (768px–1279px, 8컬럼)

- KPI 카드: 2 × 2
- 최근 실행 상태 / 피드 상태: accordion 또는 2개 stacked card
- 기사 목록: 8컬럼 전체
- 필터는 1행 일부 + “상세 필터” drawer 조합

### 4-3 모바일 (< 768px, 4컬럼)

- 헤더: 서비스명 + 실행 버튼 + 더보기
- KPI: 가로 스크롤 카드
- 최근 실행 상태 / 피드 상태: 기본 접힘
- 필터: 전면 bottom sheet 또는 drawer
- 기사 카드: 1열, 요약 접힘 기본값

---

## 5. 위젯 명세

## 5-1 `HeaderBar`

| 항목 | 명세 |
|---|---|
| 목적 | 화면 전체 상태와 핵심 액션 제공 |
| 표시 데이터 | 서비스명, 마지막 수집 시각, 최근 실행 상태, 실행 버튼 |
| 데이터 소스 | `/api/stats`, `/api/runs/latest` |
| 주요 액션 | 새로고침, 수집 실행 |
| 로딩 | 마지막 수집 시각 skeleton |
| 오류 | 상태 배지에 “상태 확인 실패” 표시 |

### 인터랙션

- `새로고침`: KPI/목록/상태 패널 전체 재조회
- `수집 실행`: 확인 모달 → 워크플로 dispatch → 성공 시 최근 실행 상태를 `queued`로 갱신

---

## 5-2 `KpiCardGroup`

| KPI | 정의 | 데이터 소스 |
|---|---|---|
| 총 기사 수 | 전체 `articles` 건수 | SQLite |
| 오늘 수집 수 | `collected_at >= 오늘 00:00` | SQLite |
| AI 미분석 수 | `ai_summary IS NULL OR ai_summary = ''` | SQLite |
| 감성 분포 | 감성별 건수/비율 | SQLite |

### 카드 공통 명세

| 항목 | 명세 |
|---|---|
| 상태 | 기본 / 로딩 / 비어있음 / 오류 |
| 클릭 동작 | 해당 조건으로 기사 목록 필터 적용 |
| 비어있음 | `—` 표시 |
| 오류 | 인라인 오류 텍스트 + 재시도 버튼 |

### 권장 계산식

```sql
SELECT COUNT(*) AS total FROM articles;

SELECT COUNT(*) AS today_count
FROM articles
WHERE datetime(collected_at) >= datetime(:today_start);

SELECT COUNT(*) AS ai_pending
FROM articles
WHERE ai_summary IS NULL OR ai_summary = '';

SELECT
  SUM(CASE WHEN ai_sentiment = 'positive' THEN 1 ELSE 0 END) AS positive,
  SUM(CASE WHEN ai_sentiment = 'neutral' THEN 1 ELSE 0 END) AS neutral,
  SUM(CASE WHEN ai_sentiment = 'negative' THEN 1 ELSE 0 END) AS negative
FROM articles;
```

---

## 5-3 `RecentRunPanel`

현재 저장소에서 운영상 가장 필요한 신규 위젯입니다.

| 항목 | 명세 |
|---|---|
| 목적 | 최근 GitHub Actions 수집 실행 상태를 확인 |
| 기본 표시 | 최근 실행 상태, 시작 시각, 종료 시각, 결과, artifact 여부 |
| 데이터 소스 | GitHub Actions API 또는 서버 캐시 |
| 주요 상태 | `queued`, `in_progress`, `success`, `failed`, `cancelled` |
| 세부 정보 | 실행 번호, 실행자, `no_ai` 여부, 실패 요약 |

### 권장 필드

- `run_id`
- `status`
- `conclusion`
- `started_at`
- `updated_at`
- `html_url`
- `actor`
- `event`
- `artifact_count`
- `no_ai`

### 인터랙션

- 패널 클릭 → GitHub Actions 실행 상세 새 탭 이동
- 실패 상태 클릭 → 실패 로그 drawer 또는 상세 페이지 이동

---

## 5-4 `FeedStatusPanel`

현재 워크플로만으로는 피드별 상태를 직접 저장하지 않으므로, 이 위젯은 **2단계 구현**을 기준으로 설계합니다.

### 1단계(MVP)

- `config.yaml`의 `feeds` 목록을 기준으로 피드 이름/URL만 표시
- 상태는 “실행 데이터 없음” 또는 최근 수집 시점 기준의 간접 상태만 제공

### 2단계(권장)

수집 과정에서 `feed_runs` 테이블 또는 JSON 로그를 추가 저장

| 항목 | 명세 |
|---|---|
| 목적 | 피드별 성공/실패/수집 건수 표시 |
| 필수 데이터 | `name`, `url`, `last_run_at`, `status`, `article_count`, `error_message` |
| 상태값 | `ok`, `warn`, `error`, `unknown` |
| 클릭 동작 | 해당 피드 기준 기사 목록 필터 적용 |
| 비어있음 | “피드 실행 이력이 없습니다” |

### 상태 규칙

- `ok`: 최근 실행 성공 + 기사 1건 이상
- `warn`: 최근 실행 성공 + 기사 0건
- `error`: 최근 실행 실패 또는 피드 요청 실패
- `unknown`: 아직 수집 이력 없음

---

## 5-5 `SearchFilterBar`

| 항목 | 명세 |
|---|---|
| 목적 | 기사 탐색 속도 향상 |
| 기본 컨트롤 | 검색어, 소스, 감성, 최소 관련도, 날짜 범위 |
| 보조 컨트롤 | 정렬, 페이지 크기, 필터 초기화 |
| URL 동기화 | 필수 |
| 적용 방식 | 검색 300ms debounce, 나머지 즉시 적용 |

### 필터 필드

- `q`: 제목 + 본문 검색
- `source`: 피드 이름 exact match
- `sentiment[]`: 복수 선택 가능
- `min_score`: 기본 30
- `date_from`, `date_to`: `published_at` 또는 `collected_at` 기준
- `has_summary`: AI 요약 존재 여부
- `has_image`: 썸네일 존재 여부

### 정렬 옵션

- `collected_at desc` (기본)
- `published_at desc`
- `relevance_score desc`
- `title asc`

---

## 5-6 `ArticleList` / `ArticleCard`

### 목록 필수 필드

| 필드 | 사용 위치 |
|---|---|
| `id` | key, 상세 진입 |
| `title` | 카드 제목 |
| `url` | 원문 링크 |
| `source` | 메타 정보 |
| `published_at` | 메타 정보 |
| `collected_at` | 메타 정보 |
| `relevance_score` | 점수 배지 |
| `ai_summary` | 확장 영역 |
| `ai_tags` | 태그 배지 |
| `ai_sentiment` | 감성 배지 |
| `image_url` | 썸네일 |
| `body` | 검색 스니펫/폴백 |

### 카드 구조

1. 썸네일(있을 때만)
2. 제목
3. 출처 / 발행시각 / 수집시각
4. 관련도 배지 / 감성 배지
5. 태그 영역
6. 펼침 시 AI 요약 + 본문 일부
7. 원문 열기 버튼

### 상태

| 상태 | 처리 |
|---|---|
| 로딩 | 3개 skeleton 카드 |
| 비어있음 | “조건에 맞는 기사가 없습니다” |
| 오류 | 인라인 오류 + 재시도 |
| 일부 데이터 누락 | 발행일/감성/이미지 없는 경우 해당 슬롯만 숨김 |

### 인터랙션

- 카드 전체 클릭보다 **명시적 원문 버튼** 우선 권장
- 태그 클릭 → 검색 필터 반영
- 관련도 배지 클릭 → `min_score` 조정
- 감성 배지 클릭 → 해당 감성 필터 반영
- 확장 토글 기본값: 데스크탑 닫힘 / 모바일 닫힘

---

## 5-7 `ExportBar`

| 항목 | 명세 |
|---|---|
| 목적 | 현재 필터 상태 그대로 CSV/JSON 추출 |
| 형식 | CSV, JSON |
| 데이터 소스 | 서버 측 필터 재실행 또는 기존 export 함수 확장 |
| 성공 처리 | 파일 다운로드 + 토스트 |
| 오류 처리 | 토스트 + 실패 사유 표시 |

### 구현 원칙

- 기존 `export_csv`, `export_json` 로직을 재사용하되 필터 조건 지원을 추가한다.
- 다운로드 파일명은 `neet-articles-YYYYMMDD-HHmm` 형식을 권장한다.

---

## 6. 데이터/API 명세

## 6-1 API 목록

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/api/stats` | KPI + 마지막 수집 시각 |
| `GET` | `/api/articles` | 기사 목록 조회 |
| `GET` | `/api/runs/latest` | 최근 수집 실행 상태 |
| `GET` | `/api/runs` | 최근 실행 이력 목록 |
| `GET` | `/api/feeds` | 피드 상태 목록 |
| `POST` | `/api/collect` | `collect.yml` 수동 실행 |
| `GET` | `/api/export/csv` | 현재 필터 기준 CSV 다운로드 |
| `GET` | `/api/export/json` | 현재 필터 기준 JSON 다운로드 |

## 6-2 `/api/stats`

```json
{
  "total": 1024,
  "today": 42,
  "ai_pending": 18,
  "sentiment": {
    "positive": 320,
    "neutral": 510,
    "negative": 176,
    "unknown": 18
  },
  "last_collected_at": "2026-07-21T05:10:00Z",
  "latest_run": {
    "status": "completed",
    "conclusion": "success",
    "run_id": 123456789
  }
}
```

## 6-3 `/api/articles`

### 쿼리 파라미터

- `q`
- `source`
- `sentiment` (복수 허용)
- `min_score`
- `date_from`
- `date_to`
- `has_summary`
- `has_image`
- `sort`
- `page`
- `limit`

### 응답 예시

```json
{
  "items": [
    {
      "id": 1,
      "title": "니트족 청년 지원 정책 확대",
      "url": "https://example.com/article/1",
      "source": "Google News – 니트족",
      "published_at": "2026-07-21T03:00:00Z",
      "collected_at": "2026-07-21T05:10:00Z",
      "relevance_score": 80,
      "ai_summary": "정부가 구직단념청년 지원 프로그램을 확대한다...",
      "ai_tags": ["청년정책", "구직단념", "취업지원"],
      "ai_sentiment": "positive",
      "image_url": "https://example.com/image.jpg",
      "body_snippet": "정부가 구직단념청년을 대상으로..."
    }
  ],
  "total": 1024,
  "page": 1,
  "limit": 20,
  "has_next": true
}
```

## 6-4 `/api/runs/latest`

```json
{
  "run_id": 123456789,
  "workflow": "collect.yml",
  "status": "completed",
  "conclusion": "success",
  "started_at": "2026-07-21T05:00:00Z",
  "updated_at": "2026-07-21T05:02:30Z",
  "actor": "nuga-cracker",
  "event": "workflow_dispatch",
  "artifact_count": 3,
  "html_url": "https://github.com/nuga-cracker/neet-content-collector/actions/runs/123456789"
}
```

---

## 7. 상태 정의

## 7-1 공통 화면 상태

| 상태 | 조건 | UI 처리 |
|---|---|---|
| initial-loading | 첫 진입, 데이터 없음 | 전체 skeleton |
| refreshing | 기존 데이터 있음 + 재조회 중 | 기존 데이터 유지 + 상단 progress |
| empty | 조건 만족 기사 0건 | empty state |
| partial-error | 일부 패널 실패 | 실패 패널만 오류 표시 |
| full-error | 핵심 API 전체 실패 | 전체 오류 화면 + 재시도 |

## 7-2 기사 카드 세부 상태

| 상태 | 처리 |
|---|---|
| `ai_summary` 없음 | “AI 분석 없음” 배지 |
| `ai_sentiment` 없음 | 감성 배지 숨김 |
| `image_url` 없음 | 썸네일 영역 제거 |
| `published_at` 없음 | “발행일 미상” |

## 7-3 실행 상태 배지

| 상태 | 색상 | 문구 |
|---|---|---|
| queued | blue | 대기 중 |
| in_progress | amber | 수집 중 |
| success | green | 성공 |
| failed | red | 실패 |
| cancelled | gray | 취소 |
| unknown | gray | 확인 불가 |

---

## 8. 주요 사용자 인터랙션

1. **페이지 진입**
   - `/api/stats`, `/api/runs/latest`, `/api/articles` 동시 호출
2. **KPI 클릭**
   - 기사 목록 필터 자동 적용
3. **검색 입력**
   - 300ms debounce 후 목록 재조회
4. **필터 변경**
   - URL 쿼리스트링 동기화
5. **수집 실행 버튼 클릭**
   - 확인 모달 → `/api/collect` → 최근 실행 상태 폴링 시작
6. **실행 실패 배지 클릭**
   - 실패 로그 또는 GitHub Actions 상세 진입
7. **CSV/JSON 다운로드 클릭**
   - 현재 필터 유지한 채 다운로드

---

## 9. 반응형 동작 요약

| 구역 | 데스크탑 | 태블릿 | 모바일 |
|---|---|---|---|
| 헤더 | 한 줄 배치 | 2줄 허용 | 액션 축약 |
| KPI | 4열 | 2x2 | 가로 스크롤 |
| 상태 패널 | 좌측 스택 | 상단 스택 | accordion |
| 필터 | 인라인 + 보조 컨트롤 | 일부 접힘 | drawer/bottom sheet |
| 기사 목록 | 2열 카드 또는 넓은 1열 | 1열 | 1열 |
| 액션 바 | 우측 상단 또는 sticky | sticky | 하단 고정 |

### 모바일 우선 규칙

- 터치 타겟 최소 44x44px
- 태그는 2줄까지만 노출 후 `+N` 처리
- 날짜/메타 정보는 줄바꿈 허용
- 긴 제목은 2줄 ellipsis

---

## 10. 구현 우선순위

### Phase 1 — 바로 구현 가능

1. `/api/stats`
2. `/api/articles`
3. KPI 카드
4. 검색/필터 바
5. 기사 목록
6. CSV/JSON 다운로드

### Phase 2 — 운영성 강화

1. `/api/runs/latest`
2. 수동 수집 실행 버튼
3. 최근 실행 상태 패널
4. 실패 로그 진입

### Phase 3 — 고도화

1. 피드별 상태 저장 구조 추가
2. `/api/feeds` 정교화
3. 실시간 업데이트(폴링 또는 SSE)
4. 저장된 필터 preset

---

## 11. 구현 핸드오프 포인트

### 백엔드

- 기존 `Database` 래퍼를 유지하되 목록/통계용 조회 메서드 추가
- `ai_tags`는 응답 직전에 JSON 파싱해 배열로 반환
- 날짜 비교는 UTC 기준으로 통일
- GitHub Actions 호출용 토큰은 서버 환경변수로 관리

### 프론트엔드

- 단일 대시보드 페이지 우선
- URL 기반 필터 상태 저장 필수
- skeleton → data → refresh 흐름 분리
- 기사 카드 재사용 가능한 배지/메타 컴포넌트로 분해

### 보안/운영

- GitHub Actions dispatch 토큰은 브라우저에 노출하지 않고 서버 경유
- 원문 URL은 새 탭 오픈 시 `rel="noreferrer noopener"` 적용
- 실패 로그는 내부 운영자만 보도록 제한 가능성 고려

---

## 12. 완료 기준(Definition of Done)

아래가 충족되면 본 설계를 기준으로 구현 착수 가능합니다.

- [x] IA 정의 완료
- [x] 핵심 위젯 정의 완료
- [x] 데이터 필드 매핑 완료
- [x] 로딩/빈 상태/오류 상태 정의 완료
- [x] 주요 인터랙션 정의 완료
- [x] 반응형 규칙 정의 완료
- [x] 현재 저장소 구조 대비 구현 갭 명시 완료
- [x] 구현 우선순위 및 핸드오프 포인트 정리 완료
