import math
from typing import Protocol
from uuid import UUID, uuid4


class IExpectation(Protocol):
    id: UUID
    name: str
    evaluator_type: str
    threshold: float
    options: dict


class Expectation(IExpectation):
    def __init__(self, name: str, evaluator_type: str, threshold: float, options: dict, id: UUID | None = None):
        self.id = id if id is not None else uuid4()
        self.name = name
        self.evaluator_type = evaluator_type
        self.threshold = threshold
        self.options = options


def validate_expectation(expectation: IExpectation) -> str:
    if not isinstance(expectation.name, str) or not expectation.name.strip():
        raise ValueError("An expectation needs a name.")
    if expectation.evaluator_type not in ("exactMatch", "semanticSimilarity", "llmJudge"):
        raise ValueError(f"Unknown evaluator type: {expectation.evaluator_type}")
    threshold = expectation.threshold
    if (isinstance(threshold, bool) or not isinstance(threshold, (int, float))
            or not math.isfinite(threshold) or not 0 <= threshold <= 1):
        raise ValueError("An expectation threshold must be a finite number from 0 to 1.")
    if expectation.evaluator_type == "exactMatch" and threshold != 1:
        raise ValueError("Exact match requires threshold 1.")
    key = "rubric" if expectation.evaluator_type == "llmJudge" else "expected"
    options = expectation.options
    if (not isinstance(options, dict) or set(options) != {key}
            or not isinstance(options[key], str) or not options[key].strip()):
        raise ValueError(f"{expectation.evaluator_type} options must contain only a nonblank {key} string.")
    return options[key]
