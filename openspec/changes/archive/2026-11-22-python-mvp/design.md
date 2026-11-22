# Design

## Context

The Python runner and exact match evaluator exist in memory; FastAPI and the React client currently expose only connectivity. `api/openapi.yaml` proposes the other operations but its generated artifacts do not yet reflect them. Existing `reporting` and `web-access` specifications remain shared target contracts; Python is the only backend implemented by this change.

## Goals / Non-Goals

**Goals:** Keep the domain testable independently of FastAPI and SQLAlchemy; provide a minimal complete Python and React workflow; enable autonomous sequential implementation.

**Non-Goals:** Export, TypeScript backend parity, migrations for a production database, concurrent runs, accounts and a component library.

## Decisions

### Separate contracts, persistence and HTTP

Domain protocols express repository and domain contracts; SQLAlchemy mappings and SQLite repositories live outside domain code and never import the web server. A small composition entry point builds dependencies and supplies them to the server or another Python caller. FastAPI translates transport data and coordinates public contracts without implementing business rules. This avoids coupling domain objects to ORM or framework types; a service container is unnecessary.

SQLite transactions save each suite aggregate atomically. Runs store their own recorded prompt and evaluation metadata, independent of later edits. Use a file-backed database configured outside the server and isolated temporary databases in tests. Initialization for a fresh database is sufficient for this MVP.

### Contracts and creation

`api/openapi.yaml` is the sole HTTP contract; the separate domain-oriented OpenAPI exercise is not an implementation input. Before implementing endpoints, add the suite description required by the product requirements and resolve input versus output expectation schemas so test creation accepts new expectation inputs while updates retain existing IDs. Specify validation and missing-resource responses and regenerate transport artifacts using the pinned tools. Preserve all other existing operations; add no export endpoint. Resolve any generator incompatibility with the existing generation workflow, not handwritten edits to generated files.

### Provider and evaluation

Use an OpenAI API adapter as a default planning assumption, with model names and API key supplied by environment configuration. The current Codex agent session is not an application credential. The adapter translates prompts and variables; the runner and evaluator protocols remain provider-independent. Use OpenAI embeddings for semantic similarity and a separately configured OpenAI model for LLM judge; define scores, threshold scales, structured judge output and error behavior in implementation tests. Exact match remains deterministic. Never log or send credentials to the browser. This choice can later be replaced through the contracts.

Tests use deterministic fake provider and evaluator responses; an optional explicitly configured live smoke test verifies real credentials and model access. Missing credentials must not block offline tests or make fabricated live-success claims.

### UI and reporting

React uses ordinary HTML controls, existing runtime backend configuration, and the generated client. Keep forms and navigation simple. Generate report snapshots from recorded runs according to the existing reporting spec and expose equivalent recorded details through the existing run response; do not recompute evaluations. Serve the shared UI separately from the optional backend.

### Autonomous execution

Tasks are sequential dependency-ordered slices, each with a concrete outcome and verification. An agent can run them serially in the existing checkout; parallel work and separate worktrees are optional, not prerequisites. Resolve routine choices locally; record assumptions and external verification limits instead of pausing for a prompt. Respect real sandbox approval boundaries and do not invent missing credentials.

## Risks / Trade-offs

- Provider availability, cost and credentials vary → mocked tests are mandatory; live verification is conditional and its absence is reported.
- Shared API and spec changes precede TypeScript parity → explicitly document Python-only progress and avoid claiming cross-backend conformance for new routes.
- Suite deletion and historical data can conflict → define and test a consistent deletion policy in the contract before implementing it.
- Provider responses can be malformed → validate at the integration boundary and record evaluation errors without losing remaining results.

## Migration Plan

Initialize a new local SQLite database, configure the Python backend and point the existing web runtime configuration at it. No existing persisted data is assumed. Roll back by stopping the Python backend and using the previous version; preserve the database file for inspection. No export or production schema migration is included.
