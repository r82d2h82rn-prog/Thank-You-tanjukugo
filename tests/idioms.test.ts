import { test } from 'node:test';
import assert from 'node:assert/strict';
import samples from '../src/data/entries.json';
import authored from '../content/idioms/drafts.json';
import { trialEntries, historicalEntries, trialWordCount, trialIdiomCount } from '../src/data/trial';
import { answer, decodeState, emptyState, mastery, State } from '../src/model';
import { canTakeExam, consumeDiagnostic, examKey, examQuestions, finishExam, gradeExam, ExamSpec } from '../src/exams';

test('all four idiom levels contain exactly 2000 complete usable entries without duplicate identities', () => {
  assert.equal(trialWordCount,3900);assert.equal(trialIdiomCount,2000);assert.equal(authored.length,1950);
  const rows=trialEntries.filter(e=>e.kind==='idiom');assert.deepEqual([1,2,3,4].map(l=>rows.filter(e=>e.level===l).length),[300,500,700,500]);
  assert.equal(new Set(rows.map(e=>e.english.toLowerCase())).size,2000);assert.equal(new Set(rows.map(e=>e.id)).size,2000);
  for(const level of [1,2,3,4])for(let section=1;section<=[6,10,14,10][level-1];section++) {
    const group=rows.filter(e=>e.level===level&&e.section===section);assert.equal(group.length,50);assert.deepEqual(group.map(e=>e.number).sort((a,b)=>a-b),Array.from({length:50},(_,i)=>i+1));
    for(const entry of group)for(const field of ['english','meaning','example','translation','explanation','pronunciation'] as const)assert.ok(entry[field].trim());
  }
  for(const old of samples.filter(e=>e.kind==='idiom')) {
    assert.deepEqual(trialEntries.find(e=>e.id===old.id),old);assert.equal(historicalEntries.get(old.id)?.english,old.english);
  }
});
test('idiom exams use 50 questions and a 48-point threshold; mastery and old histories remain independent', () => {
  const spec:ExamSpec={type:'diagnostic',level:2,kind:'idiom',mode:'choice',section:10,catalog:'draft'};
  const questions=examQuestions(trialEntries,spec);assert.equal(questions.length,50);
  const old=samples.find(e=>e.kind==='idiom')!;const state=answer(answer(emptyState(),old.id,'written',true),old.id,'written',true);
  const result=finishExam(consumeDiagnostic(state,spec),spec,questions,questions.map((entry,i)=>({entry,correct:i<48,response:i<48?entry.meaning:'時間切れ'})));
  assert.equal(result.exams?.[examKey(spec)].passed,true);assert.deepEqual(mastery(result,old.id,'written'),mastery(state,old.id,'written'));
  assert.equal(mastery(result,questions[0].id,'choice').mastered,true);assert.equal(mastery(result,questions[0].id,'written').mastered,false);
  const failed=finishExam(consumeDiagnostic(state,spec),spec,questions,questions.map((entry,i)=>({entry,correct:i<47,response:'test'})));
  assert.equal(failed.exams?.[examKey(spec)].passed,false);assert.deepEqual(decodeState(JSON.stringify(result)),result);
  assert.equal(gradeExam(questions[0],questions[0].english.toUpperCase()),true);assert.equal(gradeExam(questions[0],questions[0].english+' extra'),false);
});
test('each level idiom exam is independently gated and samples evenly across all completed sections', () => {
  for(const level of [1,2,3,4] as const) {
    const spec:ExamSpec={type:'level',level,kind:'idiom',mode:'choice',catalog:'draft'};
    let state:State=emptyState();assert.equal(canTakeExam(state,trialEntries,spec),false);
    for(let section=1;section<=[6,10,14,10][level-1];section++)state={...state,exams:{...state.exams,[examKey({...spec,type:'section',section})]:{passed:true}}};
    assert.equal(canTakeExam(state,trialEntries,spec),true);assert.equal(canTakeExam(state,trialEntries,{...spec,kind:'word'}),false);assert.equal(canTakeExam(state,trialEntries,{...spec,mode:'written'}),false);
    const questions=examQuestions(trialEntries,spec);assert.equal(questions.length,100);assert.equal(new Set(questions.map(e=>e.id)).size,100);
    const counts=[...new Set(questions.map(e=>e.section))].map(s=>questions.filter(e=>e.section===s).length);assert.ok(Math.max(...counts)-Math.min(...counts)<=1);
  }
});
