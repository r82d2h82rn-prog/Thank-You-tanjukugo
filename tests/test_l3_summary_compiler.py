import json,sys,unittest,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_l3_summary5 import compile_batch
from content_pipeline import validate_reading
ROOT=Path(__file__).resolve().parents[1]
class SummaryCompilerTests(unittest.TestCase):
 def test_original_annotations_reproduce_saved_summaries(self):
  batch=compile_batch()
  self.assertEqual(batch,json.loads((ROOT/'content/readings/l3_f09.json').read_text()))
  for p in batch:
   self.assertEqual(validate_reading(p),[])
   self.assertEqual(p['format'],9)
   self.assertEqual(len(p['questions'][0]['options']),4)
 def test_existing_readings_are_preserved_before_new_identities(self):
  old=json.loads(subprocess.check_output(['git','show','f816146:content/readings/advanced.json'],cwd=ROOT))
  current=json.loads((ROOT/'content/readings/advanced.json').read_text())
  self.assertEqual(current[:len(old)],old)
  self.assertGreaterEqual(len(current)-len(old),5)

 def test_later_summaries_reproduce_without_changing_first_batch(self):
  first=json.loads((ROOT/'content/readings/l3_f09.json').read_text())
  later=compile_batch(True)
  self.assertEqual(later,json.loads((ROOT/'content/readings/l3_f09_next5.json').read_text()))
  self.assertEqual(compile_batch(),first)
  self.assertFalse(set(p['id'] for p in first)&set(p['id'] for p in later))
  for p in later:self.assertEqual(validate_reading(p),[])
