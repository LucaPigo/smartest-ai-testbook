# Tasks

## 1. Document the agreed model

- [x] 1.1 Update requirements, domain design, glossary, examples, diagrams and current implementation notes; verify Markdown consistency, parse both Excalidraw files and inspect their changed labels.

## 2. Implement TypeScript first

- [x] 2.1 Implement self-contained expectations, validation, builder inputs, all three evaluator strategies and runner-owned outcomes; update examples and meaningful regression tests, then pass TypeScript tests and type checking before editing Python behavior.

## 3. Align Python

- [x] 3.1 Mirror TypeScript definition, evaluator and execution behavior in Python; update domain tests and verify independent criteria, literal matching, score validation, sequential generation and error isolation with focused tests.
- [x] 3.2 Update SQLite serialization and legacy definition loading while preserving identities and run history; verify restart, legacy conversion, normal resave and atomic failure tests on temporary databases.

## 4. Align transport contracts

- [x] 4.1 Update both OpenAPI documents and Python HTTP translation, regenerate all transport artifacts, update HTTP fixtures and verify API workflow tests plus generation check mode.

## 5. Guide configuration in the interface

- [x] 5.1 Replace test-wide criteria and JSON options editing with type-specific fields and fixed exact thresholds; update browser fixtures and verify client build and real-browser creation, editing, type switching and reports against the Python backend with fake model responses.

## 6. Final integration

- [x] 6.1 Review the complete change for contract propagation and cross-language parity; run strict OpenSpec validation, full relevant test suites, HTTP/browser integration, generated-artifact checks and editor diagnostics; record actual results and remaining external-provider limits in this change.

## Workflow follow-up

- Keep the completed change available for review; archive only when requested.
