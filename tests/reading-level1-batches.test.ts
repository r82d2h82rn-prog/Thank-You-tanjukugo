import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import legacy from '../content/readings/drafts.json';
import {readingRevisions} from '../src/readingRevisions';
import {readingCatalog} from '../src/readingCatalog';
import {Passage,gradeReading,recordReading,readingParagraphs} from '../src/readings';
import {sentenceRanges} from '../src/readingSentences';
import {emptyState,decodeState} from '../src/model';
for(const file of readdirSync('content/readings').filter(x=>/^enriched-level1-\d+-\d+\.json$/.test(x)))test(`Level 1 preserves sources, scores, gaps and complete sentence alignment: ${file}`,()=>{
 const batch=JSON.parse(readFileSync(`content/readings/${file}`,'utf8'));
 assert.equal(batch.length,5);assert.equal(new Set(readingRevisions.map(p=>p.id)).size,readingRevisions.length);
 assert.ok(new Set(batch.map((p:Passage)=>p.questions.length)).size>1);
 for(const p of batch){
  const old=legacy.find(x=>x.id===p.id)!;
  assert.ok(old);assert.equal(p.level,1);assert.equal(p.content.contentVersion,2);
  assert.deepEqual(p.previousSyntax,old.syntax);assert.deepEqual(p.questions.slice(0,old.questions.length),old.questions);
  assert.deepEqual(readingParagraphs(p,false).map(x=>[x.id,x.english]),old.paragraphs.map(x=>[x.id,x.english]));
  assert.deepEqual(readingCatalog.find(x=>x.id===p.id),p);
  const answer=old.questions[0].options.find(o=>o.id===old.questions[0].correctOptionId)!.text;
  for(const para of readingParagraphs(p,true)){
   const source=old.paragraphs.find(x=>x.id===para.id)!;
   assert.equal(para.english,source.english.replace('[1]',answer));
   const rows=p.sentences.filter((s:any)=>s.paragraphId===para.id);
   assert.deepEqual(rows.map(({id,english,start,end}:any)=>({id,english,start,end})),sentenceRanges(para.id,para.english));
   assert.equal(para.translation,rows.map((s:any)=>s.translation).join(''));
   for(const s of rows){
    assert.equal(source.english.slice(s.sourceStart,s.sourceEnd),s.sourceEnglish);
    const syntax=p.syntax.find((x:any)=>x.id===s.syntaxId)!;
    assert.equal(syntax.sentence,s.english);assert.equal(syntax.translation,s.translation);
    assert.ok(syntax.spans.some((x:any)=>x.role==='S'));assert.ok(syntax.spans.some((x:any)=>x.role==='V'));
    for(const span of syntax.spans)assert.equal(para.english.slice(span.start,span.end),span.text);
    const ids=new Set(syntax.spans.map((x:any)=>x.id));for(const edge of syntax.relations){assert.ok(ids.has(edge.from));assert.ok(ids.has(edge.to));}
   }
  }
  assert.ok(p.questions.length>=3&&p.questions.length<=5);
  const right=Object.fromEntries(p.questions.map((q:any)=>[q.id,q.correctOptionId]));
  for(const q of p.questions){assert.equal(q.options.length,4);assert.equal(new Set(q.options.map((o:any)=>o.id)).size,4);assert.ok(p.paragraphs.find((x:any)=>x.id===q.evidence.paragraphId).english.includes(q.evidence.quote));
   for(const o of q.options){assert.ok(o.explanation);assert.equal(gradeReading(p,{...right,[q.id]:o.id},60,'new').correct,p.questions.length-(o.id===q.correctOptionId?0:1));}
  }
  const prior=gradeReading(old,Object.fromEntries(old.questions.map(q=>[q.id,q.correctOptionId])),60,'old');
  const state=recordReading(recordReading(emptyState(),old,prior),p,gradeReading(p,right,70,'new'));
  assert.deepEqual(state.reading!.records[p.id].first,prior);assert.equal(prior.total,3);assert.deepEqual(decodeState(JSON.stringify(state)),state);
 }
});
