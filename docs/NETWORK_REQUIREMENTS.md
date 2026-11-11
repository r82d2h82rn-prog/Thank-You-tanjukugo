# 接続調査の現状

2026-11-12 JST。前タスクでの403は過去の観測です。今回、指定4リストの公式サイト・配布CDNへの通常HTTPS接続は成功し、ファイルを取得しました。許可先の回避、中継、TLS検証無効化は行っていません。

- `www.newgeneralservicelist.com` とリンク先 `static1.squarespace.com`: 語彙配布の取得成功。
- 英検、Wiktionary、大学入試センター、東京・京都・大阪・早稲田・慶應: Web取得によって掲載入口または利用条件を確認。試験本文取得の許可を意味しません。
- 慶應の指定旧URLは404。現行公式サイトの学部一般選抜ページに移動しました。
- Cambridge Dictionaryの13個別URL: Web取得は403。回避せず、語義・IPA等の確認を保留しました。
- NASA / World Bank: 今回は未使用。過去の接続結果を現在の事実確認の代わりに使いません。

現在の記録は analysis/source_access.json。前回の記録は source_access_previous.json に保存。`content:probe` は入口への疎通確認で、実ファイルの版・利用条件・権利確認の代わりにはなりません。
