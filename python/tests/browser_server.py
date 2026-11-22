"""Start an isolated backend with a deterministic model for browser verification."""

import json
import os
from types import SimpleNamespace

import uvicorn

from smartest_ai_testbook.composition import create_dependencies
from smartest_ai_testbook.web_server.app import create_app


async def create_response(**request):
    output = json.dumps({"score": 1, "feedback": "Criterion satisfied."}) if "text" in request else "Paris"
    return SimpleNamespace(status="completed", output_text=output)


async def create_embeddings(**request):
    return SimpleNamespace(data=[SimpleNamespace(index=index, embedding=[1.0, 0.0])
                                 for index, _ in enumerate(request["input"])])


if __name__ == "__main__":
    os.environ["WEB_ORIGIN"] = "http://127.0.0.1:5174"
    database_url = os.environ["BROWSER_TEST_DATABASE_URL"]
    client = SimpleNamespace(responses=SimpleNamespace(create=create_response),
                             embeddings=SimpleNamespace(create=create_embeddings))
    dependencies = create_dependencies(database_url, client=client)
    uvicorn.run(create_app(dependencies), host="127.0.0.1", port=3019)
