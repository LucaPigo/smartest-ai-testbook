import asyncio
import subprocess
import sys

from smartest_ai_testbook.composition import create_dependencies
from smartest_ai_testbook.execution.exact_match_evaluator import ExactMatchEvaluator
from smartest_ai_testbook.execution.mock_ai import MockEvaluator, MockProvider
from smartest_ai_testbook.execution.openai_model import OpenAIProvider
from smartest_ai_testbook.test_creation.expectation import Expectation
from smartest_ai_testbook.test_creation.test_case import TestCaseBuilder
from smartest_ai_testbook.test_creation.test_suite import TestSuite


class FakeModel:
    provider_name = "fake"
    model_name = "fake-model"

    async def generate_response(self, prompt, variables):
        return "Paris"


def test_compose_run_and_read_without_the_web_server(tmp_path):
    url = f"sqlite:///{(tmp_path / 'composition.db').as_posix()}"
    dependencies = create_dependencies(url)
    suite = TestSuite("Suite", "Description")
    suite.add_test(TestCaseBuilder().set_title("Test").set_prompt("Question")
                   .add_expectation(Expectation("Exact", "exactMatch", 1, {"expected": "Paris"})).build())
    dependencies.suites.save(suite)
    run = asyncio.run(dependencies.runner.run(dependencies.suites.get(suite.id), FakeModel()))
    dependencies.runs.save(run)
    assert create_dependencies(url).runs.get(run.id).results[0].passed
    subprocess.run([sys.executable, "-c", "import sys; import smartest_ai_testbook.composition; "
                    "assert not any(m == 'fastapi' or m.startswith('fastapi.') for m in sys.modules); "
                    "assert 'smartest_ai_testbook.web_server.app' not in sys.modules"], check=True)


def test_mock_mode_replaces_both_ai_services_and_ignores_openai(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-used")
    monkeypatch.setenv("AI_MODE", "mock")
    dependencies = create_dependencies(f"sqlite:///{(tmp_path / 'mock.db').as_posix()}")
    assert isinstance(dependencies.provider, MockProvider)
    assert {name: type(evaluator) for name, evaluator in dependencies.runner.evaluators.items()} == {
        "exactMatch": ExactMatchEvaluator, "semanticSimilarity": MockEvaluator, "llmJudge": MockEvaluator}

    suite = TestSuite("Suite")
    suite.add_test(TestCaseBuilder().set_title("Test").set_prompt("Capital of {{country}}?")
                   .set_variables({"country": "France"})
                   .add_expectation(Expectation("Exact", "exactMatch", 1, {"expected": "Paris"}))
                   .add_expectation(Expectation("Similar", "semanticSimilarity", 0.8, {"expected": "Paris"}))
                   .add_expectation(Expectation("Judge", "llmJudge", 0.8, {"rubric": "Names the capital."})).build())
    run = asyncio.run(dependencies.runner.run(suite, dependencies.provider.get_model("demo")))
    result = run.results[0]
    assert (run.provider_name, result.output) == ("mock", "[mock] Capital of France?")
    assert [score.passed for score in result.scores] == [False, True, True]


def test_default_mode_is_unchanged(tmp_path, monkeypatch):
    monkeypatch.delenv("AI_MODE", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    url = f"sqlite:///{(tmp_path / 'default.db').as_posix()}"
    without_key = create_dependencies(url)
    assert without_key.provider is None
    assert list(without_key.runner.evaluators) == ["exactMatch"]
    with_client = create_dependencies(url, client=object(), ai_mode="openai")
    assert isinstance(with_client.provider, OpenAIProvider)
    assert list(with_client.runner.evaluators) == ["exactMatch", "semanticSimilarity", "llmJudge"]
