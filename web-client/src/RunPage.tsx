import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Link, useNavigate, useOutletContext, useParams } from 'react-router';
import { PageTitle, SuiteNavigation } from './App';
import { errorMessage } from './errors';
import type { EvalRun } from './generated';
import type { AppContext } from './types';

export function RunPage() {
  const { suiteId } = useParams();
  const { api, suites, loaded } = useOutletContext<AppContext>();
  const suite = suites.find(item => item.id === suiteId);
  const [runs, setRuns] = useState<EvalRun[]>();
  const [error, setError] = useState('');

  useEffect(() => {
    let current = true;
    setRuns(undefined); setError('');
    if (suiteId) api.execution.listSuiteEvalRuns({ suiteId })
      .then(items => { if (current) setRuns(items); })
      .catch(async reason => { const message = await errorMessage(reason); if (current) setError(message); });
    return () => { current = false; };
  }, [api, suiteId]);

  if (!suite) return loaded ? <p role="alert">Suite not found.</p> : <p>Loading suite…</p>;
  return <>
    <SuiteNavigation suiteId={suite.id} current="execute" />
    <PageTitle back="/test-suites" title={suite.name} />
    <section>
      {error && <p role="alert" className="error">{error}</p>}
      <p className="add"><Link className="play" to={`/execute/${suite.id}/run`} aria-label="New run" title="New run">▶</Link></p>
      <h3>Reports</h3>
      {!runs ? <p>Loading runs…</p> : runs.length ? <ul className="item-list">{runs.map(run => {
        const passed = run.results.filter(result => result.passed).length;
        return <li key={run.id} className="item-row"><Link to={`/reports/${run.id}`}>{new Date(run.startedAt).toLocaleString()} — {run.providerName} / {run.modelName}</Link>
          <span>{passed}/{run.results.length} passed {passed === run.results.length ? '✓' : '⚠'}</span></li>;
      })}</ul> : <p>No runs yet.</p>}
    </section>
  </>;
}

export function RunConfigPage() {
  const { suiteId } = useParams();
  const { api, suites, loaded } = useOutletContext<AppContext>();
  const suite = suites.find(item => item.id === suiteId);
  const [provider, setProvider] = useState('openai');
  const [model, setModel] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const active = useRef(false);
  useEffect(() => { active.current = true; return () => { active.current = false; }; }, [suiteId]);

  async function start(event: FormEvent) {
    event.preventDefault();
    if (!suiteId) return;
    setBusy(true); setError('');
    try {
      const run = await api.execution.createEvalRun({ suiteId, evalRunInput: { providerName: provider, modelName: model } });
      if (active.current) navigate(`/reports/${run.id}`);
    } catch (reason) { const message = await errorMessage(reason); if (active.current) setError(message); }
    finally { if (active.current) setBusy(false); }
  }

  if (!suite) return loaded ? <p role="alert">Suite not found.</p> : <p>Loading suite…</p>;
  return <>
    <SuiteNavigation suiteId={suite.id} current="execute" />
    <PageTitle back={`/execute/${suite.id}`} title={suite.name} />
    <section>
      {error && <p role="alert" className="error">{error}</p>}
      <form onSubmit={event => void start(event)}>
        <label>Provider <select value={provider} onChange={e => setProvider(e.target.value)}>
          <option value="openai">OpenAI</option>
          <option value="mock">Mock</option>
        </select></label>
        <fieldset>
          <legend>Configure model provider</legend>
          <label>Model <input required value={model} onChange={e => setModel(e.target.value)} placeholder="Model name" /></label>
        </fieldset>
        <p className="add"><button className="play" disabled={busy} aria-label="Start run" title="Start run">{busy ? '…' : '▶'}</button></p>
      </form>
    </section>
  </>;
}

export function ReportPage() {
  const { runId } = useParams();
  const { api, suites } = useOutletContext<AppContext>();
  const [run, setRun] = useState<EvalRun>();
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    setRun(undefined); setError('');
    if (runId) api.reporting.getEvalRun({ evalRunId: runId }).then(result => {
      if (active) setRun(result);
    }).catch(async reason => { const message = await errorMessage(reason); if (active) setError(message); });
    return () => { active = false; };
  }, [api, runId]);
  if (error) return <p role="alert" className="error">{error}</p>;
  if (!run) return <p>Loading report…</p>;
  const suite = suites.find(item => item.id === run.suiteId);
  const passed = run.results.filter(result => result.passed).length;
  return <>
    <SuiteNavigation suiteId={run.suiteId} current="report" />
    <PageTitle back={`/execute/${run.suiteId}`} title={`${suite?.name ?? 'Suite report'} / detail`}
      aside={new Date(run.startedAt).toLocaleString()} />
    <section>
      <p className="muted">{run.providerName} / {run.modelName}</p>
      <div className="summary" aria-label="Run summary">
        <div><strong>{run.results.length}</strong><span>Tests</span></div>
        <div><strong>{passed}</strong><span>Passed</span></div>
        <div><strong>{run.results.length - passed}</strong><span>Failed</span></div>
      </div>
      {run.results.length === 0 && <p>No test results.</p>}
      {run.results.map((result, index) => <details key={`${result.testId}-${index}`}>
        <summary>{result.passed ? '✓' : '⚠'} {result.passed ? 'Passed' : 'Failed'} — {result.prompt}</summary>
        <p><strong>Prompt</strong></p><pre>{result.prompt}</pre>
        {result.error ? <p className="error">{result.error}</p> : <><p><strong>Output</strong></p><pre>{result.output}</pre></>}
        {result.scores.map((score, i) => <div key={`${score.expectationId}-${i}`}>
          <p><strong>{score.expectationName ?? 'Expectation'}</strong> ({score.evaluatorType}) — {score.passed ? 'Passed' : 'Failed'}</p>
          <p>Score: {score.value ?? '—'} {score.scaleMin != null && score.scaleMax != null && `(${score.scaleMin}–${score.scaleMax})`} · Threshold: {score.threshold ?? '—'}</p>
          {score.error && <p className="error">{score.error}</p>}<p>{score.feedback}</p>
        </div>)}
      </details>)}
    </section>
  </>;
}
