# Persistent storage

## Purpose

Preserve test definitions and recorded evaluation history across application restarts.

## ADDED Requirements

### Requirement: Persist suite definitions
The system SHALL persist suites, tests and expectations, including their identifiers and configuration.

#### Scenario: Restart after saving
- **WHEN** a saved suite is loaded after an application restart
- **THEN** its tests, expectations and identifiers are restored

#### Scenario: Failed update
- **WHEN** saving a suite and its contained definitions fails
- **THEN** no partial update is visible

### Requirement: Persist completed runs
The system SHALL persist completed runs, their results and expectation outcomes for later retrieval.

#### Scenario: Review after restart
- **WHEN** the application restarts after a run completes
- **THEN** the run and its recorded results and scores remain retrievable

#### Scenario: Preserve recorded information
- **WHEN** a test definition changes after a run is stored
- **THEN** the stored run retains its recorded prompt, output or error and expectation outcomes
