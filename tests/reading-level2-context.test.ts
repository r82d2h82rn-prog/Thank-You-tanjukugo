import {test} from 'node:test';
import assert from 'node:assert/strict';
import legacy from '../content/readings/drafts.json';
import batch from '../content/readings/enriched-level2-context5.json';
import {readingCatalog} from '../src/readingCatalog';
import {readingRevisions} from '../src/readingRevisions';
import {sentenceRanges} from '../src/readingSentences';
import {gradeReading,readingParagraphs,recordReading} from '../src/readings';
import {emptyState,decodeState} from '../src/model';

const start=90,paragraphs=[5,6,5,5,6],sentences=114;
test(`Level 2 vocabulary-in-context readings ${start+1}–${start+5} preserve source questions and align every sentence in the 350–400 word readings`,()=>{
 const originals=legacy.filter(p=>p.level===2).slice(start,start+5);
 assert.deepEqual(batch.map(p=>p.id),originals.map(p=>p.id));
 assert.deepEqual(batch.map(p=>p.questions.length),[6,5,7,6,5]);
 assert.deepEqual(batch.map(p=>p.paragraphs.length),paragraphs);
 assert.equal(batch.reduce((n,p)=>n+p.sentences.length,0),sentences);
 assert.equal(new Set(readingRevisions.map(p=>p.id)).size,readingRevisions.length);
 for(const [i,p] of batch.entries()){
  const old=originals[i];
  assert.equal(p.format,10);assert.equal(p.content.contentVersion,2);assert.equal(p.content.humanReviewed,false);
  assert.deepEqual(readingCatalog.find(x=>x.id===p.id),p);
  assert.deepEqual(p.previousSyntax,old.syntax);assert.deepEqual(p.questions.slice(0,3),old.questions);
  assert.deepEqual(p.paragraphs.slice(0,3).map(x=>[x.id,x.english]),old.paragraphs.map(x=>[x.id,x.english]));
  assert.ok(!('gapSolutions' in p));assert.ok(!('reviewParagraphs' in p));assert.ok(!('paragraphOrder' in p));
  assert.equal(p.syntaxOffsetBasis,'paragraphs');
  assert.equal(readingParagraphs(p,false),p.paragraphs);assert.equal(readingParagraphs(p,true),p.paragraphs);
  const words=p.paragraphs.map(x=>x.english).join(' ').match(/[A-Za-z]+(?:['-][A-Za-z]+)*/g)!.length;
  assert.equal(words,p.wordCount);assert.equal(words,p.reviewWordCount);assert.ok(words>=350&&words<=400);
  for(const para of p.paragraphs){
   const rows=p.sentences.filter(s=>s.paragraphId===para.id);
   assert.deepEqual(rows.map(s=>({id:s.id,english:s.english,start:s.start,end:s.end})),sentenceRanges(para.id,para.english));
   assert.equal(para.translation,rows.map(s=>s.translation).join(''));
   for(const s of rows){
    assert.equal(s.sourceEnglish,s.english);assert.equal(s.sourceStart,s.start);assert.equal(s.sourceEnd,s.end);
    const syn=p.syntax.find(x=>x.id===s.syntaxId)!;
    assert.ok(syn);assert.equal(syn.sentence,s.english);assert.equal(syn.translation,s.translation);
    assert.equal(syn.offsetBasis,'paragraphs');assert.equal(syn.start,s.start);assert.equal(syn.end,s.end);
    assert.ok(syn.spans.some(x=>x.role==='S'));assert.ok(syn.spans.some(x=>x.role==='V'));
    assert.ok(syn.explanation&&syn.skeleton&&syn.grammarPoints.length);
    for(const span of syn.spans){assert.equal(para.english.slice(span.start,span.end),span.text);assert.ok(span.start>=s.start&&span.end<=s.end);}
    const ids=new Set(syn.spans.map(x=>x.id));for(const edge of syn.relations){assert.ok(ids.has(edge.from));assert.ok(ids.has(edge.to));}
   }
  }
 }
});

test(`context revisions ${start+1} grade all options and preserve earlier three-question results through persistence`,()=>{
 for(const p of batch){
  const old=legacy.find(x=>x.id===p.id)!,right=Object.fromEntries(p.questions.map(q=>[q.id,q.correctOptionId]));
  for(const q of p.questions){
   assert.equal(q.options.length,4);assert.ok(p.paragraphs.find(x=>x.id===q.evidence.paragraphId)?.english.includes(q.evidence.quote));
   for(const o of q.options){assert.ok(o.explanation);assert.equal(gradeReading(p,{...right,[q.id]:o.id},465,'changed').correct,p.questions.length-(o.id===q.correctOptionId?0:1));}
  }
  const prior=gradeReading(old,Object.fromEntries(old.questions.map(q=>[q.id,q.correctOptionId])),240,'v1');
  const state=recordReading(recordReading(emptyState(),old,prior),p,gradeReading(p,right,465,'v2'));
  assert.deepEqual(state.reading!.records[p.id].first,prior);assert.equal(state.reading!.records[p.id].first.total,3);
  assert.ok(state.reading!.records[p.id].archivedAttempts!.some(x=>x.id==='v1'));
  assert.deepEqual(decodeState(JSON.stringify(state)),state);
 }
});
