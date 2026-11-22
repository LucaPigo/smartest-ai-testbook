# web-access Specification

## Purpose

Allow users to access the same web application through either system implementation using a shared HTTP contract.

## Requirements

### Requirement: Shared web interface
The system SHALL provide a single web application through a server dedicated to its static files.

#### Scenario: Open the application
- **WHEN** a user opens the web interface server address
- **THEN** the browser receives and displays the web application

### Requirement: Select the backend implementation
The system SHALL allow the backend address to be changed through public runtime configuration, without rebuilding the web application or restarting its static hosting. Reloading the page SHALL use the configured address. Public configuration MUST contain no secrets.

#### Scenario: Switch backends
- **WHEN** the served configuration changes from the TypeScript backend address to the Python backend address and the user reloads the page
- **THEN** the same application build sends requests to Python without restarting static hosting
- **AND** changing the address back and reloading selects TypeScript again

#### Scenario: Invalid runtime configuration
- **WHEN** runtime configuration is missing, cannot be loaded, or contains a missing or invalid HTTP or HTTPS backend address
- **THEN** the application displays an understandable configuration error

### Requirement: Shared HTTP contract
Both backends SHALL expose available operations according to `api/openapi.yaml`, with the same contract-defined data and observable behavior. The initial contract SHALL contain only `GET /health`, returning HTTP 200 with JSON `{"status":"ok"}`. This operation SHALL check connectivity only, without claiming readiness of persistence, providers or domain features. Routing and errors not specified by the contract MAY follow framework defaults.

#### Scenario: Check connectivity
- **WHEN** the contract's connectivity request is sent to either backend
- **THEN** both respond with the same success status code, format, and content defined by the contract

#### Scenario: Interface checks the configured backend
- **WHEN** the web application requests a connectivity check from the configured backend
- **THEN** it shows success only when the response contains status `ok`
- **AND** request failures, invalid health responses and requests exceeding five seconds produce an understandable connection failure

#### Scenario: Repeat the connectivity check
- **WHEN** the user requests another connectivity check using the interface button
- **THEN** the application checks the same configured backend again and updates the displayed result

### Requirement: Browser access from the configured origin
Both backends SHALL support browser requests from the configured web origin, including GET preflight. The default web origin SHALL be `http://localhost:3000`. CORS SHALL control browser access without requiring a custom rejection response for ordinary HTTP clients.

#### Scenario: Allowed browser origin
- **WHEN** a browser at the configured origin sends a health request or its GET preflight to either backend
- **THEN** the backend provides the CORS response headers needed for the browser to read the health response

#### Scenario: Different browser origin
- **WHEN** a browser at another origin requests health
- **THEN** the backend does not grant that origin permission to read the response

### Requirement: Reproducible API generation
The project SHALL version generated transport artifacts for both backends and the shared client, produced from the shared HTTP contract by one standard console command per application using pinned tooling. Regeneration SHALL preserve handwritten files.

#### Scenario: Repeat generation
- **WHEN** a generation command runs repeatedly with the same contract, configuration and tooling
- **THEN** generated artifacts are identical and handwritten files remain unchanged

#### Scenario: Review generated changes
- **WHEN** the contract changes and a generation command is run
- **THEN** the generated artifacts are rewritten from the contract and the differences are visible in version control

### Requirement: Suite index contains no form
The suite index SHALL list suites and link to a creation page, and SHALL NOT contain a creation form. Test and expectation management SHALL remain on one page.

#### Scenario: Create a suite from the index
- **WHEN** a user opens `/test-suites`
- **THEN** the index contains an add control linking to `/test-suites/new` and no form

### Requirement: Creation pages reuse editing logic
The suite creation page SHALL use the same form fields, validation and submission behavior as the suite edit page, differing only in the save operation. Test creation and editing SHALL continue to share one form.

#### Scenario: Same fields on new and edit
- **WHEN** a user opens the new suite page and the edit page of a suite
- **THEN** both show the same fields and the same validation messages for the same invalid input

### Requirement: Creation navigation and outcomes
The suite creation page SHALL support direct URLs and reloads. Cancel SHALL return to the suite index without submitting. A successful save SHALL open the suite edit page. Validation and request errors SHALL remain visible on the creation page with the user's input retained. A late response SHALL NOT navigate away from another page after the user leaves the creation page.

#### Scenario: Cancel or reload creation
- **WHEN** a user reloads the new suite page or cancels its form
- **THEN** reload displays that page and cancel returns to the index without a creation request

#### Scenario: Failed creation
- **WHEN** the save request fails
- **THEN** the page shows the error and retains the user's input

#### Scenario: Leave a pending creation
- **WHEN** a user leaves the new suite page before the response arrives
- **THEN** that response does not redirect the user from the page they chose

### Requirement: Execute and run configuration pages
The page at `/execute/<suite-id>` SHALL list the suite's reports and link to the run configuration page at `/execute/<suite-id>/run` with a play control, without containing a form. The run configuration page SHALL provide the provider selection and model configuration and a play control that starts the run. Starting a run SHALL open its report, and a late response SHALL NOT redirect a user who has left the page.

#### Scenario: Open run configuration
- **WHEN** a user opens `/execute/<suite-id>` and follows the play control
- **THEN** `/execute/<suite-id>/run` shows the provider and model configuration and no report list

#### Scenario: Start a run
- **WHEN** a user enters a model on `/execute/<suite-id>/run` and activates play
- **THEN** the run starts and its report opens

#### Scenario: Leave a pending run
- **WHEN** a user leaves the run configuration page before the response arrives
- **THEN** that response does not redirect the user from the page they chose

### Requirement: Wireframe-aligned pages
The client SHALL follow the wireframe: suite pages show Define, Execute and Report navigation with the current tab marked; pages show a back control with the title; suite and test lists end with an add control; the report shows Tests, Passed and Failed tiles and collapsible results with a status icon; the test page shows prompt and variables beside expectations with Save in the page bar.

#### Scenario: Current tab marked
- **WHEN** a user opens a suite's execute page
- **THEN** Execute is marked as the current page

#### Scenario: Report summary
- **WHEN** a user opens a report
- **THEN** it shows Tests, Passed and Failed tiles above results that expand to show details
