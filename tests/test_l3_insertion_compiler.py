import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_l3_insertion5 import compile_batch,apply_insertion
from content_pipeline import validate_reading
ROOT=Path(__file__).resolve().parents[1]
class InsertionCompilerTests(unittest.TestCase):
 def test_saved_insertion_batch_reproduces_exactly(self):
  self.assertEqual(compile_batch(),json.loads((ROOT/'content/readings/l3_f07.json').read_text()))
 def test_duplicate_or_out_of_order_positions_are_rejected(self):
  batch=compile_batch();config=json.loads((ROOT/'content/authoring/readings/l3-f07-insertions.json').read_text())[0]
  for positions in [[config['positions'][0]]*4,list(reversed(config['positions']))]:
   bad=copy.deepcopy(config);bad['positions']=positions
   with self.assertRaises(AssertionError):apply_insertion(copy.deepcopy(batch[0]),bad)
 def test_wrong_solution_cannot_validate_against_original_review(self):
  for p in compile_batch():
   for marker in ['[A]','[B]','[C]','[D]']:
    if marker==p['insertionSolution']['marker']:continue
    bad=copy.deepcopy(p);bad['insertionSolution']['marker']=marker
    self.assertIn('review completion differs from original and solutions',validate_reading(bad))
