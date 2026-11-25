import {test} from 'node:test';
import assert from 'node:assert/strict';
import batch from '../content/readings/l3_f07_next5.json';
import prior from '../content/readings/l3_f07.json';
import {readingCatalog} from '../src/readingCatalog';
import {sentenceRanges} from '../src/readingSentences';
import {readingParagraphs,gradeReading,recordReading,unlockReading} from '../src/readings';
import {emptyState,decodeState} from '../src/model';
import policy from '../content/authoring/readings/level3-word-policy.json';
const count=(text:string)=>text.match(/[A-Za-z]+(?:['-][A-Za-z]+)*/g)!.length;
test('later insertion source and completed text align with all sentence translations and syntax',()=>{
 assert.equal(batch.length,5);assert.ok(readingCatalog.length>=280);
 for(const [i,p] of batch.entries()){
  assert.deepEqual(readingCatalog.find(x=>x.id===p.id),p);assert.equal(p.format,7);
  const raw=p.paragraphs.map(x=>x.english).join(' '),completed=p.reviewParagraphs.map(x=>x.english).join(' ');
  assert.deepEqual([...raw.matchAll(/\[[A-D]\]/g)].map(x=>x[0]),['[A]','[B]','[C]','[D]']);
  assert.equal(count(raw),p.wordCount);assert.equal(count(completed),p.reviewWordCount);
  assert.ok(p.reviewWordCount>=policy.bandsByItemWithinFormat[i+5].min&&p.reviewWordCount<=policy.bandsByItemWithinFormat[i+5].max);
  assert.ok(Math.abs(p.reviewWordCount-policy.targetsByFormat['7'][i+5])<=2);
  assert.deepEqual(readingParagraphs(p,false),p.paragraphs);assert.deepEqual(readingParagraphs(p,true),p.reviewParagraphs);
  for(const para of p.reviewParagraphs){
   const rows=p.sentences.filter(s=>s.paragraphId===para.id),source=p.paragraphs.find(x=>x.id===para.id)!;
   assert.deepEqual(rows.map(s=>({id:s.id,english:s.english,start:s.start,end:s.end})),sentenceRanges(para.id,para.english));
   assert.equal(para.translation,rows.map(s=>s.translation).join(''));
   const rebuilt=source.english.replace(/\[[A-D]\]/g,m=>m===p.insertionSolution.marker?p.insert.sentence:'');assert.equal(rebuilt,para.english);
   for(const row of rows){
    assert.equal(source.english.slice(row.sourceStart,row.sourceEnd),row.sourceEnglish);
    assert.equal(row.sourceKind==='insertion'?p.insert.sentence:row.sourceEnglish,row.english);
    const sy=p.syntax.find(s=>s.id===row.syntaxId)!;assert.equal(sy.translation,row.translation);assert.equal(sy.sentence,row.english);
    for(const node of sy.spans)assert.equal(para.english.slice(node.start,node.end),node.text);
    const ids=new Set(sy.spans.map(n=>n.id));for(const edge of sy.relations){assert.ok(ids.has(edge.from));assert.ok(ids.has(edge.to));}
   }
  }
  const inserted=p.sentences.filter(s=>s.sourceKind==='insertion');assert.equal(inserted.length,1);assert.equal(inserted[0].translation,p.insert.translation);
 }
});
test('every later insertion position grades exactly and only the keyed position reconstructs the saved review',()=>{
 for(const p of batch){const answers=Object.fromEntries(p.questions.map(q=>[q.id,q.correctOptionId]));
  assert.equal(p.questions[0].options.find(o=>o.id===p.questions[0].correctOptionId)!.text,p.insertionSolution.marker);
  for(const q of p.questions){assert.ok(p.paragraphs.find(x=>x.id===q.evidence.paragraphId)!.english.includes(q.evidence.quote));
   for(const o of q.options){assert.ok(o.explanation);assert.equal(gradeReading(p,{...answers,[q.id]:o.id},200,'test').correct,p.questions.length-(o.id===q.correctOptionId?0:1));}
  }
  for(const option of p.questions[0].options){
   const reconstructed=p.paragraphs.map(para=>para.english.replace(/\[[A-D]\]/g,m=>m===option.text?p.insert.sentence:''));
   assert.equal(JSON.stringify(reconstructed)===JSON.stringify(p.reviewParagraphs.map(x=>x.english)),option.id===p.questions[0].correctOptionId);
  }
 }
});
test('later insertion results preserve earlier records, free unlocks and state round trips',()=>{
 const old=prior[0];let state=recordReading(emptyState(),old,gradeReading(old,Object.fromEntries(old.questions.map(q=>[q.id,q.correctOptionId])),100,'earlier'));
 for(const p of prior.slice(0,3))state=unlockReading(state,p);
 const before=state.reading!;
 for(const p of batch)state=recordReading(state,p,gradeReading(p,Object.fromEntries(p.questions.map(q=>[q.id,q.correctOptionId])),200,p.id));
 assert.deepEqual(state.reading!.records[old.id],before.records[old.id]);assert.deepEqual(state.reading!.unlockedByLevel,before.unlockedByLevel);
 assert.deepEqual(decodeState(JSON.stringify(state)),state);
});
