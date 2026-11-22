# suite-execution Specification

## Purpose
Run a suite against a selected model and record independent evaluation outcomes.

## Requirements

### Requirement: Execute a suite
The system SHALL run each test in a nonempty suite using a selected provider and model, recording run identity, start time, provider, model, test identity and original prompt.

#### Scenario: Model responds
- **WHEN** a suite is executed and the model returns a response
- **THEN** the response is recorded for that test and each configured expectation is evaluated

#### Scenario: Model fails
- **WHEN** generation fails for a test
- **THEN** its result records the error and failure and execution continues with the remaining tests

### Requirement: Evaluate each expectation
The system SHALL support exact match, semantic similarity and LLM judge strategies and retain each expectation's identity, evaluator, threshold, feedback, score and scale or error.

#### Scenario: Threshold and errors
- **WHEN** an evaluator succeeds
- **THEN** its result passes if and only if its score meets or exceeds its threshold
- **WHEN** an evaluator fails
- **THEN** its outcome is failed, the error is recorded, and remaining expectations are evaluated

### Requirement: Determine test outcome
A test SHALL pass only when model generation succeeds and every expectation passes.

#### Scenario: One expectation fails
- **WHEN** one expectation fails and the others pass
- **THEN** the test is reported as failed and all outcomes remain available

### Requirement: Select a real provider
The system SHALL allow execution against a configured OpenAI model through a provider adapter without embedding credentials in browser-delivered code.

#### Scenario: Invoke selected model
- **WHEN** a user selects a configured OpenAI model and starts a run
- **THEN** the selected model is invoked for the suite and its identity is recorded
