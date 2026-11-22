import { validateExpectation, type Expectation, type ITestCase } from '../testCreation/test-suite.js';

export interface Evaluation {
  value: number;
  feedback: string;
}

export interface Evaluator {
  evaluate(test: ITestCase, output: string, expectation: Expectation): Promise<Evaluation>;
}

export class ExactMatchEvaluator implements Evaluator {
  async evaluate(_test: ITestCase, output: string, expectation: Expectation): Promise<Evaluation> {
    const value = output === validateExpectation(expectation) ? 1 : 0;
    return {
      value,
      feedback: value === 1
        ? 'Output matches the expected answer.'
        : 'Output does not match the expected answer.',
    };
  }
}
