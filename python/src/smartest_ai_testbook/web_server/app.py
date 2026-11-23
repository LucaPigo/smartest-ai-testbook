"""HTTP API of the application, built with FastAPI.

How a request flows through this file:
1. The client sends an HTTP request, for example `GET /api/test-suites`.
2. FastAPI finds the function registered for that method and path (a "route").
3. FastAPI reads and validates the input (path parameters and JSON body) and
   passes it to the function as normal Python arguments.
4. The function calls one operation of a domain application service, which finds,
   changes and saves the data, and returns its result.
5. FastAPI converts the returned value to JSON and sends it back.

The routes contain only HTTP logic. The real work is done by the application services
(TestCatalog and RunService, created in composition.py), and small HTTP helpers live
in `helpers.py`.
"""

import os
from uuid import UUID

from fastapi import FastAPI, HTTPException, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from smartest_ai_testbook.composition import Dependencies, create_dependencies
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
    case_json, domain_error, expectation_json, invalid_request, new_expectation, or_404, run_json, suite_json,
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
    # When a service rejects input that breaks a domain rule, it raises ValueError.
    # This handler turns it into the same 422 response for every route (see helpers.py).
    app.add_exception_handler(ValueError, domain_error)

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
    # Every route does only three things: read the HTTP input, call ONE operation of an
    # application service (deps().catalog or deps().runs), and translate the outcome:
    # - a result → JSON (with `status_code=` for a success other than 200 OK);
    # - None / False (not found) → 404, through `or_404` or `HTTPException`;
    # - a ValueError raised by the domain → 422, through the `domain_error` handler.
    # Finding, validating and saving data is the job of the services, not of the routes.

    # Health

    @app.get("/health")
    def get_health() -> HealthResponse:
        # Lets clients check that the server is running.
        return HealthResponse(status="ok")

    # Test suites

    @app.get("/api/test-suites")
    def list_suites():
        # Returning a list of dicts is enough: FastAPI turns it into JSON.
        return [suite_json(suite) for suite in deps().catalog.list_suites()]

    @app.post("/api/test-suites", status_code=201)  # 201 Created
    def create_suite(data: TestSuiteInput):
        return suite_json(deps().catalog.create_suite(data.name, data.description or ""))

    @app.put("/api/test-suites/{suite_id}")
    def update_suite(suite_id: UUID, data: TestSuiteInput):
        suite = deps().catalog.update_suite(suite_id, data.name, data.description or "")
        return suite_json(or_404(suite, "Suite not found"))

    @app.delete("/api/test-suites/{suite_id}", status_code=204)
    def delete_suite(suite_id: UUID):
        if not deps().catalog.delete_suite(suite_id):
            raise HTTPException(status_code=404, detail="Suite not found")
        # 204 No Content: success, with an empty response body.
        return Response(status_code=204)

    # Test cases

    @app.get("/api/test-suites/{suite_id}/test-cases")
    def list_cases(suite_id: UUID):
        cases = or_404(deps().catalog.list_test_cases(suite_id), "Suite not found")
        return [case_json(case) for case in cases]

    @app.post("/api/test-cases", status_code=201)
    def create_case(data: CreateTestCaseInput):
        # Translate each input expectation into a domain Expectation (with a new ID).
        case = deps().catalog.add_test_case(data.suite_id, data.title, data.prompt, data.variables,
                                            [new_expectation(e) for e in data.expectations])
        return case_json(or_404(case, "Suite not found"))

    @app.get("/api/test-cases/{case_id}")
    def get_case(case_id: UUID):
        return case_json(or_404(deps().catalog.get_test_case(case_id), "Test case not found"))

    @app.put("/api/test-cases/{case_id}")
    def update_case(case_id: UUID, data: TestCaseInput):
        # Existing expectations keep their IDs; the catalog checks that they belong to this test case.
        case = deps().catalog.update_test_case(case_id, data.title, data.prompt, data.variables,
                                               [new_expectation(e, e.id) for e in data.expectations])
        return case_json(or_404(case, "Test case not found"))

    @app.delete("/api/test-cases/{case_id}", status_code=204)
    def delete_case(case_id: UUID):
        if not deps().catalog.delete_test_case(case_id):
            raise HTTPException(status_code=404, detail="Test case not found")
        return Response(status_code=204)

    # Expectations

    @app.get("/api/test-cases/{case_id}/expectations")
    def list_expectations(case_id: UUID):
        expectations = or_404(deps().catalog.list_expectations(case_id), "Test case not found")
        return [expectation_json(e) for e in expectations]

    @app.post("/api/expectations", status_code=201)
    def create_expectation(data: CreateExpectationInput):
        expectation = deps().catalog.add_expectation(data.test_case_id, new_expectation(data))
        return expectation_json(or_404(expectation, "Test case not found"))

    @app.put("/api/expectations/{expectation_id}")
    def update_expectation(expectation_id: UUID, data: ExpectationInput):
        expectation = deps().catalog.update_expectation(expectation_id, new_expectation(data))
        return expectation_json(or_404(expectation, "Expectation not found"))

    # Evaluation runs

    @app.get("/api/test-suites/{suite_id}/eval-runs")
    def list_runs(suite_id: UUID):
        runs = or_404(deps().runs.list_runs(suite_id), "Suite not found")
        return [run_json(run) for run in runs]

    # This route is `async` because running a suite calls the AI model over the network.
    # While it `await`s the answer, the server can handle other requests.
    # The other routes are plain functions: FastAPI runs them in a separate thread.
    @app.post("/api/test-suites/{suite_id}/eval-runs", status_code=201)
    async def create_run(suite_id: UUID, data: EvalRunInput):
        # The run service checks the provider, runs the suite and saves the completed run.
        run = await deps().runs.run_suite(suite_id, data.provider_name, data.model_name)
        return run_json(or_404(run, "Suite not found"))

    @app.get("/api/eval-runs/{run_id}")
    def get_run(run_id: UUID):
        return run_json(or_404(deps().runs.get_run(run_id), "Evaluation run not found"))

    return app


# The application object used by the server (see __main__.py, which starts it with uvicorn).
app = create_app()
