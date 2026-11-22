# Python implementation

Run the following commands from this directory. Python 3.12 or later and [uv](https://docs.astral.sh/uv/) are required.

Install the project and its development dependencies:

```sh
uv sync --locked
```

Start the API server:

```sh
uv run python -m smartest_ai_testbook
```

The server listens on port `3002` by default. Set the `PORT` environment variable to use another port.

For development with live reload, run `npm run server:python` from the repository root.

Set `DATABASE_URL` to a SQLAlchemy SQLite URL to change the database location (default: `sqlite:///smartest-ai-testbook.db`). The database tables are created on first use. Set `OPENAI_API_KEY` in the backend environment to enable OpenAI execution. `OPENAI_EMBEDDING_MODEL` and `OPENAI_JUDGE_MODEL` select the evaluation models; their defaults are `text-embedding-3-small` and `gpt-4o-mini`. The model under test is selected in the interface. Never put credentials in the web client.

Tests contain ID, title, prompt, variables and expectations. Exact-match and semantic-similarity checks own an `options.expected` string; each judge check owns an `options.rubric` string. Scores and thresholds use 0–1, and exact-match threshold is fixed to 1. The runner generates once per test, evaluates every check sequentially and alone determines pass/fail. Existing SQLite definitions with shared criteria remain readable and use the new form on their next normal save; stored run history is preserved.

To use the React interface, install and build it from `../web-client`, set its public runtime configuration to `http://localhost:3002`, and start its static server:

```sh
npm ci
npm run build
npm start
```

Set `WEB_ORIGIN` on the backend if the browser uses an origin other than `http://localhost:3000`. The domain and SQLite repositories can also be composed with `create_dependencies` without starting the HTTP server.

Run the tests:

```sh
uv run pytest tests -v

# or, from root: 

uv run --project python pytest -v
```

`uv run` synchronizes the environment before running a command.

The TypeScript domain implements the same configuration, evaluators and execution policy; its HTTP server remains health-only and its persistence workflow is deferred. JSON export also remains future work. Tests use fake provider responses. A live OpenAI smoke test on 2026-11-18 reached the API but authentication failed; live execution remains unverified until valid credentials and model access are configured.
