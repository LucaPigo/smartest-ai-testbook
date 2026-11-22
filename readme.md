# Smartest AI Testbook

> Domain modeling and object-oriented design for an MVP that evaluates LLM-generated responses.
> Loosely inspired by [yTestbook](https://ytestbook.intesys.it/)

## Scenario

A team is building an application powered by a language model. Responses can vary, and checking only that the program does not crash is not enough: the team needs test examples, a way to run them against a model, and explicit evaluation criteria.

**Problem to explore:** how can response quality be made observable and measurable?

Formulate the application's **core value** before proposing components or features. A suite, run, and report are useful only if they help achieve that value.

## MVP scope

Users create and edit a test suite, run it against an LLM provider, and review outputs and their evaluations. The system persists the data. JSON export remains a requirement for a later implementation.

Tests have stable identities and can be edited, but the system does not version their complete contents. Historical results retain the original prompt template, test ID, output or error, and recorded evaluation details; they are not complete snapshots of the test definition.

A test contains ID, title, prompt, optional variables and expectations. Each check owns its criteria: `options.expected` for exact match and semantic similarity, or `options.rubric` for an LLM judge. The interface shows the corresponding field directly. All scores use 0–1; exact match compares strings literally with threshold fixed to 1. Each run selects one model, generates once per test, and evaluates all expectations sequentially. The runner alone applies thresholds; a test passes when generation and every expectation pass.

Do not design dashboards, login, distributed queues, live reports, CI/CD, CLI, concurrency, or retry strategies: they are unnecessary to demonstrate the MVP's core value.

## Work for the two practical sessions

### Part 1 — Understand the domain

- Start from the typical user's tasks (Prompt / AI Engineer): define tests, start a run, and interpret results; identify needs and where the interface should help.
- Identify the problem and formulate the core value.
- Identify the actor, use cases, persisted data, and main flow.
- Analyze which information the run report needs to contain.
- Sketch a low-fidelity wireframe of the main flow and conduct a brief peer UX review.
- Draw the conceptual domain model and discuss its relationships.

### Part 2 — Design classes and interfaces

- Turn the domain model into classes and responsibilities.
- Define the runner interface and its boundary with the provider.
- Derive Strategy from interchangeable evaluators.
- Derive Adapter from the need to isolate provider APIs.
- Explain design choices and leave out details that are unnecessary for the MVP.

### Wireframe and UX review

The wireframe checks whether the user flow is understandable and whether domain and report data appear when needed. A sketch of the main screens is enough: manage suites and tests, start a run, and review its report. A polished UI or visual design is not required.

Check that the next step, required input, score scale and outcome, and provider errors are clear. Every wireframe element must correspond to a use case or MVP requirement; do not add features just to fill a screen.

## Materials

- [requirements.md](./doc/requirements.md): MVP requirements and boundaries;
- [test-case-examples.md](./doc/test-case-examples.md): tests, evaluators, and a sample report.
- [glossary.md](./doc/glossary.md): definitions of the project's main terms.

## Run the Python application

Specifications in `openspec/` and documents in `doc/` are shared. Implementations and their dependencies are in `typescript/` and `python/`.

The Python backend implements suite and test management, execution and recorded
results using SQLite and SQLAlchemy. Its optional FastAPI server exposes the
contract in [openapi.yaml](./api/openapi.yaml), and the React client provides a
minimal workflow for creating tests, running them and reviewing results. The
domain and persistence can also be composed without starting the server.

Both languages implement the same test configuration and execution behavior,
including all three evaluation strategies. The TypeScript HTTP backend currently
provides only `GET /health`; its HTTP and persistence parity with the Python
application is deferred. Generated transport types do not imply endpoint
implementation. JSON export is also deferred.

Use Node 24.22.1 and Python 3.12 or later with uv. In separate terminals:

1. In `python/`, run `uv sync --locked`, then
   `uv run --no-sync python -m smartest_ai_testbook` to start the API on port 3002.
2. In `web-client/`, run `npm ci` and `npm run dev` (or `npm run client:web` from the repository root).

Open `http://localhost:3000`. The client imports the static `configuration.js`
module at runtime. The development server serves `web-client/public/configuration.js`
directly; its current API address is `http://localhost:3002`. Edit that file and
reload to switch backends. Vite updates the interface during development without
rebuilding. To preview a production build, run `npm run build` and `npm start`
in `web-client/`; preview serves the copied `web-client/dist/configuration.js`.
The server accepts browser requests from `http://localhost:3000` by default;
set `WEB_ORIGIN` for another origin. Set `OPENAI_API_KEY` in the Python backend
environment to run a real model, and select the model in the interface.
`OPENAI_EMBEDDING_MODEL` and `OPENAI_JUDGE_MODEL` configure the evaluator models.
The default SQLite database is `smartest-ai-testbook.db` in the server's working
directory; set `DATABASE_URL` to use another SQLite URL. Runtime client
configuration is public and must contain no secrets.

See [python/readme.md](./python/readme.md) for Python configuration,
[web-architecture.md](./doc/web-architecture.md) for the component layout, and
[api-generation.md](./doc/api-generation.md) for generator versions, ownership
and safe regeneration.

## Verification and generation

- At the repository root, `npm ci` installs OpenSpec and generation/browser tooling;
  `npx openspec validate --all` validates specifications.
- In `typescript/`, `npm test` runs the available tests and `npm run typecheck` checks types.
- In `python/`, after `uv sync --locked`,
  `uv run --no-sync pytest tests -v` runs domain, persistence and HTTP tests.
- In `web-client/`, `npm run build` checks types and builds the React client.
- At the root (Java 21 required), `npm run api:server-node`, `npm run api:server-python`
  and `npm run api:client-web` regenerate the artifacts of each application; review the
  result with `git diff`.
- With both implementations installed and the client built, `npm run verify:http`
  starts both servers and applies shared HTTP checks. `npm run verify:browser`
  also uses installed Chrome to check the same client build with both backends,
  configuration failures, connection failures and browser origin handling.
  These checks do not verify real OpenAI model access.

## Containers

Compose builds complete server images; it does not mount the host's `.venv` or
`node_modules` into containers. With Docker running, start the TypeScript API and
static client using `docker compose up --build typescript web-client`.
Nginx serves the client and mounts `web-client/public/configuration.js` read-only.
To use Python, change `apiBaseUrl` to `http://localhost:3002` in that file, start
`docker compose up --build python web-client`, and reload the page. Further URL
changes require no rebuild or container restart.
The API URL is a browser address; use `localhost`, rather than a Compose service
name, when opening the app locally. The two APIs can also run together. The current
Compose configuration does not mount a persistent database volume or pass OpenAI
credentials to the Python service; configure these explicitly when needed.

Shared specifications target both languages and their domain implementations
follow the same model. The Python application additionally provides the persisted
HTTP workflow; the TypeScript HTTP server remains limited to health connectivity.
