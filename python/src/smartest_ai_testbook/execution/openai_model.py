from typing import Mapping

from openai import OpenAIError

from smartest_ai_testbook.execution.model import Model, ModelProvider, fill_variables


class OpenAIModel(Model):
    provider_name = "openai"

    def __init__(self, client, model_name: str):
        self.client = client
        self.model_name = model_name

    async def generate_response(self, prompt: str, variables: Mapping[str, str]) -> str:
        prompt = fill_variables(prompt, variables)
        try:
            response = await self.client.responses.create(model=self.model_name, input=prompt)
        except OpenAIError:
            raise RuntimeError("OpenAI request failed.") from None
        if response.status != "completed" or not isinstance(response.output_text, str) or not response.output_text:
            raise ValueError("OpenAI returned an incomplete or empty response.")
        return response.output_text


class OpenAIProvider(ModelProvider):
    provider_name = "openai"

    def __init__(self, client):
        self.client = client

    def get_model(self, model_name: str) -> Model:
        return OpenAIModel(self.client, model_name)
