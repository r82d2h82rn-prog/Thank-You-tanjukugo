#!/usr/bin/env python3
"""Create a 3900-slot EDITORIAL PROPOSAL; never call unbuilt entries lessons.

Uses only measured source ranks, source membership, and explicit exclusions.
All automated difficulty assignments remain provisional and require review.
"""
import collections,hashlib,json
from word_catalog import authored_catalog
from content_pipeline import ROOT,NOW,TARGETS,read_json,read_csv,write_csv,write_json
BASIC=set('''the be and of to a an in have it you he for they not that we on with this i do as at she but from by will or say go so all if one would about can which there know more get who like when think make time see what up some other out good people year take no well because very just come could work use than now then also into only look want give first new way find over any after day where thing most should need much right how back mean even may down such last number understand through ask too put still keep every let those long between under while little own another must home same old big high small large less live place help yes oh ah hey hello goodbye mr mrs ms dr sir madam mister apple banana pear orange lemon melon peach grape strawberry potato tomato onion carrot cat dog mouse horse cow pig sheep goat hen chicken egg bread breakfast dinner lunch mother father sister brother son daughter aunt uncle grandfather grandmother monday tuesday wednesday thursday friday saturday sunday january february march april june july august september october november december zero two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty hundred thousand million non anti ex pseudo o'clock'''.split())
SPECIALIST=set('''chemotherapy chromosome chloride capillary coefficient deflection denominator differential dissection epidemiology factorial fetal coronary cortex capillary axiom amino enzyme nucleotide logarithm matrix polynomial theorem trigonometry quantum photon neutron proton quark methanol polymer monomer tariff debenture arbitrage amortization indenture annuity collateral liquidation lien escrow subprime forex ebitda fiduciary remittance notary leasehold freehold excise debenture remuneration severance subpoena felony misdemeanor plaintiff defendant prosecution indictment litigation restitution affidavit intangible goodwill'''.split())

def build(root=ROOT):
 candidates=read_csv(root/'content/word_candidates.csv');drafts=authored_catalog(root);samples=read_json(root/'src/data/entries.json')
 by_lemma={r['lemma']:r for r in candidates};pinned={e['english']:e for e in drafts}
 legacy={e['english']:e for e in samples if e['kind']=='word'}
 reserved=set()
 if (root/'content/words/selection.json').exists():
  active_ids={e['id'] for e in drafts};reserved={e['english'] for e in read_json(root/'content/words/drafts.json') if e['id'] not in active_ids}
 excluded={}
 for r in candidates:
  word=r['lemma']
  if word in pinned:continue
  if word in reserved:excluded[word]='改訂基準でLEVEL3下限未満として保留。本文・ID・履歴は保存。'
  elif r['status']=='不採用' or word in BASIC:excluded[word]='単独基本義・機能語・固有名詞的表現。特殊語義は別途検討。'
  elif word in legacy:excluded[word]='初期の動作検証教材。履歴は保存し、今回の最終採用案には自動算入しない。'
  elif word in SPECIALIST:excluded[word]='専門性が高い候補。一般入試の学習価値を要追加調査。'
  elif not set(json.loads(r['source_ranks']))&{'ngsl','nawl','tsl','bsl'}:excluded[word]='指定リストへの掲載なし。未執筆候補の補完調査待ち。'
 def priority(r):
  ranks=json.loads(r['source_ranks']);ng=ranks.get('ngsl',{}).get('rank');ts=ranks.get('tsl',{}).get('rank');bs=ranks.get('bsl',{}).get('rank')
  # These are selection heuristics, not invented corpus frequencies or exam scores.
  return (1000+(2810-ng)/2809*200 if ng else 0)+(180 if 'nawl'in ranks else 0)+(120*(1251-ts)/1250 if ts else 0)+(80*(1745-bs)/1744 if bs else 0)
 pool=sorted([r for r in candidates if r['lemma'] not in excluded and r['lemma'] not in pinned],key=lambda r:(-priority(r),r['lemma']))
 missing=sum(TARGETS['word'])-len(drafts)
 if len(pool)<missing:raise ValueError(f'候補が不足: 必要{missing} / 利用可能{len(pool)}。水増ししない。')
 chosen=pool[:missing];remaining=iter(chosen);plan=[]
 for level,target in enumerate(TARGETS['word'],1):
  level_drafts=sorted([e for e in drafts if e['level']==level],key=lambda e:(e['section'],e['number']))
  for position in range(1,target+1):
   authored=level_drafts[position-1] if position<=len(level_drafts) else None
   row=by_lemma.get(authored['english'],dict(lemma=authored['english'],source_ranks='{}')) if authored else next(remaining);lemma=row['lemma']
   plan.append(dict(id=authored['id'] if authored else 'word-c-'+hashlib.sha256(lemma.encode()).hexdigest()[:12],lemma=lemma,proposed_level=level,proposed_section=(position-1)//100+1,proposed_number=(position-1)%100+1,pos=authored['pos'] if authored else '',authoring_status='authored_pending_review' if authored else 'unwritten',editorial_status='要確認',human_reviewed='false',assignment_basis='独自の語義・用法による暫定分類。校閲待ち。' if authored else '一般頻度・学術掲載・補助リスト順位による仮配置。品詞順・学習順の審査前。',source_ranks=row['source_ranks'],exam_frequency='',production_approved='false',frozen_number='false'))
 assert len(plan)==3900 and len({r['lemma'] for r in plan})==3900 and len({r['id'] for r in plan})==3900
 if not (root/'content/words/selection.json').exists():
  write_csv(root/'content/word_adoption_plan.csv',plan,list(plan[0]))
 if not (root/'content/words/selection.json').exists():
  write_csv(root/'analysis/word_plan_exclusions.csv',[dict(lemma=w,reason=r) for w,r in sorted(excluded.items())],['lemma','reason'])
 report=dict(updatedAt=NOW(),status='editorial_proposal_not_lessons',proposedCounts=[sum(r['proposed_level']==l for r in plan) for l in range(1,5)],authoredCounts=[sum(r['proposed_level']==l and r['authoring_status']=='authored_pending_review' for r in plan) for l in range(1,5)],unwrittenCounts=[sum(r['proposed_level']==l and r['authoring_status']=='unwritten' for r in plan) for l in range(1,5)],approvedCounts=[0]*4,excludedCandidates=len(excluded),reserveCandidates=len(pool)-missing,notes=[f'3900行は全量の仮採用・制作台帳。未執筆{missing}語を完成教材と数えない。','未執筆語の配置は頻度等による仮案。NAWL掲載だけでLEVEL4と確定しない。','正式確定番号ではない。品詞・語義・難易度の審査後にSECTION内の品詞順を決める。','既存教材・草稿のIDは再利用しない。旧検証教材の履歴を他語へ付け替えない。','大学入試の出現頻度・総合採用スコアは未検証。'])
 write_json(root/'analysis/word_plan_summary.json',report);return report
if __name__=='__main__':print(json.dumps(build(),ensure_ascii=False,indent=2))
