# API generation

For an introduction to OpenAPI, the UI-driven design of the contract and code
generation, read the [lesson in `api/doc/`](../api/doc/README.md). This page is the
operational reference.

`api/openapi.yaml` is the canonical HTTP contract. Generated transport code is
separate from handwritten server code and is committed to version control.
Change the contract and regenerate instead of editing generated artifacts.
Generated TypeScript transport definitions and the shared client do not imply
that the TypeScript backend implements the new domain endpoints.

Each application has one standard console command. Run them from the repository
root after `npm ci`. Java 21 is required by OpenAPI Generator; its version is
pinned in `openapitools.json` and the npm tools in `package.json`.

| Command | Output |
|---|---|
| `npm run api:server-node` | `typescript/src/web-server/generated/schema.ts` |
| `npm run api:server-python` | `python/src/smartest_ai_testbook/web_server/generated/` |
| `npm run api:client-web` | `web-client/src/generated/` |

After regenerating, review the changes with `git diff`: an unexpected difference
means the contract changed or a generated file was edited by hand.

## TypeScript server types

`openapi-typescript` generates the schema types. They supply the handwritten
health handler's return type; TypeScript declarations alone do not validate
network data at runtime.

## Python transport models

`python-fastapi` generates only the transport models, with the global properties
`models,modelTests=false,modelDocs=false`, in
`smartest_ai_testbook.web_server.generated.models`. It produces no router, API
base classes or server startup code.

The handwritten `smartest_ai_testbook/web_server/app.py` imports the generated
request models and translates the HTTP routes to application operations.
Evaluator-specific options are documented as objects in OpenAPI; handwritten
domain validation enforces their required keys, nonblank strings and thresholds.
Runtime dependencies belong in `python/pyproject.toml` and `uv.lock`.
Reference: [python-fastapi generator options](https://openapi-generator.tech/docs/generators/python-fastapi/).

## Browser client

`typescript-fetch` with `withInterfaces=true` generates the API classes, models
and runtime in `web-client/src/generated/`.
`api/templates/typescript-fetch/runtime.mustache` is a versioned copy of
the 7.26.0 runtime template with explicit public interfaces added to its classes,
including error and response wrappers. This implements the project's class
contract rule. When upgrading the generator, compare this template with the new
upstream runtime template. The generator also writes `.openapi-generator/` and
`.openapi-generator-ignore` metadata, which are ignored by git. The client build
typechecks generated and handwritten code together.

The generator does not delete files for models or operations removed from the
contract, so the Python and client commands first delete their generated
directories through npm `pre` scripts. These directories contain only generated
files; never put handwritten code in them.
