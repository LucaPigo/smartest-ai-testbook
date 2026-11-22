import json
from uuid import uuid4

from fastapi.testclient import TestClient

from smartest_ai_testbook.composition import create_dependencies
from smartest_ai_testbook.web_server.app import create_app


class Model:
    provider_name = "openai"
    model_name = "fake-model"

    async def generate_response(self, prompt, variables):
        return variables.get("city", "Paris")


class Provider:
    def get_model(self, model_name):
        assert model_name == "fake-model"
        return Model()


def make_client(database_url):
    dependencies = create_dependencies(database_url)
    dependencies.provider = Provider()
    return TestClient(create_app(dependencies))


def test_http_workflow_persists_snapshots_and_checks_boundaries(tmp_path):
    url = f"sqlite:///{(tmp_path / 'application.db').as_posix()}"
    expectation = {"name": "Exact", "evaluator_type": "exactMatch", "threshold": 1, "options": {"expected": "Paris"}}
    with make_client(url) as client:
        assert client.post("/api/test-suites", json={"name": "", "description": ""}).status_code == 422
        suite = client.post("/api/test-suites", json={"name": "Suite", "description": "First"}).json()
        suite_id = suite["id"]
        assert client.put(f"/api/test-suites/{suite_id}", json={"name": "Edited", "description": "Second"}).json()["id"] == suite_id
        payload = {"suite_id": suite_id, "title": "Capital", "prompt": "{{city}}",
                   "variables": {"city": "Paris"}, "expectations": [expectation]}
        invalid = {**payload, "expectations": [{**expectation, "options": {}}]}
        assert client.post("/api/test-cases", json={**payload, "title": ""}).status_code == 422
        assert client.post("/api/test-cases", json={**payload, "title": "   "}).status_code == 422
        assert client.post("/api/test-cases", json={key: value for key, value in payload.items() if key != "title"}).status_code == 422
        assert client.post("/api/test-cases", json=invalid).status_code == 422
        assert client.get(f"/api/test-suites/{suite_id}/test-cases").json() == []
        response = client.post("/api/test-cases", json=payload)
        assert response.status_code == 201
        case = response.json()
        assert case["title"] == "Capital"
        assert set(case) == {"id", "title", "prompt", "variables", "expectations"}
        case_id, expectation_id = case["id"], case["expectations"][0]["id"]
        run_response = client.post(f"/api/test-suites/{suite_id}/eval-runs",
                                   json={"provider_name": "openai", "model_name": "fake-model"})
        assert run_response.status_code == 201
        run = run_response.json()
        assert run["results"][0]["passed"] is True
        assert run["results"][0]["scores"][0]["expectation_id"] == expectation_id
        update = {key: case[key] for key in ("title", "prompt", "variables", "expectations")}
        update["title"] = "Edited title"
        update["prompt"] = "Changed"
        updated = client.put(f"/api/test-cases/{case_id}", json=update)
        assert updated.status_code == 200
        assert updated.json()["title"] == "Edited title"
        assert updated.json()["expectations"][0]["id"] == expectation_id
        update["expectations"][0]["id"] = str(uuid4())
        assert client.put(f"/api/test-cases/{case_id}", json=update).status_code == 422
        preflight = client.options("/api/test-cases", headers={"Origin": "http://localhost:3000",
                                   "Access-Control-Request-Method": "POST",
                                   "Access-Control-Request-Headers": "content-type"})
        assert preflight.status_code == 200

    with make_client(url) as client:
        assert client.get(f"/api/test-cases/{case_id}").json()["prompt"] == "Changed"
        assert client.get(f"/api/test-cases/{case_id}").json()["title"] == "Edited title"
        assert client.get(f"/api/eval-runs/{run['id']}").json()["results"][0]["prompt"] == "{{city}}"
        assert len(client.get(f"/api/test-suites/{suite_id}/eval-runs").json()) == 1
        assert client.delete(f"/api/test-suites/{suite_id}").status_code == 204
        assert client.get(f"/api/eval-runs/{run['id']}").status_code == 404


def test_expectation_endpoints_validate_and_preserve_ids(tmp_path):
    url = f"sqlite:///{(tmp_path / 'expectations.db').as_posix()}"
    expectation = {"name": "Exact", "evaluator_type": "exactMatch", "threshold": 1, "options": {"expected": "Paris"}}
    with make_client(url) as client:
        suite_id = client.post("/api/test-suites", json={"name": "Suite", "description": ""}).json()["id"]
        case = client.post("/api/test-cases", json={"suite_id": suite_id, "title": "Test", "prompt": "Question",
                           "expectations": [expectation]}).json()
        case_id = case["id"]
        assert case["variables"] == {}
        missing_rubric = {"name": "Judge", "evaluator_type": "llmJudge", "threshold": 0.5, "options": {}}
        assert client.post("/api/expectations", json={**missing_rubric, "test_case_id": case_id}).status_code == 422
        assert len(client.get(f"/api/test-cases/{case_id}/expectations").json()) == 1
        created = client.post("/api/expectations", json={**expectation, "test_case_id": case_id})
        assert created.status_code == 201
        expectation_id = created.json()["id"]
        assert client.put(f"/api/expectations/{expectation_id}", json=missing_rubric).status_code == 422
        assert client.put(f"/api/expectations/{expectation_id}", json={**expectation, "name": "Updated"}).json()["id"] == expectation_id
        assert client.delete(f"/api/test-cases/{case_id}").status_code == 204
        assert client.get(f"/api/test-cases/{case_id}").status_code == 404


def test_nonfinite_expectation_input_is_rejected_without_partial_writes(tmp_path):
    url = f"sqlite:///{(tmp_path / 'nonfinite.db').as_posix()}"
    expectation = {"name": "Exact", "evaluator_type": "exactMatch", "threshold": 1, "options": {"expected": "Paris"}}
    with make_client(url) as client:
        suite_id = client.post("/api/test-suites", json={"name": "Suite", "description": ""}).json()["id"]
        payload = {"suite_id": suite_id, "title": "Test", "prompt": "Question",
                   "variables": {}, "expectations": [expectation]}
        headers = {"Content-Type": "application/json"}
        for number in ("1e999", "NaN", "Infinity", "-Infinity"):
            invalid_threshold = json.dumps(payload).replace('"threshold": 1', f'"threshold": {number}')
            assert client.post("/api/test-cases", content=invalid_threshold, headers=headers).status_code == 422
        assert client.get(f"/api/test-suites/{suite_id}/test-cases").json() == []

        case = client.post("/api/test-cases", json=payload).json()
        case_id, expectation_id = case["id"], case["expectations"][0]["id"]
        invalid_options = {**expectation, "options": {"nested": ["overflow"]}, "test_case_id": case_id}
        body = json.dumps(invalid_options).replace('"overflow"', '1e999')
        assert client.post("/api/expectations", content=body, headers=headers).status_code == 422
        assert len(client.get(f"/api/test-cases/{case_id}/expectations").json()) == 1
        invalid_update = json.dumps(expectation).replace('"threshold": 1', '"threshold": 1e999')
        assert client.put(f"/api/expectations/{expectation_id}", content=invalid_update, headers=headers).status_code == 422
        assert client.get(f"/api/test-cases/{case_id}").json() == case


def test_suite_description_is_optional(tmp_path):
    with make_client(f"sqlite:///{tmp_path / 'optional.db'}") as client:
        suite = client.post("/api/test-suites", json={"name": "Suite"})
        assert suite.status_code == 201
        assert suite.json()["description"] == ""
