import {test} from 'node:test';
import assert from 'node:assert/strict';
import batch from '../content/readings/l3_f02.json';
import advanced from '../content/readings/advanced.json';
import original3 from '../content/readings/l3_f01.json';
import original4 from '../content/readings/l4_f06.json';
import policy from '../content/authoring/readings/level3-word-policy.json';
import {readingCatalog} from '../src/readingCatalog';
import {readingRevisions} from '../src/readingRevisions';
import {readingParagraphs,gradeReading,recordReading,unlockReading,readingAccess} from '../src/readings';
import {sentenceRanges} from '../src/readingSentences';
import {emptyState,decodeState} from '../src/model';

test('ten new L3 gap readings append independent identities and obey within-format word bands',()=>{
 assert.deepEqual(advanced.slice(0,20),[...original3,...original4]);
 assert.deepEqual(advanced.slice(20,30),batch);assert.ok(readingCatalog.length>=230);
 assert.deepEqual(batch.map(p=>p.id),Array.from({length:10},(_,i)=>`reading-l3-f02-${String(i+1).padStart(2,'0')}`));
 assert.equal(new Set(readingRevisions.map(p=>p.id)).size,readingRevisions.length);
 for(const [i,p] of batch.entries()){
  assert.deepEqual(advanced.find(x=>x.id===p.id),p);assert.deepEqual(readingCatalog.find(x=>x.id===p.id),p);
  assert.equal(p.format,2);assert.equal(p.content.humanReviewed,false);
  const band=policy.bandsByItemWithinFormat[i],target=policy.targetsByFormat['2'][i];
  const count=p.reviewParagraphs.map(x=>x.english).join(' ').match(/[A-Za-z]+(?:['-][A-Za-z]+)*/g)!.length;
  assert.equal(count,p.reviewWordCount);assert.ok(count>=band.min&&count<=band.max);assert.ok(Math.abs(count-target)<=2);
  assert.ok(p.paragraphs.length>=4&&p.paragraphs.length<=8);assert.ok(p.questions.length>=5&&p.questions.length<=8);
 }
});

test('all 251 sentences retain exact source and completed coordinates around one correctly answered gap',()=>{
 assert.equal(batch.reduce((n,p)=>n+p.sentences.length,0),251);
 for(const p of batch){
  const solution=p.gapSolutions['[1]'];
  assert.equal(p.questions[0].options.find(o=>o.id===p.questions[0].correctOptionId)!.text,solution.answer);
  assert.equal(p.paragraphs.map(x=>x.english).join(' ').match(/\[1\]/g)!.length,1);
  assert.equal(readingParagraphs(p,false),p.paragraphs);assert.equal(readingParagraphs(p,true),p.reviewParagraphs);
  let gapSentences=0;
  for(const para of p.reviewParagraphs){
   const source=p.paragraphs.find(x=>x.id===para.id)!;
   assert.equal(source.english.replace('[1]',solution.answer),para.english);
   const rows=p.sentences.filter(s=>s.paragraphId===para.id);
   assert.deepEqual(rows.map(s=>({id:s.id,english:s.english,start:s.start,end:s.end})),sentenceRanges(para.id,para.english));
   assert.equal(para.translation,rows.map(s=>s.translation).join(''));
   for(const s of rows){
    assert.equal(source.english.slice(s.sourceStart,s.sourceEnd),s.sourceEnglish);
    assert.equal(s.sourceEnglish.replace('[1]',solution.answer),s.english);
    if(s.sourceEnglish.includes('[1]'))gapSentences++;
    const syntax=p.syntax.find(x=>x.id===s.syntaxId)!;
    assert.equal(syntax.sentence,s.english);assert.equal(syntax.translation,s.translation);
    assert.equal(syntax.start,s.start);assert.equal(syntax.end,s.end);
    for(const n of syntax.spans){assert.equal(para.english.slice(n.start,n.end),n.text);assert.ok(n.start>=s.start&&n.end<=s.end);}
    const ids=new Set(syntax.spans.map(n=>n.id));for(const e of syntax.relations){assert.ok(ids.has(e.from));assert.ok(ids.has(e.to));}
   }
  }
  assert.equal(gapSentences,1);
 }
});

test('all 62 questions grade every option correctly while earlier L3 records and free unlocks survive',()=>{
 assert.equal(batch.reduce((n,p)=>n+p.questions.length,0),62);
 const old=original3[0],prior=gradeReading(old,Object.fromEntries(old.questions.map(q=>[q.id,q.correctOptionId])),240,'old');
 let baseline=recordReading(emptyState(),old,prior);
 for(const p of original3.slice(0,3))baseline=unlockReading(baseline,p);
 for(const p of batch){
  const right=Object.fromEntries(p.questions.map(q=>[q.id,q.correctOptionId]));
  for(const q of p.questions){assert.equal(new Set(q.options.map(x=>x.text)).size,4);assert.ok(p.paragraphs.find(x=>x.id===q.evidence.paragraphId)!.english.includes(q.evidence.quote));
   for(const option of q.options){assert.ok(option.explanation);assert.equal(gradeReading(p,{...right,[q.id]:option.id},600,'trial').correct,p.questions.length-(option.id===q.correctOptionId?0:1));}
  }
  assert.equal(readingAccess(baseline,p,false),false);assert.equal(readingAccess(baseline,p,true),true);assert.equal(unlockReading(baseline,p),baseline);
  const state=recordReading(baseline,p,gradeReading(p,right,600,'new'));
  assert.deepEqual(state.reading!.records[old.id].first,prior);assert.deepEqual(state.reading!.unlockedByLevel,baseline.reading!.unlockedByLevel);
  assert.deepEqual(decodeState(JSON.stringify(state)),state);
 }
});
