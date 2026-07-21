"""설정 로더 – config.yaml 과 환경변수를 합쳐 하나의 Config 객체로 반환한다."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()


@dataclass
class HttpConfig:
    timeout: int = 20
    user_agent: str = (
        "NeetContentCollector/0.1 "
        "(github.com/nuga-cracker/neet-content-collector; educational research)"
    )


@dataclass
class KeywordsConfig:
    strong: list[str] = field(default_factory=list)
    weak: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)


@dataclass
class FeedConfig:
    name: str
    url: str


@dataclass
class DatabaseConfig:
    path: str = "data/neet_articles.db"


@dataclass
class AiConfig:
    model: str = "gpt-4o-mini"
    enabled: bool = True


@dataclass
class ExportConfig:
    default_csv: str = "data/articles.csv"
    default_json: str = "data/articles.json"


@dataclass
class Config:
    relevance_threshold: int = 30
    feeds: list[FeedConfig] = field(default_factory=list)
    keywords: KeywordsConfig = field(default_factory=KeywordsConfig)
    http: HttpConfig = field(default_factory=HttpConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    ai: AiConfig = field(default_factory=AiConfig)
    export: ExportConfig = field(default_factory=ExportConfig)


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """두 dict를 재귀적으로 합친다. override 값이 우선한다."""
    result = base.copy()
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _merge(result[k], v)
        else:
            result[k] = v
    return result


def load_config(path: str | None = None) -> Config:
    """설정 파일을 읽어 Config 객체를 반환한다.

    우선순위: 환경변수 > config.yaml > 기본값
    """
    config_path = path or os.getenv("NEET_CONFIG", "config.yaml")
    raw: dict[str, Any] = {}

    if Path(config_path).exists():
        with open(config_path, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

    # 환경변수 오버라이드
    db_path = os.getenv("NEET_DB_PATH")
    if db_path:
        raw.setdefault("database", {})["path"] = db_path

    ai_model = os.getenv("OPENAI_MODEL")
    if ai_model:
        raw.setdefault("ai", {})["model"] = ai_model

    # --- 파싱 ---
    keywords_raw = raw.get("keywords", {})
    keywords = KeywordsConfig(
        strong=keywords_raw.get("strong", []),
        weak=keywords_raw.get("weak", []),
        exclude=keywords_raw.get("exclude", []),
    )

    feeds_raw = raw.get("feeds", [])
    feeds = [FeedConfig(name=f["name"], url=f["url"]) for f in feeds_raw]

    http_raw = raw.get("http", {})
    http = HttpConfig(
        timeout=http_raw.get("timeout", 20),
        user_agent=http_raw.get("user_agent", HttpConfig.user_agent),
    )

    db_raw = raw.get("database", {})
    database = DatabaseConfig(path=db_raw.get("path", "data/neet_articles.db"))

    ai_raw = raw.get("ai", {})
    ai = AiConfig(
        model=ai_raw.get("model", "gpt-4o-mini"),
        enabled=ai_raw.get("enabled", True),
    )

    export_raw = raw.get("export", {})
    export = ExportConfig(
        default_csv=export_raw.get("default_csv", "data/articles.csv"),
        default_json=export_raw.get("default_json", "data/articles.json"),
    )

    return Config(
        relevance_threshold=int(raw.get("relevance_threshold", 30)),
        feeds=feeds,
        keywords=keywords,
        http=http,
        database=database,
        ai=ai,
        export=export,
    )
