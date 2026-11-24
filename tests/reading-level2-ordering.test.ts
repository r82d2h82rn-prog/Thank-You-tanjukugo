import {test} from 'node:test';
import assert from 'node:assert/strict';
import legacy from '../content/readings/drafts.json';
import firstBatch from '../content/readings/enriched-level2-order5.json';
import nextBatch from '../content/readings/enriched-level2-order-next5.json';
import {readingCatalog} from '../src/readingCatalog';
import {readingRevisions} from '../src/readingRevisions';
import {sentenceRanges} from '../src/readingSentences';
import {gradeReading,readingParagraphs,readingParagraphLabel,recordReading} from '../src/readings';
import {emptyState,decodeState} from '../src/model';

for(const {batch,start,questions,paragraphs,sentences,min,max} of [
 {batch:firstBatch,start:70,questions:[5,6,7,5,6],paragraphs:[6,5,6,5,6],sentences:98,min:300,max:350},
 {batch:nextBatch,start:75,questions:[6,6,7,5,6],paragraphs:[6,6,6,6,6],sentences:113,min:350,max:400}
]){
test(`Level 2 items ${start+1}–${start+5} retain four-paragraph ordering questions and show every continuation after the solved order`,()=>{
 const originals=legacy.filter(p=>p.level===2).slice(start,start+5);
 assert.deepEqual(batch.map(p=>p.id),originals.map(p=>p.id));
 assert.deepEqual(batch.map(p=>p.questions.length),questions);
 assert.deepEqual(batch.map(p=>p.paragraphs.length),paragraphs);
 assert.equal(batch.reduce((n,p)=>n+p.sentences.length,0),sentences);
 assert.equal(new Set(readingRevisions.map(p=>p.id)).size,readingRevisions.length);
 for(const [i,p] of batch.entries()){
  const old=originals[i];
  assert.equal(p.format,8);assert.equal(p.content.contentVersion,2);assert.equal(p.content.humanReviewed,false);
  assert.deepEqual(readingCatalog.find(x=>x.id===p.id),p);
  assert.deepEqual(p.questions.slice(0,3),old.questions);assert.deepEqual(p.paragraphOrder,old.paragraphOrder);
  assert.deepEqual(p.previousSyntax,old.syntax);
  assert.deepEqual(p.paragraphs.slice(0,4).map(x=>[x.id,x.english]),old.paragraphs.map(x=>[x.id,x.english]));
  assert.deepEqual(p.continuationParagraphIds,p.paragraphs.slice(4).map(x=>x.id));
  assert.equal(readingParagraphs(p,false),p.paragraphs);
  const reviewed=readingParagraphs(p,true),expected=[...p.paragraphOrder,...p.continuationParagraphIds];
  assert.deepEqual(reviewed.map(x=>x.id),expected);assert.equal(reviewed.length,p.paragraphs.length);
  assert.equal(new Set(expected).size,p.paragraphs.length);
  assert.deepEqual(expected.slice(0,4),old.paragraphOrder);
  assert.equal(p.questions[0].options.find(x=>x.id===p.questions[0].correctOptionId)!.text,p.paragraphOrder.map(x=>x.slice(1)).join('→'));
  for(const para of reviewed)assert.equal(para,p.paragraphs.find(x=>x.id===para.id));
  for(const id of p.paragraphOrder)assert.equal(readingParagraphLabel(p,id),`段落 ${id.slice(1)}`);
  for(const [j,id] of p.continuationParagraphIds.entries())assert.equal(readingParagraphLabel(p,id),`続きの本文 ${j+1}`);
  const words=reviewed.map(x=>x.english).join(' ').match(/[A-Za-z]+(?:['-][A-Za-z]+)*/g)!.length;
  assert.equal(p.wordCount,words);assert.equal(p.reviewWordCount,words);assert.ok(words>=min&&words<=max);
  assert.equal(p.syntaxOffsetBasis,'paragraphs');assert.ok(!('reviewParagraphs' in p));
  for(const para of reviewed){
   const rows=p.sentences.filter(s=>s.paragraphId===para.id);
   assert.deepEqual(rows.map(s=>({id:s.id,english:s.english,start:s.start,end:s.end})),sentenceRanges(para.id,para.english));
   assert.equal(para.translation,rows.map(s=>s.translation).join(''));
   for(const s of rows){
    assert.equal(s.sourceEnglish,s.english);assert.equal(s.sourceStart,s.start);assert.equal(s.sourceEnd,s.end);
    const syn=p.syntax.find(x=>x.id===s.syntaxId)!;
    assert.ok(syn);assert.equal(syn.translation,s.translation);assert.equal(syn.sentence,s.english);
    assert.equal(syn.offsetBasis,'paragraphs');assert.equal(syn.start,s.start);assert.equal(syn.end,s.end);
    assert.ok(syn.spans.some(x=>x.role==='S'));assert.ok(syn.spans.some(x=>x.role==='V'));
    for(const span of syn.spans){assert.equal(para.english.slice(span.start,span.end),span.text);assert.ok(span.start>=s.start&&span.end<=s.end);}
    const ids=new Set(syn.spans.map(x=>x.id));for(const edge of syn.relations){assert.ok(ids.has(edge.from));assert.ok(ids.has(edge.to));}
   }
  }
 }
});

test(`ordering review ${start+1} rejects missing or duplicate continuation IDs instead of losing or repeating text`,()=>{
 const p=batch[0];
 assert.throws(()=>readingParagraphs({...p,continuationParagraphIds:[]},true));
 assert.throws(()=>readingParagraphs({...p,continuationParagraphIds:['p5','p5']},true));
 assert.throws(()=>readingParagraphs({...p,continuationParagraphIds:['p5','missing']},true));
 const old=legacy.find(x=>x.id===p.id)!;
 assert.deepEqual(readingParagraphs(old,true).map(x=>x.id),old.paragraphOrder);
 assert.equal(readingParagraphs(old,false),old.paragraphs);
});

test(`ordering revisions ${start+1} grade every option independently and keep original three-question attempts unchanged`,()=>{
 for(const p of batch){
  const old=legacy.find(x=>x.id===p.id)!,right=Object.fromEntries(p.questions.map(q=>[q.id,q.correctOptionId]));
  for(const q of p.questions){assert.equal(q.options.length,4);assert.ok(p.paragraphs.find(x=>x.id===q.evidence.paragraphId)?.english.includes(q.evidence.quote));
   for(const option of q.options){assert.ok(option.explanation);assert.equal(gradeReading(p,{...right,[q.id]:option.id},420,'changed').correct,p.questions.length-(option.id===q.correctOptionId?0:1));}
  }
  const prior=gradeReading(old,Object.fromEntries(old.questions.map(q=>[q.id,q.correctOptionId])),240,'v1');
  const state=recordReading(recordReading(emptyState(),old,prior),p,gradeReading(p,right,420,'v2'));
  assert.deepEqual(state.reading!.records[p.id].first,prior);assert.equal(state.reading!.records[p.id].first.total,3);
  assert.ok(state.reading!.records[p.id].archivedAttempts!.some(x=>x.id==='v1'));
  assert.deepEqual(decodeState(JSON.stringify(state)),state);
 }
});

}
