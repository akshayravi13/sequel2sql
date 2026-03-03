import sys
import os
from pathlib import Path
import chromadb

# Add src to sys.path (optional, safe)
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

# Path to ChromaDB (persistent) — accepts a db name argument or defaults to all DBs
PRJ_ROOT = Path(__file__).resolve().parents[1]
CHROMA_BASE = PRJ_ROOT / "src" / "db_confirmed_fixes" / "chroma"
COLLECTION_NAME = "db_confirmed_fixes"


def inspect_chroma(db_name: str | None = None):
    if db_name:
        db_dirs = [CHROMA_BASE / db_name]
    else:
        if not CHROMA_BASE.exists():
            print(f"ChromaDB base path not found: {CHROMA_BASE}")
            return
        db_dirs = sorted(p for p in CHROMA_BASE.iterdir() if p.is_dir())

    for db_path in db_dirs:
        print(f"\n{'=' * 60}")
        print(f"Database: {db_path.name}")
        print(f"Path: {db_path.resolve()}")
        print(f"{'=' * 60}")

        try:
            client = chromadb.PersistentClient(path=str(db_path))
            collection = client.get_collection(COLLECTION_NAME)
        except Exception as e:
            print(f"  Error: {e}")
            continue

        count = collection.count()
        print(f"  Collection '{COLLECTION_NAME}' has {count} records.")

        if count == 0:
            continue

        print(f"\n  First {min(5, count)} records:\n")

        results = collection.get(
            limit=min(5, count),
            include=["documents", "metadatas"],
        )

        ids = results.get("ids", [])

        for i in range(len(ids)):
            print(f"  --- Record #{i + 1} ---")
            print(f"  ID: {ids[i]}")
            print(f"  Intent (document): {results['documents'][i]}")
            print("  Metadata:")
            for k, v in results["metadatas"][i].items():
                print(f"    {k}: {v}")
            print()


if __name__ == "__main__":
    # Usage: python tests/inspect_chroma_db.py [db_name]
    db = sys.argv[1] if len(sys.argv) > 1 else None
    inspect_chroma(db)