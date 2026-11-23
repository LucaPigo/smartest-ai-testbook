# 1. The OpenAPI standard

## What OpenAPI is

**OpenAPI** is a standard format for describing HTTP APIs. An OpenAPI document is a YAML
(or JSON) file that lists, in a way both people and programs can read:

- which **endpoints** exist (method + path);
- which **input** each one accepts (path parameters, query parameters, body);
- which **responses** it returns, with their status codes and data shapes;
- the **data types** (schemas) exchanged.

The document describes *what* the API does, not *how* it is implemented. Python, TypeScript
or any other language can implement the same document.

> The name comes from the Swagger project, donated to the OpenAPI Initiative in 2015.
> "Swagger" is still the name of popular tools, such as the interactive documentation page.

## Why a contract

| Without a contract | With a contract |
|---|---|
| The client guesses field names from the server code. | Both sides read the same document. |
| A renamed field breaks the client at run time. | The change is visible in the contract, and generated code stops compiling. |
| Documentation is written by hand and goes out of date. | Documentation and code are generated from the same source. |
| Two backends drift apart. | Both are checked against one specification. |

This project follows a **contract-first** approach: the API is designed in
`openapi.yaml` first, then the code is generated and written to match it. The opposite,
**code-first**, writes the server and extracts the document from it (FastAPI can do this
too, at `/docs`). Contract-first fits this project because one contract serves two
backends (Python and TypeScript) and one client.

## Versions

The project uses **OpenAPI 3.0.3**. Version 3.1 aligns schemas fully with JSON Schema
(for example, `nullable: true` becomes `type: [string, "null"]`), but generator support
for 3.0 is broader. Always check the first line of a document:

```yaml
openapi: 3.0.3
```

## Structure of a document

Every OpenAPI document has the same top-level sections. This is
[`openapi.yaml`](../openapi.yaml), heavily shortened:

```yaml
openapi: 3.0.3                     # 1. version of the standard

info:                              # 2. metadata about this API
  title: Smartest AI Testbook API
  version: 1.0.0
  description: HTTP contract for the Smartest AI Testbook web application.

tags:                              # 3. groups of operations
  - name: Test Creation
    description: Manage suites, tests and their expectations.
  - name: Execution
    description: Create and inspect evaluation runs.

paths:                             # 4. the endpoints
  /api/test-suites:
    get:
      operationId: listTestSuites
      tags: [Test Creation]
      responses:
        '200':
          description: Test suites
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/TestSuite'

components:                        # 5. reusable definitions
  parameters:
    SuiteId: { name: suite-id, in: path, required: true, schema: { type: string, format: uuid } }
  schemas:
    TestSuite:
      type: object
      required: [id, name, tests]
      properties:
        id: { type: string, format: uuid }
        name: { type: string }
```

| Section | Contains | In this project |
|---|---|---|
| `openapi` | The version of the standard. | `3.0.3` |
| `info` | Title, version and description of the API. | Version `1.0.0` |
| `servers` | Base URLs (optional). | Omitted: the client reads the address from `configuration.js` at run time. |
| `tags` | Named groups of operations. | `Health`, `Test Creation`, `Execution`, `Reporting` |
| `paths` | Each path and its operations. | 11 paths, 16 operations |
| `components` | Reusable `schemas`, `parameters`, `responses`, … | 4 path parameters, 13 schemas |

## `$ref`: write once, reuse everywhere

`$ref` points to a definition elsewhere in the document:

```yaml
$ref: '#/components/schemas/TestSuite'
```

`#` is the current document; the rest is the path inside it. Each schema is defined once
in `components` and referenced wherever it is needed, so a change in one place applies to
every endpoint. Generators turn each named schema into one class or type.

## Schemas are (almost) JSON Schema

The data types in `components/schemas` use a dialect of **JSON Schema**: `type`,
`properties`, `required`, `enum`, `minimum`, `maxLength`, `items`, `allOf`, … Chapter 2
shows the keywords used in the project.

## Tools around a document

| Tool type | What it does | Example |
|---|---|---|
| Editor / viewer | Shows the document as navigable documentation. | Swagger Editor, Redocly, VS Code extensions |
| Validator | Checks that the document follows the standard. | `openapi-generator-cli validate` |
| Code generator | Produces models, server stubs or client SDKs. | OpenAPI Generator, `openapi-typescript` (chapter 4) |
| Test tools | Send requests or check servers against the contract. | Postman, contract tests |

To try the contract interactively, paste `openapi.yaml` into
[editor.swagger.io](https://editor.swagger.io/), or start the Python backend and open
`http://localhost:3002/docs`.

---

[Back to the lesson plan](README.md) · Next: [2. Describing an API →](02-describing-apis.md)
