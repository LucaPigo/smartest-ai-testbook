export interface Model {
  readonly providerName: string;
  readonly modelName: string;
  generateResponse(
    prompt: string,
    variables: Readonly<Record<string, string>>,
  ): Promise<string>;
}

export interface ModelProvider {
  readonly providerName: string;
  getModel(modelName: string): Model;
}

/** Replace each `{{name}}` placeholder with its variable; unknown placeholders stay unchanged. */
export function fillVariables(prompt: string, variables: Readonly<Record<string, string>>): string {
  return prompt.replace(/\{\{\s*([^{}]+?)\s*\}\}/g,
    (match, name: string) => Object.hasOwn(variables, name) ? variables[name] : match);
}
