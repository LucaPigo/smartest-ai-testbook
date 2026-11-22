import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const browser = await chromium.launch({ channel: process.env.BROWSER_CHANNEL ?? 'chrome', headless: true });
try {
  const page = await browser.newPage();
  await page.route('**/configuration.js', route => route.fulfill({ contentType: 'text/javascript',
    body: "export const apiBaseUrl = 'http://localhost:3001';" }));
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  let suite;
  let secondSuite;
  let run;
  let rejectSuite = false;
  let badHealth = false;
  let holdRun = false;
  let holdSuite = false;
  let releaseSuite;
  let notifySuiteRequested;
  const suiteRequested = new Promise(resolve => { notifySuiteRequested = resolve; });
  const suiteReleased = new Promise(resolve => { releaseSuite = resolve; });
  let releaseRun;
  let notifyRunRequested;
  const runRequested = new Promise(resolve => { notifyRunRequested = resolve; });
  const runReleased = new Promise(resolve => { releaseRun = resolve; });
  await page.route('http://localhost:3001/**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const method = request.method();
    const body = request.postDataJSON();
    if (method === 'OPTIONS') {
      await route.fulfill({ status: 204, headers: { 'access-control-allow-origin': '*', 'access-control-allow-methods': 'GET, POST, PUT, DELETE, OPTIONS', 'access-control-allow-headers': 'content-type' } });
      return;
    }
    let value;
    let status = 200;
    if (path === '/health') value = { status: badHealth ? 'bad' : 'ok' };
    else if (path === '/api/test-suites' && method === 'GET') value = [suite, secondSuite].filter(Boolean);
    else if (path === '/api/test-suites' && method === 'POST') {
      if (holdSuite) { notifySuiteRequested(); await suiteReleased; }
      if (rejectSuite) { status = 422; value = { detail: 'Invalid suite' }; }
      else { suite = { id: 'suite-1', ...body, tests: [] }; value = suite; status = 201; }
    } else if (path === '/api/test-suites/suite-1' && method === 'PUT') {
      suite = { ...suite, ...body }; value = suite;
    } else if (path === '/api/test-suites/suite-1' && method === 'DELETE') {
      suite = undefined; status = 204;
    } else if (path === '/api/test-cases' && method === 'POST') {
      assert.equal(body.suite_id, 'suite-1');
      assert.equal(body.title, 'Initial title');
      assert.equal(body.expectations[0].evaluator_type, 'exactMatch');
      assert.equal(body.expectations[0].threshold, 1);
      assert.deepEqual(body.expectations[0].options, { expected: 'Example output' });
      assert.equal('golden_reference' in body, false);
      assert.equal('goldenReference' in body, false);
      assert.equal('rubric' in body, false);
      assert.deepEqual(body.variables, { city: 'Paris' });
      const test = { ...body, id: 'test-1', expectations: body.expectations.map(item => ({ ...item, id: 'expectation-1' })) };
      suite.tests.push(test); value = test; status = 201;
    } else if (path === '/api/test-cases/test-1' && method === 'PUT') {
      assert.equal(body.title, 'Edited title');
      assert.equal(body.expectations[0].id, 'expectation-1');
      assert.equal(body.expectations[0].evaluator_type, 'semanticSimilarity');
      assert.equal(body.expectations[0].threshold, 0.85);
      assert.deepEqual(body.expectations[0].options, { expected: 'Independent reference' });
      suite.tests[0] = { ...body, id: 'test-1' }; value = suite.tests[0];
    } else if (path === '/api/expectations' && method === 'POST') {
      assert.equal(body.test_case_id, 'test-1');
      assert.equal(body.evaluator_type, 'llmJudge');
      assert.equal(body.threshold, 0.8);
      assert.deepEqual(body.options, { rubric: 'Answer with a city name.' });
      value = { ...body, id: 'expectation-2' }; suite.tests[0].expectations.push(value); status = 201;
    } else if (path === '/api/test-cases/test-1' && method === 'DELETE') {
      suite.tests = []; status = 204;
    } else if (path === '/api/test-suites/suite-2/eval-runs' && method === 'GET') value = [];
    else if (path === '/api/test-suites/suite-1/eval-runs' && method === 'GET') {
      value = run ? [run] : [];
    }
    else if (path === '/api/test-suites/suite-1/eval-runs' && method === 'POST') {
      assert.equal(body.model_name, 'fake-model');
      if (holdRun) { notifyRunRequested(); await runReleased; }
      run = { id: 'run-1', suite_id: 'suite-1', started_at: '2026-01-01T00:00:00Z', provider_name: body.provider_name, model_name: body.model_name,
        results: [{ test_id: 'test-1', prompt: 'Edited prompt', output: 'Example output', error: null, passed: true,
          scores: suite.tests[0].expectations.map(expectation => ({ expectation_id: expectation.id,
            expectation_name: expectation.name, evaluator_type: expectation.evaluator_type, threshold: expectation.threshold,
            value: 1, scale_min: 0, scale_max: 1, passed: true, feedback: 'Matched', error: null })) }] };
      value = run; status = 201;
    } else if (path === '/api/eval-runs/run-1') value = run;
    else throw new Error(`Unexpected request: ${method} ${path}`);
    await route.fulfill({ status, contentType: 'application/json', body: value === undefined ? undefined : JSON.stringify(value), headers: { 'access-control-allow-origin': '*' } });
  });

  await page.goto('http://127.0.0.1:5174');
  await page.getByText('Backend connected.', { exact: true }).waitFor();
  assert.equal(await page.getByLabel('Name', { exact: true }).count(), 0);
  assert.equal(await page.getByRole('button', { name: 'Create suite' }).count(), 0);
  await page.getByRole('link', { name: 'New suite', exact: true }).click();
  await page.waitForURL('**/test-suites/new');
  await page.getByRole('heading', { name: 'New suite', exact: true }).waitFor();
  await page.reload();
  await page.getByRole('heading', { name: 'New suite', exact: true }).waitFor();
  await page.getByRole('button', { name: 'Cancel', exact: true }).click();
  await page.waitForURL('**/test-suites');
  await page.goBack();
  await page.waitForURL('**/test-suites/new');
  await page.getByRole('heading', { name: 'New suite', exact: true }).waitFor();
  await page.getByLabel('Name', { exact: true }).fill('Example suite');
  await page.getByLabel('Description').fill('A simple suite');
  await page.getByRole('button', { name: 'Create suite' }).click();
  await page.getByRole('heading', { name: 'Example suite' }).waitFor();
  await page.waitForURL('**/test-suites/suite-1');
  await page.reload();
  await page.getByRole('heading', { name: 'Example suite' }).waitFor();
  await page.getByLabel('Description').fill('Updated suite');
  await Promise.all([
    page.waitForResponse(response => response.url().endsWith('/api/test-suites/suite-1') && response.request().method() === 'PUT'),
    page.getByRole('button', { name: 'Save suite' }).click(),
  ]);
  await page.getByRole('link', { name: 'Add test' }).click();
  await page.waitForURL('**/test-suites/suite-1/test-cases/new');
  await page.reload();
  await page.getByLabel('Title', { exact: true }).waitFor();
  await page.getByLabel('Title', { exact: true }).fill('Initial title');
  await page.locator('label').filter({ hasText: 'Prompt' }).locator('textarea').fill('Initial prompt');
  assert.equal(await page.getByLabel('Golden reference').count(), 0);
  assert.equal(await page.getByLabel('Options (JSON object)').count(), 0);
  await page.getByRole('button', { name: 'Add variable' }).click();
  await page.getByRole('group', { name: 'Variable 1' }).getByLabel('Name', { exact: true }).fill('city');
  await page.getByRole('group', { name: 'Variable 1' }).getByLabel('Value').fill('Paris');
  await page.getByRole('group', { name: 'Expectation 1' }).getByLabel('Name', { exact: true }).fill('Exact');
  const firstCheck = page.getByRole('group', { name: 'Expectation 1' });
  assert.equal(await firstCheck.getByLabel('Threshold').getAttribute('readonly'), '');
  assert.equal(await firstCheck.getByLabel('Threshold').inputValue(), '1');
  await firstCheck.getByLabel('Expected answer').fill('Example output');
  await page.getByRole('button', { name: 'Save test' }).click();
  await page.waitForURL('**/test-suites/suite-1');
  await page.getByText('Initial title', { exact: true }).waitFor();
  await page.getByText('Edit test', { exact: true }).click();
  await page.waitForURL('**/test-cases/test-1');
  await page.reload();
  await page.getByLabel('Title', { exact: true }).waitFor();
  assert.equal(await page.getByLabel('Title', { exact: true }).inputValue(), 'Initial title');
  assert.equal(await page.getByRole('group', { name: 'Variable 1' }).getByLabel('Value').inputValue(), 'Paris');
  await page.getByLabel('Title', { exact: true }).fill('Edited title');
  await page.locator('label').filter({ hasText: 'Prompt' }).locator('textarea').fill('Edited prompt');
  assert.equal(await firstCheck.getByLabel('Expected answer').inputValue(), 'Example output');
  await firstCheck.getByLabel('Evaluator').selectOption('llmJudge');
  assert.equal(await firstCheck.getByLabel('Rubric').inputValue(), '');
  assert.equal(await firstCheck.getByLabel('Expected answer').count(), 0);
  await firstCheck.getByLabel('Rubric').fill('Old rubric');
  await firstCheck.getByLabel('Evaluator').selectOption('semanticSimilarity');
  assert.equal(await firstCheck.getByLabel('Rubric').count(), 0);
  assert.equal(await firstCheck.getByLabel('Expected answer').inputValue(), '');
  assert.equal(await firstCheck.getByLabel('Threshold').inputValue(), '0.8');
  assert.equal(await firstCheck.getByLabel('Threshold').getAttribute('min'), '0');
  assert.equal(await firstCheck.getByLabel('Threshold').getAttribute('max'), '1');
  await firstCheck.getByLabel('Expected answer').fill('Independent reference');
  await firstCheck.getByLabel('Threshold').fill('0.85');
  await page.getByRole('button', { name: 'Save test' }).click();
  await page.waitForURL('**/test-suites/suite-1');
  await page.getByText('Edited title', { exact: true }).waitFor();
  await page.getByRole('link', { name: 'Edit test' }).click();
  assert.equal(await page.getByRole('button', { name: 'Save expectation' }).count(), 0);
  await page.getByRole('button', { name: 'Add expectation', exact: true }).click();
  const newCheck = page.locator('form').filter({ has: page.getByRole('heading', { name: 'New expectation', exact: true }) });
  await newCheck.getByRole('button', { name: 'Cancel', exact: true }).click();
  assert.equal(await page.getByRole('button', { name: 'Save expectation' }).count(), 0);
  await page.getByRole('button', { name: 'Add expectation', exact: true }).click();
  await newCheck.getByLabel('Name', { exact: true }).fill('Second check');
  await newCheck.getByLabel('Evaluator').selectOption('llmJudge');
  await newCheck.getByLabel('Rubric').fill('Answer with a city name.');
  await newCheck.getByRole('button', { name: 'Save expectation' }).click();
  await page.getByRole('button', { name: 'Add expectation', exact: true }).waitFor();
  assert.match(page.url(), /\/test-cases\/test-1$/);
  await page.getByRole('link', { name: 'Back' }).click();
  await page.getByText('2 expectation(s)').waitFor();
  await page.getByRole('link', { name: 'Execute', exact: true }).click();
  await page.waitForURL('**/execute/suite-1');
  await page.getByText('No runs yet.', { exact: true }).waitFor();
  assert.equal(await page.getByLabel('Model', { exact: true }).count(), 0);
  assert.equal(await page.getByRole('button', { name: 'Start run' }).count(), 0);
  await page.getByRole('link', { name: 'New run' }).click();
  await page.waitForURL('**/execute/suite-1/run');
  await page.reload();
  await page.getByLabel('Model', { exact: true }).fill('fake-model');
  await page.getByRole('button', { name: 'Start run' }).click();
  await page.waitForURL('**/reports/run-1');
  const summary = page.locator('[aria-label="Run summary"]');
  assert.match(await summary.innerText(), /1\s*Tests\s*1\s*Passed\s*0\s*Failed/);
  await page.getByText('Passed — Edited prompt').click();
  await page.getByText('Example output', { exact: true }).waitFor();
  await page.getByText('Matched', { exact: true }).first().waitFor();
  await page.reload();
  await page.getByText('Passed — Edited prompt').click();
  await page.getByText('Matched', { exact: true }).first().waitFor();

  await page.getByRole('link', { name: 'Report', exact: true }).click();
  await page.waitForURL('**/execute/suite-1');
  await page.getByRole('heading', { name: 'Reports', exact: true }).waitFor();
  await page.reload();
  await page.getByRole('link', { name: /fake-model/ }).click();
  await page.getByText('Passed — Edited prompt').click();
  await page.getByText(/Score: 1.*Threshold: 0.85/).waitFor();
  await page.goBack();
  await page.waitForURL('**/execute/suite-1');
  await page.goForward();
  await page.waitForURL('**/reports/run-1');
  await page.getByText('Passed — Edited prompt').click();
  await page.getByText('Matched', { exact: true }).first().waitFor();

  await page.goto('http://127.0.0.1:5174/');
  await page.goto('http://127.0.0.1:5174/reports/run-1');
  await page.getByText('Passed — Edited prompt').click();
  await page.getByText('Matched', { exact: true }).first().waitFor();

  secondSuite = { id: 'suite-2', name: 'Second suite', description: '', tests: [] };
  await page.goto('http://127.0.0.1:5174/execute/suite-1/run');
  await page.getByRole('button', { name: 'Check connection' }).click();
  await page.getByText('Backend connected.', { exact: true }).waitFor();
  holdRun = true;
  await page.getByLabel('Model', { exact: true }).fill('fake-model');
  await page.getByRole('button', { name: 'Start run' }).click();
  await runRequested;
  await page.getByRole('link', { name: 'Back' }).click();
  await page.waitForURL('**/execute/suite-1');
  await page.getByRole('link', { name: 'Back' }).click();
  await page.getByRole('link', { name: 'Second suite', exact: true }).click();
  const completedRun = page.waitForResponse(response => response.url().endsWith('/suite-1/eval-runs') && response.request().method() === 'POST');
  releaseRun();
  await completedRun;
  // Allow the completed request and any subsequent state updates to settle.
  await page.waitForTimeout(500);
  assert.match(page.url(), /\/test-suites\/suite-2$/);

  secondSuite = undefined;
  await page.goto('http://127.0.0.1:5174/test-suites/suite-1');
  page.once('dialog', dialog => dialog.accept());
  await page.getByRole('button', { name: 'Delete test' }).click();
  await page.getByText('No tests yet.').waitFor();
  await page.getByRole('link', { name: 'Back' }).click();
  page.once('dialog', dialog => dialog.accept());
  await page.getByRole('button', { name: 'Delete', exact: true }).click();
  await page.waitForURL('**/test-suites');
  await page.getByText('No suites yet.').waitFor();
  assert.equal(await page.getByLabel('Name', { exact: true }).count(), 0);
  rejectSuite = true;
  await page.getByRole('link', { name: 'New suite', exact: true }).click();
  await page.waitForURL('**/test-suites/new');
  await page.getByLabel('Name', { exact: true }).fill('Invalid');
  await page.getByRole('button', { name: 'Create suite' }).click();
  await page.getByRole('alert').getByText(/Invalid suite/).waitFor();
  assert.equal(await page.getByLabel('Name', { exact: true }).inputValue(), 'Invalid');
  rejectSuite = false;
  holdSuite = true;
  await page.getByRole('button', { name: 'Create suite' }).click();
  await suiteRequested;
  await page.getByRole('link', { name: 'Back' }).click();
  await page.waitForURL('**/test-suites');
  releaseSuite();
  await page.waitForTimeout(500);
  assert.match(page.url(), /\/test-suites$/);
  holdSuite = false;
  suite = undefined;
  badHealth = true;
  await page.getByRole('button', { name: 'Check connection' }).click();
  await page.getByText('Could not connect to the backend. Try again.', { exact: true }).waitFor();
  badHealth = false;
  await page.getByRole('button', { name: 'Check connection' }).click();
  await page.getByText('Backend connected.', { exact: true }).waitFor();
  const badConfig = await browser.newPage();
  await badConfig.route('**/configuration.js', route => route.fulfill({ contentType: 'text/javascript', body: "export const apiBaseUrl = 'invalid';" }));
  await badConfig.goto('http://127.0.0.1:5174');
  await badConfig.getByText('Could not load a valid backend configuration.', { exact: true }).waitFor();
  await badConfig.close();
  assert.deepEqual(errors, []);
  console.log('Browser workflow passed with a fake API.');
} finally { await browser.close(); }





