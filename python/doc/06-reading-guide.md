# 6. How to read the code

A common mistake is to open the biggest file first. In a layered project it is better
to read **from the inside out**: first the domain (the rules), then the wiring, then the
infrastructure (the details).

## Suggested reading order

Each step lists the files and what to look for. The whole domain is about 750 lines.

### Step 1 — The vocabulary (`test_creation/`)

| File | Look for |
|---|---|
| [`expectation.py`](../src/smartest_ai_testbook/test_creation/expectation.py) | `IExpectation` and `Expectation`; `validate_expectation`, which holds every rule of a check. |
| [`test_case.py`](../src/smartest_ai_testbook/test_creation/test_case.py) | `TestCase` (just data) and `TestCaseBuilder` (the **Builder**, with all the rules in `build()`). |
| [`test_suite.py`](../src/smartest_ai_testbook/test_creation/test_suite.py) | `TestSuite` and `add_test`. |
| [`repository.py`](../src/smartest_ai_testbook/test_creation/repository.py) | `SuiteRepository`: an interface with no implementation here. Ask yourself: who implements it? |
| [`test_catalog.py`](../src/smartest_ai_testbook/test_creation/test_catalog.py) | `TestCatalog`, the **application service**: one method per use case (find, change with the Builder, save through `SuiteRepository`), and the rule on expectation IDs. |

### Step 2 — Running and evaluating (`execution/`)

| File | Look for |
|---|---|
| [`model.py`](../src/smartest_ai_testbook/execution/model.py) | The `Model` and `ModelProvider` interfaces: what the runner needs from a model; `fill_variables`, shared by the real and mock models. |
| [`eval_run.py`](../src/smartest_ai_testbook/execution/eval_run.py) | `EvalRun`, `EvalResult`, `EvalScore`; the computed property `EvalResult.passed`. |
| [`exact_match_evaluator.py`](../src/smartest_ai_testbook/execution/exact_match_evaluator.py) | The `Evaluator` interface, the `Evaluation` record and the simplest **Strategy**. |
| [`eval_runner.py`](../src/smartest_ai_testbook/execution/eval_runner.py) | **The most important file.** The two loops, error handling, the threshold rule. |
| [`openai_model.py`](../src/smartest_ai_testbook/execution/openai_model.py) | The **Adapter** to OpenAI and the `{{variable}}` substitution. |
| [`semantic_similarity_evaluator.py`](../src/smartest_ai_testbook/execution/semantic_similarity_evaluator.py), [`llm_judge_evaluator.py`](../src/smartest_ai_testbook/execution/llm_judge_evaluator.py) | The other two strategies. Skim them: the interesting part is that they have the same `evaluate` signature. |
| [`mock_ai.py`](../src/smartest_ai_testbook/execution/mock_ai.py) | The offline mocks of the two AI integration points: `MockModel`/`MockProvider` (the SUT) and `MockEvaluator` (the AI evaluation service). Compare them with the OpenAI classes: same interfaces, no network. |
| [`repository.py`](../src/smartest_ai_testbook/execution/repository.py) | `RunRepository`. |
| [`run_service.py`](../src/smartest_ai_testbook/execution/run_service.py) | `RunService`, the application service for runs: provider check, runner call, saving the run. |

### Step 3 — Reports (`reporting/`)

| File | Look for |
|---|---|
| [`eval_report.py`](../src/smartest_ai_testbook/reporting/eval_report.py) | How a run is copied into an independent report. |

### Step 4 — The wiring (`composition.py`)

| File | Look for |
|---|---|
| [`composition.py`](../src/smartest_ai_testbook/composition.py) | The **composition root**: every concrete class is chosen and injected into the two application services here. Find each object you met in steps 1–3. |

### Step 5 — The infrastructure

