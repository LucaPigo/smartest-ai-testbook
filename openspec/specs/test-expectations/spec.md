# test-expectations Specification

## Purpose

Let users configure independent checks of a generated response through a small test definition and a fixed execution policy.

## Requirements

### Requirement: Self-contained expectations
A test SHALL contain ID, title, prompt, variables and at least one expectation. Each expectation SHALL contain ID, name, evaluator type, threshold and its own options. Reference answers and rubrics SHALL exist only in expectation options: `expected` for exact match and semantic similarity, `rubric` for LLM judge.

#### Scenario: Independent criteria on the same response
- **WHEN** a test contains two judge expectations with different rubrics
- **THEN** each evaluates the generated response using its own rubric
- **AND** changing one rubric does not change the other's criteria

#### Scenario: Default variables
- **WHEN** a test is created without variables
- **THEN** its variables are an empty map

### Requirement: Validate expectation configuration
The system SHALL reject unsupported evaluator types, blank names or criteria, non-finite thresholds and thresholds outside 0–1 before saving a test. Exact match SHALL require threshold 1. Semantic similarity and LLM judge SHALL accept thresholds on 0–1. Options SHALL have the required string field for the selected evaluator and SHALL NOT contain unsupported fields.

#### Scenario: Invalid criteria
- **WHEN** an exact or semantic expectation has no nonblank `expected`, or a judge has no nonblank `rubric`
- **THEN** the definition is rejected without persisting a partial update

#### Scenario: Invalid policy
- **WHEN** a submitted evaluator type is unsupported or its threshold is invalid, including exact match with threshold 0
- **THEN** the definition is rejected

### Requirement: Fixed scoring and execution
Tests and expectations SHALL execute sequentially. The model under test SHALL be selected once per run and invoked once per test. Every expectation SHALL evaluate the same generated response. Evaluators SHALL return a finite score on 0–1 and feedback; the runner SHALL determine expectation success using `score >= threshold`. Exact match SHALL compare strings literally.

#### Scenario: Evaluate one generated response
- **WHEN** a test with multiple expectations runs successfully
- **THEN** the model generates one response and every expectation evaluates that response in order
- **AND** the recorded outcome includes each expectation's identity, threshold, feedback and score on 0–1

#### Scenario: Exact match
- **WHEN** an exact expectation compares an output differing in whitespace or case from its expected string
- **THEN** it scores 0 and fails

#### Scenario: Threshold equality
- **WHEN** a score equals the configured threshold
- **THEN** that expectation passes

### Requirement: Preserve errors and historical outcomes
A test SHALL pass only when generation succeeds and every expectation passes. Generation errors SHALL skip its evaluations and SHALL NOT stop later tests. Evaluation errors or invalid scores SHALL fail that expectation and SHALL NOT stop later checks. Recorded runs and report snapshots SHALL remain independent of subsequent definition edits.

#### Scenario: Failed evaluation
- **WHEN** an evaluator fails or returns a score outside 0–1
- **THEN** the outcome records an error and failure without a numeric score
- **AND** later expectations and tests still execute

#### Scenario: Edited criteria after a run
- **WHEN** expectation criteria change after a run
- **THEN** the run retains its original recorded thresholds, scores, labels and outcomes

### Requirement: Guided expectation forms
The interface SHALL expose an expected-answer field for exact and semantic checks and a rubric field for judge checks. It SHALL fix the exact threshold to 1, provide editable 0–1 thresholds for other checks, and SHALL NOT require users to edit JSON options or test-wide criteria.

#### Scenario: Switch evaluator type
- **WHEN** the user changes an expectation to LLM judge
- **THEN** the form shows a rubric field and submits only the judge options

### Requirement: Preserve existing saved definitions
Existing SQLite definitions with test-wide reference answers or rubrics SHALL remain readable. Their shared criterion SHALL become a local option for each matching expectation; IDs, variables, titles and recorded run history SHALL be preserved. Subsequent saves SHALL use only the new definition format.

#### Scenario: Reopen an existing suite
- **WHEN** an existing suite is loaded after the change
- **THEN** each matching expectation has its original reference or rubric in its own options
- **AND** saving and reloading preserves the new configuration without rewriting previous runs

### Requirement: Equivalent language behavior
TypeScript and Python domain implementations SHALL support the same three expectation types, validation rules, score semantics and execution policy. Existing HTTP coverage differences SHALL be documented without claiming endpoint parity from generated types.

#### Scenario: Run equivalent definitions
- **WHEN** equivalent tests use deterministic model, embedding and judge responses in both languages
- **THEN** they produce equivalent scores, thresholds, outcomes and error isolation
