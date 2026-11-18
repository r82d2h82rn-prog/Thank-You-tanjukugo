import {test} from 'node:test';
import assert from 'node:assert/strict';
import legacy from '../content/readings/drafts.json';
import firstBatch from '../content/readings/enriched-level2-sentence-gap5.json';
import nextBatch from '../content/readings/enriched-level2-sentence-gap-next5.json';
import {readingCatalog} from '../src/readingCatalog';
import {readingRevisions} from '../src/readingRevisions';
import {sentenceRanges} from '../src/readingSentences';
import {gradeReading,readingParagraphs,recordReading} from '../src/readings';
import {emptyState,decodeState} from '../src/model';

for(const {batch,start,end,sentences} of [
 {batch:firstBatch,start:20,end:25,sentences:94},
 {batch:nextBatch,start:25,end:30,sentences:93},
]) {
test(`Level 2 items ${start+1}–${end} map inserted sentences and following source text separately without leaking answers`,()=>{
 const originals=legacy.filter(p=>p.level===2).slice(start,end);
 assert.deepEqual(batch.map(p=>p.id),originals.map(p=>p.id));
 assert.equal(new Set(readingRevisions.map(p=>p.id)).size,readingRevisions.length);
 assert.deepEqual(batch.map(p=>p.questions.length),[5,6,5,7,6]);
 assert.equal(batch.reduce((n,p)=>n+p.sentences.length,0),sentences);
 for(const [i,p] of batch.entries()){
  const old=originals[i];
  assert.deepEqual(readingCatalog.find(x=>x.id===p.id),p);
  assert.deepEqual(p.questions.slice(0,old.questions.length),old.questions);
  assert.deepEqual(p.previousSyntax,old.syntax);
  assert.deepEqual(p.paragraphs.slice(0,old.paragraphs.length).map(x=>[x.id,x.english]),old.paragraphs.map(x=>[x.id,x.english]));
  assert.equal(p.content.contentVersion,2);assert.equal(p.content.humanReviewed,false);
  const count=(paras:typeof p.paragraphs)=>paras.map(x=>x.english).join(' ').match(/[A-Za-z]+(?:['-][A-Za-z]+)*/g)!.length;
  assert.equal(count(p.paragraphs),p.wordCount);assert.equal(count(p.reviewParagraphs),p.reviewWordCount);
  assert.ok(p.wordCount>=250&&p.reviewWordCount<=400);
  const answer=old.questions[0].options.find(o=>o.id===old.questions[0].correctOptionId)!.text;
  assert.equal(p.gapSolutions['[1]'].answer,answer);assert.ok(answer.endsWith('.'));
  assert.equal(p.sentences.filter(s=>s.sourceKind==='gap').length,1);
  for(const [j,para] of readingParagraphs(p,true).entries()){
   const source=readingParagraphs(p,false)[j],rows=p.sentences.filter(s=>s.paragraphId===para.id),rawRanges=sentenceRanges(source.id,source.english);
   assert.equal(para.english,source.english.replace('[1]',answer));
   assert.deepEqual(rows.map(s=>({id:s.id,english:s.english,start:s.start,end:s.end})),sentenceRanges(para.id,para.english));
   assert.equal(rows.length,rawRanges.length+(source.english.includes('[1]')?1:0));
   const normalize=(s:string)=>s.replace(/\s+/g,' ').trim();
   assert.equal(normalize(rows.map(s=>s.sourceEnglish).join(' ')),normalize(source.english));
   assert.equal(rows.map(s=>s.translation).join(''),para.translation);assert.equal(source.translation,para.translation);
   for(const [k,s] of rows.entries()){
    assert.equal(source.english.slice(s.sourceStart,s.sourceEnd),s.sourceEnglish);
    const raw=rawRanges.find(r=>r.start<=s.sourceStart&&r.end>=s.sourceEnd)!;
    assert.ok(raw);assert.equal(s.sourceSentenceId,raw.id);
    if(s.sourceKind==='gap'){
     assert.equal(s.sourceEnglish,'[1]');assert.equal(s.english,answer);
     const following=rows[k+1];assert.ok(following);
     assert.equal(following.sourceKind,'text');assert.equal(following.sourceSentenceId,s.sourceSentenceId);
     assert.ok(following.sourceStart>s.sourceEnd);assert.equal(following.english,following.sourceEnglish);
    }else assert.equal(s.english,s.sourceEnglish);
    const syn=p.syntax.find(x=>x.id===s.syntaxId)!;
    assert.ok(syn);assert.equal(syn.sentence,s.english);assert.equal(syn.translation,s.translation);
    assert.equal(syn.start,s.start);assert.equal(syn.end,s.end);
    assert.ok(syn.spans.some(x=>x.role==='S'));assert.ok(syn.spans.some(x=>x.role==='V'));
    const ids=new Set(syn.spans.map(x=>x.id));
    for(const span of syn.spans){assert.equal(para.english.slice(span.start,span.end),span.text);assert.ok(span.start>=s.start&&span.end<=s.end);}
    for(const edge of syn.relations){assert.ok(ids.has(edge.from));assert.ok(ids.has(edge.to));}
   }
  }
  assert.ok(readingParagraphs(p,false).some(x=>x.english.includes('[1]')));
  assert.ok(readingParagraphs(p,true).every(x=>!x.english.includes('[1]')));
  for(const q of p.questions){assert.equal(q.options.length,4);assert.equal(q.options.filter(o=>o.id===q.correctOptionId).length,1);
   assert.ok(p.paragraphs.find(x=>x.id===q.evidence.paragraphId)?.english.includes(q.evidence.quote));
  }
 }
});

test(`Level 2 items ${start+1}–${end} keep each answer independently graded and preserve old three-question scores`,()=>{
 for(const p of batch){
  const old=legacy.find(x=>x.id===p.id)!,right=Object.fromEntries(p.questions.map(q=>[q.id,q.correctOptionId]));
  for(const q of p.questions)for(const o of q.options){assert.ok(o.explanation);assert.equal(gradeReading(p,{...right,[q.id]:o.id},300,'changed').correct,p.questions.length-(o.id===q.correctOptionId?0:1));}
  const prior=gradeReading(old,Object.fromEntries(old.questions.map(q=>[q.id,q.correctOptionId])),240,'v1');
  const state=recordReading(recordReading(emptyState(),old,prior),p,gradeReading(p,right,300,'v2'));
  assert.deepEqual(state.reading!.records[p.id].first,prior);assert.equal(state.reading!.records[p.id].first.total,3);
  assert.ok(state.reading!.records[p.id].archivedAttempts!.some(x=>x.id==='v1'));
  assert.deepEqual(decodeState(JSON.stringify(state)),state);
 }
});
}
