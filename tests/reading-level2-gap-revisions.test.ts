import {test} from 'node:test';
import assert from 'node:assert/strict';
import legacy from '../content/readings/drafts.json';
import batch from '../content/readings/enriched-level2-gap5.json';
import {readingCatalog} from '../src/readingCatalog';
import {readingRevisions} from '../src/readingRevisions';
import {sentenceRanges} from '../src/readingSentences';
import {gradeReading,readingParagraphs,recordReading} from '../src/readings';
import {emptyState,decodeState} from '../src/model';

test('Level 2 items 11–15 preserve source text and questions, hide answers and align every review sentence',()=>{
 const originals=legacy.filter(p=>p.level===2).slice(10,15);
 assert.deepEqual(batch.map(p=>p.id),originals.map(p=>p.id));
 assert.equal(new Set(readingRevisions.map(p=>p.id)).size,readingRevisions.length);
 assert.deepEqual(batch.map(p=>p.questions.length),[5,6,5,6,7]);
 assert.equal(batch.reduce((n,p)=>n+p.sentences.length,0),97);
 for(const [i,p] of batch.entries()){
  const old=originals[i];
  assert.deepEqual(readingCatalog.find(x=>x.id===p.id),p);
  assert.deepEqual(p.questions.slice(0,old.questions.length),old.questions);
  assert.deepEqual(p.previousSyntax,old.syntax);
  assert.deepEqual(p.paragraphs.slice(0,old.paragraphs.length).map(x=>[x.id,x.english]),old.paragraphs.map(x=>[x.id,x.english]));
  assert.equal(p.content.contentVersion,2);assert.equal(p.content.humanReviewed,false);
  const count=(paras:typeof p.paragraphs)=>paras.map(x=>x.english).join(' ').match(/[A-Za-z]+(?:['-][A-Za-z]+)*/g)!.length;
  assert.equal(count(p.paragraphs),p.wordCount);assert.equal(count(p.reviewParagraphs),p.reviewWordCount);
  assert.ok(p.reviewWordCount>=250&&p.reviewWordCount<=400);
  const answer=old.questions[0].options.find(o=>o.id===old.questions[0].correctOptionId)!.text;
  assert.equal(p.gapSolutions['[1]'].answer,answer);
  assert.ok(readingParagraphs(p,false).some(x=>x.english.includes('[1]')));
  assert.ok(readingParagraphs(p,true).every(x=>!x.english.includes('[1]')));
  for(const [j,para] of readingParagraphs(p,true).entries()){
   const source=readingParagraphs(p,false)[j],rows=p.sentences.filter(s=>s.paragraphId===para.id);
   assert.equal(para.english,source.english.replace('[1]',answer));
   assert.deepEqual(rows.map(s=>({id:s.id,english:s.english,start:s.start,end:s.end})),sentenceRanges(para.id,para.english));
   assert.deepEqual(rows.map(s=>({id:s.id,english:s.sourceEnglish,start:s.sourceStart,end:s.sourceEnd})),sentenceRanges(source.id,source.english));
   assert.equal(rows.map(s=>s.translation).join(''),para.translation);assert.equal(source.translation,para.translation);
   for(const s of rows){
    assert.equal(source.english.slice(s.sourceStart,s.sourceEnd),s.sourceEnglish);
    assert.equal(para.english.slice(s.start,s.end),s.english);
    const syn=p.syntax.find(x=>x.id===s.syntaxId)!;
    assert.ok(syn);assert.equal(syn.sentence,s.english);assert.equal(syn.translation,s.translation);
    assert.equal(syn.start,s.start);assert.equal(syn.end,s.end);
    assert.ok(syn.explanation&&syn.skeleton&&syn.readingOrder&&syn.grammarPoints.length);
    const ids=new Set(syn.spans.map(x=>x.id));
    for(const span of syn.spans){assert.equal(para.english.slice(span.start,span.end),span.text);assert.ok(span.start>=s.start&&span.end<=s.end);}
    for(const edge of syn.relations){assert.ok(ids.has(edge.from));assert.ok(ids.has(edge.to));}
   }
  }
  for(const q of p.questions){assert.equal(q.options.length,4);assert.equal(q.options.filter(o=>o.id===q.correctOptionId).length,1);
   assert.ok(p.paragraphs.find(x=>x.id===q.evidence.paragraphId)?.english.includes(q.evidence.quote));
  }
 }
});

test('new Level 2 gap scores keep earlier three-question attempts unchanged across persistence',()=>{
 for(const p of batch){
  const old=legacy.find(x=>x.id===p.id)!,right=Object.fromEntries(p.questions.map(q=>[q.id,q.correctOptionId]));
  for(const q of p.questions)for(const o of q.options){assert.ok(o.explanation);assert.equal(gradeReading(p,{...right,[q.id]:o.id},300,'changed').correct,p.questions.length-(o.id===q.correctOptionId?0:1));}
  const oldAttempt=gradeReading(old,Object.fromEntries(old.questions.map(q=>[q.id,q.correctOptionId])),240,'v1');
  const oldState=recordReading(emptyState(),old,oldAttempt);
  const state=recordReading(oldState,p,gradeReading(p,right,300,'v2'));
  assert.deepEqual(state.reading!.records[p.id].first,oldAttempt);
  assert.equal(state.reading!.records[p.id].first.total,3);
  assert.ok(state.reading!.records[p.id].archivedAttempts!.some(x=>x.id==='v1'));
  assert.deepEqual(decodeState(JSON.stringify(state)),state);
 }
});
