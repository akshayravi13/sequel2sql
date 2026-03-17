# Component Map

This document maps the repository structure to the concrete runtime behavior
of Sequel2SQL. It is intended as an implementation guide for readers who need
module-level orientation before extending or evaluating the system.

The central orchestration module is `src/agent/sqlagent.py`. It defines the
core agents used by the web interface and benchmark flows, registers tool
surfaces, and binds model configuration to dependency objects. In practical
terms, this is where correction workflows are assembled and where tool calls
are coordinated across validation, retrieval, and database access.

The validation subsystem lives in `src/ast_parsers`. These modules handle SQL
parsing, structure analysis, error categorization, and database-aware checks.
They provide deterministic outputs that constrain model behavior and expose
structured signals for downstream reasoning. If correction quality degrades on
specific error types, this is usually the first subsystem to inspect.

The data-access subsystem is implemented in `src/database`. It manages
connection handling, schema reflection, read-only execution controls, and
schema formatting utilities used by agent tools. Its design goal is to make
live schema information available without permitting unsafe query operations.

Semantic retrieval is implemented in `src/query_intent_vectordb`. This layer
embeds query intent, stores vectorized representations, and returns similar
examples with filtering that favors diversity over near-duplicates. It supplies
few-shot context that helps the model produce corrections aligned with prior
patterns.

Confirmed-fix storage is implemented in `src/db_confirmed_fixes`. While intent
retrieval provides broader semantic similarity, confirmed-fix retrieval focuses
on validated, practical repairs. This distinction is important because it lets
runtime context include both conceptual similarity and proven examples.

The primary product entrypoint is `sequel2sql.py`, which wires environment
configuration, dependency initialization, and web presentation around the
interactive agent. The related UI-facing logic under `src/webui` provides the
user interaction surface while delegating correction logic to the agent layer.

Benchmark orchestration is centered in `benchmark/main.py`, with supporting
provider and runtime configuration under `benchmark/src/config.py`. This part of
the codebase is responsible for repeatable large-scale evaluation, checkpoint
management, and artifact generation rather than interactive debugging.

Across these modules, the dependency flow is consistent. Input enters the agent,
tools collect validation and schema context, retrieval modules contribute
examples, the model proposes a correction, validation confirms the result, and
then the response is returned or persisted when confirmed. Keeping each step in
its own module is what makes the system testable and maintainable at scale.
