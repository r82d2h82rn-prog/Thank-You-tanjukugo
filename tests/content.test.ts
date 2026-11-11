import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ApprovedEntry, mergeCatalog } from '../src/content';
import { entries } from '../src/data';
test('reviewed content keeps existing identity and rejects unpublished content or ID reuse', () => {
  const e = { ...entries[0], content: { sourceIds: ['test-original'], contentVersion: 2, qualityStatus: 'approved', autoChecked: true, humanReviewed: true, examFrequency: null, selectionReason: 'test fixture', productionApproved: true } } as ApprovedEntry;
  const sources = [{ id: 'test-original', commercialUse: 'granted', redistribution: 'granted', licenseEvidence: 'synthetic test permission' }];
  const catalog = mergeCatalog(entries, [e], sources); assert.equal(catalog.length, 150); assert.equal(catalog.find(row => row.id === e.id), e);
  assert.throws(() => mergeCatalog(entries, [e], []));
  assert.throws(() => mergeCatalog(entries, [{ ...e, english: 'different' }], sources));
  assert.throws(() => mergeCatalog(entries, [{ ...e, content: { ...e.content, humanReviewed: false } }], sources));
  assert.throws(() => mergeCatalog(entries, [{ ...e, content: { ...e.content, qualityStatus: 'review_required' } }], sources));
});
