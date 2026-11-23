"""HTTP helpers used by the routes in app.py.

They only translate between HTTP and the domain; they hold no business rules:
- turning domain outcomes into HTTP errors (422 for invalid input, 404 for missing items);
- converting domain objects to JSON-ready dicts;
- converting request data to domain objects.
Finding, validating and saving data is done by the application services.
"""

import math
from dataclasses import asdict

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from smartest_ai_testbook.test_creation.expectation import Expectation


# --- Domain outcomes -> HTTP errors ---------------------------------------------

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


async def domain_error(_request, error):
    """Answer 422 when a service rejects input that breaks a domain rule.

    The domain does not know HTTP: it raises ValueError with a readable message.
    Registered in app.py, this handler turns it into `{"detail": "<message>"}`.
    """
    return JSONResponse(status_code=422, content={"detail": str(error)})


def or_404(result, detail):
    """Return the result of a service, or answer 404 when the service found nothing (None).

    Raising HTTPException inside a helper works like raising it in the route:
    FastAPI stops the request and sends the error status to the client.
    """
    if result is None:
        raise HTTPException(status_code=404, detail=detail)
    return result


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

def new_expectation(data, id=None):
    """Create an expectation from request data. Pass `id` to keep an existing ID."""
    return Expectation(data.name, data.evaluator_type, data.threshold, data.options, id=id)
