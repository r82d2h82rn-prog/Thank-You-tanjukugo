import { test } from 'node:test';
import assert from 'node:assert/strict';
import { trialEntries, trialWordCount } from '../src/data/trial';
import { answer, decodeState, emptyState, mastery, State } from '../src/model';
import { canTakeExam, consumeDiagnostic, examChoices, examKey, examQuestions, ExamSpec, finishExam, gradeExam } from '../src/exams';
const spec: ExamSpec = { type: 'diagnostic', level: 4, kind: 'word', mode: 'choice', section: 10, catalog: 'draft' };
test('all 3900 selected words and ten complete level-4 sections are usable with full content', () => {
  assert.equal(trialWordCount,3900);
  const rows = trialEntries.filter(e => e.kind === 'word' && e.level === 4);
  assert.equal(rows.length,1000);assert.equal(new Set(rows.map(e => e.id)).size,1000);
  for (let section=1;section<=10;section++) {
    const entries=rows.filter(e=>e.section===section);assert.equal(entries.length,100);
    for (const e of entries) for (const field of ['meaning','pronunciation','example','translation','explanation'] as const) assert.ok(e[field].trim());
  }
});
test('diagnostic consumes one opportunity but commits no mastery until all answers are present', () => {
  const original=emptyState();const state=consumeDiagnostic(original,spec);const questions=examQuestions(trialEntries,spec);
  assert.equal(canTakeExam(state,trialEntries,spec),false);assert.deepEqual(state.progress,original.progress);
  assert.throws(()=>finishExam(state,spec,questions,questions.slice(0,99).map(entry=>({entry,correct:true,response:entry.meaning}))));
  const result=finishExam(state,spec,questions,questions.map((entry,i)=>({entry,correct:i<95,response:i<95?entry.meaning:'わからない'})));
  assert.equal(result.exams?.[examKey(spec)].passed,true);assert.equal(mastery(result,questions[0].id,'choice').mastered,true);
  assert.equal(mastery(result,questions[0].id,'written').mastered,false);assert.equal(mastery(result,questions[99].id,'choice').mastered,false);
  assert.deepEqual(decodeState(JSON.stringify(result)),result);
  const options=examChoices(questions[0],trialEntries);assert.equal(options.length,8);assert.equal(new Set(options).size,8);assert.ok(options.includes(questions[0].meaning));
});
test('failed section exam demotes only missed items in its mode and preserves permanent passes', () => {
  const section={...spec,type:'section' as const};const questions=examQuestions(trialEntries,section);let state=emptyState();
  for(const e of questions)for(const mode of ['choice','written'] as const)state=answer(answer(state,e.id,mode,true),e.id,mode,true);
  assert.equal(canTakeExam(state,trialEntries,section),true);
  const passed=finishExam(state,section,questions,questions.map(entry=>({entry,correct:true,response:entry.meaning})));
  const failed=finishExam(passed,section,questions,questions.map((entry,i)=>({entry,correct:i<94,response:'test'})));
  assert.equal(failed.exams?.[examKey(section)].passed,true);assert.equal(failed.exams?.[examKey(section)].latest,94);
  assert.equal(canTakeExam(failed,trialEntries,section),false);assert.equal(mastery(failed,questions[99].id,'choice').mastered,false);assert.equal(mastery(failed,questions[99].id,'written').mastered,true);
});
test('level examinations require all same-mode section passes and sample evenly from each section', () => {
  const level={...spec,type:'level' as const,section:undefined};let state:State=emptyState();assert.equal(canTakeExam(state,trialEntries,level),false);
  for(let section=1;section<=10;section++)state={...state,exams:{...state.exams,[examKey({...spec,type:'section',section})]:{passed:true}}};
  assert.equal(canTakeExam(state,trialEntries,level),true);assert.equal(canTakeExam(state,trialEntries,{...level,mode:'written'}),false);
  const questions=examQuestions(trialEntries,level);for(let section=1;section<=10;section++)assert.equal(questions.filter(e=>e.section===section).length,10);
  const passed=finishExam(state,level,questions,questions.map(entry=>({entry,correct:true,response:entry.meaning})));
  assert.ok(passed.permanentAwards.includes('draft:level:4:word:choice'));
  const failed=finishExam(passed,level,questions,questions.map(entry=>({entry,correct:false,response:'時間切れ'})));
  assert.equal(canTakeExam(failed,trialEntries,level),true);assert.deepEqual(failed.permanentAwards,passed.permanentAwards);
  assert.equal(gradeExam(questions[0],` ${questions[0].english.toUpperCase()} `),true);assert.equal(gradeExam(questions[0],questions[0].english+'x'),false);
});
