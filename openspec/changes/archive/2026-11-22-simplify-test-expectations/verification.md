# Verification

Verified on 2026-11-22 using Windows, Node 24.22.1 for the final TypeScript checks and client build, Python 3.12.0, the pinned OpenAPI generators and installed Chrome. Initial checks and browser harnesses also passed with Node 22.22.3.

## Results

| Check | Result |
|---|---|
| TypeScript `npm test` | 25 passed; all three strategies exercised offline through the official OpenAI SDK and fake HTTP responses. |
| TypeScript `npm run typecheck` | Passed. |
| Python `.venv/Scripts/python.exe -m pytest tests -q` | 68 passed and 8 subtests passed, including domain, persistence, composition and HTTP workflows. |
| Client `npm run build` | Passed; generated and handwritten code typechecked together. |
| `npm run api:check` | All three generated targets match the canonical contract. |
| OpenAPI Generator validation | Both `api/openapi.yaml` and `api/openapi.domain.yaml` passed. |
| `openspec validate --all --strict` | All four existing specs/changes passed, including this change. |
| Fake-API browser workflow | Passed: creation, editing, guided criteria, evaluator switching, exact threshold and bounded thresholds, IDs, navigation and errors. |
| Real-backend browser workflow | Create and verify phases passed against FastAPI and SQLite with fake external model responses; backend was stopped and restarted between phases. |
| `npm run verify:browser` | Shared HTTP/CORS checks and eight browser configuration/connectivity scenarios passed. |
| Editor diagnostics | No errors found across the workspace. |
| Documentation checks | Both Excalidraw files parse with unique IDs; changed text fits its containers; examples match the new contract. |
| `git diff --check` | Passed. |

The real-backend browser test creates a test with exact, semantic and two independent judge expectations. It checks the generated response, edits criteria and evaluator types while preserving IDs, restarts the backend, and verifies that new definitions and original recorded outcomes both remain available. Browser console errors and warnings are asserted absent. Form layout was checked at 320, 768, 1024 and 1440 pixels, keyboard navigation was exercised, and a screenshot was visually inspected.

The legacy-storage regression loads shared reference/rubric fields into local options, gives existing local criteria precedence, preserves identifiers and variables, proves reads do not rewrite rows, resaves the new definition shape, and verifies unchanged recorded runs. Existing local database files were not used for test writes; their SHA-256 hashes remained unchanged.

## Review and regression evidence

- New definition tests failed against the old shared-criteria model before implementation and passed afterward.
- Temporarily changing the inclusive threshold comparison from `>=` to `>` caused failures in both languages; the correct comparison was restored and final suites passed.
- Review caught Python treating boolean embedding indices as integer indices. Both languages now reject those malformed provider responses and include regression cases.
- HTTP regression tests caught non-finite validation input causing FastAPI's error response to fail JSON serialization. The response now returns HTTP 422 with JSON-safe error details; overflow, NaN and positive/negative infinity cases pass without partial writes.

## Verification limits

No live paid OpenAI request was made. Deterministic fake external responses verify adapter requests, evaluator parsing and error handling without claiming live credentials, model access or model quality. TypeScript's HTTP server still implements health only; the new domain strategies do not imply CRUD HTTP or persistence parity. JSON export and container deployment remain outside this change.

Pytest still reports the existing collection warnings for imported domain classes and the Starlette/AnyIO deprecation warning. The client build still reports React Router's existing ignored `use client` directive notice. Neither prevents the checks above from passing.

The TypeScript OpenAI SDK is pinned to 7.62.0. Its request shapes were verified against the official [embeddings reference](https://developers.openai.com/api/reference/typescript/resources/embeddings/methods/create) and [structured-output guide](https://developers.openai.com/api/docs/guides/structured-outputs).
