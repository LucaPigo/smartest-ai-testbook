# Tasks

## 1. Suite creation page

- [x] 1.1 Replace the two duplicated suite forms with one `SuiteForm` (optional initial values, submit label, cancel link) used by `SuiteEditor`, and verify `npm run build` in `web-client` typechecks and the suite edit page still saves.
- [x] 1.2 Add `SuiteNewPage` at `/test-suites/new` using `SuiteForm`, with cancel to `/test-suites`, success navigation to the new suite's page, visible errors with retained input and a guard against navigation after unmount; verify in the browser that creating, cancelling, a failed save, a pending save and a reload of `/test-suites/new` behave as specified.
- [x] 1.3 Remove the creation form from `SuiteList` and add an add control linking to `/test-suites/new`; verify `/test-suites` contains no form and the control opens the creation page.
- [x] 1.4 Cover the suite scenarios in `web-client/tests/workflow.mjs` and verify it passes with the built client served on port 5174.

## 2. Execute and run configuration pages

- [x] 2.1 Make `RunPage` at `/execute/:suiteId` list reports with a play link, and add `RunConfigPage` at `/execute/:suiteId/run` with provider selection, model configuration and a play button that starts the run, keeping the guard against late responses; remove the `/run` routes; verify a started run opens its report and a pending run does not redirect.
- [x] 2.2 Point Execute and Report in `SuiteNavigation` and the suite list Run link to `/execute/:suiteId`; verify the links reach the execute page and the current tab is marked.
- [x] 2.3 Cover the run scenarios in `web-client/tests/workflow.mjs` and `web-client/tests/integration.mjs` and verify both pass.

## 3. Wireframe alignment

- [x] 3.1 Add shared `SuiteNavigation` current-tab marking and `PageTitle` (back control, title, aside) and use them on suite, test, run and report pages; verify the build and browser tests pass.
- [x] 3.2 Add add controls to suite and test lists, status icons and a report title with run date, and lay out the test page in two columns with Save in the page bar; verify `web-client/tests/workflow.mjs` passes.
- [x] 3.3 Compare each page with `doc/ui.excalidraw` in a real browser and verify the differences noted in the design are the only ones remaining.

## 4. Documentation and integration

- [x] 4.1 Update the route description in `doc/web-architecture.md` to list `/test-suites/new`, `/execute/<suite-id>` and `/execute/<suite-id>/run`, and state that the suite index contains no form; verify the text matches the router in `main.tsx`.
- [x] 4.2 Verify test and expectation management still work on one page: creation and editing on their existing URLs and inline Add expectation, covered by the browser workflow tests.
- [x] 4.3 Run `npm run build` in `web-client`, `npm run verify:browser`, `web-client/tests/workflow.mjs` and `web-client/tests/integration.mjs` against the Python backend, and verify all pass with no browser console errors.

## Workflow follow-up

- Archive the change after the project's review requirements are satisfied.
- Verify the archived result.
