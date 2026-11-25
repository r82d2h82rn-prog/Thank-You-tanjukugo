import {test} from 'node:test';
import assert from 'node:assert/strict';
import batch from '../content/readings/l3_f06.json';
import prior from '../content/readings/l3_f05_next5.json';
import {readingCatalog} from '../src/readingCatalog';
import {sentenceRanges} from '../src/readingSentences';
import {gradeReading,recordReading,unlockReading} from '../src/readings';
import {emptyState,decodeState} from '../src/model';
import policy from '../content/authoring/readings/level3-word-policy.json';
test('inference passages align every sentence, translation and syntax annotation and meet planned word bands',()=>{
 assert.equal(batch.length,5);assert.ok(readingCatalog.length>=265);
 for(const [i,p] of batch.entries()){
  assert.deepEqual(readingCatalog.find(x=>x.id===p.id),p);assert.equal(p.format,6);
  const count=p.paragraphs.map(x=>x.english).join(' ').match(/[A-Za-z]+(?:['-][A-Za-z]+)*/g)!.length;
  assert.equal(count,p.wordCount);assert.ok(count>=policy.bandsByItemWithinFormat[i].min&&count<=policy.bandsByItemWithinFormat[i].max);
  assert.ok(Math.abs(count-policy.targetsByFormat['6'][i])<=2);
  for(const para of p.paragraphs){
   const rows=p.sentences.filter(s=>s.paragraphId===para.id);
   assert.deepEqual(rows.map(s=>({id:s.id,english:s.english,start:s.start,end:s.end})),sentenceRanges(para.id,para.english));
   assert.equal(para.translation,rows.map(s=>s.translation).join(''));
   for(const row of rows){const sy=p.syntax.find(s=>s.id===row.syntaxId)!;assert.equal(sy.translation,row.translation);assert.equal(sy.sentence,row.english);
    for(const node of sy.spans)assert.equal(para.english.slice(node.start,node.end),node.text);
    const ids=new Set(sy.spans.map(n=>n.id));for(const edge of sy.relations){assert.ok(ids.has(edge.from));assert.ok(ids.has(edge.to));}
   }
  }
 }
});
test('all inference options grade correctly without replacing old records or free unlocks',()=>{
 const old=prior[0];let state=recordReading(emptyState(),old,gradeReading(old,Object.fromEntries(old.questions.map(q=>[q.id,q.correctOptionId])),100,'earlier'));
 for(const p of prior.slice(0,3))state=unlockReading(state,p);
 const before=state.reading!;
 for(const p of batch){const answers=Object.fromEntries(p.questions.map(q=>[q.id,q.correctOptionId]));
  for(const q of p.questions){assert.ok(p.paragraphs.find(x=>x.id===q.evidence.paragraphId)!.english.includes(q.evidence.quote));
   assert.equal(new Set(q.options.map(o=>o.text)).size,4);
   for(const o of q.options){assert.ok(o.explanation);assert.equal(gradeReading(p,{...answers,[q.id]:o.id},200,'test').correct,p.questions.length-(o.id===q.correctOptionId?0:1));}
  }
  state=recordReading(state,p,gradeReading(p,answers,200,p.id));
 }
 assert.deepEqual(state.reading!.records[old.id],before.records[old.id]);assert.deepEqual(state.reading!.unlockedByLevel,before.unlockedByLevel);
 assert.deepEqual(decodeState(JSON.stringify(state)),state);
});
