# Web architecture

The shared HTTP contract is [`api/openapi.yaml`](../api/openapi.yaml). The Python
backend implements its suite, test, expectation and evaluation-run operations,
as well as `GET /health`. The TypeScript backend currently implements only
`GET /health`; TypeScript HTTP and persistence parity is deferred. Both domain
implementations support the same test configuration, three evaluator strategies
and execution policy. The separate
`openapi.domain.yaml` is a school exercise, not the HTTP implementation contract.
JSON export is also deferred.

`GET /health` returns HTTP 200 with `{"status":"ok"}`. It checks connectivity,
not persistence, model access or evaluation readiness.

## Python backend

- [`__main__.py`](../python/src/smartest_ai_testbook/__main__.py) starts Uvicorn.
- [`web_server/app.py`](../python/src/smartest_ai_testbook/web_server/app.py)
  translates HTTP requests to domain operations and uses generated request models.
- [`composition.py`](../python/src/smartest_ai_testbook/composition.py) composes the
  repositories, runner, provider and evaluators without importing FastAPI.
- [`persistence/sqlite.py`](../python/src/smartest_ai_testbook/persistence/sqlite.py)
  implements the repository contracts using SQLAlchemy and SQLite. The domain
  does not import SQLAlchemy or the web server.
- [`web_server/generated/models/`](../python/src/smartest_ai_testbook/web_server/generated/models/)
  contains transport models, not domain entities.

Suite definitions and completed runs are saved separately. Editing or deleting a
test does not change its recorded run results; deleting a suite also deletes its
run history. The web server is optional: callers can use the dependencies composed
by `create_dependencies` without starting HTTP.

Definitions store reference answers in each exact or semantic expectation's
`options.expected`, and judge criteria in each judge expectation's `options.rubric`.
The loader also reads older rows with shared test-level criteria, copying them
into matching expectations only when the local option is absent. Local criteria
take precedence. Reads do not rewrite rows; the next normal save writes the new
shape. Existing run rows and recorded outcomes are preserved.

From `python/`, using Python 3.12 or later and uv:

```sh
uv sync --locked
uv run --no-sync python -m smartest_ai_testbook
uv run --no-sync pytest tests -v
```

The server binds to `0.0.0.0` on port 3002 by default. `PORT` changes the port;
`WEB_ORIGIN` sets the permitted browser origin and defaults to
`http://localhost:3000`. `DATABASE_URL` is a SQLAlchemy SQLite URL and defaults
to `sqlite:///smartest-ai-testbook.db`; tables are created on first use.

Set `OPENAI_API_KEY` in the backend environment to enable OpenAI execution.
`OPENAI_EMBEDDING_MODEL` and `OPENAI_JUDGE_MODEL` select evaluator models and
default to `text-embedding-3-small` and `gpt-4o-mini`. The user selects the model
under test in the interface. Tests can inject a fake provider; real model access
requires separately configured credentials and model access. Never put the key
in browser-delivered configuration.

