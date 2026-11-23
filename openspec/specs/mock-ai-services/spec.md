# mock-ai-services Specification

## Purpose

Lets users validate the complete application flow without real AI models by replacing the system under test and the AI evaluation service with deterministic offline mocks.

## Requirements

### Requirement: Two AI integration points
The system SHALL involve an AI service only at two points: the system under test, which generates one response per test during a run, and the AI evaluation service, which is used only for semantic similarity and LLM judge expectations. Exact match evaluation SHALL never require an AI service.

#### Scenario: Suite with only exact match expectations
- **WHEN** a suite whose expectations are all exact match is executed
- **THEN** only the system under test is invoked and no evaluation service is called

#### Scenario: Suite with AI expectations
- **WHEN** a test has a semantic similarity or LLM judge expectation
- **THEN** the evaluation service is invoked for that expectation after the system under test responds

### Requirement: Enable mock mode at startup
The backend SHALL replace both the system under test and the AI evaluation service with mocks when it starts with `AI_MODE` set to `mock`. With any other value or when unset, the existing OpenAI configuration SHALL apply unchanged. Mock mode SHALL not require or use OpenAI credentials, even when they are configured.

#### Scenario: Mock mode without credentials
- **WHEN** the backend starts with `AI_MODE=mock` and no OpenAI key
- **THEN** runs can be executed and all three expectation types can be evaluated

#### Scenario: Default mode unchanged
- **WHEN** the backend starts without `AI_MODE`
- **THEN** the OpenAI provider and evaluators are configured exactly as before, only when an OpenAI key is present

### Requirement: Mock system under test
The mock provider SHALL be named `mock` and SHALL supply a model for any requested model name. Its model SHALL answer, without network calls, with the prompt after substituting its variables, prefixed with `[mock] `. The run SHALL record provider `mock` and the requested model name.

#### Scenario: Mock answer
- **WHEN** a test with prompt `Capital of {{country}}?` and variable `country=France` runs on the mock model `demo`
- **THEN** the recorded output is `[mock] Capital of France?` and the run records provider `mock` and model `demo`

### Requirement: Mock AI evaluation service
In mock mode, semantic similarity and LLM judge expectations SHALL be evaluated without network calls: each valid expectation SHALL receive score 1 on the 0–1 scale with feedback `Mock evaluation`, and the normal threshold rule SHALL decide its outcome. Expectation validation SHALL still apply. Exact match SHALL keep its real behavior.

#### Scenario: AI expectations in mock mode
- **WHEN** a semantic similarity expectation with threshold 0.8 and an LLM judge expectation are evaluated in mock mode
- **THEN** both record score 1, scale 0–1, feedback `Mock evaluation` and a passed outcome

#### Scenario: Exact match in mock mode
- **WHEN** an exact match expectation expecting `Paris` evaluates the mock answer
- **THEN** it uses literal comparison and records a failed outcome with score 0

### Requirement: Accept only the configured provider
The backend SHALL start a run only when the requested provider name equals the name of the configured provider: `openai` in default mode with an OpenAI key, `mock` in mock mode. Any other request SHALL be rejected with an understandable validation error and no run SHALL be recorded.

#### Scenario: Provider mismatch
- **WHEN** the backend runs in mock mode and a client requests a run with provider `openai`
- **THEN** the request is rejected with a validation error and no run is stored

#### Scenario: Mock run over HTTP
- **WHEN** the backend runs in mock mode and a client requests a run with provider `mock` and any nonblank model name
- **THEN** the run is executed, stored and returned with provider `mock`

### Requirement: Choose the provider in the interface
The run configuration page SHALL let users choose between the `OpenAI` and `Mock` providers before starting a run, defaulting to `OpenAI`, and SHALL send the chosen provider with the model name.

#### Scenario: Start a mock run
- **WHEN** a user selects `Mock`, enters a model name and starts a run against a backend in mock mode
- **THEN** the run report shows provider `mock`, the mock answers and the recorded outcomes

#### Scenario: Provider not configured
- **WHEN** a user selects a provider that the backend has not configured
- **THEN** the interface displays the backend's validation error without claiming success

### Requirement: Equivalent mock behavior
TypeScript and Python domain implementations SHALL provide the same mock provider, mock model and mock evaluator behavior. Startup configuration and HTTP coverage differences SHALL be documented.

#### Scenario: Run equivalent definitions on mocks
- **WHEN** equivalent suites run on the mock model with mock evaluators in both languages
- **THEN** they produce equivalent outputs, scores, feedback and outcomes
