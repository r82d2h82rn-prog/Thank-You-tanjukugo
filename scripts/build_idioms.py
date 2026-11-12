#!/usr/bin/env python3
"""Import independently authored idiom batches without altering existing sample identities."""
import collections,csv,hashlib,json,pathlib,re,sys
import eng_to_ipa as ipa
from content_pipeline import ROOT,NOW,read_json,write_json,validate_entry,audit

def build():
 samples=[e for e in read_json(ROOT/'src/data/entries.json') if e['kind']=='idiom'];seen_words={e['english'].casefold() for e in samples};seen_ids={e['id'] for e in samples};examples=set();results=[];summaries=[]
 sources=read_json(ROOT/'content/sources.json')
 if not any(s['id']=='original-idiom-batches-v1' for s in sources):
  source=dict(next(s for s in sources if s['id']=='original-draft-v4'));source.update(id='original-idiom-batches-v1',name='LEVEL1・2 独自執筆の熟語教材',checkedAt=NOW(),notes='本会話で熟語本文・英語例文・和訳・用法を独自執筆。IPAはCMU辞書を使う語単位自動変換で校閲待ち。')
  sources.append(source);write_json(ROOT/'content/sources.json',sources)
 source_map={s['id']:s for s in sources}
 for file in sorted((ROOT/'content/authoring/idioms').glob('l*.psv')):
  m=re.fullmatch(r'l([12])_(\d+)(?:_(\d+))?\.psv',file.name);assert m,file
  level,start,end=int(m[1]),int(m[2]),int(m[3] or m[2]);rows=[line.split('|') for line in file.read_text().splitlines() if line.strip()]
  assert len(rows)==(end-start+1)*50,(file,len(rows));batch=[]
  for i,row in enumerate(rows):
   assert len(row)==5,(file,row)
   english,meaning,example,translation,explanation=row;assert english.casefold() not in seen_words,english;seen_words.add(english.casefold());assert example.casefold() not in examples,example;examples.add(example.casefold())
   readings=[]
   overrides={"one's":'wʌnz','oneself':'wʌnˈsɛlf','someone':'ˈsʌmwʌn',"someone's":'ˈsʌmwʌnz'}
   for word in english.split():
    reading=overrides.get(word) or ipa.convert(word)
    assert '*' not in reading,(english,word,reading)
    readings.append(reading)
   entry=dict(id='idiom-c-'+hashlib.sha256(english.encode()).hexdigest()[:12],kind='idiom',level=level,section=start+i//50,number=i%50+1,english=english,meaning=meaning,pos='熟語',pronunciation='/'+ ' '.join(readings)+'/',example=example,translation=translation,explanation=explanation,acceptedAnswers=[],content=dict(sourceIds=['original-idiom-batches-v1','cmudict-pronunciation'],contentVersion=1,qualityStatus='review_required',autoChecked=True,humanReviewed=False,productionApproved=False,examFrequency=None,selectionReason='高校入試向けの基礎的な重要表現。' if level==1 else '高校初級〜中級向けの頻出用法・句動詞・連語を独自選定。個別試験頻度は未実測。',pronunciationMethod='CMU-derived word-level IPA; phrase stress requires review',sourceUsage=[dict(sourceId='original-idiom-batches-v1',fields=['english','meaning','example','translation','explanation','proposedLevel']),dict(sourceId='cmudict-pronunciation',fields=['pronunciation'])]))
   errors=validate_entry(entry,source_map,seen_ids,False);assert not errors,(english,errors);batch.append(entry)
  path=ROOT/f'content/idioms/{file.stem}.json'
  if path.exists():assert read_json(path)==batch, 'Published idiom body changed: '+str(path)
  else:write_json(path,batch)
  results+=batch;summaries.append(dict(file=file.name,count=len(batch),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
 write_json(ROOT/'content/idioms/drafts.json',results)
 counts=[sum(e['level']==l for e in samples+results) for l in range(1,5)]
 summary=dict(updatedAt=NOW(),activeIdiomCounts=counts,newAuthoredIdioms=len(results),protectedSampleIdioms=len(samples),targetCurrentScope=[300,500],remainingCurrentScope=[300-counts[0],500-counts[1]],batches=summaries,humanReviewed=False)
 write_json(ROOT/'analysis/idiom_checkpoint.json',summary)
 write_json(ROOT/f'analysis/batches/idioms_{len(results):04}.json',summary)
 assert audit(ROOT)
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':build()
