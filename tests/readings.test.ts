import { test } from 'node:test';
import assert from 'node:assert/strict';
import data from '../content/readings/drafts.json';
import checkpoint from '../analysis/reading_checkpoint.json';
import { emptyState, decodeState, answer } from '../src/model';
import { gradeReading, Passage, readingAccess, recordReading, unlockReading } from '../src/readings';
const passages=data as Passage[];
test('reading drafts match the measured quota, have evidence and exact syntax offsets',()=>{
 assert.equal(passages.length,100);
 assert.equal(checkpoint.complete,true);
 assert.equal(passages.reduce((n,p)=>n+p.questions.length,0),300);
 assert.equal(passages.length,checkpoint.authoredPassages);
 assert.equal(new Set(passages.map(p=>p.id)).size,passages.length);
 assert.deepEqual(Array.from({length:10},(_,i)=>passages.filter(p=>p.format===i+1).length),checkpoint.countsByFormat);
 if(checkpoint.complete)assert.deepEqual(checkpoint.countsByFormat,[10,10,10,10,10,10,10,10,10,10]);
 for(const p of passages){assert.ok(p.wordCount>=150&&p.wordCount<=250);assert.equal(p.questions.length,3);if(p.format===7){assert.ok(p.insert?.sentence);for(const marker of ['[A]','[B]','[C]','[D]'])assert.ok(p.paragraphs.some(x=>x.english.includes(marker)));}if(p.format===8){assert.equal(p.paragraphs.length,4);assert.equal(new Set(p.paragraphOrder).size,4);const order=p.questions[0].options.find(o=>o.id===p.questions[0].correctOptionId)!.text;assert.equal(order,p.paragraphOrder!.map(id=>id.slice(1)).join('→'));}for(const q of p.questions){assert.equal(q.options.length,4);assert.equal(new Set(q.options.map(o=>o.text)).size,4);assert.ok(p.paragraphs.find(x=>x.id===q.evidence.paragraphId)!.english.includes(q.evidence.quote));}for(const x of p.syntax){const para=p.paragraphs.find(y=>y.id===x.paragraphId)!;assert.equal(para.english.slice(x.start,x.end),x.sentence);for(const span of x.spans)assert.equal(para.english.slice(span.start,span.end),span.text);}}
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
