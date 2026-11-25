import {test} from 'node:test';
import assert from 'node:assert/strict';
import batch from '../content/readings/l3_f04.json';
import oldGap from '../content/readings/l3_f03.json';
import advanced from '../content/readings/advanced.json';
import policy from '../content/authoring/readings/level3-word-policy.json';
import {readingCatalog} from '../src/readingCatalog';
import {readingParagraphs,gradeReading,recordReading,unlockReading,readingAccess} from '../src/readings';
import {sentenceRanges} from '../src/readingSentences';
import {emptyState,decodeState} from '../src/model';

test('ten title readings append new identities, obey word bands and contain no gap or solution machinery',()=>{
 assert.ok(readingCatalog.length>=250);assert.ok(advanced.length>=50);
 assert.deepEqual(advanced.slice(30,40),oldGap);assert.deepEqual(advanced.slice(40,50),batch);
 assert.equal(new Set(readingCatalog.map(p=>p.id)).size,readingCatalog.length);
 for(const [i,p] of batch.entries()){
  assert.equal(p.id,`reading-l3-f04-${String(i+1).padStart(2,'0')}`);
  assert.deepEqual(readingCatalog.find(x=>x.id===p.id),p);assert.equal(p.format,4);
  const en=p.paragraphs.map(x=>x.english).join(' '),count=en.match(/[A-Za-z]+(?:['-][A-Za-z]+)*/g)!.length;
  assert.equal(count,p.wordCount);const band=policy.bandsByItemWithinFormat[i];
  assert.ok(count>=band.min&&count<=band.max);assert.ok(Math.abs(count-policy.targetsByFormat['4'][i])<=2);
  assert.ok(!/\[[1-9A-D]\]/.test(en));assert.ok(!('gapSolutions' in p));assert.ok(!('insert' in p));
  assert.equal(readingParagraphs(p,false),p.paragraphs);assert.equal(readingParagraphs(p,true),p.paragraphs);
  assert.ok(p.questions[0].prompt.includes('題名'));assert.equal(p.content.humanReviewed,false);
  assert.ok(p.paragraphs.length>=4&&p.paragraphs.length<=8);assert.ok(p.questions.length>=5&&p.questions.length<=8);
 }
});

test('all 280 sentences have exact translations, syntax spans and paragraph coordinates',()=>{
 assert.equal(batch.reduce((n,p)=>n+p.sentences.length,0),280);
 for(const p of batch)for(const para of p.paragraphs){
  const rows=p.sentences.filter(s=>s.paragraphId===para.id);
  assert.deepEqual(rows.map(s=>({id:s.id,english:s.english,start:s.start,end:s.end})),sentenceRanges(para.id,para.english));
  assert.equal(para.translation,rows.map(s=>s.translation).join(''));
  for(const row of rows){
   assert.equal(para.english.slice(row.start,row.end),row.english);
   assert.equal(row.sourceStart,row.start);assert.equal(row.sourceEnd,row.end);assert.equal(row.sourceEnglish,row.english);
   const sy=p.syntax.find(s=>s.id===row.syntaxId)!;assert.ok(sy);assert.equal(sy.sentence,row.english);assert.equal(sy.translation,row.translation);
   assert.equal(sy.start,row.start);assert.equal(sy.end,row.end);assert.ok(sy.explanation&&sy.grammarPoints.length);
   assert.ok(sy.spans.some(n=>n.role==='S'));assert.ok(sy.spans.some(n=>n.role==='V'));
   for(const node of sy.spans){assert.equal(para.english.slice(node.start,node.end),node.text);assert.ok(node.start>=row.start&&node.end<=row.end);}
   const ids=new Set(sy.spans.map(n=>n.id));for(const rel of sy.relations){assert.ok(ids.has(rel.from));assert.ok(ids.has(rel.to));}
  }
 }
});

test('all 65 questions grade every option and preserve previous reading attempts and free unlock slots',()=>{
 assert.equal(batch.reduce((n,p)=>n+p.questions.length,0),65);
 const old=oldGap[0],prior=gradeReading(old,Object.fromEntries(old.questions.map(q=>[q.id,q.correctOptionId])),600,'prior');
 let baseline=recordReading(emptyState(),old,prior);
 for(const p of oldGap.slice(0,3))baseline=unlockReading(baseline,p);
 for(const p of batch){
  const right=Object.fromEntries(p.questions.map(q=>[q.id,q.correctOptionId]));
  for(const q of p.questions){
   assert.equal(new Set(q.options.map(o=>o.text)).size,4);
   assert.ok(p.paragraphs.find(x=>x.id===q.evidence.paragraphId)!.english.includes(q.evidence.quote));
   for(const o of q.options){assert.ok(o.explanation);assert.equal(gradeReading(p,{...right,[q.id]:o.id},600,'trial').correct,p.questions.length-(o.id===q.correctOptionId?0:1));}
  }
  assert.equal(readingAccess(baseline,p,false),false);assert.equal(readingAccess(baseline,p,true),true);
  assert.equal(unlockReading(baseline,p),baseline);
  const state=recordReading(baseline,p,gradeReading(p,right,600,'next'));
  assert.deepEqual(state.reading!.records[old.id].first,prior);assert.deepEqual(state.reading!.unlockedByLevel,baseline.reading!.unlockedByLevel);
  assert.deepEqual(decodeState(JSON.stringify(state)),state);
 }
});
