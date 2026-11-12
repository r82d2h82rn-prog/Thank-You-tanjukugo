import type { ExamRecords } from "./exams";
export type Mode = 'choice' | 'written';
export type Kind = 'word' | 'idiom';
export type Level = 1 | 2 | 3 | 4;
export interface Entry { id: string; number: number; level: Level; section: number; kind: Kind; english: string; meaning: string; pos: string; pronunciation: string; example: string; translation: string; explanation: string; acceptedAnswers: string[] }
export interface Attempt { id: string; at: string; correct: boolean }
export interface Mastery { streak: number; mastered: boolean; history: Attempt[]; lastAnsweredAt?: string; lastResult?: boolean; masteredAt?: string | null }
export interface State { exams?: ExamRecords; version: 1; progress: Record<string, Partial<Record<Mode, Mastery>>>; favorites: string[]; settings: { sound: boolean; speech: boolean }; lastSection?: { level: Level; kind: Kind; section: number; mode?: Mode; catalog?: 'sample' | 'draft' }; permanentAwards: string[] }
export const emptyState = (): State => ({ version: 1, progress: {}, favorites: [], settings: { sound: true, speech: false }, permanentAwards: [] });
export const mastery = (state: State, id: string, mode: Mode): Mastery => state.progress[id]?.[mode] ?? { streak: 0, mastered: false, history: [] };
export function answer(state: State, id: string, mode: Mode, correct: boolean, at = new Date().toISOString()): State {
  const previous = mastery(state, id, mode);
  const streak = correct ? previous.streak + 1 : 0;
  return { ...state, progress: { ...state.progress, [id]: { ...state.progress[id], [mode]: { streak, mastered: streak >= 2, lastAnsweredAt: at, lastResult: correct, masteredAt: streak >= 2 ? (previous.masteredAt ?? at) : null, history: [...previous.history, { id: `${at}-${previous.history.length}`, at, correct }] } } } };
}
export function normalize(value: string) { return value.trim().toLowerCase(); }
export function grade(entry: Entry, value: string) { return [entry.english, ...entry.acceptedAnswers].some(a => normalize(a) === normalize(value)); }
export function shuffle<T>(items: readonly T[], random = Math.random): T[] { const result = [...items]; for (let i = result.length - 1; i > 0; i--) { const j = Math.floor(random() * (i + 1)); [result[i], result[j]] = [result[j], result[i]]; } return result; }
export function choices(entry: Entry, pool: Entry[]): string[] { return shuffle([entry.meaning, ...shuffle([...new Set(pool.map(e => e.meaning))].filter(m => m !== entry.meaning)).slice(0, 3)]); }
export function validateEntries(entries: Entry[]) {
  const ids = new Set<string>(); const labels = new Set<string>();
  for (const e of entries) {
    if (ids.has(e.id) || labels.has(`${e.kind}:${e.english}`)) throw new Error(`教材の重複: ${e.id}`);
    if (!e.id || !e.english || !e.meaning || !e.example || !e.translation || !e.pronunciation || e.level < 1 || e.level > 4 || e.section < 1) throw new Error(`教材の不備: ${e.id}`);
    ids.add(e.id); labels.add(`${e.kind}:${e.english}`);
  }
}
export function decodeState(raw: string | null): State {
  if (raw === null) return emptyState();
  const s = JSON.parse(raw);
  if (s.version !== 1 || typeof s.progress !== 'object' || !s.progress || !Array.isArray(s.favorites) || !s.favorites.every((x: unknown) => typeof x === 'string') || typeof s.settings?.sound !== 'boolean' || typeof s.settings?.speech !== 'boolean' || !Array.isArray(s.permanentAwards)) throw new Error('保存データの形式に対応していません');
  for (const modes of Object.values(s.progress)) {
    if (!modes || typeof modes !== 'object') throw new Error('習得データが破損しています');
    for (const record of Object.values(modes)) {
      const r = record as Mastery;
      if (!r || !Number.isInteger(r.streak) || r.streak < 0 || r.mastered !== (r.streak >= 2) || !Array.isArray(r.history) || !r.history.every(h => typeof h.at === 'string' && typeof h.correct === 'boolean')) throw new Error('学習履歴が破損しています');
    }
  }
  if (s.exams !== undefined) {
    if (!s.exams || typeof s.exams !== 'object' || Array.isArray(s.exams)) throw new Error('試験記録が破損しています');
    for (const r of Object.values(s.exams) as import('./exams').ExamRecord[]) {
      if (!r || typeof r !== 'object' || (r.passed !== undefined && typeof r.passed !== 'boolean') || (r.diagnosticUsed !== undefined && typeof r.diagnosticUsed !== 'boolean') || ['best','latest','attempts'].some(k => { const n = r[k as 'best']; return n !== undefined && (!Number.isInteger(n) || n < 0 || (k !== 'attempts' && n > 100)); })) throw new Error('試験記録が破損しています');
    }
  }
  return s as State;
}
