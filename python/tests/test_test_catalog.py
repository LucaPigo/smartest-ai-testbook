from uuid import uuid4

import pytest

from smartest_ai_testbook.persistence.sqlite import SQLAlchemySuiteRepository, create_database
from smartest_ai_testbook.test_creation.expectation import Expectation
from smartest_ai_testbook.test_creation.test_catalog import TestCatalog


def exact(expected="Paris", id=None):
    return Expectation("Exact", "exactMatch", 1, {"expected": expected}, id=id)


def judge(rubric="Names the capital."):
    return Expectation("Judge", "llmJudge", 0.8, {"rubric": rubric})


@pytest.fixture
def repository(tmp_path):
    return SQLAlchemySuiteRepository(create_database(f"sqlite:///{(tmp_path / 'catalog.db').as_posix()}"))


@pytest.fixture
def catalog(repository):
    return TestCatalog(repository)


def test_suites_are_created_updated_listed_and_deleted(catalog, repository):
    suite = catalog.create_suite("Suite", "First")
    assert [item.id for item in catalog.list_suites()] == [suite.id]
    updated = catalog.update_suite(suite.id, "Edited", "Second")
    assert (updated.id, repository.get(suite.id).name, repository.get(suite.id).description) == (suite.id, "Edited", "Second")
    assert catalog.delete_suite(suite.id) is True
    assert catalog.list_suites() == []


def test_missing_items_return_nothing_and_save_nothing(catalog, repository):
    missing = uuid4()
    assert catalog.update_suite(missing, "Name") is None
    assert catalog.delete_suite(missing) is False
    assert catalog.list_test_cases(missing) is None
    assert catalog.add_test_case(missing, "Title", "Prompt", {}, [exact()]) is None
    assert catalog.get_test_case(missing) is None
    assert catalog.update_test_case(missing, "Title", "Prompt", {}, []) is None
    assert catalog.delete_test_case(missing) is False
    assert catalog.list_expectations(missing) is None
    assert catalog.add_expectation(missing, exact()) is None
    assert catalog.update_expectation(missing, exact()) is None
    assert repository.list() == []


def test_test_cases_are_added_read_updated_and_deleted_with_stable_ids(catalog, repository):
    suite = catalog.create_suite("Suite")
    case = catalog.add_test_case(suite.id, "Capital", "Capital of {{country}}?", {"country": "France"}, [exact()])
    expectation_id = case.expectations[0].id
    assert [item.id for item in catalog.list_test_cases(suite.id)] == [case.id]
    assert catalog.get_test_case(case.id).prompt == "Capital of {{country}}?"

    updated = catalog.update_test_case(case.id, "Edited", "Changed", None, [exact("Rome", id=expectation_id)])
    stored = repository.get(suite.id).tests[0]
    assert (updated.id, stored.id, stored.title, stored.variables) == (case.id, case.id, "Edited", {})
    assert (stored.expectations[0].id, stored.expectations[0].options) == (expectation_id, {"expected": "Rome"})

    assert catalog.delete_test_case(case.id) is True
    assert repository.get(suite.id).tests == []


def test_expectations_are_listed_added_and_updated(catalog, repository):
    suite = catalog.create_suite("Suite")
    case = catalog.add_test_case(suite.id, "Capital", "Question", {}, [exact()])
    added = catalog.add_expectation(case.id, judge())
    assert [item.id for item in catalog.list_expectations(case.id)] == [case.expectations[0].id, added.id]

    updated = catalog.update_expectation(added.id, judge("Only the city name."))
    stored = repository.get(suite.id).tests[0]
    assert (updated.id, stored.id) == (added.id, case.id)
    assert stored.expectations[1].options == {"rubric": "Only the city name."}


def test_invalid_input_raises_and_saves_nothing(catalog, repository):
    suite = catalog.create_suite("Suite")
    with pytest.raises(ValueError, match="Title"):
        catalog.add_test_case(suite.id, "  ", "Prompt", {}, [exact()])
    assert repository.get(suite.id).tests == []

    case = catalog.add_test_case(suite.id, "Capital", "Question", {}, [exact()])
    other = catalog.add_test_case(suite.id, "Other", "Question", {}, [exact()])
    own_id, foreign_id = case.expectations[0].id, other.expectations[0].id
    for ids in ([foreign_id], [own_id, own_id], [uuid4()]):
        with pytest.raises(ValueError, match="Expectation IDs must belong to this test case"):
            catalog.update_test_case(case.id, "Edited", "Question", {}, [exact(id=item) for item in ids])
    with pytest.raises(ValueError, match="rubric"):
        catalog.add_expectation(case.id, Expectation("Judge", "llmJudge", 0.8, {}))
    with pytest.raises(ValueError, match="rubric"):
        catalog.update_expectation(own_id, Expectation("Judge", "llmJudge", 0.8, {}))

    stored = repository.get(suite.id).tests[0]
    assert (stored.title, [item.id for item in stored.expectations]) == ("Capital", [own_id])
