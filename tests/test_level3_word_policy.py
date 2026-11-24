import json
import pathlib
import statistics
import sys
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from level3_word_policy import POLICY, level3_word_plan, validate_level3_word_count


class Level3WordPolicyTests(unittest.TestCase):
    def test_each_remaining_format_restarts_at_401_and_ends_at_600(self):
        expected=[(401,420),(421,440),(441,460),(461,480),(481,500),
                  (501,520),(521,540),(541,560),(561,580),(580,600)]
        for form in range(2,11):
            for item, bounds in enumerate(expected,1):
                p=level3_word_plan(form,item)
                self.assertEqual((p['min'],p['max']),bounds)
                validate_level3_word_count(form,item,p['target'])
        self.assertEqual(level3_word_plan(10,1)['max'],420)
        self.assertEqual(level3_word_plan(2,10)['min'],580)

    def test_targets_cover_low_middle_and_high_in_each_band_across_formats(self):
        for item in range(1,11):
            plans=[level3_word_plan(f,item) for f in range(2,11)]
            counts=[p['target'] for p in plans]
            lo,hi=plans[0]['min'],plans[0]['max']
            self.assertEqual(len(set(counts)),9)
            self.assertEqual(min(counts),lo)
            self.assertEqual(max(counts),hi)
            self.assertLessEqual(abs(statistics.mean(counts)-(lo+hi)/2),0.5)

    def test_underlength_and_lower_bound_clustering_are_rejected(self):
        for form in range(2,11):
            for item in range(1,11):
                p=level3_word_plan(form,item)
                for bad in [p['min']-1,p['max']+1]:
                    with self.assertRaises(ValueError):validate_level3_word_count(form,item,bad)
        rejected=0
        for form in range(2,11):
            p=level3_word_plan(form,1)
            try:validate_level3_word_count(form,1,p['min'])
            except ValueError:rejected+=1
        self.assertGreaterEqual(rejected,6)
        with self.assertRaises(ValueError):level3_word_plan(11,1)
        with self.assertRaises(ValueError):level3_word_plan(2,0)

    def test_existing_first_ten_are_exempt_from_new_targets(self):
        root=pathlib.Path(__file__).resolve().parents[1]
        passages=[]
        for name in ['enriched-level3.json','enriched-level3-next5.json']:
            passages+=json.loads((root/'content/readings'/name).read_text())
        self.assertEqual(len(passages),10)
        for item,p in enumerate(passages,1):
            self.assertIsNone(validate_level3_word_count(1,item,p.get('reviewWordCount',p['wordCount']))['target'])
        self.assertEqual(POLICY['preservedFormats'],[1])

if __name__=='__main__':unittest.main()
