"""
Seed db_confirmed_fixes.json into per-database ChromaDB instances.

Run:
    python -m src.db_confirmed_fixes.info

Reads db_confirmed_fixes.json, groups entries by db_id, and upserts each
entry into a database-specific ChromaDB collection under chroma/<db_id>/.
The intent field is embedded as the document; all other fields are stored
as metadata.
"""

import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

# ---------------------------------------------------------------------------
# Configuration (mirrors store.py constants)
# ---------------------------------------------------------------------------

COLLECTION_NAME = "db_confirmed_fixes"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHROMA_BASE_PATH = Path(__file__).parent / "chroma"
DATA_FILE = Path(__file__).parent / "db_confirmed_fixes.json"


def _get_chroma_collection(database_name: str) -> chromadb.Collection:
    """
    Create (or open) a ChromaDB persistent collection for the given database.
    """
    sanitized_db_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", database_name)
    db_path = CHROMA_BASE_PATH / sanitized_db_name
    db_path.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(db_path))
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=emb_fn,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def seed_confirmed_fixes() -> dict[str, int]:
    """
    Read db_confirmed_fixes.json and upsert all entries into per-database
    ChromaDB collections.

    Returns a dict of {db_id: count_seeded}.
    """
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        entries = json.load(f)

    # Group by db_id
    by_db: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        by_db[entry["db_id"]].append(entry)

    confirmed_at = datetime.now(timezone.utc).isoformat()
    summary: dict[str, int] = {}

    for db_id, db_entries in sorted(by_db.items()):
        collection = _get_chroma_collection(db_id)

        documents = []
        metadatas = []
        ids = []

        for entry in db_entries:
            intent = entry["intent"]
            corrected_sql = entry["corrected_sql"]
            error_sql = entry["error_sql"]
            explanation = entry["explanation"]

            # Deterministic ID from db + intent + corrected_sql
            doc_id = hashlib.sha256(
                f"{db_id}::{intent}::{corrected_sql}".encode("utf-8")
            ).hexdigest()[:16]

            metadata = {
                "intent": intent,
                "corrected_sql": corrected_sql,
                "error_sql": error_sql,
                "explanation": explanation,
                "confirmed_at": confirmed_at,
                "usage_count": 0,
            }

            documents.append(intent)
            metadatas.append(metadata)
            ids.append(doc_id)

        # Batch upsert all entries for this database at once
        collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

        summary[db_id] = len(db_entries)
        print(f"  ✓ {db_id}: {len(db_entries)} entries seeded")

    return summary


def main():
    print(f"Reading confirmed fixes from {DATA_FILE}")
    print(f"ChromaDB base path: {CHROMA_BASE_PATH}\n")

    summary = seed_confirmed_fixes()

    total = sum(summary.values())
    print(f"\nDone! Seeded {total} entries across {len(summary)} databases.")


if __name__ == "__main__":
    main()
