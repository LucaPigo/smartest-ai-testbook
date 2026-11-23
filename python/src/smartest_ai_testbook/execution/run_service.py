"""Application service for the execution use cases.

RunService starts, lists and reads evaluation runs. It receives every collaborator
by dependency injection: the repositories, the runner and the configured model
provider (OpenAI, the mock, or None when no provider is configured).

Outcomes use no extra classes: an operation returns None when the suite or run
does not exist, and raises ValueError for invalid input.
"""

from typing import Protocol
from uuid import UUID

from smartest_ai_testbook.execution.eval_run import IEvalRun
from smartest_ai_testbook.execution.eval_runner import IEvalRunner
from smartest_ai_testbook.execution.model import ModelProvider
from smartest_ai_testbook.execution.repository import RunRepository
from smartest_ai_testbook.test_creation.repository import SuiteRepository

Id = UUID | str


class IRunService(Protocol):
    async def run_suite(self, suite_id: Id, provider_name: str, model_name: str) -> IEvalRun | None: ...
    def list_runs(self, suite_id: Id) -> list[IEvalRun] | None: ...
    def get_run(self, run_id: Id) -> IEvalRun | None: ...


class RunService(IRunService):
    def __init__(self, suites: SuiteRepository, runs: RunRepository, runner: IEvalRunner,
                 provider: ModelProvider | None):
        self.suites = suites
        self.runs = runs
        self.runner = runner
        self.provider = provider

    async def run_suite(self, suite_id: Id, provider_name: str, model_name: str) -> IEvalRun | None:
        suite = self.suites.get(suite_id)
        if suite is None:
            return None
        # Only a run for the configured provider, with a model name, is accepted.
        if self.provider is None or provider_name != self.provider.provider_name or not model_name.strip():
            raise ValueError("Unknown provider or unavailable model configuration")
        # The runner raises ValueError for an empty suite; the run is saved only when it completes.
        run = await self.runner.run(suite, self.provider.get_model(model_name))
        self.runs.save(run)
        return run

    def list_runs(self, suite_id: Id) -> list[IEvalRun] | None:
        if self.suites.get(suite_id) is None:
            return None
        return self.runs.list(suite_id)

    def get_run(self, run_id: Id) -> IEvalRun | None:
        return self.runs.get(run_id)
