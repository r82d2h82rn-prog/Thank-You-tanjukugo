import drafts from '../../content/words/drafts.json';
import { authoredAdditions as additions } from './authoredAdditions';
import selection from '../../content/words/selection.json';
import { entries as samples } from './index';
import { Entry, validateEntries } from '../model';

// An ID-based placement overlay changes only editorial placement, never mastery identity.
const archivedWords = [...drafts, ...additions] as Entry[];
const byId = new Map(archivedWords.map(entry => [entry.id, entry]));
const scopedWords: Entry[] = selection.placements.map(placement => {
  const original = byId.get(placement.id);
  if (!original || ![3, 4].includes(placement.level)) throw new Error(`配置先の本文がありません: ${placement.id}`);
  return { ...original, ...placement, level: placement.level as Entry['level'] };
});
const selectedIds = new Set(scopedWords.map(e => e.id));
const lowerWords = (drafts as Entry[]).filter(e => e.level < 3);
const reservedWords = (drafts as Entry[]).filter(e => e.level >= 3 && !selectedIds.has(e.id));
if (selectedIds.size !== scopedWords.length || byId.size !== archivedWords.length || reservedWords.length !== selection.expectedReservedWords || lowerWords.length + scopedWords.length + reservedWords.length !== byId.size) throw new Error('教材の配置台帳に重複・欠落があります');
export const trialWords: Entry[] = [...lowerWords, ...scopedWords];
export const trialEntries = [...trialWords, ...samples.filter(entry => entry.kind === 'idiom')];
validateEntries(trialEntries);
export const trialWordCount = trialWords.length;
export const historicalEntries = new Map([...samples, ...archivedWords, ...trialWords].map(entry => [entry.id, entry]));
