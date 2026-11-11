import { test, expect } from '@playwright/test';
import data from '../src/data/entries.json';
const key = 'thank-you.learning.v1';
test('browser study flow: independent mastery, sounds, storage, search, mobile', async ({ page }) => {
  const errors: string[] = []; page.on('pageerror', e => errors.push(e.message));
  await page.addInitScript(() => {
    const w = window as any; w.audioNotes = 0; w.speechCalls = 0;
    class AudioMock { currentTime = 0; destination = {}; resume() { return Promise.resolve(); } createOscillator() { return { frequency: { value: 0 }, connect() {}, start() { w.audioNotes++; }, stop() {} }; } createGain() { return { gain: { setValueAtTime() {}, linearRampToValueAtTime() {}, exponentialRampToValueAtTime() {} }, connect() {} }; } }
    w.AudioContext = AudioMock;
    Object.defineProperty(window, 'speechSynthesis', { configurable: true, value: { cancel() {}, speak() { w.speechCalls++; } } });
  });
  await page.goto('/');
  await expect(page.getByText('今日も、英語を自分の力に。')).toBeVisible();
  await page.getByRole('tab', { name: '設定', exact: true }).click();
  await page.getByRole('switch', { name: 'Premium検証モード' }).click();
  await page.getByRole('switch', { name: '英語の発音音声' }).click();
  await page.getByRole('tab', { name: 'ホーム', exact: true }).click();
  await page.getByRole('button', { name: 'LEVEL 1 高校入試', exact: true }).click();
  await page.getByRole('button', { name: 'SECTION 01 · 英単語', exact: true }).click();
  const run = async (mode: 'choice' | 'written', incorrectFirst = false) => {
    await page.getByRole('button', { name: mode === 'choice' ? '選択式練習を始める' : '記述式練習', exact: true }).click();
    const random = page.getByRole('switch', { name: 'ランダム順' }); if (await random.isChecked()) await random.click();
    await page.getByRole('button', { name: 'この設定で練習を開始' }).click();
    for (let i = 0; i < 10; i++) {
      if (incorrectFirst && i === 0) await page.getByRole('button', { name: 'わからない', exact: true }).click();
      else if (mode === 'choice') await page.getByRole('button', { name: data[i].meaning, exact: true }).click();
      else { await page.getByRole('textbox', { name: '英語の入力 1', exact: true }).fill(data[i].english.toUpperCase()); await page.getByRole('button', { name: '回答する', exact: true }).click(); }
      await expect(page.getByText(i === 0 && incorrectFirst ? 'もう一度、覚えよう' : '✓ 正解！', { exact: true })).toBeVisible();
      await page.getByRole('button', { name: i === 9 ? '結果を見る →' : '次の問題へ →', exact: true }).click();
    }
    await page.getByRole('button', { name: 'セクション一覧へ' }).click();
  };
  await run('choice'); await run('choice');
  const saved = async () => {
    await expect(page.getByText('保存済み', { exact: true })).toBeVisible();
    return page.evaluate(k => JSON.parse(localStorage.getItem(k)!), key);
  };
  let state = await saved(); expect(state.progress[data[0].id].choice.mastered).toBe(true); expect(state.progress[data[0].id].written).toBeUndefined();
  await run('written'); await run('written');
  state = await saved(); expect(state.progress[data[0].id].written.mastered).toBe(true);
  await run('choice', true);
  state = await saved(); expect(state.progress[data[0].id].choice.mastered).toBe(false); expect(state.progress[data[0].id].written.mastered).toBe(true); expect(state.progress[data[0].id].written.history).toHaveLength(2);
  expect(await page.evaluate(() => (window as any).audioNotes)).toBeGreaterThan(0);
  await page.getByRole('tab', { name: '設定', exact: true }).click();
  await page.getByRole('switch', { name: '効果音', exact: true }).click();
  const notes = await page.evaluate(() => (window as any).audioNotes);
  await page.getByRole('tab', { name: '検索', exact: true }).click();
  await page.getByRole('textbox', { name: '教材を検索', exact: true }).fill('learn');
  await page.getByRole('button', { name: 'learn の詳細', exact: true }).click();
  await page.getByRole('button', { name: '発音を聴く', exact: true }).click();
  expect(await page.evaluate(() => (window as any).speechCalls)).toBeGreaterThan(0);
  expect(await page.evaluate(() => (window as any).audioNotes)).toBe(notes);
  await saved(); await page.reload();
  await expect(page.getByText('今日も、英語を自分の力に。')).toBeVisible();
  state = await saved(); expect(state.settings.sound).toBe(false); expect(state.settings.speech).toBe(true); expect(state.progress[data[0].id].written.mastered).toBe(true);
  await page.getByRole('tab', { name: '設定', exact: true }).click();
  await expect(page.getByRole('switch', { name: 'Premium検証モード' })).not.toBeChecked();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole('tab', { name: 'ホーム', exact: true }).click();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: 'test-results/home-mobile.png', fullPage: true });
  await page.getByRole('button', { name: 'LEVEL 2 高校初級〜中級', exact: true }).click();
  await expect(page.getByText('教材準備中', { exact: true }).first()).toBeVisible();
  expect(errors).toEqual([]);
});
test('corrupted data is preserved and does not silently reset', async ({ page }) => {
  await page.addInitScript(k => localStorage.setItem(k, '{invalid'), key);
  await page.goto('/'); await expect(page.getByText('保存データの確認が必要です')).toBeVisible();
  expect(await page.evaluate(k => localStorage.getItem(k), key)).toBe('{invalid');
});
test('idiom word inputs, favorites and retained list position', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('tab', { name: '設定', exact: true }).click();
  await page.getByRole('switch', { name: 'Premium検証モード' }).click();
  await page.getByRole('tab', { name: 'ホーム', exact: true }).click();
  await page.getByRole('button', { name: 'LEVEL 1 高校入試', exact: true }).click();
  await page.getByRole('button', { name: 'SECTION 01 · 英熟語', exact: true }).click();
  await page.getByRole('button', { name: 'look forward to の詳細', exact: true }).click();
  await page.getByRole('button', { name: '☆ お気に入り登録', exact: true }).click();
  await expect(page.getByRole('button', { name: '★ お気に入り解除', exact: true })).toBeVisible();
  await page.getByRole('button', { name: '← 戻る', exact: true }).click();
  await expect(page.getByRole('button', { name: 'look forward to の詳細', exact: true })).toBeInViewport();
  await page.getByRole('button', { name: 'お気に入り', exact: true }).click();
  await expect(page.getByText('1件を表示', { exact: false })).toBeVisible();
  await page.getByRole('button', { name: '記述式練習', exact: true }).click();
  await page.getByRole('button', { name: 'お気に入り', exact: true }).click();
  await page.getByRole('button', { name: 'この設定で練習を開始' }).click();
  await expect(page.getByText('3語 · 最初の頭文字：l')).toBeVisible();
  for (const [i, word] of ['look', 'forward', 'to'].entries()) await page.getByRole('textbox', { name: `英語の入力 ${i + 1}`, exact: true }).fill(word);
  await page.getByRole('button', { name: '回答する', exact: true }).click();
  await expect(page.getByText('✓ 正解！', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: '結果を見る →', exact: true }).click();
  await expect(page.getByRole('button', { name: '間違えた教材だけ再練習', exact: true })).toBeDisabled();
});
