"""HTTP API of the application, built with FastAPI.

How a request flows through this file:
1. The client sends an HTTP request, for example `GET /api/test-suites`.
2. FastAPI finds the function registered for that method and path (a "route").
3. FastAPI reads and validates the input (path parameters and JSON body) and
   passes it to the function as normal Python arguments.
4. The function uses the domain objects to do the work and returns a value.
5. FastAPI converts the returned value to JSON and sends it back.

The routes contain only HTTP logic. The real work is done by the domain classes,
and small reusable helpers live in `helpers.py`.
"""

import os
from uuid import UUID

from fastapi import FastAPI, HTTPException, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from smartest_ai_testbook.composition import Dependencies, create_dependencies
from smartest_ai_testbook.test_creation.test_suite import TestSuite
# Input models generated from the OpenAPI contract (api/). They are Pydantic classes:
# FastAPI uses them to check that the request body has the expected fields and types.
from smartest_ai_testbook.web_server.generated.models.create_expectation_input import CreateExpectationInput
from smartest_ai_testbook.web_server.generated.models.create_test_case_input import CreateTestCaseInput
from smartest_ai_testbook.web_server.generated.models.eval_run_input import EvalRunInput
from smartest_ai_testbook.web_server.generated.models.expectation_input import ExpectationInput
from smartest_ai_testbook.web_server.generated.models.health_response import HealthResponse
from smartest_ai_testbook.web_server.generated.models.test_case_input import TestCaseInput
from smartest_ai_testbook.web_server.generated.models.test_suite_input import TestSuiteInput
from smartest_ai_testbook.web_server.helpers import (
    build_case, case_json, expectation_json, find_case, find_expectation, find_suite,
    invalid_request, new_expectation, run_json, suite_json,
)


