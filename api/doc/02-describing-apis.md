# 2. Describing an API

This chapter reads one complete operation of [`openapi.yaml`](../openapi.yaml), then
explains each building block and the conventions the project chose.

## One operation, line by line

Starting a run of a suite:

```yaml
paths:
  /api/test-suites/{suite-id}/eval-runs:            # the path, with a parameter
    parameters:
      - $ref: '#/components/parameters/SuiteId'     # shared by every operation of this path
    post:                                           # the HTTP method
      operationId: createEvalRun                    # unique name, becomes a method name
      tags: [Execution]                             # group, becomes an API class
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/EvalRunInput'
      responses:
        '201':
          description: Created evaluation run
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EvalRun'
        '404':
          description: Test suite not found
        '422':
          description: Invalid provider, model, or suite configuration
```

Read it as a sentence: *"POST to `/api/test-suites/{suite-id}/eval-runs`, with a JSON
`EvalRunInput` body, returns 201 and an `EvalRun`, or 404 if the suite does not exist, or
422 if the input is invalid."*

## Paths and operations

A **path** is a URL template; an **operation** is one HTTP method on that path.

```yaml
/api/test-suites:          # path
  get: ...                 # operation: list suites
  post: ...                # operation: create a suite
```

| Method | Meaning | Body | Typical success |
|---|---|---|---|
| `get` | read | no | 200 |
| `post` | create | yes | 201 |
| `put` | replace / update | yes | 200 |
| `delete` | remove | no | 204 |

Every operation in the project has:

- an **`operationId`**: unique, in camelCase, a verb + a noun (`listTestSuites`,
  `createTestCase`, `getEvalRun`). Generators use it as the method name.
- one **tag**: generators use it to group methods into classes (`TestCreationApi`,
  `ExecutionApi`, `ReportingApi`, `HealthApi`).
- optionally a `summary` or `description` for readers.

## Parameters

Parameters are values in the URL. This project uses only **path parameters**, defined once
in `components/parameters` and referenced:

```yaml
components:
  parameters:
    SuiteId:
      name: suite-id          # must match {suite-id} in the path
      in: path                # path | query | header | cookie
      required: true          # always true for path parameters
      schema: { type: string, format: uuid }
```

| `in` | Example | Used here |
|---|---|---|
| `path` | `/api/test-cases/{case-id}` | yes: `suite-id`, `case-id`, `expectation-id`, `eval-run-id` |
| `query` | `/api/test-suites?name=abc` | no |
| `header` | `X-Request-Id: ...` | no |

## Request bodies

```yaml
requestBody:
  required: true
  content:
    application/json:                 # media type
      schema: { $ref: '#/components/schemas/TestSuiteInput' }
```

All bodies are JSON. The schema defines what the client must send.

## Responses

Responses are keyed by **status code** (as strings). Each has a `description` and, if it
returns data, a `content` with a schema:

```yaml
responses:
  '200':
    description: Updated test suite
    content:
      application/json:
        schema: { $ref: '#/components/schemas/TestSuite' }
  '404':
    description: Test suite not found         # no body described
```

Status codes used in the project:

| Code | Meaning | When |
|---|---|---|
| 200 | OK | successful read or update |
| 201 | Created | successful creation (suite, test, expectation, run) |
| 204 | No Content | successful deletion |
| 404 | Not Found | the suite, test, expectation or run does not exist |
| 422 | Unprocessable Entity | the input has the wrong shape, breaks a domain rule, or names a provider that is not configured |

## Schemas

Schemas describe the JSON data. The main keywords:

```yaml
TestCaseInput:
  type: object
  required: [title, prompt, expectations]        # these properties must be present
  properties:
    title: { type: string, minLength: 1, pattern: '\S' }   # at least one non-space character
    prompt: { type: string, minLength: 1 }
    variables:
      type: object
      default: {}
      additionalProperties: { type: string }      # a map: any key, string values
    expectations:
      type: array
      minItems: 1
      items: { $ref: '#/components/schemas/Expectation' }
```

| Keyword | Meaning | Example in the contract |
|---|---|---|
| `type` | `object`, `array`, `string`, `number`, `integer`, `boolean` | everywhere |
| `format` | refines a type | `uuid`, `date-time` |
| `required` | properties that must be present | `[title, prompt, expectations]` |
| `enum` | the only allowed values | `evaluator_type: [exactMatch, semanticSimilarity, llmJudge]` |
| `minLength`, `pattern` | string constraints | `name: { minLength: 1 }` |
| `minimum`, `maximum` | number constraints | `threshold: 0..1` |
| `minItems` | array constraint | at least one expectation |
| `additionalProperties` | map values, or forbid extra keys | `variables` map; `HealthResponse` forbids extras |
| `nullable: true` | the value may be `null` | `EvalResult.output`, `EvalResult.error` |
| `readOnly: true` | set by the server only | `EvalResult.passed` |
| `default` | value assumed when missing | `variables: {}` |
| `allOf` | combine schemas | see below |

### Composition with `allOf`

The project separates what the client **sends** from what the server **returns**. The
returned object is the input plus the identifier assigned by the server:

```yaml
Expectation:
  allOf:
    - $ref: '#/components/schemas/ExpectationInput'   # name, evaluator_type, threshold, options
    - type: object
      required: [id]
      properties:
        id: { type: string, format: uuid }
```

`allOf` means "valid against all these schemas". The same technique builds `TestCase`
(from `TestCaseInput`) and `CreateExpectationInput` (input plus `test_case_id`).

### Limits of schemas

Some rules cannot be expressed, or are expressed only as text:

```yaml
options:
  type: object
  additionalProperties: true
  description: 'Exactly one nonblank string: expected for exactMatch or semanticSimilarity, rubric for llmJudge.'
```

"Which key is required depends on `evaluator_type`" is a business rule. The contract
documents it, and the **domain** enforces it (`validate_expectation`). A contract
describes the shape of the messages; it does not replace domain validation.

## Conventions of this project

| Topic | Convention | Example |
|---|---|---|
| Path prefix | application endpoints under `/api/`; health at the root | `/api/test-cases`, `/health` |
| Path segments | plural nouns, kebab-case | `/test-suites`, `/eval-runs` |
| Path parameters | kebab-case, UUID format | `{suite-id}`, `{eval-run-id}` |
| JSON properties | snake_case | `suite_id`, `evaluator_type`, `started_at` |
| `operationId` | camelCase verb + noun | `listSuiteEvalRuns` |
| Schema names | PascalCase; inputs end with `Input` | `TestSuiteInput` / `TestSuite` |
| Create inputs with a parent | `Create…Input` adds the parent ID | `CreateTestCaseInput.suite_id` |
| Errors | status code; FastAPI returns `{"detail": ...}` | 404, 422 |

Consistency matters more than any single choice: a reader who learns the pattern of one
endpoint can predict all the others.

---

← [1. The OpenAPI standard](01-openapi-standard.md) · Next: [3. API design: a UI-driven BFF →](03-api-design-bff.md)
