import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import legacy from '../content/readings/drafts.json';
import advanced from '../content/readings/advanced.json';
import ratings from '../content/readings/difficulty.json';
import { readingCatalog } from '../src/readingCatalog';
import { gradeReading } from '../src/readings';
test('legacy source bytes stay identical and all 200 IDs remain in the combined catalogue',()=>{
 assert.deepEqual(readFileSync('content/readings/drafts.json'),readFileSync('content/backups/readings-20261113/level1-level2.json'));
 assert.equal(legacy.length,200);
 assert.equal(new Set(readingCatalog.map(p=>p.id)).size,readingCatalog.length);
 for(const p of legacy) { const current=readingCatalog.find(x=>x.id===p.id)!; assert.deepEqual(current.paragraphs.slice(0,p.paragraphs.length).map(x=>({id:x.id,english:x.english})),p.paragraphs.map(x=>({id:x.id,english:x.english}))); assert.deepEqual(current.questions.slice(0,p.questions.length),p.questions); }
});
test('upper-level answers grade exactly once and changing one answer changes the score by one',()=>{
 for(const raw of advanced){
  const p=readingCatalog.find(p=>p.id===raw.id)!;
  const answers=Object.fromEntries(p.questions.map(q=>[q.id,q.correctOptionId]));
  assert.equal(gradeReading(p,answers,120,'first').correct,p.questions.length);
  for(const q of p.questions) for(const wrong of q.options.filter(o=>o.id!==q.correctOptionId)) assert.equal(gradeReading(p,{...answers,[q.id]:wrong.id},120,'wrong').correct,p.questions.length-1);
  for(const score of Object.values(raw.difficulty.scores))assert.ok(Number.isInteger(score)&&score>=1&&score<=5);
  assert.equal(raw.editorialReview.independentHumanReviewed,false);
 }
 assert.equal(Object.keys(ratings.ratings).length,readingCatalog.length);
});
