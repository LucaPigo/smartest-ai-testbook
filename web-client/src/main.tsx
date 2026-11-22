import { createRoot } from 'react-dom/client';
import { BrowserRouter, Link, Navigate, Route, Routes } from 'react-router';
import { App } from './App';
import { SuiteList, SuiteNewPage, SuitePage, TestPage } from './SuitePage';
import { RunPage, RunConfigPage, ReportPage } from './RunPage';
import './style.css';

createRoot(document.getElementById('root')!).render(
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<App />}>
        <Route index element={<Navigate to="/test-suites" replace />} />
        <Route path="test-suites" element={<SuiteList />} />
        <Route path="test-suites/new" element={<SuiteNewPage />} />
        <Route path="test-suites/:suiteId" element={<SuitePage />} />
        <Route path="test-suites/:suiteId/test-cases/new" element={<TestPage />} />
        <Route path="test-cases/:caseId" element={<TestPage />} />
        <Route path="execute/:suiteId" element={<RunPage />} />
        <Route path="execute/:suiteId/run" element={<RunConfigPage />} />
        <Route path="reports/:runId" element={<ReportPage />} />
        <Route path="*" element={<p>Page not found. <Link to="/test-suites">View test suites</Link></p>} />
      </Route>
    </Routes>
  </BrowserRouter>,
);
