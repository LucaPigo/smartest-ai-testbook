import math
import os
from dataclasses import asdict
from uuid import UUID

from fastapi import FastAPI, HTTPException, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from smartest_ai_testbook.composition import Dependencies, create_dependencies
from smartest_ai_testbook.test_creation.expectation import Expectation
from smartest_ai_testbook.test_creation.test_case import TestCaseBuilder
from smartest_ai_testbook.test_creation.test_suite import TestSuite
from smartest_ai_testbook.web_server.generated.models.create_expectation_input import CreateExpectationInput
from smartest_ai_testbook.web_server.generated.models.create_test_case_input import CreateTestCaseInput
from smartest_ai_testbook.web_server.generated.models.eval_run_input import EvalRunInput
from smartest_ai_testbook.web_server.generated.models.expectation_input import ExpectationInput
from smartest_ai_testbook.web_server.generated.models.health_response import HealthResponse
from smartest_ai_testbook.web_server.generated.models.test_case_input import TestCaseInput
from smartest_ai_testbook.web_server.generated.models.test_suite_input import TestSuiteInput


def _expectation(item):
    return {"id": item.id, "name": item.name, "evaluator_type": item.evaluator_type,
            "threshold": item.threshold, "options": item.options}


def _case(item):
    return {"id": item.id, "title": item.title, "prompt": item.prompt, "variables": item.variables,
            "expectations": [_expectation(e) for e in item.expectations]}


def _suite(item):
    return {"id": item.id, "name": item.name, "description": item.description,
            "tests": [_case(test) for test in item.tests]}


def _run(item):
    return {"id": item.id, "suite_id": item.suite_id, "started_at": item.started_at,
            "provider_name": item.provider_name, "model_name": item.model_name,
            "results": [{"test_id": result.test_id, "prompt": result.prompt, "output": result.output,
                         "error": result.error, "passed": result.passed,
                         "scores": [asdict(score) for score in result.scores]} for result in item.results]}


def _build_case(data, expectations, id=None):
    builder = TestCaseBuilder().set_title(data.title).set_prompt(data.prompt).set_variables(data.variables or {})
    for expectation in expectations:
        builder.add_expectation(expectation)
    try:
        return builder.build(id=id)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


def _new_expectation(data, id=None):
    return Expectation(data.name, data.evaluator_type, data.threshold, data.options, id=id)


