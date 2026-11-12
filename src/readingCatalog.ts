import enriched from '../content/readings/enriched.json';
import legacy from '../content/readings/drafts.json';
import advanced from '../content/readings/advanced.json';
import type { Passage } from './readings';
// The legacy file is immutable; upper-level batches only append new identities.
export const readingCatalog = [...legacy.map(p=>enriched.find(e=>e.id===p.id)??p), ...advanced] as Passage[];
