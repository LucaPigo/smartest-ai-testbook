import asyncio
import unittest

from smartest_ai_testbook.execution.eval_run import EvalResult, EvalScore
from smartest_ai_testbook.execution.eval_runner import EvalRunner
from smartest_ai_testbook.execution.exact_match_evaluator import Evaluation, ExactMatchEvaluator
from smartest_ai_testbook.test_creation.expectation import Expectation
from smartest_ai_testbook.test_creation.test_case import TestCaseBuilder as CaseBuilder
from smartest_ai_testbook.test_creation.test_suite import TestSuite as Suite


class Model:
    provider_name = "Test provider"
    model_name = "Test model"

    def __init__(self):
        self.calls = []

    async def generate_response(self, prompt, variables):
        self.calls.append((prompt, variables.copy()))
        if prompt == "Fail":
            raise ValueError("Model unavailable")
        return "Paris"


class FailingEvaluator:
    async def evaluate(self, test, output, expectation):
        raise ValueError("Judge unavailable")


class PartialEvaluator:
    async def evaluate(self, test, output, expectation):
        await asyncio.sleep(0)
        return Evaluation(value=0.5, feedback="Partial")


def make_test(prompt, expectations):
    builder = CaseBuilder().set_title("Test").set_prompt(prompt)
    for expectation in expectations:
        builder.add_expectation(expectation)
    return builder.build()


