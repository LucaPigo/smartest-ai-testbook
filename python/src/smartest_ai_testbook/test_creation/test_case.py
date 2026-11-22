from typing import Protocol, Self
from uuid import UUID, uuid4

from smartest_ai_testbook.test_creation.expectation import Expectation, IExpectation, validate_expectation


class ITestCase(Protocol):
    id: UUID
    title: str
    prompt: str
    variables: dict[str, str]
    expectations: list[IExpectation]


class ITestCaseBuilder(Protocol):
    def set_title(self, title: str) -> Self: ...
    def set_prompt(self, prompt: str) -> Self: ...
    def set_variables(self, variables: dict[str, str]) -> Self: ...
    def add_expectation(self, expectation: IExpectation) -> Self: ...
    def build(self, id: UUID | None = None) -> ITestCase: ...


class TestCase(ITestCase):
    def __init__(self, prompt: str, variables: dict[str, str], expectations: list[IExpectation],
                 id: UUID | None = None, *, title: str):
        self.id = id if id is not None else uuid4()
        self.title = title
        self.prompt = prompt
        self.variables = variables
        self.expectations = expectations


class TestCaseBuilder(ITestCaseBuilder):
    def __init__(self):
        self.title: str | None = None
        self.prompt: str | None = None
        self.variables: dict[str, str] = {}
        self.expectations: list[IExpectation] = []

    def set_title(self, title: str) -> Self:
        self.title = title
        return self

    def set_prompt(self, prompt: str) -> Self:
        self.prompt = prompt
        return self

    def set_variables(self, variables: dict[str, str]) -> Self:
        self.variables = variables
        return self

    def add_expectation(self, expectation: IExpectation) -> Self:
        self.expectations.append(expectation)
        return self

    def build(self, id: UUID | None = None) -> TestCase:
        if not self.title or not self.title.strip():
            raise ValueError("Title must be set.")
        if not self.prompt or not self.prompt.strip():
            raise ValueError("Prompt must be set.")
        if not self.expectations:
            raise ValueError("At least one expectation is required.")
        for expectation in self.expectations:
            validate_expectation(expectation)
        expectations = [Expectation(e.name, e.evaluator_type, e.threshold, e.options.copy(), id=e.id)
                        for e in self.expectations]
        return TestCase(self.prompt, self.variables.copy(), expectations, id=id, title=self.title)