def create_app(dependencies: Dependencies | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Tests can pass their own `dependencies` (for example a temporary database).
    When nothing is passed, the real dependencies are created on first use.
    """
    app = FastAPI()

    # When the request body is invalid, FastAPI raises RequestValidationError and
    # answers with status 422. We replace the default handler with our own (see helpers.py).
    app.add_exception_handler(RequestValidationError, invalid_request)

    # CORS: browsers block calls from a web page to a server on another origin
    # (here the web client on port 3000 calls this server on another port).
    # This middleware tells the browser which origin, methods and headers are allowed.
    app.add_middleware(CORSMiddleware, allow_origins=[os.getenv("WEB_ORIGIN", "http://localhost:3000")],
                       allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Content-Type"])

    # `app.state` is a place where FastAPI lets us store shared objects.
    app.state.dependencies = dependencies

    def deps():
        # Create the real dependencies only when the first request needs them,
        # so importing this module does not open the database.
        if app.state.dependencies is None:
            app.state.dependencies = create_dependencies()
        return app.state.dependencies

    # --- Routes ---------------------------------------------------------------
    # A decorator such as `@app.get("/path")` registers the function below it as
    # the handler for HTTP GET requests on that path. Likewise for post, put and delete.
    #
    # How FastAPI fills the function arguments:
    # - `{suite_id}` in the path becomes the `suite_id` argument. The type hint
    #   `UUID` makes FastAPI reject values that are not valid UUIDs.
    # - An argument typed with a Pydantic model (e.g. `data: TestSuiteInput`) is
    #   read from the JSON body and validated.
    #
    # `status_code=` sets the status of a successful response (default 200 OK).
    # `raise HTTPException(...)` stops the function and returns an error status.

    # Health

    @app.get("/health")
    def get_health() -> HealthResponse:
        # Lets clients check that the server is running.
        return HealthResponse(status="ok")

    # Test suites

    @app.get("/api/test-suites")
    def list_suites():
        # Returning a list of dicts is enough: FastAPI turns it into JSON.
        return [suite_json(suite) for suite in deps().suites.list()]

    @app.post("/api/test-suites", status_code=201)  # 201 Created
    def create_suite(data: TestSuiteInput):
        suite = TestSuite(data.name, data.description or "")
        deps().suites.save(suite)
        return suite_json(suite)

    @app.put("/api/test-suites/{suite_id}")
    def update_suite(suite_id: UUID, data: TestSuiteInput):
        suite = find_suite(deps().suites, suite_id)  # 404 if it does not exist
        suite.name, suite.description = data.name, data.description or ""
        deps().suites.save(suite)
        return suite_json(suite)

    @app.delete("/api/test-suites/{suite_id}", status_code=204)
    def delete_suite(suite_id: UUID):
        if not deps().suites.delete(suite_id):
            raise HTTPException(status_code=404, detail="Suite not found")
        # 204 No Content: success, with an empty response body.
        return Response(status_code=204)

    # Test cases
    # Test cases are stored inside their suite, so every change saves the whole suite.

    @app.get("/api/test-suites/{suite_id}/test-cases")
    def list_cases(suite_id: UUID):
        return [case_json(case) for case in find_suite(deps().suites, suite_id).tests]

    @app.post("/api/test-cases", status_code=201)
    def create_case(data: CreateTestCaseInput):
        suite = find_suite(deps().suites, data.suite_id)
        case = build_case(data, [new_expectation(e) for e in data.expectations])
        suite.add_test(case)
        deps().suites.save(suite)
        return case_json(case)

    @app.get("/api/test-cases/{case_id}")
    def get_case(case_id: UUID):
        # find_case returns (suite, index, case); [2] takes the case.
        return case_json(find_case(deps().suites, case_id)[2])

    @app.put("/api/test-cases/{case_id}")
    def update_case(case_id: UUID, data: TestCaseInput):
        suite, index, old_case = find_case(deps().suites, case_id)
        # The client may keep, change or remove existing expectations, but it may not
        # repeat an ID or use an ID that belongs to another test case.
        existing_ids = {item.id for item in old_case.expectations}
        input_ids = [item.id for item in data.expectations]
        if len(input_ids) != len(set(input_ids)) or not set(input_ids).issubset(existing_ids):
            raise HTTPException(status_code=422, detail="Expectation IDs must belong to this test case")
        # Build a new test case with the same ID and put it in place of the old one.
        case = build_case(data, [new_expectation(e, e.id) for e in data.expectations], id=case_id)
        suite.tests[index] = case
        deps().suites.save(suite)
        return case_json(case)

    @app.delete("/api/test-cases/{case_id}", status_code=204)
    def delete_case(case_id: UUID):
        suite, index, _ = find_case(deps().suites, case_id)
        suite.tests.pop(index)
        deps().suites.save(suite)
        return Response(status_code=204)

    # Expectations
    # Expectations live inside a test case, so a change rebuilds that test case.

    @app.get("/api/test-cases/{case_id}/expectations")
    def list_expectations(case_id: UUID):
        return [expectation_json(e) for e in find_case(deps().suites, case_id)[2].expectations]

    @app.post("/api/expectations", status_code=201)
    def create_expectation(data: CreateExpectationInput):
        suite, index, case = find_case(deps().suites, data.test_case_id)
        expectation = new_expectation(data)
        # Rebuild the test case with the old expectations plus the new one.
        suite.tests[index] = build_case(case, [*case.expectations, expectation], id=case.id)
        deps().suites.save(suite)
        return expectation_json(expectation)

    @app.put("/api/expectations/{expectation_id}")
    def update_expectation(expectation_id: UUID, data: ExpectationInput):
        suite, case, index = find_expectation(deps().suites, expectation_id)
        expectation = new_expectation(data, expectation_id)
        # Replace one expectation in a copy of the list, then rebuild the test case.
        expectations = case.expectations.copy()
        expectations[index] = expectation
        suite.tests[suite.tests.index(case)] = build_case(case, expectations, id=case.id)
        deps().suites.save(suite)
        return expectation_json(expectation)

    # Evaluation runs

    @app.get("/api/test-suites/{suite_id}/eval-runs")
    def list_runs(suite_id: UUID):
        find_suite(deps().suites, suite_id)  # only to answer 404 if the suite does not exist
        return [run_json(run) for run in deps().runs.list(suite_id)]

    # This route is `async` because running a suite calls the AI model over the network.
    # While it `await`s the answer, the server can handle other requests.
    # The other routes are plain functions: FastAPI runs them in a separate thread.
    @app.post("/api/test-suites/{suite_id}/eval-runs", status_code=201)
    async def create_run(suite_id: UUID, data: EvalRunInput):
        suite = find_suite(deps().suites, suite_id)
        provider = deps().provider  # None when no OpenAI key is configured
        if data.provider_name != "openai" or not data.model_name.strip() or provider is None:
            raise HTTPException(status_code=422, detail="Unknown provider or unavailable model configuration")
        try:
            run = await deps().runner.run(suite, provider.get_model(data.model_name))
        except ValueError as error:
            # Turn a domain error into an HTTP error the client can understand.
            raise HTTPException(status_code=422, detail=str(error)) from error
        deps().runs.save(run)
        return run_json(run)

    @app.get("/api/eval-runs/{run_id}")
    def get_run(run_id: UUID):
        run = deps().runs.get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Evaluation run not found")
        return run_json(run)

    return app


# The application object used by the server (see __main__.py, which starts it with uvicorn).
app = create_app()
