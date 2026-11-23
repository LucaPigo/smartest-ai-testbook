# Verification

Verified on 2026-11-23 using Windows, Node 22.22.3, Python 3.12.0 and installed Chrome.

## Results

| Check | Result |
|---|---|
| `openspec validate add-application-services --strict` | Valid. |
| Python `.venv/Scripts/python.exe -m pytest tests -q` | 87 passed and 8 subtests passed: 5 new `TestCatalog` tests, 4 new `RunService` tests (5 cases), and a new composition test for the same rules without HTTP. |
| HTTP assertions | `tests/test_api_workflow.py` changed only in `make_client` (provider injected through `create_dependencies(provider=...)`); every HTTP assertion is unchanged and passes. |
| HTTP behavior before/after | A scripted sequence of 41 requests in mock mode (successes, 24 responses with 404 or 422, including foreign and duplicate expectation IDs, unconfigured provider, blank model, empty suite and cascade delete) produced identical status codes and bodies, with IDs and dates normalized, on the previous commit and on this change. |
| TypeScript untouched | `git diff --stat -- typescript/` and `git status --short typescript/` are empty. |
| Client `npm run build` | Passed. |
| Fake-API browser workflow (`web-client/tests/workflow.mjs`) | Passed against the Vite dev client. |
| Editor diagnostics | No errors or warnings in the workspace; `app.py` and `composition.py` checked explicitly. Pylance did not report an analysis for the new `test_catalog.py` and `run_service.py`, which were not open in the editor. |
| Lesson links | All relative links in `python/doc/` resolve; no remaining references to removed helpers or `Dependencies` fields. |
| `git diff --check` | Passed. |

## Scope notes

- By decision of the project owner, TypeScript is out of scope; `doc/domain-design.md` and `doc/web-architecture.md` document that the application services and repository contracts exist only in Python.
- The web server now registers a `ValueError` handler that answers 422 with `{"detail": message}`, the same body the previous `HTTPException(422)` translations produced.
