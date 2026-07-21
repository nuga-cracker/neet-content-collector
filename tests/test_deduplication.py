"""URL 정규화 및 중복 제거 단위 테스트."""

from __future__ import annotations

import pytest

from neet_collector.deduplication import (
    DuplicateChecker,
    normalize_title,
    normalize_url,
    title_similarity,
    url_hash,
)


class TestNormalizeUrl:
    def test_removes_tracking_params(self):
        url = "https://example.com/article?utm_source=naver&utm_campaign=abc&id=123"
        norm = normalize_url(url)
        assert "utm_source" not in norm
        assert "utm_campaign" not in norm
        assert "id=123" in norm

    def test_removes_www(self):
        a = normalize_url("https://www.example.com/article")
        b = normalize_url("https://example.com/article")
        assert a == b

    def test_removes_trailing_slash(self):
        a = normalize_url("https://example.com/article/")
        b = normalize_url("https://example.com/article")
        assert a == b

    def test_removes_fragment(self):
        a = normalize_url("https://example.com/article#section1")
        b = normalize_url("https://example.com/article")
        assert a == b

    def test_normalizes_scheme_to_https(self):
        norm = normalize_url("http://example.com/article")
        assert norm.startswith("https://")

    def test_sorts_query_params(self):
        a = normalize_url("https://example.com/search?b=2&a=1")
        b = normalize_url("https://example.com/search?a=1&b=2")
        assert a == b


class TestNormalizeTitle:
    def test_lowercases(self):
        assert normalize_title("NEET 청년 급증") == normalize_title("neet 청년 급증")

    def test_removes_extra_whitespace(self):
        assert normalize_title("니트족  청년") == normalize_title("니트족 청년")

    def test_strips_separators(self):
        t = normalize_title("니트족 | 청년 실업")
        assert "|" not in t

    def test_normalizes_unicode(self):
        # NFC 정규화가 동일한 결과를 만들어야 함
        import unicodedata
        title = "니트족"
        assert normalize_title(unicodedata.normalize("NFD", title)) == normalize_title(
            unicodedata.normalize("NFC", title)
        )


class TestTitleSimilarity:
    def test_identical_titles(self):
        assert title_similarity("니트족 청년 급증", "니트족 청년 급증") == 1.0

    def test_completely_different(self):
        sim = title_similarity("니트족 청년 급증", "패션 스웨터 가디건")
        assert sim == 0.0

    def test_partial_overlap(self):
        sim = title_similarity("니트족 청년 문제 심각", "청년 실업 문제 심각")
        assert 0.0 < sim < 1.0

    def test_empty_strings(self):
        assert title_similarity("", "") == 1.0

    def test_one_empty(self):
        assert title_similarity("니트족", "") == 0.0


class TestUrlHash:
    def test_same_url_same_hash(self):
        assert url_hash("https://example.com/a") == url_hash("https://example.com/a")

    def test_different_url_different_hash(self):
        assert url_hash("https://example.com/a") != url_hash("https://example.com/b")

    def test_normalized_urls_same_hash(self):
        a = url_hash("https://www.example.com/article/?utm_source=x")
        b = url_hash("https://example.com/article")
        assert a == b


class TestDuplicateChecker:
    def test_new_url_not_duplicate(self):
        checker = DuplicateChecker()
        assert not checker.is_duplicate("https://example.com/a", "니트족 기사 제목")

    def test_same_url_is_duplicate(self):
        checker = DuplicateChecker()
        checker.mark_seen("https://example.com/a", "니트족 기사 제목")
        assert checker.is_duplicate("https://example.com/a", "다른 제목")

    def test_similar_title_is_duplicate(self):
        checker = DuplicateChecker(similarity_threshold=0.8)
        checker.mark_seen("https://example.com/a", "니트족 청년 급증 문제 심각")
        # 단어가 거의 같은 제목
        assert checker.is_duplicate("https://example.com/b", "니트족 청년 급증 문제 심각")

    def test_different_title_not_duplicate(self):
        checker = DuplicateChecker()
        checker.mark_seen("https://example.com/a", "니트족 청년 급증")
        assert not checker.is_duplicate("https://example.com/b", "청년 취업 지원 정책 발표")

    def test_mark_seen_registers_url(self):
        checker = DuplicateChecker()
        checker.mark_seen("https://example.com/a", "제목A")
        assert checker.is_duplicate("https://www.example.com/a/", "전혀 다른 제목")
