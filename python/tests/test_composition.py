import asyncio
import subprocess
import sys

import pytest

from smartest_ai_testbook.composition import create_dependencies
from smartest_ai_testbook.execution.exact_match_evaluator import ExactMatchEvaluator
from smartest_ai_testbook.execution.mock_ai import MockEvaluator, MockProvider
from smartest_ai_testbook.execution.openai_model import OpenAIProvider
from smartest_ai_testbook.test_creation.expectation import Expectation


class FakeModel:
    provider_name = "fake"
    model_name = "fake-model"

    async def generate_response(self, prompt, variables):
        return "Paris"


class FakeProvider:
    provider_name = "fake"

    def get_model(self, model_name):
        return FakeModel()


def test_compose_run_and_read_without_the_web_server(tmp_path):
    url = f"sqlite:///{(tmp_path / 'composition.db').as_posix()}"
    dependencies = create_dependencies(url, provider=FakeProvider())
    suite = dependencies.catalog.create_suite("Suite", "Description")
    dependencies.catalog.add_test_case(suite.id, "Test", "Question", {},
                                       [Expectation("Exact", "exactMatch", 1, {"expected": "Paris"})])
    run = asyncio.run(dependencies.runs.run_suite(suite.id, "fake", "fake-model"))
    assert create_dependencies(url).runs.get_run(run.id).results[0].passed
    subprocess.run([sys.executable, "-c", "import sys; import smartest_ai_testbook.composition; "
                    "assert not any(m == 'fastapi' or m.startswith('fastapi.') for m in sys.modules); "
                    "assert 'smartest_ai_testbook.web_server.app' not in sys.modules"], check=True)


def test_same_rules_apply_without_the_web_server(tmp_path):
    dependencies = create_dependencies(f"sqlite:///{(tmp_path / 'rules.db').as_posix()}", provider=FakeProvider())
    catalog = dependencies.catalog
    suite = catalog.create_suite("Suite")
    case = catalog.add_test_case(suite.id, "Test", "Question", {},
                                 [Expectation("Exact", "exactMatch", 1, {"expected": "Paris"})])
    other = catalog.add_test_case(suite.id, "Other", "Question", {},
                                  [Expectation("Exact", "exactMatch", 1, {"expected": "Paris"})])
    foreign = other.expectations[0]
    with pytest.raises(ValueError, match="Expectation IDs must belong to this test case"):
        catalog.update_test_case(case.id, "Test", "Question", {}, [foreign])
    with pytest.raises(ValueError, match="Unknown provider"):
        asyncio.run(dependencies.runs.run_suite(suite.id, "openai", "gpt"))
    assert dependencies.runs.list_runs(suite.id) == []
    assert catalog.get_test_case(case.id).expectations[0].id == case.expectations[0].id


def test_mock_mode_replaces_both_ai_services_and_ignores_openai(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-used")
    monkeypatch.setenv("AI_MODE", "mock")
    dependencies = create_dependencies(f"sqlite:///{(tmp_path / 'mock.db').as_posix()}")
    assert isinstance(dependencies.runs.provider, MockProvider)
    assert {name: type(evaluator) for name, evaluator in dependencies.runs.runner.evaluators.items()} == {
        "exactMatch": ExactMatchEvaluator, "semanticSimilarity": MockEvaluator, "llmJudge": MockEvaluator}

    suite = dependencies.catalog.create_suite("Suite")
    dependencies.catalog.add_test_case(suite.id, "Test", "Capital of {{country}}?", {"country": "France"}, [
        Expectation("Exact", "exactMatch", 1, {"expected": "Paris"}),
        Expectation("Similar", "semanticSimilarity", 0.8, {"expected": "Paris"}),
        Expectation("Judge", "llmJudge", 0.8, {"rubric": "Names the capital."}),
    ])
    run = asyncio.run(dependencies.runs.run_suite(suite.id, "mock", "demo"))
    result = run.results[0]
    assert (run.provider_name, result.output) == ("mock", "[mock] Capital of France?")
    assert [score.passed for score in result.scores] == [False, True, True]


def test_default_mode_is_unchanged(tmp_path, monkeypatch):
    monkeypatch.delenv("AI_MODE", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    url = f"sqlite:///{(tmp_path / 'default.db').as_posix()}"
    without_key = create_dependencies(url)
    assert without_key.runs.provider is None
    assert list(without_key.runs.runner.evaluators) == ["exactMatch"]
    with_client = create_dependencies(url, client=object(), ai_mode="openai")
    assert isinstance(with_client.runs.provider, OpenAIProvider)
    assert list(with_client.runs.runner.evaluators) == ["exactMatch", "semanticSimilarity", "llmJudge"]
