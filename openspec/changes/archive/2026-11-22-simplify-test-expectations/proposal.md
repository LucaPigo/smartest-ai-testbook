# Proposal

## Why

Test-wide reference answers and rubrics prevent independent expectations and scatter evaluation configuration across the test. The school exercise needs one clear place for each check's criteria and one predictable execution rule.

## What Changes

- **BREAKING:** Remove `goldenReference` and `rubric` from test contracts. Exact match and semantic similarity use `expectation.options.expected`; LLM judge uses `expectation.options.rubric`.
- Keep test ID, title, prompt, optional variables and one or more expectations. Validate supported expectation types, required options and finite thresholds on the 0–1 scale. Exact match requires threshold 1.
- Generate once per test, evaluate all expectations sequentially, and let only the runner determine pass/fail from scores. Preserve error isolation and recorded historical outcomes.
- Replace the generic JSON options editor with evaluator-specific fields and keep model selection at run level.
- Update requirements, examples, glossary, both diagrams, HTTP contracts and generated artifacts. Implement equivalent domain behavior in TypeScript first, then Python; keep existing HTTP implementation boundaries explicit.
- Read existing SQLite test definitions by translating their old shared criteria into each expectation without deleting data or changing stored runs.

## Capabilities

### New Capabilities

- `test-expectations`: Define, persist, configure and execute self-contained evaluation expectations with a fixed scoring and execution policy.

### Modified Capabilities

None. Existing reporting snapshot requirements and web connectivity requirements remain applicable.

## Impact

Shared documentation and Excalidraw diagrams; TypeScript and Python domain code and tests; Python persistence and HTTP translation; both OpenAPI documents, generated transport code and React forms; offline API and real-browser workflow checks. No new execution policies, test versioning, aggregation, export implementation or TypeScript HTTP CRUD endpoints are introduced. Existing user edits and databases are preserved.
