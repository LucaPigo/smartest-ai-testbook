import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import httpx
from openai import APIError

from smartest_ai_testbook.execution.eval_runner import EvalRunner
from smartest_ai_testbook.execution.exact_match_evaluator import ExactMatchEvaluator
from smartest_ai_testbook.execution.llm_judge_evaluator import LLMJudgeEvaluator
from smartest_ai_testbook.execution.openai_model import OpenAIProvider
from smartest_ai_testbook.execution.semantic_similarity_evaluator import SemanticSimilarityEvaluator
from smartest_ai_testbook.test_creation.expectation import Expectation
from smartest_ai_testbook.test_creation.test_case import TestCase as Case
from smartest_ai_testbook.test_creation.test_suite import TestSuite as Suite


def run(awaitable):
    return asyncio.run(awaitable)


def client(*, text="ok", vectors=None):
    response = SimpleNamespace(status="completed", output_text=text)
    data = [SimpleNamespace(index=i, embedding=v) for i, v in enumerate(vectors if vectors is not None else [[1.0, 0.0], [1.0, 0.0]])]
    return SimpleNamespace(responses=SimpleNamespace(create=AsyncMock(return_value=response)),
                           embeddings=SimpleNamespace(create=AsyncMock(return_value=SimpleNamespace(data=data))))


def case(expectations=None):
    return Case("Question", {}, expectations or [Expectation("Exact", "exactMatch", 1, {"expected": "Reference"})], title="Test")


def test_model_sends_selected_model_and_substitutes_once():
    api = client(text="Answer")
    model = OpenAIProvider(api).get_model("chosen-model")
    assert run(model.generate_response("Hello {{name}} and {{name}}; {{other}}", {"name": "{{other}}", "other": "world"})) == "Answer"
    assert model.provider_name == "openai"
    api.responses.create.assert_awaited_once_with(model="chosen-model", input="Hello {{other}} and {{other}}; world")


def test_model_rejects_incomplete_or_empty_output_and_propagates_errors():
    api = client(text="")
    model = OpenAIProvider(api).get_model("model")
    with pytest.raises(ValueError):
        run(model.generate_response("prompt", {}))
    api.responses.create.return_value = SimpleNamespace(status="incomplete", output_text="partial")
    with pytest.raises(ValueError):
        run(model.generate_response("prompt", {}))
    api.responses.create.side_effect = RuntimeError("provider unavailable")
    with pytest.raises(RuntimeError, match="provider unavailable"):
        run(model.generate_response("prompt", {}))


@pytest.mark.parametrize("output", ["Reference", "reference", "Reference "])
def test_exact_matching_is_literal_and_returns_only_value_and_feedback(output):
    expectation = Expectation("Exact", "exactMatch", 1, {"expected": "Reference"})
    score = run(ExactMatchEvaluator().evaluate(case(), output, expectation))
    assert score.value == (1 if output == "Reference" else 0)
    assert set(vars(score)) == {"value", "feedback"}


@pytest.mark.parametrize("vectors, value", [([[1, 0], [1, 0]], 1), ([[1, 0], [0, 1]], 0.5), ([[1, 0], [-1, 0]], 0)])
def test_semantic_similarity_uses_cosine_on_zero_to_one_scale(vectors, value):
    api = client(vectors=vectors)
    evaluator = SemanticSimilarityEvaluator(api, "embedding-model")
    score = run(evaluator.evaluate(case(), "Output", Expectation("similarity", "semanticSimilarity", 0.6, {"expected": "Reference"})))
    assert score.value == value
    assert set(vars(score)) == {"value", "feedback"}
    api.embeddings.create.assert_awaited_once_with(model="embedding-model", input=["Reference", "Output"], encoding_format="float")


def test_semantic_similarity_reads_each_local_reference_and_response_order_uses_indices():
    api = client(vectors=[[1, 0], [1, 0]])
    api.embeddings.create.return_value.data.reverse()
    evaluator = SemanticSimilarityEvaluator(api, "embed")
    for reference in ("Reference", "Another reference"):
        score = run(evaluator.evaluate(case(), "Output", Expectation("similarity", "semanticSimilarity", 1, {"expected": reference})))
        assert score.value == 1
    assert [call.kwargs["input"] for call in api.embeddings.create.await_args_list] == [["Reference", "Output"], ["Another reference", "Output"]]


@pytest.mark.parametrize("indices", [[0], [0, 0], [0, True], [False, 1]])
def test_semantic_similarity_rejects_missing_duplicate_or_boolean_indices(indices):
    api = client()
    api.embeddings.create.return_value.data = [SimpleNamespace(index=i, embedding=[1, 0]) for i in indices]
    with pytest.raises(ValueError, match="invalid embeddings"):
        run(SemanticSimilarityEvaluator(api, "embed").evaluate(
            case(), "Output", Expectation("similarity", "semanticSimilarity", 0.5, {"expected": "Reference"})))


