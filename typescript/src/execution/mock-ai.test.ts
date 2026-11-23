import assert from 'node:assert/strict';
import test from 'node:test';
import { TestCaseBuilder, TestSuite, type Expectation } from '../testCreation/test-suite.js';
import { EvalRunner } from './eval-runner.js';
import { ExactMatchEvaluator } from './exact-match-evaluator.js';
import { MockEvaluator, MockProvider } from './mock-ai.js';

const exact: Expectation = {
  id: 'exact', name: 'Exact answer', evaluatorType: 'exactMatch', threshold: 1, options: { expected: 'Paris' },
};
const semantic: Expectation = { ...exact, id: 'semantic', name: 'Similar', evaluatorType: 'semanticSimilarity',
  threshold: 0.8 };
const judge: Expectation = { ...exact, id: 'judge', name: 'Judge', evaluatorType: 'llmJudge', threshold: 0.9,
  options: { rubric: 'Names the capital.' } };

test('the mock model answers with the filled prompt and reports its identity', async () => {
  const provider = new MockProvider();
  const model = provider.getModel('demo');
  assert.equal(provider.providerName, 'mock');
  assert.equal(model.providerName, 'mock');
  assert.equal(model.modelName, 'demo');
  assert.equal(await model.generateResponse('Capital of {{country}}? {{unknown}}', { country: 'France' }),
    '[mock] Capital of France? {{unknown}}');
});

test('the mock evaluator validates the expectation and always scores 1', async () => {
  const definition = new TestCaseBuilder().withTitle('Test').withPrompt('Prompt').withExpectation(semantic).build();
  const evaluator = new MockEvaluator();
  assert.deepEqual(await evaluator.evaluate(definition, 'any output', judge), { value: 1, feedback: 'Mock evaluation' });
  await assert.rejects(evaluator.evaluate(definition, 'any output', { ...judge, options: {} }), /rubric/);
});

test('a mock run evaluates AI expectations with the mock and exact match for real', async () => {
  const suite = new TestSuite('Mock suite');
  suite.addTest(new TestCaseBuilder().withTitle('Capital').withPrompt('Capital of {{country}}?')
    .withVariables({ country: 'France' })
    .withExpectation(exact).withExpectation(semantic).withExpectation(judge).build());
  const mock = new MockEvaluator();
  const runner = new EvalRunner({ exactMatch: new ExactMatchEvaluator(), semanticSimilarity: mock, llmJudge: mock });

  const run = await runner.run(suite, new MockProvider().getModel('demo'));

  assert.equal(run.providerName, 'mock');
  assert.equal(run.modelName, 'demo');
  const [result] = run.results;
  assert.equal(result.output, '[mock] Capital of France?');
  assert.deepEqual(result.scores.map(score => [score.expectationId, score.value, score.passed]),
    [['exact', 0, false], ['semantic', 1, true], ['judge', 1, true]]);
  assert.equal(result.scores[1].feedback, 'Mock evaluation');
  assert.deepEqual([result.scores[1].scaleMin, result.scores[1].scaleMax], [0, 1]);
  assert.equal(result.passed, false);
});
