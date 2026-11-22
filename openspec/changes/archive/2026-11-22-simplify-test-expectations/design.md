# Design

## Context

See [proposal.md](./proposal.md) for motivation. The current Python application persists suite definitions as JSON inside SQLite rows and implements all three evaluator strategies. TypeScript implements creation and exact-match execution but lacks the other two strategies. Both runners already execute sequentially and copy expectation metadata into results. Evaluators redundantly calculate pass/fail before runners calculate it again.

## Goals / Non-Goals

**Goals:** Keep the documented OO responsibilities and explicit public contracts, make each check understandable on its own, and preserve existing local data and reporting snapshots.

**Non-Goals:** New class hierarchies, configurable execution policies, TypeScript CRUD HTTP implementation, overall scores, export implementation and full test versioning.

## Decisions

### Criteria belong to expectations

Keep the existing small `Expectation` record/contract with `options`. Exact and semantic checks require exactly `{expected: string}` and judge requires exactly `{rubric: string}`. Reject blank criteria, unsupported types/options and invalid thresholds. This avoids multiple optional test-wide fields and additional configuration classes. The builder validates the full definition before returning a test; a direct reusable expectation validation function is sufficient. IDs and names remain for readable historical outcomes. Variables default to an empty map.

### One scoring policy

All strategies produce values on 0–1. Exact match is literal equality, scoring 0 or 1, with threshold fixed to 1. Semantic similarity retains the current normalized cosine calculation; the judge requests and validates 0–1 structured output. An evaluator returns a small score/feedback value; the runner alone applies thresholds and adds recorded metadata. Recorded outcomes retain existing scale fields for API and history compatibility. Invalid evaluator scores are recorded as evaluation errors. Evaluators still receive the test's prompt/variables for context; criteria never enter the model-under-test input.

### Preserve the existing execution architecture

Retain Builder, Adapter and Strategy and the separate creation, execution, reporting and exporting boundaries. The application chooses one model per run; the runner generates once per test and evaluates every expectation in order. It catches generation errors per test and evaluation errors per check. A test passes only when generation and all checks succeed. No policy objects, factories, parallelism or retries are added. Implement and verify TypeScript first, then mirror the behavior in Python. TypeScript gains the missing domain evaluator strategies and a minimal provider adapter needed to exercise them; its HTTP server scope stays unchanged.

### Contracts, persistence and forms

Update both OpenAPI exercises but generate transport artifacts only from `api/openapi.yaml`, preserving route paths and methods. Keep `options` as an object with documented evaluator-specific forms rather than introducing generator-sensitive polymorphic schemas; handwritten domain validation enforces its exact content. Apply schema bounds to numeric thresholds and default variables to `{}`. Replace the JSON editor with ordinary expected-answer/rubric controls, exact threshold 1 and editable 0–1 thresholds otherwise. Keep existing title, variable controls, IDs and routing.

Generated numeric bounds reject non-finite input before the HTTP handler runs. FastAPI's default validation response cannot serialize those invalid numbers, so a small validation-error handler encodes non-finite values as strings in the otherwise standard error details. This preserves HTTP 422 instead of producing HTTP 500; domain checks remain responsible for expectation invariants.

For old SQLite definitions, the loader copies a legacy test criterion into each corresponding expectation when its local option is missing. Local options take precedence. The next normal save writes the new form; reads do not rewrite rows. Existing run rows and databases are never deleted or recomputed. This is a small compatibility branch in the existing loader, not a migration framework.

## Risks / Trade-offs

- Breaking test/HTTP shape -> update examples, contracts, generated clients, handlers, fixtures and UI together; no compatibility fields remain in new test contracts.
- Duplicate expected text across checks -> accept the small duplication to keep checks independent and understandable.
- Provider failures and malformed scores -> deterministic offline tests cover integration boundaries and error isolation; report live-provider verification limits explicitly.
- Existing user changes -> edit the current working tree narrowly without resets, unsolicited commits or database replacement.
- Historical planning artifacts describe the former design -> retain them as history; new shared behavior is recorded by this change and current product documentation.

## Migration Plan

Update documentation first, then TypeScript domain and tests, then Python domain and tests, then persistence/HTTP contracts/generated artifacts and the client. Verify offline end-to-end workflows on temporary databases, including legacy definition reload and history preservation. Deploy the new server and client together. Rollback requires the previous code with a pre-change database backup after new definitions have been saved; do not perform destructive rollback automatically.
