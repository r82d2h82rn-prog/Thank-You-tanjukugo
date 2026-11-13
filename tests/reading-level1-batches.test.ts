import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import legacy from '../content/readings/drafts.json';
import {readingRevisions} from '../src/readingRevisions';
import {readingCatalog} from '../src/readingCatalog';
import {Passage,gradeReading,recordReading,readingParagraphs,readingQuestionEvidence} from '../src/readings';
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
  assert.deepEqual(p.paragraphs.map((x:any)=>[x.id,x.english]),old.paragraphs.map(x=>[x.id,x.english]));
  assert.equal(readingParagraphs(p,false).map(x=>x.english).join(' '),old.paragraphs.map(x=>x.english).join(' '));
  assert.deepEqual(readingCatalog.find(x=>x.id===p.id),p);
  const answer=old.questions[0].options.find(o=>o.id===old.questions[0].correctOptionId)!.text;
  for(const para of readingParagraphs(p,true)){
   const exercise=readingParagraphs(p,false).find(x=>x.id===para.id)!;
   assert.equal(para.english,exercise.english.replace('[1]',answer));
   const rows=p.sentences.filter((s:any)=>s.paragraphId===para.id);
   assert.deepEqual(rows.map(({id,english,start,end}:any)=>({id,english,start,end})),sentenceRanges(para.id,para.english));
   assert.equal(para.translation,rows.map((s:any)=>s.translation).join(''));
   for(const s of rows){
    const source=old.paragraphs.find(x=>x.id===(s.sourceParagraphId??s.paragraphId))!;
    assert.equal(source.english.slice(s.sourceStart,s.sourceEnd),s.sourceEnglish);
    assert.equal(s.sourceEnglish.replace('[1]',answer),s.english);
    const syntax=p.syntax.find((x:any)=>x.id===s.syntaxId)!;
    assert.equal(syntax.sentence,s.english);assert.equal(syntax.translation,s.translation);
    if(syntax.structureType==='formula'){
     assert.equal(p.id,'reading-l1-f05-04');assert.equal(s.english,'Best wishes, The camp team.');assert.ok(!syntax.spans.some((x:any)=>x.role==='V'));
    }else{
     if(syntax.implicitSubject){assert.equal(p.id,'reading-l1-f05-04');assert.ok(['We','you'].includes(syntax.implicitSubject));assert.ok(!syntax.spans.some((x:any)=>x.role==='S'));}
     else assert.ok(syntax.spans.some((x:any)=>x.role==='S'));
     assert.ok(syntax.spans.some((x:any)=>x.role==='V'));
    }
    for(const span of syntax.spans)assert.equal(para.english.slice(span.start,span.end),span.text);
    const ids=new Set(syntax.spans.map((x:any)=>x.id));for(const edge of syntax.relations){assert.ok(ids.has(edge.from));assert.ok(ids.has(edge.to));}
   }
  }
  assert.ok(p.questions.length>=3&&p.questions.length<=5);
  const right=Object.fromEntries(p.questions.map((q:any)=>[q.id,q.correctOptionId]));
  for(const q of p.questions){assert.equal(q.options.length,4);assert.equal(new Set(q.options.map((o:any)=>o.id)).size,4);assert.ok(p.paragraphs.find((x:any)=>x.id===q.evidence.paragraphId).english.includes(q.evidence.quote));
   const evidence=readingQuestionEvidence(p,q);assert.ok(readingParagraphs(p,true).find(x=>x.id===evidence.paragraphId)!.english.includes(evidence.quote));
   for(const o of q.options){assert.ok(o.explanation);assert.equal(gradeReading(p,{...right,[q.id]:o.id},60,'new').correct,p.questions.length-(o.id===q.correctOptionId?0:1));}
  }
  const prior=gradeReading(old,Object.fromEntries(old.questions.map(q=>[q.id,q.correctOptionId])),60,'old');
  const state=recordReading(recordReading(emptyState(),old,prior),p,gradeReading(p,right,70,'new'));
  assert.deepEqual(state.reading!.records[p.id].first,prior);assert.equal(prior.total,3);assert.deepEqual(decodeState(JSON.stringify(state)),state);
 }
});

test('logical paragraph restoration retains source coordinates and relocates displayed evidence',()=>{
 for(const id of ['reading-l1-f03-09','reading-l1-f03-10']){
  const p=readingCatalog.find(x=>x.id===id)!;
  assert.equal(p.paragraphs.length,1);assert.equal(readingParagraphs(p,false).length,3);assert.equal(readingParagraphs(p,true).length,3);
  assert.ok(readingQuestionEvidence(p,p.questions[2]).paragraphId!=='p1');
 }
 const lee=readingCatalog.find(x=>x.id==='reading-l1-f03-10')!;
 const sentences=readingParagraphs(lee,true).flatMap(p=>sentenceRanges(p.id,p.english));
 assert.ok(sentences.some(s=>s.english==='Mr. Lee changed the next discussion.'));
 assert.ok(!sentences.some(s=>s.english==='Mr.'));
});

test('object-depictive participles link to the depicted people',()=>{
 for(const [id,text,head] of [['reading-l1-f03-01','laughing beside a river','three friends'],['reading-l1-f04-03','filling part of it with earth','workers']]){
  const p=readingCatalog.find(p=>p.id===id)!;const syntax=p.syntax.find(s=>s.spans.some(x=>x.text===text))!;
  const from=syntax.spans.find(s=>s.text===text)!,to=syntax.spans.find(s=>s.text===head)!;
  assert.ok(syntax.relations.some(x=>x.from===from.id&&x.to===to.id));
 }
});
