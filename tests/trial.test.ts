import { test } from 'node:test';
import assert from 'node:assert/strict';
import drafts from '../content/words/drafts.json';
import selection from '../content/words/selection.json';
import { entries } from '../src/data';
import { historicalEntries, trialEntries, trialWordCount } from '../src/data/trial';
import { answer, choices, decodeState, emptyState, mastery } from '../src/model';

test('every selected draft is practiceable while reserved and sample identities remain available', () => {
  assert.equal(trialWordCount, 1700 + selection.placements.length);
  assert.equal(historicalEntries.size, drafts.length + (trialWordCount - drafts.length + selection.expectedReservedWords) + 150);
  assert.deepEqual([1, 2, 3, 4].map(level => trialEntries.filter(e => e.kind === 'word' && e.level === level).length), [800, 900, 1200, selection.placements.filter(p => p.level === 4).length]);
  assert.equal(trialEntries.filter(e => e.kind === 'idiom').length, 50);
  assert.equal(entries.length, 150);
  for (const row of drafts) {
    assert.equal(historicalEntries.get(row.id)?.english, row.english);
    assert.equal(row.content.productionApproved, false);
    assert.equal(row.content.humanReviewed, false);
  }
  const draft = trialEntries.find(e => e.level === 3 && e.section === 8)!;
  const options = choices(draft, trialEntries.filter(e => e.kind === 'word'));
  assert.equal(options.length, 4);
  assert.equal(options.filter(option => option === draft.meaning).length, 1);
  let state = answer(answer(emptyState(), entries[0].id, 'choice', true), entries[0].id, 'choice', true);
  state = answer(answer(state, draft.id, 'choice', true), draft.id, 'choice', true);
  state.lastSection = { level: 3, kind: 'word', section: 8, mode: 'choice', catalog: 'draft' };
  const restored = decodeState(JSON.stringify(state));
  assert.equal(restored.lastSection?.catalog, 'draft');
  assert.equal(mastery(restored, draft.id, 'choice').mastered, true);
  assert.equal(mastery(restored, draft.id, 'written').mastered, false);
  assert.equal(mastery(restored, entries[0].id, 'choice').mastered, true);
  assert.equal(historicalEntries.get(entries[0].id)?.english, entries[0].english);
});
