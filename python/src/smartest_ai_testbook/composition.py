"""Compose the application independently of the optional HTTP server."""

import os
from dataclasses import dataclass

from smartest_ai_testbook.execution.eval_runner import EvalRunner
from smartest_ai_testbook.execution.exact_match_evaluator import ExactMatchEvaluator
from smartest_ai_testbook.execution.llm_judge_evaluator import LLMJudgeEvaluator
from smartest_ai_testbook.execution.model import ModelProvider
from smartest_ai_testbook.execution.openai_model import OpenAIProvider
from smartest_ai_testbook.execution.repository import RunRepository
from smartest_ai_testbook.execution.semantic_similarity_evaluator import SemanticSimilarityEvaluator
from smartest_ai_testbook.persistence.sqlite import SQLAlchemyRunRepository, SQLAlchemySuiteRepository, create_database
from smartest_ai_testbook.test_creation.repository import SuiteRepository


@dataclass
class Dependencies:
    suites: SuiteRepository
    runs: RunRepository
    runner: EvalRunner
    provider: ModelProvider | None


def create_dependencies(database_url: str | None = None, client=None) -> Dependencies:
    engine = create_database(database_url or os.getenv("DATABASE_URL", "sqlite:///smartest-ai-testbook.db"))
    if client is None and os.getenv("OPENAI_API_KEY"):
        from openai import AsyncOpenAI
        client = AsyncOpenAI()
    evaluators = {"exactMatch": ExactMatchEvaluator()}
    if client is not None:
        evaluators.update({
            "semanticSimilarity": SemanticSimilarityEvaluator(client, os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")),
            "llmJudge": LLMJudgeEvaluator(client, os.getenv("OPENAI_JUDGE_MODEL", "gpt-4o-mini")),
        })
    return Dependencies(SQLAlchemySuiteRepository(engine), SQLAlchemyRunRepository(engine),
                        EvalRunner(evaluators), OpenAIProvider(client) if client is not None else None)
