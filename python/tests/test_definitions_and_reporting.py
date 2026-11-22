import asyncio
from uuid import uuid4

import pytest

from smartest_ai_testbook.execution.eval_runner import EvalRunner
from smartest_ai_testbook.execution.exact_match_evaluator import ExactMatchEvaluator
from smartest_ai_testbook.reporting import ReportGenerator
from smartest_ai_testbook.test_creation.expectation import Expectation
from smartest_ai_testbook.test_creation.test_case import TestCaseBuilder
from smartest_ai_testbook.test_creation.test_suite import TestSuite


class Model:
    provider_name = "Fake"
    model_name = "Fake model"

    async def generate_response(self, prompt, variables):
        if prompt == "Failure":
            raise ValueError("Unavailable")
        return "Paris"


def test_builder_validates_criteria_before_creating_a_test():
    exact = Expectation("Exact", "exactMatch", 1, {"expected": "Paris"})
    semantic = Expectation("Semantic", "semanticSimilarity", 0.7, {"expected": "Paris"})
    judge = Expectation("Judge", "llmJudge", 0.8, {"rubric": "Correctness"})
    with pytest.raises(ValueError, match="Prompt"):
        TestCaseBuilder().set_title("Test").add_expectation(exact).build()
    with pytest.raises(ValueError, match="expectation"):
        TestCaseBuilder().set_title("Test").set_prompt("Question").build()
    for evaluator_type in ("exactMatch", "semanticSimilarity"):
        with pytest.raises(ValueError, match="expected"):
            expectation = Expectation("Missing reference", evaluator_type, 1, {})
            TestCaseBuilder().set_title("Test").set_prompt("Question").add_expectation(expectation).build()
    with pytest.raises(ValueError, match="rubric"):
        TestCaseBuilder().set_title("Test").set_prompt("Question").add_expectation(Expectation("Missing rubric", "llmJudge", 0.8, {})).build()

    variables = {"city": "Paris"}
    builder = (TestCaseBuilder().set_title("Test").set_prompt("Question").set_variables(variables)
               .add_expectation(exact).add_expectation(judge))
    case = builder.build()
    variables["other"] = "value"
    exact.name, exact.options["expected"] = "Changed", "London"
    judge.options["rubric"] = "Changed criterion"
    builder.add_expectation(semantic)
    assert case.variables == {"city": "Paris"}
    assert [(check.id, check.name, check.options) for check in case.expectations] == [
        (exact.id, "Exact", {"expected": "Paris"}), (judge.id, "Judge", {"rubric": "Correctness"})]


def test_suite_and_expectations_keep_their_identity_when_edited():
    suite_id, expectation_id = uuid4(), uuid4()
    suite = TestSuite("Initial", "Description", id=suite_id)
    expectation = Expectation("Exact", "exactMatch", 1, {"expected": "Paris"}, id=expectation_id)
    case = TestCaseBuilder().set_title("Test").set_prompt("Original").add_expectation(expectation).build()
    suite.add_test(case)
    case_id = case.id
    edited = TestCaseBuilder().set_title("Test").set_prompt("Edited").add_expectation(expectation).build(id=case_id)
    assert edited.id == case.id
    suite.name, suite.description, case.prompt, case.expectations[0].name = "New", "Updated", "Edited", "Changed"
    assert (suite.id, case.id, case.expectations[0].id, edited.expectations[0].id) == (suite_id, case_id, expectation_id, expectation_id)
    suite.tests.remove(case)
    assert suite.tests == []


def test_report_is_an_independent_snapshot_of_results_scores_and_errors():
    expectation = Expectation("Exact", "exactMatch", 1, {"expected": "Paris"})
    suite = TestSuite("Suite")
    case = TestCaseBuilder().set_title("Test").set_prompt("Original").add_expectation(expectation).build()
    failure = TestCaseBuilder().set_title("Test").set_prompt("Failure").add_expectation(expectation).build()
    suite.add_test(case).add_test(failure)
    run = asyncio.run(EvalRunner({"exactMatch": ExactMatchEvaluator()}).run(suite, Model()))
    case.prompt = "Edited before report"
    case.expectations[0].name = "Edited expectation"
    case.expectations[0].threshold = 0.2
    case.expectations[0].options["expected"] = "London"
    report = ReportGenerator().generate(run)
    run.provider_name = "Changed"
    run.results[0].prompt = "Changed"
    run.results[0].scores[0].value = 0
    run.results[0].scores.append(run.results[0].scores[0])
    run.results[1].error = "Changed"
    run.results.clear()

    assert report.provider_name == "Fake"
    assert report.results[0].prompt == "Original"
    assert report.results[0].passed
    assert len(report.results[0].scores) == 1
    assert report.results[0].scores[0].value == 1
    assert report.results[0].scores[0].expectation_id == expectation.id
    assert report.results[0].scores[0].expectation_name == "Exact"
    assert report.results[0].scores[0].threshold == 1
    assert report.results[1].error == "Unavailable"
    assert not report.results[1].passed