An AI service is used at two points: the system under test during a run, and the
AI evaluation service for semantic-similarity and LLM-judge expectations (see
[domain design](./domain-design.md#ai-integration-points)). Set `AI_MODE=mock` to
replace both with deterministic offline mocks at startup; no OpenAI key is needed
or used. The mock provider is named `mock`, its model answers `[mock] ` followed
by the filled prompt, and the AI expectations receive score 1 with feedback
`Mock evaluation`; exact match stays real. A run is accepted only when its
requested provider matches the configured one: `openai` in default mode with a
key, `mock` in mock mode. Otherwise the server answers 422. The run page offers
the `OpenAI` and `Mock` providers.

## TypeScript backend

[`typescript/src/index.ts`](../typescript/src/index.ts) starts the Express app;
[`web-server/app.ts`](../typescript/src/web-server/app.ts) provides health and
CORS. The default port is 3001; `PORT` and `WEB_ORIGIN` configure the port and
allowed browser origin. Generated TypeScript transport types describe the shared
contract but do not imply implementation of its other routes. The TypeScript
domain provides the same mock provider, model and evaluator as Python, but has no
composition module or `AI_MODE` handling, because its HTTP server does not run suites.

From `typescript/`:

```sh
npm ci
npm test
npm run typecheck
npm run dev
```

## Shared React client

[`web-client/src/main.tsx`](../web-client/src/main.tsx) and
[`TestForm.tsx`](../web-client/src/TestForm.tsx) implement a minimal interface
using native HTML controls and the generated Fetch client. The interface manages
suites and tests, configures expectations, submits runs and displays recorded
results and errors. A health check uses a five-second timeout. Connecting to the
TypeScript backend can establish health connectivity, but its missing application
routes cannot support the Python workflow.

Each expectation uses native controls for its name, evaluator type and required
criterion: an expected-answer field for exact match and semantic similarity, or
a rubric field for an LLM judge. There are no test-wide criteria or JSON options
editors. Exact-match threshold is fixed to 1; the other thresholds are editable
within 0–1. Changing type submits only that type's criterion. Variables are optional.
The user chooses the model under test once per run; evaluator models are configured
in the backend environment. The runner generates once per test, evaluates the
same response against all checks in order, and applies all thresholds.

The client uses declarative React Router routes with separate pages for the suite
list (`/test-suites`), suite creation (`/test-suites/new`), suite definition
(`/test-suites/<suite-id>`), test editing (`/test-cases/<case-id>`), the execute page
with report list and play control (`/execute/<suite-id>`), run configuration
(`/execute/<suite-id>/run`) and report detail (`/reports/<run-id>`). New tests use `/test-suites/<suite-id>/test-cases/new`. The
suite index contains no form, and the suite creation page reuses the suite edit form.
Test and expectation management share one page. Pages follow `doc/ui.excalidraw`;
provider and model are configured on the run configuration page when a run starts, not on the suite page.
`BrowserRouter` uses normal browser history. Vite provides SPA fallback locally;
the Nginx configuration serves `index.html` for application routes so direct links
and reloads also work in the container.

[`web-client/public/configuration.js`](../web-client/public/configuration.js) is
a public runtime module containing only the browser-accessible API address:

```js
export const apiBaseUrl = 'http://localhost:3002';
```

The application loads it at runtime from the site's root. The Vite development
server serves `public/configuration.js` directly and provides live updates.
From `web-client/`:

```sh
npm ci
npm run dev
```

Open `http://localhost:3000`, or use `npm run client:web` from the repository root.
Edit `public/configuration.js` and reload to select another backend.
For production preview, run `npm run build` and `npm start`: Vite copies the module
to `dist/configuration.js` during the build, and preview serves that copy.
Set `WEB_ORIGIN` to the exact browser origin; an HTTPS page requires an
HTTPS API address to avoid mixed content.

## Contract generation and verification

From the repository root, `npm run api:server-node`, `npm run api:server-python` and
`npm run api:client-web` generate the TypeScript backend types, the Python transport
models and the React Fetch client. Root dependencies are installed with `npm ci`; Java is
required for OpenAPI Generator. Generated files should be changed through the
contract and generator, not by hand.

Python's tests include domain, persistence and HTTP workflow tests with fake model
responses. `api/scripts/verify-web.mjs` checks shared health and origin behavior;
its browser mode also exercises runtime configuration. The React workflow test
uses a fake API. These checks have different scopes: health checks do not prove
that the application routes or a real OpenAI model work. Run the relevant tests
against the current checkout before reporting their results.

Verification on 2026-11-18: all 38 Python tests passed, generated artifacts
matched the contract, and the React build passed. Browser tests covered the UI
with a fake API and the FastAPI/SQLite workflow with a fake model, including a
database restart. Shared health and runtime-configuration browser checks passed.
A live OpenAI request reached the service but authentication failed, so real
model execution remains unverified. Pytest reported collection and dependency
deprecation warnings.

## Containers

[`compose.yaml`](../compose.yaml) defines independent TypeScript, Python and
static-client services. The client configuration module is mounted read-only,
so changing its API address and reloading the browser switches the destination
without rebuilding the client image. The configured address selects port 3002
for the Python workflow. The current Compose configuration does
not mount a persistent database volume or pass OpenAI credentials to Python;
configure these explicitly when needed. Container behavior must be verified
against the current images and configuration.
