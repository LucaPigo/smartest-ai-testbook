from dataclasses import dataclass, replace
from typing import Protocol
from uuid import UUID

from smartest_ai_testbook.execution.eval_run import EvalScore, IEvalRun


@dataclass
class ReportResult:
    test_id: UUID | str
    prompt: str
    output: str | None
    error: str | None
    passed: bool
    scores: list[EvalScore]


class IEvalReport(Protocol):
    id: UUID
    suite_id: UUID | str
    started_at: str
    provider_name: str
    model_name: str
    results: list[ReportResult]


class IReportGenerator(Protocol):
    def generate(self, run: IEvalRun) -> IEvalReport: ...


class EvalReport(IEvalReport):
    def __init__(self, run: IEvalRun):
        self.id = run.id
        self.suite_id = run.suite_id
        self.started_at = run.started_at
        self.provider_name = run.provider_name
        self.model_name = run.model_name
        self.results = [
            ReportResult(result.test_id, result.prompt, result.output, result.error, result.passed,
                         [replace(score) for score in result.scores])
            for result in run.results
        ]


class ReportGenerator(IReportGenerator):
    def generate(self, run: IEvalRun) -> IEvalReport:
        return EvalReport(run)
