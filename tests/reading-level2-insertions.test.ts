import {test} from 'node:test';
import assert from 'node:assert/strict';
import legacy from '../content/readings/drafts.json';
import firstBatch from '../content/readings/enriched-level2-insert5.json';
import nextBatch from '../content/readings/enriched-level2-insert-next5.json';
import {readingCatalog} from '../src/readingCatalog';
import {readingRevisions} from '../src/readingRevisions';
import {sentenceRanges} from '../src/readingSentences';
import {gradeReading,readingParagraphs,recordReading} from '../src/readings';
import {emptyState,decodeState} from '../src/model';

const words=(text:string)=>(text.replace(/\[[A-D]\]/g,'').match(/[A-Za-z]+(?:['-][A-Za-z]+)*/g)??[]).length;

for(const {batch,start,end,sentences,questionCounts} of [
 {batch:firstBatch,start:60,end:65,sentences:106,questionCounts:[5,6,7,5,6]},
 {batch:nextBatch,start:65,end:70,sentences:109,questionCounts:[6,5,6,7,5]},
]) {
test(`Level 2 items ${start+1}–${end} keep original insertion questions and reveal the completed reading only after submission`,()=>{
 const originals=legacy.filter(p=>p.level===2).slice(start,end);
 assert.deepEqual(batch.map(p=>p.id),originals.map(p=>p.id));
 assert.deepEqual(batch.map(p=>p.questions.length),questionCounts);
 assert.equal(batch.reduce((n,p)=>n+p.sentences.length,0),sentences);
 assert.equal(new Set(readingRevisions.map(p=>p.id)).size,readingRevisions.length);
 for(const [i,p] of batch.entries()){
  const old=originals[i],marker=old.questions[0].options.find(o=>o.id===old.questions[0].correctOptionId)!.text;
  assert.equal(p.format,7);assert.equal(p.content.contentVersion,2);assert.equal(p.content.humanReviewed,false);
  assert.deepEqual(readingCatalog.find(x=>x.id===p.id),p);
  assert.deepEqual(p.questions.slice(0,3),old.questions);assert.deepEqual(p.insert,old.insert);
  assert.deepEqual(p.previousSyntax,old.syntax);
  assert.deepEqual(p.paragraphs.slice(0,old.paragraphs.length).map(x=>[x.id,x.english]),old.paragraphs.map(x=>[x.id,x.english]));
  assert.deepEqual(p.insertionSolution,{questionId:'q1',marker,sentence:p.insert.sentence,paragraphId:p.paragraphs.find(x=>x.english.includes(marker))!.id});
  assert.ok(!('gapSolutions' in p));assert.equal(p.syntaxOffsetBasis,'reviewParagraphs');
  assert.equal(readingParagraphs(p,false),p.paragraphs);assert.equal(readingParagraphs(p,true),p.reviewParagraphs);
  assert.deepEqual(p.paragraphs.flatMap(x=>x.english.match(/\[[A-D]\]/g)??[]),['[A]','[B]','[C]','[D]']);
  assert.ok(!p.paragraphs.some(x=>x.english.includes(p.insert.sentence)));
  const body=p.paragraphs.map(x=>x.english).join(' '),review=p.reviewParagraphs.map(x=>x.english).join(' ');
  assert.equal(p.wordCount,words(body));assert.equal(p.reviewWordCount,words(review));
  assert.ok(p.wordCount>=300&&p.wordCount<=350);assert.ok(p.reviewWordCount>=300&&p.reviewWordCount<=350);
  assert.equal(p.reviewWordCount,p.wordCount+words(p.insert.sentence));
  assert.ok(!/\[[A-D]\]/.test(review));assert.equal(review.split(p.insert.sentence).length-1,1);
  for(const [j,para] of p.reviewParagraphs.entries()){
   const source=p.paragraphs[j];
   assert.equal(para.id,source.id);
   assert.equal(para.english,source.english.replace(/\[[A-D]\]/g,m=>m===marker?p.insert.sentence:''));
   const rows=p.sentences.filter(s=>s.paragraphId===para.id);
   assert.deepEqual(rows.map(s=>({id:s.id,english:s.english,start:s.start,end:s.end})),sentenceRanges(para.id,para.english));
   assert.equal(para.translation,rows.map(s=>s.translation).join(''));assert.equal(source.translation,para.translation);
   for(const s of rows){
    const syn=p.syntax.find(x=>x.id===s.syntaxId)!;
    assert.ok(s.translation);assert.ok(syn.explanation);assert.ok(syn.grammarPoints.length);
    assert.equal(syn.offsetBasis,'reviewParagraphs');assert.equal(syn.sentence,s.english);
    assert.equal(syn.translation,s.translation);assert.equal(syn.start,s.start);assert.equal(syn.end,s.end);
    assert.ok(syn.spans.some(x=>x.role==='S'));assert.ok(syn.spans.some(x=>x.role==='V'));
    for(const span of syn.spans){assert.equal(para.english.slice(span.start,span.end),span.text);assert.ok(span.start>=s.start&&span.end<=s.end);}
    const ids=new Set(syn.spans.map(x=>x.id));for(const edge of syn.relations){assert.ok(ids.has(edge.from));assert.ok(ids.has(edge.to));}
   }
  }
 }
});

test(`insertion ${start+1}–${end} source coordinates cover every original text character once and map the inserted sentence to its answer marker`,()=>{
 for(const p of batch){
  const inserted=p.sentences.filter(s=>s.sourceKind==='insertion');assert.equal(inserted.length,1);
  assert.equal(inserted[0].english,p.insert.sentence);assert.equal(inserted[0].translation,p.insert.translation);
  assert.equal(inserted[0].sourceEnglish,p.insertionSolution.marker);
  assert.equal(inserted[0].paragraphId,p.insertionSolution.paragraphId);
  for(const para of p.paragraphs){
   const sourceRanges=sentenceRanges(para.id,para.english),covered=new Uint16Array(para.english.length);
   for(const s of p.sentences.filter(x=>x.paragraphId===para.id)){
    assert.equal(para.english.slice(s.sourceStart,s.sourceEnd),s.sourceEnglish);
    const origin=sourceRanges.find(r=>r.id===s.sourceSentenceId)!;assert.ok(origin);
    assert.ok(origin.start<=s.sourceStart&&origin.end>=s.sourceEnd);
    if(s.sourceKind==='text')assert.equal(s.sourceEnglish,s.english);
    else assert.equal(s.sourceKind,'insertion');
    for(let i=s.sourceStart;i<s.sourceEnd;i++)covered[i]++;
   }
   const labels=[...para.english.matchAll(/\[[A-D]\]/g)];
   for(let i=0;i<para.english.length;i++){
    const label=labels.find(m=>i>=m.index!&&i<m.index!+m[0].length);
    if(label)assert.equal(covered[i],label[0]===p.insertionSolution.marker?1:0);
    else if(!/\s/.test(para.english[i]))assert.equal(covered[i],1,`${p.id} ${para.id} missing or duplicated source character ${i}`);
    else assert.ok(covered[i]<=1);
   }
  }
 }
});

test(`insertion ${start+1}–${end} revision choices grade independently while older three-question attempts retain their saved scores`,()=>{
 for(const p of batch){
  const old=legacy.find(x=>x.id===p.id)!,right=Object.fromEntries(p.questions.map(q=>[q.id,q.correctOptionId]));
  for(const q of p.questions){
   assert.equal(q.options.length,4);assert.ok(p.paragraphs.find(x=>x.id===q.evidence.paragraphId)?.english.includes(q.evidence.quote));
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
