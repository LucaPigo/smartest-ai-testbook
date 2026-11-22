import { ResponseError } from './generated';

export async function errorMessage(reason: unknown): Promise<string> {
  if (reason instanceof ResponseError) {
    const body = await reason.response.text();
    return `Request failed (${reason.response.status})${body ? `: ${body}` : ''}`;
  }
  return reason instanceof Error ? reason.message : 'The request failed.';
}
