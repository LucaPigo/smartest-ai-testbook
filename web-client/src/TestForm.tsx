import { useState, type FormEvent } from 'react';
import type { ExpectationInput, TestCase } from './generated';
import { errorMessage } from './errors';

type ExpectationForm = { id?: string; name: string; evaluatorType: ExpectationInput['evaluatorType']; threshold: string; criterion: string };
type VariableForm = { name: string; value: string };
export type TestFormValue = {
  title: string;
  prompt: string;
  variables: Record<string, string>;
  expectations: (ExpectationInput & { id?: string })[];
};

const emptyExpectation = (): ExpectationForm => ({ name: '', evaluatorType: 'exactMatch', threshold: '1', criterion: '' });

function expectationInput(value: ExpectationForm): ExpectationInput & { id?: string } {
  if (!value.name.trim()) throw new Error('Each expectation needs a name.');
  if (!value.criterion.trim()) throw new Error('Each expectation needs an expected answer or rubric.');
  const threshold = Number(value.threshold);
  if (!value.threshold.trim() || !Number.isFinite(threshold) || threshold < 0 || threshold > 1) {
    throw new Error('Each threshold must be between 0 and 1.');
  }
  return {
    id: value.id,
    name: value.name,
    evaluatorType: value.evaluatorType,
    threshold: value.evaluatorType === 'exactMatch' ? 1 : threshold,
    options: value.evaluatorType === 'llmJudge' ? { rubric: value.criterion } : { expected: value.criterion },
  };
}

function ExpectationFields({ value, onChange }: {
  value: ExpectationForm;
  onChange: (changes: Partial<ExpectationForm>) => void;
}) {
  return <>
    <label>Name <input required value={value.name} onChange={e => onChange({ name: e.target.value })} /></label>
    <label>Evaluator <select value={value.evaluatorType} onChange={e => onChange({
      evaluatorType: e.target.value as ExpectationInput['evaluatorType'],
      threshold: e.target.value === 'exactMatch' ? '1' : '0.8',
      criterion: '',
    })}>
      <option value="exactMatch">Exact match</option>
      <option value="semanticSimilarity">Semantic similarity</option>
      <option value="llmJudge">LLM judge</option>
    </select></label>
    <label>Threshold <input required type="number" min="0" max="1" step="any" readOnly={value.evaluatorType === 'exactMatch'} value={value.threshold} onChange={e => onChange({ threshold: e.target.value })} /></label>
    <label>{value.evaluatorType === 'llmJudge' ? 'Rubric' : 'Expected answer'} <textarea required value={value.criterion} onChange={e => onChange({ criterion: e.target.value })} /></label>
  </>;
}

export function TestForm({ test, onSave, onCancel }: {
  test?: TestCase;
  onSave: (value: TestFormValue) => Promise<void>;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState(test?.title ?? '');
  const [prompt, setPrompt] = useState(test?.prompt ?? '');
  const [variables, setVariables] = useState<VariableForm[]>(
    Object.entries(test?.variables ?? {}).map(([name, value]) => ({ name, value })),
  );
  const [expectations, setExpectations] = useState<ExpectationForm[]>(test?.expectations.map(e => ({
    id: e.id,
    name: e.name,
    evaluatorType: e.evaluatorType,
    threshold: e.evaluatorType === 'exactMatch' ? '1' : String(e.threshold),
    criterion: String(e.options[e.evaluatorType === 'llmJudge' ? 'rubric' : 'expected'] ?? ''),
  })) ?? [emptyExpectation()]);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  function changeExpectation(index: number, values: Partial<ExpectationForm>) {
    setExpectations(current => current.map((item, i) => i === index ? { ...item, ...values } : item));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    try {
      if (!title.trim()) throw new Error('A test title is required.');
      if (new Set(variables.map(variable => variable.name)).size !== variables.length) {
        throw new Error('Variable names must be unique.');
      }
      const parsedVariables = Object.fromEntries(variables.map(({ name, value }) => [name, value]));
      if (!expectations.length) throw new Error('Add at least one expectation.');
      const parsedExpectations = expectations.map(expectationInput);
      setSaving(true);
      await onSave({
        title,
        prompt,
        variables: parsedVariables,
        expectations: parsedExpectations,
      });
    } catch (reason) {
      setError(await errorMessage(reason));
    } finally {
      setSaving(false);
    }
  }

  return <form onSubmit={event => void submit(event)}>
    <div className="form-bar">
      <h3>{test ? 'Edit test' : 'New test'}</h3>
      <div>
        <button disabled={saving} type="submit">{saving ? 'Saving…' : 'Save test'}</button>
        <button className="secondary" type="button" onClick={onCancel}>Cancel</button>
      </div>
    </div>
    {error && <p role="alert" className="error">{error}</p>}
    <div className="two-columns">
    <div>
    <label>Title <input required value={title} onChange={e => setTitle(e.target.value)} /></label>
    <label>Prompt <textarea required value={prompt} onChange={e => setPrompt(e.target.value)} /></label>
    <h3>Variables</h3>
    {variables.map((variable, index) => <fieldset key={index}>
      <legend>Variable {index + 1}</legend>
      <label>Name <input required value={variable.name} onChange={e => setVariables(current => current.map((item, i) => i === index ? { ...item, name: e.target.value } : item))} /></label>
      <label>Value <input value={variable.value} onChange={e => setVariables(current => current.map((item, i) => i === index ? { ...item, value: e.target.value } : item))} /></label>
      <button type="button" className="secondary" onClick={() => setVariables(current => current.filter((_, i) => i !== index))}>Remove variable</button>
    </fieldset>)}
    <button type="button" className="secondary" onClick={() => setVariables(current => [...current, { name: '', value: '' }])}>Add variable</button>
    </div>
    <div>
    <h3>Expectations</h3>
    {expectations.map((expectation, index) => <fieldset key={index}>
      <legend>Expectation {index + 1}</legend>
      <ExpectationFields value={expectation} onChange={changes => changeExpectation(index, changes)} />
      <button type="button" className="secondary" onClick={() => setExpectations(current => current.filter((_, i) => i !== index))}>Remove expectation</button>
    </fieldset>)}
    {!test && <button type="button" className="secondary" onClick={() => setExpectations(current => [...current, emptyExpectation()])}>Add expectation</button>}
    </div>
    </div>
  </form>;
}


export function ExpectationForm({ onSave, onCancel }: {
  onSave: (value: ExpectationInput) => Promise<void>;
  onCancel: () => void;
}) {
  const [value, setValue] = useState(emptyExpectation());
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    try {
      const expectation = expectationInput(value);
      setSaving(true);
      await onSave(expectation);
    } catch (reason) {
      setError(await errorMessage(reason));
    } finally {
      setSaving(false);
    }
  }
  return <form onSubmit={event => void submit(event)}>
    <h3>New expectation</h3>
    <ExpectationFields value={value} onChange={changes => setValue({ ...value, ...changes })} />
    {error && <p role="alert" className="error">{error}</p>}
    <button disabled={saving} type="submit">{saving ? 'Saving…' : 'Save expectation'}</button>
    <button type="button" className="secondary" onClick={onCancel}>Cancel</button>
  </form>;
}

