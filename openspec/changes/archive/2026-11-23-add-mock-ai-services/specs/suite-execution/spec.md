# Spec Delta

## MODIFIED Requirements

### Requirement: Select a real provider
The system SHALL allow execution against a configured OpenAI model through a provider adapter without embedding credentials in browser-delivered code. A run SHALL be accepted only for the provider configured at startup, which is OpenAI unless mock mode is enabled.

#### Scenario: Invoke selected model
- **WHEN** a user selects a configured OpenAI model and starts a run
- **THEN** the selected model is invoked for the suite and its identity is recorded

#### Scenario: OpenAI not configured
- **WHEN** a run is requested with provider `openai` but the backend has no OpenAI key or runs in mock mode
- **THEN** the request is rejected with a validation error and no model is invoked
