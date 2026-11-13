"""Build only L2/format1/01–05 from authored additions and sentence annotations.

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
BASE = ROOT / 'content/readings/drafts.json'
OUTPUT = ROOT / 'content/readings/enriched.json'


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def compile_batch():
    originals = [p for p in json.loads(BASE.read_text()) if p['level'] == 2][:5]
    additions = json.loads((AUTHOR / 'l2-first5-additions.json').read_text())
    rows = iter(line.split('\t') for line in (AUTHOR / 'l2-first5.tsv').read_text().splitlines()
                if line and not line.startswith('#'))
    result = []
    for original, addition in zip(originals, additions):
        p = copy.deepcopy(original)
        p['content'].update(contentVersion=2, standardVersion=2,
                            selectionReason='既存3段落・3問を保持し、自然な続きの段落と設問を追加。LEVEL2の250〜400語・4〜7問を適用。人間の校閲は未実施。')
        p['previousSyntax'] = p['syntax']
        p['syntax'], p['sentences'] = [], []
        for en, jp in addition['paragraphs']:
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
                    k = used.get((role, text), 0)
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
                assert any(s['role'] == 'S' for s in spans) and any(s['role'] == 'V' for s in spans)
                syntax = {'id': f"{p['id']}:{sid}", 'passageId': p['id'], 'contentVersion': 2,
                          'paragraphId': para['id'], 'sentenceId': sid, 'sentence': sentence,
                          'start': m.start(), 'end': m.end(), 'translation': jp, 'explanation': note,
                          'spans': spans, 'relations': relations,
                          'skeleton': ' / '.join(s['role'] + ': ' + s['text'] for s in spans if s['role'] in ('S', 'V', 'O', 'C')),
                          'grammarPoints': [note], 'readingOrder': '主節のSとVを先に確認し、上の文法解説で従属節・修飾句・並列・否定の範囲をたどる。最後に全文訳と照合する。',
                          'reviewStatus': 'ai_author_checked_human_pending'}
                p['syntax'].append(syntax)
                p['sentences'].append({'id': sid, 'paragraphId': para['id'], 'english': sentence,
                                       'translation': jp, 'start': m.start(), 'end': m.end(), 'syntaxId': syntax['id']})
                translations.append(jp)
            para['translation'] = ''.join(translations)
        p['wordCount'] = len(re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*", ' '.join(x['english'] for x in p['paragraphs'])))
        p['recommendedSeconds'] = round(p['wordCount'] * 1.3 / 15) * 15
        p['difficulty'] = {'scores': {'vocabulary': 2, 'syntax': 2, 'logic': 2, 'questions': 2},
                           'method': 'AI rubric: 1=高校入試、2=大学受験基礎、3=標準〜難関、4=難関、5=最難関',
                           'status': 'ai_assessed_human_pending',
                           'rationale': '身近な事例から情報の限界を考えるLEVEL2。関係詞節・間接疑問・動名詞・比較と基本的な因果対比を含む。明示された情報を中心に、異なる条件への一般化を避けて読む。'}
        p['review'] = {'fullTranslation': 'ai_checked_human_pending', 'fullSyntax': 'ai_checked_human_pending',
                       'questionUniqueness': 'ai_checked_human_pending', 'englishNaturalness': 'ai_checked_human_pending'}
        result.append(p)
    assert next(rows, None) is None, 'Unused authored sentence rows'
    return originals, result


EXTRAS = [
    [
        ('ボランティアが新しく記入欄を設けた情報はどれか。',
         ['価格と、情報を確認した日付', '訪問者の給料と購入時の年齢', 'すべての製品の販売順位', 'メーカーの広告費と従業員数'],
         ['pricesとthe date on which information had been checkedが直接の根拠。', '最初の給料の話は男性の思い出であり、新しい記録項目ではない。', '販売順位を調べたとは書かれていない。', '広告費や従業員数を記録する話はない。'],
         'added spaces for prices and the date'),
        ('リアの続報は、読者が何を区別するのを助けるために限界を説明したか。',
         ['実際に確かめた結果と、期待に基づく提案', '安い物は必ず修理でき、高い物は必ず修理できないという二種類', '扇風機を買った男性と、広報紙の発行者', '新品と中古品の色の違い'],
         ['末文のdistinguish an observed result from a hopeful suggestionに一致する。', '価格による一律の修理可否を本文は述べていない。', 'この二人を区別することが続報の目的ではない。', '色の違いについての記述はない。'],
         'distinguish an observed result from a hopeful suggestion')
    ],
    [
        ('雨の日にも公園の道がよいかと聞かれ、生徒たちはどう対応したか。',
         ['雨天の証拠がないため、測定時の天候と日付を明示した', '雨の日には大通りが必ず快適だと結論づけた', 'すべての測定値を捨て、案内を廃止した', '天気予報だけを使って雨天の経路を決定した'],
         ['no evidence about that conditionのため結論を広げず、条件を加えた。', '雨天の比較結論は出していない。', '案内を廃止したとは述べていない。', '天気予報で雨天の道を決めたわけではない。'],
         'added the dates and weather of their measurements instead of extending their conclusion'),
        ('通行できない道などの報告を確認するために必要だったものは何か。',
         ['場所と日付', '投稿者の学校の成績', '町内のすべての道路の写真', '利用者が払った交通費'],
         ['each message needed a location and a dateと明示される。', '学校の成績は報告の条件ではない。', '全道路の写真を要求してはいない。', '交通費は検証の条件として出てこない。'],
         'each message needed a location and a date'),
        ('読者からの提案はどのように扱われたか。',
         ['調べるきっかけとし、確認なしに公開情報を変更しなかった', '提案が届けば必ずすぐ公開情報を変更した', 'すべて事実でないものとして無視した', '最も短い道を選んだ人の提案だけ採用した'],
         ['a reason to investigateとnot as an automatic changeの対比に一致。', '確認なしの自動変更を本文は明確に否定する。', '調査の理由として扱っており、無視ではない。', '距離で提案者を選別する記述はない。'],
         'a reason to investigate, not as an automatic change')
    ],
    [
        ('試用時に、ある来場者は取り消し線の付いた原材料の絵をどう受け取ったか。',
         ['その日だけ用意できないという意味', 'すべての料理に必ず使われるという意味', '料理の値段が下がるという意味', '携帯電話の録音が終わったという意味'],
         ['simply unavailable that dayが誤解の内容を示す。', '常に使用するという解釈ではない。', '値段の話はこの誤解に関係しない。', '録音状態を示す絵ではない。'],
         'one visitor thought a crossed-out ingredient was simply unavailable that day'),
        ('グループが立ち止まって確認することにしたのはどのような場合か。',
         ['重要な質問が明確になっていない場合', '相手と普通の日常会話を始めるすべての場合', 'アプリが素早く訳せた場合に必ず', '原材料一覧と料理が一致し、確認事項もない場合'],
         ['whenever an important question remained unclearが判断条件。', 'ordinary conversationsにはアプリを使い続けており、全会話ではない。', '速さ自体ではなく重要事項の不明確さが条件。', '一致していること自体は停止条件ではない。'],
         'pause whenever an important question remained unclear')
    ],
    [
        ('不具合を報告せず黙っていた利用者がいた理由は何か。',
         ['普通の摩耗について責任を問われるのを恐れたから', '報告には必ず修理の専門資格が必要だったから', '図書館が報告の受付を禁止していたから', '借りた道具を誰にも返す必要がなかったから'],
         ['they feared being blamed for ordinary wearと明示される。', '資格が必要という記述はない。', '施設は報告を求めており、受付禁止ではない。', '返却義務がないとは述べていない。'],
         'they feared being blamed for ordinary wear'),
        ('新しい用紙では、何と何を分けて記入するようになったか。',
         ['観察した不具合と、その原因についての説明', '利用者の住所と撮影した鳥の種類', '借りる曜日と購入するカメラの色', '面接の点数とカメラの販売価格'],
         ['separated the observed problem from any explanation of its causeに一致。', '住所と鳥の種類の記入については述べない。', '曜日と色を分ける用紙ではない。', '面接の点数や販売価格は用紙の項目ではない。'],
         'separated the observed problem from any explanation of its cause'),
        ('オマルは次回、ストラップの緩みをいつ記入したか。',
         ['道具を施設から持ち出す前', '鳥を撮影し終えた後', '次の利用者が困ったと知った後', '修理費の支払いを拒否された後'],
         ['before taking a tool awayが報告時点を特定する。', '次回の報告は撮影終了後ではなく持ち出す前。', '次の利用者の苦情を待ったわけではない。', '支払いを拒否されたという出来事はない。'],
         'describe a loose strap before taking a tool away'),
        ('明確な報告は、次の利用者を守るほかに、どの負担を軽くしたか。',
         ['利用者が不具合の原因を推測しなければならないという負担', '職員が安全性を一切確認しなくてよいという負担', '利用者が期限内に返却するという義務', '借りる前にすべての道具を購入するという義務'],
         ['reducing the pressure on users to guess why something had gone wrongが根拠。', '職員は安全性をcheckedしており、点検をやめていない。', '返却期限をなくしたとは述べていない。', '購入義務はもともと述べられていない。'],
         'reducing the pressure on users to guess why something had gone wrong')
    ],
    [
        ('クラスは追加の観察で、人数をどのような時間帯に数えることにしたか。',
         ['互いに似た時間帯', '日によって意図的に大きく違う時間帯', '音楽公演が終わる瞬間だけ', '店主が店を閉めた後だけ'],
         ['count people at similar timesが直接の根拠。', '比較条件を大きく変える方針ではない。', '普通の日も観察するので公演終了時に限定しない。', '閉店後だけという条件はない。'],
         'count people at similar times'),
        ('クラスが測定項目を選ぶ前に、成功の意味を複数挙げた理由に合うものはどれか。',
         ['何も買わずに場所を楽しむ人もおり、来客や購買だけでは効果全体を測れないから', '客が増えることはどんな場合も悪い結果だから', '写真がなければ人数を数える方法がないから', '催しの日には観察してはいけないと分かったから'],
         ['末段落は効果のすべてを観察で捉えられない例として非購買の利用を挙げる。', '来客増を一律に悪いと評価する記述はない。', '写真以外の現地観察を計画している。', '催しの日にも観察する計画である。'],
         'someone might enjoy the space without buying anything'),
        ('最終報告の整理方法として正しいものはどれか。',
         ['写真で分かること、追加観察で分かるかもしれないこと、別の証拠が必要なことを分けた', '写真から分かったことをすべて誤りとして削除した', '新しい観察を行う前から、事業の成功を確定した', '別の証拠が必要な点は、すべて失敗したと結論づけた'],
         ['末文の三つのwhat節が三種類の情報を分けて示す。', '写真が示す限定的な事実は残している。', 'might establishで可能性を述べ、確定していない。', '証拠不足を失敗の証明とは扱っていない。'],
         'separated what the photograph showed, what the new observations might establish')
    ]
]


def main():
    originals, batch = compile_batch()
    for i, (p, questions) in enumerate(zip(batch, EXTRAS)):
        for prompt, options, reasons, quote in questions:
            shift = (i + len(p['questions'])) % 4
            order = list(range(4))[shift:] + list(range(4))[:shift]
            p['questions'].append({'id': f"q{len(p['questions']) + 1}", 'prompt': prompt,
                                  'options': [{'id': 'abcd'[n], 'text': options[j], 'explanation': reasons[j]} for n, j in enumerate(order)],
                                  'correctOptionId': 'abcd'[order.index(0)], 'explanation': reasons[0],
                                  'evidence': {'paragraphId': next(x['id'] for x in p['paragraphs'] if quote in x['english']), 'quote': quote}})
    previous = json.loads(OUTPUT.read_text())
    by_id = {p['id']: p for p in previous}
    saved_other = [p for p in previous if p['id'] not in {p['id'] for p in batch}]
    for old, p in zip(originals, batch):
        assert [x['english'] for x in p['paragraphs'][:len(old['paragraphs'])]] == [x['english'] for x in old['paragraphs']]
        assert p['questions'][:len(old['questions'])] == old['questions']
        assert p['previousSyntax'] == old['syntax']
        assert 250 <= p['wordCount'] <= 400 and 4 <= len(p['questions']) <= 7
        assert len({x['id'] for x in p['paragraphs']}) == len(p['paragraphs'])
        if p['id'] in by_id:
            assert by_id[p['id']] == p, 'Refuse to overwrite a different saved revision'
        else:
            previous.append(p)
    assert [p for p in previous if p['id'] not in {p['id'] for p in batch}] == saved_other
    OUTPUT.write_text(json.dumps(previous, ensure_ascii=False, indent=2) + '\n')
    manifest = {'batch': 'l2-first5-v2', 'baseRemoteCommit': 'c50c06942d867856ceb8fec12dddd82d127861b5',
                'humanReviewed': 0, 'preservedOtherRevisions': len(saved_other), 'preservedOtherDigest': digest(saved_other),
                'passages': [{'id': p['id'], 'words': p['wordCount'], 'paragraphs': len(p['paragraphs']),
                              'questions': len(p['questions']), 'sentences': len(p['sentences']),
                              'sentenceTranslations': len(p['sentences']), 'fullSentenceSyntax': len(p['syntax']),
                              'originalDigest': digest(old), 'preservedQuestionsDigest': digest(old['questions']),
                              'difficulty': p['difficulty']['scores']} for old, p in zip(originals, batch)]}
    (ROOT / 'analysis/reading_l2_first5_batch.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == '__main__':
    main()
