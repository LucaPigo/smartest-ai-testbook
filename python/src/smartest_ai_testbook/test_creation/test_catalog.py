"""Application service for the test creation use cases.

TestCatalog is the single place where suites, test cases and expectations are
found, changed and saved. It receives the suite repository by dependency injection,
so it does not know how data is stored, and entities never save themselves.

Outcomes use no extra classes: an operation returns None (or False for a delete)
when the requested item does not exist, and raises ValueError for invalid input.
"""

from typing import Mapping, Protocol
from uuid import UUID

from smartest_ai_testbook.test_creation.expectation import Expectation, IExpectation
from smartest_ai_testbook.test_creation.repository import SuiteRepository
from smartest_ai_testbook.test_creation.test_case import ITestCase, TestCaseBuilder
from smartest_ai_testbook.test_creation.test_suite import ITestSuite, TestSuite

Id = UUID | str


class ITestCatalog(Protocol):
    def list_suites(self) -> list[ITestSuite]: ...
    def create_suite(self, name: str, description: str = "") -> ITestSuite: ...
    def update_suite(self, suite_id: Id, name: str, description: str = "") -> ITestSuite | None: ...
    def delete_suite(self, suite_id: Id) -> bool: ...
    def list_test_cases(self, suite_id: Id) -> list[ITestCase] | None: ...
    def add_test_case(self, suite_id: Id, title: str, prompt: str, variables: Mapping[str, str] | None,
                      expectations: list[IExpectation]) -> ITestCase | None: ...
    def get_test_case(self, case_id: Id) -> ITestCase | None: ...
    def update_test_case(self, case_id: Id, title: str, prompt: str, variables: Mapping[str, str] | None,
                         expectations: list[IExpectation]) -> ITestCase | None: ...
    def delete_test_case(self, case_id: Id) -> bool: ...
    def list_expectations(self, case_id: Id) -> list[IExpectation] | None: ...
    def add_expectation(self, case_id: Id, expectation: IExpectation) -> IExpectation | None: ...
    def update_expectation(self, expectation_id: Id, expectation: IExpectation) -> IExpectation | None: ...


class TestCatalog(ITestCatalog):
    def __init__(self, suites: SuiteRepository):
        self.suites = suites

    # --- Suites ---------------------------------------------------------------

    def list_suites(self) -> list[ITestSuite]:
        return self.suites.list()

    def create_suite(self, name: str, description: str = "") -> ITestSuite:
        suite = TestSuite(name, description)
        self.suites.save(suite)
        return suite

    def update_suite(self, suite_id: Id, name: str, description: str = "") -> ITestSuite | None:
        suite = self.suites.get(suite_id)
        if suite is None:
            return None
        suite.name, suite.description = name, description
        self.suites.save(suite)
        return suite

    def delete_suite(self, suite_id: Id) -> bool:
        # Deleting a suite also deletes its tests, expectations and run history.
        return self.suites.delete(suite_id)

    # --- Test cases -----------------------------------------------------------
    # Test cases are stored inside their suite, so every change saves the whole suite.

    def list_test_cases(self, suite_id: Id) -> list[ITestCase] | None:
        suite = self.suites.get(suite_id)
        return None if suite is None else suite.tests

    def add_test_case(self, suite_id: Id, title: str, prompt: str, variables: Mapping[str, str] | None,
                      expectations: list[IExpectation]) -> ITestCase | None:
        suite = self.suites.get(suite_id)
        if suite is None:
            return None
        case = _build_case(title, prompt, variables, expectations)  # ValueError before any save
        suite.add_test(case)
        self.suites.save(suite)
        return case

    def get_test_case(self, case_id: Id) -> ITestCase | None:
        found = self._find_case(case_id)
        return None if found is None else found[2]

    def update_test_case(self, case_id: Id, title: str, prompt: str, variables: Mapping[str, str] | None,
                         expectations: list[IExpectation]) -> ITestCase | None:
        found = self._find_case(case_id)
        if found is None:
            return None
        suite, index, old_case = found
        # The update may keep, change or drop existing expectations, but it may not
        # repeat an ID or use an ID that belongs to another test case.
        existing_ids = {item.id for item in old_case.expectations}
        input_ids = [item.id for item in expectations]
        if len(input_ids) != len(set(input_ids)) or not set(input_ids).issubset(existing_ids):
            raise ValueError("Expectation IDs must belong to this test case")
        # Build a new test case with the same ID and put it in place of the old one.
        case = _build_case(title, prompt, variables, expectations, id=old_case.id)
        suite.tests[index] = case
        self.suites.save(suite)
        return case

    def delete_test_case(self, case_id: Id) -> bool:
        found = self._find_case(case_id)
        if found is None:
            return False
        suite, index, _ = found
        suite.tests.pop(index)
        self.suites.save(suite)
        return True

    # --- Expectations ---------------------------------------------------------
    # Expectations live inside a test case, so a change rebuilds and revalidates that test case.

    def list_expectations(self, case_id: Id) -> list[IExpectation] | None:
        case = self.get_test_case(case_id)
        return None if case is None else case.expectations

    def add_expectation(self, case_id: Id, expectation: IExpectation) -> IExpectation | None:
        found = self._find_case(case_id)
        if found is None:
            return None
        suite, index, case = found
        rebuilt = _build_case(case.title, case.prompt, case.variables, [*case.expectations, expectation], id=case.id)
        suite.tests[index] = rebuilt
        self.suites.save(suite)
        return rebuilt.expectations[-1]

    def update_expectation(self, expectation_id: Id, expectation: IExpectation) -> IExpectation | None:
        found = self._find_expectation(expectation_id)
        if found is None:
            return None
        suite, case_index, expectation_index = found
        case = suite.tests[case_index]
        # Replace one expectation, keeping its ID, in a copy of the list, then rebuild the test case.
        expectations = case.expectations.copy()
        expectations[expectation_index] = Expectation(expectation.name, expectation.evaluator_type,
                                                      expectation.threshold, expectation.options,
                                                      id=case.expectations[expectation_index].id)
        rebuilt = _build_case(case.title, case.prompt, case.variables, expectations, id=case.id)
        suite.tests[case_index] = rebuilt
        self.suites.save(suite)
        return rebuilt.expectations[expectation_index]

    # --- Lookups across suites ------------------------------------------------

    def _find_case(self, case_id: Id) -> tuple[ITestSuite, int, ITestCase] | None:
        """Return (suite, index of the case in the suite, case), or None."""
        for suite in self.suites.list():
            for index, case in enumerate(suite.tests):
                if str(case.id) == str(case_id):
                    return suite, index, case
        return None

    def _find_expectation(self, expectation_id: Id) -> tuple[ITestSuite, int, int] | None:
        """Return (suite, index of the case, index of the expectation in the case), or None."""
        for suite in self.suites.list():
            for case_index, case in enumerate(suite.tests):
                for index, expectation in enumerate(case.expectations):
                    if str(expectation.id) == str(expectation_id):
                        return suite, case_index, index
        return None


def _build_case(title: str, prompt: str, variables: Mapping[str, str] | None,
                expectations: list[IExpectation], id: UUID | None = None) -> ITestCase:
    """Build a test case with the Builder; it raises ValueError when a domain rule is broken."""
    builder = TestCaseBuilder().set_title(title).set_prompt(prompt).set_variables(dict(variables or {}))
    for expectation in expectations:
        builder.add_expectation(expectation)
    return builder.build(id=id)
