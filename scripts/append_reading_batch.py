#!/usr/bin/env python3
"""Append original, explicitly authored reading records from a compact JSON batch."""
import json,re,sys
from pathlib import Path
level,form=map(int,sys.argv[1:3]);path=Path(f'content/authoring/readings/l{level}_f{form:02}.jsonl')
records=[]
batch=json.load(sys.stdin);pending=Path('analysis/reading_authoring_pending.json');pending.write_text(json.dumps(batch,ensure_ascii=False))
for title,en,jp,qs,syn,vocab,*extra in batch:
 paras=list(map(list,zip(en.split('||'),jp.split('||'))));assert len(en.split('||'))==len(jp.split('||'))
 ext=extra[0].copy() if extra else {}
 if 'shuffle' in ext:
  order=ext.pop('shuffle');paras=[paras[n-1] for n in order];ext['paragraphOrder']=[order.index(n)+1 for n in range(1,len(order)+1)]
 questions=[]
 for prompt,options,reasons,quote in qs:
  opts=options.split('|');why=reasons.split('|');assert len(opts)==len(why)==4
  questions.append([prompt,opts,why,[next(i+1 for i,p in enumerate(paras) if quote in p[0]),quote]])
 sentence,parts,translation,explanation=syn
 if not any(sentence in p[0] for p in paras) and any(sentence.rstrip('.') in p[0] for p in paras):sentence=sentence.rstrip('.')
 if not any(sentence in p[0] for p in paras):
  matches=[p[0] for p in paras if p[0].casefold().count(sentence.casefold())==1];assert len(matches)==1,(title,sentence)
  start=matches[0].casefold().index(sentence.casefold());sentence=matches[0][start:start+len(sentence)]
 for part in parts:
  if part[1] not in sentence and sentence.casefold().count(part[1].casefold())==1:
   start=sentence.casefold().index(part[1].casefold());part[1]=sentence[start:start+len(part[1])]
 record=dict(title=title,paragraphs=paras,questions=questions,syntax=[next(i+1 for i,p in enumerate(paras) if sentence in p[0]),sentence,parts,translation,explanation],vocabulary=vocab,**ext)
 count=len(re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*",en));assert 160<=count<=320,(title,count)
 records.append(record)
 print(title,count)
old=path.read_text() if path.exists() else ''
assert len(old.splitlines())+len(records)<=10
path.write_text(old+''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))

pending.unlink()
