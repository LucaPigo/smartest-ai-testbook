import OpenAI, { OpenAIError } from 'openai';
import { validateExpectation, type Expectation, type ITestCase } from '../testCreation/test-suite.js';
import type { Evaluation, Evaluator } from './exact-match-evaluator.js';

/** Cosine similarity normalized from [-1, 1] to the [0, 1] score scale. */
export class SemanticSimilarityEvaluator implements Evaluator {
  constructor(private readonly client: OpenAI, private readonly embeddingModel: string) {}

  async evaluate(_test: ITestCase, output: string, expectation: Expectation): Promise<Evaluation> {
    const expected = validateExpectation(expectation);
    let response;
    try {
      response = await this.client.embeddings.create({
        model: this.embeddingModel, input: [expected, output], encoding_format: 'float',
      });
    } catch (error) {
      if (error instanceof OpenAIError) throw new Error('OpenAI request failed.');
      throw error;
    }
    let cosine: number;
    try {
      const vectors = new Map(response.data.map(item => [item.index, item.embedding]));
      const first = vectors.get(0);
      const second = vectors.get(1);
      if (response.data.length !== 2 || vectors.size !== 2 || !first?.length || !second
        || first.length !== second.length
        || [...first, ...second].some(value => typeof value !== 'number' || !Number.isFinite(value))) {
        throw new Error();
      }
      const firstNorm = Math.hypot(...first);
      const secondNorm = Math.hypot(...second);
      if (!firstNorm || !secondNorm || !Number.isFinite(firstNorm) || !Number.isFinite(secondNorm)) {
        throw new Error();
      }
      cosine = first.reduce((sum, value, i) => sum + (value / firstNorm) * (second[i] / secondNorm), 0);
    } catch {
      throw new Error('OpenAI returned invalid embeddings.');
    }
    return { value: (Math.max(-1, Math.min(1, cosine)) + 1) / 2,
      feedback: 'Similarity to the reference answer.' };
  }
}
