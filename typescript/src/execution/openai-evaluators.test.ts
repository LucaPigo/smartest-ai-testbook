import assert from 'node:assert/strict';
import test from 'node:test';
import OpenAI from 'openai';
import { TestCaseBuilder, TestSuite, type Expectation } from '../testCreation/test-suite.js';
import { EvalRunner } from './eval-runner.js';
import { ExactMatchEvaluator } from './exact-match-evaluator.js';
import { LLMJudgeEvaluator } from './llm-judge-evaluator.js';
import { OpenAIProvider } from './openai-model.js';
import { SemanticSimilarityEvaluator } from './semantic-similarity-evaluator.js';

const exact: Expectation = {
  id: 'exact', name: 'Exact answer', evaluatorType: 'exactMatch', threshold: 1,
  options: { expected: 'Reference' },
};
const semantic: Expectation = { ...exact, id: 'semantic', evaluatorType: 'semanticSimilarity', threshold: 0.5 };
const judge: Expectation = { ...exact, id: 'judge', evaluatorType: 'llmJudge', threshold: 0.8,
  options: { rubric: 'Correct and concise.' } };

function definition(expectations = [exact]) {
  const builder = new TestCaseBuilder().withTitle('Question').withPrompt('Capital of {{country}}?')
    .withVariables({ country: 'France' });
  for (const expectation of expectations) builder.withExpectation(expectation);
  return builder.build();
}

function api({ text = 'Reference', vectors = [[1, 0], [1, 0]], status = 'completed', failure = '',
  indices = [0, 1] }: { text?: string | ((body: Record<string, unknown>) => string);
    vectors?: number[][]; status?: string; failure?: string; indices?: unknown[] } = {}) {
  const requests: Array<{ path: string; body: Record<string, unknown> }> = [];
  const client = new OpenAI({ apiKey: 'offline-key', maxRetries: 0,
    async fetch(input, init) {
      const path = new URL(input instanceof Request ? input.url : String(input)).pathname;
      const body = JSON.parse(String(init?.body));
      requests.push({ path, body });
      const failed = failure === 'generation' && !body.text && path.endsWith('/responses')
        || failure === 'judge' && Boolean(body.text) || failure === 'embeddings' && path.endsWith('/embeddings');
      const data = failed ? { error: { message: 'sentinel-secret-do-not-expose', type: 'server_error' } }
        : path.endsWith('/embeddings') ? { data: vectors.map((embedding, i) => ({ index: indices[i], embedding })) }
          : { object: 'response', status, output: [{ type: 'message', content: [{ type: 'output_text',
            text: typeof text === 'function' ? text(body) : text }] }] };
      return new Response(JSON.stringify(data), { status: failed ? 500 : 200,
        headers: { 'content-type': 'application/json' } });
    },
  });
  return { client, requests };
}

test('provider selects one model and substitutes prompt variables once', async () => {
  const { client, requests } = api({ text: 'Answer' });
  const model = new OpenAIProvider(client).getModel('chosen-model');
  assert.equal(model.providerName, 'openai');
  assert.equal(model.modelName, 'chosen-model');
  assert.equal(await model.generateResponse('Hello {{name}} and {{name}}; {{other}}; {{toString}}',
    { name: '{{other}}', other: 'world' }), 'Answer');
  assert.equal(requests.length, 1);
  assert.equal(requests[0].body.model, 'chosen-model');
  assert.equal(requests[0].body.input, 'Hello {{other}} and {{other}}; world; {{toString}}');
});

test('model rejects incomplete and empty responses', async () => {
  for (const options of [{ text: '' }, { status: 'incomplete', text: 'partial' }]) {
    await assert.rejects(new OpenAIProvider(api(options).client).getModel('model').generateResponse('prompt', {}),
      /incomplete or empty response/i);
  }
});

test('exact matching is literal and evaluators return only score and feedback', async () => {
  const evaluator = new ExactMatchEvaluator();
  for (const output of ['Reference', 'reference', 'Reference ']) {
    const evaluation = await evaluator.evaluate(definition(), output, exact);
    assert.equal(evaluation.value, output === 'Reference' ? 1 : 0);
    assert.deepEqual(Object.keys(evaluation).sort(), ['feedback', 'value']);
  }
});

