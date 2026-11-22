# Proposal

## Why

The current Python application can execute a small in-memory example, but users cannot yet manage persistent tests and review real model runs through the web application. This change delivers a teachable end-to-end MVP while keeping the domain usable independently of HTTP and storage technologies.

## What Changes

- Complete Python test creation, execution, evaluator strategies, reporting and persistent run history.
- Store definitions and recorded outcomes in SQLite through SQLAlchemy, separated from the domain and optional web server.
- Implement the operations in `api/openapi.yaml` in the Python backend and connect a minimal React UI without a component library.
- Allow expectations to be supplied when a test is created and returned with assigned identifiers.
- Compose dependencies outside the domain and web server where needed.
- Keep JSON export in the long-term requirements, outside this change. TypeScript backend parity is deferred; shared specifications describe the target behavior and progress remains explicit.

## Capabilities

### New Capabilities

- `test-management`: Create, edit, remove and retrieve suites, tests and expectations.
- `suite-execution`: Run configured tests against a selected model and record individual evaluation outcomes.
- `persistent-storage`: Preserve definitions and execution history across application restarts.
- `mvp-web-workflow`: Use the shared web application to manage tests, start runs and review results through the Python backend.

### Modified Capabilities

None. Existing reporting requirements continue to apply and will be implemented in Python; existing web-access requirements remain the shared target, with TypeScript parity deferred.

## Impact

Python domain, storage, composition and FastAPI code; the shared React client; `api/openapi.yaml` and generated transport artifacts; Python dependency configuration and project documentation. OpenAI API access with environment configuration is the planning default, not a user-selected provider. The model is configurable.
