# Quickstart

This guide walks through a complete local setup for Sequel2SQL, including the
interactive web interface, database services, and benchmark runner. The
commands are intentionally minimal so that a fresh environment can be brought
up quickly and verified end to end.

## Prerequisites

Before starting, ensure the machine has Python 3.12 or newer, the `uv`
package manager, Docker, and Git. These are the only required external tools
for local execution of the current pipeline.

## 1) Clone And Install

```bash
git clone https://github.com/SVijayB/sequel2sql
cd sequel2sql
uv sync
```

## 2) Configure Environment

```bash
cp .env.example .env
```

Set at least these values in `.env`:

`MISTRAL_API_KEY` is required for the default model path, while
`GOOGLE_API_KEY` is only needed when running Google-backed configurations.
`DATABASE` defaults to `postgres`, `DEFAULT_MODEL` should match the provider
format used by the project, and `LOGFIRE_TOKEN` can be set when observability
is desired.

## 3) Start Database Services

Bring up the benchmark and PostgreSQL services with Docker Compose and confirm
the container state before launching the app.

```bash
docker compose -f benchmark/docker-compose.yml up -d
docker compose -f benchmark/docker-compose.yml ps
```

## 4) Launch Web UI

```bash
uv run python sequel2sql.py
```

Open `http://localhost:8000`.

If a different database should be used at runtime, override `DATABASE` for the
process invocation:

```bash
DATABASE=california_schools_template uv run python sequel2sql.py
```

## 5) Run Benchmark

The interactive benchmark mode is useful for first runs because it helps
confirm provider settings and dataset constraints:

```bash
./benchmark.sh
```

For quick validation, run a small subset:

```bash
./benchmark.sh --limit 20 --provider mistral
```

Supported providers include `mistral`, `google`, `codestral`, and
`sequel2sql` for internal pipeline evaluation.

## 6) Run Tests

After setup, run the test suite to confirm environment health:

```bash
uv run pytest
```

For targeted validation during iteration:

```bash
uv run pytest tests/test_validator.py -v
```

## Troubleshooting

Connection failures are usually caused by stopped containers or incorrect
database names. If startup fails, inspect `docker compose ... ps` and
container logs first. If model calls fail, validate API keys and provider
selection in `.env`. If queries execute against an unexpected schema,
re-check the `DATABASE` value used at launch.

## Where Next

Continue with [architecture/overview.md](architecture/overview.md) for system
design, [benchmark/overview.md](benchmark/overview.md) for evaluation details,
and [deliverables/final-report.md](deliverables/final-report.md) for the full
report narrative.
