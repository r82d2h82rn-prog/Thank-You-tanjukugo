"""Compile authored Level 2 items 11–15; keep question and review text separate."""
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHOR = ROOT / 'content/authoring/reading-enrichment'


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def compile_batch():
    originals = [p for p in json.loads((ROOT / 'content/readings/drafts.json').read_text()) if p['level'] == 2][10:15]
    additions = json.loads((AUTHOR / 'l2-gap5-additions.json').read_text())
    rows = iter(line.split('\t') for line in (AUTHOR / 'l2-gap5.tsv').read_text().splitlines() if line and not line.startswith('#'))
    result = []
    for old, extra in zip(originals, additions, strict=True):
        assert old['id'] == extra['id']
        p = copy.deepcopy(old)
        p['content'].update(contentVersion=2, standardVersion=2,
            selectionReason='既存英文・設問IDを保護し、自然な続きと新設問を補完。全英文を文別和訳・構文に対応付け。人間の正式校閲は未実施。')
        p['previousSyntax'] = p['syntax']
        p['syntax'], p['sentences'] = [], []
        for english in extra['paragraphs']:
            p['paragraphs'].append({'id': f"p{len(p['paragraphs']) + 1}", 'english': english, 'translation': ''})
        answer = next(o['text'] for o in old['questions'][0]['options'] if o['id'] == old['questions'][0]['correctOptionId'])
        assert sum(x['english'].count('[1]') for x in p['paragraphs']) == 1
        p['gapSolutions'] = {'[1]': {'questionId': 'q1', 'answer': answer}}
        p['reviewParagraphs'] = copy.deepcopy(p['paragraphs'])
        p['syntaxOffsetBasis'] = 'reviewParagraphs'
        for source, para in zip(p['paragraphs'], p['reviewParagraphs'], strict=True):
            para['english'] = source['english'].replace('[1]', answer)
            pattern = r'\S.*?(?:[.!?](?=\s|$)|$)'
            sources, matches = list(re.finditer(pattern, source['english'])), list(re.finditer(pattern, para['english']))
            translations = []
            for i, (sm, m) in enumerate(zip(sources, matches, strict=True)):
                row = next(rows)
                assert len(row) in (3, 4), row
                jp, annotation, note = row[:3]
                en, sid, spans, used = m.group(), f"{para['id']}-s{i+1:03}", [], {}
                for n, item in enumerate(annotation.split(';')):
                    label, text = item.split('=', 1)
                    role, _, kind = label.partition(':')
                    kind, _, ordinal = kind.partition('@')
                    hits = [x.start() for x in re.finditer(r'(?<!\w)' + re.escape(text) + r'(?!\w)', en)]
                    k = int(ordinal)-1 if ordinal else used.get((role, text), 0)
                    assert len(hits) > k, (p['id'], sid, text, en)
                    start = m.start() + hits[k]
                    used[(role, text)] = k+1
                    spans.append({'id': f'n{n+1}', 'role': role, 'text': text, 'start': start,
                                  'end': start+len(text), **({'kind': kind} if kind else {})})
                for s in spans:
                    s['depth'] = sum(t['role'] in ('clause', 'phrase') and t['start'] <= s['start'] and t['end'] >= s['end']
                        and (t['start'], t['end']) != (s['start'], s['end']) for t in spans)
                relations = []
                for link in row[3].split(';') if len(row) == 4 else []:
                    a, b = link.split('=>')
                    relations.append({'from': next(s['id'] for s in spans if s['text'] == a),
                                      'to': next(s['id'] for s in spans if s['text'] == b), 'type': 'modifies'})
                assert any(s['role'] == 'S' for s in spans) and any(s['role'] == 'V' for s in spans)
                previous = [s['explanation'] for s in old['syntax'] if s['sentence'] == sm.group()]
                explanation = note + (' 既存解説：' + ' '.join(previous) if previous else '')
                syntax = {'id': f"{p['id']}:{sid}", 'passageId': p['id'], 'contentVersion': 2,
                    'paragraphId': para['id'], 'sentenceId': sid, 'sentence': en, 'start': m.start(), 'end': m.end(),
                    'translation': jp, 'explanation': explanation, 'spans': spans, 'relations': relations,
                    'skeleton': ' / '.join(s['role']+': '+s['text'] for s in spans if s['role'] in ('S','V','O','C')),
                    'grammarPoints': [note], 'readingOrder': '主節のSとVを先に押さえ、解説に沿って句節の働きと修飾先、対比・否定の範囲を確認し、全文訳と照合する。',
                    'reviewStatus': 'ai_author_checked_human_pending', 'offsetBasis': 'reviewParagraphs'}
                p['syntax'].append(syntax)
                p['sentences'].append({'id': sid, 'paragraphId': para['id'], 'english': en, 'translation': jp,
                    'start': m.start(), 'end': m.end(), 'sourceEnglish': sm.group(), 'sourceStart': sm.start(),
                    'sourceEnd': sm.end(), 'syntaxId': syntax['id']})
                translations.append(jp)
            source['translation'] = para['translation'] = ''.join(translations)
        for q in extra['questions']:
            assert len(q['options']) == 4 and 0 <= q['correctIndex'] < 4
            order = list(range(4)); shift = (len(result)+len(p['questions'])) % 4
            order = order[shift:]+order[:shift]
            p['questions'].append({'id': f"q{len(p['questions'])+1}", 'prompt': q['prompt'],
                'options': [{'id': 'abcd'[n], **q['options'][j]} for n,j in enumerate(order)],
                'correctOptionId': 'abcd'[order.index(q['correctIndex'])],
                'explanation': q['options'][q['correctIndex']]['explanation'],
                'evidence': {'paragraphId': next(x['id'] for x in p['paragraphs'] if q['quote'] in x['english']), 'quote': q['quote']}})
        words = lambda paras: len(re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*", ' '.join(x['english'] for x in paras)))
        p['wordCount'], p['reviewWordCount'] = words(p['paragraphs']), words(p['reviewParagraphs'])
        p['recommendedSeconds'] = round(p['reviewWordCount']*1.3/15)*15
        p['difficulty'] = {'scores': {'vocabulary':2,'syntax':2,'logic':2,'questions':2},
            'method':'AI rubric: 1=高校入試、2=大学受験基礎、3=標準〜難関、4=難関、5=最難関',
            'status':'ai_assessed_human_pending', 'rationale': extra['rationale']}
        p['review'] = {k:'ai_checked_human_pending' for k in ('fullTranslation','fullSyntax','questionUniqueness','englishNaturalness')}
        assert p['questions'][:len(old['questions'])] == old['questions']
        assert [(x['id'],x['english']) for x in p['paragraphs'][:len(old['paragraphs'])]] == [(x['id'],x['english']) for x in old['paragraphs']]
        assert 250 <= p['reviewWordCount'] <= 400 and 4 <= len(p['questions']) <= 7
        result.append(p)
    assert next(rows, None) is None, 'Unused annotation rows'
    return originals, result


if __name__ == '__main__':
    originals, batch = compile_batch()
    path = ROOT / 'content/readings/enriched-level2-gap5.json'
    if path.exists():
        assert json.loads(path.read_text()) == batch, 'Refuse a different saved revision'
    path.write_text(json.dumps(batch, ensure_ascii=False, indent=2)+'\n')
    manifest = {'batch':'l2-items11-15-v2', 'baseCommit':'d4b18c1841488dbd596aacd2d9dc27d011cc0c56', 'humanReviewed':0,
        'passages':[{'id':p['id'],'words':p['wordCount'],'reviewWords':p['reviewWordCount'],
            'paragraphs':len(p['paragraphs']),'questions':len(p['questions']),'sentences':len(p['sentences']),
            'translationCoverage':1,'syntaxCoverage':1,'originalDigest':digest(old)} for old,p in zip(originals,batch)]}
    (ROOT / 'analysis/reading_l2_gap5_batch.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest,ensure_ascii=False))
