from copy import deepcopy
from dataclasses import asdict

import pytest
from sqlalchemy.orm import Session

from smartest_ai_testbook.execution.eval_run import EvalResult, EvalRun, EvalScore
from smartest_ai_testbook.persistence.sqlite import SQLAlchemyRunRepository, SQLAlchemySuiteRepository, SuiteRow, create_database
from smartest_ai_testbook.test_creation.expectation import Expectation
from smartest_ai_testbook.test_creation.test_case import TestCase as Case
from smartest_ai_testbook.test_creation.test_suite import TestSuite as Suite


@pytest.fixture
def repositories(tmp_path):
    url = f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
    engine = create_database(url)
    return url, SQLAlchemySuiteRepository(engine), SQLAlchemyRunRepository(engine)


def make_suite():
    suite = Suite("Answers", "Original description")
    suite.add_test(Case("Question {{place}}", {"place": "France"},
                        [Expectation("Exact", "exactMatch", 1, {"expected": "Paris"})], title="Capital"))
    return suite


def test_suite_round_trip_update_delete_and_restart(repositories):
    url, suites, _ = repositories
    suite = make_suite()
    suites.save(suite)
    loaded = SQLAlchemySuiteRepository(create_database(url)).get(suite.id)
    assert loaded.id == suite.id and loaded.description == suite.description
    assert loaded.tests[0].id == suite.tests[0].id
    assert loaded.tests[0].title == "Capital"
    assert loaded.tests[0].variables == {"place": "France"}
    assert loaded.tests[0].expectations[0].id == suite.tests[0].expectations[0].id
    assert loaded.tests[0].expectations[0].options == {"expected": "Paris"}
    loaded.name = "Edited"
    loaded.tests[0].prompt = "Changed"
    suites.save(loaded)
    assert [(item.name, item.tests[0].prompt) for item in suites.list()] == [("Edited", "Changed")]
    assert suites.delete(suite.id) and not suites.delete(suite.id)
    assert suites.get(suite.id) is None


def test_failed_save_preserves_previous_aggregate(repositories):
    _, suites, _ = repositories
    suite = make_suite()
    suites.save(suite)
    suite.name = "Invalid update"
    suite.tests[0].expectations[0].options = {"not_json": object()}
    with pytest.raises(Exception):
        suites.save(suite)
    assert suites.get(suite.id).name == "Answers"


def test_existing_tests_without_title_remain_readable(repositories):
    _, suites, _ = repositories
    suite = make_suite()
    suites.save(suite)
    with Session(suites.engine) as session, session.begin():
        row = session.get(SuiteRow, str(suite.id))
        row.tests = [{key: value for key, value in item.items() if key != "title"} for item in row.tests]
    restored = suites.get(suite.id)
    assert restored.tests[0].title == restored.tests[0].prompt
    suites.save(restored)
    assert suites.get(suite.id).tests[0].title == restored.tests[0].prompt


def test_runs_are_snapshots_and_cascade_only_with_suite(repositories):
    url, suites, runs = repositories
    suite = make_suite()
    suites.save(suite)
    test = suite.tests[0]
    run = EvalRun(suite.id, "fake", "model")
    result = EvalResult(test.id, test.prompt, output="Paris")
    result.add_score(EvalScore(expectation_id=test.expectations[0].id, expectation_name="Exact", evaluator_type="exactMatch",
                               threshold=1, value=1, scale_min=0, scale_max=1, passed=True, feedback="matched"))
    result.add_score(EvalScore(expectation_id="failed-id", passed=False, feedback="Evaluation failed.", error="unavailable"))
    run.add_result(result)
    runs.save(run)
    suite.tests.clear()
    suites.save(suite)
    restored = SQLAlchemyRunRepository(create_database(url)).get(run.id)
    assert (restored.id, restored.suite_id, restored.started_at) == (run.id, suite.id, run.started_at)
    assert (restored.results[0].prompt, restored.results[0].output) == ("Question {{place}}", "Paris")
    assert [asdict(score) for score in restored.results[0].scores] == [asdict(score) for score in result.scores]
    assert [item.id for item in runs.list(suite.id)] == [run.id]
    assert suites.delete(suite.id)
    assert runs.get(run.id) is None and runs.list(suite.id) == []


def test_run_rejects_missing_suite(repositories):
    _, _, runs = repositories
    with pytest.raises(Exception):
        runs.save(EvalRun(make_suite().id, "fake", "model"))


def test_legacy_criteria_load_locally_and_resave_without_changing_runs(repositories):
    _, suites, runs = repositories
    suite = make_suite()
    case = suite.tests[0]
    case.expectations.extend([
        Expectation("Semantic", "semanticSimilarity", 0.8, {"expected": "Lyon"}),
        Expectation("Judge", "llmJudge", 0.8, {"rubric": "Correct city"}),
    ])
    suites.save(suite)
    run = EvalRun(suite.id, "fake", "model")
    result = EvalResult(case.id, case.prompt, "Paris")
    result.add_score(EvalScore(feedback="Original", passed=True, value=1, threshold=1,
                               expectation_id=case.expectations[0].id))
    run.add_result(result)
    runs.save(run)
    with Session(suites.engine) as session, session.begin():
        row = session.get(SuiteRow, str(suite.id))
        legacy = deepcopy(row.tests[0])
        legacy["goldenReference"], legacy["rubric"] = "Paris", "Correct city"
        legacy["expectations"][0]["options"] = {}
        legacy["expectations"][2]["options"] = {}
        row.tests = [dict(legacy)]

    restored = suites.get(suite.id)
    restored_case = restored.tests[0]
    assert restored_case.id == case.id and restored_case.title == case.title
    assert restored_case.variables == case.variables
    assert [e.id for e in restored_case.expectations] == [e.id for e in case.expectations]
    assert [e.options for e in restored_case.expectations] == [
        {"expected": "Paris"}, {"expected": "Lyon"}, {"rubric": "Correct city"},
    ]
    with Session(suites.engine) as session:
        assert "goldenReference" in session.get(SuiteRow, str(suite.id)).tests[0]
    suites.save(restored)
    with Session(suites.engine) as session:
        saved = session.get(SuiteRow, str(suite.id)).tests[0]
        assert set(saved) == {"id", "title", "prompt", "variables", "expectations"}
    assert suites.get(suite.id).tests[0].expectations[1].options == {"expected": "Lyon"}
    assert asdict(runs.get(run.id).results[0].scores[0]) == asdict(result.scores[0])
