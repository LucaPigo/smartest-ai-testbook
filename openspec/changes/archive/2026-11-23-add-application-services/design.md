# Design

## Context

See proposal.md for motivation and the delta spec for the required behavior.

- Python: `create_dependencies` returns `Dependencies(suites, runs, runner, provider)`. Routes in `web_server/app.py` call the repositories and runner directly; `web_server/helpers.py` holds `find_suite`, `find_case`, `find_expectation` (404 lookups across suites), `build_case` and `new_expectation`. The expectation-ID ownership check lives in `update_case`; the provider check and run saving live in `create_run`.
- `doc/domain-design.md` states that the application, for example an HTTP handler, is the caller and that subsystems need no wrapper classes.
- TypeScript has the same entities, builder, runner and strategies, but no repository contracts, persistence or HTTP workflow. It is out of scope for this change by decision of the project owner.
- Python tests: `test_composition.py` uses `dependencies.suites`, `.runner` and `.runs`; `test_api_workflow.py` replaces `dependencies.provider` with a fake.

## Goals / Non-Goals

**Goals:**
- One place per subsystem that owns the use-case sequences and their rules, with an explicit contract, usable with or without HTTP.
- Routes reduced to: validate transport input, call one service operation, translate the outcome.

**Non-Goals:**
- Any TypeScript change: services, repository contracts or domain adjustments. This is an accepted exception to the AGENTS.md parity rule, documented in the domain design.
- Active Record (entities saving themselves) or a generic unit-of-work.
- Changing the HTTP contract, status codes, messages or the storage format.
- Domain exception hierarchies; reporting or exporting services.

## Decisions

### Two application services, one per subsystem
| Contract (`Protocol`) | Implementation | Collaborators | Module |
|---|---|---|---|
| `ITestCatalog` | `TestCatalog` | `SuiteRepository` | `test_creation/test_catalog.py` |
| `IRunService` | `RunService` | `SuiteRepository`, `RunRepository`, `IEvalRunner`, `ModelProvider \| None` | `execution/run_service.py` |

Operations:

| `TestCatalog` | Result |
|---|---|
| `list_suites()` | suites |
| `create_suite(name, description)` | created suite |
| `update_suite(suite_id, name, description)` | suite or not found |
| `delete_suite(suite_id)` | `True` / `False` (not found) |
| `list_test_cases(suite_id)` | test cases or not found |
| `add_test_case(suite_id, title, prompt, variables, expectations)` | test case or not found |
| `get_test_case(case_id)` | test case or not found |
| `update_test_case(case_id, title, prompt, variables, expectations)` | test case or not found; validation error for foreign or duplicate expectation IDs |
| `delete_test_case(case_id)` | `True` / `False` |
| `list_expectations(case_id)` | expectations or not found |
| `add_expectation(case_id, expectation)` | expectation or not found |
| `update_expectation(expectation_id, expectation)` | expectation or not found |

| `RunService` | Result |
|---|---|
| `run_suite(suite_id, provider_name, model_name)` (async) | saved run or not found; validation error for an unconfigured provider, blank model name or empty suite |
| `list_runs(suite_id)` | runs or not found |
| `get_run(run_id)` | run or not found |

Expectations are passed as `IExpectation` values; the services build test cases with `TestCaseBuilder`, so all domain validation still runs in the builder. The lookups across suites (`find_case`, `find_expectation`) become private helpers of `TestCatalog`.
*Alternatives:* one service for the whole application (mixes subsystems and their collaborators); a service per entity (more classes than the use cases need); putting `save` on entities (Active Record, couples the domain to persistence).

### Outcomes without new exception classes
"Not found" is an empty result (`None`, or `False` for deletes); invalid input is the domain's existing `ValueError`, with the same messages the routes use today (`Expectation IDs must belong to this test case`, `Unknown provider or unavailable model configuration`, builder and runner messages). Each route knows its resource, so it keeps its own 404 message. The order of checks stays as today: existence first (404), then validation (422).
*Alternative:* a `NotFoundError` class; rejected as an extra class and contract for a two-value outcome.

### Composition and HTTP
`Dependencies` becomes `Dependencies(catalog: ITestCatalog, runs: IRunService)`, built by `create_dependencies`, which keeps creating repositories, runner and provider internally. A new optional `provider` parameter, like the existing `client` parameter, lets tests inject a fake model provider instead of mutating `Dependencies`. Routes call `deps().catalog` and `deps().runs`, translate empty results to 404 and `ValueError` to 422. `helpers.py` keeps only transport concerns: `invalid_request`, the `*_json` serializers and `new_expectation` (input model → domain `Expectation`).
*Alternative:* keep repositories in `Dependencies` and create services in the web server; rejected because the composition root must stay the single place that wires objects.

### Documentation
Replace the domain-design statements about the HTTP handler being the caller with an "Application services" section, add the two contracts and repositories to the class view, and state in the implementation boundaries that the services exist only in Python. Update `doc/web-architecture.md` and the Python lesson: the dependency diagram and rings (ch. 1), the border translation (ch. 2), `Dependencies` and the fake-provider example (ch. 3), an Application Service pattern entry (ch. 4), the request and run flows (ch. 5), the reading order (ch. 6) and `deps()` in Appendix A.

## Risks / Trade-offs

- [Behavior drift while moving logic] → Existing HTTP workflow tests keep their assertions unchanged and must pass; service tests cover each rule directly.
- [More classes to explain] → One service per subsystem, named after the use cases; the lesson presents them as the place where use cases live.
- [The two domain implementations diverge further] → Accepted by the project owner; the difference is documented in `doc/domain-design.md` and `doc/web-architecture.md`, so the TypeScript domain is not read as equivalent.
- [`Dependencies` shape change breaks callers] → Only the web server, `browser_server.py` and tests use it; all are updated in the same tasks.

## Migration Plan

No data or API migration. Stored suites and runs are read and written by the same repositories.
