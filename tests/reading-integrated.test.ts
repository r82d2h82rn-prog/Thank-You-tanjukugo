import { test } from 'node:test';
import assert from 'node:assert/strict';
import enriched from '../content/readings/enriched.json';
import legacy from '../content/readings/drafts.json';
import { sentenceRanges } from '../src/readingSentences';
import { gradeReading, recordReading } from '../src/readings';
import { emptyState, decodeState } from '../src/model';
test('sentence splitting keeps abbreviations, decimal numbers and quoted endings',()=>{
 const text='Dr. Lee measured 3.5 cm. "Is it ready?" Yes, it is.';
 assert.deepEqual(sentenceRanges('p1',text).map(x=>x.english),['Dr. Lee measured 3.5 cm.','"Is it ready?"','Yes, it is.']);
 for(const s of sentenceRanges('p1',text))assert.equal(text.slice(s.start,s.end),s.english);
});
test('five preserved texts have aligned translations and syntax for every sentence',()=>{
 for(const p of enriched){
  const old=legacy.find(x=>x.id===p.id)!;assert.equal(p.content.contentVersion,old.content.contentVersion+1);
  assert.deepEqual(p.questions.slice(0,old.questions.length),old.questions);
  assert.deepEqual(p.paragraphs.map(x=>x.english),old.paragraphs.map(x=>x.english));
  for(const para of p.paragraphs){const ranges=sentenceRanges(para.id,para.english);assert.equal(ranges.length,p.sentences.filter(s=>s.paragraphId===para.id).length);
   for(const r of ranges){const s=p.syntax.find(s=>s.paragraphId===para.id&&s.start===r.start&&s.end===r.end)!;assert.ok(s);assert.equal(s.sentence,r.english);assert.ok(s.translation);assert.ok(s.explanation);assert.ok(s.spans.some(x=>x.role==='S'));assert.ok(s.spans.some(x=>x.role==='V'));for(const span of s.spans)assert.equal(para.english.slice(span.start,span.end),span.text);}
  }
 }
});
test('adding questions never recalculates the score saved for an earlier version',()=>{
 const old=legacy[0],current=enriched[0];const answers=Object.fromEntries(old.questions.map(q=>[q.id,q.correctOptionId]));
 const attempt=gradeReading(old,answers,300,'old');const before=recordReading(emptyState(),old,attempt);const snapshot=structuredClone(before.reading!.records[old.id]);
 const next=recordReading(before,current,gradeReading(current,Object.fromEntries(current.questions.map(q=>[q.id,q.correctOptionId])),500,'new'));
 assert.deepEqual(next.reading!.records[old.id].first,snapshot.first);assert.equal(next.reading!.records[old.id].first.total,3);assert.equal(next.reading!.records[old.id].latest.total,5);assert.equal(next.reading!.records[old.id].latest.contentVersion,2);assert.deepEqual(decodeState(JSON.stringify(next)),next);
});
