"""CLI 진입점.

사용 예:
    python -m neet_collector collect
    python -m neet_collector collect --no-ai
    python -m neet_collector export --format csv --output data/articles.csv
    python -m neet_collector export --format json
    python -m neet_collector stats
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from .ai_analysis import analyze
from .collector import collect_all
from .config import load_config
from .database import Database
from .exporter import export_csv, export_json


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=level,
    )


def cmd_collect(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    db = Database(config.database.path)

    articles = collect_all(config)
    new_count = 0
    skipped = 0

    for article in articles:
        if db.url_hash_exists(article.url_hash or ""):
            skipped += 1
            continue

        # AI 분석 (선택)
        if not args.no_ai and config.ai.enabled:
            result = analyze(article.title, article.body, model=config.ai.model)
            if result:
                article.ai_summary = result["summary"]
                article.ai_tags = json.dumps(result["tags"], ensure_ascii=False)
                article.ai_sentiment = result["sentiment"]

        row_id = db.insert(article)
        if row_id is not None:
            new_count += 1
        else:
            skipped += 1

    print(f"✅ 수집 완료: 신규 {new_count}건, 중복 스킵 {skipped}건 (DB 총 {db.count()}건)")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    db = Database(config.database.path)

    fmt = args.format.lower()
    output = args.output

    if fmt == "csv":
        output = output or config.export.default_csv
        n = export_csv(db, output, limit=args.limit)
    elif fmt == "json":
        output = output or config.export.default_json
        n = export_json(db, output, limit=args.limit)
    else:
        print(f"❌ 지원하지 않는 형식: {fmt} (csv 또는 json)")
        return 1

    print(f"✅ {fmt.upper()} 내보내기 완료: {output} ({n}건)")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    db = Database(config.database.path)
    rows = db.all_articles(limit=5)
    total = db.count()
    print(f"📊 저장된 기사 수: {total}건")
    if rows:
        print("\n최근 5건:")
        for r in rows:
            print(f"  [{r['relevance_score']:3d}점] {r['title'][:60]}")
            print(f"         출처: {r['source']} | {r['published_at'] or '날짜 미상'}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m neet_collector",
        description="니트족(NEET) 관련 기사·콘텐츠 자동 수집기",
    )
    parser.add_argument("--config", default=None, help="설정 파일 경로 (기본값: config.yaml)")
    parser.add_argument("--verbose", "-v", action="store_true", help="디버그 로그 출력")
    sub = parser.add_subparsers(dest="command", required=True)

    # collect
    p_collect = sub.add_parser("collect", help="RSS 피드에서 기사를 수집합니다")
    p_collect.add_argument(
        "--no-ai", action="store_true", help="AI 분석을 건너뜁니다"
    )
    p_collect.set_defaults(func=cmd_collect)

    # export
    p_export = sub.add_parser("export", help="DB에서 파일로 내보냅니다")
    p_export.add_argument(
        "--format", "-f", default="csv", choices=["csv", "json"], help="출력 형식"
    )
    p_export.add_argument("--output", "-o", default=None, help="출력 파일 경로")
    p_export.add_argument("--limit", "-l", type=int, default=None, help="내보낼 최대 건수")
    p_export.set_defaults(func=cmd_export)

    # stats
    p_stats = sub.add_parser("stats", help="수집 통계를 출력합니다")
    p_stats.set_defaults(func=cmd_stats)

    args = parser.parse_args()
    _setup_logging(args.verbose)

    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