test('semantic similarity normalizes cosine and reads each local reference by response index', async () => {
  for (const [vectors, expected] of [
    [[[1, 0], [1, 0]], 1], [[[1, 0], [0, 1]], 0.5], [[[1, 0], [-1, 0]], 0],
  ] as const) {
    const { client, requests } = api({ vectors: vectors.map(vector => [...vector]), indices: [1, 0] });
    const evaluator = new SemanticSimilarityEvaluator(client, 'embedding-model');
    for (const reference of ['Reference', 'Another reference']) {
      const evaluation = await evaluator.evaluate(definition(), 'Output', { ...semantic, options: { expected: reference } });
      assert.equal(evaluation.value, expected);
      assert.deepEqual(Object.keys(evaluation).sort(), ['feedback', 'value']);
    }
    assert.deepEqual(requests.map(request => request.body), [
      { model: 'embedding-model', input: ['Reference', 'Output'], encoding_format: 'float' },
      { model: 'embedding-model', input: ['Another reference', 'Output'], encoding_format: 'float' },
    ]);
  }
});

test('semantic similarity rejects missing, duplicate, boolean-index and invalid embeddings', async () => {
  for (const options of [
    { vectors: [[1, 0]] }, { vectors: [[1, 0], [1, 0]], indices: [0, 0] },
    { indices: [0, true] }, { indices: [false, 1] },
    ...[[[0, 0], [1, 1]], [[1], [1, 2]], [[NaN], [1]], [[1], [Infinity]], [[], []]]
      .map(vectors => ({ vectors })),
  ]) {
    await assert.rejects(new SemanticSimilarityEvaluator(api(options).client, 'embed')
      .evaluate(definition(), 'Output', semantic), /invalid embeddings/i);
  }
});

test('judge receives each local rubric, the prompt and variables with a structured score request', async () => {
  const { client, requests } = api({ text: '{"score":0.8,"feedback":"Good"}' });
  const evaluator = new LLMJudgeEvaluator(client, 'judge-model');
  for (const rubric of ['Be correct.', 'Be concise.']) {
    assert.deepEqual(await evaluator.evaluate(definition(), 'Output', { ...judge, options: { rubric } }),
      { value: 0.8, feedback: 'Good' });
  }
  assert.deepEqual(requests.map(request => JSON.parse(String(request.body.input).split('instructions: ')[1])), [
    { prompt: 'Capital of {{country}}?', variables: { country: 'France' }, rubric: 'Be correct.', answer: 'Output' },
    { prompt: 'Capital of {{country}}?', variables: { country: 'France' }, rubric: 'Be concise.', answer: 'Output' },
  ]);
  assert.equal(requests[0].body.model, 'judge-model');
  assert.deepEqual(requests[0].body.text, { format: { type: 'json_schema', name: 'evaluation', strict: true,
    schema: { type: 'object', properties: { score: { type: 'number' }, feedback: { type: 'string' } },
      required: ['score', 'feedback'], additionalProperties: false } } });
});

test('judge rejects malformed structured scores and incomplete responses', async () => {
  for (const text of ['not json', '{}', 'null', '[]', '{"score":true,"feedback":"x"}',
    '{"score":1.1,"feedback":"x"}', '{"score":-0.1,"feedback":"x"}',
    '{"score":0.5,"feedback":" "}', '{"score":0.5,"feedback":"x","extra":1}']) {
    await assert.rejects(new LLMJudgeEvaluator(api({ text }).client, 'judge')
      .evaluate(definition(), 'Output', judge), /invalid judge response/i);
  }
  await assert.rejects(new LLMJudgeEvaluator(api({ status: 'incomplete', text: '{"score":1,"feedback":"Good"}' }).client,
    'judge').evaluate(definition(), 'Output', judge), /invalid judge response/i);
});

test('all strategies evaluate one generated response and SDK errors remain isolated and sanitized', async () => {
  for (const failure of ['', 'generation', 'embeddings', 'judge']) {
    const { client, requests } = api({ failure, text: body => body.text ? '{"score":0.8,"feedback":"Good"}' : 'Reference' });
    const suite = new TestSuite('All strategies');
    suite.addTest(definition([semantic, judge, exact]));
    const run = await new EvalRunner({ exactMatch: new ExactMatchEvaluator(),
      semanticSimilarity: new SemanticSimilarityEvaluator(client, 'embed'), llmJudge: new LLMJudgeEvaluator(client, 'judge') })
      .run(suite, new OpenAIProvider(client).getModel('chosen-model'));
    const result = run.results[0];
    assert.equal(requests.filter(request => request.path.endsWith('/responses') && !request.body.text).length, 1);
    assert.equal(result.passed, failure === '');
    if (failure === 'generation') {
      assert.equal(result.error, 'OpenAI request failed.');
      assert.deepEqual(result.scores, []);
    } else {
      assert.equal(result.scores.length, 3);
      assert.equal(result.scores[2].passed, true);
      const failed = failure === 'embeddings' ? result.scores[0] : failure === 'judge' ? result.scores[1] : undefined;
      if (failed) assert.equal(failed.error, 'OpenAI request failed.');
    }
    assert.equal(JSON.stringify(run).includes('sentinel-secret-do-not-expose'), false);
  }
});
