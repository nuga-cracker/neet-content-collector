"""SQLite 영속 저장소 모듈."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, Optional


@dataclass
class Article:
    """수집된 기사 데이터 모델."""

    title: str
    url: str
    source: str
    published_at: Optional[str] = None
    body: str = ""
    image_url: Optional[str] = None
    collected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    relevance_score: int = 0
    # AI 분석 결과 (선택)
    ai_summary: Optional[str] = None
    ai_tags: Optional[str] = None        # JSON 배열 문자열
    ai_sentiment: Optional[str] = None  # positive / neutral / negative
    # 내부 필드
    url_hash: Optional[str] = None
    content_hash: Optional[str] = None

    @property
    def id(self) -> Optional[int]:
        return getattr(self, "_id", None)


_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS articles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    url             TEXT    NOT NULL UNIQUE,
    url_hash        TEXT    NOT NULL,
    content_hash    TEXT,
    title           TEXT    NOT NULL,
    body            TEXT,
    source          TEXT,
    published_at    TEXT,
    image_url       TEXT,
    collected_at    TEXT    NOT NULL,
    relevance_score INTEGER DEFAULT 0,
    ai_summary      TEXT,
    ai_tags         TEXT,
    ai_sentiment    TEXT
)
"""

_CREATE_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_url_hash ON articles(url_hash);
"""


class Database:
    """SQLite 래퍼."""

    def __init__(self, db_path: str = "data/neet_articles.db") -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _init(self) -> None:
        with self._conn() as conn:
            conn.execute(_CREATE_TABLE)
            conn.execute(_CREATE_INDEX)

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def url_exists(self, url: str) -> bool:
        """URL이 이미 저장돼 있으면 True를 반환한다."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM articles WHERE url = ? LIMIT 1", (url,)
            ).fetchone()
        return row is not None

    def url_hash_exists(self, url_hash: str) -> bool:
        """url_hash가 이미 저장돼 있으면 True를 반환한다."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM articles WHERE url_hash = ? LIMIT 1", (url_hash,)
            ).fetchone()
        return row is not None

    def insert(self, article: Article) -> Optional[int]:
        """기사를 DB에 삽입한다. URL 중복 시 None을 반환한다."""
        sql = """
        INSERT OR IGNORE INTO articles
            (url, url_hash, content_hash, title, body, source, published_at,
             image_url, collected_at, relevance_score,
             ai_summary, ai_tags, ai_sentiment)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self._conn() as conn:
            cur = conn.execute(
                sql,
                (
                    article.url,
                    article.url_hash,
                    article.content_hash,
                    article.title,
                    article.body,
                    article.source,
                    article.published_at,
                    article.image_url,
                    article.collected_at,
                    article.relevance_score,
                    article.ai_summary,
                    article.ai_tags,
                    article.ai_sentiment,
                ),
            )
            return cur.lastrowid if cur.rowcount > 0 else None

    def update_ai(self, url: str, summary: str, tags: str, sentiment: str) -> None:
        """AI 분석 결과를 기존 기사에 업데이트한다."""
        with self._conn() as conn:
            conn.execute(
                """UPDATE articles
                   SET ai_summary = ?, ai_tags = ?, ai_sentiment = ?
                   WHERE url = ?""",
                (summary, tags, sentiment, url),
            )

    def all_articles(self, limit: Optional[int] = None) -> list[dict]:
        """모든 기사를 dict 리스트로 반환한다."""
        sql = "SELECT * FROM articles ORDER BY collected_at DESC"
        if limit:
            sql += f" LIMIT {int(limit)}"
        with self._conn() as conn:
            rows = conn.execute(sql).fetchall()
        return [dict(r) for r in rows]

    def count(self) -> int:
        """저장된 기사 수를 반환한다."""
        with self._conn() as conn:
            row = conn.execute("SELECT COUNT(*) FROM articles").fetchone()
        return row[0] if row else 0
