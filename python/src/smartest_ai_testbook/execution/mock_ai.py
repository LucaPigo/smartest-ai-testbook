"""Offline replacements for the two AI integration points.

MockModel (supplied by MockProvider) replaces the system under test, and MockEvaluator
replaces the AI evaluation service. They check the application flow without real models,
not the quality of the results.
"""

from typing import Mapping

from smartest_ai_testbook.execution.exact_match_evaluator import Evaluation, Evaluator
from smartest_ai_testbook.execution.model import Model, ModelProvider, fill_variables
from smartest_ai_testbook.test_creation.expectation import IExpectation, validate_expectation
from smartest_ai_testbook.test_creation.test_case import ITestCase


class MockModel(Model):
    provider_name = "mock"

    def __init__(self, model_name: str):
        self.model_name = model_name

    async def generate_response(self, prompt: str, variables: Mapping[str, str]) -> str:
        return f"[mock] {fill_variables(prompt, variables)}"


class MockProvider(ModelProvider):
    provider_name = "mock"

    def get_model(self, model_name: str) -> Model:
        return MockModel(model_name)


class MockEvaluator(Evaluator):
    """Used in place of semantic similarity and LLM judge: every valid expectation scores 1."""

    async def evaluate(self, test: ITestCase, output: str, expectation: IExpectation) -> Evaluation:
        validate_expectation(expectation)
        return Evaluation(value=1, feedback="Mock evaluation")
