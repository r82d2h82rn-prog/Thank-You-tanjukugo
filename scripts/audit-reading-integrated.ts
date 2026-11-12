import { readFileSync, writeFileSync } from 'node:fs';
import { readingCatalog } from '../src/readingCatalog';
import { sentenceRanges } from '../src/readingSentences';
import enriched from '../content/readings/enriched.json';
const distribution=(xs:number[])=>Object.fromEntries([...new Set(xs)].sort((a,b)=>a-b).map(v=>[v,xs.filter(x=>x===v).length]));
const report={baseCommit:'1eba13cd88c186a30bf22dc87bbe0c14a9bc0605',scope:`220 saved readings; ${enriched.length} enriched, not full completion`,humanReviewed:0,levels:{} as Record<string,unknown>,passages:[] as unknown[]};
for(const level of [1,2,3,4]){
 const pool=readingCatalog.filter(p=>p.level===level);let sentences=0,syntax=0,translations=0;
 for(const p of pool){
  const ranges=p.paragraphs.flatMap(para=>sentenceRanges(para.id,para.english).map(s=>({...s,paragraphId:para.id})));
  const full=ranges.filter(r=>p.syntax.some(s=>s.paragraphId===r.paragraphId&&s.start===r.start&&s.end===r.end&&s.sentence===r.english));
  const complete=enriched.find(e=>e.id===p.id);sentences+=ranges.length;syntax+=full.length;translations+=complete?.sentences.length??0;
  report.passages.push({id:p.id,level,words:p.wordCount,paragraphs:p.paragraphs.length,questions:p.questions.length,sentences:ranges.length,syntaxCorrespondence:full.length,explicitSentenceTranslations:complete?.sentences.length??0,paragraphTranslations:p.paragraphs.filter(x=>x.translation).length,translationMeaningReview:complete?'AI checked; human pending':'not sentence-aligned; semantic audit pending',revisionCandidate:level>1&&p.wordCount<[0,150,250,400,600][level]});
 }
 report.levels[level]={readings:pool.length,wordRange:[Math.min(...pool.map(x=>x.wordCount)),Math.max(...pool.map(x=>x.wordCount))],paragraphDistribution:distribution(pool.map(x=>x.paragraphs.length)),questionDistribution:distribution(pool.map(x=>x.questions.length)),sentences,fullyMatchedSyntax:syntax,syntaxRate:syntax/sentences,explicitSentenceTranslations:translations,explicitSentenceTranslationRate:translations/sentences};
}
writeFileSync('analysis/reading_integrated_audit.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report.levels));
