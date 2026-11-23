# Spec Delta

## MODIFIED Requirements

### Requirement: Server-independent domain
Suite management, execution, persistence and reporting SHALL be usable without starting the web server. Every use case of the web workflow SHALL be available as a domain operation that applies its rules and saves through injected repositories; the web server SHALL only translate requests and outcomes.

#### Scenario: Execute without HTTP
- **WHEN** an application composes the domain and persistence dependencies without the web server
- **THEN** it can save a suite, execute it and retrieve its run

#### Scenario: Same rules without HTTP
- **WHEN** an application without the web server updates a test case using an expectation ID that belongs to another test case, or starts a run with a provider that is not configured
- **THEN** the domain operation rejects it with the same validation error the HTTP workflow reports, and nothing is saved

#### Scenario: Missing items without HTTP
- **WHEN** an application without the web server asks to change or read a suite, test case, expectation or run that does not exist
- **THEN** the domain operation reports that it was not found and nothing is saved

#### Scenario: Unchanged HTTP behavior
- **WHEN** a client uses any operation of the HTTP contract
- **THEN** status codes, response bodies and error messages are the same as before the use cases moved into the domain

## ADDED Requirements

### Requirement: Document use-case operation coverage
The Python domain SHALL provide the use-case operations for suites, test cases, expectations and runs. The documentation SHALL state that the TypeScript domain does not provide them, alongside its existing persistence and HTTP coverage differences.

#### Scenario: Read the coverage difference
- **WHEN** a reader consults the domain design or web architecture documents
- **THEN** they learn that the use-case operations exist only in the Python domain and why