class ExecutionTests(unittest.TestCase):
    def test_execution_and_error_isolation(self):
        exact = Expectation("Exact", "exactMatch", 1, {"expected": "Paris"})
        unregistered = Expectation("Unregistered similarity", "semanticSimilarity", 1, {"expected": "Paris"})
        failing = Expectation("Judge", "llmJudge", 1, {"rubric": "Be correct"})
        suite = Suite("Answers")
        suite.add_test(make_test("Fail", [exact]))
        test = make_test("Return {{city}}", [unregistered, failing, exact])
        test.variables["city"] = "Paris"
        suite.add_test(test)
        model = Model()
        run = asyncio.run(EvalRunner({"exactMatch": ExactMatchEvaluator(), "llmJudge": FailingEvaluator()}).run(suite, model))
        self.assertEqual(model.calls, [("Fail", {}), ("Return {{city}}", {"city": "Paris"})])
        self.assertEqual((run.suite_id, run.provider_name, run.model_name), (suite.id, "Test provider", "Test model"))
        failed, result = run.results
        self.assertEqual((failed.prompt, failed.error, failed.scores, failed.passed), ("Fail", "Model unavailable", [], False))
        self.assertEqual(result.output, "Paris")
        self.assertEqual([score.error for score in result.scores], ["Unknown evaluator type: semanticSimilarity", "Judge unavailable", None])
        self.assertEqual([score.passed for score in result.scores], [False, False, True])
        self.assertEqual(result.scores[2].expectation_id, exact.id)
        test.expectations[2].name = "Edited"
        self.assertEqual(result.scores[2].expectation_name, "Exact")
        self.assertFalse(result.passed)

    def test_result_and_threshold_rules(self):
        result = EvalResult("id", "prompt", "Paris")
        self.assertFalse(result.passed)
        result.add_score(EvalScore(feedback="Match", passed=True, value=1))
        self.assertTrue(result.passed)
        self.assertFalse(EvalResult("id", "prompt", "Paris", "").passed)
        expectation = Expectation("Exact", "exactMatch", 1, {"expected": "Paris"})
        matching = Expectation("Other reference", "exactMatch", 1, {"expected": "paris "})
        suite = Suite("Mismatch")
        suite.add_test(make_test("Mismatch", [expectation, matching]))
        class Mismatch(Model):
            async def generate_response(self, prompt, variables):
                return "paris "
        run = asyncio.run(EvalRunner({"exactMatch": ExactMatchEvaluator()}).run(suite, Mismatch()))
        self.assertEqual((run.results[0].scores[0].value, run.results[0].passed), (0, False))
        self.assertEqual((run.results[0].scores[1].value, run.results[0].scores[1].passed), (1, True))
        with self.assertRaisesRegex(ValueError, "empty suite"):
            asyncio.run(EvalRunner({}).run(Suite("Empty"), Model()))

    def test_runner_applies_threshold_to_async_evaluator(self):
        expectation = Expectation("Partial", "semanticSimilarity", 0.75, {"expected": "Paris"})
        suite = Suite("Threshold")
        suite.add_test(make_test("Paris", [expectation]))
        run = asyncio.run(EvalRunner({"semanticSimilarity": PartialEvaluator()}).run(suite, Model()))
        score = run.results[0].scores[0]
        self.assertEqual((score.value, score.threshold, score.passed), (0.5, 0.75, False))

    def test_tests_and_expectations_await_in_order_and_generate_once_each(self):
        events = []

        class OrderedModel(Model):
            async def generate_response(self, prompt, variables):
                events.append(f"generate start: {prompt}")
                await asyncio.sleep(0)
                events.append(f"generate end: {prompt}")
                return await super().generate_response(prompt, variables)

        class OrderedEvaluator:
            async def evaluate(self, test, output, expectation):
                assert output == "Paris"
                events.append(f"evaluate start: {test.prompt}/{expectation.name}")
                await asyncio.sleep(0)
                events.append(f"evaluate end: {test.prompt}/{expectation.name}")
                return Evaluation(0.8, "Reviewed")

        expectations = [Expectation(name, "semanticSimilarity", 0.8, {"expected": "Paris"}) for name in ("First", "Second")]
        suite = Suite("Ordered")
        first = make_test("Return {{city}}", expectations)
        first.variables["city"] = "Paris"
        suite.add_test(first).add_test(make_test("Then return Paris", expectations))
        model = OrderedModel()
        run = asyncio.run(EvalRunner({"semanticSimilarity": OrderedEvaluator()}).run(suite, model))
        self.assertEqual(model.calls, [("Return {{city}}", {"city": "Paris"}), ("Then return Paris", {})])
        self.assertEqual(events, [
            "generate start: Return {{city}}", "generate end: Return {{city}}",
            "evaluate start: Return {{city}}/First", "evaluate end: Return {{city}}/First",
            "evaluate start: Return {{city}}/Second", "evaluate end: Return {{city}}/Second",
            "generate start: Then return Paris", "generate end: Then return Paris",
            "evaluate start: Then return Paris/First", "evaluate end: Then return Paris/First",
            "evaluate start: Then return Paris/Second", "evaluate end: Then return Paris/Second",
        ])
        self.assertTrue(all(result.passed for result in run.results))

    def test_invalid_scores_fail_without_stopping_later_expectations(self):
        for invalid in (float("nan"), float("inf"), -float("inf"), -0.1, 1.1, True, "0.8", None):
            with self.subTest(value=invalid):
                class InvalidEvaluator:
                    async def evaluate(self, test, output, expectation):
                        return Evaluation(invalid if expectation.name == "Invalid" else 0.8, "Reviewed")

                checks = [Expectation(name, "semanticSimilarity", 0.8, {"expected": "Paris"}) for name in ("Invalid", "Valid")]
                suite = Suite("Invalid score")
                suite.add_test(make_test("Question", checks))
                run = asyncio.run(EvalRunner({"semanticSimilarity": InvalidEvaluator()}).run(suite, Model()))
                failed, passed = run.results[0].scores
                self.assertEqual((failed.value, failed.scale_min, failed.scale_max, failed.passed), (None, None, None, False))
                self.assertIn("finite number from 0 to 1", failed.error)
                self.assertEqual((passed.value, passed.scale_min, passed.scale_max, passed.threshold, passed.passed), (0.8, 0, 1, 0.8, True))
                self.assertFalse(run.results[0].passed)
