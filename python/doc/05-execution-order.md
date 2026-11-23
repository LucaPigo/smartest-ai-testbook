# 5. Order of execution

In this chapter we follow the program while it runs. We look at three moments:

1. **Startup**: from the command line to a server waiting for requests.
2. **A simple request**: creating a test case.
3. **The main use case**: running a suite and evaluating the answers.

## 1. Startup

The server is started with:

```sh
uv run python -m smartest_ai_testbook
```

`python -m package` runs the file `__main__.py` of that package. Here is what happens,
in order:

```mermaid
sequenceDiagram
    participant Shell
    participant Main as __main__.py
    participant App as web_server/app.py
    participant Uvicorn

    Shell->>Main: python -m smartest_ai_testbook
    Main->>App: import app
    Note over App: Module code runs:<br/>app = create_app()
    Note over App: FastAPI app created, routes registered,<br/>dependencies = None (not created yet)
    App-->>Main: app
    Main->>Uvicorn: uvicorn.run(app, port=3002)
    Note over Uvicorn: Waits for HTTP requests
```

1. [`__main__.py`](../src/smartest_ai_testbook/__main__.py) imports `app` from `web_server/app.py`.
2. Importing a module runs its top-level code. The last line of `app.py` is
   `app = create_app()`.
3. `create_app` creates the FastAPI object, registers the error handler and the CORS
   middleware, and registers every route (each `@app.get`, `@app.post`, … decorator
   runs once now and records "for this method and path, call this function").
   The route functions themselves do **not** run yet.
4. `uvicorn.run` starts the HTTP server, which waits for requests.

Notice what has **not** happened yet: no database has been opened, no OpenAI client
created. `create_app` only stored `dependencies = None`.

### The first request: lazy creation of the dependencies

Every route calls `deps()`. The first time, `app.state.dependencies` is `None`, so
`deps()` calls `create_dependencies()` ([chapter 3](03-dependency-injection.md)):

1. `create_database(url)` creates the SQLAlchemy engine and the tables if they do not exist;
2. if `AI_MODE=mock`, the mock provider and mock evaluator are chosen; otherwise, if
   `OPENAI_API_KEY` is set, an OpenAI client is created;
3. the evaluators, the repositories, the runner and the provider are created and connected.

From the second request on, `deps()` returns the same objects.

## 2. A simple request: creating a test case

The browser sends:

```http
POST /api/test-cases
Content-Type: application/json

{"suite_id": "…", "title": "Capital", "prompt": "Capital of {{country}}?",
 "variables": {"country": "France"},
 "expectations": [{"name": "Exact", "evaluator_type": "exactMatch",
                   "threshold": 1, "options": {"expected": "Paris"}}]}
```

```mermaid
sequenceDiagram
    actor Client as Browser
    participant F as FastAPI
    participant R as create_case (route)
    participant H as helpers
    participant B as TestCaseBuilder
    participant S as TestSuite
    participant Repo as SQLAlchemySuiteRepository

    Client->>F: POST /api/test-cases (JSON)
    Note over F: Find the route for POST /api/test-cases<br/>Validate JSON with CreateTestCaseInput
    alt invalid shape
        F-->>Client: 422 (invalid_request handler)
    end
    F->>R: create_case(data)
    R->>H: find_suite(suites, data.suite_id)
    H->>Repo: get(suite_id)
    Repo-->>H: TestSuite or None
    alt suite not found
        H-->>Client: 404 (HTTPException)
    end
    R->>H: build_case(data, [new_expectation(e), ...])
    H->>B: set_title, set_prompt, set_variables, add_expectation
    H->>B: build()
    Note over B: Check domain rules
    alt rule broken (ValueError)
        H-->>Client: 422 (HTTPException)
    end
    B-->>R: TestCase
    R->>S: add_test(case)
    R->>Repo: save(suite)
    R->>H: case_json(case)
    R-->>F: dict
    F-->>Client: 201 + JSON
```

Step by step:

1. **Routing.** FastAPI finds the function registered with `@app.post("/api/test-cases")`.
2. **Shape validation.** The argument `data: CreateTestCaseInput` tells FastAPI to read
   the JSON body and validate it with that Pydantic model. If a field is missing or has
   the wrong type, the route is not even called: the client gets `422`.
3. **Lookup.** `find_suite` asks the repository for the suite; if it does not exist, it
   raises `HTTPException(404)`.
4. **Transport → domain.** `new_expectation` turns each input expectation into a domain
   `Expectation`.
5. **Domain validation.** `build_case` uses the **Builder**. If a domain rule is broken,
   `build()` raises `ValueError`, which `build_case` translates into `422`.
6. **Domain operation.** `suite.add_test(case)` adds the test to the suite.
7. **Persistence.** `suites.save(suite)` stores the whole suite (test cases are stored
   inside their suite).
8. **Domain → transport.** `case_json` turns the test case into a dict; FastAPI sends it
   as JSON with status `201 Created`.

Every other CRUD route follows the same shape: *validate → find → build or change domain
objects → save → serialise*.

