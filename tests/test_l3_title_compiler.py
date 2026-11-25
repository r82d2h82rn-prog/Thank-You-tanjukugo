import json,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from build_l3_title10 import compile_batch
class L3TitleCompilerTests(unittest.TestCase):
 def test_authored_title_batch_is_reproducible(self):
  root=pathlib.Path(__file__).resolve().parents[1]
  batch=compile_batch()
  self.assertEqual(batch,json.loads((root/'content/readings/l3_f04.json').read_text()))
  self.assertEqual(sum(len(p['sentences']) for p in batch),280)
  self.assertEqual(sum(len(p['questions']) for p in batch),65)
  for p in batch:
   self.assertNotIn('gapSolutions',p)
   self.assertEqual(p['questions'][0]['prompt'],'本文全体に最も適した英語の題名はどれか。')
