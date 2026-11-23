"""Compose the application independently of the optional HTTP server.

This is the single place where the application objects are created and connected
to each other ("composition root"). The other classes do not create what they need:
they receive it ready to use from here. This technique is called dependency injection.

Benefits:
- tests can pass a temporary database or a fake OpenAI client without changing other code;
- the domain does not depend on the web server: FastAPI calls `create_dependencies`,
  but the application can also be used without it.
"""

import os
from dataclasses import dataclass

from smartest_ai_testbook.execution.eval_runner import EvalRunner
from smartest_ai_testbook.execution.exact_match_evaluator import Evaluator, ExactMatchEvaluator
from smartest_ai_testbook.execution.llm_judge_evaluator import LLMJudgeEvaluator
from smartest_ai_testbook.execution.mock_ai import MockEvaluator, MockProvider
from smartest_ai_testbook.execution.model import ModelProvider
from smartest_ai_testbook.execution.openai_model import OpenAIProvider
from smartest_ai_testbook.execution.repository import RunRepository
from smartest_ai_testbook.execution.semantic_similarity_evaluator import SemanticSimilarityEvaluator
from smartest_ai_testbook.persistence.sqlite import SQLAlchemyRunRepository, SQLAlchemySuiteRepository, create_database
from smartest_ai_testbook.test_creation.repository import SuiteRepository

# What @dataclass does
# The class only lists fields with their types and has no handwritten constructor. @dataclass generates it automatically from the fields, in the order they are declared. It is as if we had written:
# class Dependencies:
#     def __init__(self, suites, runs, runner, provider):
#         self.suites = suites
#         self.runs = runs
#         self.runner = runner
#         self.provider = provider
@dataclass
class Dependencies:
    """Container that holds the ready-to-use objects of the application."""

    suites: SuiteRepository      # saves and reads test suites
    runs: RunRepository          # saves and reads evaluation runs
    runner: EvalRunner           # runs a suite and evaluates the answers
    provider: ModelProvider | None  # gives access to the models under test; None without OpenAI or mock mode


def create_dependencies(database_url: str | None = None, client=None, ai_mode: str | None = None) -> Dependencies:
    """Create all the application objects and return them in a Dependencies container.

    All parameters are optional and mainly useful in tests:
    - `database_url`: the database to use instead of the configured one;
    - `client`: an OpenAI client (real or fake) to use instead of creating one;
    - `ai_mode`: "mock" to use the offline mocks instead of the AI_MODE environment variable.
    """
    # 1. Database. Priority: the parameter, then the DATABASE_URL environment
    #    variable, then a local SQLite file.
    engine = create_database(database_url or os.getenv("DATABASE_URL", "sqlite:///smartest-ai-testbook.db"))

    # 2. Evaluators: they decide whether a model answer is correct.
    #    The dict maps the name used in expectations to the object that does the evaluation.
    #    The type hint says the dict may hold any Evaluator, not only ExactMatchEvaluator.
    #    exactMatch compares texts exactly and needs no external service, so it is always available.
    evaluators: dict[str, Evaluator] = {"exactMatch": ExactMatchEvaluator()}

    # 3. The two AI integration points: the provider of the system under test (SUT)
    #    and the AI evaluators (semanticSimilarity and llmJudge).
    provider: ModelProvider | None = None
    if (ai_mode or os.getenv("AI_MODE")) == "mock":
        # Mock mode replaces both points with offline mocks: no OpenAI client is created,
        # even when a key is configured. One mock evaluator serves both AI evaluator types.
        mock_evaluator = MockEvaluator()
        evaluators.update({"semanticSimilarity": mock_evaluator, "llmJudge": mock_evaluator})
        provider = MockProvider()
    else:
        # OpenAI client. If none was passed and an API key is configured, create a real one.
        # Otherwise `client` stays None and the application works without OpenAI.
        # The import is inside the `if` so the openai library is loaded only when needed.
        if client is None and os.getenv("OPENAI_API_KEY"):
            from openai import AsyncOpenAI
            client = AsyncOpenAI()
        # The other evaluators call OpenAI, so they are added only when a client exists.
        # The model names can be changed with environment variables.
        if client is not None:
            evaluators.update({
                "semanticSimilarity": SemanticSimilarityEvaluator(client, os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")),
                "llmJudge": LLMJudgeEvaluator(client, os.getenv("OPENAI_JUDGE_MODEL", "gpt-4o-mini")),
            })
            provider = OpenAIProvider(client)

    # Compose the dependencies and return them
    # 4. Both repositories share the same database. Named arguments make it clear
    #    which field of Dependencies receives each object.
    return Dependencies(
        suites=SQLAlchemySuiteRepository(engine),
        runs=SQLAlchemyRunRepository(engine),
        runner=EvalRunner(evaluators),
        provider=provider,
    )
