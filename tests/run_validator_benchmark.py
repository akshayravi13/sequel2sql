# -*- coding: utf-8 -*-
"""
Run all issue_sql queries from postgresql_full.jsonl through the validator.

Usage:
    cd sequel2sql
    uv run python tests/run_validator_benchmark.py

Outputs results to tests/output/validator_benchmark_results.json
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add src to path so ast_parsers is importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ast_parsers.validator import validate
from ast_parsers.result import ValidationResult


# ─── Schema parser ───────────────────────────────────────────────────────────


def parse_schema_from_ddl(ddl_text: str) -> Dict[str, Dict[str, str]]:
    """
    Parse CREATE TABLE statements from preprocess_schema text into
    {table_name: {column_name: column_type}} dict.

    Handles quoted identifiers, DEFAULT clauses, FOREIGN KEY, PRIMARY KEY, etc.
    Also catches CREATE TABLE AS SELECT, CREATE TEMP TABLE, IF NOT EXISTS, etc.
    """
    schema: Dict[str, Dict[str, str]] = {}

    # ── Pass 1: Full column parsing for standard CREATE TABLE (columns) ──────
    table_pattern = re.compile(
        r'CREATE\s+TABLE\s+"?(\w+)"?\s*\((.*?)\);',
        re.IGNORECASE | re.DOTALL,
    )

    for match in table_pattern.finditer(ddl_text):
        table_name = match.group(1)
        body = match.group(2)
        columns: Dict[str, str] = {}

        for line in body.split("\n"):
            line = line.strip().rstrip(",")
            if not line:
                continue
            # Skip constraint lines
            if re.match(
                r"^\s*(PRIMARY\s+KEY|FOREIGN\s+KEY|UNIQUE|CHECK|CONSTRAINT)",
                line,
                re.IGNORECASE,
            ):
                continue

            # Parse: "column_name" type_name ... or column_name type_name ...
            col_match = re.match(
                r'"?(\w+)"?\s+([a-zA-Z][\w\s()]*?)(?:\s+(?:NOT\s+NULL|NULL|DEFAULT|PRIMARY|UNIQUE|REFERENCES|CHECK)|\s*$)',
                line,
                re.IGNORECASE,
            )
            if col_match:
                col_name = col_match.group(1)
                col_type = col_match.group(2).strip()
                columns[col_name] = col_type

        if columns:
            schema[table_name] = columns

    # ── Pass 2: Broad catch-all for any CREATE TABLE variant ─────────────────
    # Catches: CREATE TABLE AS SELECT, CREATE TEMP TABLE, CREATE TABLE IF NOT
    # EXISTS, CREATE UNLOGGED TABLE, etc.  Registers the table name with an
    # empty column dict if not already parsed in pass 1.
    broad_pattern = re.compile(
        r'CREATE\s+(?:TEMP(?:ORARY)?\s+)?(?:UNLOGGED\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:"?(\w+)"?\.)?\"?(\w+)\"?',
        re.IGNORECASE,
    )
    for match in broad_pattern.finditer(ddl_text):
        table_name = match.group(2)  # group(1) is optional schema qualifier
        if table_name and table_name.lower() not in {k.lower() for k in schema}:
            schema[table_name] = {}

    # ── Pass 3: SELECT INTO creates a table too ──────────────────────────────
    select_into_pattern = re.compile(
        r"SELECT\s+.+?\s+INTO\s+(?:TEMP(?:ORARY)?\s+)?(?:TABLE\s+)?\"?(\w+)\"?",
        re.IGNORECASE | re.DOTALL,
    )
    for match in select_into_pattern.finditer(ddl_text):
        table_name = match.group(1)
        if table_name and table_name.lower() not in {k.lower() for k in schema}:
            schema[table_name] = {}

    return schema


# ─── Main runner ─────────────────────────────────────────────────────────────


def run_benchmark_validation(
    data_path: str,
    output_path: str,
    limit: Optional[int] = None,
) -> None:
    """Run all issue_sql queries through the validator and save results."""

    # Load data
    print(f"Loading data from {data_path}...")
    with open(data_path, "r") as f:
        entries = [json.loads(line) for line in f]

    if limit:
        entries = entries[:limit]

    print(
        f"Loaded {len(entries)} entries across {len(set(e['db_id'] for e in entries))} databases"
    )

    # Parse schemas per db_id (cache to avoid re-parsing)
    schema_cache: Dict[str, Dict[str, Dict[str, str]]] = {}

    results: List[dict] = []
    error_count = 0
    valid_count = 0
    parse_fail_count = 0

    for i, entry in enumerate(entries):
        instance_id = entry.get("instance_id", f"entry_{i}")
        db_id = entry["db_id"]
        category = entry.get("category", "unknown")
        issue_sqls = entry.get("issue_sql", [])

        # Skip multi-query entries (16 entries have >1 issue_sql)
        if len(issue_sqls) > 1:
            continue

        # Parse schema if not cached
        if db_id not in schema_cache:
            ddl = entry.get("preprocess_schema", "")
            schema_cache[db_id] = parse_schema_from_ddl(ddl)

        # Start with cached schema and merge tables from preprocess_sql
        schema = dict(schema_cache[db_id])
        preprocess_sqls = entry.get("preprocess_sql", [])
        if preprocess_sqls:
            for ps in preprocess_sqls:
                if ps and "CREATE" in ps.upper():
                    extra_tables = parse_schema_from_ddl(ps)
                    schema.update(extra_tables)

        for sql_idx, sql in enumerate(issue_sqls):
            if not sql or not sql.strip():
                continue

            try:
                result = validate(sql, schema=schema)
            except Exception as exc:
                parse_fail_count += 1
                results.append(
                    {
                        "instance_id": instance_id,
                        "db_id": db_id,
                        "category": category,
                        "sql_index": sql_idx,
                        "sql": sql[:200],
                        "valid": None,
                        "exception": str(exc)[:200],
                        "errors": [],
                        "tags": [],
                    }
                )
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

        # Progress
        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(entries)} entries...")

    # ── Summary stats ────────────────────────────────────────────────────────
    total = valid_count + error_count + parse_fail_count
    print(f"\n{'=' * 60}")
    print(f"VALIDATION RESULTS SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total SQL queries:        {total}")
    print(f"  Valid (no errors):      {valid_count}")
    print(f"  Invalid (has errors):   {error_count}")
    print(f"  Parse exceptions:       {parse_fail_count}")
    print(f"{'=' * 60}")

    # Error breakdown by tag
    tag_counts: Dict[str, int] = {}
    for r in results:
        for tag in r.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    if tag_counts:
        print(f"\nError Tag Distribution:")
        for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
            print(f"  {tag:45s} {count:>4d}")

    # Error breakdown by db_id
    db_error_counts: Dict[str, Tuple[int, int]] = {}  # db_id -> (valid, invalid)
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
    print(f"  {'-' * 35} {'-' * 6} {'-' * 8}")
    for db in sorted(db_error_counts.keys()):
        v, inv = db_error_counts[db]
        print(f"  {db:<35s} {v:>6d} {inv:>8d}")

    # Error breakdown by category
    cat_counts: Dict[str, Tuple[int, int]] = {}
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
    print(f"  {'-' * 25} {'-' * 6} {'-' * 8}")
    for cat in sorted(cat_counts.keys()):
        v, inv = cat_counts[cat]
        print(f"  {cat:<25s} {v:>6d} {inv:>8d}")

    # ── Save full results ────────────────────────────────────────────────────
    output = {
        "summary": {
            "total_queries": total,
            "valid": valid_count,
            "invalid": error_count,
            "parse_exceptions": parse_fail_count,
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

    # ── Also save just the errors to a separate file for quick review ────────
    error_results = [r for r in results if r.get("valid") is False]
    error_output_path = output_path.replace(".json", "_errors_only.json")
    with open(error_output_path, "w") as f:
        json.dump(error_results, f, indent=2, default=str)

    print(f"Errors-only file saved to: {error_output_path}")
    print(f"({len(error_results)} entries with errors)")


if __name__ == "__main__":
    data_file = str(ROOT / "benchmark" / "data" / "postgresql_full.jsonl")
    output_file = str(ROOT / "tests" / "output" / "validator_benchmark_results.json")

    run_benchmark_validation(data_file, output_file)
