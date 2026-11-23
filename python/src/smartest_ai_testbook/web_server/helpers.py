"""Helper functions used by the routes in app.py.

They fall into three groups:
- converting domain objects to JSON-ready dicts;
- building domain objects from the request data;
- finding stored objects, answering 404 when they do not exist.
"""

import math
from dataclasses import asdict

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from smartest_ai_testbook.test_creation.expectation import Expectation
from smartest_ai_testbook.test_creation.test_case import TestCaseBuilder


# --- Error handling -----------------------------------------------------------

async def invalid_request(_request, error):
    """Answer 422 when the request body does not match the expected model.

    It is registered in app.py with `add_exception_handler`, so FastAPI calls it
    instead of its default handler.
    """
    # The error details may contain the invalid input. Values such as NaN or Infinity
    # are not valid JSON, so they are sent as strings.
    content = jsonable_encoder({"detail": error.errors()}, custom_encoder={
        float: lambda value: value if math.isfinite(value) else str(value),
    })
    return JSONResponse(status_code=422, content=content)


# --- Domain objects -> JSON -----------------------------------------------------
# Each function copies the fields of a domain object into a dict with the names
# defined by the API contract. FastAPI then turns the dict into JSON.

def expectation_json(item):
    return {"id": item.id, "name": item.name, "evaluator_type": item.evaluator_type,
            "threshold": item.threshold, "options": item.options}


def case_json(item):
    return {"id": item.id, "title": item.title, "prompt": item.prompt, "variables": item.variables,
            "expectations": [expectation_json(e) for e in item.expectations]}


def suite_json(item):
    return {"id": item.id, "name": item.name, "description": item.description,
            "tests": [case_json(test) for test in item.tests]}


def run_json(item):
    return {"id": item.id, "suite_id": item.suite_id, "started_at": item.started_at,
            "provider_name": item.provider_name, "model_name": item.model_name,
            "results": [{"test_id": result.test_id, "prompt": result.prompt, "output": result.output,
                         "error": result.error, "passed": result.passed,
                         # asdict turns a dataclass into a dict
                         "scores": [asdict(score) for score in result.scores]} for result in item.results]}


# --- Request data -> domain objects ---------------------------------------------

def build_case(data, expectations, id=None):
    """Build a test case with the domain builder.

    `data` can be a request body or an existing test case: both have title,
    prompt and variables. Pass `id` to keep the ID of an existing test case.
    """
    builder = TestCaseBuilder().set_title(data.title).set_prompt(data.prompt).set_variables(data.variables or {})
    for expectation in expectations:
        builder.add_expectation(expectation)
    try:
        return builder.build(id=id)
    except ValueError as error:
        # The domain rejects invalid data with ValueError: report it as 422.
        raise HTTPException(status_code=422, detail=str(error)) from error


def new_expectation(data, id=None):
    """Create an expectation from request data. Pass `id` to keep an existing ID."""
    return Expectation(data.name, data.evaluator_type, data.threshold, data.options, id=id)


# --- Lookups ------------------------------------------------------------------
# Raising HTTPException inside a helper works like raising it in the route:
# FastAPI stops the request and sends the error status to the client.

def find_suite(suites, suite_id):
    suite = suites.get(suite_id)
    if suite is None:
        raise HTTPException(status_code=404, detail="Suite not found")
    return suite


def find_case(suites, case_id):
    """Return (suite, index of the case in the suite, case)."""
    for suite in suites.list():
        for index, case in enumerate(suite.tests):
            if case.id == case_id:
                return suite, index, case
    raise HTTPException(status_code=404, detail="Test case not found")


def find_expectation(suites, expectation_id):
    """Return (suite, case, index of the expectation in the case)."""
    for suite in suites.list():
        for case in suite.tests:
            for index, expectation in enumerate(case.expectations):
                if expectation.id == expectation_id:
                    return suite, case, index
    raise HTTPException(status_code=404, detail="Expectation not found")
