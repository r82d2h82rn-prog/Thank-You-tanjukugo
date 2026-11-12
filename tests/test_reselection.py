import collections,hashlib,json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from word_catalog import authored_catalog
from content_pipeline import validate_entry

class ReselectionTests(unittest.TestCase):
 def test_overlay_preserves_every_source_and_completes_level3(self):
  old=json.loads((ROOT/'content/words/drafts.json').read_text());new=json.loads((ROOT/'content/words/reselected_additions.json').read_text());selection=json.loads((ROOT/'content/words/selection.json').read_text());active=authored_catalog(ROOT)
  for name in selection.get('additionalBatchFiles',[]):new+=json.loads((ROOT/name).read_text())
  sources={e['id']:e for e in old+new}
  self.assertEqual(len(sources),len(old)+len(new))
  self.assertEqual(set(sources),{e['id'] for e in active}|{e['id'] for e in old if e['level']>=3 and e['id'] not in {a['id'] for a in active}})
  self.assertEqual(len({e['english'] for e in active}),len(active))
  self.assertEqual(sum(e['level']==3 for e in active),1200)
  self.assertEqual(sum(e['level']==1 for e in active),800)
  self.assertEqual(sum(e['level']==2 for e in active),900)
  advanced=sum(e['level']==4 for e in new)
  self.assertEqual(sum(e['level']==4 for e in active),100+advanced)
  permissions={s['id']:s for s in json.loads((ROOT/'content/sources.json').read_text())};seen=set()
  for e in active:
   self.assertEqual(validate_entry(e,permissions,seen,False),[])
   self.assertEqual({k:v for k,v in e.items() if k not in ['level','section','number']},{k:v for k,v in sources[e['id']].items() if k not in ['level','section','number']})
  order={'動詞':0,'名詞':1,'形容詞':2,'副詞':3,'その他':4}
  for level,section in {(e['level'],e['section']) for e in active}:
   rows=sorted([e for e in active if e['level']==level and e['section']==section],key=lambda e:e['number'])
   self.assertEqual([e['number'] for e in rows],list(range(1,101)))
   self.assertEqual([order.get(e['pos'],4) for e in rows],sorted(order.get(e['pos'],4) for e in rows))
  summary=json.loads((ROOT/'analysis/reselection_summary.json').read_text())
  self.assertEqual(hashlib.sha256((ROOT/'content/words/drafts.json').read_bytes()).hexdigest(),summary['legacyArchiveSha256'])
