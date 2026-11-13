"""Build only L3/format1/01–05 from authored additions and sentence annotations.

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
OUTPUT = ROOT / 'content/readings/enriched-level3.json'


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def compile_batch():
    originals = json.loads((ROOT / 'content/readings/advanced.json').read_text())[:5]
    additions = json.loads((AUTHOR / 'l3-first5-additions.json').read_text())
    rows = iter(line.split('\t') for line in (AUTHOR / 'l3-first5.tsv').read_text().splitlines()
                if line and not line.startswith('#'))
    result = []
    for original, addition in zip(originals, additions):
        p = copy.deepcopy(original)
        p['content'].update(contentVersion=2, standardVersion=2,
                            selectionReason='既存3段落・3問を保持し、自然な続きの段落と設問を追加。LEVEL3の400〜600語・5〜8問を適用。人間の校閲は未実施。')
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
        p['difficulty'] = {'scores': {'vocabulary': 3, 'syntax': 4, 'logic': 3, 'questions': 3},
                           'method': 'AI rubric: 1=高校入試、2=大学受験基礎、3=標準〜難関、4=難関、5=最難関',
                           'status': 'ai_assessed_human_pending',
                           'rationale': 'LEVEL3：具体例を抽象的な判断基準へ結び付ける論説。多重の関係節、分詞構文、倒置・強調、長い目的語、複数段落を結ぶ条件・反論・推論を含む。'}
        p['review'] = {'fullTranslation': 'ai_checked_human_pending', 'fullSyntax': 'ai_checked_human_pending',
                       'questionUniqueness': 'ai_checked_human_pending', 'englishNaturalness': 'ai_checked_human_pending'}
        result.append(p)
    assert next(rows, None) is None, 'Unused authored sentence rows'
    return originals, result

EXTRAS = [
 [
 ('新しい表示が最初に移動時刻や座席の必要を尋ねた狙いは何か。',['最低気温を無条件に全員への推奨とするのを防ぐ','気温を表示から完全に除く','全員の移動時刻を同じにする','休憩を禁止する'],['質問の順序が最低数値と万人向け推奨の同一視を防ぐ。','気温はremained visibleとある。','時刻を選ぶ仕組みで統一ではない。','座席の必要を考慮している。'],'the order of the questions prevented the lowest number'),
 ('試行で明らかになった座席情報の限界は何か。',['表示されたベンチも必要時に埋まっている可能性がある','すべてのベンチが撤去されていた','休憩場所の情報は気温を変える','ゆっくり歩く人は必ず立ち続けられる'],['could be occupiedが利用可能性の限界。','撤去ではなく使用中の可能性。','情報による物理的な気温変化は述べない。','長く立てない利用者を想定する。'],'could be occupied when it was needed'),
 ('終段落を踏まえ、筆者が支持しそうな町の約束はどれか。',['判断材料を改善し、実際の空席までは保証しない','経路上の全事情を制御する','最良経路を全住民に保証する','不確実な条件があれば情報を一切出さない'],['情報改善と状況の完全制御を区別する結論に合う。','pretending to controlを退ける。','単一の最良経路という出発点を修正している。','不確実でも改善情報を提供する。'],'without pretending to control every circumstance')
 ],
 [
 ('生徒が提案した絵が、問いを生む用途に役立つための条件は何か。',['根拠の説明を添えること','税記録の青い印と区別なく混ぜること','すべての税文書を隠すこと','港のどの場所にも同じ絵を置くこと'],['explanation of its evidential basisが必要な区別を支える。','区別なしの併置は権威の借用を招く。','資料の隠蔽は提案していない。','同じ絵の反復は述べない。'],'accompanied by an explanation of its evidential basis'),
 ('復元の絵が文書の権威を借りるとは、文脈上どのような危険か。',['推測に基づく内容が記録済みの事実と同じ確かさに見える','文書の著作権が絵によって消える','港の活動がすべて課税対象に変わる','青い印の場所に建物が現在も建つ'],['根拠の異なる画像を同列表示するため起きる混同。','権威はここでは証拠としての信頼性。','過去の税制度を変える話ではない。','現在の建物の存在は保証しない。'],'borrow the authority of the documents'),
 ('日誌と税記録をそのまま一枚の地図へまとめられなかったのはなぜか。',['日誌の荷下ろし場所の位置が正確でないから','日誌が一切の港の活動に触れないから','税記録がすべて偽造だったから','学芸員が資料の比較を禁止したから'],['did not locate them preciselyが不足する情報。','日誌にはtemporary unloading placesが出てくる。','偽造を示す記述はない。','来館者を比較へ招いている。'],'did not locate them precisely'),
 ('最終的な展示変更が来館者に開いた検討は何か。',['資料の種類によって残す情報がどう異なるか','どちらか一方の資料が全て真実で他方は全て虚偽か','不明な場所に好きな活動を確定してよいか','港が存在しなかったと証明できるか'],['終文が二種の記録の保存内容の違いを調べると述べる。','完全信頼か完全拒絶かの二択を避ける。','想像を等しく確定する立場を否定する。','港自体の存在を疑う議論ではない。'],'how two kinds of record differed in what they preserved')
 ],
 [
 ('指導者が情報要求の内容を評価した基準は何か。',['その情報が診断を実際に変え得るか','要求の文章が常に長いか','慎重そうに聞こえる言葉が多いか','以前の答えと同じ答えを言うか'],['変え得る情報かという関連性を重視する。','説明の長さが教育性を決めるとはしない。','sounding cautiousだけの評価を退ける。','以前の答えの記憶と判断力を区別する。'],'something that could actually change the diagnosis'),
 ('別の環境へ機械を移す際、技術者が新たに区別した二種類の特徴が重要になるのはなぜか。',['普段存在しないため未検討の特徴を、無関係と確認済みの特徴と混同せずに済むから','以前無視した特徴は全て新環境でも必ず無関係だから','初心者の疑問は常に熟練者の説明より正しいから','新環境ではマニュアルが全状況を予見するから'],['irrelevantだからの除外とusually absentのための未検討を区別する。','環境変化で習慣の信頼性が失われ得る。','初心者の常時優越は述べない。','末文は全状況の予見を否定する。'],'a feature which she had ignored because it was irrelevant from one which she had failed to consider because it was usually absent')
 ],
 [
 ('既知の慣行に関する説明が不要という反論に、チームはどう対応したか。',['指摘を認めつつ、全員に同一の表示方法が必要という前提は退けた','既知の読者の存在を否定した','未知語を展示からすべて削除した','長い説明を全員に必読とした'],['accepted the pointとrejected the assumptionの対比に一致。','指摘そのものは認める。','語は保持する方針。','第二層はoptionalである。'],'accepted the point, but rejected the assumption'),
 ('二層の表示が示す設計上の考えはどれか。',['概要をすぐ得る経路と詳しく理解する経路を用意できる','読者の予備知識の差をなくすまで展示しない','短い見出しがあれば説明は常に不要になる','長い説明を読まない人には何も分からない'],['headingとoptional second layerが役割を分担する。','予備知識の異なる読者で試す。','目的や読者によって説明を利用できる構成。','注記を飛ばしても識別した人がいる。'],'an optional second layer explained the obligations'),
 ('説明付き表示を使って改められた印象は何か。',['所有者は収入減だけを気にしているという印象','所有者が農業を一切知らないという印象','どの読者も義務を同一に理解するという印象','土地には作物を育てる機能がないという印象'],['lost incomeだけという印象をreviseした。','農業を知らないとの記述はない。','この箇所の以前の印象は所有者の関心。','土地の生産機能を否定していない。'],'an earlier impression that the owner was concerned only with lost income'),
 ('共同体内の意見の不一致を隠す注記にはどんな問題があるか。',['元の語を残していても、その概念を固定化・単純化しかねない','語を残しただけで必ず全員が同じ理解に達する','意見が違えば義務に関する共通性は一切なくなる','どんな説明でも短くすることが不可能になる'],['未知語保持と概念保護が別であると第6段落が示す。','語の共有と解釈の一致は別。','終文はshared relationshipを明示。','注記の長さの不可能性を論じていない。'],'preserve unfamiliar vocabulary while simplifying the idea'),
 ('最終段落から妥当に導ける筆者の立場はどれか。',['解釈の幅を示しても、共有された関係を表す語の意味は維持できる','意味のある語なら全員の解釈が必ず一致する','意見が割れる語は必ず身近な語に置き換えるべきだ','説明には具体例を用いてはいけない'],['不一致自体も共有された関係に関することが結論。','identicallyの理解を装う必要はないとする。','その置換が関係を落とすと指摘する。','最終表示はexampleを提供した。'],'the disagreements themselves concerned a shared relationship')
 ],
 [
 ('二つの複製の比較で、議論を前進させた問いはどれか。',['それぞれは何について正確なのか','どちらがあらゆる面で完全なのか','どちらの原品を廃棄すべきか','どちらに注意書きが一切不要なのか'],['what each copy was accurate aboutという対象を限定した問い。','単一の優劣評価から問いを具体化した。','原品廃棄は提案しない。','無条件に注意不要とはしない。'],'what each copy was accurate about'),
 ('滑らかさを年代の証拠とした誤解から分かることは何か。',['相違の記録や一見明快な表示だけで適切な推論は保証されない','滑らかな物はどれも必ず古い','製造方法は複製の理解に一切関係しない','複製には触れること自体を全面禁止すべきだ'],['記録の存在と理解の保証を分け、具体的な誤解を示す。','まさに訂正対象の推論。','訂正に製造方法の説明が必要だった。','接する機会の禁止は結論ではない。'],'treat smoothness as evidence of age'),
 ('筆者の結論に最も近い授業活動はどれか。',['複製から得た体験がどの主張を支え得るか、根拠と限界を説明させる','複製に触れたことだけで理解済みと判定する','原品以外を全て無価値と説明する','限界の一般的注意を一度読ませれば誤解はないと扱う'],['最後の結論は経験とそれに基づく主張の関係の検討。','access aloneの保証を否定。','copies inevitably deceiveという全面否定を退ける。','一般警告だけから具体的な問いへ変えている。'],'examine the relationship between an experience and the claims made on its basis')
 ]
]

def main():
    originals, batch = compile_batch()
    for i,(old,p,extra) in enumerate(zip(originals,batch,EXTRAS)):
        for prompt,options,reasons,quote in extra:
            shift=(i+len(p['questions']))%4
            order=list(range(4))[shift:]+list(range(4))[:shift]
            p['questions'].append({'id':f"q{len(p['questions'])+1}",'prompt':prompt,
              'options':[{'id':'abcd'[n],'text':options[j],'explanation':reasons[j]} for n,j in enumerate(order)],
              'correctOptionId':'abcd'[order.index(0)],'explanation':reasons[0],
              'evidence':{'paragraphId':next(x['id'] for x in p['paragraphs'] if quote in x['english']),'quote':quote}})
        assert p['questions'][:len(old['questions'])]==old['questions']
        assert [(x['id'],x['english']) for x in p['paragraphs'][:3]]==[(x['id'],x['english']) for x in old['paragraphs']]
        assert 400<=p['wordCount']<=600 and 5<=len(p['questions'])<=8
    if OUTPUT.exists():assert json.loads(OUTPUT.read_text())==batch,'Do not overwrite saved revisions'
    OUTPUT.write_text(json.dumps(batch,ensure_ascii=False,indent=2)+'\n')
    manifest={'batch':'l3-first5-v2','baseCommit':'052a5dc592f5ecfee692a15e9b3c857291049025','humanReviewed':0,
      'passages':[{'id':p['id'],'words':p['wordCount'],'paragraphs':len(p['paragraphs']),'questions':len(p['questions']),
       'sentences':len(p['sentences']),'translationCoverage':1,'syntaxCoverage':1,'originalDigest':digest(old)} for old,p in zip(originals,batch)]}
    (ROOT/'analysis/reading_l3_first5_batch.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest,ensure_ascii=False))

if __name__=='__main__':main()
