import { readFileSync, writeFileSync } from 'node:fs';
import { readingCatalog } from '../src/readingCatalog';
import { readingParagraphs } from '../src/readings';
import { sentenceRanges } from '../src/readingSentences';
import {readingRevisions as enriched} from '../src/readingRevisions';
const actualWords=(p:Parameters<typeof readingParagraphs>[0])=>readingParagraphs(p,true).map(x=>x.english).join(' ').match(/[A-Za-z]+(?:['-][A-Za-z]+)*/g)?.length??0;
const distribution=(xs:number[])=>Object.fromEntries([...new Set(xs)].sort((a,b)=>a-b).map(v=>[v,xs.filter(x=>x===v).length]));
const report={baseCommit:'c50c06942d867856ceb8fec12dddd82d127861b5',scope:`220 saved readings; ${enriched.length} enriched, not full completion`,humanReviewed:0,levels:{} as Record<string,unknown>,passages:[] as unknown[]};
for(const level of [1,2,3,4]){
 const pool=readingCatalog.filter(p=>p.level===level);let sentences=0,syntax=0,translations=0;
 for(const p of pool){
  const ranges=readingParagraphs(p,true).flatMap(para=>sentenceRanges(para.id,para.english).map(s=>({...s,paragraphId:para.id})));
  const full=ranges.filter(r=>p.syntax.some(s=>s.paragraphId===r.paragraphId&&s.start===r.start&&s.end===r.end&&s.sentence===r.english));
  const complete=enriched.find(e=>e.id===p.id);sentences+=ranges.length;syntax+=full.length;translations+=complete?.sentences.length??0;
  report.passages.push({id:p.id,level,words:actualWords(p),sourceWords:p.wordCount,paragraphs:readingParagraphs(p,false).length,questions:p.questions.length,sentences:ranges.length,syntaxCorrespondence:full.length,explicitSentenceTranslations:complete?.sentences.length??0,paragraphTranslations:p.paragraphs.filter(x=>x.translation).length,translationMeaningReview:complete?'AI checked; human pending':'not sentence-aligned; semantic audit pending',revisionCandidate:level>1&&p.wordCount<[0,150,250,400,600][level]});
 }
 report.levels[level]={readings:pool.length,wordRange:[Math.min(...pool.map(actualWords)),Math.max(...pool.map(actualWords))],wordDistribution:distribution(pool.map(actualWords)),paragraphDistribution:distribution(pool.map(x=>readingParagraphs(x,false).length)),questionDistribution:distribution(pool.map(x=>x.questions.length)),sentences,fullyMatchedSyntax:syntax,syntaxRate:syntax/sentences,explicitSentenceTranslations:translations,explicitSentenceTranslationRate:translations/sentences};
}
writeFileSync('analysis/reading_integrated_audit.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report.levels));
