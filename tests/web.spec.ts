import { test, expect } from '@playwright/test';
import data from '../src/data/entries.json';
const key = 'thank-you.learning.v1';
// Legacy sample-flow checks deliberately choose the sample catalog; new users now open the full catalog.
test.beforeEach(async ({ page }, testInfo) => {
  if (testInfo.title.startsWith('corrupted') || testInfo.title.startsWith('level 4')) return;
  await page.addInitScript(k => localStorage.setItem(k, JSON.stringify({ version:1, progress:{}, favorites:[], settings:{sound:true,speech:false}, permanentAwards:[], lastSection:{level:1,kind:'word',section:1,catalog:'sample'} })), key);
});
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
      await expect(page.getByText(i === 0 && incorrectFirst ? '？ わからない' : '✓ 正解！', { exact: true })).toBeVisible();
      await expect(page.getByTestId('question-content')).toHaveCount(0);
      await expect(page.getByRole('button', { name: /次へ|次の問題|NEXT|結果を見る/ })).toHaveCount(0);
      await page.waitForTimeout(420);
      await page.getByTestId('practice-card').click({ position: { x: 20, y: 20 } });
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
  await page.waitForTimeout(420);
  await page.getByTestId('practice-card').click({ position: { x: 20, y: 20 } });
  await expect(page.getByRole('button', { name: '間違えた教材だけ再練習', exact: true })).toBeDisabled();
});
test('explanation replaces question; controls and double taps cannot skip or double save', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('tab', { name: '設定', exact: true }).click();
  await page.getByRole('switch', { name: 'Premium検証モード' }).click();
  await page.getByRole('switch', { name: '英語の発音音声' }).click();
  await page.getByRole('tab', { name: 'ホーム', exact: true }).click();
  await page.getByRole('button', { name: 'LEVEL 1 高校入試', exact: true }).click();
  await page.getByRole('button', { name: 'SECTION 01 · 英単語', exact: true }).click();
  await page.getByRole('button', { name: '選択式練習を始める', exact: true }).click();
  await page.getByRole('switch', { name: 'ランダム順' }).click();
  await page.getByRole('button', { name: 'この設定で練習を開始' }).click();
  await page.getByRole('button', { name: '学ぶ', exact: true }).dblclick({ delay: 30 });
  await expect(page.getByTestId('question-content')).toHaveCount(0);
  await expect(page.getByTestId('explanation-content')).toHaveCount(1);
  await expect(page.getByText('✓ 正解！', { exact: true })).toBeInViewport();
  await page.screenshot({ path: 'test-results/practice-explanation.png', fullPage: true });
  await expect(page.getByRole('button', { name: /次へ|次の問題|NEXT/ })).toHaveCount(0);
  await expect(page.getByText('選択式 · 1 / 10', { exact: true })).toBeVisible();
  await page.waitForTimeout(420);
  await page.getByRole('button', { name: '発音を聴く', exact: true }).click();
  await page.getByRole('button', { name: '☆ お気に入り登録', exact: true }).click();
  await expect(page.getByText('選択式 · 1 / 10', { exact: true })).toBeVisible();
  await expect(page.getByText('保存済み', { exact: true })).toBeVisible();
  const state = await page.evaluate(k => JSON.parse(localStorage.getItem(k)!), key);
  expect(state.progress['word-l1-0001'].choice.history).toHaveLength(1);
  expect(state.favorites).toContain('word-l1-0001');
  const surface = page.getByTestId('practice-surface');
  const bounds = await surface.boundingBox();
  await surface.click({ position: { x: bounds!.width - 4, y: 20 } });
  await expect(page.getByText('選択式 · 2 / 10', { exact: true })).toBeVisible();
});
test('wrong-item review continues after first correct answer until mastered', async ({ page }) => {
  await page.addInitScript(() => {
    (window as any).speechCalls = 0;
    Object.defineProperty(window, 'speechSynthesis', { configurable: true, value: { cancel() {}, speak() { (window as any).speechCalls++; } } });
  });
  await page.addInitScript(k => {
    localStorage.setItem(k, JSON.stringify({ version: 1, progress: {}, favorites: ['word-l1-0001'], settings: { sound: false, speech: true }, permanentAwards: [] }));
  }, key);
  // The seed is only for setup; preserve real writes on this page.
  await page.goto('/');
  await page.getByRole('tab', { name: '設定', exact: true }).click();
  await page.getByRole('switch', { name: 'Premium検証モード' }).click();
  await page.getByRole('tab', { name: 'ホーム', exact: true }).click();
  await page.getByRole('button', { name: 'LEVEL 1 高校入試', exact: true }).click();
  await page.getByRole('button', { name: 'SECTION 01 · 英単語', exact: true }).click();
  await page.getByRole('button', { name: '選択式練習を始める', exact: true }).click();
  await page.getByRole('button', { name: 'お気に入り', exact: true }).click();
  await page.getByRole('button', { name: 'この設定で練習を開始' }).click();
  await page.getByRole('button', { name: 'わからない', exact: true }).click();
  await page.waitForTimeout(420); await page.getByTestId('practice-card').click({ position: { x: 20, y: 20 } });
  await page.getByRole('button', { name: '間違えた教材だけ再練習', exact: true }).click();
  for (let n = 0; n < 2; n++) {
    await page.getByRole('button', { name: '学ぶ', exact: true }).click();
    await page.waitForTimeout(420); await page.getByTestId('practice-card').click({ position: { x: 20, y: 20 } });
    if (n === 0) await expect(page.getByRole('button', { name: '学ぶ', exact: true })).toBeVisible();
  }
  expect(await page.evaluate(() => (window as any).speechCalls)).toBeGreaterThanOrEqual(3);
  await expect(page.getByText('今日の一歩、おつかれさまでした。')).toBeVisible();
  await expect(page.getByRole('button', { name: '間違えた教材だけ再練習', exact: true })).toBeDisabled();
});
test('source credits distinguish unverified references from imported material', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('tab', { name: '設定', exact: true }).click();
  await page.getByRole('button', { name: '教材・出典・ライセンス', exact: true }).click();
  await expect(page.getByText('教材の制作・利用条件', { exact: true })).toBeVisible();
  await expect(page.getByText('NGSL', { exact: true })).toBeVisible();
  await expect(page.getByText('確認済みバージョン：1.2 / 商用利用条件：記録あり', { exact: true })).toHaveCount(4);
  await expect(page.getByText(/重複をまとめて5,619語の候補/)).toBeVisible();
  await expect(page.getByRole('link', { name: 'https://creativecommons.org/licenses/by-sa/4.0/', exact: true })).toBeVisible();
  await expect(page.getByText('確認済みバージョン：未確認 / 商用利用条件：未確認', { exact: true }).first()).toBeVisible();
});

