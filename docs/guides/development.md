# Development Guide

## Environment Setup

Development begins with dependency synchronization and environment file setup.
The baseline workflow below is sufficient for local feature development,
testing, and docs updates.

```bash
uv sync
cp .env.example .env
```

Start required containers:

```bash
docker compose -f benchmark/docker-compose.yml up -d
```

## Run Modes

Sequel2SQL supports an interactive runtime path and a benchmark path.

### Web UI

Use the command below for interactive SQL debugging in the local UI.

```bash
uv run python sequel2sql.py
```

### Benchmark

Use the benchmark entrypoint when evaluating provider behavior at scale.

```bash
./benchmark.sh
```

## Testing

A full test run is recommended before merge:

```bash
uv run pytest
```

For iterative changes in validation logic, these focused tests are commonly
used:

```bash
uv run pytest tests/test_validator.py -v
uv run pytest tests/test_validator_fixes.py -v
```

## Recommended Workflow

The most reliable workflow is to keep changes small, run targeted tests against
the touched modules, then run the full suite before merge. When behavior,
interfaces, or operational guidance changes, update documentation in the same
change set so that runtime and docs do not drift.

## Debugging Checklist

When debugging correction quality issues, validate schema context first,
confirm provider selection in environment and benchmark config, inspect
retrieval examples for relevance, and then review checkpoint and output
artifacts for benchmark anomalies.

## Core Paths

Agent orchestration is centered in `src/agent/sqlagent.py`, validation lives in
`src/ast_parsers`, database logic in `src/database`, retrieval logic in
`src/query_intent_vectordb`, confirmed-fix persistence in
`src/db_confirmed_fixes`, and benchmark orchestration in `benchmark/main.py`.

## Docs Build

To preview documentation locally:

```bash
uv run mkdocs serve
```

For CI-equivalent validation:

```bash
uv run mkdocs build --strict
```
