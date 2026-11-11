# 教材制作の引き継ぎ

2026-11-12 JST。作業ブランチは `feat/full-content-production`。元は `feat/content-pipeline-and-practice-flow`、基点コミット e51d57edd430e20a053b6cea202b0e9b2a65b1e8。

## 現在まで

公開保存はユーザー承認後に完了。PR #1: https://github.com/r82d2h82rn-prog/Thank-You-tanjukugo/pull/1 。リモート基点は9b723f696561121467e58131cdfdda22f6ff0520。ローカルCLIにはpush認証がないため、認証済みGitHub連携で保存しています。

- 最新追加: LEVEL 1 SECTION 1とLEVEL 2 SECTION 2に独自200語を制作。累計500語。
- content/word_adoption_plan.csvに3,900語の仮採用・制作台帳。配分800/900/1200/1000、未執筆3,400語。未執筆語の品詞・難易度・SECTION内順は未確定で、正式番号を凍結していない。

- 公式4リストの配布バイト列・版・出所・著作者表示・SHA256・文字コードを保存。公式由来5,619候補を取得し、重複963候補の複数ソース情報を保持。
- NGSL/TSL/BSLは実配布の順位、NAWLは957見出しのみ。NAWLにアルファベット順位を設定しない。BSLの説明1,700語と実ファイル1,744語の差は未解決。
- 既存100単語草稿の掲載を照合。前回のLEVEL 3/4各100語と最新のLEVEL 1/2各100語を独自制作。草稿合計500語、検証用150項目、校閲待ち計650項目。
- 6入試入口・利用条件を確認。第三者英文を含む利用範囲が未確定のため、本文取得・分析は0。入口の行に年度があっても試験分析数に含めない。
- 学習用検証教材150項目と既存履歴は維持。設定の出典画面を実際の調査状況・ライセンス表示に更新。

## 再開手順

1. 最新の `feat/full-content-production` を取得し既存チェックアウトで作業。SPEC.md と docs/CONTENT_SPEC.md が仕様の正本。別worktreeは不要。
2. `npm ci`。`npm run typecheck` / `npm test` / `npm run test:content` / `npm run content:audit`。通常チェックと公開判定を混同しない。
3. 必要な場合だけ `npm run content:import-official`。保存済み配布物をハッシュ照合して再現するオフライン処理で、再実行しても候補の編集判断・件数は変わらない。元ファイルを変更する場合は、現行の公式リンクとライセンスを再確認しmanifestを明示更新。
4. docs/SOURCE_LICENSES.md の未解決事項を確認。語義・例文・IPAの辞書確認は未完了。公式未掲載の新規13語は analysis/dictionary_checks.csv。403だったCambridgeの確認を成功扱いしない。
5. content/review_queue.csv の650項目を校閲。レビュー結果の正本は各JSONのcontentメタデータ。CSVはレビュー用一覧で、単にtrueを書いても実際の確認を済ませたことにはしない。
6. 最優先で単語候補の採否・LEVELを審査し、仮採用台帳の未執筆3,400語分の本文制作を進める。ただし検証用100語がすべて最終採用されるとは限らない。収録目標・SECTION数は変更しない。難しい専門語や基本義で埋めない。
7. 公式リスト由来の候補集合はCC BY-SA 4.0を維持。製品教材への継承範囲・表示・配布形態を確認し、原文の例文や定義をコピーせず独自制作する。
8. 人手確認が済んだSECTION単位を approved.json に移す。既存IDを他語へ流用しない。検証用の置換は同じID・同じ英語・同じkindのみ。試験実装は別工程のままで、教材導入だけで連携済みと報告しない。
9. 入試は各資料について分析利用範囲と第三者部分を特定し、必要手続き・担当者を確認。許諾前に本文をダウンロードしない。許可済みの英文だけ analysis/private/ に置き、exam_sources.csv に実年度・学部・方式・URL・根拠・ハッシュを設定。本文はGitに含めない。
10. `npm run content:analyze`。no_authorized_corpusなら頻度は未検証を維持。原形表は analysis/lemma_forms.json に明示したもののみ。developmentをdevelopに統合しない。熟語検出は候補で人手確認前の確定頻度をnullに保つ。
11. 単語の後に熟語2,000（50個×40SECTION）、長文400（各LEVEL10形式×10題）を制作する。長文画面・色分け描画は未実装で、データ検査成功だけでは演習可能と報告しない。
12. `content:audit` と `content:release-check` を区別。全量・校閲・権利が揃うまで後者は失敗する。CONTENT_STATUS.md、docs/CONTENT_REPORT.md、QA_REPORT.md、進捗・再開手順を実数で更新し、変更をGitHubへコミットする。

現時点の最終不足は正式承認済み基準で3,900語・2,000熟語・400長文。人手未確認の草稿は残数から引きません。

新しい制作バッチはcontent/authoring/word_batch_20261112.tsvの列形式に従い、`python3 scripts/import_authored_words.py PATH`で取り込みます。既存語の上書きは拒否します。`npm run content:plan-words`で台帳を再生成する場合、未確定の配置が変わることがあります。正式承認済みの番号には適用しないでください。
