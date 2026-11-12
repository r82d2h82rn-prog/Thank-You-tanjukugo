#!/usr/bin/env python3
"""Record a validated 100-word authoring boundary, without changing old materials."""
import collections, hashlib, json
from content_pipeline import ROOT,NOW,write_json,read_json
from reselect_words import read_new
new=read_new(); counts=dict(collections.Counter(e['level'] for e in new));n=len(new)
write_json(ROOT/f'analysis/batches/reselection_{n:04}.json',dict(checkedAt=NOW(),cumulativeNewWords=n,newByLevel=counts,legacyDrafts=2600,legacySha256=hashlib.sha256((ROOT/'content/words/drafts.json').read_bytes()).hexdigest(),checks=['complete batches of 100','nonempty meaning/IPA/example/translation/explanation','unique headwords and IDs against legacy/sample/all new batches','valid provenance; no editorial approval granted'],humanReviewed=False))
print(json.dumps({'validatedNewWords':n,'newByLevel':counts},ensure_ascii=False))
