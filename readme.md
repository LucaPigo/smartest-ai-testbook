# Smartest AI Testbook

> Domain modeling and object-oriented design for an MVP that evaluates LLM-generated responses.
> Loosely inspired by [yTestbook](https://ytestbook.intesys.it/).

A school exercise in software engineering: a small web application to **test AI language
models** the way unit tests check ordinary code. Users write test suites, run them against
a model and review how each answer was evaluated.

- [1. The project in brief](#1-the-project-in-brief)
- [2. Run the project in development](#2-run-the-project-in-development)
- [3. Tests and checks](#3-tests-and-checks)
- [4. Study the project](#4-study-the-project)
- [5. Course activities](#5-course-activities)

## 1. The project in brief

### Problem and core value

LLM answers vary from one call to the next, so checking that the program does not crash is
not enough. **Core value:** turn variable LLM outputs into measurable, reviewable results.

### What the MVP does

1. **Define** a test suite: test cases with a prompt, optional variables and one or more
   expectations (exact match, semantic similarity, LLM judge), each with a 0–1 threshold.
2. **Execute** the suite against one model: one answer per test, every expectation evaluated.
3. **Report** the results: output or error, score and outcome of every expectation; a test
   passes only when all its expectations pass.

Data is stored in SQLite. Out of scope: dashboards, login, queues, live reports, CI/CD, CLI,
concurrency, retries. JSON export is a requirement for a later implementation.

### Repository map

| Folder | Contents |
|---|---|
| [`doc/`](./doc/) | Shared documentation: requirements, glossary, domain design, wireframe, architecture. |
| [`api/`](./api/) | The OpenAPI contract shared by client and backends, and its lesson in `api/doc/`. |
| [`python/`](./python/) | **Complete backend**: domain, SQLite persistence, FastAPI server, tests, lesson in `python/doc/`. |
| [`typescript/`](./typescript/) | The same domain in TypeScript; its HTTP server provides only `GET /health`. |
| [`web-client/`](./web-client/) | React client used with the Python backend. |
| [`openspec/`](./openspec/) | Specifications (`specs/`) and the history of implemented changes (`changes/archive/`). |

## 2. Run the project in development

### Prerequisites

| Tool | Version | Needed for |
|---|---|---|
| Node.js | 24.22.1 | web client, TypeScript, root tooling |
| Python + [uv](https://docs.astral.sh/uv/) | Python 3.12 or later | Python backend |
| Java | 21 | only to regenerate code from the API contract |
| Docker | any recent | only to run the containers |

### First run, step by step

From the repository root:

```sh
# 1. Install dependencies
(cd python && uv sync --locked)
(cd web-client && npm ci)
npm ci                          # optional: OpenSpec, code generators, browser checks

# 2. Create the backend configuration (not versioned)
cp .env.example .env            # PowerShell: Copy-Item .env.example .env

# 3. Start the backend (terminal 1): http://localhost:3002, live reload, reads .env
npm run server:python

# 4. Start the client (terminal 2): http://localhost:3000
npm run client:web
```

Open `http://localhost:3000`, create a suite and a test, then go to **Execute**, press ▶,
choose the **Mock** provider, type any model name and start the run.

### Mock mode and real models

An AI service is used at two points: the **model under test** during a run, and the **AI
evaluators** (semantic similarity and LLM judge). The `.env` template sets `AI_MODE=mock`,
which replaces both with offline mocks: no API key or cost, and the full flow still runs.
Mock answers are `[mock] ` plus the prompt, AI expectations score 1, exact match stays real.

To use OpenAI instead, edit `.env`, restart the backend and choose the **OpenAI** provider:

```sh
AI_MODE=
OPENAI_API_KEY=sk-...
```

The server accepts only the provider it was started with; the other one returns a 422 error.

### Configuration

Backend environment variables, read from `.env` by `npm run server:python`:

| Variable | Default | Purpose |
|---|---|---|
| `AI_MODE` | empty | `mock` replaces the model under test and the AI evaluators with mocks |
| `OPENAI_API_KEY` | none | enables the OpenAI provider and the AI evaluators |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | model used by semantic similarity |
| `OPENAI_JUDGE_MODEL` | `gpt-4o-mini` | model used by the LLM judge |
| `DATABASE_URL` | `sqlite:///smartest-ai-testbook.db` | SQLite database; tables are created on first use |
| `WEB_ORIGIN` | `http://localhost:3000` | browser origin allowed by CORS |

The client reads the backend address at run time from
[`web-client/public/configuration.js`](./web-client/public/configuration.js)
(`http://localhost:3002`). It is public: never put secrets in it.

### Other ways to run

| Goal | Command | Notes |
|---|---|---|
| Backend without npm | `cd python && uv run python -m smartest_ai_testbook` | does not read `.env`: set variables in the shell; `PORT` changes the port |
| Containers | `docker compose up --build python web-client` | Compose reads `AI_MODE` from `.env`; it does not pass OpenAI credentials or persist the database |
| TypeScript server | `npm run server:node` | port 3001, `GET /health` only |
| TypeScript domain example | `cd typescript && node --import tsx src/examples/run-suite.ts` | runs a suite with a constant demo model |
| Production build of the client | `cd web-client && npm run build && npm start` | serves `dist/` on port 3000 |

More details: [python/readme.md](./python/readme.md) and
[doc/web-architecture.md](./doc/web-architecture.md).

## 3. Tests and checks

| What | Where | Command |
|---|---|---|
| Python tests (domain, persistence, HTTP) | `python/` | `uv run pytest tests -v` |
| TypeScript tests and types | `typescript/` | `npm ci`, then `npm test` and `npm run typecheck` |
| Client types and build | `web-client/` | `npm run build` |
| Specifications | root | `npx openspec validate --all` |
| Shared HTTP checks on both servers | root | `npm run verify:http` |
| Browser checks (installed Chrome) | root | `npm run verify:browser` |
| Regenerate code from the contract (Java 21) | root | `npm run api:server-node`, `npm run api:server-python`, `npm run api:client-web`, then review with `git diff` |

All checks use fake or mock models: they do not prove that a real OpenAI model is reachable.

## 4. Study the project

### Suggested learning path

| # | Topic | Read |
|---|---|---|
| 1 | **The domain**: what the application must do and its vocabulary | [requirements.md](./doc/requirements.md), [glossary.md](./doc/glossary.md), [test-case-examples.md](./doc/test-case-examples.md) |
| 2 | **Domain design**: subsystems, classes, contracts, patterns, AI integration points | [domain-design.md](./doc/domain-design.md), [domain-class-diagram.excalidraw](./doc/domain-class-diagram.excalidraw) |
| 3 | **User interface**: screens and the API calls each one needs | [ui.excalidraw](./doc/ui.excalidraw) |
| 4 | **HTTP contract**: OpenAPI, UI-driven (BFF) design, code generation | [api/doc lesson](./api/doc/README.md) |
| 5 | **Python architecture**: domain independence, dependency injection, patterns, order of execution | [python/doc lesson](./python/doc/README.md) |
| 6 | **Libraries**: FastAPI and SQLAlchemy through the project's code | [Appendix A](./python/doc/07-fastapi.md), [Appendix B](./python/doc/08-sqlalchemy.md) |
| 7 | **System view**: servers, client, configuration, containers | [web-architecture.md](./doc/web-architecture.md) |
| 8 | **Specifications and decisions**: requirements as testable scenarios, and how each change was planned | [openspec/specs](./openspec/specs/), [openspec/changes/archive](./openspec/changes/archive/) |

Open `.excalidraw` files with [excalidraw.com](https://excalidraw.com/) or the Excalidraw
VS Code extension.

### Design strategies

| Strategy | Where | Explained in |
|---|---|---|
| Interfaces as public contracts (every class implements one) | both languages | [AGENTS.md](./AGENTS.md), [python/doc ch. 4](./python/doc/04-design-patterns.md) |
| Independent domain, dependencies pointing inwards | `python/src`, `typescript/src` | [python/doc ch. 1–2](./python/doc/01-architecture.md) |
| Dependency injection and a single composition root | `python/.../composition.py` | [python/doc ch. 3](./python/doc/03-dependency-injection.md) |
| **Builder** for valid test cases | `TestCaseBuilder` | [python/doc ch. 4](./python/doc/04-design-patterns.md#builder) |
| **Strategy** for interchangeable evaluators | `Evaluator` and its implementations | [python/doc ch. 4](./python/doc/04-design-patterns.md#strategy) |
| **Adapter** to isolate the AI provider | `OpenAIModel`, `MockModel` | [python/doc ch. 4](./python/doc/04-design-patterns.md#adapter) |
| **Repository** to hide the database | `SuiteRepository`, `RunRepository` | [python/doc ch. 4](./python/doc/04-design-patterns.md#repository) |
| Offline mocks of the AI services | `execution/mock_ai.py`, `mock-ai.ts` | [domain-design.md](./doc/domain-design.md#ai-integration-points) |
| Contract-first, UI-driven API (Backend for Frontend) | `api/openapi.yaml` | [api/doc ch. 3](./api/doc/03-api-design-bff.md) |
| Generated transport code, handwritten logic | `generated/` folders | [api/doc ch. 4](./api/doc/04-code-generation.md) |
| Spec-driven changes | `openspec/` | [openspec/changes/archive](./openspec/changes/archive/) |

### Technologies

| Area | Technologies |
|---|---|
| Python backend | Python 3.12, FastAPI 0.128, Pydantic, Uvicorn, SQLAlchemy 2, SQLite, pytest, uv |
| TypeScript domain and server | TypeScript 7, Node.js 24, Express 5, `node:test`, tsx |
| Web client | React 19, React Router 7, Vite 7, generated Fetch client |
| AI provider | OpenAI SDK (responses and embeddings), offline mocks |
| HTTP contract | OpenAPI 3.0.3, OpenAPI Generator 7.26 (`python-fastapi`, `typescript-fetch`), `openapi-typescript` |
| Specifications | OpenSpec |
| Tooling | Docker Compose, Nginx, Playwright |

The rules every implementation follows (English only, explicit interfaces, the same features
in both languages, minimal code) are in [AGENTS.md](./AGENTS.md).

## 5. Course activities

The project supports two practical sessions.

**Part 1 — Understand the domain**

- Start from the tasks of the typical user (Prompt / AI Engineer): define tests, start a run,
  interpret results; find where the interface should help.
- Identify the problem and formulate the core value before proposing features.
- Identify the actor, use cases, persisted data and main flow, and what a run report must contain.
- Sketch a low-fidelity wireframe of the main flow and run a short peer UX review.
- Draw the conceptual domain model and discuss its relationships.

**Part 2 — Design classes and interfaces**

- Turn the domain model into classes and responsibilities.
- Define the runner interface and its boundary with the provider.
- Derive Strategy from interchangeable evaluators and Adapter from the need to isolate provider APIs.
- Explain the design choices and leave out what the MVP does not need.

**Wireframe review checklist.** A sketch of the main screens is enough: manage suites and
tests, start a run, review its report. Check that the next step, the required input, the
score scale and outcome, and provider errors are clear. Every element must correspond to a
use case or MVP requirement.
