from dataclasses import dataclass
from typing import Protocol

from smartest_ai_testbook.test_creation.expectation import IExpectation, validate_expectation
from smartest_ai_testbook.test_creation.test_case import ITestCase


@dataclass
class Evaluation:
    value: float
    feedback: str


class Evaluator(Protocol):
    async def evaluate(self, test: ITestCase, output: str, expectation: IExpectation) -> Evaluation: ...


class ExactMatchEvaluator(Evaluator):
    async def evaluate(self, test: ITestCase, output: str, expectation: IExpectation) -> Evaluation:
        value = 1 if output == validate_expectation(expectation) else 0
        return Evaluation(
            value=value,
            feedback="Output matches the expected answer." if value == 1 else "Output does not match the expected answer.",
        )
