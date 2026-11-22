# Design

## Context

The client uses BrowserRouter and shared outlet context. The suite index contains the suite creation form. Test and expectation management already share one page, with expectation creation inline. The wireframe in `doc/ui.excalidraw` defines an execute page listing reports and a separate run configuration page. See [proposal.md](./proposal.md).

## Goals / Non-Goals

**Goals:** The suite index contains no form. Suite creation has its own route reusing the edit form. Pages follow the wireframe using existing form fields and API calls.

**Non-Goals:** HTTP or domain changes, splitting test and expectation management, a new routing framework, generated clients, new dependencies and a visual redesign beyond the wireframe.

## Decisions

Extract suite listing into a component with an add link and no form. Replace the two duplicated suite forms with one SuiteForm taking optional initial values, used by SuiteEditor and a new SuiteNewPage. Keep suite editing, test creation/editing and expectation management at their existing URLs, reusing TestForm and ExpectationForm.

Keep RunPage at `/execute/:suiteId` with the list of reports and a play link, and add RunConfigPage at `/execute/:suiteId/run` with provider selection, model configuration and a play button that starts the run. The configuration belongs to the run, as in the domain model: it is chosen at run start and not stored on the suite, so the API is unchanged. Execute and Report navigation both lead to `/execute/:suiteId`; the report detail stays at `/reports/:runId`.

Add shared SuiteNavigation (with the current tab marked) and PageTitle (back control, title, optional aside). Lay out the test page in two columns with Save in the page bar; the report page shows summary tiles and collapsible results with status icons.

Cancel on suite creation goes to the index. Successful suite and test saves retain current navigation and a started run opens its report. Preserve loading and missing-resource states and guard asynchronous completions after unmount. Use direct functions and existing React state rather than a generic CRUD-page abstraction.

## Risks / Trade-offs

- Existing bookmarks -> all existing URLs remain; only `/test-suites/new` is added.
- Reloads and browser navigation -> retain BrowserRouter and existing SPA fallback, verify actual browser paths.
- Pending requests after leaving a page -> keep navigation/error updates scoped to the mounted page.
- Existing dirty checkout -> preserve unrelated code and completed changes.