def create_app(dependencies: Dependencies | None = None) -> FastAPI:
    app = FastAPI()

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_request, error):
        # Invalid numeric input must not make the validation response invalid JSON.
        content = jsonable_encoder({"detail": error.errors()}, custom_encoder={
            float: lambda value: value if math.isfinite(value) else str(value),
        })
        return JSONResponse(status_code=422, content=content)

    app.add_middleware(CORSMiddleware, allow_origins=[os.getenv("WEB_ORIGIN", "http://localhost:3000")],
                       allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Content-Type"])
    app.state.dependencies = dependencies

    def deps():
        if app.state.dependencies is None:
            app.state.dependencies = create_dependencies()
        return app.state.dependencies

    def find_suite(suite_id):
        suite = deps().suites.get(suite_id)
        if suite is None:
            raise HTTPException(status_code=404, detail="Suite not found")
        return suite

    def find_case(case_id):
        for suite in deps().suites.list():
            for index, case in enumerate(suite.tests):
                if case.id == case_id:
                    return suite, index, case
        raise HTTPException(status_code=404, detail="Test case not found")

    def find_expectation(expectation_id):
        for suite in deps().suites.list():
            for case in suite.tests:
                for index, expectation in enumerate(case.expectations):
                    if expectation.id == expectation_id:
                        return suite, case, index
        raise HTTPException(status_code=404, detail="Expectation not found")

    @app.get("/health")
    def get_health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.get("/api/test-suites")
    def list_suites():
        return [_suite(suite) for suite in deps().suites.list()]

    @app.post("/api/test-suites", status_code=201)
    def create_suite(data: TestSuiteInput):
        suite = TestSuite(data.name, data.description or "")
        deps().suites.save(suite)
        return _suite(suite)

    @app.put("/api/test-suites/{suite_id}")
    def update_suite(suite_id: UUID, data: TestSuiteInput):
        suite = find_suite(suite_id)
        suite.name, suite.description = data.name, data.description or ""
        deps().suites.save(suite)
        return _suite(suite)

    @app.delete("/api/test-suites/{suite_id}", status_code=204)
    def delete_suite(suite_id: UUID):
        if not deps().suites.delete(suite_id):
            raise HTTPException(status_code=404, detail="Suite not found")
        return Response(status_code=204)

    @app.get("/api/test-suites/{suite_id}/test-cases")
    def list_cases(suite_id: UUID):
        return [_case(case) for case in find_suite(suite_id).tests]

    @app.post("/api/test-cases", status_code=201)
    def create_case(data: CreateTestCaseInput):
        suite = find_suite(data.suite_id)
        case = _build_case(data, [_new_expectation(e) for e in data.expectations])
        suite.add_test(case)
        deps().suites.save(suite)
        return _case(case)

    @app.get("/api/test-cases/{case_id}")
    def get_case(case_id: UUID):
        return _case(find_case(case_id)[2])

    @app.put("/api/test-cases/{case_id}")
    def update_case(case_id: UUID, data: TestCaseInput):
        suite, index, old_case = find_case(case_id)
        existing_ids = {item.id for item in old_case.expectations}
        input_ids = [item.id for item in data.expectations]
        if len(input_ids) != len(set(input_ids)) or not set(input_ids).issubset(existing_ids):
            raise HTTPException(status_code=422, detail="Expectation IDs must belong to this test case")
        case = _build_case(data, [_new_expectation(e, e.id) for e in data.expectations], id=case_id)
        suite.tests[index] = case
        deps().suites.save(suite)
        return _case(case)

    @app.delete("/api/test-cases/{case_id}", status_code=204)
    def delete_case(case_id: UUID):
        suite, index, _ = find_case(case_id)
        suite.tests.pop(index)
        deps().suites.save(suite)
        return Response(status_code=204)

    @app.get("/api/test-cases/{case_id}/expectations")
    def list_expectations(case_id: UUID):
        return [_expectation(e) for e in find_case(case_id)[2].expectations]

    @app.post("/api/expectations", status_code=201)
    def create_expectation(data: CreateExpectationInput):
        suite, index, case = find_case(data.test_case_id)
        expectation = _new_expectation(data)
        suite.tests[index] = _build_case(case, [*case.expectations, expectation], id=case.id)
        deps().suites.save(suite)
        return _expectation(expectation)

    @app.put("/api/expectations/{expectation_id}")
    def update_expectation(expectation_id: UUID, data: ExpectationInput):
        suite, case, index = find_expectation(expectation_id)
        expectation = _new_expectation(data, expectation_id)
        expectations = case.expectations.copy()
        expectations[index] = expectation
        suite.tests[suite.tests.index(case)] = _build_case(case, expectations, id=case.id)
        deps().suites.save(suite)
        return _expectation(expectation)

    @app.get("/api/test-suites/{suite_id}/eval-runs")
    def list_runs(suite_id: UUID):
        find_suite(suite_id)
        return [_run(run) for run in deps().runs.list(suite_id)]

    @app.post("/api/test-suites/{suite_id}/eval-runs", status_code=201)
    async def create_run(suite_id: UUID, data: EvalRunInput):
        suite = find_suite(suite_id)
        if data.provider_name != "openai" or not data.model_name.strip() or deps().provider is None:
            raise HTTPException(status_code=422, detail="Unknown provider or unavailable model configuration")
        try:
            run = await deps().runner.run(suite, deps().provider.get_model(data.model_name))
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        deps().runs.save(run)
        return _run(run)

    @app.get("/api/eval-runs/{run_id}")
    def get_run(run_id: UUID):
        run = deps().runs.get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Evaluation run not found")
        return _run(run)

    return app


app = create_app()
