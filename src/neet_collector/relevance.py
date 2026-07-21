"""관련도 점수 계산 및 필터링 모듈."""

from __future__ import annotations

import re

from .config import KeywordsConfig

# 강한 키워드 점수
STRONG_SCORE = 40
# 보조 키워드 점수
WEAK_SCORE = 15
# 제외 키워드 감점
EXCLUDE_PENALTY = 60


def _normalize(text: str) -> str:
    """공백 정규화 및 소문자 변환."""
    return re.sub(r"\s+", " ", text).strip().lower()


def score(title: str, body: str, keywords: KeywordsConfig) -> int:
    """제목과 본문에서 관련도 점수(0~100)를 계산한다.

    Args:
        title: 기사 제목
        body: 기사 본문 또는 요약
        keywords: 키워드 설정

    Returns:
        0~100 사이의 정수 점수 (높을수록 관련도 높음)
    """
    combined = _normalize(f"{title} {body}")

    total = 0

    for kw in keywords.strong:
        if _normalize(kw) in combined:
            total += STRONG_SCORE

    for kw in keywords.weak:
        if _normalize(kw) in combined:
            total += WEAK_SCORE

    for kw in keywords.exclude:
        if _normalize(kw) in combined:
            total -= EXCLUDE_PENALTY

    # 제목에 강한 키워드가 있으면 보너스
    title_norm = _normalize(title)
    for kw in keywords.strong:
        if _normalize(kw) in title_norm:
            total += 20

    return max(0, min(100, total))


def is_relevant(title: str, body: str, keywords: KeywordsConfig, threshold: int = 30) -> bool:
    """주어진 임계값 이상이면 관련 기사로 판단한다."""
    return score(title, body, keywords) >= threshold
