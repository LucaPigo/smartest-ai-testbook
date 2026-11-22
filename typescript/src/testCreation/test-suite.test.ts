import assert from 'node:assert/strict';
import test from 'node:test';
import { TestCaseBuilder, TestSuite, type Expectation } from './test-suite.js';

const expectation: Expectation = {
  id: 'exact', name: 'Exact answer', evaluatorType: 'exactMatch', threshold: 1, options: { expected: 'Paris' },
};

test('builds a test and adds it to a suite with separate identities', () => {
  const builder = new TestCaseBuilder()
    .withTitle('Capital city')
    .withPrompt('Return exactly: Paris')
    .withExpectation(expectation);
  const first = builder.build();
  const second = builder.build();
  const suite = new TestSuite('Basic answers', 'A deterministic example');
  suite.addTest(first);

  assert.match(first.id, /^[0-9a-f-]{36}$/);
  assert.match(suite.id, /^[0-9a-f-]{36}$/);
  assert.notEqual(first.id, second.id);
  assert.equal(first.title, 'Capital city');
  assert.equal(first.prompt, 'Return exactly: Paris');
  assert.equal('goldenReference' in first, false);
  assert.equal('rubric' in first, false);
  assert.deepEqual(first.variables, {});
  assert.deepEqual(first.expectations, [expectation]);
  builder.withExpectation({ ...expectation, id: 'another' });
  assert.equal(first.expectations.length, 1);
  assert.deepEqual(suite.tests, [first]);
});

test('rejects a blank title, blank prompt and missing expectations', () => {
  assert.throws(() => new TestCaseBuilder().withTitle(' ').build(), /title/i);
  assert.throws(() => new TestCaseBuilder().withTitle('Title').withPrompt('  ').build(), /prompt/i);
  assert.throws(() => new TestCaseBuilder().withTitle('Title').withPrompt('Hello').build(), /expectation/i);
});

test('copies optional variables and allows independent criteria', () => {
  const variables = { country: 'France' };
  const definition = new TestCaseBuilder().withTitle('Capital').withPrompt('{{country}}')
    .withVariables(variables).withExpectation(expectation)
    .withExpectation({ ...expectation, id: 'semantic', evaluatorType: 'semanticSimilarity', threshold: 0.8,
      options: { expected: 'The capital is Paris.' } })
    .withExpectation({ ...expectation, id: 'judge', evaluatorType: 'llmJudge', threshold: 0.8,
      options: { rubric: 'Be concise.' } }).build();
  variables.country = 'Italy';
  assert.deepEqual(definition.variables, { country: 'France' });
  assert.deepEqual(definition.expectations.map(item => item.options), [
    { expected: 'Paris' }, { expected: 'The capital is Paris.' }, { rubric: 'Be concise.' },
  ]);
});

test('rejects invalid evaluator definitions before building a test', () => {
  const invalid: Array<Partial<Expectation>> = [
    { name: ' ' }, { evaluatorType: 'unknown' }, { evaluatorType: 'toString' },
    ...[NaN, Infinity, -Infinity, -0.1, 1.1].map(threshold => ({ threshold })),
    { threshold: 0 }, { options: {} }, { options: { expected: '' } },
    { options: { expected: ' ' } }, { options: { expected: 42 } },
    { options: { expected: 'Paris', normalize: true } },
    { evaluatorType: 'semanticSimilarity', options: { rubric: 'Correct.' } },
    { evaluatorType: 'llmJudge', options: { expected: 'Paris' } },
    { evaluatorType: 'llmJudge', options: { rubric: ' ' } },
  ];
  for (const changes of invalid) {
    assert.throws(() => new TestCaseBuilder().withTitle('Test').withPrompt('Question')
      .withExpectation({ ...expectation, ...changes }).build());
  }
});
