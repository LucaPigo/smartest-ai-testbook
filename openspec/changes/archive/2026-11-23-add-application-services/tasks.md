# Tasks

## 1. Document the application services

- [x] 1.1 Update `doc/domain-design.md` (replace "the HTTP handler is the caller / no wrapper classes" with an Application services section, add `ITestCatalog`, `IRunService`, `SuiteRepository` and `RunRepository` to the class view, update the execution sequence, state that the services exist only in Python) and `doc/web-architecture.md` (routes delegate to services; TypeScript has no services); verify the documents agree with the spec and design.

## 2. Python domain services

- [x] 2.1 Add `TestCatalog` (`test_creation/test_catalog.py`) implementing `ITestCatalog`, with tests on temporary SQLite databases: create, update and delete suites; add, read, update and delete test cases; list, add and update expectations; ID preservation; the foreign and duplicate expectation-ID rule; not-found results; nothing saved on validation errors. Verify `uv run pytest tests`.
- [x] 2.2 Add `RunService` (`execution/run_service.py`) implementing `IRunService`, with tests using the mock provider: saved run, list and get runs, not-found suite and run, unconfigured provider, blank model name, empty suite, nothing saved on errors. Verify `uv run pytest tests`.

## 3. Python composition and HTTP

- [x] 3.1 Change `Dependencies` to expose `catalog` and `runs`, add the optional `provider` parameter to `create_dependencies`, and update `tests/test_composition.py` and `tests/browser_server.py`; verify the composition tests, including mock mode and the no-FastAPI import check.
- [x] 3.2 Make the routes in `web_server/app.py` call the services and translate empty results to 404 and `ValueError` to 422; remove lookups, `build_case` and orchestration from `helpers.py`; update `tests/test_api_workflow.py` only where it builds dependencies, keeping every HTTP assertion unchanged; verify `uv run pytest tests`.

## 4. Python lesson

- [x] 4.1 Update `python/doc/` chapters 1–6 and Appendix A for the application services (layers and dependency diagram, border translation, `Dependencies` and fake provider, Application Service pattern, request and run flows, reading order, `deps()`), keeping comments and lesson style; verify code excerpts match the implementation and internal links resolve.

## 5. Final integration

- [x] 5.1 Confirm TypeScript is untouched (`git diff --stat typescript/` is empty); run `openspec validate add-application-services --strict`, Python tests, the client build, the fake-API browser workflow and editor diagnostics; record actual results in `verification.md`.

## Workflow follow-up

- Keep the completed change available for review; archive only when requested.
