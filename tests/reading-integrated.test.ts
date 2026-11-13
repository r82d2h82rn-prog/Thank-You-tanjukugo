import { test } from 'node:test';
import assert from 'node:assert/strict';
import lowerEnriched from '../content/readings/enriched.json';
import upperEnriched from '../content/readings/enriched-level3.json';
import advanced from '../content/readings/advanced.json';
const enriched=[...lowerEnriched,...upperEnriched];
import legacy from '../content/readings/drafts.json';
import { sentenceRanges } from '../src/readingSentences';
import { gradeReading, recordReading, readingParagraphs } from '../src/readings';
import { emptyState, decodeState } from '../src/model';
test('sentence splitting keeps abbreviations, decimal numbers and quoted endings',()=>{
 const text='Dr. Lee measured 3.5 cm. "Is it ready?" Yes, it is.';
 assert.deepEqual(sentenceRanges('p1',text).map(x=>x.english),['Dr. Lee measured 3.5 cm.','"Is it ready?"','Yes, it is.']);
 for(const s of sentenceRanges('p1',text))assert.equal(text.slice(s.start,s.end),s.english);
});
test('preserved revision texts have aligned translations and syntax for every sentence',()=>{
 for(const p of enriched){
  const old=[...legacy,...advanced].find(x=>x.id===p.id)!;assert.equal(p.content.contentVersion,old.content.contentVersion+1);
  assert.deepEqual(p.questions.slice(0,old.questions.length),old.questions);
  assert.deepEqual(p.paragraphs.slice(0,old.paragraphs.length).map(x=>({id:x.id,english:x.english})),old.paragraphs.map(x=>({id:x.id,english:x.english})));
  assert.equal(new Set(p.paragraphs.map(x=>x.id)).size,p.paragraphs.length);
  for(const para of readingParagraphs(p,true)){const ranges=sentenceRanges(para.id,para.english);assert.equal(ranges.length,p.sentences.filter(s=>s.paragraphId===para.id).length);
   for(const r of ranges){const s=p.syntax.find(s=>s.paragraphId===para.id&&s.start===r.start&&s.end===r.end)!;assert.ok(s);assert.equal(s.sentence,r.english);assert.ok(s.translation);assert.ok(s.explanation);assert.ok(s.spans.some(x=>x.role==='S'));assert.ok(s.spans.some(x=>x.role==='V'));for(const span of s.spans)assert.equal(para.english.slice(span.start,span.end),span.text);}
  }
 }
});
test('the first five Level 2 revisions meet length and variation standards without changing old questions',()=>{
 const batch=enriched.filter(p=>p.level===2);assert.equal(batch.length,5);
 assert.deepEqual(batch.map(p=>p.paragraphs.length),[4,5,4,5,4]);
 assert.deepEqual(batch.map(p=>p.questions.length),[5,6,5,7,6]);
 assert.equal(batch.reduce((n,p)=>n+p.sentences.length,0),88);
 for(const p of batch){
  const old=legacy.find(x=>x.id===p.id)!;
  assert.deepEqual(p.previousSyntax,old.syntax);
  const words=p.paragraphs.map(x=>x.english).join(' ').match(/[A-Za-z]+(?:['-][A-Za-z]+)*/g)!.length;
  assert.equal(p.wordCount,words);assert.ok(words>=250&&words<=400);
  for(const para of p.paragraphs){
   const sentences=p.sentences.filter(x=>x.paragraphId===para.id);
   assert.equal(para.translation,sentences.map(s=>s.translation).join(''));
   assert.deepEqual(sentences.map(s=>({id:s.id,english:s.english,start:s.start,end:s.end})),sentenceRanges(para.id,para.english));
   for(const s of sentences)assert.equal(p.syntax.find(x=>x.id===s.syntaxId)!.translation,s.translation);
  }
  const right=Object.fromEntries(p.questions.map(q=>[q.id,q.correctOptionId]));
  assert.equal(gradeReading(p,right,100,'new').correct,p.questions.length);
  for(const q of p.questions)for(const option of q.options){
   assert.ok(option.explanation);assert.equal(gradeReading(p,{...right,[q.id]:option.id},100,'one-change').correct,p.questions.length-(option.id===q.correctOptionId?0:1));
  }
  const oldAttempt=gradeReading(old,Object.fromEntries(old.questions.map(q=>[q.id,q.correctOptionId])),100,'v1');
  const state=recordReading(recordReading(emptyState(),old,oldAttempt),p,gradeReading(p,right,200,'v2'));
  assert.deepEqual(state.reading!.records[p.id].first,oldAttempt);assert.equal(oldAttempt.total,3);
  assert.equal(state.reading!.records[p.id].latest.total,p.questions.length);
 }
 const first=batch[0].syntax.find(x=>x.sentence.startsWith('Even'))!;
 const even=first.spans.find(x=>x.text==='Even')!,subject=first.spans.find(x=>x.text==='a skilled volunteer')!;
 assert.ok(first.relations.some(x=>x.from===even.id&&x.to===subject.id));
});
test('adding questions never recalculates the score saved for an earlier version',()=>{
 const old=legacy[0],current=enriched[0];const answers=Object.fromEntries(old.questions.map(q=>[q.id,q.correctOptionId]));
 const attempt=gradeReading(old,answers,300,'old');const before=recordReading(emptyState(),old,attempt);const snapshot=structuredClone(before.reading!.records[old.id]);
 const next=recordReading(before,current,gradeReading(current,Object.fromEntries(current.questions.map(q=>[q.id,q.correctOptionId])),500,'new'));
 assert.deepEqual(next.reading!.records[old.id].first,snapshot.first);assert.equal(next.reading!.records[old.id].first.total,3);assert.equal(next.reading!.records[old.id].latest.total,5);assert.equal(next.reading!.records[old.id].latest.contentVersion,2);assert.deepEqual(decodeState(JSON.stringify(next)),next);
});
test('authored nested modifier links point to their actual antecedents',()=>{
 const sample=enriched.find(p=>p.id==='reading-l1-f01-07')!;
 const syntax=sample.syntax.find(x=>x.sentence.includes('places where'))!;
 const relative=syntax.spans.find(x=>x.text==='where people needed light for safety')!;
 const head=syntax.spans.find(x=>x.text==='places')!;
 assert.ok(syntax.relations.some(x=>x.from===relative.id&&x.to===head.id&&x.type==='modifies'));
 for(const p of enriched)for(const syntax of p.syntax){const ids=new Set(syntax.spans.map(n=>n.id));for(const link of syntax.relations){assert.ok(ids.has(link.from));assert.ok(ids.has(link.to));assert.notEqual(link.from,link.to);}}
});
test('gap answers and their coordinates are used only in submitted review',()=>{
 const gaps=enriched.filter(p=>'reviewParagraphs' in p);
 assert.equal(gaps.length,5);
 for(const p of gaps){
  const original=legacy.find(x=>x.id===p.id)!;
  assert.deepEqual(readingParagraphs(p,false).map(x=>x.english),original.paragraphs.map(x=>x.english));
  assert.ok(readingParagraphs(p,false).some(x=>x.english.includes('[1]')));
  assert.ok(readingParagraphs(p,true).every(x=>!x.english.includes('[1]')));
  const gap=p.questions[0];const answer=gap.options.find(x=>x.id===gap.correctOptionId)!.text;
  for(const [i,para] of readingParagraphs(p,true).entries())assert.equal(para.english,original.paragraphs[i].english.replace('[1]',answer));
  for(const sentence of p.sentences){if(!('sourceEnglish' in sentence))throw new Error('source alignment missing');const para=original.paragraphs.find(x=>x.id===sentence.paragraphId)!;assert.equal(para.english.slice(sentence.sourceStart,sentence.sourceEnd),sentence.sourceEnglish);assert.equal(sentence.sourceEnglish.replace('[1]',answer),sentence.english);}
 }
});
test('revised attempts retain the previously stored first, best and latest snapshots',()=>{
 const old=legacy[0],p=enriched[0],right=Object.fromEntries(old.questions.map(q=>[q.id,q.correctOptionId]));
 const wrong=(id:string)=>old.questions.find(q=>q.id===id)!.options.find(o=>o.id!==right[id])!.id;
 const first=gradeReading(old,{...right,q1:wrong('q1')},500,'first-old');
 const best=gradeReading(old,right,400,'best-old');const latest=gradeReading(old,{...right,q1:wrong('q1'),q2:wrong('q2')},300,'latest-old');
 const state={...emptyState(),reading:{unlockedByLevel:{},records:{[p.id]:{attempts:3,first,best,latest}}}};
 const next=recordReading(state,p,gradeReading(p,Object.fromEntries(p.questions.map(q=>[q.id,q.correctOptionId])),100,'new-version'));
 assert.equal(next.reading!.records[p.id].best.id,'new-version');
 for(const a of [first,best,latest])assert.deepEqual(next.reading!.records[p.id].archivedAttempts!.find(x=>x.id===a.id),a);
 assert.deepEqual(state.reading.records[p.id],{attempts:3,first,best,latest});
 assert.deepEqual(decodeState(JSON.stringify(next)),next);
 assert.equal(recordReading(next,old,first),next);
});
test('malformed archived attempts are rejected instead of silently restored',()=>{
 const p=enriched[0];const state=recordReading(emptyState(),p,gradeReading(p,Object.fromEntries(p.questions.map(q=>[q.id,q.correctOptionId])),10,'valid'));
 for(const archive of [{},[{}]]){const corrupted=JSON.parse(JSON.stringify(state));corrupted.reading.records[p.id].archivedAttempts=archive;assert.throws(()=>decodeState(JSON.stringify(corrupted)));}
});
