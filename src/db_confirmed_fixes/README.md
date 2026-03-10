# DB Confirmed Fixes

Persistent storage layer for **confirmed SQL fixes** using [ChromaDB](https://www.trychroma.com/). When a user confirms that a corrected SQL query is correct, the fix is embedded and stored so it can be retrieved for future similar queries.

## How It Works

Each database gets its own ChromaDB collection under `chroma/<database_name>/`. Fixes are embedded by their **intent** (natural language description) using the `all-MiniLM-L6-v2` sentence-transformer model.

### Core Modules

| File | Description |
|---|---|
| `retriever.py` | Save, retrieve, and prune confirmed fixes in ChromaDB |
| `info.py` | One-time seeder — reads `db_confirmed_fixes.json` and populates per-DB ChromaDB instances |
| `db_confirmed_fixes.json` | 50 curated fix entries with db_id mappings from the benchmark dataset |

### Key Functions (`retriever.py`)

| Function | Description |
|---|---|
| `save_confirmed_fix()` | Stores a confirmed fix with deduplication (intent similarity ≥ 0.8) |
| `find_similar_confirmed_fixes()` | Retrieves top-N fixes ranked by cosine similarity |
| `prune_confirmed_fixes()` | Tiered cleanup when collection exceeds 500 items |

### Data Schema

Each stored fix contains:

- **`intent`** — Natural language query intent (also used as the embedding document)
- **`corrected_sql`** — The validated correct SQL
- **`error_sql`** — The original broken SQL
- **`explanation`** — 2–4 sentence description of what was wrong and how it was fixed
- **`confirmed_at`** — ISO timestamp
- **`usage_count`** — Tracks how often this fix has been retrieved

### Integration

The agent exposes two tools that call into this module:
- `find_similar_confirmed_fixes_tool` — Called early during query fixing to check for prior solutions
- `save_confirmed_fix_tool` — Called after the user explicitly confirms a fix is correct

## Directory Structure

```
db_confirmed_fixes/
├── __init__.py
├── retriever.py               # Core save/retrieve/prune logic
├── info.py                    # One-time ChromaDB seeder script
├── db_confirmed_fixes.json    # Curated fix entries (50 examples)
├── README.md
└── chroma/                    # ChromaDB persistent storage (gitignored)
    └── <database_name>/
```
