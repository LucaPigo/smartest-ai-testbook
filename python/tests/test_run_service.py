import asyncio
from uuid import uuid4

import pytest

from smartest_ai_testbook.execution.eval_runner import EvalRunner
from smartest_ai_testbook.execution.exact_match_evaluator import ExactMatchEvaluator
from smartest_ai_testbook.execution.mock_ai import MockProvider
from smartest_ai_testbook.execution.run_service import RunService
from smartest_ai_testbook.persistence.sqlite import SQLAlchemyRunRepository, SQLAlchemySuiteRepository, create_database
from smartest_ai_testbook.test_creation.expectation import Expectation
from smartest_ai_testbook.test_creation.test_catalog import TestCatalog


@pytest.fixture
def setup(tmp_path):
    engine = create_database(f"sqlite:///{(tmp_path / 'runs.db').as_posix()}")
    suites, runs = SQLAlchemySuiteRepository(engine), SQLAlchemyRunRepository(engine)
    service = RunService(suites, runs, EvalRunner({"exactMatch": ExactMatchEvaluator()}), MockProvider())
    return TestCatalog(suites), service, runs


def test_a_completed_run_is_saved_and_can_be_listed_and_read(setup):
    catalog, service, runs = setup
    suite = catalog.create_suite("Suite")
    catalog.add_test_case(suite.id, "Capital", "Capital of {{country}}?", {"country": "France"},
                          [Expectation("Exact", "exactMatch", 1, {"expected": "Paris"})])

    run = asyncio.run(service.run_suite(suite.id, "mock", "demo"))

    assert (run.provider_name, run.model_name, run.results[0].output) == ("mock", "demo", "[mock] Capital of France?")
    assert [item.id for item in service.list_runs(suite.id)] == [run.id]
    assert service.get_run(run.id).results[0].output == "[mock] Capital of France?"
    assert runs.get(run.id) is not None


def test_missing_suite_or_run_returns_nothing(setup):
    _, service, _ = setup
    assert asyncio.run(service.run_suite(uuid4(), "mock", "demo")) is None
    assert service.list_runs(uuid4()) is None
    assert service.get_run(uuid4()) is None


@pytest.mark.parametrize("provider_name, model_name, message", [
    ("openai", "demo", "Unknown provider"),
    ("mock", "   ", "Unknown provider"),
])
def test_invalid_run_requests_raise_and_save_nothing(setup, provider_name, model_name, message):
    catalog, service, _ = setup
    suite = catalog.create_suite("Suite")
    catalog.add_test_case(suite.id, "Capital", "Question", {},
                          [Expectation("Exact", "exactMatch", 1, {"expected": "Paris"})])
    with pytest.raises(ValueError, match=message):
        asyncio.run(service.run_suite(suite.id, provider_name, model_name))
    assert service.list_runs(suite.id) == []


def test_runs_require_a_configured_provider_and_a_nonempty_suite(setup, tmp_path):
    catalog, service, runs = setup
    empty = catalog.create_suite("Empty")
    with pytest.raises(ValueError, match="empty suite"):
        asyncio.run(service.run_suite(empty.id, "mock", "demo"))
    assert service.list_runs(empty.id) == []

    unconfigured = RunService(service.suites, runs, service.runner, None)
    with pytest.raises(ValueError, match="Unknown provider"):
        asyncio.run(unconfigured.run_suite(empty.id, "openai", "gpt"))
