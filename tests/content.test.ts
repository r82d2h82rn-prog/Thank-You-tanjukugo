import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ApprovedEntry, mergeCatalog } from '../src/content';
import { entries } from '../src/data';
import { answer, decodeState, emptyState, mastery } from '../src/model';
test('reviewed content keeps existing identity and rejects unpublished content or ID reuse', () => {
  const e = { ...entries[0], content: { sourceIds: ['test-original'], contentVersion: 2, qualityStatus: 'approved', autoChecked: true, humanReviewed: true, examFrequency: null, selectionReason: 'test fixture', productionApproved: true } } as ApprovedEntry;
  const sources = [{ id: 'test-original', commercialUse: 'granted', redistribution: 'granted', licenseEvidence: 'synthetic test permission' }];
  const catalog = mergeCatalog(entries, [e], sources); assert.equal(catalog.length, 150); assert.equal(catalog.find(row => row.id === e.id), e);
  assert.throws(() => mergeCatalog(entries, [e], []));
  assert.throws(() => mergeCatalog(entries, [{ ...e, english: 'different' }], sources));
  assert.throws(() => mergeCatalog(entries, [{ ...e, content: { ...e.content, humanReviewed: false } }], sources));
  assert.throws(() => mergeCatalog(entries, [{ ...e, content: { ...e.content, qualityStatus: 'review_required' } }], sources));
  assert.throws(() => mergeCatalog(entries, [{ ...e, content: { ...e.content, autoChecked: false } }], sources));
});

test('a full approved section replaces samples without recycling their identities or mastery', () => {
  const metadata = { sourceIds: ['fixture'], contentVersion: 1, qualityStatus: 'approved' as const, autoChecked: true, humanReviewed: true, examFrequency: null, selectionReason: 'Synthetic migration fixture', productionApproved: true };
  const sources = [{ id: 'fixture', commercialUse: 'granted', redistribution: 'granted', licenseEvidence: 'Synthetic fixture' }];
  const section: ApprovedEntry[] = Array.from({ length: 100 }, (_, index) => ({ ...entries[0], id: `synthetic-new-${index}`, english: `synthetic-entry-${index}`, number: index + 1, content: metadata }));
  const saved = answer(answer(emptyState(), entries[0].id, 'choice', true), entries[0].id, 'choice', true);
  const catalog = mergeCatalog(entries, section, sources);
  assert.equal(catalog.filter(e => e.kind === 'word').length, 100);
  assert.equal(catalog.filter(e => e.kind === 'idiom').length, 50);
  assert.equal(catalog.some(e => e.id === entries[0].id), false);
  const restored = decodeState(JSON.stringify(saved));
  assert.equal(mastery(restored, entries[0].id, 'choice').mastered, true);
  assert.equal(mastery(restored, section[0].id, 'choice').mastered, false);
  assert.throws(() => mergeCatalog(entries, [{ ...section[0], id: entries[0].id }, ...section.slice(1)], sources));
  assert.throws(() => mergeCatalog(entries, section.slice(1), sources));
  assert.throws(() => mergeCatalog(entries, [section[0], ...section.slice(0, 99)], sources));
  assert.throws(() => mergeCatalog(entries, [section[0], { ...section[1], number: 1 }, ...section.slice(2)], sources));
});
