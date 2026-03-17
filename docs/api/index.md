# API and Tool Reference

This page describes the practical tool surfaces exposed by the runtime agent
and summarizes the operational contract expected by downstream callers.

## Agent Tooling (High-Level)

### `analyze_and_fix_sql`

`analyze_and_fix_sql` is the top-level orchestration helper used by the
interactive flow. It composes schema discovery, SQL validation, retrieval of
similar examples, taxonomy guidance, and final context packaging so that the
model can generate a correction against grounded signals.

### `validate_query`

`validate_query` evaluates SQL against connected database context and returns
structured validation output that includes error categories and metadata.

### `execute_sql_query`

`execute_sql_query` runs read-only SQL under safety controls and returns
structured tabular output for inspection-oriented workflows.

### `describe_database_schema`

`describe_database_schema` returns schema descriptions for referenced tables or
wider table sets when broader context is needed.

### Confirmed Fix Retrieval/Write

`find_similar_confirmed_fixes` and `save_confirmed_fix` provide persistence and
retrieval paths for user-confirmed repairs. Together they allow validated fixes
to become reusable context in future correction attempts.

## Core Runtime Data Objects

### `AgentDeps`

`AgentDeps` is the dependency container passed into tool calls. It carries
database handles and runtime constraints required by execution paths.

### `ValidationResult`

`ValidationResult` is the validation payload containing status flags,
categorized errors, and query metadata used by agent logic.

### `SQLAnalysisContext`

`SQLAnalysisContext` aggregates schema signals, detected errors, retrieval
examples, and supporting metadata for downstream correction generation.

## Model Configuration

Current agent-layer model selectors are `mistral`, `google`, and `codestral`.
The benchmark layer also supports `sequel2sql` for internal pipeline mode.

## Operational Contract

The target dialect is PostgreSQL. Query execution paths are read-only and
output-constrained. The correction contract follows a fixed quality path:
validate, retrieve context, reason, and validate again.
