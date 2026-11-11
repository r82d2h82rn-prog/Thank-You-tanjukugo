# 教材工程の再開手順

集計と件数: ../CONTENT_STATUS.md。最優先の外部前提: NETWORK_REQUIREMENTS.md。

1. `git checkout feat/content-pipeline-and-practice-flow` を使う。既存チェックアウトで作業し、別worktreeを自動作成しない。
2. `npm ci`、`npm run typecheck`、`npm test`、`npm run test:content`、`npm run content:audit` を実行。
3. ネットワーク設定変更後に `npm run content:probe`。現在の接続失敗記録を、資料を調査済みという意味で使わない。
4. 公式の利用条件を確認し、content/sources.json の根拠、版、許可範囲を更新。内容の未確認状態で許可フラグをgrantedに書き換えない。
5. 利用可能なリストを `lemma,rank`（またはword,rank）のUTF-8 CSVに正規化し、`python3 scripts/content_pipeline.py import-candidates PATH --source ngsl --kind word` で取り込む。複数ソースの順位・由来を保持し、同一ソース内で競合する順位は拒否する。訳文・例文・音声の権利は別に確認する。
6. 入試本文は許諾がある場合だけ分析用のローカル領域に置く。analysis/private/ はGit除外。分析資料ごとの年度・大学・学部・方式・科目・URL・許諾根拠・SHA256を exam_sources.csv に記録。掲載入口の行を実際の試験として数えない。
7. `npm run content:analyze`。実データがないとno_authorized_corpusと空の単語頻度を出力する。現在の0試験を分析済みと報告しない。合成テストの大学名・英文はtests内だけで使い、実績に含めない。
8. 草稿100語をレビューし、公式情報の裏付けを付ける。採用リストを増やして独自例文等を制作。IDの再利用は禁止。部分的な正式データを入れるとSECTION不完全が検出されるので、校閲と承認はSECTION単位で揃える。
9. 正式データは content/words/approved.json と content/idioms/approved.json に保存。アプリはsource条件と承認状態を検証し、同一ID・同一英語の検証教材を正式教材に置き換える。異なる語へのID流用を拒否。
10. 長文は content/readings/approved.json のスキーマに従い制作。長文画面との接続は未実装なので、データ検査成功だけで利用可能と報告しない。
11. `npm run content:audit` と `npm run content:release-check` を分けて実行。QA_REPORT.md、CONTENT_STATUS.md、PROGRESS.md を実数で更新し、検証済みの単位をコミットしてGitHubに記録する。

原形変換は analysis/lemma_forms.json に明示されたもののみ。developとdevelopmentを同一化しない。熟語検出は活用・最大3語の挿入を許す候補検出であり、句境界や意味の妥当性を自動確定するものではない。人手確認前は熟語の確定頻度をnullに維持する。

分析スコアの暫定仕様は30%正規化入試頻度・25%大学年度の広がり・25%一般/学術重要度・20%LEVEL適合。現段階では後半2指標の根拠が不足し、総合スコアを算出していない。実測と推定を別フィールドで維持する。
