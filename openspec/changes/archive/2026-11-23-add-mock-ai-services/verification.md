# Verification

Verified on 2026-11-23 using Windows, Node 22.22.3, Python 3.12.0 and installed Chrome.

## Results

| Check | Result |
|---|---|
| `openspec validate add-mock-ai-services --strict` | Valid. |
| TypeScript `npm test` | 28 passed, including 3 new mock tests (mock answer and identity, mock evaluator score and validation, mock run through `EvalRunner`). |
| TypeScript `npm run typecheck` | Passed. |
| Python `.venv/Scripts/python.exe -m pytest tests -q` | 76 passed and 8 subtests passed: 3 domain mock tests equivalent to TypeScript, 2 composition tests (mock mode ignores a configured OpenAI key; default mode unchanged), 2 HTTP tests (stored mock run, 422 for providers that are not configured in both modes). |
| Client `npm run build` | Passed. |
| `docker compose config` with `AI_MODE=mock` | Passed; the Python service receives `AI_MODE: mock`. |
| Real-backend browser check (mock mode) | Python backend started with `AI_MODE=mock`, a temporary SQLite database and no OpenAI key; Vite dev client. Selecting `OpenAI` displayed `Request failed (422): Unknown provider or unavailable model configuration`. Selecting `Mock` opened the report with `mock / demo`, output `[mock] Capital of France?`, exact match failed with score 0, semantic similarity and LLM judge passed with score 1 and `Mock evaluation`, test failed. No page errors. |
| Fake-API browser workflow (`web-client/tests/workflow.mjs`) | Passed against the Vite dev client; the default `openai` provider path is unchanged. |
| Editor diagnostics | No errors or warnings in the workspace. |
| Lesson links | All relative links in `python/doc/` resolve. |
| `git diff --check` | Passed. |

## Parity review

- `fillVariables` / `fill_variables` are shared by the OpenAI and mock models in both languages, with identical placeholder behavior.
- `MockModel`, `MockProvider` and `MockEvaluator` have the same names, provider name (`mock`), output format, score and feedback in both languages; the equivalent tests assert the same outputs, scores and outcomes.
- `ModelProvider` exposes `providerName` / `provider_name` in both languages.
- `AI_MODE` handling, the provider check and the HTTP tests exist only in Python, because the TypeScript server is health-only; this is documented in `doc/web-architecture.md` and `doc/domain-design.md`.

## Not run

- The real-backend Playwright script `web-client/tests/integration.mjs` was not rerun; it uses the default `openai` provider with a fake OpenAI client, a path covered by the Python HTTP tests and the fake-API workflow above.
- No live OpenAI request was made; default-mode behavior is covered by the unchanged offline OpenAI tests.
