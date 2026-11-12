#!/usr/bin/env python3
"""Validate original reading batches and materialize exercise-ready drafts without approval."""
import collections,hashlib,json,re
from pathlib import Path
from content_pipeline import ROOT,NOW,read_json,write_json,validate_reading,validate_provenance

def build():
 sources=read_json(ROOT/'content/sources.json')
 for level in [1,2]:
  source_id=f'original-reading-l{level}-v1'
  if not any(s['id']==source_id for s in sources):
   source=dict(next(s for s in sources if s['id']=='original-draft-v4'));source.update(id=source_id,name=f'LEVEL{level} 独自執筆の長文・設問・和訳・構文',checkedAt=NOW(),notes='本プロジェクトで独自執筆した読解教材。語数・構造・解答根拠・構文位置を検査。自然さ・難易度・解答一意性は人手校閲待ち。');sources.append(source);write_json(ROOT/'content/sources.json',sources)
 source_map={s['id']:s for s in sources};result=[];ids=set();bodies=set();checkpoints=[]
 for file in sorted((ROOT/'content/authoring/readings').glob('l[1-4]_f*.jsonl')):
  level=int(re.search(r'l(\d)_f',file.stem)[1]);source_id=f'original-reading-l{level}-v1'
  authored=[json.loads(line) for line in file.read_text().splitlines() if line.strip()];batch=[];form=int(re.search(r'_f(\d+)',file.stem)[1]);assert 1<=len(authored)<=10,(file,len(authored))
  for i,a in enumerate(authored):
   pid=f'reading-l{level}-f{form:02}-{i+1:02}';assert pid not in ids;ids.add(pid)
   paragraphs=[dict(id=f'p{j+1}',english=p[0],translation=p[1]) for j,p in enumerate(a['paragraphs'])]
   body=' '.join(p['english'] for p in paragraphs);word_count=len(re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*",body))
   assert (150 if level==1 else 160)<=word_count<=(250 if level==1 else 320),(pid,word_count)
   assert body.casefold() not in bodies; bodies.add(body.casefold());questions=[]
   assert len(a['questions']) in range(3,11)
   for j,q in enumerate(a['questions']):
    prompt,options,reasons,evidence=q;assert len(options)==len(reasons)==4
    rotation=(i+j+form)%4;ordered=list(range(4));ordered=ordered[rotation:]+ordered[:rotation]
    choices=[dict(id='abcd'[n],text=options[original],explanation=reasons[original]) for n,original in enumerate(ordered)]
    correct='abcd'[ordered.index(0)]
    questions.append(dict(id=f'q{j+1}',prompt=prompt,options=choices,correctOptionId=correct,explanation=reasons[0],evidence=dict(paragraphId=f'p{evidence[0]}',quote=evidence[1])))
   para_number,sentence,parts,jp,explanation=a['syntax'];para=paragraphs[para_number-1];assert para['english'].count(sentence)==1,(pid,sentence)
   sentence_start=para['english'].index(sentence);spans=[]
   for j,(role,text) in enumerate(parts):
    assert sentence.count(text)==1,(pid,text)
    start=sentence_start+sentence.index(text);spans.append(dict(id=f'n{j+1}',role=role,text=text,start=start,end=start+len(text)))
   verb=next((s['id'] for s in spans if s['role']=='V'),None)
   syntax=[dict(id='s1',paragraphId=para['id'],sentence=sentence,start=sentence_start,end=sentence_start+len(sentence),translation=jp,explanation=explanation,spans=spans,relations=[dict(**{'from':s['id'],'to':verb},type='modifies') for s in spans if s['role'] in ('M','phrase') and verb])]
   passage=dict(id=pid,level=level,format=form,title=a['title'],paragraphs=paragraphs,questions=questions,syntax=syntax,wordCount=word_count,recommendedSeconds=round((word_count/90*60+len(questions)*35)/15)*15,vocabulary=[dict(english=w,meaning=m) for w,m in a.get('vocabulary',[])],content=dict(sourceIds=[source_id],contentVersion=1,qualityStatus='review_required',autoChecked=True,humanReviewed=False,productionApproved=False,examFrequency=None,selectionReason='高校入試相当を目安とする150〜250語の独自長文。各形式10題。難易度・自然さ・解答一意性は校閲待ち。' if level==1 else '高校初級〜中級を目安とする160〜320語の独自長文。各形式10題。難易度・自然さ・解答一意性は校閲待ち。',sourceUsage=[dict(sourceId=source_id,fields=['title','paragraphs','questions','syntax','vocabulary'])]))
   if 'paragraphOrder' in a:passage['paragraphOrder']=[f'p{n}' for n in a['paragraphOrder']];assert set(passage['paragraphOrder'])=={p['id'] for p in paragraphs}
   if 'insert' in a:passage['insert']=a['insert']
   errors=validate_reading(passage)+validate_provenance(passage['content'],source_map,False);assert not errors,(pid,errors)
   batch.append(passage)
  path=ROOT/f'content/readings/l{level}_f{form:02}.json'
  if path.exists():
   previous=read_json(path);assert previous==batch[:len(previous)],'Existing reading changed: '+str(path)
  write_json(path,batch)
  result+=batch
  check=dict(checkedAt=NOW(),file=str(path.relative_to(ROOT)),level=level,format=form,count=len(batch),wordCounts=[p['wordCount'] for p in batch],questions=sum(len(p['questions']) for p in batch),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),checks=['150-250 words' if level==1 else '160-320 words','at most 10 original passages per format; quota checked on completion','four unique options per question','answer evidence occurs verbatim','syntax spans match original characters'],humanReviewed=False)
  write_json(ROOT/f'analysis/batches/readings_l{level}_f{form:02}.json',check);checkpoints.append(check)
 write_json(ROOT/'content/readings/drafts.json',result)
 advanced_path=ROOT/'content/readings/advanced.json'
 if advanced_path.exists():result+=read_json(advanced_path)
 levels={}
 for level in range(1,5):
  pool=[p for p in result if p['level']==level];counts=[sum(p['format']==f for p in pool) for f in range(1,11)]
  levels[str(level)]=dict(authoredPassages=len(pool),countsByFormat=counts,totalQuestions=sum(len(p['questions']) for p in pool),totalWords=sum(p['wordCount'] for p in pool),complete=len(pool)==100 and counts==[10]*10)
 summary=dict(updatedAt=NOW(),authoredPassages=len(result),totalQuestions=sum(len(p['questions']) for p in result),totalWords=sum(p['wordCount'] for p in result),levels=levels,complete=len(result)==400 and all(x['complete'] for x in levels.values()),humanReviewed=False,productionApproved=False,batches=[c['file'] for c in checkpoints])
 write_json(ROOT/'analysis/reading_checkpoint.json',summary);print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':build()
