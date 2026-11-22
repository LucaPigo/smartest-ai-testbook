# MVP Requirements — Smartest AI Testbook

## Goal and core value

The system enables a team to define tests for an LLM-based application, run them against a model, and obtain readable evaluations of the responses. Its core value is turning variable LLM outputs into measurable, reviewable results.

This project describes an MVP. Design only features needed to define a suite, run it, evaluate responses, review results, or export data.

## Functional requirements

### FR-1 — Manage test suites and test cases

- Users can create and edit a `TestSuite` with a name and description.
- A suite contains one or more `TestCase` objects.
- Each `TestCase` contains a stable ID, a nonblank title and prompt, optional variables, and one or more expectations. Variables default to an empty map.
- Each expectation contains its own ID, name, evaluator type, threshold and options. Exact and semantic checks require `options.expected`; judge checks require `options.rubric`. Criteria are nonblank strings and are not test-level fields.
- The system rejects unsupported evaluator types or options and invalid criteria or thresholds before saving a definition.
- The interface shows an expected-answer field for exact and semantic checks and a rubric field for judge checks, without requiring JSON options editing.
- Tests are editable; the system does not manage test versions. Each historical result records the original prompt template, but not the complete test definition.

### FR-2 — Run a suite

- Users select one model for a suite run. The application obtains it through a `ModelProvider`.
- Tests execute sequentially. The system sends each test's prompt and variables to the selected model once and collects one generated output.
- All of a test's expectations evaluate that same output sequentially. Reference answers and rubrics are never part of the model-under-test input.
- Each execution is represented by an `EvalRun` linked to the suite and its results.
- An error on one test is recorded in its `EvalResult` and does not discard the other results in the run.

### FR-3 — Evaluate responses

- Each generated output can be evaluated by one or more `Evaluator` implementations.
- All evaluator values and thresholds use the 0–1 scale and must be finite. Exact-match threshold is fixed to 1; semantic and judge thresholds are configurable within 0–1.
- Evaluators return a value and feedback. The runner alone applies `value >= threshold` and records expectation identity, the applied threshold and pass/fail status. Successful outcomes retain scale bounds 0 and 1; evaluation errors or invalid values produce failed outcomes with an error and no numeric value.
- The MVP starts with three strategies:
  - `ExactMatchEvaluator`: literal string equality against `options.expected`, scoring 0 or 1; differences in case, whitespace or JSON formatting fail;
  - `SemanticSimilarityEvaluator`: semantic similarity against `options.expected`;
  - `LlmJudgeEvaluator`: evaluation using an LLM and `options.rubric`.
- A test passes only when generation succeeds and all its expectations pass. An evaluation failure never stops later checks or tests; a generation failure skips that test's evaluations and continues with the next test.
- Sharing a 0–1 scale does not make different evaluation algorithms equivalent. The system does not average their values.

### FR-4 — Review the report

- At the end of a run, `EvalReport` lists the recorded `EvalResult` objects without aggregating them.
- The report makes the suite, run date, model/provider, test ID, generated output, applied evaluators, scores and scales, thresholds and outcomes, and feedback available for review.
- The report does not calculate an overall score or aggregate test results.

### FR-5 — Persistence and export

- Suites, test cases, runs, and results are stored in a database.
- Existing SQLite definitions with shared test-level criteria remain readable: the loader copies those criteria into the corresponding expectations when local options are absent. A normal save writes the new format; existing run history is preserved.
- Users can export a suite as JSON. The export includes the suite, its tests, and the related run and result history.
- The exported file can be stored and versioned outside the system; individual tests are not versioned inside the application.

## Essential non-functional requirements

- **Extensibility:** an evaluator or provider adapter can be added without changing the runner's core logic.
- **Error isolation:** an error for one test is recorded without losing other results in the run.
- **Minimum traceability:** each run records its date/time and provider/model; each result retains the test ID, output, and evaluations.

## Outside the MVP scope

Internal test versioning, automatic baseline/regression comparison, dashboards and live updates, accounts and permissions, CSV import/export, CI/CD and CLI, concurrent execution, retries/backoff, cost optimization, and selection of specific database or queue technologies.
