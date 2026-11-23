# Proposal

## Why

An AI service is involved at two points of the application: the **system under test (SUT)**, the model that answers each prompt during a run, and the **AI evaluation service**, used only by `semanticSimilarity` and `llmJudge` expectations (`exactMatch` needs none). Today both require a real OpenAI key, model access and paid calls, so the complete workflow cannot be demonstrated in class, exercised in a browser or checked end to end without credentials. Mock replacements for both services let anyone validate the application flow; the goal is to check the flow, not the quality of the results.

## What Changes

- Document the two AI integration points (SUT during a run, evaluation service when an AI expectation exists) in the domain and web architecture documents and in the Python lesson.
- Add a mock SUT: a mock model provider whose models answer with the prompt after filling in its variables, clearly marked as a mock answer, without network calls.
- Add a mock AI evaluator used in place of semantic similarity and LLM judge: it validates the expectation as usual and always returns score 1 with the feedback `Mock evaluation`, without network calls. Exact match stays the real deterministic evaluator.
- Add one backend startup switch, `AI_MODE=mock`, that replaces both AI services with their mocks at the same time. Without it the current OpenAI behavior is unchanged.
- Model providers expose their provider name, and the Python server accepts a run only when its requested provider is the configured one (`openai` by default, `mock` in mock mode).
- The web client run page lets the user choose the `OpenAI` or `Mock` provider instead of a fixed, disabled `OpenAI` option.
- Implement the domain mocks in TypeScript first and then in Python. The TypeScript HTTP server stays health-only, so TypeScript gets the domain classes, tests and the existing example; Python also gets composition, HTTP and tests.

## Capabilities

### New Capabilities
- `mock-ai-services`: deterministic offline replacements for the SUT model and the AI evaluation service, the startup switch that enables them together, provider selection for mock runs and equivalent behavior in both languages.

### Modified Capabilities
- `suite-execution`: the requirement "Select a real provider" changes so that a run is accepted only for the provider configured at startup, which is OpenAI unless mock mode is enabled.

## Impact

- **Domain (TypeScript, Python)**: `ModelProvider` gains a provider name; new mock model, mock provider and mock evaluator classes in `execution/`; prompt variable substitution shared by the OpenAI and mock models.
- **Python composition and HTTP**: `create_dependencies` reads `AI_MODE`; `create_run` compares the requested provider with the configured one. No API contract change: `provider_name` is already a free string.
- **Web client**: provider selector on the run configuration page.
- **Configuration**: new optional `AI_MODE` variable for the Python backend and its Compose service.
- **Tests**: new domain tests in both languages, Python composition and HTTP tests in mock mode; existing fake providers gain a provider name.
- **Documentation**: `doc/domain-design.md`, `doc/web-architecture.md`, `doc/glossary.md`, `python/readme.md` and the `python/doc/` lesson.
- **No new dependencies.**
