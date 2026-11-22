import asyncio
import subprocess
import sys

from smartest_ai_testbook.composition import create_dependencies
from smartest_ai_testbook.test_creation.expectation import Expectation
from smartest_ai_testbook.test_creation.test_case import TestCaseBuilder
from smartest_ai_testbook.test_creation.test_suite import TestSuite


class FakeModel:
    provider_name = "fake"
    model_name = "fake-model"

    async def generate_response(self, prompt, variables):
        return "Paris"


def test_compose_run_and_read_without_the_web_server(tmp_path):
    url = f"sqlite:///{(tmp_path / 'composition.db').as_posix()}"
    dependencies = create_dependencies(url)
    suite = TestSuite("Suite", "Description")
    suite.add_test(TestCaseBuilder().set_title("Test").set_prompt("Question")
                   .add_expectation(Expectation("Exact", "exactMatch", 1, {"expected": "Paris"})).build())
    dependencies.suites.save(suite)
    run = asyncio.run(dependencies.runner.run(dependencies.suites.get(suite.id), FakeModel()))
    dependencies.runs.save(run)
    assert create_dependencies(url).runs.get(run.id).results[0].passed
    subprocess.run([sys.executable, "-c", "import sys; import smartest_ai_testbook.composition; "
                    "assert not any(m == 'fastapi' or m.startswith('fastapi.') for m in sys.modules); "
                    "assert 'smartest_ai_testbook.web_server.app' not in sys.modules"], check=True)
