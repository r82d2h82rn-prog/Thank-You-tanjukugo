import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import batch from '../content/readings/enriched-level3.json';
import original from '../content/readings/advanced.json';
import {readingCatalog} from '../src/readingCatalog';
import {gradeReading,recordReading} from '../src/readings';
import {emptyState} from '../src/model';
import {sentenceRanges} from '../src/readingSentences';
test('Level 3 first five overlays cover every sentence and retain original IDs, text, answers and scores',()=>{
 assert.equal(batch.length,5);assert.deepEqual(batch.map(p=>p.questions.length),[6,7,5,8,6]);
 assert.deepEqual(batch.map(p=>p.paragraphs.length),[5,6,5,7,6]);
 assert.equal(batch.reduce((n,p)=>n+p.sentences.length,0),118);
 for(const p of batch){
  const old=original.find(x=>x.id===p.id)!;
  assert.equal(p.content.contentVersion,old.content.contentVersion+1);
  assert.equal(p.content.humanReviewed,false);assert.equal(p.content.productionApproved,false);
  assert.deepEqual(p.previousSyntax,old.syntax);assert.deepEqual(p.questions.slice(0,3),old.questions);
  assert.deepEqual(p.paragraphs.slice(0,3).map(x=>[x.id,x.english]),old.paragraphs.map(x=>[x.id,x.english]));
  assert.deepEqual(readingCatalog.find(x=>x.id===p.id),p);
  const words=p.paragraphs.map(x=>x.english).join(' ').match(/[A-Za-z]+(?:['-][A-Za-z]+)*/g)!.length;
  assert.equal(words,p.wordCount);assert.ok(words>=400&&words<=600);
  for(const para of p.paragraphs){
   const sentences=p.sentences.filter(s=>s.paragraphId===para.id);
   assert.deepEqual(sentences.map(s=>({id:s.id,english:s.english,start:s.start,end:s.end})),sentenceRanges(para.id,para.english));
   assert.equal(para.translation,sentences.map(s=>s.translation).join(''));
   for(const s of sentences){const syntax=p.syntax.find(x=>x.id===s.syntaxId)!;assert.ok(syntax);assert.equal(syntax.translation,s.translation);assert.ok(syntax.explanation);}
  }
  const answers=Object.fromEntries(p.questions.map(q=>[q.id,q.correctOptionId]));
  for(const q of p.questions)for(const o of q.options){assert.ok(o.explanation);assert.equal(gradeReading(p,{...answers,[q.id]:o.id},400,'new').correct,p.questions.length-(o.id===q.correctOptionId?0:1));}
  const prior=gradeReading(old,Object.fromEntries(old.questions.map(q=>[q.id,q.correctOptionId])),300,'prior');
  const state=recordReading(recordReading(emptyState(),old,prior),p,gradeReading(p,answers,400,'new'));
  assert.deepEqual(state.reading!.records[p.id].first,prior);assert.equal(state.reading!.records[p.id].first.total,3);
  assert.equal(state.reading!.records[p.id].latest.total,p.questions.length);
 }
});
test('nested relative modifier targets the intended repeated conditions and inversion remains represented',()=>{
 const s=batch[2].syntax.find(x=>x.sentence.startsWith('Teaching required'))!;
 const relative=s.spans.find(x=>x.text==='that an expert had ceased consciously to register')!;
 const head=s.spans.find(x=>x.kind==='先行詞'&&x.text==='conditions')!;
 assert.equal(head.start,s.sentence.lastIndexOf('conditions')+s.start);
 assert.ok(s.relations.some(x=>x.from===relative.id&&x.to===head.id));
 assert.ok(batch.every(p=>p.syntax.some(x=>/倒置|強調構文/.test(x.explanation))));
 assert.equal(readFileSync('content/readings/drafts.json','utf8'),readFileSync('content/backups/readings-20261113/level1-level2.json','utf8'));
});
