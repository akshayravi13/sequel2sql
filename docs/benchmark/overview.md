# Benchmark and Findings

## Evaluation Scope

Sequel2SQL is evaluated on the BIRD-CRITIC PostgreSQL debugging benchmark.
The objective is to measure SQL repair success under realistic schema-linked
errors, rather than idealized query-generation settings.

## Reported Metrics

The primary metric used in reporting is correction success rate:

$$
	ext{Success Rate} =
\frac{\text{Number of Successfully Corrected Queries}}
{\text{Total Queries}}
$$

## Consolidated Results

Project reporting shows that tool-enabled runs outperform prompt-only baselines
for both major model families used in this repository. Gemini 3 Flash improves
from 42% to 48% when Sequel2SQL tools are available, and Mistral Large regressed
from 32% to 25% under the same condition. The net pattern is consistent:
structured retrieval and validation improve correction reliability.

## Benchmark Execution

A quick subset run can be used to verify end-to-end benchmark behavior:

```bash
./benchmark.sh --limit 20 --provider mistral
```

The full interactive entrypoint remains:

```bash
./benchmark.sh
```

Outputs are written to timestamped directories under `benchmark/outputs`, and
logs are written under `benchmark/logs`.

## Notes

Evaluation is dockerized for consistency and supports both provider mode
(`mistral`, `google`, `codestral`) and internal orchestration mode
(`sequel2sql`). Full experiment protocol and extended analysis are documented
in the final report.
