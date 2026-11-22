# Web access delta

## ADDED Requirements

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
