"""CSV 및 JSON 내보내기 모듈."""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

from .database import Database

logger = logging.getLogger(__name__)

# 내보낼 필드 순서
_FIELDS = [
    "id",
    "title",
    "url",
    "source",
    "published_at",
    "body",
    "image_url",
    "collected_at",
    "relevance_score",
    "ai_summary",
    "ai_tags",
    "ai_sentiment",
]


def export_csv(db: Database, output_path: str, limit: int | None = None) -> int:
    """기사를 CSV 파일로 내보낸다. 저장된 건수를 반환한다."""
    rows = db.all_articles(limit=limit)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in _FIELDS})

    logger.info("CSV 내보내기 완료: %s (%d건)", output_path, len(rows))
    return len(rows)


def export_json(db: Database, output_path: str, limit: int | None = None) -> int:
    """기사를 JSON 파일로 내보낸다. 저장된 건수를 반환한다."""
    rows = db.all_articles(limit=limit)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cleaned = [{k: row.get(k) for k in _FIELDS} for row in rows]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    logger.info("JSON 내보내기 완료: %s (%d건)", output_path, len(rows))
    return len(rows)
