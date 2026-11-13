"""Build only L4/format6/01–05 from authored additions and sentence annotations.

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
OUTPUT = ROOT / 'content/readings/enriched-level4.json'


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def compile_batch():
    originals = [p for p in json.loads((ROOT / 'content/readings/advanced.json').read_text()) if p['level'] == 4][:5]
    additions = json.loads((AUTHOR / 'l4-first5-additions.json').read_text())
    rows = iter(line.split('\t') for line in (AUTHOR / 'l4-first5.tsv').read_text().splitlines()
                if line and not line.startswith('#'))
    result = []
    for original, addition in zip(originals, additions):
        p = copy.deepcopy(original)
        p['content'].update(contentVersion=2, standardVersion=2,
                            selectionReason='既存3段落・3問を保持し、自然な続きの段落と設問を追加。LEVEL4の600〜900語・6〜10問を適用。人間の校閲は未実施。')
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
                implicit = sentence.startswith(('Imagine ', 'Consider ' , 'Consider,'))
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
        p['difficulty'] = {'scores': {'vocabulary': 4, 'syntax': 5, 'logic': 5, 'questions': 4},
                           'method': 'AI rubric: 1=高校入試、2=大学受験基礎、3=標準〜難関、4=難関、5=最難関',
                           'status': 'ai_assessed_human_pending',
                           'rationale': 'LEVEL4：責任・正当化・解釈・価値・独立性の抽象的論説。多重修飾、挿入、省略、複雑な譲歩と仮定、否定の作用域を読み分け、複数段落にまたがる暗黙の前提と含意を検討する。'}
        p['review'] = {'fullTranslation': 'ai_checked_human_pending', 'fullSyntax': 'ai_checked_human_pending',
                       'questionUniqueness': 'ai_checked_human_pending', 'englishNaturalness': 'ai_checked_human_pending'}
        result.append(p)
    assert next(rows, None) is None, 'Unused authored sentence rows'
    return originals, result
EXTRAS = [
 [
 ('結果を審査員から伏せるだけでは不十分なのはなぜか。',['事故後に得られた技術的知識まで、当時の知識から取り除けるわけではないから','事故を知らない審査員は当時の検査員より必ず情報が少ないから','結果を伏せると修繕費も算出できなくなるから','判断時の条件を調べることが結果の価値を否定するから'],['結果を知らなくても、事故が促した研究の知識を持ち得る。','情報量の大小でなく、当時なかった知識の混入が論点。','修繕費算定不能という主張はない。','結果の証拠価値は保ちながら責任基準を区別する。'],'reviewers may possess technical knowledge acquired only because the failure prompted research'),
 ('作業条件を考慮する審査について、筆者が退ける評価はどれか。',['実行可能で正当な追加調査だったかを検討する','同じ見落としなら無被害の検査員も批判し得る','条件を十分に説明できた以上、どんな見落としも免責する','当時の不確実性を残した現実的な代案を比較する'],['本文が支持する評価であり、設問の退ける対象ではない。','警告が両者にあれば両者批判を認める。','every omissionを不可避にする寛大な記述を免責の語彙と批判する。','不確実性のない架空判断との比較を退けている。'],'contextual understanding becomes a vocabulary for exemption'),
 ('警告を両者が安価に確認できたという仮定から、最も妥当に導けることはどれか。',['嵐に遭った側だけに注意義務が生じる','注意不足への批判は両者に及び得るが、修繕・補償への損害の意味は別に残る','損害差があるので、両者への批判の根拠も必ず異なる','同じ注意不足なら補償額も同じにすべきだ'],['注意基準は嵐への遭遇で初めて生じるものではない。','共通のomissionとdamageのrepair/compensation上の意味を分ける。','批判の共通根拠として警告の見落としを設定している。','補償額の同一化は結論に含まれない。'],'although the damage might still matter for questions of repair and compensation'),
 ('警告が得られなかったという反実仮想の役割はどれか。',['被害が同じでも、当時の認識可能性が違えば同じ注意不足は立証されないと示す','警告がない事故では、設計そのものの再調査も不要と示す','記録がなければ責任を論じる方法は存在しないと示す','損害を受けなかった検査員の能力が高いという評価を補強する'],['Had the warning ...と主節のwould not establishがこの対比を示す。','責任判断の限界を再調査の不要へ広げてはならない。','記録一般の不在を設定していない。','chanceに助けられた実績を能力と短絡しない結論である。'],'Had the warning been unavailable, the same pattern of damage would not by itself establish the same failure of care.')
 ],
 [
 ('申請者の介護事情を追加の距離点に換算する例が示すのは何か。',['発言を記録に入れても、分類原理への異議は認めていない場合がある','事情を数値化すれば、分類の正当化はもはや不要になる','どんな事情も数値化しなければ配分を比較できない','介護事情のある申請者への配分を必ず拒否すべきだ'],['testimonyの入力とassumptionの不変を対比する例。','分類原理が無検討で残る危険を述べる。','既存の距離だけへの換算を十分条件にしない。','具体的な配分の拒否を筆者は指示しない。'],'The testimony has entered the record, but the original assumption may remain untouched'),
 ('批判後にも同じ規則が残ることを、筆者が直ちに失敗とみなさない理由は何か。',['異議があっても規則は変更してはいけないから','批判に理由を示して応答した存続と、批判を遮断した存続は異なるから','採用されなかった異議は最初から関連性がなかったから','決定が予測可能なら根拠の説明は省略できるから'],['変更禁止を求めていない。','survival after an answerとbecause no objectionの対比に一致。','拒否も正当化を検討されるべき対象である。','予測可能性と理由へのアクセスを区別する。'],'its survival after an answer has been given is different from its survival because no relevant objection was allowed'),
 ('人間の委員会に裁量を移すだけでは不十分だという議論の狙いはどれか。',['自動計算より人の判断を常に低く評価する','判断主体の変更と、判断根拠を問えることを区別する','事情を個別に考慮すること自体を禁止する','不透明な規則なら予測可能性も必ず失われると示す'],['人と機械の一律の優劣を論じていない。','移管後も根拠がinaccessibleなら説明責任は確保されない。','個別事情を理由付きで検討することを認める。','予測可能でも批判に閉じている規則はあり得る。'],'while leaving the grounds of authority equally inaccessible'),
 ('退けた異議の例も公表することが訂正に役立つのはなぜか。',['成功例だけでは隠れる矛盾や分類境界の判断根拠も検討できるから','拒否例が一つでもあれば制度全体の不当性が証明されるから','結果を公表すれば拒否理由も自動的に正しくなるから','後の申請者が過去と同じ例外を必ず獲得できるから'],['inconsistenciesの露呈をcorrectionの条件へ結び付ける。','矛盾の検討可能性と制度全体の棄却は別。','公表で理由の正当性が自動保証されるわけではない。','例外を得る権利の保証を結論は否定する。'],'it might disclose inconsistencies that a summary of successful appeals would conceal'),
 ('本文全体から見て、説明責任の実現を最もよく示す制度はどれか。',['異議申立ての件数を増やすが分類原理は再検討しない制度','申立ての採否を理由付きで記録し、その区別の妥当性も後から問える制度','部屋が足りないので全申立てに同じ定型理由で答える制度','申立人の不満がなくなるまで配分結果を変更し続ける制度'],['機会の数と原理への異議可能性は別。','根拠と分類境界が公的な批判に開かれるという結論を満たす。','文面の応答だけで事情への適切な理由があるとは言えない。','不一致解消や望む結果の保証は目的ではない。'],'the boundary between a relevant circumstance and an irrelevant one would no longer be protected merely by the authority')
 ],
 [
 ('娘が会話を完了した反対例を、相手が見知らぬ人だったとして説明し直すことが妥当になる条件は何か。',['その区別を作品の他の箇所も支えていること','その区別を加えれば批評家の好む解釈が守れること','一つの場面を区別すれば他の細部の検討が不要になること','作者が対話を避ける性格だったと推測できること'],['区別がelsewhereでsustainedという条件が付く。','解釈を守るためだけの条件追加は反証不能化を招く。','さらなる本文への注意を求める立場に反する。','作者の性格の推測はこの条件を満たさない。'],'If that distinction were sustained elsewhere'),
 ('第二の解釈が形式をよく説明しても第一の批評家の不満が残り得るという箇所の含意は何か。',['形式の説明が成功すれば鑑賞上の不満は非合理になる','満足できなければ、その形式についての説明も誤りになる','形式の機能の説明と、体験への評価は関連するが同じ判断ではない','感情による評価は本文との関係を持つ必要がない'],['説明から満足への一義的決着を否定する。','不満と形式的な説明は両立し得る。','説明・満足・道徳判断を区別する段落の趣旨。','評価が自由だから根拠不要という結論ではない。'],'An account of how an ending works does not settle whether the experience it offers is satisfying'),
 ('物理仮説の実験への言及は、筆者の立場をどう限定しているか。',['解釈は実験できないので根拠に応答する必要もない','実験と同じ手順は要求しないが、本文の反対材料に応答する制約は求める','文学解釈は再現可能な実験だけで一意に決めるべきだ','技巧的な解釈なら反証不能でも根拠のある読みと等価になる'],['実験の不採用と無制約な解釈を混同している。','実験との非同一性とresponsiveness to a textを両立させる。','そのような要求は明示的に否定する。','unconstrainedなingenuityを本文への応答から区別する。'],'not to demand the sort of experiment through which a physical hypothesis might be tested')
 ],
 [
 ('回答票の実務上の必要を認めても、価格化できない理由の排除を正当化できないのはなぜか。',['記録形式が排除したことを、住民にその理由がないという発見として使えないから','比較できる情報を集めること自体が不公正だから','価格として出せない価値は常に他の公共需要より優先するから','記録された意見は決定に一切使ってはいけないから'],['設計のeffectを住民についてのdiscoveryと取り違える循環を批判。','意思決定用情報の必要にはforceを認めている。','価値の自動優先を結論は否定する。','情報を使うことではなく排除からの誤推論を問題にする。'],'has mistaken an effect of its own design for a discovery'),
 ('住民が除去に反対しつつ、決定された場合の補償交渉に応じることを筆者はどう捉えるか。',['補償の話を始めた以上、反対は論理的に撤回される','判断の段階が違うので、条件付きの立場として両立し得る','どちらかの意見を記録から除くことで初めて整合的になる','結果が同じなら条件の記録は不要になる'],['条件付き交渉を事前同意に変換することこそ批判対象。','different stagesに関する問いなのでwithout inconsistencyに共存できる。','区別を残すことが改訂票の意義。','要約時にもconditional structureの保持が必要。'],'These positions can coexist without inconsistency'),
 ('コメント欄を設けた相談でも、本文の批判が当てはまり得るのはどの場合か。',['コメントの条件や区別を、最終的な集計が消してしまう場合','コメントが交通改善の必要にも触れている場合','コメントに住民ごとの価値観の差が含まれる場合','不満が残っていても、当局が優先した理由を説明した場合'],['入力で広げても集計で狭める問題を指摘する。','改善支持と除去反対は両立し得る。','価値観の相違は排除を正当化しない。','述べられた理由による却下と意見の消去は区別する。'],'if the method of counting answers erases the distinctions'),
 ('共通の価値尺度がないまま、当局が交通計画を優先した場合、筆者が求める応答に近いものはどれか。',['合意に至らなかった以上、いかなる決定も永久に延期する','補償が用意されたことを、除去が住民全員に受容された証拠とする','対立が残ることを認め、なぜ交通上の考慮を優先したか説明する','合意に反する立場を集計対象外として一致率を報告する'],['共通尺度の完成まで待つ義務は否定する。','補償と受容を同一視している。','conflictの消滅を主張せず優先理由を述べるという結論。','手続き設計による不一致の消去を再現する。'],'to explain why one consideration was given priority'),
 ('補償が決定後に適切であり得るという主張が、庭園存続の議論と両立するのはなぜか。',['適切な補償は、決定前に除去が正当だったことを証明するから','損害への対処の適切さと、喪失を受容したかは別に判断されるから','金銭は価値と無関係なので補償の意味もないから','補償があれば異議を記録する必要がなくなるから'],['retrospectively showingを否定している。','Compensation ... appropriateとacceptabilityの非同一性を示す。','金銭の有用性は本文が認める。','補償を事前同意の代用にしてはいけない。'],'without retrospectively showing that the loss was acceptable'),
 ('筆者のいう開放性が守るものを最も適切に表すのはどれか。',['住民の希望する決定が必ず採用されること','住民が一つの共通尺度だけで価値を答えられること','採用されなくても、表明した不一致が別の選好として改変されないこと','金銭を選ぶ住民の回答を除き非金銭的価値だけを残すこと'],['not a right to secure the preferred outcomeと明記。','共通尺度への強制こそ問題。','being overruledとdisagreement represented as an unexpressed preferenceの区別。','金銭を好むことの合理性も認めている。'],'a preference one never expressed')
 ],
 [
 ('原理の異なる機器でも校正基準を共有し得るという議論は、独立性の判断に何を求めるか。',['機器の外観や原理の差ではなく、特定の一致を生み得る共通要因との関係を示す','機器を異なる研究室へ移せば全ての依存が解消するとみなす','共通性が一つでもあれば、その比較からは何も学べないとする','校正基準だけが唯一の可能な誤差源だと確定する'],['independenceをpossible source of agreementとの関係で特定する。','設置場所が異なるだけでは関連する共有を消せない。','比較自体にも共有conventionsが必要と認める。','校正は共有要素の一例で唯一の原因とはしない。'],'with respect to a possible source of agreement'),
 ('校正を変えて一つのパターンが消えた場合に妥当な推論はどれか。',['元の校正に依存した全測定を同じ理由で棄却する','依存の存在を記録すれば、その推論への関係の説明は省ける','その推論で校正が果たす役割を調べ、他の測定への結論は区別する','一部が変わるなら校正変更後の機器の全結果も無効になる'],['every measurementの誤りの証明ではない。','why the dependence matteredという説明をなお求める。','再調査の根拠と全測定の否定を区別する。','新機器の全面無効という結論は導けない。'],'it would not prove that every measurement made with it had been mistaken'),
 ('比較結果のたびに「特定されない欠陥」で説明を調整する代案の問題は何か。',['最初と違う説明を出した時点で科学的批判ではなくなる','どの結果でも維持できるため、元の説明と見分ける検討ができなくなる','代案が完全な理論でないので異議を述べる権利がない','他者への依存を少しでも含むから誤りと決まる'],['代案の提示そのものは有益な批判の条件になり得る。','any conceivable resultを吸収する説明の識別不能性を批判。','完全なreplacement theoryの事前提出は不要とする。','依存の全面排除は要求しない。'],'an unspecified flaw'),
 ('本文全体に照らし、批判者に求められる責任を最も適切に表すものはどれか。',['完全な代替理論がないなら懸念を表明しない','依存を含む主張は例外なく不採用とする','具体的な未解決の可能性を示し、自分の提案を強める・弱める材料も問えるようにする','従来の一致を疑う姿勢さえ維持すれば根拠を更新しなくてよい'],['完全理論がなくてもspecific possibilityを示してよい。','依存が推論に関係するかを検討する立場。','批判自体も問われる対象に開く段落と最終結論を結び付ける。','疑念を不可侵にする姿勢を批判する。'],'what would strengthen or weaken it')
 ]
]

def main():
    originals,batch=compile_batch()
    correct=[[0,2,1,0],[0,1,1,0,1],[0,2,1],[0,1,0,2,1,2],[0,2,1,2]]
    for i,(old,p,extra) in enumerate(zip(originals,batch,EXTRAS)):
        for k,(prompt,options,reasons,quote) in enumerate(extra):
            j=correct[i][k]
            shift=(i+len(p['questions']))%4;order=list(range(4))[shift:]+list(range(4))[:shift]
            p['questions'].append({'id':f"q{len(p['questions'])+1}",'prompt':prompt,
             'options':[{'id':'abcd'[n],'text':options[j],'explanation':reasons[j]} for n,j in enumerate(order)],
             'correctOptionId':'abcd'[order.index(j)],
             'explanation':reasons[j],'evidence':{'paragraphId':next(x['id'] for x in p['paragraphs'] if quote in x['english']),'quote':quote}})
        assert [(x['id'],x['english']) for x in p['paragraphs'][:3]]==[(x['id'],x['english']) for x in old['paragraphs']]
    for i,p in enumerate(batch):
        assert p['questions'][:3]==originals[i]['questions']
        assert 600<=p['wordCount']<=900 and 6<=len(p['questions'])<=10
    if OUTPUT.exists():assert json.loads(OUTPUT.read_text())==batch,'Refuse to replace saved revisions'
    OUTPUT.write_text(json.dumps(batch,ensure_ascii=False,indent=2)+'\n')
    manifest={'batch':'l4-first5-v2','baseCommit':'b9fac1ae32d71e82097b8afe94c3882f90ad8a9e','humanReviewed':0,
     'passages':[{'id':p['id'],'words':p['wordCount'],'paragraphs':len(p['paragraphs']),'questions':len(p['questions']),
      'sentences':len(p['sentences']),'translationCoverage':1,'syntaxCoverage':1,'originalDigest':digest(old)} for old,p in zip(originals,batch)]}
    (ROOT/'analysis/reading_l4_first5_batch.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest,ensure_ascii=False))

if __name__=='__main__':main()
