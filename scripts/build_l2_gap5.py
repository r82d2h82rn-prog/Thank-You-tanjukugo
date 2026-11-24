"""Compile authored Level 2 gap batches; keep question and review text separate."""
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHOR = ROOT / 'content/authoring/reading-enrichment'


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def sentence_matches(text):
    matches = list(re.finditer(r'\S.*?(?:[.!?](?=\s|$)|$)', text))
    result, i = [], 0
    while i < len(matches):
        m = matches[i]
        if (i + 1 < len(matches)
                and re.search(r'\bfrom\s+(?:Which|What|Who|Where|When|Why|How)\b[^.!?]*\?$', m.group())
                and re.match(r'to\s+(?:Which|What|Who|Where|When|Why|How)\b', matches[i+1].group())):
            m = re.compile(r'\S[\s\S]*').match(text, m.start(), matches[i+1].end())
            i += 1
        result.append(m)
        i += 1
    return result


def insertion_review(text, marker, sentence):
    """Remove location labels in review; map each review character to source."""
    output, mapping, cursor = [], [], 0
    for token in re.finditer(r'\[[A-D]\]', text):
        output.append(text[cursor:token.start()])
        mapping.extend((i, i+1, 'text') for i in range(cursor, token.start()))
        if token.group() == marker:
            output.append(sentence)
            mapping.extend((token.start(), token.end(), 'insertion') for _ in sentence)
        cursor = token.end()
    output.append(text[cursor:])
    mapping.extend((i, i+1, 'text') for i in range(cursor, len(text)))
    return ''.join(output), mapping


