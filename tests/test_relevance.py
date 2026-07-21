"""관련도 필터 단위 테스트."""

from __future__ import annotations

import pytest

from neet_collector.config import KeywordsConfig
from neet_collector.relevance import is_relevant, score

# 테스트용 기본 키워드
KEYWORDS = KeywordsConfig(
    strong=["니트족", "청년 니트", "NEET", "청년 무업자", "구직 단념 청년", "구직단념청년"],
    weak=["쉬었음 청년", "은둔 청년", "고립 청년", "히키코모리", "청년 실업", "장기 미취업", "청년 취업"],
    exclude=["니트웨어", "니트 패션", "스웨터", "가디건", "뜨개질", "원사"],
)


class TestScoring:
    def test_strong_keyword_in_title(self):
        s = score("니트족 청년 급증", "취업도 교육도 포기한 청년이 늘고 있다", KEYWORDS)
        assert s >= 50, f"강한 키워드 제목 점수가 낮음: {s}"

    def test_strong_keyword_in_body_only(self):
        s = score("청년 문제 심각", "구직단념청년이 증가하는 추세다", KEYWORDS)
        assert s >= 30, f"강한 키워드 본문 점수가 낮음: {s}"

    def test_weak_keyword(self):
        s = score("은둔 청년 지원 정책", "쉬었음 청년이 늘어나고 있다", KEYWORDS)
        assert s > 0, f"보조 키워드 점수가 0이면 안 됨: {s}"

    def test_exclude_keyword_reduces_score(self):
        s_with = score("니트족 증가", "니트웨어 패션 브랜드 관련 기사", KEYWORDS)
        s_without = score("니트족 증가", "청년 취업난이 심각하다", KEYWORDS)
        assert s_with < s_without, "제외 키워드가 점수를 낮춰야 함"

    def test_pure_fashion_article_filtered_out(self):
        s = score("가디건 코디법", "니트웨어 원사 뜨개질 스웨터 패션 트렌드", KEYWORDS)
        assert s == 0, f"패션 기사 점수가 0이어야 함: {s}"

    def test_score_clamped_0_to_100(self):
        s = score("니트족 NEET 청년 무업자 구직단념청년", "청년 니트 히키코모리 은둔 청년 쉬었음", KEYWORDS)
        assert 0 <= s <= 100

    def test_neet_english_keyword(self):
        s = score("NEET youth statistics 2024", "NEET 비율이 증가하고 있다", KEYWORDS)
        assert s >= 30


class TestIsRelevant:
    def test_relevant_article_passes(self):
        assert is_relevant("니트족 청년 급증", "구직단념청년 증가", KEYWORDS, threshold=30)

    def test_irrelevant_article_blocked(self):
        assert not is_relevant("패션 트렌드 2024", "스웨터 가디건 뜨개질 원사", KEYWORDS, threshold=30)

    def test_threshold_boundary(self):
        s = score("은둔 청년 지원", "장기 미취업 관련", KEYWORDS)
        assert is_relevant("은둔 청년 지원", "장기 미취업 관련", KEYWORDS, threshold=s)
        assert not is_relevant("은둔 청년 지원", "장기 미취업 관련", KEYWORDS, threshold=s + 1)
