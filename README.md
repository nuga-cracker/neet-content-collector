# NEET · 청년정책 링크 허브

**니트족(NEET: 취업·교육·직업훈련에 참여하지 않는 청년층) 관련 기사·콘텐츠 자동 수집기**

RSS 피드에서 관련 기사를 수집하고, 관련도 필터링·중복 제거·AI 분석을 거쳐 SQLite에 저장하는 Python MVP입니다.

[![Collect NEET Articles](https://github.com/nuga-cracker/neet-content-collector/actions/workflows/collect.yml/badge.svg)](https://github.com/nuga-cracker/neet-content-collector/actions/workflows/collect.yml)

---

## 목차

1. [기능](#기능)
2. [설치](#설치)
3. [설정](#설정)
4. [실행](#실행)
5. [데이터 필드](#데이터-필드)
6. [GitHub Actions](#github-actions)
7. [법적·윤리적 주의사항](#법적윤리적-주의사항)

---

## 기능

- **RSS 수집**: Google News RSS 및 사용자 지정 RSS URL에서 기사 수집
- **관련도 필터링**: 강한/보조/제외 키워드 기반 점수 계산, 임계값 미달 기사 자동 제외
- **중복 제거**: URL 정규화, URL 해시, 제목 유사도 기반 중복 감지
- **SQLite 저장**: URL 고유 제약, 영속 데이터 저장
- **AI 분석** (선택): OpenAI API로 요약·태그·감성 분석 (API 키 없으면 자동 건너뜀)
- **CSV/JSON 내보내기**: CLI 명령으로 즉시 내보내기
- **GitHub Actions**: 매일 자동 수집 및 artifact 업로드

---

## 설치

### 요구 사항

- Python 3.11 이상

### 방법 1: pip로 설치 (개발 모드)

```bash
git clone https://github.com/nuga-cracker/neet-content-collector.git
cd neet-content-collector
pip install -e ".[dev]"
```

### 방법 2: requirements 방식

```bash
pip install feedparser requests pyyaml python-dotenv beautifulsoup4 lxml openai
```

---

## 설정

### 환경 변수

`.env.example`을 복사해 `.env` 파일을 만들고 필요한 값을 입력합니다.

```bash
cp .env.example .env
```

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 키 (없으면 AI 분석 건너뜀) | - |
| `OPENAI_MODEL` | 사용할 OpenAI 모델 | `gpt-4o-mini` |
| `NEET_CONFIG` | 설정 파일 경로 | `config.yaml` |
| `NEET_DB_PATH` | SQLite DB 파일 경로 | `data/neet_articles.db` |

### config.yaml

프로젝트 루트의 `config.yaml`에서 RSS 피드, 키워드, 임계값 등을 수정할 수 있습니다.

```yaml
relevance_threshold: 30   # 관련도 점수 임계값 (0~100)

feeds:
  - name: "Google News – 니트족"
    url: "https://news.google.com/rss/search?q=%EB%8B%88%ED%8A%B8%EC%A1%B1&hl=ko&gl=KR&ceid=KR:ko"
  # 원하는 RSS URL 추가 가능

keywords:
  strong: ["니트족", "청년 니트", "NEET", ...]
  weak:   ["쉬었음 청년", "은둔 청년", ...]
  exclude: ["니트웨어", "니트 패션", ...]
```

---

## 실행

### 기사 수집

```bash
python -m neet_collector collect
```

AI 분석을 건너뛰려면:

```bash
python -m neet_collector collect --no-ai
```

### 내보내기

```bash
# CSV로 내보내기
python -m neet_collector export --format csv --output data/articles.csv

# JSON으로 내보내기
python -m neet_collector export --format json --output data/articles.json

# 최근 100건만 CSV로
python -m neet_collector export --format csv --limit 100
```

### 통계 확인

```bash
python -m neet_collector stats
```

### 테스트 실행

```bash
pytest tests/ -v
```

---

## 데이터 필드

| 필드 | 설명 |
|------|------|
| `id` | DB 내부 ID |
| `title` | 기사 제목 |
| `url` | 원문 URL |
| `source` | 출처 (언론사/피드 이름) |
| `published_at` | 발행일 (ISO 8601) |
| `body` | 본문 또는 RSS 요약문 (최대 2,000자) |
| `image_url` | 대표 이미지 URL |
| `collected_at` | 수집 시각 (UTC ISO 8601) |
| `relevance_score` | 관련도 점수 (0~100) |
| `ai_summary` | AI 생성 요약 (선택) |
| `ai_tags` | AI 생성 태그 목록 JSON (선택) |
| `ai_sentiment` | 감성 분석 결과: `positive` / `neutral` / `negative` (선택) |

---

## GitHub Actions

`.github/workflows/collect.yml`에 두 가지 워크플로가 포함됩니다.

- **Collect and Export**: 매일 한국시간 오전 9시 자동 실행 + 수동 실행 가능
  - 수집 결과(DB, CSV, JSON)를 **artifact**로 업로드 (저장소에 커밋하지 않음)
  - `OPENAI_API_KEY` secret이 없어도 정상 동작
- **Run Tests**: pytest 자동 실행

저장소 Settings → Secrets and variables → Actions 에서 `OPENAI_API_KEY`를 등록하면 AI 분석이 활성화됩니다.

---

## 법적·윤리적 주의사항

> **이 프로젝트는 연구·교육 목적의 메타데이터 수집기입니다.**

- 기사 **전문 재배포가 목적이 아닙니다**. 제목·짧은 요약·원문 링크 중심으로만 활용하세요.
- 각 언론사·서비스의 **이용약관**과 **robots.txt**를 반드시 확인하고 준수하세요.
- Google News RSS 등 공개 API/피드만 사용하며, 무단 스크래핑은 하지 않습니다.
- 수집된 데이터에는 **저작권**이 존재할 수 있습니다. 상업적 재사용 전 반드시 확인하세요.
- 개인을 특정할 수 있는 정보(이름, 연락처 등)는 수집하지 않으며 **개인정보보호법**을 준수합니다.
- API 요청은 적절한 간격을 두고 서버에 과부하를 주지 않습니다.
- **비밀 키(API 키 등)를 저장소에 절대 커밋하지 마세요.** `.env` 파일은 `.gitignore`에 포함됩니다.

---

## 프로젝트 구조

```
neet-content-collector/
├── src/neet_collector/
│   ├── __init__.py
│   ├── __main__.py       # CLI 진입점
│   ├── config.py         # 설정 로더
│   ├── collector.py      # RSS 수집
│   ├── relevance.py      # 관련도 점수
│   ├── deduplication.py  # 중복 제거
│   ├── database.py       # SQLite 저장소
│   ├── ai_analysis.py    # OpenAI 분석
│   └── exporter.py       # CSV/JSON 내보내기
├── tests/
│   ├── test_relevance.py
│   ├── test_deduplication.py
│   ├── test_collector_parsing.py
│   └── test_config.py
├── data/                 # DB·출력 파일 (gitignore)
├── .github/workflows/collect.yml
├── config.yaml
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

---

## 라이선스

MIT
