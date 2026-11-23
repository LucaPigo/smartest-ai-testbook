import asyncio

import pytest

from smartest_ai_testbook.execution.eval_runner import EvalRunner
from smartest_ai_testbook.execution.exact_match_evaluator import Evaluation, ExactMatchEvaluator
from smartest_ai_testbook.execution.mock_ai import MockEvaluator, MockProvider
from smartest_ai_testbook.test_creation.expectation import Expectation
from smartest_ai_testbook.test_creation.test_case import TestCaseBuilder
from smartest_ai_testbook.test_creation.test_suite import TestSuite


def exact():
    return Expectation("Exact answer", "exactMatch", 1, {"expected": "Paris"}, id="exact")


def semantic():
    return Expectation("Similar", "semanticSimilarity", 0.8, {"expected": "Paris"}, id="semantic")


def judge(options=None):
    return Expectation("Judge", "llmJudge", 0.9, options if options is not None else {"rubric": "Names the capital."},
                       id="judge")


def test_mock_model_answers_with_the_filled_prompt_and_reports_its_identity():
    provider = MockProvider()
    model = provider.get_model("demo")
    assert provider.provider_name == "mock"
    assert (model.provider_name, model.model_name) == ("mock", "demo")
    answer = asyncio.run(model.generate_response("Capital of {{country}}? {{unknown}}", {"country": "France"}))
    assert answer == "[mock] Capital of France? {{unknown}}"


def test_mock_evaluator_validates_the_expectation_and_always_scores_1():
    definition = TestCaseBuilder().set_title("Test").set_prompt("Prompt").add_expectation(semantic()).build()
    evaluator = MockEvaluator()
    assert asyncio.run(evaluator.evaluate(definition, "any output", judge())) == Evaluation(1, "Mock evaluation")
    with pytest.raises(ValueError, match="rubric"):
        asyncio.run(evaluator.evaluate(definition, "any output", judge({})))


def test_mock_run_evaluates_ai_expectations_with_the_mock_and_exact_match_for_real():
    suite = TestSuite("Mock suite")
    suite.add_test(TestCaseBuilder().set_title("Capital").set_prompt("Capital of {{country}}?")
                   .set_variables({"country": "France"})
                   .add_expectation(exact()).add_expectation(semantic()).add_expectation(judge()).build())
    mock = MockEvaluator()
    runner = EvalRunner({"exactMatch": ExactMatchEvaluator(), "semanticSimilarity": mock, "llmJudge": mock})

    run = asyncio.run(runner.run(suite, MockProvider().get_model("demo")))

    assert (run.provider_name, run.model_name) == ("mock", "demo")
    result = run.results[0]
    assert result.output == "[mock] Capital of France?"
    assert [(s.expectation_id, s.value, s.passed) for s in result.scores] == [
        ("exact", 0, False), ("semantic", 1, True), ("judge", 1, True)]
    assert result.scores[1].feedback == "Mock evaluation"
    assert (result.scores[1].scale_min, result.scores[1].scale_max) == (0, 1)
    assert result.passed is False
