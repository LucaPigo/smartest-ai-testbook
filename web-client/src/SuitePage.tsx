import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Link, useNavigate, useOutletContext, useParams } from 'react-router';
import { PageTitle, SuiteNavigation } from './App';
import { errorMessage } from './errors';
import { ExpectationForm, TestForm, type TestFormValue } from './TestForm';
import type { TestSuite, TestSuiteInput } from './generated';
import type { AppContext } from './types';

export function SuiteList() {
  const { api, suites, loaded, refreshSuites } = useOutletContext<AppContext>();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function remove(suite: TestSuite) {
    if (!window.confirm('Delete this suite and its run history?')) return;
    setBusy(true); setError('');
    try { await api.tests.deleteTestSuite({ suiteId: suite.id }); await refreshSuites(); }
    catch (reason) { setError(await errorMessage(reason)); }
    finally { setBusy(false); }
  }

  return <section>
    <h2>Test suites</h2>
    {error && <p role="alert" className="error">{error}</p>}
    {!loaded ? <p>Loading suites…</p> : suites.length ? <ul className="item-list">{suites.map(suite => <li key={suite.id} className="item-row">
      <Link to={`/test-suites/${suite.id}`}><strong>{suite.name}</strong></Link>
      <span className="muted">{suite.tests.length} {suite.tests.length === 1 ? 'test' : 'tests'}</span>
      <div className="actions"><Link to={`/test-suites/${suite.id}`}>Edit</Link><Link to={`/execute/${suite.id}`}>Run</Link>
        <button type="button" className="link-button" disabled={busy} onClick={() => void remove(suite)}>Delete</button></div>
    </li>)}</ul> : <p>No suites yet.</p>}
    <p className="add"><Link to="/test-suites/new" aria-label="New suite" title="New suite">⊕</Link></p>
  </section>;
}

function SuiteForm({ suite, submitLabel, onSave, onCancel }: {
  suite?: TestSuite;
  submitLabel: string;
  onSave: (value: TestSuiteInput) => Promise<void>;
  onCancel?: () => void;
}) {
  const [name, setName] = useState(suite?.name ?? '');
  const [description, setDescription] = useState(suite?.description ?? '');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError('');
    try { await onSave({ name, description }); }
    catch (reason) { setError(await errorMessage(reason)); }
    finally { setBusy(false); }
  }
  return <form onSubmit={event => void submit(event)}>
    {error && <p role="alert" className="error">{error}</p>}
    <label>Name <input required value={name} onChange={e => setName(e.target.value)} /></label>
    <label>Description <textarea value={description} onChange={e => setDescription(e.target.value)} /></label>
    <button disabled={busy}>{submitLabel}</button>
    {onCancel && <button type="button" className="secondary" onClick={onCancel}>Cancel</button>}
  </form>;
}

export function SuiteNewPage() {
  const { api, refreshSuites } = useOutletContext<AppContext>();
  const navigate = useNavigate();
  const active = useRef(false);
  useEffect(() => { active.current = true; return () => { active.current = false; }; }, []);
  async function create(value: TestSuiteInput) {
    const suite = await api.tests.createTestSuite({ testSuiteInput: value });
    await refreshSuites();
    if (active.current) navigate(`/test-suites/${suite.id}`);
  }
  return <section>
    <PageTitle back="/test-suites" title="New suite" />
    <SuiteForm submitLabel="Create suite" onSave={create} onCancel={() => navigate('/test-suites')} />
  </section>;
}

export function SuitePage() {
  const { suiteId } = useParams();
  const { suites, loaded } = useOutletContext<AppContext>();
  const suite = suites.find(item => item.id === suiteId);
  if (!suite) return loaded ? <p role="alert">Suite not found.</p> : <p>Loading suite…</p>;
  return <SuiteEditor key={suite.id} suite={suite} />;
}

function SuiteEditor({ suite }: { suite: TestSuite }) {
  const { api, refreshSuites } = useOutletContext<AppContext>();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function save(value: TestSuiteInput) {
    await api.tests.updateTestSuite({ suiteId: suite.id, testSuiteInput: value });
    await refreshSuites();
  }
  async function removeTest(caseId: string) {
    if (!window.confirm('Delete this test?')) return;
    setBusy(true); setError('');
    try { await api.tests.deleteTestCase({ caseId }); await refreshSuites(); }
    catch (reason) { setError(await errorMessage(reason)); }
    finally { setBusy(false); }
  }
  return <>
    <SuiteNavigation suiteId={suite.id} current="define" />
    <PageTitle back="/test-suites" title={suite.name} />
    <section>
      {error && <p role="alert" className="error">{error}</p>}
      <SuiteForm suite={suite} submitLabel="Save suite" onSave={save} />
      <h3>Tests</h3>
      {suite.tests.length ? <ul className="item-list">{suite.tests.map(test => <li key={test.id} className="item-row">
        <span className="test-prompt">{test.title}</span>
        <span className="muted">{test.expectations.length} expectation(s)</span>
        <div className="actions"><Link to={`/test-cases/${test.id}`}>Edit test</Link>
          <button type="button" className="link-button" disabled={busy} onClick={() => void removeTest(test.id)}>Delete test</button></div>
      </li>)}</ul> : <p>No tests yet.</p>}
      <p className="add"><Link to={`/test-suites/${suite.id}/test-cases/new`} aria-label="Add test" title="Add test">⊕</Link></p>
    </section>
  </>;
}

export function TestPage() {
  const { suiteId, caseId } = useParams();
  const { api, suites, loaded, refreshSuites } = useOutletContext<AppContext>();
  const navigate = useNavigate();
  const [adding, setAdding] = useState(false);
  const active = useRef(false);
  useEffect(() => { active.current = true; return () => { active.current = false; }; }, [caseId, suiteId]);
  const suite = caseId ? suites.find(item => item.tests.some(test => test.id === caseId)) : suites.find(item => item.id === suiteId);
  const test = suite?.tests.find(item => item.id === caseId);
  if (!suite || (caseId && !test)) return loaded ? <p role="alert">Test or suite not found.</p> : <p>Loading test…</p>;

  async function save(value: TestFormValue) {
    if (!suite) return;
    if (test) await api.tests.updateTestCase({ caseId: test.id, testCaseInput: {
      ...value, expectations: value.expectations.map(expectation => ({ ...expectation, id: expectation.id! })),
    } });
    else await api.tests.createTestCase({ createTestCaseInput: { suiteId: suite.id, ...value } });
    await refreshSuites();
    if (active.current) navigate(`/test-suites/${suite.id}`);
  }

  return <>
    <SuiteNavigation suiteId={suite.id} current="define" />
    <PageTitle back={`/test-suites/${suite.id}`} title={test ? `${suite.name} / ${test.title}` : `${suite.name} / New test`} />
    <section>
      <TestForm key={test ? `${test.id}-${test.expectations.map(item => item.id).join(',')}` : 'new'} test={test} onSave={save} onCancel={() => navigate(`/test-suites/${suite.id}`)} />
      {test && !adding && <button type="button" className="secondary" onClick={() => setAdding(true)}>Add expectation</button>}
      {test && adding && <ExpectationForm onCancel={() => setAdding(false)} onSave={async value => {
        await api.tests.createExpectation({ createExpectationInput: { ...value, testCaseId: test.id } });
        await refreshSuites(); setAdding(false);
      }} />}
    </section>
  </>;
}
