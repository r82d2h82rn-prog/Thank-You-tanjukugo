# 単語再選定・追加教材の保存前レビュー

## 作業環境の実数

| 区分 | LEVEL1 | LEVEL2 | LEVEL3 | LEVEL4 |
|---|---:|---:|---:|---:|
| 試用演習に接続した本文付き草稿 | 800 | 900 | 1,200 | 200 |

既存本文2,600語は全フィールド不変。独自補完600語（L3向け500・L4向け100）があり、保存済みの本文は合計3,200語。100語を下位候補として保留し、現在の選定は3,100語。旧L3から80語をL4、旧L4から80語をL3へ移す。教材IDと保存キーを維持し、旧教材・保留語の履歴を別の語に付け替えない。L4は残り800語で、1,000語の全量はまだ未完成。

## 追加教材

- content/authoring/reselection/batch_01.tsv〜batch_05.tsv：L3補完500語。
- content/authoring/reselection/advanced_01.tsv：L4追加100語。
- content/words/reselected_additions.json：追加本文。本文・例文・和訳・用法説明は独自制作。英検の個別語の級・入試頻度は実測済みとして扱わない。
- content/words/selection.json：IDごとの表示配置。原データは上書きしない。

L4の例：abate, acquiesce, adjudicate, bequeath, circumvent, corroborate, exacerbate, exonerate。難しい一般語・抽象語も含む。すべて人手校閲待ちで、正式承認はしていない。

## 検証

型検査、TypeScript10件、Python16件、Webビルドを実行。ブラウザ操作検証は実行環境のChromium socket() EPERMのため未確認。自動検査は語義・自然さ・難易度の人手校閲の代わりではない。

## Webへの反映が止まっている理由

GitHubの自動承認審査が、content/review_queue.csvのアップロードを「この具体的な教材データを公開GitHubへ送る明示承認がない」として拒否した。教材データと出所の一致・個人アカウント情報や学習履歴を含まないこと・既存公開リポジトリであることを確認後も再び拒否。別手段で回避せず、その後ユーザーが「Githubで使えるようにして。反映して。それが終わり次第レベル4全実装」と指示。今回の600語・配置台帳を同じ公開リポジトリへ保存し、続けて残り800語も同じ方法で反映する承認を確認した。

対象保存先：https://github.com/r82d2h82rn-prog/Thank-You-tanjukugo の feat/full-content-production。Git連携によりVercelプレビューを更新する。公開保存すると教材本文を誰でも閲覧できる。一般向けGoogle Play公開や課金の開始は行わない。

## 次の再開操作

公開保存の承認後、今回の600語・配置・アプリ接続をまとめて保存し、Webビルドの成功を確認。次はadvanced_02.tsvから100語ずつ制作し、各バッチでreselect_words.py --build→refresh_content_progress.py→検査→保存→Web反映。L4の既存SECTION番号は新規バッチ追加で変更しない。最終LEVEL4=1,000語。

## 公開対象の縮小

全件の本文を繰り返し含む旧review_queue.csvと旧word_adoption_plan.csvは公開済みの元の版を維持する。今回の本文アップロードは新規600語だけのreselected_additions.jsonと、600語だけのreselection_review_queue.csv。既存本文2,600語は再送も変更もせず、配置変更はIDだけのselection.jsonを使う。旧全件索引は履歴資料であり、現行配置の正本はselection.json。

公開保存は追加本文600語とLEVEL3/4のID配置に限定する。全件の選定理由一覧analysis/selection_decisions.jsonは公開対象から外し、手元の検証資料として保持する。LEVEL1/2の配置と旧全件索引は変更しない。
