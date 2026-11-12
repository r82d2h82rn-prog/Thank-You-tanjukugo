#!/usr/bin/env python3
"""Append authored upper-level batches; never rebuild or edit protected L1/L2."""
import collections,hashlib,json,re,sys
from pathlib import Path
from content_pipeline import validate_reading,validate_provenance
from reading_quality import ROOT,protect,main as quality

def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def build(level,form):
 path=ROOT/f'content/authoring/readings/advanced_l{level}_f{form:02}.jsonl'
 authored=[json.loads(x) for x in path.read_text().splitlines() if x.strip()];assert len(authored)==10
 legacy=json.loads((ROOT/'content/readings/drafts.json').read_text());advanced_path=ROOT/'content/readings/advanced.json';data=legacy+(json.loads(advanced_path.read_text()) if advanced_path.exists() else []);protect(data)
 sources=json.loads((ROOT/'content/sources.json').read_text());source_id=f'original-reading-l{level}-v1'
 if not any(x['id']==source_id for x in sources):
  source=dict(next(x for x in sources if x['id']=='original-reading-l2-v1'));source.update(id=source_id,name=f'LEVEL{level} 独自執筆の上級読解教材',notes='独自の仮想事例に基づく教材。実在の研究結果や入試出題実績を主張しない。自動構造検証とAI執筆者確認を実施。独立人間校閲は未完了。');sources.append(source)
 batch=[]
 for i,a in enumerate(authored):
  pid=f'reading-l{level}-f{form:02}-{i+1:02}';paragraphs=[{'id':f'p{j+1}','english':en,'translation':jp} for j,(en,jp) in enumerate(zip(a['en'],a['jp']))];assert len(a['en'])==len(a['jp'])
  body=' '.join(a['en']);wc=len(re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*",body));assert (190 if level==3 else 210)<=wc<=420,(pid,wc)
  questions=[]
  for j,(prompt,options,reasons,quote) in enumerate(a['questions']):
   order=list(range(4));shift=(i+2*j+level)%4;order=order[shift:]+order[:shift]
   questions.append({'id':f'q{j+1}','prompt':prompt,'options':[{'id':'abcd'[k],'text':options[n],'explanation':reasons[n]} for k,n in enumerate(order)],'correctOptionId':'abcd'[order.index(0)],'explanation':reasons[0],'evidence':{'paragraphId':next(p['id'] for p in paragraphs if quote in p['english']),'quote':quote}})
  sentence,jp,explanation,parts,edges=a['syntax'];para=next(p for p in paragraphs if sentence in p['english']);assert para['english'].count(sentence)==1
  start=para['english'].index(sentence);spans=[]
  for j,part in enumerate(parts):
   role,text=part[:2];hits=[m.start() for m in re.finditer(re.escape(text),sentence)]
   assert len(hits)==1 or len(part)==3,(pid,text)
   n=start+hits[part[2] if len(part)==3 else 0];spans.append({'id':f'n{j+1}','role':role,'text':text,'start':n,'end':n+len(text)})
  syntax={'id':'s1','paragraphId':para['id'],'sentence':sentence,'translation':jp,'explanation':explanation,'start':start,'end':start+len(sentence),'spans':spans,'relations':[{'from':f'n{x+1}','to':f'n{y+1}','type':kind} for x,y,kind in edges]}
  content={'sourceIds':[source_id],'contentVersion':1,'qualityStatus':'review_required','autoChecked':True,'humanReviewed':False,'productionApproved':False,'examFrequency':None,'selectionReason':'大学受験標準〜難関の構文と根拠・限定の読解' if level==3 else '最難関を想定した暗黙の前提・譲歩・多重修飾の統合読解','sourceUsage':[{'sourceId':source_id,'fields':['title','paragraphs','questions','syntax','vocabulary']}]}
  p={'id':pid,'level':level,'format':form,'title':a['title'],'paragraphs':paragraphs,'questions':questions,'syntax':[syntax],'wordCount':wc,'recommendedSeconds':round((wc/(75 if level==3 else 60)*60+len(questions)*55)/15)*15,'vocabulary':[{'english':en,'meaning':jp} for en,jp in a.get('vocabulary',[])],'content':content,'difficulty':{'scores':dict(zip(['vocabulary','syntax','logic','questions'],a['scores'])),'method':'ai_author_editorial_v1','status':'author_assessed_independent_review_pending','rationale':a['rationale']},'editorialReview':{'status':'author_checked','reviewer':'AI author; not independent human review','checks':['paragraph-by-paragraph complete translation','all four options compared against text','evidence and limitation of each inference','syntax head/embedded clause and relation targets'],'independentHumanReviewed':False}}
  errors=validate_reading(p)+validate_provenance(content,{s['id']:s for s in sources},False);assert not errors,(pid,errors)
  assert all(type(v)==int and 1<=v<=5 for v in a['scores']);batch.append(p)
 existing={p['id']:p for p in data}
 for p in batch:
  if p['id'] in existing:assert existing[p['id']]==p,'refuse overwrite'
  else:data.append(p)
 protect(data);assert len({p['id'] for p in data})==len(data)
 assert len({' '.join(x['english'] for x in p['paragraphs']).casefold() for p in data})==len(data)
 write(ROOT/f'content/readings/l{level}_f{form:02}.json',batch);write(ROOT/'content/sources.json',sources);write(ROOT/'content/readings/advanced.json',[p for p in data if p['level']>=3])
 checkpoint={'authoredPassages':len(data),'totalQuestions':sum(len(p['questions']) for p in data),'totalWords':sum(p['wordCount'] for p in data),'complete':len(data)==400,'levels':{str(l):{'authoredPassages':sum(p['level']==l for p in data),'countsByFormat':[sum(p['level']==l and p['format']==f for p in data) for f in range(1,11)],'complete':all(sum(p['level']==l and p['format']==f for p in data)==10 for f in range(1,11))} for l in range(1,5)},'humanReviewed':False,'productionApproved':False}
 write(ROOT/'analysis/reading_checkpoint.json',checkpoint)
 write(ROOT/f'analysis/batches/advanced_l{level}_f{form:02}.json',{'ids':[p['id'] for p in batch],'authored':10,'structurallyVerified':10,'aiAuthorChecked':10,'independentlyHumanReviewed':0,'questions':sum(len(p['questions']) for p in batch),'wordCounts':[p['wordCount'] for p in batch],'protectedExistingUnchanged':200,'sha256':hashlib.sha256((ROOT/f'content/readings/l{level}_f{form:02}.json').read_bytes()).hexdigest()})
 quality();print('PASS',level,form,len(batch),'new original passages; protected 200 unchanged')
if __name__=='__main__':build(*map(int,sys.argv[1:3]))
