from dataclasses import asdict
from uuid import UUID

from sqlalchemy import JSON, ForeignKey, String, create_engine, event, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from smartest_ai_testbook.execution.eval_run import EvalResult, EvalRun, EvalScore, IEvalRun
from smartest_ai_testbook.execution.repository import RunRepository
from smartest_ai_testbook.test_creation.expectation import Expectation
from smartest_ai_testbook.test_creation.repository import SuiteRepository
from smartest_ai_testbook.test_creation.test_case import TestCase
from smartest_ai_testbook.test_creation.test_suite import ITestSuite, TestSuite


class Base(DeclarativeBase):
    pass


class SuiteRow(Base):
    __tablename__ = "suites"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    tests: Mapped[list] = mapped_column(JSON)


class RunRow(Base):
    __tablename__ = "runs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    suite_id: Mapped[str] = mapped_column(ForeignKey("suites.id", ondelete="CASCADE"), index=True)
    started_at: Mapped[str] = mapped_column(String)
    provider_name: Mapped[str] = mapped_column(String)
    model_name: Mapped[str] = mapped_column(String)
    results: Mapped[list] = mapped_column(JSON)


def create_database(database_url: str) -> Engine:
    engine = create_engine(database_url)

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    return engine


def _identity(value):
    try:
        return UUID(value)
    except (TypeError, ValueError):
        return value


def _suite(row: SuiteRow) -> TestSuite:
    suite = TestSuite(row.name, row.description, UUID(row.id))
    for item in row.tests:
        expectations = []
        for entry in item["expectations"]:
            options = entry["options"].copy()
            key = "rubric" if entry["evaluator_type"] == "llmJudge" else "expected"
            legacy_key = "rubric" if key == "rubric" else "goldenReference"
            if key not in options and item.get(legacy_key) is not None:
                options[key] = item[legacy_key]
            expectations.append(Expectation(entry["name"], entry["evaluator_type"], entry["threshold"], options, UUID(entry["id"])))
        suite.add_test(TestCase(item["prompt"], item["variables"], expectations, UUID(item["id"]),
                                title=item.get("title") or item["prompt"]))
    return suite


class SQLAlchemySuiteRepository(SuiteRepository):
    def __init__(self, engine: Engine):
        self.engine = engine

    def save(self, suite: ITestSuite) -> None:
        tests = [{"id": str(test.id), "title": test.title, "prompt": test.prompt,
                    "variables": test.variables,
                    "expectations": [{
                        "id": str(e.id), 
                        "name": e.name, 
                        "evaluator_type": e.evaluator_type,
                        "threshold": e.threshold, 
                        "options": e.options} for e in test.expectations]}
                for test in suite.tests]
        with Session(self.engine) as session, session.begin():
            session.merge(SuiteRow(id=str(suite.id), name=suite.name, description=suite.description, tests=tests))

    def get(self, suite_id: UUID | str) -> ITestSuite | None:
        with Session(self.engine) as session:
            row = session.get(SuiteRow, str(suite_id))
            return _suite(row) if row else None

    def list(self) -> list[ITestSuite]:
        with Session(self.engine) as session:
            return [_suite(row) for row in session.scalars(select(SuiteRow))]

    def delete(self, suite_id: UUID | str) -> bool:
        with Session(self.engine) as session, session.begin():
            row = session.get(SuiteRow, str(suite_id))
            if row is None:
                return False
            session.delete(row)
            return True


def _run(row: RunRow) -> EvalRun:
    run = EvalRun(_identity(row.suite_id), row.provider_name, row.model_name)
    run.id, run.started_at = UUID(row.id), row.started_at
    for item in row.results:
        result = EvalResult(_identity(item["test_id"]), item["prompt"], item["output"], item["error"])
        for score in item["scores"]:
            result.add_score(EvalScore(**{**score, "expectation_id": _identity(score["expectation_id"])}))
        run.add_result(result)
    return run


class SQLAlchemyRunRepository(RunRepository):
    def __init__(self, engine: Engine):
        self.engine = engine

    def save(self, run: IEvalRun) -> None:
        results = []
        for result in run.results:
            scores = []
            for score in result.scores:
                data = asdict(score)
                if data["expectation_id"] is not None:
                    data["expectation_id"] = str(data["expectation_id"])
                scores.append(data)
            results.append({"test_id": str(result.test_id), "prompt": result.prompt,
                            "output": result.output, "error": result.error, "scores": scores})
        with Session(self.engine) as session, session.begin():
            session.merge(RunRow(id=str(run.id), suite_id=str(run.suite_id), started_at=run.started_at,
                                 provider_name=run.provider_name, model_name=run.model_name, results=results))

    def get(self, run_id: UUID | str) -> IEvalRun | None:
        with Session(self.engine) as session:
            row = session.get(RunRow, str(run_id))
            return _run(row) if row else None

    def list(self, suite_id: UUID | str) -> list[IEvalRun]:
        with Session(self.engine) as session:
            return [_run(row) for row in session.scalars(select(RunRow).where(RunRow.suite_id == str(suite_id)))]
