import type { Level, State } from './model';
export const readingFormats = ['内容一致','語句空所補充','文・節の空所補充','主題・タイトル','指示語','推論','文挿入','段落整序','要約','語句の意味推測'];
export interface Paragraph { id: string; english: string; translation: string }
export interface ReadingQuestion { id: string; prompt: string; options: { id: string; text: string; explanation: string }[]; correctOptionId: string; explanation: string; evidence: { paragraphId: string; quote: string } }
export interface SyntaxNode { id: string; role: 'S'|'V'|'O'|'C'|'M'|'clause'|'phrase'; text: string; start: number; end: number }
export interface ReadingSyntax { id: string; paragraphId: string; sentence: string; start: number; end: number; translation: string; explanation: string; spans: SyntaxNode[]; relations: {from:string;to:string;type:string}[] }
export interface Passage { id: string; level: Level; format: number; title: string; paragraphs: Paragraph[]; questions: ReadingQuestion[]; syntax: ReadingSyntax[]; recommendedSeconds: number; wordCount: number; vocabulary: {english:string;meaning:string}[]; paragraphOrder?: string[]; insert?: {sentence:string;translation:string} }
export interface ReadingAttempt { id: string; correct: number; total: number; elapsedSeconds: number; submittedAt: string; answers: Record<string,string> }
export interface ReadingRecord { attempts: number; first: ReadingAttempt; best: ReadingAttempt; latest: ReadingAttempt }
export interface ReadingState { unlockedByLevel: Partial<Record<Level,string[]>>; records: Record<string,ReadingRecord> }
export const emptyReading = (): ReadingState => ({unlockedByLevel:{},records:{}});
export const readingAccess = (state: State,p: Passage,premium:boolean) => premium || !!state.reading?.unlockedByLevel[p.level]?.includes(p.id);
export function unlockReading(state:State,p:Passage):State {
 const r=state.reading??emptyReading(),ids=r.unlockedByLevel[p.level]??[];
 if(ids.includes(p.id)||ids.length>=3)return state;
 return {...state,reading:{...r,unlockedByLevel:{...r.unlockedByLevel,[p.level]:[...ids,p.id]}}};
}
export function gradeReading(p:Passage,answers:Record<string,string>,elapsedSeconds:number,id:string,at=new Date().toISOString()):ReadingAttempt {
 if(!id||!Number.isFinite(elapsedSeconds)||elapsedSeconds<0||Object.keys(answers).length!==p.questions.length||p.questions.some(q=>!q.options.some(o=>o.id===answers[q.id])))throw new Error('全設問への有効な回答が必要です');
 return {id,correct:p.questions.filter(q=>answers[q.id]===q.correctOptionId).length,total:p.questions.length,elapsedSeconds:Math.round(elapsedSeconds),submittedAt:at,answers:{...answers}};
}
export function recordReading(state:State,p:Passage,a:ReadingAttempt):State {
 const r=state.reading??emptyReading(),old=r.records[p.id];
 if(old?.latest.id===a.id)return state;
 const better=!old||a.correct/a.total>old.best.correct/old.best.total||(a.correct/a.total===old.best.correct/old.best.total&&a.elapsedSeconds<old.best.elapsedSeconds);
 return {...state,reading:{...r,records:{...r.records,[p.id]:{attempts:(old?.attempts??0)+1,first:old?.first??a,best:better?a:old!.best,latest:a}}}};
}
export function validateReadingState(r:ReadingState):void {
 if(!r||typeof r!=='object'||!r.unlockedByLevel||typeof r.unlockedByLevel!=='object'||!r.records||typeof r.records!=='object')throw new Error('長文の保存データが破損しています');
 for(const [level,ids] of Object.entries(r.unlockedByLevel))if(!['1','2','3','4'].includes(level)||!Array.isArray(ids)||ids.length>3||new Set(ids).size!==ids.length||ids.some(id=>typeof id!=='string'||!id))throw new Error('長文の解放記録が破損しています');
 for(const value of Object.values(r.records)) {
  if(!value||!Number.isInteger(value.attempts)||value.attempts<1)throw new Error('長文の成績が破損しています');
  for(const a of [value.first,value.best,value.latest])if(!a||!a.id||!Number.isInteger(a.correct)||!Number.isInteger(a.total)||a.total<1||a.correct<0||a.correct>a.total||!Number.isFinite(a.elapsedSeconds)||a.elapsedSeconds<0||typeof a.submittedAt!=='string'||!a.answers||typeof a.answers!=='object'||Object.values(a.answers).some(v=>typeof v!=='string'))throw new Error('長文の成績が破損しています');
 }
}
export const duration = (s:number) => `${Math.floor(s/60)}:${String(Math.floor(s%60)).padStart(2,'0')}`;