## 3. The main use case: running a suite

The browser sends `POST /api/test-suites/{suite_id}/eval-runs` with
`{"provider_name": "openai", "model_name": "gpt-4o-mini"}`.

### In the web server

```python
# web_server/app.py — create_run (simplified)
suite = find_suite(deps().suites, suite_id)                 # 404 if missing
provider = deps().provider                                  # OpenAI, mock, or None without an API key
if provider is None or data.provider_name != provider.provider_name or not data.model_name.strip():
    raise HTTPException(422, ...)                           # only the configured provider is accepted
run = await deps().runner.run(suite, provider.get_model(data.model_name))
deps().runs.save(run)
return run_json(run)
```

The route is `async def` because running a suite waits for the network many times.
While a route is waiting at an `await`, the server can serve other requests.

### In the domain: `EvalRunner.run`

This is the heart of the application, in
[`execution/eval_runner.py`](../src/smartest_ai_testbook/execution/eval_runner.py).
It contains **two nested loops**: over the tests, and for each test over its expectations.

```mermaid
sequenceDiagram
    participant Route as create_run
    participant Runner as EvalRunner
    participant Model as Model (OpenAIModel)
    participant Ev as Evaluator (strategy)

    Route->>Runner: await run(suite, model)
    Note over Runner: Empty suite? → ValueError → 422<br/>Create EvalRun(suite.id, provider, model)
    loop for each test in suite.tests
        Runner->>Model: await generate_response(prompt, variables)
        alt model error
            Note over Runner: EvalResult with error, no scores
        else answer received
            Note over Runner: EvalResult with output
            loop for each expectation in test.expectations
                Note over Runner: evaluator = evaluators[expectation.evaluator_type]
                Runner->>Ev: await evaluate(test, output, expectation)
                alt evaluation error or invalid value
                    Note over Runner: EvalScore(passed=False, error=...)
                else Evaluation(value, feedback)
                    Note over Runner: EvalScore(passed = value >= threshold)
                end
            end
        end
        Note over Runner: run.add_result(result)
    end
    Runner-->>Route: EvalRun
```

The rules applied by the runner:

1. **One answer per test.** The model is called once per test; every expectation
   evaluates that same answer.
2. **Errors stay local.** A model error fails only that test; an evaluator error fails
   only that expectation. The run always continues with the next test or expectation.
3. **The runner decides.** Evaluators return a value from 0 to 1; the runner checks it
   is a valid number and decides `passed = value >= threshold`.
4. **A test passes only if everything passes.** `EvalResult.passed` is a computed
   property, not a stored flag:

   ```python
   @property
   def passed(self) -> bool:
       return (self.error is None and self.output is not None
               and bool(self.scores) and all(score.passed for score in self.scores))
   ```

Tests and expectations run **in order, one at a time**: there is no parallelism, retry or
weighting. This keeps the behaviour simple to predict and explain.

### The two AI calls in the run

In the diagram above an AI service is called at two points only:

1. `Model.generate_response`: the **system under test** answers the prompt, once per test;
2. `Evaluator.evaluate`, but only for `semanticSimilarity` and `llmJudge` expectations:
   the **AI evaluation service** scores the answer. `exactMatch` compares texts locally.

In mock mode (`AI_MODE=mock`) both calls go to offline mocks. With the prompt
`Capital of {{country}}?`, the variable `country=France` and three expectations, the run
records:

| Step | Result |
|---|---|
| Mock model answer | `[mock] Capital of France?` |
| `exactMatch` expecting `Paris` | score 0, failed (real comparison) |
| `semanticSimilarity`, threshold 0.8 | score 1, passed, feedback `Mock evaluation` |
| `llmJudge`, threshold 0.8 | score 1, passed, feedback `Mock evaluation` |
| Test outcome | failed, because one expectation failed |

The sequence of calls is exactly the same as with real models: this is what the mocks
are for. They validate the flow, not the results.

### Back in the web server

`deps().runs.save(run)` stores the run in its own table, then `run_json(run)` serialises
it and FastAPI answers `201 Created`. The browser shows each test, its output, the score
of every expectation and whether it passed.

### And the reporting subsystem?

`ReportGenerator.generate(run)` creates an `EvalReport`, an independent copy (snapshot) of
a finished run. Today it is used by the domain tests
(`tests/test_definitions_and_reporting.py`); the web server sends the stored run
directly with `run_json`.

## Summary of the whole journey

```mermaid
flowchart LR
    A["HTTP request"] --> B["FastAPI<br/>routing + Pydantic validation"]
    B --> C["Route in app.py"]
    C --> D["helpers.py<br/>find / build / translate"]
    D --> E["Domain objects<br/>Builder, Suite, Runner, Strategies"]
    E --> F["Repository<br/>SQLite"]
    C --> G["helpers.py<br/>*_json"]
    G --> H["HTTP response (JSON)"]
```

---

← [4. Design patterns](04-design-patterns.md) · Next: [6. How to read the code →](06-reading-guide.md)
