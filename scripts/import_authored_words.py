#!/usr/bin/env python3
"""Import complete independently authored rows as unapproved drafts, preserving IDs."""
import argparse,csv,hashlib,json,pathlib
from content_pipeline import ROOT,NOW,normalized,read_json,write_json,read_csv,write_csv,validate_entry

def ingest(path,root=ROOT):
 sources=read_json(root/'content/sources.json');source_ids={s['id'] for s in sources}
 sid='original-draft-v4'
 if sid not in source_ids:
  template=next(s for s in sources if s['id']=='original-draft-v3').copy()
  template.update(id=sid,name='追加の高校・大学入試向け語彙草稿',notes='content/authoringの独自執筆バッチ。品詞・意味・発音・例文・和訳・用法を整備。件数は進捗JSONから計測。人手校閲・採否・最終LEVELは未確認。')
  sources.append(template)
 candidates=read_csv(root/'content/word_candidates.csv');by_lemma={r['lemma']:r for r in candidates}
 drafts=read_json(root/'content/words/drafts.json');samples=read_json(root/'src/data/entries.json')
 existing={normalized(e['english']):e for e in drafts+samples if e['kind']=='word'}
 source_map={s['id']:s for s in sources};new=[]
 positions={(e['level'],e['section'],e['number']):e['id'] for e in drafts}
 with path.open(encoding='utf-8',newline='') as file:
  for row in csv.DictReader(file,delimiter='\t'):
   lemma=normalized(row['english']);level=int(row['level']);section=int(row['section']);number=int(row['number'])
   official=sorted(set(json.loads(by_lemma.get(lemma,{}).get('source_ranks') or '{}'))&{'ngsl','nawl','tsl','bsl'})
   metadata=dict(sourceIds=[sid]+official,contentVersion=1,qualityStatus='review_required',autoChecked=True,humanReviewed=False,examFrequency=None,selectionReason=f'高校・大学入試につながる用法と学習上の価値を重視した独自選定。暫定LEVEL {level}。入試頻度は未検証。',productionApproved=False,sourceUsage=[dict(sourceId=s,fields=['english','candidateSelection']) for s in official]+[dict(sourceId=sid,fields=['meaning','pos','pronunciation','example','translation','explanation','proposedLevel'])])
   entry={k:row[k] for k in ['english','pos','pronunciation','meaning','example','translation','explanation']}
   entry.update(id='word-c-'+hashlib.sha256(lemma.encode()).hexdigest()[:12],level=level,section=section,number=number,kind='word',acceptedAnswers=[],content=metadata)
   if lemma in existing:
    old=existing[lemma]
    if all(old.get(k)==entry.get(k) for k in ['english','pos','pronunciation','meaning','example','translation','explanation','level','section','number']):continue
    raise ValueError('既存語の内容・IDを自動上書きしません: '+lemma)
   position=(level,section,number)
   if position in positions:raise ValueError('既存の教材番号を自動上書きしません: '+str(position))
   positions[position]=entry['id']
   errors=validate_entry(entry,source_map,set(),require_approval=False)
   if errors:raise ValueError((lemma,errors))
   existing[lemma]=entry;new.append(entry)
   if lemma not in by_lemma:
    r=dict(lemma=lemma,source_ranks='{}',status='要確認',proposed_level=str(level),level_basis='独自選定・指定リスト未掲載',exam_frequency='',adoption_reason=metadata['selectionReason'],provenance_source_ids=json.dumps([sid]));by_lemma[lemma]=r;candidates.append(r)
   r=by_lemma[lemma];r.update(status='採用候補' if official else '要確認',proposed_level=str(level),level_basis='独自選定・人手校閲待ち',adoption_reason=metadata['selectionReason'])
   r['provenance_source_ids']=json.dumps(sorted(set(json.loads(r['provenance_source_ids']))|{sid}))
 # Validation is complete before writing any catalog.
 write_json(root/'content/sources.json',sources)
 write_json(root/'content/words/drafts.json',sorted(drafts+new,key=lambda e:(e['level'],e['section'],e['number'])))
 write_csv(root/'content/word_candidates.csv',sorted(candidates,key=lambda r:r['lemma']),['lemma','source_ranks','status','proposed_level','level_basis','exam_frequency','adoption_reason','provenance_source_ids'])
 return {'added':len(new),'totalDrafts':len(drafts)+len(new)}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('path',type=pathlib.Path);a=p.parse_args();print(json.dumps(ingest(a.path),ensure_ascii=False))
