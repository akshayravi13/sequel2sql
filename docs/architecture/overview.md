# Architecture Overview

Sequel2SQL is designed as a verification-first SQL correction system for
PostgreSQL workloads. The architecture intentionally avoids single-step query
rewrites and instead uses a staged debugging loop where every candidate query
is checked against deterministic signals before being returned. This design
choice is the core reason the system behaves more reliably than prompt-only
repair workflows on difficult schema-linked errors.

At runtime, an input query enters the agent layer and is routed through tool
calls that gather schema context, validate structure, and retrieve relevant
historical examples. The model uses that context to propose a correction,
which is validated again before output. When a repair is confirmed by the
workflow, it can be persisted and become part of future retrieval context.
In practice, this creates a feedback loop where the system improves practical
guidance without changing the base model.

The agent layer is implemented in `src/agent/sqlagent.py` and defines the
interactive web agent, the benchmark-oriented agent, and a syntax-focused
agent path. Model selection is configured to support multiple providers while
keeping the orchestration pattern stable. This separation allows model
experimentation without redesigning tools or data flow.

Validation logic is implemented in `src/ast_parsers` and acts as the primary
deterministic guardrail. It combines SQL parsing, structural analysis, and
database-aware checks so that common error classes can be detected in a way
the model can consume directly. The output of this layer is not just pass/fail;
it includes categorized metadata that shapes subsequent reasoning.

Database integration is isolated in `src/database`, where schema reflection,
execution controls, and tool-level safeguards are enforced. The system is
deliberately read-only for query execution paths used by the agent, which
reduces risk while still allowing schema-grounded debugging. This layer is
also responsible for producing schema representations that are suitable for
prompt context and tool responses.

Retrieval is split across `src/query_intent_vectordb` and
`src/db_confirmed_fixes`. The intent vector store provides semantically similar
examples, while the confirmed-fix store preserves validated repairs that have
high practical relevance. Together they provide concrete context that helps
the model avoid generic but incorrect rewrites.

Benchmark execution is orchestrated by `benchmark/main.py` with provider and
runtime settings in `benchmark/src/config.py`. This layer handles repeatable
evaluation, artifact generation, and result tracking. Its role is separate
from user-facing correction but essential for measuring the architecture under
controlled conditions.

The architecture follows four consistent principles: deterministic validation
before answer generation, schema-grounded reasoning over guesswork, controlled
database interaction for safety, and modular boundaries that allow provider and
tool evolution with minimal cross-layer coupling.
