"""Word bands by item WITHIN each Level 3 format, not global item number."""
import json
from pathlib import Path

POLICY = json.loads((Path(__file__).resolve().parents[1] / 'content/authoring/readings/level3-word-policy.json').read_text())


def level3_word_plan(form, item):
    if type(form) is not int or type(item) is not int or not (1 <= form <= 10 and 1 <= item <= 10):
        raise ValueError('LEVEL3の形式・形式内番号は1〜10の整数で指定する')
    if form in POLICY['preservedFormats']:
        return {'min': 400, 'max': 600, 'target': None}
    band = POLICY['bandsByItemWithinFormat'][item - 1]
    return {**{k: band[k] for k in ('min', 'max')}, 'target': POLICY['targetsByFormat'][str(form)][item - 1]}


def validate_level3_word_count(form, item, completed_word_count):
    """The caller counts the answer-completed English, including inserted text once."""
    plan = level3_word_plan(form, item)
    if type(completed_word_count) is not int or not plan['min'] <= completed_word_count <= plan['max']:
        raise ValueError(f"LEVEL3 形式{form}・{item}題目: 完成語数{completed_word_count}は{plan['min']}〜{plan['max']}語の範囲外")
    if plan['target'] is not None and abs(completed_word_count - plan['target']) > POLICY['targetTolerance']:
        raise ValueError(f"LEVEL3 形式{form}・{item}題目: 下限偏重防止の制作目標は{plan['target']}語（±{POLICY['targetTolerance']}語、指定帯内）")
    return plan
