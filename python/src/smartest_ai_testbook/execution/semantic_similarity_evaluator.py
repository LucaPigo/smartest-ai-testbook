import math

from openai import OpenAIError

from smartest_ai_testbook.execution.exact_match_evaluator import Evaluation, Evaluator
from smartest_ai_testbook.test_creation.expectation import IExpectation, validate_expectation
from smartest_ai_testbook.test_creation.test_case import ITestCase


class SemanticSimilarityEvaluator(Evaluator):
    """Cosine similarity normalized from [-1, 1] to the [0, 1] score scale."""

    def __init__(self, client, embedding_model: str):
        self.client = client
        self.embedding_model = embedding_model

    async def evaluate(self, test: ITestCase, output: str, expectation: IExpectation) -> Evaluation:
        expected = validate_expectation(expectation)
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model, input=[expected, output], encoding_format="float"
            )
        except OpenAIError:
            raise RuntimeError("OpenAI request failed.") from None
        try:
            vectors = {item.index: item.embedding for item in response.data}
            if (len(response.data) != 2 or set(vectors) != {0, 1}
                    or any(isinstance(item.index, bool) for item in response.data)):
                raise ValueError
            first, second = vectors[0], vectors[1]
            if not first or len(first) != len(second):
                raise ValueError
            if any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) for v in [*first, *second]):
                raise ValueError
            first_norm = math.hypot(*first)
            second_norm = math.hypot(*second)
            if not first_norm or not second_norm or not math.isfinite(first_norm) or not math.isfinite(second_norm):
                raise ValueError
            cosine = sum((a / first_norm) * (b / second_norm) for a, b in zip(first, second))
        except (AttributeError, TypeError, ValueError) as error:
            raise ValueError("OpenAI returned invalid embeddings.") from error
        value = (max(-1.0, min(1.0, cosine)) + 1) / 2
        return Evaluation(value=value, feedback="Similarity to the reference answer.")
