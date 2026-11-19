# LEVEL2 長文41〜45：指示語

対象reading-l2-f05-01〜05。原本drafts.json、旧3段落の英文・ID、q1〜q3の全オブジェクト、過去の改訂層を維持。独立したenriched-level2-reference5.jsonをカタログへ接続。41〜45は内容一致でなく指示語形式であり、以前の継続先の形式名を訂正した。

|番号|題名|語数|段落|設問|文数|
|---|---|---:|---:|---:|---:|
|41|紙の切符に残った記憶|269|4|5|19|
|42|二つの試験管のラベル|280|5|6|19|
|43|夕食の写真を選ぶ時|269|4|5|18|
|44|届く速さの違う手紙|266|5|7|18|
|45|水族館の質問カード|268|4|6|18|

切符と音声の由来・異なる記憶の保存、実験記録の参照先と他班の確認、写真の許可と経験の正確さ、受け手の状況に合った通信、観察と仮説の区別を続きの段落に追加。新設問14問・計29問、四択の個別解説と本文根拠を保存。

全92文に文別和訳、SVOCM・句節・修飾関係、骨格、文法説明、段落内offsetを付与。This/That/Theseの指す内容、関係節、間接疑問、形式目的語、動名詞、不定詞、受動態、否定と比較を各文で説明。旧構文はpreviousSyntaxで保存。意味・自然さ・一意性はAI執筆者確認で、人間の正式校閲は0題。

空所のない形式であり、出題とレビューにparagraphsを共用。syntaxOffsetBasisと構文offsetBasisはparagraphs。gapSolutionsやreviewParagraphsを追加せず、旧設問の正答を本文へ挿入しない。

## 検証

- TS54件・型検査・Webビルド成功。教材構造監査issuesは0。
- 全文の文区切り・原文offset・文別訳の連結・構文spanの字句と範囲・修飾先の参照を検証。
- 全29問の各選択肢の採点、本文根拠、旧3問の保存済み点数を再計算しないこと、受験履歴の保持と保存往復を検証。
- --batch 41-45を追加。11〜15から今回まで七つのバッチを再生成し、過去の改訂教材・manifestに差分なし。今回も同一データを再現。
- 実機の画面操作は未検証。既知のChromium起動制約があり、構造検査を実機操作の合格とは扱わない。
- 構造検査のみで解説の意味の正確さを保証しない。人間の正式校閲は未実施。

LEVEL2は100題中45題832文を全英文補完。全LEVEL累計80題1590文（LEVEL1=15、LEVEL2=45、LEVEL3=10、LEVEL4=10）。保存済み100/100/10/10題と改訂済み数を区別。LEVEL2全体の文別訳832/1485文、全文一致構文869/1485文。全体監査はanalysis/reading_integrated_audit.json。

原稿はcontent/authoring/reading-enrichment/l2-reference5-additions.jsonとl2-reference5.tsv。再現はpython3 scripts/build_l2_gap5.py --batch 41-45。元教材のハッシュと件数はanalysis/reading_l2_reference5_batch.json。

利用者の継続指示および前回の明示デプロイ指示に従い、同じGitHub r82d2h82rn-prog/Thank-You-tanjukugo のmainへ保存し、Git連携のVercel yukitoshis-projects-2c28f209/tanjukugo 本番へ反映する。公開成功は新コミットのDeployment has completedで確認する。未関連のanalysis/selection_decisions.jsonは含めない。

次はLEVEL2の46〜50題（reading-l2-f05-06〜10、指示語）。元の指示対象・本文・設問を保持して続行する。
