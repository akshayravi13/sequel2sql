# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sequel2SQL is an agentic LLM + RAG framework for SQL error diagnosis, optimization, and correction. While most LLMs excel at generating SQL from natural language (NL2SQL), they struggle with fixing erroneous queries. This project addresses that gap using retrieval-augmented generation and agent-based workflows, leveraging database schemas, official documentation, and past correction examples.

**Project Context:**
- Capstone project for MS in Data Science, University of Washington
- Sponsored by Microsoft
- Python 3.12+ required

## Development Commands

This project uses [uv](https://github.com/astral-sh/uv) for fast, reliable Python package management.

### Initial Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Configure API keys:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your keys:
   - `MISTRAL_API_KEY` — primary model (Mistral Large)
   - `GOOGLE_API_KEY` — optional (Gemini Flash)
   - `DATABASE` — PostgreSQL database name for the web UI
   - `LOGFIRE_TOKEN` — optional, for observability

3. **Set up LogFire (optional):**
   ```bash
   uv run logfire auth
   uv run logfire projects new
   ```
   LogFire is already configured in [src/agent/sqlagent.py](src/agent/sqlagent.py) via `logfire.configure(send_to_logfire="if-token-present")`.

### Running the Application

The web interface requires a running PostgreSQL instance (see Docker section below).

```bash
# Run the web interface — connects to DATABASE from .env (default: "postgres")
uv run python sequel2sql.py

# Use a different database without editing .env
DATABASE=california_schools_template uv run python sequel2sql.py
```

Open http://localhost:8000 for the chat interface.

### Testing

```bash
# Run all tests
uv run pytest

# Run a specific test file
uv run pytest tests/test_validator.py

# Verbose output
uv run pytest -v

# Inspect ChromaDB contents
uv run python tests/inspect_chroma_db.py
```

### Benchmarking

Run the BIRD-CRITIC PostgreSQL benchmark (530 queries):

```bash
# Interactive mode (recommended for first-time users)
./benchmark.sh

# Command-line mode — limit to N queries, optionally choose provider
./benchmark.sh --limit 20
./benchmark.sh --limit 20 --provider mistral

# Full benchmark
./benchmark.sh
```

Available `--provider` options: `mistral`, `google`, `sequel2sql` (uses the agentic pipeline directly).

See [benchmark/README.md](benchmark/README.md) for data download and setup details.

### Docker (PostgreSQL for development/web UI)

All Docker configuration lives in `benchmark/docker-compose.yml` — there is no separate `docker/` directory.

```bash
# Start containers (PostgreSQL + evaluation container)
docker compose -f benchmark/docker-compose.yml up -d

# Check status
docker compose -f benchmark/docker-compose.yml ps

# Test connection
docker compose -f benchmark/docker-compose.yml exec postgresql psql -U root -d postgres -c "SELECT 1, version();"

# Stop
docker compose -f benchmark/docker-compose.yml down
```

### Managing Dependencies

```bash
uv add <package-name>
uv add --dev <package-name>
uv sync
```

## Code Architecture

### System Overview

Sequel2SQL uses an **agentic pipeline** combining AST-based validation, semantic retrieval, and LLM reasoning. The core flow for fixing a SQL query:

1. **Schema Discovery** — retrieve relevant table schemas from the live database
2. **Validation** — AST-based syntax and schema error detection via sqlglot
3. **Semantic Retrieval** — embed query intent and fetch top-6 similar examples from ChromaDB
4. **LLM Reasoning** — agent generates corrected query using schema, errors, and few-shot examples
5. **Execution** — optionally run corrected query to verify

### Core Components

**Agent Layer** ([src/agent/](src/agent/)):
- **sqlagent.py**: Defines three Pydantic AI agents and their registered tools:
  - `agent`: Benchmark/default agent (`mistral:mistral-large-latest`, uses `BENCHMARK_PROMPT`)
  - `webui_agent`: Interactive chat agent (`mistral:mistral-large-latest`, uses `WEBUI_PROMPT`). This is what `sequel2sql.py` exposes via `webui_agent.to_web()`.
  - `syntax_fixer_agent`: Dedicated syntax-only fixer (returns raw SQL string, no explanation)
  - `DEFAULT_MODEL = "mistral:mistral-large-latest"` — change here to switch models globally
- **prompts/base_prompt.py**: Core identity, constraints, and tool catalog shared by all agents
- **prompts/benchmark_prompt.py**: Batch/benchmark-mode prompt extension
- **prompts/webui_prompt.py**: Interactive chat prompt extension with routing logic

**Tools registered on `agent` and `webui_agent`:**
- `analyze_and_fix_sql` — orchestrates schema fetch + validation + few-shot retrieval in one call
- `describe_database_schema` — returns DDL-like schema for specified tables
- `execute_sql_query` — runs SELECT queries against the live database
- `validate_query` — plain validation without database context
- `similar_examples_tool` / `find_similar_examples` — semantic search over ChromaDB

**AST Parser & Validation** ([src/ast_parsers/](src/ast_parsers/)):
- **validator.py**: SQL syntax and schema validation using sqlglot; detects silent fixes
- **query_analyzer.py**: AST-based structural analysis (joins, aggregations, subqueries, etc.)
- **llm_tool.py**: `validate_sql()` — the validation interface called by agent tools
- **error_codes.py**, **error_context.py**: Structured error taxonomy with canonical tags (e.g., `SYNTAX_ERROR`, `SCHEMA_ERROR`)
- **models.py**: Pydantic models for `ValidationResult`, `ValidationErrorOut`

**Database Layer** ([src/database/](src/database/)):
- **database.py**: `Database` class — SQLAlchemy-based, PostgreSQL-only, reflects schema on init, limits queries to SELECT only (caps at 100 rows)
- **deps.py**: `AgentDeps` dataclass — dependency injection container for agent tools
- **tools.py**: `execute_sql()` tool function; blocks system catalog queries and routes through `AgentDeps`
- **format_schema.py**: Formats reflected SQLAlchemy metadata into human-readable DDL text

**Vector Database RAG** ([src/query_intent_vectorDB/](src/query_intent_vectorDB/)):
- **search_similar_query.py**: `find_similar_examples()` — semantic search returning `FewShotExample` objects
- **embed_query_intent.py**: Embedding logic using `all-MiniLM-L6-v2`
- **process_query_intent.py**: AST-based query intent extraction for indexing
- ChromaDB collection `query_intents` persisted in [src/chroma_db/](src/chroma_db/)

**Entry Points:**
- **sequel2sql.py**: Launches web UI via `webui_agent.to_web(deps=...)` on port 8000
- **benchmark/main.py**: Benchmark orchestrator (called by `benchmark.sh`); 5-phase pipeline: prompt generation → LLM inference → post-processing → Docker eval → results

**Benchmarking** ([benchmark/](benchmark/)):
- **main.py**: Main entry point; interactive or `--limit N --provider PROVIDER` CLI mode
- **src/config.py**: Provider configs (mistral, google, sequel2sql), API key loading
- **src/inference_engine.py**: Sequential query processing with checkpointing
- **src/sequel2sql_client.py**: Calls the local `webui_agent` pipeline instead of an external API
- **src/checkpoint_manager.py**: Saves/resumes benchmark runs; outputs in `benchmark/outputs/run_<timestamp>/`

### Key Dependencies

- **pydantic-ai**: Agent framework, tool registration, `RunContext`, `ModelRetry`
- **mistralai** / **google-genai**: LLM backends
- **chromadb**: Vector database for semantic search
- **sentence-transformers**: `all-MiniLM-L6-v2` embedding model
- **sqlglot**: SQL parsing, AST analysis, dialect-aware validation
- **sqlalchemy**: Database connectivity and schema reflection
- **logfire**: Optional observability (`send_to_logfire="if-token-present"`)
- **uvicorn**: ASGI server for web interface

### Important Implementation Details

**Database Connection** ([src/agent/sqlagent.py](src/agent/sqlagent.py)):
- `get_database_deps(database_name, ...)` creates an `AgentDeps` with a `Database` instance
- Default connection: `localhost:5534`, user `root`, password `123123`
- `Database.__init__` defaults to port 5432; `get_database_deps` overrides to 5534 for Docker

**Validation Strategy**:
- `validate_sql(sql, db_name, dialect)` in [src/ast_parsers/llm_tool.py](src/ast_parsers/llm_tool.py) is the agent-facing interface
- Schema context is loaded from the live database via SQLAlchemy reflection (not from static JSON schema files)
- Validation catches both hard parse errors and "silent fixes" (sqlglot auto-corrects without raising)

**Vector Database**:
- ChromaDB collection: `query_intents`
- Documents indexed by AST-extracted query intent, not raw SQL
- `find_similar_examples(query, n_results=6)` returns structurally diverse examples with diversity filtering to prevent near-duplicate results

**Module Import Note**:
- The directory is `src/query_intent_vectorDB/` (uppercase DB) but Python imports use `src.query_intent_vectordb` (lowercase). This works silently on macOS (case-insensitive filesystem) but may fail on Linux.

## Code Style Guidelines

From [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md):

- **Indentation**: Use tabs (not spaces)
- **Line length**: Maximum 80 characters
- **Braces**: Opening braces on next line for class/method declarations
- **Spacing**: One space between operators and operands
- **Variable naming**: Descriptive names (avoid single-letter variables like `a` or `x`)
- **Commits**: Must be atomic — one logical change per commit

## Project-Specific Notes

- PostgreSQL-only — not intended for other SQL dialects
- The goal is error correction, not initial query generation (NL2SQL)
- Only SELECT queries are permitted; INSERT/UPDATE/DELETE/DDL are blocked at the tool layer
- `benchmark/agent/` directory exists but is currently empty (the pipeline is in `benchmark/main.py` + `benchmark/src/`)
