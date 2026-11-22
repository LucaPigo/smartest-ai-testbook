from typing import Protocol, Self
from uuid import UUID, uuid4

from smartest_ai_testbook.test_creation.test_case import ITestCase


class ITestSuite(Protocol):
    id: UUID
    name: str
    description: str
    tests: list[ITestCase]

    def add_test(self, test_case: ITestCase) -> Self: ...


class TestSuite(ITestSuite):
    def __init__(self, name: str, description: str = "", id: UUID | None = None):
        self.id = id if id is not None else uuid4()
        self.name = name
        self.description = description
        self.tests: list[ITestCase] = []

    def add_test(self, test_case: ITestCase) -> Self:
        self.tests.append(test_case)
        return self
