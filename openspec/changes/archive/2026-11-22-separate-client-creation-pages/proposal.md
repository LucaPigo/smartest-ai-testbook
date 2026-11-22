# Proposal

## Why

The client mixes a suite creation form with the suite list, and its pages differ from the wireframe in `doc/ui.excalidraw`. Users need an index that only lists and links to a dedicated creation page, and pages that follow the wireframe.

## What Changes

- Move suite creation to `/test-suites/new` and keep `/test-suites` as an index without forms, with an add control as in the wireframe.
- Rename the run routes as in the wireframe: `/execute/:suiteId` lists reports with a play control, and `/execute/:suiteId/run` holds the provider and model configuration and starts the run. The run configuration is chosen when a run starts, not on the suite.
- Keep test and expectation management on one page, with test creation and editing on their existing URLs and sharing `TestForm`.
- Make the suite creation page reuse the suite edit form.
- Follow the wireframe layout: suite navigation with the current tab marked, back control with page title, add controls on lists, report summary tiles with collapsible results and status icons, and a two-column test page with Save in the page bar.
- Preserve success, validation, error and asynchronous navigation behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-access`: The suite index contains no form and links to a creation page; pages follow the wireframe.

## Impact

Shared React client routes/page components, browser workflow tests and web architecture documentation. HTTP contracts, generated artifacts and domain implementations are unchanged.
