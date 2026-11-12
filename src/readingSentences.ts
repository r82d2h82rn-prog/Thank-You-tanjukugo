export interface SentenceRange { id:string; english:string; start:number; end:number }
export function sentenceRanges(paragraphId:string,text:string):SentenceRange[] {
 const result:SentenceRange[]=[];let start=0;
 const abbr=/\b(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|St|vs|etc|e\.g|i\.e)\.$/i;
 for(let i=0;i<text.length;i++){
  if(!/[.!?]/.test(text[i]))continue;
  if(text[i]==='.'&&(/\d/.test(text[i-1]??'')&&/\d/.test(text[i+1]??'')))continue;
  if(text[i]==='.'&&(abbr.test(text.slice(start,i+1))||/\b[A-Z]\.$/.test(text.slice(start,i+1))))continue;
  let end=i+1;while(/["'”’)]/.test(text[end]??'')&&end<text.length)end++;
  if(end<text.length&&!/\s/.test(text[end]))continue;
  result.push({id:`${paragraphId}-s${String(result.length+1).padStart(3,'0')}`,english:text.slice(start,end),start,end});
  while(end<text.length&&/\s/.test(text[end]))end++;start=end;i=end-1;
 }
 if(start<text.length)result.push({id:`${paragraphId}-s${String(result.length+1).padStart(3,'0')}`,english:text.slice(start),start,end:text.length});
 return result;
}
