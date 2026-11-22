import { randomUUID } from 'node:crypto';

export interface Expectation {
  /** Stable identifier used to link this check to its recorded score. */
  id: string;
  /** Human-readable label shown when reviewing the result. */
  name: string;
  /** Key that selects the evaluator algorithm for this check. */
  evaluatorType: string;
  /** Minimum score required to pass on the fixed 0–1 scale. */
  threshold: number;
  /** One expected answer for exact/semantic checks, or a rubric for a judge. */
  options: Record<string, unknown>;
}

export function validateExpectation(expectation: Expectation): string {
  if (typeof expectation.name !== 'string' || !expectation.name.trim()) {
    throw new Error('An expectation needs a name.');
  }
  if (!['exactMatch', 'semanticSimilarity', 'llmJudge'].includes(expectation.evaluatorType)) {
    throw new Error(`Unknown evaluator type: ${expectation.evaluatorType}`);
  }
  const threshold = expectation.threshold;
  if (typeof threshold !== 'number' || !Number.isFinite(threshold) || threshold < 0 || threshold > 1) {
    throw new Error('An expectation threshold must be a finite number from 0 to 1.');
  }
  if (expectation.evaluatorType === 'exactMatch' && threshold !== 1) {
    throw new Error('Exact match requires threshold 1.');
  }
  const key = expectation.evaluatorType === 'llmJudge' ? 'rubric' : 'expected';
  const options = expectation.options;
  if (!options || typeof options !== 'object' || Array.isArray(options)
    || Object.keys(options).length !== 1 || !Object.hasOwn(options, key)
    || typeof options[key] !== 'string' || !options[key].trim()) {
    throw new Error(`${expectation.evaluatorType} options must contain only a nonblank ${key} string.`);
  }
  return options[key];
}

export interface ITestCase {
  /** Stable identifier used to associate the test with its results. */
  readonly id: string;
  readonly title: string;
  /** Instruction sent to the model, potentially containing placeholders. */
  readonly prompt: string;
  /** Named values supplied for placeholders in the prompt. */
  readonly variables: Record<string, string>;
  /** Checks configured to evaluate the model response. */
  readonly expectations: Expectation[];
}

export interface ITestSuite {
  readonly id: string;
  readonly name: string;
  readonly description: string;
  readonly tests: ITestCase[];
  addTest(test: ITestCase): void;
}

export interface ITestCaseBuilder {
  withTitle(title: string): ITestCaseBuilder;
  withPrompt(prompt: string): ITestCaseBuilder;
  withVariables(variables: Record<string, string>): ITestCaseBuilder;
  withExpectation(expectation: Expectation): ITestCaseBuilder;
  build(): ITestCase;
}

class TestCase implements ITestCase {
  readonly id = randomUUID();
  constructor(
    readonly title: string,
    readonly prompt: string,
    readonly variables: Record<string, string>,
    readonly expectations: Expectation[],
  ) {}
}

export class TestCaseBuilder implements ITestCaseBuilder {
  private title = '';
  private prompt = '';
  private variables: Record<string, string> = {};
  private expectations: Expectation[] = [];

  withTitle(title: string): ITestCaseBuilder {
    this.title = title;
    return this;
  }

  withPrompt(prompt: string): ITestCaseBuilder {
    this.prompt = prompt;
    return this;
  }

  withVariables(variables: Record<string, string>): ITestCaseBuilder {
    this.variables = variables;
    return this;
  }

  withExpectation(expectation: Expectation): ITestCaseBuilder {
    this.expectations.push(expectation);
    return this;
  }

  build(): ITestCase {
    if (!this.title.trim()) throw new Error('A test needs a title.');
    if (!this.prompt.trim()) throw new Error('A test needs a prompt.');
    if (this.expectations.length === 0) throw new Error('A test needs an expectation.');
    for (const expectation of this.expectations) validateExpectation(expectation);
    return new TestCase(this.title, this.prompt, { ...this.variables },
      this.expectations.map(expectation => ({ ...expectation, options: { ...expectation.options } })));
  }
}

export class TestSuite implements ITestSuite {
  readonly id = randomUUID();
  readonly tests: ITestCase[] = [];

  constructor(readonly name: string, readonly description = '') {}

  addTest(test: ITestCase): void {
    this.tests.push(test);
  }
}
