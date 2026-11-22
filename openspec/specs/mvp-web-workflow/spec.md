# mvp-web-workflow Specification

## Purpose
Let users manage test suites and review model evaluations in a simple web interface.

## Requirements

### Requirement: Manage definitions through the interface
The web interface SHALL allow users to list, create, edit and delete suites and tests, and configure their expectations.

#### Scenario: Create a test
- **WHEN** a user supplies a valid test and its expectations in the interface
- **THEN** the interface saves them and displays the created test

#### Scenario: Invalid input or request failure
- **WHEN** the input is invalid or a save request fails
- **THEN** the interface displays an understandable error without claiming success

### Requirement: Run and review a suite
The web interface SHALL allow users to select a provider and model, start a run, list stored runs and review individual recorded results and failures.

#### Scenario: Review a completed run
- **WHEN** a user opens a completed run
- **THEN** the interface shows run metadata, test prompts, output or error, expectation outcomes, scores, thresholds and feedback

### Requirement: Python HTTP contract
The Python backend SHALL implement the operations specified by `api/openapi.yaml` with the defined request and response formats and status codes.

#### Scenario: Create a test with expectations
- **WHEN** a client sends a valid test creation request containing expectation inputs
- **THEN** the response contains the created test and expectation identifiers

### Requirement: Server-independent domain
Suite management, execution, persistence and reporting SHALL be usable without starting the web server.

#### Scenario: Execute without HTTP
- **WHEN** an application composes the domain and persistence dependencies without the web server
- **THEN** it can save a suite, execute it and retrieve its run
