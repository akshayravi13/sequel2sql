# Sequel2SQL

Sequel2SQL is an agentic framework for repairing broken PostgreSQL queries
with a workflow that combines deterministic validation, live schema awareness,
retrieval of similar historical fixes, and tool-augmented LLM reasoning.
Instead of relying on single-pass prompt generation, the system executes a
structured correction loop so that each candidate query is grounded in
database reality before it is returned.

This documentation site is written as a technical report for evaluators,
sponsors, and contributors. It explains both what the project achieves and
how the implementation is organized, including runtime architecture, benchmark
results, development workflows, and operational interfaces.

## Documentation Scope

The material is organized to move from outcomes to implementation detail.
The quickstart explains how to run the web interface and benchmark pipeline,
the architecture section describes system design and module boundaries, the
benchmark section reports evaluation findings, and the API and development
sections describe interfaces and contributor workflows.

## Project Snapshot

Sequel2SQL focuses on SQL debugging and correction rather than NL2SQL query
generation. The current scope is PostgreSQL, with read-only safeguards around
query execution. The central objective is higher correction reliability than
prompt-only repair pipelines, evaluated on the BIRD-CRITIC PostgreSQL subset.

## Team and Sponsorship

Sequel2SQL is a University of Washington MSDS capstone project sponsored by
Microsoft.

The project team includes Akshay Ravi, Aravindh Manavalan, Jay Sanghavi,
Smeet Dedhia, and Vijay Balaji S, with sponsorship from Dhruv Relwani,
Software Developer at Microsoft.

## Start Here

For the complete academic deliverable, begin with
[deliverables/final-report.md](deliverables/final-report.md). For operational
setup, read [getting-started.md](getting-started.md). For implementation
structure, continue to [architecture/overview.md](architecture/overview.md),
and for measured results see
[benchmark/overview.md](benchmark/overview.md).
