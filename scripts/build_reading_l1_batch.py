"""Compile literal human-readable annotations; never infer syntax or translate automatically."""
import copy,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
first,last=map(int,sys.argv[1:]);assert last-first==4 and 41<=first<=last<=60
name=f'l1-{first:03}-{last:03}'
plan=json.loads((ROOT/f'content/authoring/reading-enrichment/{name}.json').read_text())
class Range:
 def __init__(self,row):self.row=row
 def start(self):return self.row['start']
 def end(self):return self.row['end']
 def group(self):return self.row['english']
def ranges(text):
 result=subprocess.run(['node','--import','tsx','scripts/sentence_ranges_json.ts'],input=json.dumps([{'paragraphId':'p','text':text}]),text=True,capture_output=True,cwd=ROOT,check=True)
 return [Range(row) for row in json.loads(result.stdout)[0]]
# Only paragraph boundaries change. The underlying source remains immutable.
def exercise_paragraphs(original):
 starts=plan[original['id']]['starts']
 if not starts:return copy.deepcopy(original['paragraphs']),[]
 source=original['paragraphs'][0];text=source['english'];cuts=[0]+[text.index(x) for x in starts]+[len(text)];rows=[];mapping=[]
 for i,(a,b) in enumerate(zip(cuts,cuts[1:])):
  while b>a and text[b-1].isspace():b-=1
  ident=f'p{i+1}';rows.append({'id':ident,'english':text[a:b],'translation':''});mapping.append({'paragraphId':ident,'sourceParagraphId':source['id'],'start':a,'end':b})
 assert ' '.join(x['english'] for x in rows)==text
 return rows,mapping
