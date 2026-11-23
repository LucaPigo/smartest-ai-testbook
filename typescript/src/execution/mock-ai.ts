// Offline replacements for the two AI integration points: the system under test
// (MockModel, supplied by MockProvider) and the AI evaluation service (MockEvaluator).
// They check the application flow without real models, not the quality of results.
import { validateExpectation, type Expectation, type ITestCase } from '../testCreation/test-suite.js';
import type { Evaluation, Evaluator } from './exact-match-evaluator.js';
import { fillVariables, type Model, type ModelProvider } from './model.js';

export class MockModel implements Model {
  readonly providerName = 'mock';

  constructor(readonly modelName: string) {}

  async generateResponse(prompt: string, variables: Readonly<Record<string, string>>): Promise<string> {
    return `[mock] ${fillVariables(prompt, variables)}`;
  }
}

export class MockProvider implements ModelProvider {
  readonly providerName = 'mock';

  getModel(modelName: string): Model {
    return new MockModel(modelName);
  }
}

/** Used in place of semantic similarity and LLM judge: every valid expectation scores 1. */
export class MockEvaluator implements Evaluator {
  async evaluate(_test: ITestCase, _output: string, expectation: Expectation): Promise<Evaluation> {
    validateExpectation(expectation);
    return { value: 1, feedback: 'Mock evaluation' };
  }
}
