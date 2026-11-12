import drafts from '../../content/words/drafts.json';
import { entries as samples } from './index';
import { Entry, validateEntries } from '../model';

// Trial access never grants editorial approval or rewrites published/sample IDs.
export const trialWords = drafts as Entry[];
export const trialEntries = [...trialWords, ...samples.filter(entry => entry.kind === 'idiom')];
validateEntries(trialEntries);
export const trialWordCount = trialWords.length;
export const historicalEntries = new Map([...samples, ...trialEntries].map(entry => [entry.id, entry]));
