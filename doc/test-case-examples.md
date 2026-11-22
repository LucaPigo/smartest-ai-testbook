# Minimal Test and Report Examples

These examples show the data needed to define tests and review a run. Test IDs remain stable when contents are edited. Historical results retain the original prompt template and recorded outcomes, without versioning the complete test definition.

## `TestCase` examples

Every test has an ID, title, prompt, variables and at least one expectation. Variables are optional and default to an empty map. Criteria belong to each expectation's options.

| ID and title | Prompt and variables | Expectations |
|---|---|---|
| **TC-01 — Password reset** | Prompt: “Answer `{{query}}` using only `{{context}}`.” Variables: `query` = “How can I reset my password?”, `context` = “Go to Settings > Security and click Reset.” | `exactMatch`, threshold 1, `options.expected` = “Go to Settings > Security and click Reset.”; `semanticSimilarity`, threshold 0.85, its own `options.expected` = “Go to Settings > Security and click Reset.” |
| **TC-02 — Extract contact data** | Prompt: “Return exactly this JSON shape with no surrounding text: `{"name":"...","email":"...","amount":0}`. Extract the values from `{{email_text}}`.” Variable: `email_text` = “I am Mario Rossi (mario@test.it) and request a refund of 150 euros.” | `exactMatch`, threshold 1, `options.expected` = `{"name":"Mario Rossi","email":"mario@test.it","amount":150}`. This checks the literal output string, including formatting; it is not a JSON-schema validator. |
| **TC-03 — Delayed package** | Prompt: “Respond with empathy and professionalism to a customer whose package is three days late.” | Two `llmJudge` expectations, each with threshold 0.8: “Empathetic tone” uses `options.rubric` = “Apologize clearly and use a professional, empathetic tone.”; “Authorized assistance” uses `options.rubric` = “Offer practical assistance without promising compensation not authorized by the prompt.” |
| **TC-04 — Unknown private information** | Prompt: “What is this customer's private phone number? No phone number is supplied.” | `llmJudge`, threshold 0.8, `options.rubric` = “Say the number is unknown; do not invent one.” |

All scores use 0–1. Exact match scores 0 or 1 and has a fixed threshold of 1. Semantic similarity and judge thresholds can be configured within 0–1. Sharing a scale does not make different algorithms equivalent; no average is calculated.

A complete definition might contain these two independent checks:

```json
{
  "id": "TC-05",
  "title": "Capital of France",
  "prompt": "What is the capital of {{country}}?",
  "variables": { "country": "France" },
  "expectations": [
    {
      "id": "EXP-01",
      "name": "Correct answer",
      "evaluatorType": "semanticSimilarity",
      "threshold": 0.85,
      "options": { "expected": "Paris" }
    },
    {
      "id": "EXP-02",
      "name": "Concise answer",
      "evaluatorType": "llmJudge",
      "threshold": 0.8,
      "options": { "rubric": "The answer contains only the city name." }
    }
  ]
}
```

The IDs above are illustrative; the application assigns UUIDs. The model under test receives only the prompt and variables. The interface presents an expected-answer or rubric field rather than a JSON options editor.

## Short example of an LLM judge prompt

```text
Evaluate the model response using this expectation's rubric.
Return a numeric score from 0 to 1 and brief feedback.
Evaluate only the requested criterion; do not reward unsupported claims.
Return JSON: {"score": 0.8, "feedback": "..."}
```

For TC-03's “Empathetic tone” check, `1` means the answer clearly apologizes and uses an empathetic, professional tone; `0` means it is rude or ignores the issue. The second check uses its own rubric to assess assistance and compensation.

## Run report format

The application selects one model per run. For each test, the runner generates one response and evaluates every expectation against that same response in order. Evaluators return values and feedback; the runner applies `value >= threshold`. A test passes only if generation succeeds and all its expectations pass.

`EvalReport` shows run details and one row per test. A row identifies every check by ID, name and evaluator type, alongside its score, scale, threshold and outcome. The abbreviated examples below omit IDs for readability.

| Test ID | Generated output | Score per expectation | Outcome | Feedback |
|---|---|---|---|---|
| **TC-01** | “Go to Settings > Security and click Reset.” | Exact Match `1/1` (threshold `1`); Similarity `0.92/1` (threshold `0.85`) | PASS | The string matches exactly and exceeds the semantic threshold. |
| **TC-02** | `{"name": "Mario Rossi", "email": "mario@test.it", "amount": 150}` | Exact Match `0/1` (threshold `1`) | FAIL | The extra spaces differ from the expected string, even though the JSON data is equivalent. |
| **TC-03** | “We are sorry for the delay. We understand the inconvenience and are happy to help.” | Empathetic tone `0.9/1`; Authorized assistance `0.8/1` (both thresholds `0.8`) | PASS | Both independent criteria pass; equality with a threshold is sufficient. |
| **TC-04** | “You can reach the customer at +1-555-0199.” | LLM Judge `0.1/1` (threshold `0.8`) | FAIL | The response invents a phone number. |

A generation error fails the test and leaves its scores empty. An evaluation error or invalid score fails that expectation without a numeric value; later checks and tests still execute. The report distinguishes these technical errors from an ordinary failed comparison.

The report also includes the run ID, suite, date/time and provider/model. It does not aggregate results or calculate an overall score. Values above are illustrative, not live model measurements.

## MVP history limitation

Runs and results are saved with the stable `TestCase` ID. If a test is edited, the historical report retains the original prompt template, outputs, expectation labels, thresholds and evaluations, but not the complete test definition or substituted model input. JSON export is a documented requirement whose implementation remains deferred.
