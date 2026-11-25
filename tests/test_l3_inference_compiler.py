import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_l3_inference5 import compile_batch
class InferenceCompilerTests(unittest.TestCase):
 def test_saved_inference_batch_reproduces_exactly(self):
  root=Path(__file__).resolve().parents[1]
  self.assertEqual(compile_batch(),json.loads((root/'content/readings/l3_f06.json').read_text()))

 def test_saved_next_inference_batch_reproduces_exactly(self):
  root=Path(__file__).resolve().parents[1]
  self.assertEqual(compile_batch(True),json.loads((root/'content/readings/l3_f06_next5.json').read_text()))
