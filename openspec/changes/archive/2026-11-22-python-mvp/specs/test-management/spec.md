# Test management

## Purpose

Allow users to define and maintain suites and their test expectations.

## ADDED Requirements

### Requirement: Manage suites
The system SHALL create, list, update and delete suites with a stable identifier, name and description.

#### Scenario: Update a suite
- **WHEN** a user changes an existing suite's name or description
- **THEN** subsequent reads return the updated values with the same identifier

### Requirement: Manage tests and expectations
The system SHALL create, retrieve, update and delete tests in a suite and create, read and update their expectations. Test definitions SHALL include a prompt, variables, optional reference and rubric, and expectations with evaluator type, threshold and options.

#### Scenario: Create a test with expectations
- **WHEN** a user creates a test with one or more expectation inputs
- **THEN** the returned test contains those expectations with assigned stable identifiers

#### Scenario: Reject an invalid test
- **WHEN** a user submits a test without a prompt, without expectations, or without a criterion required by a selected evaluator
- **THEN** the system rejects the definition without persisting a partial test

### Requirement: Preserve historical results
Editing a test or expectation SHALL NOT change previously recorded run results.

#### Scenario: Edit after a run
- **WHEN** a user edits a prompt or expectation after a completed run
- **THEN** the previous run retains its recorded prompt, expectation identity, threshold and outcome
