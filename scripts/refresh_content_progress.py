#!/usr/bin/env python3
"""Refresh measured progress without granting editorial or production approval."""
import collections,json
from content_pipeline import ROOT,NOW,TARGETS,read_json,write_json,write_csv,audit
from build_word_plan import build

def refresh(root=ROOT):
 plan=build(root)
 if not audit(root):raise ValueError('教材構造エラー。進捗を成功扱いしません。')
 report=read_json(root/'analysis/content_audit.json');samples=read_json(root/'src/data/entries.json');metadata=read_json(root/'content/provenance.json')
 drafts=read_json(root/'content/words/drafts.json');rows=[]
 for e in samples+drafts:
  m=e.get('content') or metadata[e['id']]
  rows.append(dict(id=e['id'],kind=e['kind'],level=e['level'],section=e['section'],number=e['number'],english=e['english'],meaning=e['meaning'],pos=e['pos'],pronunciation=e['pronunciation'],example=e['example'],translation=e['translation'],review_status=m['qualityStatus'],human_reviewed=str(m['humanReviewed']).lower(),source_ids=json.dumps(m['sourceIds'],ensure_ascii=False),dictionary_check='not_fully_verified'))
 write_csv(root/'content/review_queue.csv',rows,list(rows[0]))
 summary=dict(updatedAt=NOW(),wordTargets=TARGETS['word'],authoredWordDrafts=plan['authoredCounts'],unwrittenWords=plan['unwrittenCounts'],approved=report['approvedCounts'],humanReviewPending=report['humanReviewPending'],source='analysis/content_audit.json and analysis/word_plan_summary.json',releaseReady=report['releaseReady'])
 write_json(root/'analysis/production_checkpoint.json',summary)
 lines=['# 教材の制作状況','','全量目標は単語3,900・熟語2,000・長文400。本文と検証状態の実数を記録します。仮採用行は完成教材ではありません。','','| LEVEL | 単語目標 | 本文付き草稿 | 未執筆 | 正式承認済み単語 |','|---|---:|---:|---:|---:|']
 for l in range(4):lines.append(f"| {l+1} | {TARGETS['word'][l]} | {plan['authoredCounts'][l]} | {plan['unwrittenCounts'][l]} | {report['approvedCounts']['word'][l]} |")
 lines+=['',f"単語草稿合計{len(drafts)}語。旧検証用100単語・50熟語は別枠。人手確認待ち{report['humanReviewPending']}項目。正式承認済み教材だけを通常の製品教材に取り込みます。",'', '熟語は初期検証用50個のみ。正式2,000個と長文400題は未完成。入試本文の分析は許諾範囲未確定で0試験のままです。未取得・未検証の頻度を補っていません。','', '既存150教材のIDと保存形式を維持。単語草稿は個別の独自例文・和訳・用法説明を持ちます。意味・IPA・自然さ・難易度は人手確認待ちで、自動構造検査と区別します。','', 'PR: https://github.com/r82d2h82rn-prog/Thank-You-tanjukugo/pull/1 。最新の再開情報はdocs/AUTHORING_CHECKPOINT.md。']
 (root/'CONTENT_STATUS.md').write_text('\n'.join(lines)+'\n')
 checkpoint=['# 本文制作の再開地点','',f'計測日時: {summary["updatedAt"]}', '', 'ユーザーの指示は全量追加。公開GitHub保存の明示承認は継続しています。小さな追加報告だけで依頼を完了扱いにしません。','',f'本文付き単語草稿: {len(drafts)} / 3,900。LEVEL別 '+str(plan['authoredCounts'])+'。未執筆 '+str(plan['unwrittenCounts'])+'。','', 'content/authoring/words_l*_s*.tsvが今回の独自執筆バッチ。各ファイルの英語・和訳・IPA・用法解説は手作りで、テンプレートの語句差し替えによる水増しをしていません。', '', '次は未完了の単語SECTIONの本文制作。既存語・既存IDの上書きはimport_authored_words.pyが拒否。各SECTIONは100語、品詞順は動詞→名詞→形容詞→副詞→その他。', '', '取り込み後にrefresh_content_progress.pyで計測し、内容をGitHubへ保存。人手校閲済み・正式承認済みへ機械的に変更しない。単語全量の後に熟語2,000、長文400の制作へ進む。', '', 'GitHub CLIのpush認証はないため、認証済みGitHub連携のcreate_tree/create_commit/update_refを使用。ローカルとリモートのtree SHAを照合する。リモートブランチfeat/full-content-production、PR #1。現在のGitHub基点はgitのorigin/feat/full-content-productionから取得する。','', '大学本文は別途利用条件が確定したものだけ分析。架空の頻度を作らない。ブラウザのsocket() EPERMは未解消。']
 (root/'docs/AUTHORING_CHECKPOINT.md').write_text('\n'.join(checkpoint)+'\n')
 return summary
if __name__=='__main__':print(json.dumps(refresh(),ensure_ascii=False,indent=2))
