import {test} from 'node:test';
import assert from 'node:assert/strict';
import first from '../content/readings/l3_f09.json';
import next from '../content/readings/l3_f09_next5.json';
import prior from '../content/readings/l3_f08_next5.json';
import {readingCatalog} from '../src/readingCatalog';
import {sentenceRanges} from '../src/readingSentences';
import {readingParagraphs,gradeReading,recordReading,unlockReading} from '../src/readings';
import {emptyState,decodeState} from '../src/model';
import policy from '../content/authoring/readings/level3-word-policy.json';
const count=(s:string)=>s.match(/[A-Za-z]+(?:['-][A-Za-z]+)*/g)!.length;
for(const {batch,offset,sentenceCount} of [{batch:first,offset:0,sentenceCount:92},{batch:next,offset:5,sentenceCount:116}]){
test(`L3 summaries ${offset+1}–${offset+5} preserve the whole readable text with aligned translations and syntax`,()=>{
 assert.equal(batch.length,5);assert.equal(batch.reduce((n,p)=>n+p.sentences.length,0),sentenceCount);
 assert.equal(new Set(readingCatalog.map(p=>p.id)).size,readingCatalog.length);
 for(const [i,p] of batch.entries()){
  assert.deepEqual(readingCatalog.find(x=>x.id===p.id),p);assert.equal(p.format,9);
  assert.deepEqual(readingParagraphs(p,false),p.paragraphs);assert.deepEqual(readingParagraphs(p,true),p.paragraphs);
  assert.equal(count(p.paragraphs.map(x=>x.english).join(' ')),p.wordCount);
  assert.ok(p.wordCount>=policy.bandsByItemWithinFormat[i+offset].min&&p.wordCount<=policy.bandsByItemWithinFormat[i+offset].max);
  assert.ok(Math.abs(p.wordCount-policy.targetsByFormat['9'][i+offset])<=2);
  for(const para of p.paragraphs){
   const rows=p.sentences.filter(s=>s.paragraphId===para.id);
   assert.deepEqual(rows.map(s=>({id:s.id,english:s.english,start:s.start,end:s.end})),sentenceRanges(para.id,para.english));
   assert.equal(para.translation,rows.map(s=>s.translation).join(''));
   for(const row of rows){
    assert.equal(para.english.slice(row.sourceStart,row.sourceEnd),row.sourceEnglish);assert.equal(row.sourceEnglish,row.english);
    const sy=p.syntax.find(s=>s.id===row.syntaxId)!;assert.equal(sy.sentence,row.english);assert.equal(sy.translation,row.translation);
    assert.ok(sy.explanation);assert.ok(sy.spans.some(n=>n.role==='S'));assert.ok(sy.spans.some(n=>n.role==='V'));
    for(const n of sy.spans){assert.equal(para.english.slice(n.start,n.end),n.text);assert.ok(n.start>=row.start&&n.end<=row.end);}
    const ids=new Set(sy.spans.map(n=>n.id));for(const edge of sy.relations){assert.ok(ids.has(edge.from));assert.ok(ids.has(edge.to));}
   }
  }
 }
});
test(`summary ${offset+1}–${offset+5} choices are distinct extended English summaries and every option grades independently`,()=>{
 for(const p of batch){
  const summary=p.questions[0];assert.match(summary.prompt,/要約/);
  assert.equal(new Set(summary.options.map(o=>o.text)).size,4);
  for(const option of summary.options){assert.ok(count(option.text)>=28&&count(option.text)<=60);assert.ok(option.explanation);}
  const correct=Object.fromEntries(p.questions.map(q=>[q.id,q.correctOptionId]));
  for(const q of p.questions){
   assert.equal(q.options.length,4);assert.equal(q.options.filter(o=>o.id===q.correctOptionId).length,1);
   assert.ok(p.paragraphs.find(x=>x.id===q.evidence.paragraphId)!.english.includes(q.evidence.quote));
   for(const o of q.options){assert.ok(o.explanation);assert.equal(gradeReading(p,{...correct,[q.id]:o.id},300,'changed').correct,p.questions.length-(o.id===q.correctOptionId?0:1));}
  }
 }
});
test(`new summaries ${offset+1}–${offset+5} keep ordering scores and unlocks while storing independent attempts`,()=>{
 const old=prior[0];const oldAttempt=gradeReading(old,Object.fromEntries(old.questions.map(q=>[q.id,q.correctOptionId])),300,'ordering');
 let state=recordReading(emptyState(),old,oldAttempt);for(const p of prior.slice(0,3))state=unlockReading(state,p);
 const before=state.reading!;
 for(const p of batch){
  const wrong=Object.fromEntries(p.questions.map(q=>[q.id,q.options.find(o=>o.id!==q.correctOptionId)!.id]));
  const first=gradeReading(p,wrong,400,p.id+'-first');
  const best=gradeReading(p,Object.fromEntries(p.questions.map(q=>[q.id,q.correctOptionId])),300,p.id+'-best');
  state=recordReading(recordReading(state,p,first),p,best);
  assert.deepEqual(state.reading!.records[p.id].first,first);assert.deepEqual(state.reading!.records[p.id].best,best);
 }
 assert.deepEqual(state.reading!.records[old.id],before.records[old.id]);assert.deepEqual(state.reading!.unlockedByLevel,before.unlockedByLevel);
 assert.deepEqual(decodeState(JSON.stringify(state)),state);
});

}
