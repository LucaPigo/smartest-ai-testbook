import { useEffect, useState } from 'react';
import { Link, Outlet } from 'react-router';
import { Configuration, HealthApi, TestCreationApi, ExecutionApi, ReportingApi, type TestSuite } from './generated';
import { errorMessage } from './errors';
import type { Api, AppContext } from './types';

export function App() {
  const [api, setApi] = useState<Api>();
  const [connection, setConnection] = useState('Loading application configuration…');
  const [error, setError] = useState('');
  const [suites, setSuites] = useState<TestSuite[]>([]);
  const [loaded, setLoaded] = useState(false);

  async function checkConnection(client: Api) {
    setConnection('Checking connection…');
    try {
      const health = await client.health.getHealth({ signal: AbortSignal.timeout(5000) });
      if (health.status !== 'ok') throw new Error('Invalid health response');
      setConnection('Backend connected.');
      try {
        setSuites(await client.tests.listTestSuites());
        setLoaded(true);
        setError('');
      } catch (reason) { setError(await errorMessage(reason)); }
    } catch { setConnection('Could not connect to the backend. Try again.'); }
  }

  useEffect(() => {
    const configurationUrl = new URL('/configuration.js', window.location.origin).href;
    import(/* @vite-ignore */ configurationUrl).then(({ apiBaseUrl }) => {
      if (typeof apiBaseUrl !== 'string' || !['http:', 'https:'].includes(new URL(apiBaseUrl).protocol)) {
        throw new Error('Invalid backend URL');
      }
      const config = new Configuration({ basePath: apiBaseUrl.replace(/\/+$/, '') });
      const client = {
        health: new HealthApi(config), tests: new TestCreationApi(config),
        execution: new ExecutionApi(config), reporting: new ReportingApi(config),
      };
      setApi(client);
      void checkConnection(client);
    }).catch(() => setConnection('Could not load a valid backend configuration.'));
  }, []);

  async function refreshSuites() {
    if (api) setSuites(await api.tests.listTestSuites());
  }

  return <main>
    <header>
      <h1><Link to="/test-suites">Smartest AI TestBook</Link></h1>
      <div className="connection"><span role="status" className="muted">{connection}</span>
        {api && <button type="button" className="secondary" onClick={() => void checkConnection(api)}>Check connection</button>}
      </div>
    </header>
    {error && <p role="alert" className="error">{error}</p>}
    {api && <Outlet context={{ api, suites, loaded, refreshSuites } satisfies AppContext} />}
  </main>;
}

export function SuiteNavigation({ suiteId, current }: { suiteId: string; current: 'define' | 'execute' | 'report' }) {
  const tab = (name: typeof current, to: string, label: string) =>
    <Link to={to} aria-current={current === name ? 'page' : undefined}>{label}</Link>;
  return <nav aria-label="Suite navigation" className="suite-nav">
    {tab('define', `/test-suites/${suiteId}`, 'Define')}
    {tab('execute', `/execute/${suiteId}`, 'Execute')}
    {tab('report', `/execute/${suiteId}`, 'Report')}
  </nav>;
}

export function PageTitle({ back, title, aside }: { back: string; title: string; aside?: string }) {
  return <div className="page-title">
    <Link to={back} aria-label="Back">‹</Link>
    <h2>{title}</h2>
    {aside && <span className="muted">{aside}</span>}
  </div>;
}