| File | Look for |
|---|---|
| [`persistence/sqlite.py`](../src/smartest_ai_testbook/persistence/sqlite.py) | The two tables (`SuiteRow`, `RunRow`), the repositories and the conversions `_suite` / `_run`. |
| [`web_server/app.py`](../src/smartest_ai_testbook/web_server/app.py) | `create_app`, `deps()` and the routes grouped by resource. Every route calls one service operation and translates its outcome. |
| [`web_server/helpers.py`](../src/smartest_ai_testbook/web_server/helpers.py) | Translations between HTTP and domain: `domain_error` (ValueError → 422), `or_404` (None → 404), `*_json`, `new_expectation`. No business rules. |
| [`__main__.py`](../src/smartest_ai_testbook/__main__.py) | Four lines that start Uvicorn. |

### Step 6 — The tests (`tests/`)

Tests are executable documentation. Start with
[`test_composition.py`](../tests/test_composition.py) (the whole application without
HTTP, plus the independence check),
[`test_test_catalog.py`](../tests/test_test_catalog.py) and
[`test_run_service.py`](../tests/test_run_service.py) (every use case and rule, without HTTP) and
[`test_api_workflow.py`](../tests/test_api_workflow.py) (the HTTP workflow with a fake
model). Notice how fakes are injected.

Run them from the `python/` folder:

```sh
uv run pytest tests -v
```

## Questions to ask while reading any file

1. **Which ring is this file in?** Domain, infrastructure or wiring?
2. **What does it import?** If a domain file imported `fastapi` or `sqlalchemy`, the
   dependency rule would be broken.
3. **What does it receive and what does it create?** Collaborators should arrive through
   the constructor or as parameters.
4. **Which contract does each class implement?** Look at the `Protocol` in parentheses.
5. **Where are the rules?** Business rules belong to the domain; the web server only
   translates.

## Review questions

Try to answer without looking, then check in the code.

1. Which package defines `SuiteRepository` and which package implements it? Why this way round?
2. Why does `EvalRunner` receive a dict of evaluators instead of creating them?
3. Where is the decision `passed = value >= threshold` taken? Why not inside each evaluator?
4. What happens to the other tests of a run if the model fails on the first test?
5. A test case with a blank title arrives over HTTP. Which layer rejects it, and with which status code?
6. Why is the `openai` library imported inside an `if` in `composition.py`?
7. What does `create_app` do when it receives `dependencies`, and what does it do when it does not?
8. Which classes would change if we replaced SQLite with PostgreSQL? Which would not?
9. What are the two points where the application calls an AI service? Which expectation type never needs one?
10. Which file changes behavior when `AI_MODE=mock` is set, and which classes are unaware of it?
11. Where is the rule "expectation IDs must belong to this test case" checked? Why is it not in the HTTP route, and why not in `TestSuite` with a `save()` method?

## Exercises

1. **Draw the dependencies.** Open every file in `src/` and draw an arrow for each
   `import` between packages. Check that no arrow leaves the domain.
2. **A new strategy.** Design a `ContainsEvaluator` that returns 1 when the output
   *contains* the expected text. List every file you would have to touch. (Hint: the
   runner is not one of them. The list of supported evaluator types in
   `validate_expectation` and the API contract are.)
3. **A new adapter.** Sketch a `FakeModel` that always answers `"42"` and use it with
   `EvalRunner` in a short script, without the web server and without OpenAI.
   Then compare it with `MockModel` in `execution/mock_ai.py`.
4. **Run the application in mock mode.** Start the backend with `AI_MODE=mock`, create a
   suite with one expectation of each type, run it with the `Mock` provider and explain
   every score in the report. Then pick the `OpenAI` provider and explain the error.
5. **Follow a request.** Pick `PUT /api/expectations/{expectation_id}` and write, step by
   step as in [chapter 5](05-execution-order.md), what happens from the request to the
   response.

---

← [5. Order of execution](05-execution-order.md) · [Back to the lesson plan](README.md) · Appendices: [A. FastAPI](07-fastapi.md), [B. SQLAlchemy](08-sqlalchemy.md)
