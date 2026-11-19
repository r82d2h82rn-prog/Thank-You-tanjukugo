# LEVEL2 長文36〜40：主題・タイトル

対象reading-l2-f04-06〜10。元のdrafts.json、既存3段落の英文とID、q1〜q3の全オブジェクト、過去の改訂層は保持。独立したenriched-level2-title-next5.jsonをカタログに接続。

|番号|題名|語数|段落|設問|文数|
|---|---|---:|---:|---:|---:|
|36|発見を生む分類箱|270|4|5|18|
|37|声に出して読む理由|270|5|6|18|
|38|競争しない学習記録|269|4|5|17|
|39|見学路の小さな窓|277|5|7|19|
|40|友達のための説明図|271|4|6|18|

分類の根拠と欠測、音読と内容要約の補完、振り返りの任意共有、日常作業の展示と受け手の理解、個別の説明による双方の理解確認を続きの段落に加えた。新設問14問、計29問。全選択肢に個別解説と本文根拠を保存。

全90文に文別和訳・SVOCM・句節・修飾リンク・骨格・文法説明・段落内offsetを付与。動名詞主語、使役、間接疑問、関係節、省略、受動態、過去完了、比較・否定・対比を文ごとに説明。人間の正式校閲は0題、意味・自然さ・解答一意性はAI執筆者確認。構造検査だけで意味の正確性を保証しない。

主題形式なので空所の補完は行わず、paragraphsを本文・提出後レビューに共用。syntaxOffsetBasisとoffsetBasisはparagraphs。全文訳は文別訳の連結と一致し、旧構文はpreviousSyntaxで保存。旧3問の点数を新設問数へ再計算しない。

## 検証

- TS52件・型検査・Webビルド成功。構造監査issuesは0。
- 全文の文区切り・翻訳連結・原文offset・構文span・修飾先ID・正答根拠を検査。
- 全29問の各選択肢の採点と、旧受験履歴の保持・保存往復を検査。
- コンパイラ--batch 36-40を追加。保存済み改訂と異なる内容への上書きは拒否。
- 実機の画面操作は未検証。既知のChromium起動制約があり、今回の自動検査を実機合格とは扱わない。

LEVEL2は100題中40題740文を全英文補完。全LEVEL累計75題1498文（LEVEL1=15、LEVEL2=40、LEVEL3=10、LEVEL4=10）。保存済みは100/100/10/10題。LEVEL2全体の文別訳740/1455、全文一致構文782/1455。最新全体監査はanalysis/reading_integrated_audit.json。

原稿はcontent/authoring/reading-enrichment/l2-title-next5-additions.jsonとl2-title-next5.tsv。再現はpython3 scripts/build_l2_gap5.py --batch 36-40。元教材のハッシュはanalysis/reading_l2_title_next5_batch.json。

利用者の「次」「デプロイも」に従い、先行31〜35の完成分と今回36〜40を同じGitHubのmainへ保存し、Git連携のVercel本番デプロイを行う。対象はr82d2h82rn-prog/Thank-You-tanjukugo、Vercelはyukitoshis-projects-2c28f209/tanjukugo。公開成功は新コミットのDeployment has completedステータスで確認する。未関連のanalysis/selection_decisions.jsonは含めない。

次はLEVEL2の41〜45題（reading-l2-f05-01〜05、内容一致）。元の本文と設問を保持して続行する。
