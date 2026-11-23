# Design

## Context

See proposal.md for motivation and the specs for the required behavior.

- The SUT is reached through the `Model` / `ModelProvider` contracts; `OpenAIModel` and `OpenAIProvider` are the only implementations. `OpenAIModel` fills `{{variable}}` placeholders before calling the API.
- AI evaluation is reached through the `Evaluator` Strategy contract. The runner selects a strategy by `evaluator_type` from a dict it receives at construction.
- Python: `create_dependencies` in `composition.py` creates the provider and evaluator dict once at startup; without an OpenAI client, `provider` is `None` and only `exactMatch` is registered. `create_run` in `web_server/app.py` accepts only `provider_name == "openai"`.
- TypeScript: the same domain contracts exist; there is no composition module and the HTTP server is health-only. Tests and `src/examples/run-suite.ts` create providers as object literals.
- The web client run page sends `providerName: 'openai'` from a disabled selector.

## Goals / Non-Goals

**Goals:**
- Replace each AI integration point with a mock by plugging another implementation into the existing contracts, with no change to `EvalRunner`, the API contract or persistence.
- Keep the mocks small enough to be read in class as further examples of Adapter and Strategy.

**Non-Goals:**
- Simulating realistic answers, latency, random failures or varied scores.
- Choosing evaluators per run, or mixing a mock SUT with real evaluators (or the opposite).
- A TypeScript composition module, `AI_MODE` handling or HTTP routes in TypeScript.
- An endpoint that tells the client which provider is configured.

## Decisions

### Mocks are domain implementations of the existing contracts
Add one module per language next to the OpenAI adapters (`execution/mock_ai.py`, `execution/mock-ai.ts`) containing:
- `MockModel` implementing `Model`: `provider_name = "mock"`, answers `"[mock] " + filled prompt`.
- `MockProvider` implementing `ModelProvider`: returns `MockModel(model_name)` for any name.
- `MockEvaluator` implementing `Evaluator`: calls `validate_expectation`, then returns `Evaluation(value=1, feedback="Mock evaluation")`.

One `MockEvaluator` class is registered under both `semanticSimilarity` and `llmJudge`, because the mock behavior is identical for both.
*Alternatives:* two mock evaluator classes (duplicated code with no behavioral difference); test doubles under `tests/` (not usable by the running application, which is the point of the change).

### Shared prompt variable substitution
Move the `{{variable}}` substitution out of `OpenAIModel` into a function in the `model` module (`fill_variables` / `fillVariables`) used by both `OpenAIModel` and `MockModel`. This guarantees the mock shows exactly the prompt the real SUT would receive.
*Alternative:* duplicating the regular expression in the mock; rejected because the two could diverge.

### `ModelProvider` exposes its provider name
Add `provider_name` / `providerName` to the `ModelProvider` contract (`"openai"` for `OpenAIProvider`, `"mock"` for `MockProvider`). `create_run` then rejects a request when `provider is None or data.provider_name != provider.provider_name`, replacing the hard-coded `"openai"`. The run still records the name reported by the model.
*Alternatives:* a separate `provider_name` field in `Dependencies` (two values to keep consistent); a dict of providers keyed by name (more structure than one configured provider needs).

### One startup switch in the composition root
`create_dependencies(database_url=None, client=None, ai_mode=None)` reads `ai_mode or os.getenv("AI_MODE")`. When it is `"mock"`: no OpenAI client is created, the provider is `MockProvider()` and the evaluators are `exactMatch` (real) plus `MockEvaluator` for the two AI types. Otherwise the current code path runs unchanged. The parameter mirrors `database_url` so tests do not need to patch the environment. Any value other than `mock` means default mode; no extra validation of this trusted startup setting.
*Alternative:* automatic fallback when no key exists; rejected by the user because a missing key would silently produce mock runs.

### Web client selector
Enable the provider `<select>` with `OpenAI` (`openai`, default) and `Mock` (`mock`) options, keep the chosen value in state and send it as `providerName`. A mismatch with the backend configuration is shown through the existing error display.

### Configuration and documentation
Pass `AI_MODE: ${AI_MODE:-}` to the Python Compose service. Document the two AI integration points and mock mode in `doc/domain-design.md`, `doc/web-architecture.md`, `doc/glossary.md`, `python/readme.md` and the `python/doc/` lesson (chapters on dependency injection, patterns and execution order).

## Risks / Trade-offs

- [Mock runs look like real runs in stored history] → The provider is recorded as `mock` and every output starts with `[mock] `, so reports are unambiguous.
- [Exact match always fails on mock answers] → Accepted and documented: it shows the failure path, while the AI evaluators show the success path. The goal is the flow, not the result.
- [Changing the `ModelProvider` contract breaks existing fakes] → Update the fakes in the TypeScript tests and example and in the Python HTTP tests in the same tasks.
- [The client cannot know which provider is configured] → The user picks it; a wrong choice returns an understandable 422, as already happens without an OpenAI key.

## Migration Plan

No data migration. Default behavior is unchanged when `AI_MODE` is unset; removing the variable and restarting the backend returns to OpenAI mode. Existing stored runs are unaffected.
