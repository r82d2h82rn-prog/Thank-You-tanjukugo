# 本文制作の再開地点

計測日時: 2026-11-12T00:57:53.957164+00:00

ユーザーの指示は全量追加。公開GitHub保存の明示承認は継続しています。小さな追加報告だけで依頼を完了扱いにしません。

本文付き単語草稿: 2500 / 3,900。LEVEL別 [800, 900, 700, 100]。未執筆 [0, 0, 500, 900]。

content/authoring/words_l*_s*.tsvが今回の独自執筆バッチ。各ファイルの英語・和訳・IPA・用法解説は手作りで、テンプレートの語句差し替えによる水増しをしていません。

次は未完了の単語SECTIONの本文制作。既存語・既存IDの上書きはimport_authored_words.pyが拒否。各SECTIONは100語、品詞順は動詞→名詞→形容詞→副詞→その他。

取り込み後にrefresh_content_progress.pyで計測し、内容をGitHubへ保存。人手校閲済み・正式承認済みへ機械的に変更しない。単語全量の後に熟語2,000、長文400の制作へ進む。

GitHub CLIのpush認証はないため、認証済みGitHub連携のcreate_tree/create_commit/update_refを使用。ローカルとリモートのtree SHAを照合する。リモートブランチfeat/full-content-production、PR #1。現在のGitHub基点はgitのorigin/feat/full-content-productionから取得する。

大学本文は別途利用条件が確定したものだけ分析。架空の頻度を作らない。ブラウザのsocket() EPERMは未解消。
