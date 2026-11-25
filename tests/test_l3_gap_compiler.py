import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from build_l3_gap10 import parse_sentence,compile_batch
class L3GapCompilerTests(unittest.TestCase):
 def test_explicit_annotations_keep_repeated_words_and_gap_offsets(self):
  text,nodes,edges,gaps=parse_sentence('<M to="v">Before the test</M>, <S>the test</S> <V>was</V> <C><g>provisional</g></C>.')
  self.assertEqual(text,'Before the test, the test was provisional.')
  self.assertEqual(text[slice(*gaps[0])],'provisional')
  for n in nodes:self.assertEqual(text[n['start']:n['end']],n['text'])
  self.assertEqual(nodes[0]['role'],'M');self.assertEqual(nodes[1]['text'],'the test')
  self.assertEqual(edges[0]['to'],next(n['id'] for n in nodes if n['role']=='V'))
 def test_missing_authored_structure_is_rejected_not_guessed(self):
  with self.assertRaises(AssertionError):parse_sentence('Birds fly.')
  with self.assertRaises(AssertionError):parse_sentence('<S>Birds</S> fly.')
  with self.assertRaises(AssertionError):parse_sentence('<S>Birds</S> <V>fly</V>. Another sentence.')
 def test_ten_passages_reproduce_saved_original_batch(self):
  import json
  root=pathlib.Path(__file__).resolve().parents[1]
  self.assertEqual(compile_batch(),json.loads((root/'content/readings/l3_f02.json').read_text()))

 def test_sentence_gap_batch_reproduces_with_all_sentences_covered(self):
  import json
  root=pathlib.Path(__file__).resolve().parents[1]
  batch=compile_batch(3)
  self.assertEqual(batch,json.loads((root/'content/readings/l3_f03.json').read_text()))
  self.assertEqual(sum(len(p['sentences']) for p in batch),253)
  self.assertEqual(sum(len(p['questions']) for p in batch),66)
 def test_unrelated_format_is_rejected(self):
  with self.assertRaises(AssertionError):compile_batch(4)