@pytest.mark.parametrize("vectors", [[[0, 0], [1, 1]], [[1], [1, 2]], [[float('nan')], [1]], [[1], [float('inf')]], [[], []]])
def test_semantic_similarity_rejects_invalid_embeddings(vectors):
    evaluator = SemanticSimilarityEvaluator(client(vectors=vectors), "embed")
    with pytest.raises(ValueError):
        run(evaluator.evaluate(case(), "Output", Expectation("similarity", "semanticSimilarity", 0.5, {"expected": "Reference"})))


def test_judge_uses_independent_rubrics_and_returns_only_value_and_feedback():
    api = client(text=json.dumps({"score": 0.8, "feedback": "Good"}))
    evaluator = LLMJudgeEvaluator(api, "judge-model")
    for rubric in ("Be correct.", "Be concise."):
        score = run(evaluator.evaluate(case(), "Output", Expectation("judge", "llmJudge", 0.8, {"rubric": rubric})))
        assert vars(score) == {"value": 0.8, "feedback": "Good"}
    requests = [call.kwargs for call in api.responses.create.await_args_list]
    for request, rubric in zip(requests, ("Be correct.", "Be concise.")):
        assert request["model"] == "judge-model"
        assert f'"rubric": "{rubric}"' in request["input"] and '"answer": "Output"' in request["input"]
        assert request["text"]["format"]["type"] == "json_schema"
    assert "Be concise." not in requests[0]["input"]
    assert "Be correct." not in requests[1]["input"]


def test_judge_receives_prompt_variables():
    api = client(text=json.dumps({"score": 1, "feedback": "Correct"}))
    expectation = Expectation("judge", "llmJudge", 0.5, {"rubric": "Correct city"})
    test = Case("Capital of {{country}}?", {"country": "France"}, [expectation], title="Test")
    run(LLMJudgeEvaluator(api, "judge").evaluate(test, "Paris", expectation))
    assert '"country": "France"' in api.responses.create.await_args.kwargs["input"]


@pytest.mark.parametrize("text", ["not json", "{}", "null", "[]", '{"score": true, "feedback": "x"}', '{"score": 1.1, "feedback": "x"}', '{"score": -0.1, "feedback": "x"}', '{"score": 0.5, "feedback": " "}', '{"score": NaN, "feedback": "x"}', '{"score": 0.5, "feedback": "x", "extra": 1}'])
def test_judge_rejects_malformed_output(text):
    with pytest.raises(ValueError):
        run(LLMJudgeEvaluator(client(text=text), "judge").evaluate(case(), "Output", Expectation("judge", "llmJudge", 0.5, {"rubric": "Correct and concise"})))


def test_judge_rejects_incomplete_response_and_propagates_provider_error():
    api = client(text='{"score": 0.8, "feedback": "Good"}')
    evaluator = LLMJudgeEvaluator(api, "judge")
    expectation = Expectation("judge", "llmJudge", 0.5, {"rubric": "Correct and concise"})
    api.responses.create.return_value.status = "incomplete"
    with pytest.raises(ValueError, match="invalid judge"):
        run(evaluator.evaluate(case(), "Output", expectation))
    api.responses.create.side_effect = RuntimeError("provider unavailable")
    with pytest.raises(RuntimeError, match="provider unavailable"):
        run(evaluator.evaluate(case(), "Output", expectation))


def test_failed_judge_does_not_prevent_other_expectation():
    api = client(text="broken")
    suite = Suite("Errors")
    suite.add_test(case([Expectation("judge", "llmJudge", 0.5, {"rubric": "Correct and concise"}), Expectation("exact", "exactMatch", 1, {"expected": "Reference"})]))
    model = OpenAIProvider(client(text="Reference")).get_model("model")
    result = run(EvalRunner({"llmJudge": LLMJudgeEvaluator(api, "judge"), "exactMatch": ExactMatchEvaluator()}).run(suite, model)).results[0]
    assert result.scores[0].error is not None and not result.scores[0].passed
    assert result.scores[1].passed


@pytest.mark.parametrize("failure", ["generation", "embeddings", "judge"])
def test_openai_sdk_errors_do_not_expose_provider_message_in_run(failure):
    secret = "sentinel-secret-do-not-expose"
    api = client(text='{"score": 1, "feedback": "Good"}' if failure == "judge" else "Reference")
    error = APIError(secret, request=httpx.Request("POST", "https://example.invalid"), body={"message": secret})
    if failure == "embeddings":
        api.embeddings.create.side_effect = error
    elif failure == "judge":
        # The first call generates an answer; the second invokes the judge.
        api.responses.create.side_effect = [SimpleNamespace(status="completed", output_text="Reference"), error]
    else:
        api.responses.create.side_effect = error
    options = {"expected": "Reference"} if failure == "embeddings" else {"rubric": "Correct and concise"}
    expectation = Expectation("Check", "semanticSimilarity" if failure == "embeddings" else "llmJudge", 0.5, options)
    suite = Suite("Errors")
    suite.add_test(case([expectation]))
    runner = EvalRunner({"semanticSimilarity": SemanticSimilarityEvaluator(api, "embed"),
                         "llmJudge": LLMJudgeEvaluator(api, "judge")})
    result = run(runner.run(suite, OpenAIProvider(api).get_model("model"))).results[0]
    message = result.error if failure == "generation" else result.scores[0].error
    assert message == "OpenAI request failed."
    assert secret not in message
