"""설정 로더 단위 테스트."""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest

from neet_collector.config import load_config


def _write_config(tmp_path: Path, content: str) -> str:
    p = tmp_path / "config.yaml"
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return str(p)


class TestLoadConfig:
    def test_loads_defaults_without_file(self, tmp_path):
        cfg = load_config(str(tmp_path / "nonexistent.yaml"))
        assert cfg.relevance_threshold == 30
        assert cfg.feeds == []
        assert cfg.ai.model == "gpt-4o-mini"

    def test_loads_keywords_from_yaml(self, tmp_path):
        path = _write_config(
            tmp_path,
            """
            keywords:
              strong: ["니트족", "NEET"]
              weak: ["청년 실업"]
              exclude: ["니트웨어"]
            """,
        )
        cfg = load_config(path)
        assert "니트족" in cfg.keywords.strong
        assert "NEET" in cfg.keywords.strong
        assert "청년 실업" in cfg.keywords.weak
        assert "니트웨어" in cfg.keywords.exclude

    def test_loads_feeds_from_yaml(self, tmp_path):
        path = _write_config(
            tmp_path,
            """
            feeds:
              - name: "테스트 피드"
                url: "https://example.com/rss"
            """,
        )
        cfg = load_config(path)
        assert len(cfg.feeds) == 1
        assert cfg.feeds[0].name == "테스트 피드"
        assert cfg.feeds[0].url == "https://example.com/rss"

    def test_env_overrides_db_path(self, tmp_path, monkeypatch):
        monkeypatch.setenv("NEET_DB_PATH", "/tmp/test.db")
        cfg = load_config(str(tmp_path / "nonexistent.yaml"))
        assert cfg.database.path == "/tmp/test.db"

    def test_env_overrides_model(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
        cfg = load_config(str(tmp_path / "nonexistent.yaml"))
        assert cfg.ai.model == "gpt-4o"

    def test_relevance_threshold_loaded(self, tmp_path):
        path = _write_config(tmp_path, "relevance_threshold: 50\n")
        cfg = load_config(path)
        assert cfg.relevance_threshold == 50
