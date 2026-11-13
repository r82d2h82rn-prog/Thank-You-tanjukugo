import {readingRevisions} from './readingRevisions';
import legacy from '../content/readings/drafts.json';
import advanced from '../content/readings/advanced.json';
import type { Passage } from './readings';
// The legacy file is immutable; upper-level batches only append new identities.
export const readingCatalog = [...legacy,...advanced].map(p=>readingRevisions.find(e=>e.id===p.id)??p) as Passage[];
