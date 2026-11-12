# 本文制作の再開地点

計測日時: 2026-11-12T09:24:30.036735+00:00

ユーザーの指示は全量追加。公開GitHub保存の明示承認は継続しています。小さな追加報告だけで依頼を完了扱いにしません。

本文付き単語草稿: 3900 / 3,900。LEVEL別 [800, 900, 1200, 1000]。未執筆 [0, 0, 0, 0]。

content/authoring/words_l*_s*.tsvが今回の独自執筆バッチ。各ファイルの英語・和訳・IPA・用法解説は手作りで、テンプレートの語句差し替えによる水増しをしていません。

再選定の正本はcontent/words/selection.json、基準はcontent/authoring/reselection/policy.json。既存2,600語は不変。新規本文は同フォルダのbatch_*.tsv（LEVEL3補完500語）とadvanced_*.tsv（LEVEL4追加）。100語ごとにcheckpoint_reselection.pyで検査して保存し、reselect_words.py --buildで配置台帳を更新する。refresh_content_progress.pyで実数を更新。旧import_authored_words.pyでは配置を変更しない。

取り込み後にrefresh_content_progress.pyで計測し、内容をGitHubへ保存。人手校閲済み・正式承認済みへ機械的に変更しない。ユーザーの追加指示に従いLEVEL3熟語700個・LEVEL4熟語500個も実装。熟語は合計2,000個。長文は未制作。

GitHub CLIのpush認証はないため、認証済みGitHub連携のcreate_tree/create_commit/update_refを使用。ローカルとリモートのtree SHAを照合する。リモートブランチfeat/full-content-production、PR #1。現在のGitHub基点はgitのorigin/feat/full-content-productionから取得する。

大学本文は別途利用条件が確定したものだけ分析。架空の頻度を作らない。ブラウザのsocket() EPERMは未解消。全量単語の公開済み基点は0f17af7。熟語の再開情報はanalysis/idiom_checkpoint.json。
