import { answer, Entry, Kind, Level, mastery, Mode, normalize, shuffle, State } from './model';
export type ExamType = 'diagnostic' | 'section' | 'level';
export interface ExamSpec { type: ExamType; level: Level; kind: Kind; mode: Mode; section?: number; catalog: 'draft' | 'sample' }
export interface ExamRecord { diagnosticUsed?: boolean; passed?: boolean; best?: number; latest?: number; attempts?: number; completedAt?: string }
export type ExamRecords = Record<string, ExamRecord>;
export interface ExamAnswer { entry: Entry; correct: boolean; response: string }
export const examKey = (spec: ExamSpec) => `${spec.catalog}:${spec.level}:${spec.kind}:${spec.mode}:${spec.type === 'level' ? 'level' : spec.section}`;
export const examPool = (entries: Entry[], spec: ExamSpec) => entries.filter(e => e.level === spec.level && e.kind === spec.kind && (spec.type === 'level' || e.section === spec.section));
export function canTakeExam(state: State, entries: Entry[], spec: ExamSpec): boolean {
  const pool = examPool(entries, spec), size = spec.kind === 'word' ? 100 : 50;
  const sections = [...new Set(pool.map(e => e.section))];
  if (!pool.length || sections.some(s => pool.filter(e => e.section === s).length !== size)) return false;
  if (spec.type === 'diagnostic') return spec.mode === 'choice' && !state.exams?.[examKey(spec)]?.diagnosticUsed;
  if (spec.type === 'section') return pool.every(e => mastery(state, e.id, spec.mode).mastered);
  const expected = spec.kind === 'word' ? [8, 9, 12, 10][spec.level - 1] : [6, 10, 14, 10][spec.level - 1];
  return sections.length === expected && sections.every(section => state.exams?.[examKey({ ...spec, type: 'section', section })]?.passed);
}
export function examQuestions(entries: Entry[], spec: ExamSpec): Entry[] {
  const pool = examPool(entries, spec);
  if (spec.type !== 'level') return shuffle(pool);
  const sections = [...new Set(pool.map(e => e.section))].sort((a,b) => a-b);
  const base = Math.floor(100 / sections.length), extra = 100 % sections.length;
  return shuffle(sections.flatMap((s,i) => shuffle(pool.filter(e => e.section === s)).slice(0, base + (i < extra ? 1 : 0))));
}
export function examChoices(entry: Entry, entries: Entry[]): string[] {
  return shuffle([entry.meaning, ...shuffle([...new Set(entries.filter(e => e.kind === entry.kind).map(e => e.meaning))].filter(m => m !== entry.meaning)).slice(0,7)]);
}
export function consumeDiagnostic(state: State, spec: ExamSpec): State {
  const key = examKey(spec);
  return { ...state, exams: { ...state.exams, [key]: { ...state.exams?.[key], diagnosticUsed: true } } };
}
export function finishExam(state: State, spec: ExamSpec, questions: Entry[], answers: ExamAnswer[], at = new Date().toISOString()): State {
  const expected = spec.type === 'level' || spec.kind === 'word' ? 100 : 50;
  if (questions.length !== expected || answers.length !== expected || new Set(questions.map(e => e.id)).size !== expected || answers.some((a,i) => a.entry.id !== questions[i].id)) throw new Error('全問完了した試験だけ確定できます');
  let result = state;
  for (const a of answers) {
    if (spec.type === 'diagnostic' && !a.correct) continue;
    result = answer(result, a.entry.id, spec.mode, a.correct, at);
    // A successful exam answer certifies mastery immediately, independently per mode.
    if (a.correct) {
      const record = mastery(result, a.entry.id, spec.mode);
      result = { ...result, progress: { ...result.progress, [a.entry.id]: { ...result.progress[a.entry.id], [spec.mode]: { ...record, streak: Math.max(2, record.streak), mastered: true, masteredAt: record.masteredAt ?? at } } } };
    }
  }
  const score = answers.filter(a => a.correct).length, passed = score >= (expected === 50 ? 48 : 95);
  const key = examKey(spec), previous = result.exams?.[key];
  result = { ...result, exams: { ...result.exams, [key]: { ...previous, diagnosticUsed: previous?.diagnosticUsed || spec.type === 'diagnostic', passed: previous?.passed || passed, best: Math.max(previous?.best ?? 0, score), latest: score, attempts: (previous?.attempts ?? 0) + 1, completedAt: at } } };
  if (spec.type === 'level' && passed) {
    const award = `${spec.catalog}:level:${spec.level}:${spec.kind}:${spec.mode}`;
    result = { ...result, permanentAwards: [...new Set([...result.permanentAwards, award])] };
  }
  return result;
}
export const gradeExam = (entry: Entry, response: string) => normalize(entry.english) === normalize(response);
