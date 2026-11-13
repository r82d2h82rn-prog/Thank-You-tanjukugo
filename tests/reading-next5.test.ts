import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import legacy from '../content/readings/drafts.json';
import advanced from '../content/readings/advanced.json';
import {readingRevisions} from '../src/readingRevisions';
import {readingCatalog} from '../src/readingCatalog';
import {Passage,ReadingSyntax,gradeReading,recordReading} from '../src/readings';
import {sentenceRanges} from '../src/readingSentences';
import {emptyState,decodeState} from '../src/model';
type Revision=Passage & {content:{contentVersion:number;humanReviewed:boolean};previousSyntax:ReadingSyntax[];sentences:{id:string;paragraphId:string;english:string;translation:string;start:number;end:number;syntaxId:string}[]};
for(const file of readdirSync('content/readings').filter(x=>/^enriched-level[234]-next5.json$/.test(x)))test(`complete aligned 06–10 revisions, unique grading and old score preservation: ${file}`,()=>{
 const batch=JSON.parse(readFileSync(`content/readings/${file}`,'utf8')) as Revision[];
 assert.equal(batch.length,5);assert.equal(new Set(readingRevisions.map(p=>p.id)).size,readingRevisions.length);
 const level=batch[0].level,base=[...legacy,...advanced].filter(p=>p.level===level).slice(5,10);
 assert.deepEqual(batch.map(p=>p.id),base.map(p=>p.id));
 assert.ok(new Set(batch.map(p=>p.questions.length)).size>1);assert.ok(new Set(batch.map(p=>p.paragraphs.length)).size>1);
 for(const [i,p] of batch.entries()){
  const old=base[i],limits={1:[150,250,3,5],2:[250,400,4,7],3:[400,600,5,8],4:[600,900,6,10]}[level];
  const words=p.paragraphs.map(x=>x.english).join(' ').match(/[A-Za-z]+(?:['-][A-Za-z]+)*/g)!.length;
  assert.equal(words,p.wordCount);assert.ok(words>=limits[0]&&words<=limits[1]);assert.ok(p.questions.length>=limits[2]&&p.questions.length<=limits[3]);
  assert.equal(p.content.contentVersion,old.content.contentVersion+1);assert.equal(p.content.humanReviewed,false);
  assert.deepEqual(p.previousSyntax,old.syntax);assert.deepEqual(p.questions.slice(0,old.questions.length),old.questions);
  assert.deepEqual(p.paragraphs.slice(0,old.paragraphs.length).map(x=>[x.id,x.english]),old.paragraphs.map(x=>[x.id,x.english]));
  assert.deepEqual(readingCatalog.find(x=>x.id===p.id),p);
  for(const para of p.paragraphs){
   const rows=p.sentences.filter(s=>s.paragraphId===para.id);
   assert.deepEqual(rows.map(s=>({id:s.id,english:s.english,start:s.start,end:s.end})),sentenceRanges(para.id,para.english));
   assert.equal(para.translation,rows.map(s=>s.translation).join(''));
   for(const s of rows){const syntax=p.syntax.find(x=>x.id===s.syntaxId)!;assert.ok(syntax);assert.equal(syntax.sentence,s.english);assert.equal(syntax.translation,s.translation);assert.ok(syntax.explanation);
    for(const span of syntax.spans)assert.equal(para.english.slice(span.start,span.end),span.text);
    const ids=new Set(syntax.spans.map(x=>x.id));for(const edge of syntax.relations){assert.ok(ids.has(edge.from));assert.ok(ids.has(edge.to));}
   }
  }
  const right=Object.fromEntries(p.questions.map(q=>[q.id,q.correctOptionId]));
  for(const q of p.questions)for(const o of q.options){assert.ok(o.explanation);assert.equal(gradeReading(p,{...right,[q.id]:o.id},400,'new').correct,p.questions.length-(o.id===q.correctOptionId?0:1));}
  const prior=gradeReading(old,Object.fromEntries(old.questions.map(q=>[q.id,q.correctOptionId])),300,'old');
  const state=recordReading(recordReading(emptyState(),old,prior),p,gradeReading(p,right,400,'new'));
  assert.deepEqual(state.reading!.records[p.id].first,prior);assert.equal(state.reading!.records[p.id].first.total,3);
  assert.deepEqual(decodeState(JSON.stringify(state)),state);
 }
});
