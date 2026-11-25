import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_l3_ordering5 import compile_batch
from content_pipeline import validate_reading
ROOT=Path(__file__).resolve().parents[1]
class OrderingCompilerTests(unittest.TestCase):
 def test_explicit_sources_reproduce_saved_ordering_batch(self):
  batch=compile_batch()
  self.assertEqual(batch,json.loads((ROOT/'content/readings/l3_f08.json').read_text()))
  for p in batch:
   self.assertEqual(validate_reading(p),[])
   self.assertEqual(sorted(p['paragraphOrder']),[para['id'] for para in p['paragraphs']])
 def test_previous_readings_preserved_by_append(self):
  import subprocess
  prior=json.loads(subprocess.check_output(['git','show','76a28f9:content/readings/advanced.json'],cwd=ROOT))
  current=json.loads((ROOT/'content/readings/advanced.json').read_text())
  self.assertEqual(current[:len(prior)],prior)
  self.assertEqual(len(current)-len(prior),10)
