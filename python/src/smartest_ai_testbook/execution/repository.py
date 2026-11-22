from typing import Protocol
from uuid import UUID

from smartest_ai_testbook.execution.eval_run import IEvalRun


class RunRepository(Protocol):
    def save(self, run: IEvalRun) -> None: ...
    def get(self, run_id: UUID | str) -> IEvalRun | None: ...
    def list(self, suite_id: UUID | str) -> list[IEvalRun]: ...
