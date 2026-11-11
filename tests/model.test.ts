import { test } from 'node:test';
import assert from 'node:assert/strict';
import { answer, choices, decodeState, emptyState, grade, mastery, validateEntries } from '../src/model';
import { entries } from '../src/data';
test('150 unique sample entries, stable IDs, full example data, correct section sizes', () => {
  validateEntries(entries);
  assert.equal(entries.filter(e => e.kind === 'word').length, 100);
  assert.equal(entries.filter(e => e.kind === 'idiom').length, 50);
  assert.throws(() => validateEntries([...entries, entries[0]]));
});
test('two consecutive answers master only the selected mode; misses reset only that mode', () => {
  for (const mode of ['choice', 'written'] as const) {
    const other = mode === 'choice' ? 'written' : 'choice';
    let s = emptyState(); s = answer(s, 'word-l1-0001', mode, true);
    assert.equal(mastery(s, 'word-l1-0001', mode).mastered, false);
    s = answer(s, 'word-l1-0001', mode, true);
    assert.equal(mastery(s, 'word-l1-0001', mode).mastered, true);
    assert.equal(mastery(s, 'word-l1-0001', other).history.length, 0);
    s = answer(answer(s, 'word-l1-0001', other, true), 'word-l1-0001', other, true);
    const untouched = mastery(s, 'word-l1-0001', other);
    s = answer(s, 'word-l1-0001', mode, false);
    assert.equal(mastery(s, 'word-l1-0001', mode).streak, 0);
    assert.equal(mastery(s, 'word-l1-0001', mode).mastered, false);
    assert.deepEqual(mastery(s, 'word-l1-0001', other), untouched);
  }
});
test('incorrect answer breaks a streak and immutable state keeps old history', () => {
  const before = answer(emptyState(), 'x', 'choice', true);
  const after = answer(answer(before, 'x', 'choice', false), 'x', 'choice', true);
  assert.equal(mastery(after, 'x', 'choice').mastered, false);
  assert.equal(mastery(before, 'x', 'choice').history.length, 1);
});
test('four distinct choices always contain exactly one correct meaning', () => {
  for (const entry of entries) for (let i = 0; i < 20; i++) {
    const options = choices(entry, entries.filter(e => e.kind === entry.kind));
    assert.equal(new Set(options).size, 4); assert.equal(options.filter(x => x === entry.meaning).length, 1);
  }
});
test('written grading accepts only explicit alternatives, ignores case and outer spaces', () => {
  assert.equal(grade(entries[0], ' LEARN '), true);
  assert.equal(grade(entries[0], 'learns'), false);
  const idiom = entries.find(e => e.english === 'look for')!;
  assert.equal(grade(idiom, ' LOOK FOR '), true);
  assert.equal(grade(idiom, 'look  for'), false);
});
test('storage round trip preserves independent history, settings, awards, favorites', () => {
  const original = answer(answer(emptyState(), 'x', 'choice', true), 'x', 'written', false);
  original.permanentAwards.push('future-award'); original.favorites.push('x'); original.settings.sound = false;
  const decoded = decodeState(JSON.stringify(original)); assert.deepEqual(decoded, original);
  assert.deepEqual(decodeState(null), emptyState());
  assert.throws(() => decodeState('{broken')); assert.throws(() => decodeState('{"version":2}'));
  assert.throws(() => decodeState(JSON.stringify({ ...original, progress: { x: { choice: { streak: -1 } } } })));
});
