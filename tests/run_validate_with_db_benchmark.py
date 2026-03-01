# -*- coding: utf-8 -*-
"""
Run all issue_sql queries from postgresql_full.jsonl through validate_with_db
using live Docker PostgreSQL databases.

Prerequisites:
    1. Start Docker containers:
       cd benchmark && docker-compose up -d
    2. Wait for databases to be healthy:
       docker exec sequel2sql_postgresql pg_isready -U root

Usage:
    cd sequel2sql
    uv run python tests/run_validate_with_db_benchmark.py

Outputs:
    tests/output/validate_with_db_benchmark_results.json
    tests/output/validate_with_db_benchmark_errors_only.json
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add src to path so ast_parsers is importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from ast_parsers.validator import validate_with_db, invalidate_schema_cache
from ast_parsers.result import ValidationResult

# ─── Docker PostgreSQL connection config ─────────────────────────────────────
# These match benchmark/docker-compose.yml
PG_USER = "root"
PG_PASSWORD = "123123"
PG_HOST = "localhost"  # Docker maps container port to host
PG_PORT = 5433         # docker-compose maps 5433 -> 5432
DB_TEMPLATE_SUFFIX = "_template"

# ─── Engine cache ────────────────────────────────────────────────────────────
_engine_cache: Dict[str, Engine] = {}


def get_engine(db_name: str) -> Engine:
    """Get or create a SQLAlchemy engine for the given database."""
    if db_name not in _engine_cache:
        url = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{db_name}"
        _engine_cache[db_name] = create_engine(url, pool_size=3, max_overflow=5)
    return _engine_cache[db_name]


def check_db_exists(db_name: str) -> bool:
    """Check if a database exists on the PostgreSQL server."""
    try:
        engine = get_engine("postgres")
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name},
            )
            return result.fetchone() is not None
    except Exception as e:
        print(f"  ⚠ Could not check database '{db_name}': {e}")
        return False


def run_preprocess_sql(db_name: str, preprocess_sqls: List[str]) -> bool:
    """Run preprocess SQL statements on the given database. Returns True on success."""
    if not preprocess_sqls:
        return True
    try:
        engine = get_engine(db_name)
        with engine.connect() as conn:
            for sql_stmt in preprocess_sqls:
                if not sql_stmt or not sql_stmt.strip():
                    continue
                try:
                    conn.execute(text(sql_stmt))
                except Exception as e:
                    # Some preprocess SQL may fail (e.g. DROP IF EXISTS on non-existing)
                    # That's generally fine — continue with the rest
                    pass
            conn.commit()
        return True
    except Exception as e:
        return False


def run_cleanup_sql(db_name: str, cleanup_sqls: List[str]) -> None:
    """Run cleanup SQL statements to restore DB state."""
    if not cleanup_sqls:
        return
    try:
        engine = get_engine(db_name)
        with engine.connect() as conn:
            for sql_stmt in cleanup_sqls:
                if not sql_stmt or not sql_stmt.strip():
                    continue
                try:
                    conn.execute(text(sql_stmt))
                except Exception:
                    pass
            conn.commit()
    except Exception:
        pass


def check_docker_connection() -> bool:
    """Verify we can connect to the Docker PostgreSQL instance."""
    try:
        engine = get_engine("postgres")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("✓ Connected to Docker PostgreSQL")
        return True
    except Exception as e:
        print(f"✗ Cannot connect to Docker PostgreSQL at {PG_HOST}:{PG_PORT}")
        print(f"  Error: {e}")
        print(f"\n  Please start Docker containers first:")
        print(f"    cd benchmark && docker-compose up -d")
        print(f"    # Wait for healthy status, then retry")
        return False


# ─── Main runner ─────────────────────────────────────────────────────────────


def run_benchmark(
    data_path: str,
    output_path: str,
    limit: Optional[int] = None,
) -> None:
    """Run all issue_sql queries through validate_with_db with live DB."""

    # Check Docker connection first
    if not check_docker_connection():
        sys.exit(1)

    # Load data
    print(f"Loading data from {data_path}...")
    with open(data_path, "r") as f:
        entries = [json.loads(line) for line in f]

    if limit:
        entries = entries[:limit]

    # Get unique db_ids and check which template databases exist
    db_ids = sorted(set(e["db_id"] for e in entries))
    print(f"Loaded {len(entries)} entries across {len(db_ids)} databases")

    available_dbs: Dict[str, str] = {}  # db_id -> actual db name to connect to
    for db_id in db_ids:
        # Prefer the real (writable) database — templates are read-only
        if check_db_exists(db_id):
            available_dbs[db_id] = db_id
            print(f"  ✓ {db_id} -> {db_id}")
        else:
            template_name = f"{db_id}{DB_TEMPLATE_SUFFIX}"
            if check_db_exists(template_name):
                available_dbs[db_id] = template_name
                print(f"  ✓ {db_id} -> {template_name} (template, read-only)")
            else:
                print(f"  ✗ {db_id} -> NOT FOUND (skipping)")

    print(f"\nAvailable databases: {len(available_dbs)}/{len(db_ids)}")
    if not available_dbs:
        print("No databases available! Exiting.")
        sys.exit(1)

    # Run validation
    results: List[dict] = []
    error_count = 0
    valid_count = 0
    skip_count = 0
    exception_count = 0

    for i, entry in enumerate(entries):
        instance_id = entry.get("instance_id", f"entry_{i}")
        db_id = entry["db_id"]
        category = entry.get("category", "unknown")
        issue_sqls = entry.get("issue_sql", [])
        preprocess_sqls = entry.get("preprocess_sql", [])
        cleanup_sqls = entry.get("clean_up_sql", [])

        # Skip multi-query entries (16 entries have >1 issue_sql)
        if len(issue_sqls) > 1:
            continue

        if db_id not in available_dbs:
            skip_count += len(issue_sqls) if issue_sqls else 1
            continue

        actual_db = available_dbs[db_id]

        # Run preprocess SQL if any
        run_preprocess_sql(actual_db, preprocess_sqls)

        # Invalidate live schema cache after preprocess_sql may have created
        # new tables — forces re-reflection on the next validate_with_db call
        if preprocess_sqls:
            invalidate_schema_cache(get_engine(actual_db))

        for sql_idx, sql in enumerate(issue_sqls):
            if not sql or not sql.strip():
                continue

            try:
                engine = get_engine(actual_db)
                result = validate_with_db(sql, engine)
            except Exception as exc:
                exception_count += 1
                results.append({
                    "instance_id": instance_id,
                    "db_id": db_id,
                    "category": category,
                    "sql_index": sql_idx,
                    "sql": sql[:500],
                    "valid": None,
                    "exception": str(exc)[:200],
                    "errors": [],
                    "tags": [],
                })
                continue

            if result.valid:
                valid_count += 1
            else:
                error_count += 1

            entry_result = {
                "instance_id": instance_id,
                "db_id": db_id,
                "category": category,
                "sql_index": sql_idx,
                "sql": sql[:500],
                "valid": result.valid,
                "errors": [e.to_dict() for e in result.errors],
                "tags": [t.value for t in result.tags],
            }

            if result.query_metadata:
                entry_result["query_metadata"] = result.query_metadata.to_dict()

            results.append(entry_result)

        # Run cleanup SQL to restore DB state
        run_cleanup_sql(actual_db, cleanup_sqls)

        # Progress
        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(entries)} entries...")

    # ── Summary stats ────────────────────────────────────────────────────────
    total = valid_count + error_count + exception_count
    print(f"\n{'='*60}")
    print(f"VALIDATE_WITH_DB BENCHMARK RESULTS")
    print(f"{'='*60}")
    print(f"Total SQL queries:        {total}")
    print(f"  Valid (no errors):      {valid_count}")
    print(f"  Invalid (has errors):   {error_count}")
    print(f"  Exceptions:             {exception_count}")
    print(f"  Skipped (no DB):        {skip_count}")
    print(f"{'='*60}")

    # Error breakdown by tag
    tag_counts: Dict[str, int] = {}
    for r in results:
        for tag in r.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    if tag_counts:
        print(f"\nError Tag Distribution:")
        for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
            print(f"  {tag:45s} {count:>4d}")

    # Per-database breakdown
    db_error_counts: Dict[str, List[int]] = {}
    for r in results:
        db = r["db_id"]
        if db not in db_error_counts:
            db_error_counts[db] = [0, 0]
        if r.get("valid") is True:
            db_error_counts[db][0] += 1
        elif r.get("valid") is False:
            db_error_counts[db][1] += 1

    print(f"\nPer-Database Breakdown:")
    print(f"  {'Database':<35s} {'Valid':>6s} {'Invalid':>8s}")
    print(f"  {'-'*35} {'-'*6} {'-'*8}")
    for db in sorted(db_error_counts.keys()):
        v, inv = db_error_counts[db]
        print(f"  {db:<35s} {v:>6d} {inv:>8d}")

    # Per-category breakdown
    cat_counts: Dict[str, List[int]] = {}
    for r in results:
        cat = r.get("category", "unknown")
        if cat not in cat_counts:
            cat_counts[cat] = [0, 0]
        if r.get("valid") is True:
            cat_counts[cat][0] += 1
        elif r.get("valid") is False:
            cat_counts[cat][1] += 1

    print(f"\nPer-Category Breakdown:")
    print(f"  {'Category':<25s} {'Valid':>6s} {'Invalid':>8s}")
    print(f"  {'-'*25} {'-'*6} {'-'*8}")
    for cat in sorted(cat_counts.keys()):
        v, inv = cat_counts[cat]
        print(f"  {cat:<25s} {v:>6d} {inv:>8d}")

    # ── Comparison with static validation ────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"COMPARISON: Static validate() vs validate_with_db()")
    print(f"{'='*60}")
    print(f"{'Metric':<30s} {'Static':>10s} {'With DB':>10s}")
    print(f"{'-'*30} {'-'*10} {'-'*10}")

    # Load static results if they exist
    static_path = output_path.replace("validate_with_db_", "validator_")
    if os.path.exists(static_path):
        with open(static_path) as f:
            static_data = json.load(f)
        s = static_data["summary"]
        print(f"{'Valid queries':<30s} {s['valid']:>10d} {valid_count:>10d}")
        print(f"{'Invalid queries':<30s} {s['invalid']:>10d} {error_count:>10d}")

        static_tags = s.get("tag_distribution", {})
        all_tags = sorted(set(list(static_tags.keys()) + list(tag_counts.keys())))
        print(f"\n{'Tag':<45s} {'Static':>8s} {'With DB':>8s} {'Δ':>6s}")
        print(f"{'-'*45} {'-'*8} {'-'*8} {'-'*6}")
        for tag in all_tags:
            sc = static_tags.get(tag, 0)
            dc = tag_counts.get(tag, 0)
            delta = dc - sc
            sign = "+" if delta > 0 else ""
            print(f"  {tag:<43s} {sc:>8d} {dc:>8d} {sign}{delta:>5d}")
    else:
        print(f"  (Static results not found at {static_path} — run run_validator_benchmark.py first)")

    # ── Save full results ────────────────────────────────────────────────────
    output = {
        "summary": {
            "total_queries": total,
            "valid": valid_count,
            "invalid": error_count,
            "exceptions": exception_count,
            "skipped": skip_count,
            "tag_distribution": tag_counts,
            "per_database": {
                db: {"valid": v, "invalid": inv}
                for db, (v, inv) in db_error_counts.items()
            },
            "per_category": {
                cat: {"valid": v, "invalid": inv}
                for cat, (v, inv) in cat_counts.items()
            },
        },
        "results": results,
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\nFull results saved to: {output_path}")

    # Save errors-only
    error_results = [r for r in results if r.get("valid") is False]
    error_output_path = output_path.replace(".json", "_errors_only.json")
    with open(error_output_path, "w") as f:
        json.dump(error_results, f, indent=2, default=str)

    print(f"Errors-only file saved to: {error_output_path}")
    print(f"({len(error_results)} entries with errors)")


if __name__ == "__main__":
    data_file = str(ROOT / "benchmark" / "data" / "postgresql_full.jsonl")
    output_file = str(ROOT / "tests" / "output" / "validate_with_db_benchmark_results.json")

    run_benchmark(data_file, output_file)