test('level 4 opens all ten sections and diagnostic cancellation preserves mastery', async ({ page }) => {
  const errors: string[] = []; page.on('pageerror', e => errors.push(e.message));
  await page.goto('/');
  await expect(page.getByText('現在利用中：英単語3,900語', { exact: false })).toBeVisible();
  await page.getByRole('button', { name: /LEVEL 4 大学受験上級/ }).click();
  for (let s=1;s<=10;s++) await expect(page.getByRole('button',{ name:`SECTION ${String(s).padStart(2,'0')} · 英単語`,exact:true })).toBeVisible();
  await page.getByRole('button', { name:'SECTION 10 · 英単語',exact:true }).click();
  await page.getByRole('button', { name:'初回診断を受験',exact:true }).click();
  await page.getByRole('button', { name:'試験を開始する',exact:true }).click();
  await expect(page.getByText(/試験 1 \/ 100/)).toBeVisible();
  await expect(page.getByRole('button', { name: /^\d\. / })).toHaveCount(8);
  await page.getByRole('button', { name:'試験：わからない',exact:true }).click();
  await expect(page.getByText(/試験 2 \/ 100/)).toBeVisible();
  await expect(page.getByText('✓ 正解！', {exact:true})).toHaveCount(0);
  await page.getByRole('button', { name:'試験を中断して戻る（今回の変更は破棄）',exact:true }).click();
  await expect(page.getByText('保存済み',{exact:true})).toBeVisible();
  const state=await page.evaluate(k=>JSON.parse(localStorage.getItem(k)!),key);
  expect(state.progress).toEqual({});expect(state.exams['draft:4:word:choice:10'].diagnosticUsed).toBe(true);
  await page.reload();
  await expect(page.getByRole('button',{name:'前回の学習を再開 →',exact:true})).toBeVisible();
  expect(errors).toEqual([]);
});