def compile_batch(start=10, end=15, stem='l2-gap5'):
    originals = [p for p in json.loads((ROOT / 'content/readings/drafts.json').read_text()) if p['level'] == 2][start:end]
    additions = json.loads((AUTHOR / f'{stem}-additions.json').read_text())
    rows = iter(line.split('\t') for line in (AUTHOR / f'{stem}.tsv').read_text().splitlines() if line and not line.startswith('#'))
    result = []
    first_item_number = start + 1
    for old, extra in zip(originals, additions, strict=True):
        assert old['id'] == extra['id']
        p = copy.deepcopy(old)
        p['content'].update(contentVersion=2, standardVersion=2,
            selectionReason='既存英文・設問IDを保護し、自然な続きと新設問を補完。全英文を文別和訳・構文に対応付け。人間の正式校閲は未実施。')
        p['previousSyntax'] = p['syntax']
        p['syntax'], p['sentences'] = [], []
        for english in extra['paragraphs']:
            p['paragraphs'].append({'id': f"p{len(p['paragraphs']) + 1}", 'english': english, 'translation': ''})
        if p['format'] == 8:
            assert len(old['paragraphs']) == 4 and len(old['paragraphOrder']) == 4
            assert set(old['paragraphOrder']) == {x['id'] for x in old['paragraphs']}
            p['continuationParagraphIds'] = [x['id'] for x in p['paragraphs'][len(old['paragraphs']):]]
        answer = next(o['text'] for o in old['questions'][0]['options'] if o['id'] == old['questions'][0]['correctOptionId'])
        has_gap = p['format'] in (2, 3)
        has_insert = p['format'] == 7
        assert sum(x['english'].count('[1]') for x in p['paragraphs']) == int(has_gap)
        if has_gap:
            p['gapSolutions'] = {'[1]': {'questionId': 'q1', 'answer': answer}}
            p['reviewParagraphs'] = copy.deepcopy(p['paragraphs'])
        if has_insert:
            assert re.fullmatch(r'\[[A-D]\]', answer)
            assert sorted(re.findall(r'\[[A-D]\]', ' '.join(x['english'] for x in p['paragraphs']))) == ['[A]', '[B]', '[C]', '[D]']
            p['reviewParagraphs'] = copy.deepcopy(p['paragraphs'])
            p['insertionSolution'] = {'questionId': 'q1', 'marker': answer, 'sentence': p['insert']['sentence'],
                'paragraphId': next(x['id'] for x in p['paragraphs'] if answer in x['english'])}
        review_paragraphs = p['reviewParagraphs'] if has_gap or has_insert else p['paragraphs']
        p['syntaxOffsetBasis'] = 'reviewParagraphs' if has_gap or has_insert else 'paragraphs'
        for source, para in zip(p['paragraphs'], review_paragraphs, strict=True):
            if has_insert:
                para['english'], insertion_map = insertion_review(source['english'], answer, p['insert']['sentence'])
            else:
                para['english'] = source['english'].replace('[1]', answer)
            sources, matches = sentence_matches(source['english']), sentence_matches(para['english'])
            translations = []
            sentence_gap = p['format'] == 3
            if not sentence_gap and not has_insert:
                assert len(sources) == len(matches)
            gap_start = source['english'].find('[1]')
            gap_end = gap_start + len(answer)
            delta = len(answer) - 3
            for i, m in enumerate(matches):
                if has_insert:
                    mapped = insertion_map[m.start():m.end()]
                    assert len({x[2] for x in mapped}) == 1, (p['id'], m.group())
                    source_kind = mapped[0][2]
                    source_start, source_end = mapped[0][0], mapped[-1][1]
                    source_english = source['english'][source_start:source_end]
                    source_index = next(j for j, sm in enumerate(sources) if sm.start() <= source_start and sm.end() >= source_end)
                    assert (source_kind == 'insertion' and source_english == answer and m.group() == p['insert']['sentence']) or (source_kind == 'text' and source_english == m.group())
                elif sentence_gap:
                    def source_offset(position, is_end=False):
                        if gap_start < 0 or position <= gap_start:
                            return position
                        if position >= gap_end:
                            return position - delta
                        return gap_start + (3 if is_end else 0)
                    source_start = source_offset(m.start())
                    source_end = source_offset(m.end(), True)
                    source_english = source['english'][source_start:source_end]
                    source_index = next(j for j, sm in enumerate(sources) if sm.start() <= source_start and sm.end() >= source_end)
                else:
                    sm = sources[i]
                    source_start, source_end, source_english = sm.start(), sm.end(), sm.group()
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
                previous = [s['explanation'] for s in old['syntax'] if s['sentence'] == source_english]
                explanation = note + (' 既存解説：' + ' '.join(previous) if previous else '')
                syntax = {'id': f"{p['id']}:{sid}", 'passageId': p['id'], 'contentVersion': 2,
                    'paragraphId': para['id'], 'sentenceId': sid, 'sentence': en, 'start': m.start(), 'end': m.end(),
                    'translation': jp, 'explanation': explanation, 'spans': spans, 'relations': relations,
                    'skeleton': ' / '.join(s['role']+': '+s['text'] for s in spans if s['role'] in ('S','V','O','C')),
                    'grammarPoints': [note], 'readingOrder': '主節のSとVを先に押さえ、解説に沿って句節の働きと修飾先、対比・否定の範囲を確認し、全文訳と照合する。',
                    'reviewStatus': 'ai_author_checked_human_pending', 'offsetBasis': p['syntaxOffsetBasis']}
                p['syntax'].append(syntax)
                p['sentences'].append({'id': sid, 'paragraphId': para['id'], 'english': en, 'translation': jp,
                    'start': m.start(), 'end': m.end(), 'sourceEnglish': source_english, 'sourceStart': source_start,
                    'sourceEnd': source_end, 'syntaxId': syntax['id'],
                    **({'sourceSentenceId': f"{source['id']}-s{source_index+1:03}",
                        'sourceKind': source_kind if has_insert else 'gap' if source_english == '[1]' else 'text'} if sentence_gap or has_insert else {})})
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
        words = lambda paras: len(re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*", re.sub(r'\[[A-D]\]', '', ' '.join(x['english'] for x in paras)) if has_insert else ' '.join(x['english'] for x in paras)))
        p['wordCount'], p['reviewWordCount'] = words(p['paragraphs']), words(review_paragraphs)
        p['recommendedSeconds'] = round(p['reviewWordCount']*1.3/15)*15
        p['difficulty'] = {'scores': {'vocabulary':2,'syntax':2,'logic':2,'questions':2},
            'method':'AI rubric: 1=高校入試、2=大学受験基礎、3=標準〜難関、4=難関、5=最難関',
            'status':'ai_assessed_human_pending', 'rationale': extra['rationale']}
        p['review'] = {k:'ai_checked_human_pending' for k in ('fullTranslation','fullSyntax','questionUniqueness','englishNaturalness')}
        assert p['questions'][:len(old['questions'])] == old['questions']
        assert [(x['id'],x['english']) for x in p['paragraphs'][:len(old['paragraphs'])]] == [(x['id'],x['english']) for x in old['paragraphs']]
        # User correction: items 51–75 are 300–350 words; 76–100 are 350–400.
        index = first_item_number + len(result)
        minimum, maximum = (350, 400) if index >= 76 else (300, 350) if index >= 51 else (250, 400)
        assert minimum <= p['reviewWordCount'] <= maximum, (p['id'], p['reviewWordCount'], minimum, maximum)
        assert 4 <= len(p['questions']) <= 7
        result.append(p)
    assert next(rows, None) is None, 'Unused annotation rows'
    return originals, result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', choices=['11-15', '16-20', '21-25', '26-30', '31-35', '36-40', '41-45', '46-50', '51-55', '56-60', '61-65', '66-70', '71-75', '76-80', '81-85'], default='11-15')
    args = parser.parse_args()
    start, end, stem, output, base = {
        '11-15': (10, 15, 'l2-gap5', 'enriched-level2-gap5', 'd4b18c1841488dbd596aacd2d9dc27d011cc0c56'),
        '16-20': (15, 20, 'l2-gap-next5', 'enriched-level2-gap-next5', 'f3a873d311f3153493f2b34fd984d0a18c862694'),
        '21-25': (20, 25, 'l2-sentence-gap5', 'enriched-level2-sentence-gap5', '1d69f03c4b842a8e94eda305a22ab6a3625667ec'),
        '26-30': (25, 30, 'l2-sentence-gap-next5', 'enriched-level2-sentence-gap-next5', '115332f356a14e255836a7165549c42c68de95c7'),
        '31-35': (30, 35, 'l2-title5', 'enriched-level2-title5', '784acd951bd9bcd06c9837574b9ac5fcc8dac4e5'),
        '36-40': (35, 40, 'l2-title-next5', 'enriched-level2-title-next5', '784acd951bd9bcd06c9837574b9ac5fcc8dac4e5'),
        '41-45': (40, 45, 'l2-reference5', 'enriched-level2-reference5', 'bc846e59a2faca7ad628b509bd24b1b534a6c91e'),
        '46-50': (45, 50, 'l2-reference-next5', 'enriched-level2-reference-next5', 'e32d3e594ac9e0a380bbc27408b89837072de223'),
        '51-55': (50, 55, 'l2-inference5', 'enriched-level2-inference5', 'e32d3e594ac9e0a380bbc27408b89837072de223'),
        '56-60': (55, 60, 'l2-inference-next5', 'enriched-level2-inference-next5', '42db8c36d5dfff02f23d5d1b228e47fa6a44387c'),
        '61-65': (60, 65, 'l2-insert5', 'enriched-level2-insert5', '11b6fed889ecda96f4b3ab7207e4ae344616c879'),
        '66-70': (65, 70, 'l2-insert-next5', 'enriched-level2-insert-next5', '0ecafd3efb652b7421a8e0564ea222db2b1fa34f'),
        '71-75': (70, 75, 'l2-order5', 'enriched-level2-order5', 'f64ccc42952be213124f7967a05d9be08a30d27a'),
        '76-80': (75, 80, 'l2-order-next5', 'enriched-level2-order-next5', 'a629f13d5da8715fc88f7e2c6edad85d347ff823'),
        '81-85': (80, 85, 'l2-summary5', 'enriched-level2-summary5', 'e66747c5e830055f2617371b8a957a8d1974d958'),
    }[args.batch]
    originals, batch = compile_batch(start, end, stem)
    path = ROOT / f'content/readings/{output}.json'
    if path.exists():
        assert json.loads(path.read_text()) == batch, 'Refuse a different saved revision'
    path.write_text(json.dumps(batch, ensure_ascii=False, indent=2)+'\n')
    manifest = {'batch':f'l2-items{args.batch}-v2', 'baseCommit':base, 'humanReviewed':0,
        'passages':[{'id':p['id'],'words':p['wordCount'],'reviewWords':p['reviewWordCount'],
            'paragraphs':len(p['paragraphs']),'questions':len(p['questions']),'sentences':len(p['sentences']),
            'translationCoverage':1,'syntaxCoverage':1,'originalDigest':digest(old)} for old,p in zip(originals,batch)]}
    manifest_name = {'11-15': 'reading_l2_gap5_batch', '16-20': 'reading_l2_gap_next5_batch',
                     '21-25': 'reading_l2_sentence_gap5_batch', '26-30': 'reading_l2_sentence_gap_next5_batch',
                     '31-35': 'reading_l2_title5_batch', '36-40': 'reading_l2_title_next5_batch', '41-45': 'reading_l2_reference5_batch', '46-50': 'reading_l2_reference_next5_batch', '51-55': 'reading_l2_inference5_batch', '56-60': 'reading_l2_inference_next5_batch', '61-65': 'reading_l2_insert5_batch', '66-70': 'reading_l2_insert_next5_batch', '71-75': 'reading_l2_order5_batch', '76-80': 'reading_l2_order_next5_batch', '81-85': 'reading_l2_summary5_batch'}[args.batch]
    (ROOT / f'analysis/{manifest_name}.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest,ensure_ascii=False))
