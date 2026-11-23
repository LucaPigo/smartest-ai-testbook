# Tasks

## 1. Document the two AI integration points and mock mode

- [x] 1.1 Update `doc/domain-design.md` (two AI integration points, `ModelProvider.providerName`, mock classes in the pattern view), `doc/glossary.md` (mock mode, AI evaluation service) and `doc/web-architecture.md` (`AI_MODE`, provider check, current TypeScript/Python differences); verify the documents agree with the specs and with each other.

## 2. Implement TypeScript first

- [x] 2.1 Extract `fillVariables` into `execution/model.ts`, use it in `OpenAIModel`, and add `providerName` to `ModelProvider` and `OpenAIProvider`; update the object-literal providers in tests and `src/examples/run-suite.ts`; verify `npm test` and `npm run typecheck` pass with unchanged OpenAI behavior.
- [x] 2.2 Add `execution/mock-ai.ts` with `MockModel`, `MockProvider` and `MockEvaluator`, each explicitly implementing its interface; add `mock-ai.test.ts` covering the mock answer with variables, provider and model identity, score 1 / `Mock evaluation` for semantic and judge expectations, expectation validation errors, and exact match failing on the mock answer through `EvalRunner`; verify `npm test` and `npm run typecheck` pass before editing Python.

## 3. Align the Python domain

- [x] 3.1 Mirror 2.1 in Python: `fill_variables` in `execution/model.py`, used by `OpenAIModel`; `provider_name` on `ModelProvider` and `OpenAIProvider`; verify `uv run pytest tests` passes.
- [x] 3.2 Add `execution/mock_ai.py` with `MockModel`, `MockProvider` and `MockEvaluator` explicitly implementing their `Protocol`s, and domain tests equivalent to 2.2; verify the outputs, scores, feedback and outcomes match the TypeScript tests.

## 4. Python composition and HTTP

- [x] 4.1 Add the `ai_mode` parameter and `AI_MODE` handling to `create_dependencies`; extend `tests/test_composition.py` to check that mock mode creates no OpenAI client, uses the mock provider and evaluators, runs a suite with all three expectation types without HTTP, and that default mode is unchanged; verify with `uv run pytest tests`.
- [x] 4.2 Replace the hard-coded `"openai"` check in `create_run` with the configured provider's name; give the fake providers in `tests/test_api_workflow.py` a provider name; add HTTP tests for a stored mock run and for the 422 provider mismatch in both modes; verify with `uv run pytest tests`.
- [x] 4.3 Pass `AI_MODE` to the Python service in `compose.yaml` and document `AI_MODE=mock` in `python/readme.md`; verify the Compose file parses (`docker compose config`) or record that Docker is unavailable.

## 5. Web client

- [x] 5.1 Enable the provider selector on the run configuration page with `OpenAI` (default) and `Mock` options and send the selected `providerName`; verify the client build passes and, in a browser against the Python backend started with `AI_MODE=mock`, a mock run shows provider `mock`, `[mock]` outputs, passed AI expectations and a failed exact match, while selecting `OpenAI` shows the backend error.

## 6. Python lesson

- [x] 6.1 Update the `python/doc/` lesson: the two AI integration points, mock mode as a dependency-injection example in chapter 3, the mocks as Adapter and Strategy examples in chapter 4, and mock mode in the execution order of chapter 5; verify internal links and code excerpts match the implementation.

## 7. Final integration

- [x] 7.1 Review the change for cross-language parity and contract propagation; run `openspec validate add-mock-ai-services --strict`, TypeScript tests and type checking, Python tests, the client build and editor diagnostics; record actual results in this change.

## Workflow follow-up

- Keep the completed change available for review; archive only when requested.
