import { test } from 'node:test';
import assert from 'node:assert/strict';
import lowerEnriched from '../content/readings/enriched.json';
import upperEnriched from '../content/readings/enriched-level3.json';
const enriched=[...lowerEnriched,...upperEnriched];
import { readingCatalog as data } from '../src/readingCatalog';
import checkpoint from '../analysis/reading_checkpoint.json';
import { emptyState, decodeState, answer } from '../src/model';
import { gradeReading, Passage, readingAccess, recordReading, unlockReading } from '../src/readings';
const passages=data as Passage[];
test('reading drafts match the measured quota, have evidence and exact syntax offsets',()=>{
 assert.ok(passages.length>=200 && passages.length<=400);
 assert.equal(checkpoint.complete,passages.length===400);
 assert.equal(passages.reduce((n,p)=>n+p.questions.length,0),checkpoint.totalQuestions+enriched.reduce((n,p)=>n+p.questions.length-3,0));
 assert.equal(passages.length,checkpoint.authoredPassages);
 assert.equal(new Set(passages.map(p=>p.id)).size,passages.length);
 for(const level of [1,2] as const){
  const pool=passages.filter(p=>p.level===level);assert.equal(pool.length,100);
  assert.deepEqual(Array.from({length:10},(_,i)=>pool.filter(p=>p.format===i+1).length),[10,10,10,10,10,10,10,10,10,10]);
  assert.deepEqual(checkpoint.levels[String(level) as '1'|'2'].countsByFormat,[10,10,10,10,10,10,10,10,10,10]);
 }
 for(const p of passages){assert.ok(p.wordCount>=({1:150,2:160,3:190,4:210}[p.level])&&p.wordCount<=({1:250,2:320,3:600,4:420}[p.level]));assert.ok(p.questions.length>=3&&p.questions.length<=10);if(p.format===7){assert.ok(p.insert?.sentence);for(const marker of ['[A]','[B]','[C]','[D]'])assert.ok(p.paragraphs.some(x=>x.english.includes(marker)));}if(p.format===8){assert.equal(p.paragraphs.length,4);assert.equal(new Set(p.paragraphOrder).size,4);const order=p.questions[0].options.find(o=>o.id===p.questions[0].correctOptionId)!.text;assert.equal(order,p.paragraphOrder!.map(id=>id.slice(1)).join('→'));}for(const q of p.questions){assert.equal(q.options.length,4);assert.equal(new Set(q.options.map(o=>o.text)).size,4);assert.ok(p.paragraphs.find(x=>x.id===q.evidence.paragraphId)!.english.includes(q.evidence.quote));}for(const x of p.syntax){const para=(p.reviewParagraphs??p.paragraphs).find(y=>y.id===x.paragraphId)!;assert.equal(para.english.slice(x.start,x.end),x.sentence);for(const span of x.spans)assert.equal(para.english.slice(span.start,span.end),span.text);}}
});
test('three free reading unlocks require explicit calls, persist, and never replace earlier choices',()=>{
 let state=answer(emptyState(),'old-word','choice',true);const original=state.progress;
 assert.equal(readingAccess(state,passages[0],false),false);
 for(const p of passages.slice(0,3))state=unlockReading(state,p);
 const before=state;state=unlockReading(state,passages[3]);assert.equal(state,before);assert.equal(readingAccess(state,passages[3],false),false);assert.equal(readingAccess(state,passages[3],true),true);
 assert.equal(unlockReading(state,passages[0]),state);assert.deepEqual(state.progress,original);
 const other={...passages[3],id:'level2-example',level:2 as const};state=unlockReading(state,other);assert.equal(readingAccess(state,other,false),true);
 assert.deepEqual(decodeState(JSON.stringify(state)),state);assert.equal(decodeState(JSON.stringify(emptyState())).reading,undefined);
});
test('reading submission grades once, keeps first and latest, and compares best by accuracy then time',()=>{
 const p=passages[0],answers=Object.fromEntries(p.questions.map(q=>[q.id,q.correctOptionId]));
 assert.throws(()=>gradeReading(p,{},20,'bad'));
 const first=gradeReading(p,answers,500,'first');let state=recordReading(emptyState(),p,first);assert.equal(recordReading(state,p,first),state);
 const faster=gradeReading(p,answers,200,'second');state=recordReading(state,p,faster);
 const wrong={...answers,[p.questions[0].id]:p.questions[0].options.find(o=>o.id!==p.questions[0].correctOptionId)!.id};const latest=gradeReading(p,wrong,10,'third');state=recordReading(state,p,latest);
 const r=state.reading!.records[p.id];assert.equal(r.attempts,3);assert.equal(r.first.id,'first');assert.equal(r.best.id,'second');assert.equal(r.latest.id,'third');assert.equal(first.elapsedSeconds,500);assert.equal(first.correct,p.questions.length);
 assert.deepEqual(decodeState(JSON.stringify(state)),state);
});
test('corrupt reading records are rejected without accepting arrays as maps',()=>{
 for(const reading of [[],{unlockedByLevel:[],records:{}},{unlockedByLevel:{},records:[]},{unlockedByLevel:{1:['x','x']},records:{}}])assert.throws(()=>decodeState(JSON.stringify({...emptyState(),reading})));
 const p=passages[0],answers=Object.fromEntries(p.questions.map(q=>[q.id,q.correctOptionId]));
 const state=recordReading(emptyState(),p,gradeReading(p,answers,10,'valid'));
 const invalid=JSON.parse(JSON.stringify(state));invalid.reading.records[p.id].latest.answers=[];
 assert.throws(()=>decodeState(JSON.stringify(invalid)));
 assert.throws(()=>gradeReading(p,{...answers,unexpected:'a'},20,'extra'));
 assert.throws(()=>gradeReading(p,answers,-1,'negative'));
});

test('real Level 2 passages preserve Level 1 unlocks, results and independent free slots',()=>{
 const l1=passages.filter(p=>p.level===1),l2=passages.filter(p=>p.level===2);
 const answers=Object.fromEntries(l1[0].questions.map(q=>[q.id,q.correctOptionId]));
 let state=recordReading(emptyState(),l1[0],gradeReading(l1[0],answers,120,'level1-existing'));
 for(const p of l1.slice(0,3))state=unlockReading(state,p);
 const original=state.reading!.records[l1[0].id];
 for(const p of l2.slice(0,3))state=unlockReading(state,p);
 assert.equal(state.reading!.records[l1[0].id],original);
 assert.deepEqual(state.reading!.unlockedByLevel[1],l1.slice(0,3).map(p=>p.id));
 assert.deepEqual(state.reading!.unlockedByLevel[2],l2.slice(0,3).map(p=>p.id));
 assert.equal(unlockReading(state,l2[3]),state);
 const a=Object.fromEntries(l2[0].questions.map(q=>[q.id,q.correctOptionId]));
 state=recordReading(state,l2[0],gradeReading(l2[0],a,240,'level2-attempt'));
 assert.equal(state.reading!.records[l1[0].id],original);
 assert.equal(state.reading!.records[l2[0].id].best.correct,l2[0].questions.length);
 assert.deepEqual(decodeState(JSON.stringify(state)),state);
});
