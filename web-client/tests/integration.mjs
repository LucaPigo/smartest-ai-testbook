import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const phase = process.argv[2];
if (!['create', 'verify'].includes(phase)) throw new Error('Use create or verify.');
const browser = await chromium.launch({ channel: process.env.BROWSER_CHANNEL ?? 'chrome', headless: true });
try {
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => { if (['error', 'warning'].includes(message.type())) errors.push(message.text()); });
  await page.route('**/configuration.js', route => route.fulfill({ contentType: 'text/javascript',
    body: "export const apiBaseUrl = 'http://127.0.0.1:3019';" }));
  await page.goto('http://127.0.0.1:5174');
  await page.getByText('Backend connected.', { exact: true }).waitFor();
  assert.equal(await page.getByLabel('Name', { exact: true }).count(), 0);
  assert.equal(await page.getByRole('button', { name: 'Create suite' }).count(), 0);
  if (phase === 'create') {
    await page.getByRole('link', { name: 'New suite', exact: true }).click();
    await page.waitForURL('**/test-suites/new');
    await page.reload();
    await page.getByRole('heading', { name: 'New suite', exact: true }).waitFor();
    await page.getByLabel('Name', { exact: true }).fill('Browser integration suite');
    await page.getByLabel('Description').fill('SQLite browser workflow');
    await page.getByRole('button', { name: 'Create suite' }).click();
    await page.getByRole('heading', { name: 'Browser integration suite' }).waitFor();
    await page.getByRole('link', { name: 'Add test' }).click();
    await page.waitForURL('**/test-suites/*/test-cases/new');
    await page.getByLabel('Title', { exact: true }).fill('Original title');
    await page.locator('label').filter({ hasText: 'Prompt' }).locator('textarea').fill('Original prompt');
    assert.equal(await page.getByLabel('Golden reference').count(), 0);
    assert.equal(await page.getByLabel('Options (JSON object)').count(), 0);
    await page.getByRole('button', { name: 'Add variable' }).click();
    await page.getByRole('group', { name: 'Variable 1' }).getByLabel('Name', { exact: true }).fill('country');
    await page.getByRole('group', { name: 'Variable 1' }).getByLabel('Value').fill('France');
    const checks = [
      { name: 'Exact', type: 'exactMatch', criterion: 'Paris', threshold: '1' },
      { name: 'Similar answer', type: 'semanticSimilarity', criterion: 'The capital is Paris.', threshold: '0.85' },
      { name: 'Correct information', type: 'llmJudge', criterion: 'Name the capital of France.', threshold: '0.8' },
      { name: 'Concise answer', type: 'llmJudge', criterion: 'Use one city name.', threshold: '0.8' },
    ];
    for (const [index, check] of checks.entries()) {
      if (index) await page.getByRole('button', { name: 'Add expectation' }).click();
      const fields = page.getByRole('group', { name: `Expectation ${index + 1}` });
      await fields.getByLabel('Name', { exact: true }).fill(check.name);
      await fields.getByLabel('Evaluator').selectOption(check.type);
      assert.equal(await fields.getByLabel('Threshold').inputValue(), check.type === 'exactMatch' ? '1' : '0.8');
      await fields.getByLabel(check.type === 'llmJudge' ? 'Rubric' : 'Expected answer').fill(check.criterion);
      if (check.type === 'exactMatch') assert.equal(await fields.getByLabel('Threshold').getAttribute('readonly'), '');
      else await fields.getByLabel('Threshold').fill(check.threshold);
    }
    for (const width of [320, 768, 1024, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true,
        `The form must fit a ${width}px viewport.`);
    }
    const [createdResponse] = await Promise.all([
      page.waitForResponse(response => response.url().endsWith('/api/test-cases') && response.request().method() === 'POST'),
      page.getByRole('button', { name: 'Save test' }).click(),
    ]);
    assert.equal(createdResponse.status(), 201);
    const original = await createdResponse.json();
    assert.equal('golden_reference' in original, false);
    assert.equal('goldenReference' in original, false);
    assert.equal('rubric' in original, false);
    assert.deepEqual(original.expectations.map(check => check.options), [
      { expected: 'Paris' }, { expected: 'The capital is Paris.' },
      { rubric: 'Name the capital of France.' }, { rubric: 'Use one city name.' },
    ]);
    await page.waitForURL('**/test-suites/*');
    await page.getByText('Original title', { exact: true }).waitFor();
    await page.getByRole('link', { name: 'Execute', exact: true }).click();
    await page.waitForURL('**/execute/*');
    await page.getByText('No runs yet.', { exact: true }).waitFor();
    assert.equal(await page.getByLabel('Model', { exact: true }).count(), 0);
    await page.getByRole('link', { name: 'New run' }).click();
    await page.waitForURL('**/execute/*/run');
    await page.reload();
    await page.getByLabel('Model', { exact: true }).fill('fake-model');
    await page.getByRole('button', { name: 'Start run' }).click();
    await page.getByText('Passed — Original prompt').click();
    await page.getByText('Paris', { exact: true }).waitFor();
    await page.getByText(/Score: 1.*Threshold: 1/).waitFor();
    await page.getByText(/Score: 1.*Threshold: 0.85/).waitFor();
    await page.getByRole('link', { name: 'Define', exact: true }).click();
    await page.getByRole('link', { name: 'Edit test' }).click();
    await page.waitForURL('**/test-cases/*');
    assert.equal(await page.getByLabel('Title', { exact: true }).inputValue(), 'Original title');
    await page.getByLabel('Title', { exact: true }).fill('Changed title');
    await page.locator('label').filter({ hasText: 'Prompt' }).locator('textarea').fill('Changed prompt');
    const first = page.getByRole('group', { name: 'Expectation 1' });
    await first.getByLabel('Name', { exact: true }).fill('Changed exact');
    await first.getByLabel('Evaluator').selectOption('semanticSimilarity');
    assert.equal(await first.getByLabel('Expected answer').inputValue(), '');
    assert.equal(await first.getByLabel('Threshold').inputValue(), '0.8');
    await first.getByLabel('Expected answer').fill('Lyon');
    await first.getByLabel('Threshold').fill('0.6');
    const second = page.getByRole('group', { name: 'Expectation 2' });
    await second.getByLabel('Name', { exact: true }).fill('Changed semantic');
    await second.getByLabel('Evaluator').selectOption('llmJudge');
    assert.equal(await second.getByLabel('Rubric').inputValue(), '');
    assert.equal(await second.getByLabel('Expected answer').count(), 0);
    await second.getByLabel('Rubric').fill('Updated correctness.');
    await second.getByLabel('Threshold').fill('0.9');
    const third = page.getByRole('group', { name: 'Expectation 3' });
    await third.getByLabel('Name', { exact: true }).fill('Changed judge');
    await third.getByLabel('Evaluator').selectOption('exactMatch');
    assert.equal(await third.getByLabel('Expected answer').inputValue(), '');
    assert.equal(await third.getByLabel('Threshold').inputValue(), '1');
    assert.equal(await third.getByLabel('Threshold').getAttribute('readonly'), '');
    assert.equal(await third.getByLabel('Rubric').count(), 0);
    await third.getByLabel('Expected answer').fill('Paris');
    const [updatedResponse] = await Promise.all([
      page.waitForResponse(response => response.url().endsWith(`/api/test-cases/${original.id}`) && response.request().method() === 'PUT'),
      page.getByRole('button', { name: 'Save test' }).click(),
    ]);
    assert.equal(updatedResponse.status(), 200);
    const updated = await updatedResponse.json();
    assert.deepEqual(updated.expectations.map(check => check.id), original.expectations.map(check => check.id));
    assert.deepEqual(updated.expectations.map(check => check.options), [
      { expected: 'Lyon' }, { rubric: 'Updated correctness.' }, { expected: 'Paris' }, { rubric: 'Use one city name.' },
    ]);
    await page.getByText('Changed title', { exact: true }).waitFor();
    await page.getByRole('link', { name: 'Edit test' }).click();
    assert.equal(await page.getByRole('button', { name: 'Save expectation', exact: true }).count(), 0);
    await page.getByRole('button', { name: 'Add expectation', exact: true }).click();
    const newCheck = page.locator('form').filter({ has: page.getByRole('heading', { name: 'New expectation', exact: true }) });
    await newCheck.getByRole('button', { name: 'Cancel', exact: true }).click();
    await page.getByRole('button', { name: 'Add expectation', exact: true }).click();
    await newCheck.getByLabel('Name', { exact: true }).fill('Additional check');
    await newCheck.getByLabel('Expected answer').fill('Paris');
    await newCheck.getByRole('button', { name: 'Save expectation', exact: true }).click();
    await page.getByRole('group', { name: 'Expectation 5' }).getByLabel('Name', { exact: true }).waitFor();
  } else {
    await page.getByRole('link', { name: 'Browser integration suite' }).click();
    await page.getByText('Changed title', { exact: true }).waitFor();
    await page.getByRole('link', { name: 'Edit test' }).click();
    assert.equal(await page.getByRole('group', { name: 'Variable 1' }).getByLabel('Value').inputValue(), 'France');
    assert.equal(await page.getByRole('group', { name: 'Expectation 1' }).getByLabel('Expected answer').inputValue(), 'Lyon');
    assert.equal(await page.getByRole('group', { name: 'Expectation 1' }).getByLabel('Threshold').inputValue(), '0.6');
    assert.equal(await page.getByRole('group', { name: 'Expectation 2' }).getByLabel('Rubric').inputValue(), 'Updated correctness.');
    assert.equal(await page.getByRole('group', { name: 'Expectation 3' }).getByLabel('Threshold').inputValue(), '1');
    assert.equal(await page.getByRole('group', { name: 'Expectation 4' }).getByLabel('Rubric').inputValue(), 'Use one city name.');
    assert.equal(await page.getByRole('group', { name: 'Expectation 5' }).getByLabel('Name', { exact: true }).inputValue(), 'Additional check');
    assert.equal(await page.getByRole('group', { name: 'Expectation 5' }).getByLabel('Expected answer').inputValue(), 'Paris');
    await page.getByRole('link', { name: 'Report', exact: true }).click();
    await page.getByRole('heading', { name: 'Reports', exact: true }).waitFor();
    await page.reload();
    await page.getByRole('link', { name: /fake-model/ }).click();
    await page.getByText('Passed — Original prompt').click();
    await page.getByText('Original prompt', { exact: true }).waitFor();
    await page.getByText('Paris', { exact: true }).waitFor();
    await page.getByText(/Score: 1.*Threshold: 1/).waitFor();
    await page.getByText(/Score: 1.*Threshold: 0.85/).waitFor();
    await page.getByText('Exact (exactMatch) — Passed', { exact: true }).waitFor();
    await page.getByText('Similar answer (semanticSimilarity) — Passed', { exact: true }).waitFor();
    await page.getByText('Correct information (llmJudge) — Passed', { exact: true }).waitFor();
  }
  assert.deepEqual(errors, []);
  console.log(`Real API browser ${phase} phase passed.`);
} finally { await browser.close(); }
