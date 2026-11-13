"""Compile manually authored 06–10 revisions at a specified level.

Legacy paragraphs/questions are immutable prefixes. All offsets are measured in
the actual version-2 paragraphs. This is an authored-data compiler, not a parser.
"""
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHOR = ROOT / 'content/authoring/reading-enrichment'


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def compile_batch(level):
    originals = [p for p in json.loads((ROOT / ('content/readings/drafts.json' if level == 2 else 'content/readings/advanced.json')).read_text()) if p['level'] == level][5:10]
    additions = json.loads((AUTHOR / f'l{level}-next5-additions.json').read_text())
    rows = iter(line.split('\t') for line in (AUTHOR / f'l{level}-next5.tsv').read_text().splitlines()
                if line and not line.startswith('#'))
    result = []
    for original, addition in zip(originals, additions):
        p = copy.deepcopy(original)
        p['content'].update(contentVersion=2, standardVersion=2,
                            selectionReason=f'既存の英文・設問IDを保護してLEVEL{level}の新版基準を適用。自然な論理展開を補い、全英文の和訳と構文を追加。人間の校閲は未実施。')
        p['previousSyntax'] = p['syntax']
        p['syntax'], p['sentences'] = [], []
        for en in addition['paragraphs']:
            jp = ''
            p['paragraphs'].append({'id': f"p{len(p['paragraphs']) + 1}", 'english': en, 'translation': jp})
        for para in p['paragraphs']:
            translations = []
            # All sentences in this batch are checked: no abbreviations/decimals.
            for i, m in enumerate(re.finditer(r'\S.*?(?:[.!?](?=\s|$)|$)', para['english'])):
                row = next(rows)
                assert len(row) in (3, 4), row
                jp, annotation, note = row[:3]
                sentence, sid, spans, used = m.group(), f"{para['id']}-s{i + 1:03}", [], {}
                for n, item in enumerate(annotation.split(';')):
                    label, text = item.split('=', 1)
                    role, _, kind = label.partition(':')
                    hits = [x.start() for x in re.finditer(r'(?<!\w)' + re.escape(text) + r'(?!\w)', sentence)]
                    kind, _, ordinal = kind.partition('@')
                    k = int(ordinal) - 1 if ordinal else used.get((role, text), 0)
                    assert len(hits) > k, (p['id'], sid, text, sentence)
                    start = m.start() + hits[k]
                    used[(role, text)] = k + 1
                    spans.append({'id': f'n{n + 1}', 'role': role, 'text': text,
                                  'start': start, 'end': start + len(text), **({'kind': kind} if kind else {})})
                for s in spans:
                    s['depth'] = sum(t['role'] in ('clause', 'phrase') and t['start'] <= s['start'] and
                                     t['end'] >= s['end'] and (t['start'], t['end']) != (s['start'], s['end'])
                                     for t in spans)
                relations = []
                for link in row[3].split(';') if len(row) == 4 else []:
                    source, target = link.split('=>')
                    a = next(s for s in spans if s['text'] == source)
                    b = next(s for s in spans if s['text'] == target)
                    relations.append({'from': a['id'], 'to': b['id'], 'type': 'modifies'})
                implicit = sentence.startswith(('Imagine ', 'Consider ' , 'Consider,', 'Suppose '))
                assert (implicit or any(s['role'] == 'S' for s in spans)) and any(s['role'] == 'V' for s in spans)
                syntax = {'id': f"{p['id']}:{sid}", 'passageId': p['id'], 'contentVersion': 2,
                          'paragraphId': para['id'], 'sentenceId': sid, 'sentence': sentence,
                          'start': m.start(), 'end': m.end(), 'translation': jp, 'explanation': note,
                          'spans': spans, 'relations': relations,
                          'skeleton': ('S: you（命令文で省略） / ' if implicit else '') + ' / '.join(s['role'] + ': ' + s['text'] for s in spans if s['role'] in ('S', 'V', 'O', 'C')),
                          'implicitSubject': 'you' if implicit else None, 'grammarPoints': [note], 'readingOrder': '主節のSとVを先に確認し、上の文法解説で従属節・修飾句・並列・否定の範囲をたどる。最後に全文訳と照合する。',
                          'reviewStatus': 'ai_author_checked_human_pending'}
                p['syntax'].append(syntax)
                p['sentences'].append({'id': sid, 'paragraphId': para['id'], 'english': sentence,
                                       'translation': jp, 'start': m.start(), 'end': m.end(), 'syntaxId': syntax['id']})
                translations.append(jp)
            para['translation'] = ''.join(translations)
        p['wordCount'] = len(re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*", ' '.join(x['english'] for x in p['paragraphs'])))
        p['recommendedSeconds'] = round(p['wordCount'] * 1.3 / 15) * 15
        p['difficulty'] = {'scores': dict(zip(['vocabulary','syntax','logic','questions'],{2:[2,2,2,2],3:[3,4,3,3],4:[4,5,5,4]}[level])),
                           'method': 'AI rubric: 1=高校入試、2=大学受験基礎、3=標準〜難関、4=難関、5=最難関',
                           'status': 'ai_assessed_human_pending',
                           'rationale': {2:'身近な事例を通じて因果・対比・基本的な条件を読む。関係節・間接疑問・比較を含む。',3:'抽象的な論旨と具体例の関係を追い、複雑な修飾・分詞構文・倒置・強調を読み分ける。',4:'多重修飾、複雑な譲歩・仮定・省略と否定の作用域を読み分け、暗黙の前提や複数段落にわたる含意を検討する。'}[level]}
        p['review'] = {'fullTranslation': 'ai_checked_human_pending', 'fullSyntax': 'ai_checked_human_pending',
                       'questionUniqueness': 'ai_checked_human_pending', 'englishNaturalness': 'ai_checked_human_pending'}
        result.append(p)
    assert next(rows, None) is None, 'Unused authored sentence rows'
    return originals, result
def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('level',type=int,choices=[2,3,4]);parser.add_argument('--base-commit',default='bbb5680a3b2403576a49eaa4c0674f169a65fc81');args=parser.parse_args()
    level=args.level;originals,batch=compile_batch(level)
    additions=json.loads((AUTHOR/f'l{level}-next5-additions.json').read_text())
    for i,(old,p,author) in enumerate(zip(originals,batch,additions)):
        for q in author['questions']:
            assert len(q['options'])==4 and 0<=q['correctIndex']<4
            shift=(i+len(p['questions']))%4;order=list(range(4))[shift:]+list(range(4))[:shift]
            p['questions'].append({'id':f"q{len(p['questions'])+1}",'prompt':q['prompt'],
             'options':[{'id':'abcd'[n],**q['options'][j]} for n,j in enumerate(order)],
             'correctOptionId':'abcd'[order.index(q['correctIndex'])],
             'explanation':q['options'][q['correctIndex']]['explanation'],
             'evidence':{'paragraphId':next(x['id'] for x in p['paragraphs'] if q['quote'] in x['english']),'quote':q['quote']}})
        assert p['questions'][:len(old['questions'])]==old['questions']
        assert [(x['id'],x['english']) for x in p['paragraphs'][:len(old['paragraphs'])]]==[(x['id'],x['english']) for x in old['paragraphs']]
        bounds={2:(250,400,4,7),3:(400,600,5,8),4:(600,900,6,10)}[level]
        assert bounds[0]<=p['wordCount']<=bounds[1] and bounds[2]<=len(p['questions'])<=bounds[3]
    output=ROOT/f'content/readings/enriched-level{level}-next5.json'
    if output.exists():assert json.loads(output.read_text())==batch,'Refuse to overwrite a different saved revision'
    output.write_text(json.dumps(batch,ensure_ascii=False,indent=2)+'\n')
    manifest={'batch':f'l{level}-next5-v2','baseCommit':args.base_commit,'humanReviewed':0,
      'passages':[{'id':p['id'],'words':p['wordCount'],'paragraphs':len(p['paragraphs']),'questions':len(p['questions']),
        'sentences':len(p['sentences']),'translationCoverage':1,'syntaxCoverage':1,'originalDigest':digest(old)} for old,p in zip(originals,batch)]}
    (ROOT/f'analysis/reading_l{level}_next5_batch.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest,ensure_ascii=False))

if __name__=='__main__':main()
