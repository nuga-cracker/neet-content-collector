"""URL 정규화 및 제목 기반 중복 제거 모듈."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def normalize_url(url: str) -> str:
    """URL을 정규화하여 중복 감지에 사용할 키를 반환한다.

    - 스킴을 https로 통일
    - 쿼리 파라미터 정렬
    - 단편(fragment) 제거
    - 끝의 슬래시 제거
    """
    try:
        parsed = urlparse(url.strip())
        scheme = "https"
        netloc = parsed.netloc.lower().removeprefix("www.")
        path = parsed.path.rstrip("/")
        # 불필요한 추적 파라미터 제거
        _tracking = {
            "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
            "fbclid", "gclid", "ref", "from", "source",
        }
        qs = parse_qs(parsed.query, keep_blank_values=False)
        qs_clean = {k: v for k, v in qs.items() if k.lower() not in _tracking}
        query = urlencode(sorted(qs_clean.items()), doseq=True)
        return urlunparse((scheme, netloc, path, "", query, ""))
    except Exception:
        return url.strip()


def normalize_title(title: str) -> str:
    """제목을 소문자·공백 정규화하여 유사 제목 비교에 사용한다."""
    text = unicodedata.normalize("NFC", title)
    text = re.sub(r"[\s\-_·|＋]+", " ", text).strip().lower()
    # 특수문자 제거 (알파벳, 숫자, 한글, 공백 유지)
    text = re.sub(r"[^\w\s가-힣]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def url_hash(url: str) -> str:
    """정규화된 URL의 SHA-256 해시를 반환한다."""
    return hashlib.sha256(normalize_url(url).encode()).hexdigest()


def content_hash(title: str, body: str) -> str:
    """제목+본문의 SHA-256 해시를 반환한다."""
    combined = f"{normalize_title(title)}||{body[:500]}"
    return hashlib.sha256(combined.encode()).hexdigest()


def title_similarity(a: str, b: str) -> float:
    """두 제목의 단어 집합 기반 자카드 유사도(0~1)를 반환한다."""
    words_a = set(normalize_title(a).split())
    words_b = set(normalize_title(b).split())
    if not words_a and not words_b:
        return 1.0
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


class DuplicateChecker:
    """메모리 내 중복 체크 (수집 세션 동안 사용)."""

    def __init__(self, similarity_threshold: float = 0.85) -> None:
        self._seen_urls: set[str] = set()
        self._seen_titles: list[str] = []
        self._similarity_threshold = similarity_threshold

    def is_duplicate(self, url: str, title: str) -> bool:
        """URL 또는 제목이 이전에 처리된 항목과 중복이면 True를 반환한다."""
        norm_url = normalize_url(url)
        if norm_url in self._seen_urls:
            return True

        norm_title = normalize_title(title)
        for seen_title in self._seen_titles:
            if title_similarity(norm_title, seen_title) >= self._similarity_threshold:
                return True

        return False

    def mark_seen(self, url: str, title: str) -> None:
        """URL과 제목을 '처리 완료'로 등록한다."""
        self._seen_urls.add(normalize_url(url))
        self._seen_titles.append(normalize_title(title))
