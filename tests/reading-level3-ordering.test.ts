import {test} from 'node:test';
import assert from 'node:assert/strict';
import first from '../content/readings/l3_f08.json';
import next from '../content/readings/l3_f08_next5.json';
import {readingCatalog} from '../src/readingCatalog';
import {sentenceRanges} from '../src/readingSentences';
import {readingParagraphs,gradeReading,recordReading,unlockReading} from '../src/readings';
import {emptyState,decodeState} from '../src/model';
import policy from '../content/authoring/readings/level3-word-policy.json';
const count=(s:string)=>s.match(/[A-Za-z]+(?:['-][A-Za-z]+)*/g)!.length;
for(const {batch,offset,sentenceCount} of [{batch:first,offset:0,sentenceCount:98},{batch:next,offset:5,sentenceCount:107}]){
test(`L3 ordering ${offset+1}–${offset+5} presents four shuffled paragraphs and restores all aligned text on review`,()=>{
 assert.equal(batch.length,5);assert.equal(batch.reduce((n,p)=>n+p.sentences.length,0),sentenceCount);
 assert.equal(new Set(readingCatalog.map(p=>p.id)).size,readingCatalog.length);
 for(const [i,p] of batch.entries()){
  assert.deepEqual(readingCatalog.find(x=>x.id===p.id),p);assert.equal(p.format,8);
  assert.deepEqual(p.paragraphs.map(x=>x.id),['p1','p2','p3','p4']);
  const source=readingParagraphs(p,false),review=readingParagraphs(p,true);
  assert.deepEqual(source,p.paragraphs);assert.deepEqual(review.map(x=>x.id),p.paragraphOrder);
  assert.deepEqual([...p.paragraphOrder].sort(),source.map(x=>x.id));
  assert.equal(count(review.map(x=>x.english).join(' ')),p.wordCount);
  assert.ok(p.wordCount>=policy.bandsByItemWithinFormat[i+offset].min&&p.wordCount<=policy.bandsByItemWithinFormat[i+offset].max);
  assert.ok(Math.abs(p.wordCount-policy.targetsByFormat['8'][i+offset])<=2);
  assert.equal(p.questions[0].options.find(o=>o.id===p.questions[0].correctOptionId)!.text,p.paragraphOrder.map(x=>x.slice(1)).join('→'));
  for(const para of review){
   const rows=p.sentences.filter(s=>s.paragraphId===para.id);
   assert.deepEqual(rows.map(s=>({id:s.id,english:s.english,start:s.start,end:s.end})),sentenceRanges(para.id,para.english));
   assert.equal(para.translation,rows.map(s=>s.translation).join(''));
   for(const row of rows){
    assert.equal(para.english.slice(row.sourceStart,row.sourceEnd),row.sourceEnglish);assert.equal(row.sourceEnglish,row.english);
    const sy=p.syntax.find(s=>s.id===row.syntaxId)!;
    assert.equal(sy.sentence,row.english);assert.equal(sy.translation,row.translation);assert.ok(sy.explanation);
    assert.ok(sy.spans.some(s=>s.role==='S'));assert.ok(sy.spans.some(s=>s.role==='V'));
    for(const node of sy.spans){assert.equal(para.english.slice(node.start,node.end),node.text);assert.ok(node.start>=row.start&&node.end<=row.end);}
    const ids=new Set(sy.spans.map(n=>n.id));for(const edge of sy.relations){assert.ok(ids.has(edge.from));assert.ok(ids.has(edge.to));}
   }
  }
 }
});
test(`L3 ordering ${offset+1}–${offset+5} validates each offered permutation, all option grades and retained independent attempts`,()=>{
 for(const p of batch){
  const answers=Object.fromEntries(p.questions.map(q=>[q.id,q.correctOptionId]));
  const q1=p.questions[0];assert.equal(new Set(q1.options.map(o=>o.text)).size,4);
  for(const o of q1.options){
   const ids=o.text.split('→').map(x=>'p'+x);assert.deepEqual([...ids].sort(),['p1','p2','p3','p4']);
   assert.equal(JSON.stringify(ids)===JSON.stringify(p.paragraphOrder),o.id===q1.correctOptionId);
  }
  for(const q of p.questions){
   assert.equal(q.options.length,4);assert.ok(p.paragraphs.find(para=>para.id===q.evidence.paragraphId)!.english.includes(q.evidence.quote));
   for(const o of q.options){assert.ok(o.explanation);assert.equal(gradeReading(p,{...answers,[q.id]:o.id},360,'option').correct,p.questions.length-(q.correctOptionId===o.id?0:1));}
  }
  const first=gradeReading(p,Object.fromEntries(p.questions.map(q=>[q.id,q.options.find(o=>o.id!==q.correctOptionId)!.id])),300,'first'),latest=gradeReading(p,answers,400,'latest');
  const state=recordReading(recordReading(emptyState(),p,first),p,latest);
  assert.deepEqual(state.reading!.records[p.id].first,first);assert.deepEqual(state.reading!.records[p.id].best,latest);
  assert.deepEqual(decodeState(JSON.stringify(state)),state);
 }
 const state=unlockReading(unlockReading(emptyState(),batch[0]),batch[1]);
 assert.deepEqual(decodeState(JSON.stringify(state)),state);
});
test(`L3 ordering ${offset+1}–${offset+5} rejects incomplete or duplicated review orders`,()=>{
 for(const p of batch){
  assert.throws(()=>readingParagraphs({...p,paragraphOrder:p.paragraphOrder.slice(1)},true));
  assert.throws(()=>readingParagraphs({...p,paragraphOrder:['p1','p1','p3','p4']},true));
  assert.throws(()=>readingParagraphs({...p,paragraphOrder:['p1','p2','p3','missing']},true));
 }
});

}
