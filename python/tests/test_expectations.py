import asyncio

import pytest

from smartest_ai_testbook.execution.eval_runner import EvalRunner
from smartest_ai_testbook.execution.exact_match_evaluator import ExactMatchEvaluator
from smartest_ai_testbook.test_creation.expectation import Expectation
from smartest_ai_testbook.test_creation.test_case import TestCaseBuilder as Builder
from smartest_ai_testbook.test_creation.test_suite import TestSuite as Suite


def definition(expectations):
    builder = Builder().set_title("Capital").set_prompt("Capital of France?")
    for expectation in expectations:
        builder.add_expectation(expectation)
    return builder.build()


def test_local_references_are_independent_and_input_contains_no_criteria():
    first = Expectation("Exact city", "exactMatch", 1, {"expected": "Paris"})
    second = Expectation("Different reference", "exactMatch", 1, {"expected": "Lyon"})
    case = definition([first, second])
    assert case.variables == {}
    assert not hasattr(case, "goldenReference") and not hasattr(case, "rubric")

    class Model:
        provider_name = "fake"
        model_name = "fake-model"

        def __init__(self):
            self.calls = []

        async def generate_response(self, prompt, variables):
            self.calls.append((prompt, variables))
            return "Paris"

    suite, model = Suite("Local criteria"), Model()
    suite.add_test(case)
    run = asyncio.run(EvalRunner({"exactMatch": ExactMatchEvaluator()}).run(suite, model))
    assert model.calls == [("Capital of France?", {})]
    assert [score.passed for score in run.results[0].scores] == [True, False]
    assert not run.results[0].passed


@pytest.mark.parametrize("changes", [
    {"name": " "}, {"evaluator_type": "unknown"}, {"threshold": 0},
    {"threshold": float("nan")}, {"threshold": float("inf")}, {"threshold": True},
    {"threshold": -0.1}, {"threshold": 1.1}, {"options": {}},
    {"options": {"expected": " "}}, {"options": {"expected": 1}},
    {"options": {"expected": "Paris", "rubric": "Correct"}},
])
def test_invalid_check_is_rejected_before_build(changes):
    values = {"name": "Exact", "evaluator_type": "exactMatch", "threshold": 1,
              "options": {"expected": "Paris"}, **changes}
    with pytest.raises(ValueError):
        definition([Expectation(**values)])
