"""수집기 파싱 로직 단위 테스트."""

from __future__ import annotations

import textwrap
from unittest.mock import MagicMock, patch

import pytest

from neet_collector.collector import (
    _extract_body,
    _extract_image,
    _parse_date,
)


def _make_entry(**kwargs) -> MagicMock:
    """feedparser Entry 흉내를 내는 MagicMock을 반환한다."""
    entry = MagicMock()
    entry.__contains__ = lambda self, key: key in kwargs
    entry.get = lambda key, default=None: kwargs.get(key, default)
    for k, v in kwargs.items():
        setattr(entry, k, v)
    return entry


class TestParseDate:
    def test_published_parsed(self):
        entry = _make_entry(published_parsed=(2024, 3, 15, 10, 30, 0, 4, 75, 0))
        result = _parse_date(entry)
        assert result is not None
        assert "2024-03-15" in result

    def test_fallback_to_updated_parsed(self):
        entry = _make_entry(
            published_parsed=None,
            updated_parsed=(2024, 6, 1, 0, 0, 0, 5, 153, 0),
        )
        result = _parse_date(entry)
        assert result is not None
        assert "2024-06-01" in result

    def test_no_date_returns_none(self):
        entry = _make_entry(published_parsed=None, updated_parsed=None)
        result = _parse_date(entry)
        assert result is None


class TestExtractBody:
    def test_extracts_from_summary(self):
        entry = _make_entry(
            content=[],
            summary="<p>니트족 청년이 급증하고 있다.</p>",
        )
        body = _extract_body(entry)
        assert "니트족" in body
        assert "<p>" not in body  # HTML 태그 제거 확인

    def test_extracts_from_content_first(self):
        entry = _make_entry(
            content=[{"value": "<p>콘텐츠 본문: 청년 무업자 증가</p>"}],
            summary="요약문",
        )
        body = _extract_body(entry)
        assert "청년 무업자" in body

    def test_truncates_long_body(self):
        entry = _make_entry(
            content=[],
            summary="A" * 3000,
        )
        body = _extract_body(entry)
        assert len(body) <= 2000

    def test_empty_entry_returns_empty_string(self):
        entry = _make_entry(content=[], summary="")
        body = _extract_body(entry)
        assert body == ""


class TestExtractImage:
    def test_extracts_from_media_thumbnail(self):
        entry = _make_entry(
            media_thumbnail=[{"url": "https://example.com/image.jpg"}],
            media_content=[],
            enclosures=[],
            summary="",
        )
        img = _extract_image(entry)
        assert img == "https://example.com/image.jpg"

    def test_extracts_from_summary_img_tag(self):
        entry = _make_entry(
            media_thumbnail=None,
            media_content=[],
            enclosures=[],
            summary='<img src="https://example.com/thumb.png" />',
        )
        img = _extract_image(entry)
        assert img == "https://example.com/thumb.png"

    def test_returns_none_when_no_image(self):
        entry = _make_entry(
            media_thumbnail=None,
            media_content=[],
            enclosures=[],
            summary="텍스트만 있는 요약",
        )
        img = _extract_image(entry)
        assert img is None
