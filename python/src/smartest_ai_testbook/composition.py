"""Compose the application independently of the optional HTTP server.

This is the single place where the application objects are created and connected
to each other ("composition root"). The other classes do not create what they need:
they receive it ready to use from here. This technique is called dependency injection.

What it returns are the two application services (TestCatalog and RunService): every
use case goes through them, and they save data through the injected repositories.

Benefits:
- tests can pass a temporary database, a fake OpenAI client or a fake provider without changing other code;
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
from smartest_ai_testbook.execution.run_service import IRunService, RunService
from smartest_ai_testbook.execution.semantic_similarity_evaluator import SemanticSimilarityEvaluator
from smartest_ai_testbook.persistence.sqlite import SQLAlchemyRunRepository, SQLAlchemySuiteRepository, create_database
from smartest_ai_testbook.test_creation.test_catalog import ITestCatalog, TestCatalog

# What @dataclass does
# The class only lists fields with their types and has no handwritten constructor. @dataclass generates it automatically from the fields, in the order they are declared. It is as if we had written:
# class Dependencies:
#     def __init__(self, catalog, runs):
#         self.catalog = catalog
#         self.runs = runs
@dataclass
class Dependencies:
    """Container that holds the application services, the entry points of every use case.

    Repositories, runner and provider are created below and injected into the services;
    callers (the web server, tests, scripts) only use the services.
    """

    catalog: ITestCatalog    # suites, test cases and expectations
    runs: IRunService        # start, list and read evaluation runs


def create_dependencies(database_url: str | None = None, client=None, ai_mode: str | None = None,
                        provider: ModelProvider | None = None) -> Dependencies:
    """Create all the application objects and return them in a Dependencies container.

    All parameters are optional and mainly useful in tests:
    - `database_url`: the database to use instead of the configured one;
    - `client`: an OpenAI client (real or fake) to use instead of creating one;
    - `provider`: a model provider (for example a fake) to use instead of the configured one;
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
    configured_provider: ModelProvider | None = None
    if (ai_mode or os.getenv("AI_MODE")) == "mock":
        # Mock mode replaces both points with offline mocks: no OpenAI client is created,
        # even when a key is configured. One mock evaluator serves both AI evaluator types.
        mock_evaluator = MockEvaluator()
        evaluators.update({"semanticSimilarity": mock_evaluator, "llmJudge": mock_evaluator})
        configured_provider = MockProvider()
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
            configured_provider = OpenAIProvider(client)

    # Compose the dependencies and return them
    # 4. Both repositories share the same database. Each application service receives
    #    the collaborators it needs; named arguments make it clear which field gets which service.
    suites = SQLAlchemySuiteRepository(engine)
    return Dependencies(
        catalog=TestCatalog(suites),
        runs=RunService(suites, SQLAlchemyRunRepository(engine), EvalRunner(evaluators),
                        provider if provider is not None else configured_provider),
    )
