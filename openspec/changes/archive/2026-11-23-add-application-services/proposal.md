# Proposal

## Why

The use cases of the application are orchestrated by the Python HTTP routes: each route decides the sequence "find, change domain objects, save" and some routes hold business rules (expectation IDs must belong to their test case, a test case is rebuilt when one of its expectations changes, tests and expectations are located across suites, only the configured provider is accepted and a completed run is saved). Code that uses the domain without HTTP must repeat these sequences, and another client would duplicate the rules. The domain should be the single place where data is orchestrated, saving through injected repositories, while HTTP only translates requests and responses.

## What Changes

- Add one **application service** per subsystem, each with an explicit public contract and receiving its collaborators by dependency injection:
  - a test catalog for suites, test cases and expectations, using the suite repository;
  - a run service for starting, listing and reading evaluation runs, using the suite and run repositories, the runner and the configured model provider.
- Move the rules and sequences listed above from the web server into these services. Entities stay persistence-ignorant: they never save themselves.
- Services report "not found" with an empty result and invalid input with the domain's validation error; the web server translates them to the existing 404 and 422 responses.
- The Python composition root exposes the two services; HTTP routes become thin translators. HTTP behavior, status codes and messages do not change.
- **Python only.** By explicit decision of the project owner, this change does not touch TypeScript, which already lacks persistence and the HTTP workflow. This is an accepted exception to the AGENTS.md rule of implementing every feature in both languages; the domain design documents that the application services exist only in Python.
- Update the domain design, which currently states that the HTTP handler is the caller and that no additional subsystem classes exist, and the Python lesson.

## Capabilities

### New Capabilities

None.

### Modified Capabilities
- `mvp-web-workflow`: the requirement "Server-independent domain" changes so that every use case of the web workflow, with its rules, is available as a domain operation that saves through injected repositories, and HTTP only translates it.

## Impact

- **Python domain**: new application service classes and contracts in the test creation and execution subsystems. TypeScript is unchanged.
- **Python composition and HTTP**: `Dependencies` exposes the services instead of repositories, runner and provider; `web_server/app.py` and `helpers.py` lose lookups and orchestration. No API contract change.
- **Tests**: new Python service tests; Python composition and HTTP tests use the services; HTTP workflow tests must pass unchanged in their assertions.
- **Documentation**: `doc/domain-design.md`, `doc/web-architecture.md` and the `python/doc/` lesson (chapters 1–6 and Appendix A).
- **No new dependencies.**
