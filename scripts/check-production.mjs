import { spawn } from 'node:child_process';
import { chromium } from '@playwright/test';
import assert from 'node:assert/strict';
import drafts from '../content/words/drafts.json' with { type: 'json' };
import additions from '../content/words/reselected_additions.json' with { type: 'json' };
import selection from '../content/words/selection.json' with { type: 'json' };
import { readFileSync } from 'node:fs';
const extra = (selection.additionalBatchFiles ?? []).flatMap(name => JSON.parse(readFileSync(name, 'utf8')));
const byId = new Map([...drafts, ...additions, ...extra].map(e => [e.id, e]));
const trialWords = [...drafts.filter(e => e.level < 3), ...selection.placements.map(p => ({...byId.get(p.id), ...p}))];
const server = spawn('python3', ['-m', 'http.server', '8082', '--bind', '127.0.0.1', '--directory', 'dist'], { stdio: 'ignore' });
let browser;
try {
  for (let i = 0; i < 50; i++) { try { if ((await fetch('http://127.0.0.1:8082')).ok) break; } catch {} await new Promise(r => setTimeout(r, 100)); }
  browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const errors = []; page.on('pageerror', e => errors.push(e.message));
  await page.addInitScript(() => {
    window.audioFrequencies = [];
    const RealAudioContext = window.AudioContext;
    window.AudioContext = class extends RealAudioContext {
      createOscillator() { const oscillator = super.createOscillator(); const start = oscillator.start.bind(oscillator); oscillator.start = time => { window.audioFrequencies.push(oscillator.frequency.value); start(time); }; return oscillator; }
    };
  });
  await page.goto('http://127.0.0.1:8082');
  await page.getByText('今日も、英語を自分の力に。').waitFor();
  await page.screenshot({ path: 'test-results/home-desktop.png', fullPage: true });
  await page.getByRole('tab', { name: '設定', exact: true }).click();
  assert.equal(await page.getByRole('switch', { name: 'Premium検証モード' }).count(), 0);
  await page.getByRole('tab', { name: 'ホーム', exact: true }).click();
  await page.getByRole('button', { name: 'LEVEL 1 高校入試', exact: true }).click();
  await page.getByRole('button', { name: 'SECTION 01 · 英単語', exact: true }).click();
  await page.getByRole('button', { name: '選択式練習を始める', exact: true }).click();
  await page.getByRole('switch', { name: 'ランダム順' }).click();
  await page.getByRole('button', { name: 'この設定で練習を開始' }).click();
  const first = trialWords.find(entry => entry.level === 1 && entry.section === 1 && entry.number === 1);
  await page.getByRole('button', { name: first.meaning, exact: true }).click();
  await page.getByText('✓ 正解！', { exact: true }).waitFor();
  await page.waitForTimeout(420);
  await page.getByTestId('practice-card').click({ position: { x: 20, y: 20 } });
  await page.getByRole('button', { name: 'わからない', exact: true }).click();
  await page.getByText('？ わからない', { exact: true }).waitFor();
  await page.getByRole('tab', { name: 'ホーム', exact: true }).click();
  await page.getByRole('button', { name: 'LEVEL 3 高校上級・大学受験中級', exact: true }).click();
  await page.getByRole('button', { name: 'SECTION 08 · 英単語', exact: true }).click();
  await page.getByRole('button', { name: '選択式練習を始める', exact: true }).click();
  const random = page.getByRole('switch', { name: 'ランダム順' });
  if (await random.isChecked()) await random.click();
  await page.getByRole('button', { name: 'この設定で練習を開始', exact: true }).click();
  const draft = trialWords.find(entry => entry.level === 3 && entry.section === 8 && entry.number === 1);
  await page.getByRole('button', { name: draft.meaning, exact: true }).click();
  await page.getByText('✓ 正解！', { exact: true }).waitFor();
  await page.getByText(/^保存済み(?: · .*)?$/).waitFor();
  const saved = await page.evaluate(() => JSON.parse(localStorage.getItem('thank-you.learning.v1')));
  assert.equal(saved.progress[first.id].choice.history.length, 1);
  assert.equal(saved.progress[draft.id].choice.history.length, 1);
  assert.equal(saved.lastSection.catalog, 'draft');
  await page.reload();
  await page.getByText('今日も、英語を自分の力に。').waitFor();
  assert.equal(await page.getByText(/制作済み|検討済み|校閲前|草稿|試用中/).count(), 0);
  await page.getByRole('button', { name: '前回の学習を再開 →', exact: true }).click();
  await page.getByRole('button', { name: draft.english + ' の詳細', exact: true }).waitFor();
  await page.setViewportSize({ width: 390, height: 844 });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  const frequencies = await page.evaluate(() => window.audioFrequencies);
  for (const f of [900, 660, 880, 220, 174]) assert.ok(frequencies.includes(f), `missing sound ${f}`);
  assert.deepEqual(errors, []);
  console.log('PASS production: developer mode absent; real Web Audio tap/correct/wrong oscillator graphs; full-catalog practice history persists; mobile width fits; browser runtime has no errors.');
} finally { await browser?.close(); server.kill(); }
