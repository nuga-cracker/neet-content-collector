"""RSS 피드 수집 모듈."""

from __future__ import annotations

import logging
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional

import feedparser
import requests
from bs4 import BeautifulSoup

from .config import Config, FeedConfig
from .database import Article
from .deduplication import content_hash, url_hash
from .relevance import is_relevant, score

logger = logging.getLogger(__name__)


def _parse_date(entry: feedparser.FeedParserDict) -> Optional[str]:
    """피드 항목에서 발행일을 ISO 8601 문자열로 파싱한다."""
    # feedparser가 파싱한 struct_time 사용
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6]).isoformat()
        except Exception:
            pass
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        try:
            return datetime(*entry.updated_parsed[:6]).isoformat()
        except Exception:
            pass
    # 문자열로 직접 파싱
    for attr in ("published", "updated"):
        val = entry.get(attr, "")
        if val:
            try:
                return parsedate_to_datetime(val).isoformat()
            except Exception:
                return val
    return None


def _extract_image(entry: feedparser.FeedParserDict) -> Optional[str]:
    """피드 항목에서 대표 이미지 URL을 추출한다."""
    # media:thumbnail / media:content
    media = entry.get("media_thumbnail") or entry.get("media_content", [])
    if media and isinstance(media, list) and media[0].get("url"):
        return media[0]["url"]
    # <enclosure>
    if entry.get("enclosures"):
        for enc in entry.enclosures:
            if enc.get("type", "").startswith("image"):
                return enc.get("href") or enc.get("url")
    # HTML 요약에서 <img> 파싱
    summary_html = entry.get("summary", "") or ""
    if "<img" in summary_html:
        try:
            soup = BeautifulSoup(summary_html, "lxml")
            img = soup.find("img")
            if img and img.get("src"):
                return img["src"]
        except Exception:
            pass
    return None


def _extract_body(entry: feedparser.FeedParserDict) -> str:
    """피드 항목에서 본문 텍스트를 추출한다."""
    content = entry.get("content", [])
    if content:
        raw = content[0].get("value", "")
        try:
            soup = BeautifulSoup(raw, "lxml")
            return soup.get_text(separator=" ", strip=True)[:2000]
        except Exception:
            return raw[:2000]
    summary = entry.get("summary", "") or ""
    try:
        soup = BeautifulSoup(summary, "lxml")
        return soup.get_text(separator=" ", strip=True)[:2000]
    except Exception:
        return summary[:2000]


def _source_from_feed(feed_config: FeedConfig, entry: feedparser.FeedParserDict) -> str:
    """출처 이름을 결정한다."""
    # 피드 메타데이터에서 출처 추출
    source_tags = entry.get("source", {})
    if source_tags and source_tags.get("title"):
        return source_tags["title"]
    return feed_config.name


def collect_feed(
    feed_config: FeedConfig,
    config: Config,
    seen_urls: Optional[set[str]] = None,
) -> list[Article]:
    """하나의 RSS 피드에서 기사 목록을 수집한다.

    Args:
        feed_config: 피드 이름과 URL
        config: 전체 설정
        seen_urls: 이번 세션에서 이미 처리한 URL 집합 (선택)

    Returns:
        관련도 필터를 통과한 Article 객체 목록
    """
    articles: list[Article] = []
    seen_urls = seen_urls or set()

    try:
        headers = {"User-Agent": config.http.user_agent}
        response = requests.get(
            feed_config.url,
            headers=headers,
            timeout=config.http.timeout,
        )
        response.raise_for_status()
        feed = feedparser.parse(response.content)
    except Exception as exc:
        logger.warning("피드 수집 실패 [%s]: %s", feed_config.name, exc)
        return articles

    if feed.bozo and not feed.entries:
        logger.warning("피드 파싱 오류 [%s]: %s", feed_config.name, feed.bozo_exception)
        return articles

    for entry in feed.entries:
        try:
            url = entry.get("link", "").strip()
            if not url:
                continue

            title = entry.get("title", "").strip()
            if not title:
                continue

            body = _extract_body(entry)
            rel_score = score(title, body, config.keywords)

            if rel_score < config.relevance_threshold:
                logger.debug("관련도 미달 스킵 (%d): %s", rel_score, title)
                continue

            u_hash = url_hash(url)
            c_hash = content_hash(title, body)

            if u_hash in seen_urls:
                logger.debug("세션 내 중복 스킵: %s", url)
                continue
            seen_urls.add(u_hash)

            article = Article(
                title=title,
                url=url,
                source=_source_from_feed(feed_config, entry),
                published_at=_parse_date(entry),
                body=body,
                image_url=_extract_image(entry),
                relevance_score=rel_score,
                url_hash=u_hash,
                content_hash=c_hash,
            )
            articles.append(article)
            logger.info("수집 [%d점]: %s", rel_score, title)

        except Exception as exc:
            logger.warning("항목 처리 실패 [%s]: %s", feed_config.name, exc)
            continue

    return articles


def collect_all(config: Config) -> list[Article]:
    """모든 피드에서 기사를 수집한다."""
    all_articles: list[Article] = []
    seen_urls: set[str] = set()

    for feed_config in config.feeds:
        logger.info("피드 수집 시작: %s", feed_config.name)
        articles = collect_feed(feed_config, config, seen_urls)
        all_articles.extend(articles)
        logger.info("피드 완료 [%s]: %d건", feed_config.name, len(articles))

    logger.info("전체 수집 완료: %d건", len(all_articles))
    return all_articles