base=json.loads((ROOT/'content/readings/drafts.json').read_text())
lines=iter((ROOT/f'content/authoring/reading-enrichment/{name}.tsv').read_text().splitlines())
solutions=['']*5;out=[]
for original,answer in zip(base[first-1:last],solutions):
 p=copy.deepcopy(original);p['content']['contentVersion']=2;p['previousSyntax']=p['syntax'];p['syntax']=[];p['sentences']=[]
 exercise,mapping=exercise_paragraphs(original);p['exerciseParagraphs']=exercise;p['paragraphMappings']=mapping;p['reviewParagraphs']=copy.deepcopy(exercise);p['syntaxOffsetBasis']='reviewParagraphs'
 for source,review in zip(p['exerciseParagraphs'],p['reviewParagraphs']):
  review['english']=source['english'].replace('[1]',answer)
  matches=ranges(review['english'])
  mapping_row=next((x for x in mapping if x['paragraphId']==source['id']),{'sourceParagraphId':source['id'],'start':0})
  gap=source['english'].find('[1]')
  def source_position(position,end=False):
   if gap<0 or position<=gap:return position
   if position>=gap+len(answer):return position-len(answer)+3
   return gap+3 if end else gap

  translations=[]
  for i,m in enumerate(matches):
   old_start=source_position(m.start());old_end=source_position(m.end(),True);old_text=source['english'][old_start:old_end]
   en=m.group();fields=next(lines).split('\t');assert len(fields) in (3,4);jp,annotation,note=fields[:3];meta=json.loads(fields[3]) if len(fields)==4 else {};sid=f"{source['id']}-s{i+1:03}";spans=[];used={}
   for n,part in enumerate(annotation.split(';')):
    role,text=part.split('=',1);hits=[x.start() for x in re.finditer(r'(?<!\w)'+re.escape(text)+r'(?!\w)',en)];assert hits,(p['id'],sid,text)
    k=used.get((role,text),0);start=m.start()+hits[k];used[(role,text)]=k+1
    spans.append({'id':f'n{n+1}','role':role,'text':text,'start':start,'end':start+len(text)})
   assert any(s['role']=='S' for s in spans) or meta.get('implicitSubject') or meta.get('structureType')=='formula'
   assert any(s['role']=='V' for s in spans) or meta.get('structureType')=='formula'
   if meta.get('structureType')=='formula':assert en=='Best wishes, The camp team.'
   if meta.get('implicitSubject'):assert original['id']=='reading-l1-f05-04'

   relations=[]
   explanation=note
   syntax={'id':f"{p['id']}:{sid}",'passageId':p['id'],'contentVersion':2,'paragraphId':source['id'],'sentenceId':sid,'sentence':en,'start':m.start(),'end':m.end(),'translation':jp,'explanation':explanation,'spans':spans,'relations':relations,'skeleton':' / '.join(s['role']+': '+s['text'] for s in spans if s['role'] in ('S','V','O','C')),'grammarPoints':[note],'readingOrder':'主節の主語と動詞を確認し、解説に沿って句節・否定・比較の範囲を読み、日本語訳で意味を確かめる。','reviewStatus':'ai_author_checked_human_pending','offsetBasis':'reviewParagraphs'}
   syntax.update(meta)
   if meta.get('implicitSubject'):syntax['skeleton']='S（省略）: '+meta['implicitSubject']+' / '+syntax['skeleton']
   if meta.get('structureType')=='formula':syntax['skeleton']='書簡の結辞と署名（定形動詞なし）'
   p['syntax'].append(syntax);p['sentences'].append({'id':sid,'paragraphId':source['id'],'english':en,'translation':jp,'start':m.start(),'end':m.end(),'sourceEnglish':old_text,'sourceStart':old_start+mapping_row['start'],'sourceEnd':old_end+mapping_row['start'],'sourceParagraphId':mapping_row['sourceParagraphId'],'syntaxId':syntax['id']});translations.append(jp)
  source['translation']=review['translation']=''.join(translations)
 for raw in p['paragraphs']:
  selected=[x for x in p['reviewParagraphs'] if next((m['sourceParagraphId'] for m in mapping if m['paragraphId']==x['id']),x['id'])==raw['id']]
  raw['translation']=''.join(x['translation'] for x in selected)
 p['reviewEvidence']={q['id']:{'paragraphId':next(x['id'] for x in p['reviewParagraphs'] if q['evidence']['quote'] in x['english']),'quote':q['evidence']['quote']} for q in p['questions']}
 p['reviewWordCount']=len(re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*",' '.join(x['english'] for x in p['reviewParagraphs'])))
 p['review']={'fullTranslation':'ai_checked_human_pending','fullSyntax':'ai_checked_human_pending','questionUniqueness':'ai_checked_human_pending'};out.append(p)
try:next(lines);raise AssertionError('unused authored annotation')
except StopIteration:pass






for p in out:
 spec=plan[p['id']]
 for syntax in p['syntax']:
  for modifier,head in spec.get('links',[]):
   node=next((x for x in syntax['spans'] if x['text']==modifier),None)
   if not node:continue
   target=next((x for x in syntax['spans'] if x['text']==head),None)
   if not target:
    assert head in syntax['sentence'];at=syntax['sentence'].index(head)+syntax['start'];ident=f"n{len(syntax['spans'])+1}"
    target={'id':ident,'role':'phrase','text':head,'start':at,'end':at+len(head),'kind':'修飾先'};syntax['spans'].append(target)
   syntax['relations'].append({'from':node['id'],'to':target['id'],'type':'modifies'})
 for prompt,options,reasons,quote in spec['questions']:
  assert len(options)==len(reasons)==4 and len(set(options))==4
  order=list(range(4));shift=(first+len(p['questions']))%4;order=order[shift:]+order[:shift];qid=f"q{len(p['questions'])+1}"
  evidence={'paragraphId':next(x['id'] for x in p['paragraphs'] if quote in x['english']),'quote':quote}
  p['questions'].append({'id':qid,'prompt':prompt,'options':[{'id':'abcd'[n],'text':options[j],'explanation':reasons[j]} for n,j in enumerate(order)],'correctOptionId':'abcd'[order.index(0)],'explanation':reasons[0],'evidence':evidence})
  p['reviewEvidence'][qid]={'paragraphId':next(x['id'] for x in p['reviewParagraphs'] if quote in x['english']),'quote':quote}
path=ROOT/f'content/readings/enriched-level1-{first:03}-{last:03}.json'
if path.exists():assert json.loads(path.read_text())==out,'refuse changed saved revision'
path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('Compiled',len(out),'readings and',sum(len(p['sentences']) for p in out),'sentences')
