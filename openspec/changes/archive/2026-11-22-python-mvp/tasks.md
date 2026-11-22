# Tasks

Execute the groups in order. Agents may work sequentially and make routine implementation decisions autonomously. Do not request prompts for routine choices; document assumptions and report any genuinely unavailable external verification. The shared specifications describe the target; the TypeScript backend implementation and verification are deferred.

## 1. Contract and boundaries

- [x] 1.1 Update `api/openapi.yaml` to include suite description, creation inputs for nested expectations, stable IDs on update, validation and missing-resource responses; validate the contract and example create/update requests.
- [x] 1.2 Define suite deletion and run-history behavior consistently in the contract and tests, preserving historical results when test definitions change; verify the documented scenarios.
- [x] 1.3 Regenerate transport artifacts with the pinned generator and verify generation check mode and the client build; document that generated TypeScript artifacts are shared transport, not TypeScript backend parity.
- [x] 1.4 Define Python public domain and repository protocols and dependency boundaries; verify domain imports neither SQLAlchemy nor FastAPI and each domain class explicitly implements its public protocol.

## 2. Python definitions

- [x] 2.1 Complete suite and test creation/editing, including description, variables, rubric and stable IDs; verify create/edit/delete and identity with domain tests.
- [x] 2.2 Validate required prompt, at least one expectation and criterion per evaluator; verify invalid definitions do not produce partial tests.

## 3. Python SQLite persistence

- [x] 3.1 Add SQLAlchemy and configure SQLite outside the domain and server; verify fresh database initialization and dependency installation.
- [x] 3.2 Implement suite, test and expectation persistence using atomic transactions; verify round trips, updates, deletion, rollback and restart against a temporary SQLite database.
- [x] 3.3 Implement run, result and score persistence; verify round trips, historical snapshots after definition changes and the agreed deletion policy.

## 4. Python execution and evaluations

- [x] 4.1 Complete sequential runner behavior and deterministic exact match; verify prompt and variables, thresholds, empty suites, provider errors and per-expectation error isolation.
- [x] 4.2 Implement the configurable OpenAI model adapter with environment-supplied credentials and fake-client tests for requests, variable substitution, response parsing and errors; document configuration without exposing secrets.
- [x] 4.3 Implement semantic similarity using configurable embeddings and an explicit score scale; verify threshold, malformed responses and error isolation with fake responses.
- [x] 4.4 Implement rubric-based LLM judge with structured score and feedback validation; verify scale, threshold and malformed or failed responses with fake responses.

## 5. Python reporting and composition

- [x] 5.1 Implement reporting from completed runs according to the existing reporting spec; verify deep snapshot independence, errors, scores and original prompts.
- [x] 5.2 Compose database, repositories, provider and evaluators outside the web server; verify saving a suite, running it with a fake model and retrieving the run without importing or starting FastAPI.

## 6. Python HTTP API

- [x] 6.1 Implement suite, test and expectation endpoints from the canonical OpenAPI contract; verify successful requests, nested creation, validation, missing resources and persistence with HTTP tests.
- [x] 6.2 Implement run creation, listing and retrieval; verify recorded results, error isolation, report data and persistence with a fake provider and temporary SQLite database.
- [x] 6.3 Preserve health and configure browser access for the implemented methods; verify health and CORS preflight for the configured origin.

## 7. React workflow

- [x] 7.1 Implement minimal suite, test and expectation forms and lists with native controls and the generated client; verify create/edit/delete and visible request errors in a browser.
- [x] 7.2 Implement model selection, run submission and result review with native controls; verify prompt, outcomes, threshold, feedback and error display in a browser using a fake provider.
- [x] 7.3 Preserve runtime backend selection and update usage documentation; verify the client build and documented startup against Python.

## 8. Integration and handoff

- [x] 8.1 Run Python tests, generated-contract checks and the React build; record results and any environment limitations.
- [x] 8.2 Exercise create suite → create test with expectations → run → restart → review using SQLite and a fake provider; verify domain usage without the web server and the corresponding browser flow.
- [x] 8.3 If configured credentials and model access are available, perform a real OpenAI smoke test; otherwise document it as unverified without blocking offline verification or claiming live success.
- [x] 8.4 Update project documentation with startup, database, model and credential configuration, Python-only implementation status and deferred export; verify the documented commands against the resulting project.
