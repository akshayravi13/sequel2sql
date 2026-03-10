"""
Test that each of the first 50 entries in postgresql_full.jsonl can retrieve
its corresponding confirmed fix from the per-database ChromaDB instances.

Uses the `query` field from postgresql_full.jsonl (the user's natural-language
question) as the search intent, queries ChromaDB directly (bypassing the 0.75
similarity threshold in find_similar_confirmed_fixes), and checks whether the
seeded confirmed fix ranks as the top-1 result.

Run:
    cd <project_root>
    .venv/bin/python -m tests.test_confirmed_fix_retrieval
"""

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path for direct script execution (e.g. uv run)
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.db_confirmed_fixes.retriever import _get_collection  # noqa: E402

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BENCHMARK_DATA = PROJECT_ROOT / "benchmark" / "data" / "postgresql_full.jsonl"
CONFIRMED_FIXES = (
    PROJECT_ROOT / "src" / "db_confirmed_fixes" / "db_confirmed_fixes.json"
)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------


def load_benchmark_entries(limit: int = 50) -> list[dict]:
    """Load the first `limit` entries from postgresql_full.jsonl."""
    entries = []
    with open(BENCHMARK_DATA, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            entries.append(json.loads(line))
    return entries


def load_confirmed_fixes() -> dict[str, dict]:
    """Load confirmed fixes keyed by instance_id."""
    with open(CONFIRMED_FIXES, "r", encoding="utf-8") as f:
        fixes = json.load(f)
    return {fix["instance_id"]: fix for fix in fixes}


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------


def run_retrieval_test():
    benchmark_entries = load_benchmark_entries(50)
    confirmed_fixes = load_confirmed_fixes()

    total = 0
    top1_hits = 0
    top4_hits = 0
    misses = []

    print(f"Testing retrieval for {len(benchmark_entries)} benchmark entries...")
    print("Querying ChromaDB directly (no similarity threshold)\n")
    print(
        f"{'ID':<18} {'DB':<25} {'Top-1 Sim':>10} {'Rank':>6}  {'Status'}"
    )
    print("-" * 85)

    for entry in benchmark_entries:
        instance_id = entry["instance_id"]
        db_id = entry["db_id"]
        query_intent = entry["query"]  # natural-language question from benchmark

        # Skip if no confirmed fix exists for this instance
        if instance_id not in confirmed_fixes:
            continue

        expected_fix = confirmed_fixes[instance_id]
        expected_sql = expected_fix["corrected_sql"]
        total += 1

        # Query ChromaDB directly (bypasses the 0.75 threshold)
        collection = _get_collection(db_id)
        count = collection.count()

        if count == 0:
            rank = -1
            top_sim = 0.0
        else:
            results = collection.query(
                query_texts=[query_intent],
                n_results=min(4, count),
                include=["documents", "metadatas", "distances"],
            )

            # Find rank of the expected fix
            rank = -1
            top_sim = 0.0
            if results["distances"] and results["distances"][0]:
                top_sim = 1.0 - results["distances"][0][0]  # best match similarity

                for idx, meta in enumerate(results["metadatas"][0]):
                    if meta.get("corrected_sql") == expected_sql:
                        rank = idx + 1
                        break

        if rank == 1:
            top1_hits += 1
            status = "✓ TOP-1"
        elif rank > 1:
            top4_hits += 1
            status = f"~ RANK-{rank}"
        else:
            status = "✗ NOT IN TOP-4"
            misses.append((instance_id, top_sim))

        print(
            f"{instance_id:<18} {db_id:<25} {top_sim:>10.4f} {rank:>6}  {status}"
        )

    # Summary
    print("-" * 85)
    print(f"\n{'Metric':<35} {'Value':>10}")
    print("-" * 45)
    print(f"{'Total entries tested':<35} {total:>10}")
    print(f"{'Top-1 hits (exact best match)':<35} {top1_hits:>10}")
    print(f"{'Top-4 hits (in results)':<35} {top1_hits + top4_hits:>10}")
    print(f"{'Not found in top-4':<35} {len(misses):>10}")
    print(f"{'Top-1 accuracy':<35} {top1_hits / total * 100:>9.1f}%")
    print(f"{'Top-4 recall':<35} {(top1_hits + top4_hits) / total * 100:>9.1f}%")

    if misses:
        print(f"\nMissing from top-4 ({len(misses)}):")
        for iid, sim in misses:
            print(f"  - {iid}  (best sim: {sim:.4f})")

    return top1_hits, top4_hits, total


if __name__ == "__main__":
    top1, top4, total = run_retrieval_test()
    # Exit with non-zero if top-1 accuracy is below 80%
    exit(0 if top1 / total >= 0.8 else 1)
