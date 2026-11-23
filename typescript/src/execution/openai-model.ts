import OpenAI, { OpenAIError } from 'openai';
import { fillVariables, type Model, type ModelProvider } from './model.js';

export class OpenAIModel implements Model {
  readonly providerName = 'openai';

  constructor(private readonly client: OpenAI, readonly modelName: string) {}

  async generateResponse(prompt: string, variables: Readonly<Record<string, string>>): Promise<string> {
    const input = fillVariables(prompt, variables);
    let response;
    try {
      response = await this.client.responses.create({ model: this.modelName, input });
    } catch (error) {
      if (error instanceof OpenAIError) throw new Error('OpenAI request failed.');
      throw error;
    }
    if (response.status !== 'completed' || typeof response.output_text !== 'string' || !response.output_text) {
      throw new Error('OpenAI returned an incomplete or empty response.');
    }
    return response.output_text;
  }
}

export class OpenAIProvider implements ModelProvider {
  readonly providerName = 'openai';

  constructor(private readonly client: OpenAI) {}

  getModel(modelName: string): Model {
    return new OpenAIModel(this.client, modelName);
  }
}
