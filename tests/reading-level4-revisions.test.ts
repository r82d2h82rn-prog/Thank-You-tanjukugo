import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import batch from '../content/readings/enriched-level4.json';
import original from '../content/readings/advanced.json';
import {readingCatalog} from '../src/readingCatalog';
import {gradeReading,recordReading} from '../src/readings';
import {emptyState} from '../src/model';
import {sentenceRanges} from '../src/readingSentences';
test('Level 4 first five overlays cover every sentence and retain original IDs, text, answers and scores',()=>{
 assert.equal(batch.length,5);assert.deepEqual(batch.map(p=>p.questions.length),[7,8,6,9,7]);
 assert.deepEqual(batch.map(p=>p.paragraphs.length),[6,7,8,6,9]);
 assert.equal(batch.reduce((n,p)=>n+p.sentences.length,0),146);
 for(const p of batch){
  const old=original.find(x=>x.id===p.id)!;
  assert.equal(p.content.contentVersion,old.content.contentVersion+1);
  assert.equal(p.content.humanReviewed,false);assert.equal(p.content.productionApproved,false);
  assert.deepEqual(p.previousSyntax,old.syntax);assert.deepEqual(p.questions.slice(0,3),old.questions);
  assert.deepEqual(p.paragraphs.slice(0,3).map(x=>[x.id,x.english]),old.paragraphs.map(x=>[x.id,x.english]));
  assert.deepEqual(readingCatalog.find(x=>x.id===p.id),p);
  const words=p.paragraphs.map(x=>x.english).join(' ').match(/[A-Za-z]+(?:['-][A-Za-z]+)*/g)!.length;
  assert.equal(words,p.wordCount);assert.ok(words>=600&&words<=900);
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
test('imperative sentences keep the omitted subject implicit rather than colouring an object as S',()=>{
 for(const p of batch)for(const s of p.syntax){
  const para=p.paragraphs.find(x=>x.id===s.paragraphId)!;
  assert.equal(para.english.slice(s.start,s.end),s.sentence);
  for(const span of s.spans)assert.equal(para.english.slice(span.start,span.end),span.text);
  const ids=new Set(s.spans.map(x=>x.id));for(const r of s.relations){assert.ok(ids.has(r.from));assert.ok(ids.has(r.to));}
  assert.ok(s.spans.some(x=>x.role==='V'));
  if(s.implicitSubject==='you'){assert.ok(s.skeleton.includes('省略'));assert.ok(s.spans.filter(x=>x.role==='S').every(x=>!s.spans.some(o=>o.role==='O'&&o.start===x.start&&o.end===x.end))); }
  else assert.ok(s.spans.some(x=>x.role==='S'));
 }
 assert.ok(batch[0].syntax.some(s=>s.implicitSubject==='you'));
});
