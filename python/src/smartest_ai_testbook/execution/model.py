import re
from typing import Mapping, Protocol


class Model(Protocol):
    provider_name: str
    model_name: str

    async def generate_response(self, prompt: str, variables: Mapping[str, str]) -> str: ...


class ModelProvider(Protocol):
    provider_name: str

    def get_model(self, model_name: str) -> Model: ...


def fill_variables(prompt: str, variables: Mapping[str, str]) -> str:
    """Replace each {{name}} placeholder with its variable; unknown placeholders stay unchanged."""
    return re.sub(r"\{\{\s*([^{}]+?)\s*\}\}", lambda match: variables.get(match[1], match[0]), prompt)
