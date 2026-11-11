import data from './entries.json';
import { Entry, validateEntries } from '../model';
export const entries = data as Entry[];
validateEntries(entries);
export const levelNames = ['高校入試', '高校初級〜中級', '高校上級・大学受験中級', '最難関大学'];
export const targetCounts = [{ word: 800, idiom: 300 }, { word: 900, idiom: 500 }, { word: 1200, idiom: 700 }, { word: 1000, idiom: 500 }];
