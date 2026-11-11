# 教材調査に必要な接続

2026-11-12 JST。現在のネットワークはrestrictedで、下記11ホストはHTTPS CONNECT段階で403拒否。分析対象の公式本文は取得していない。再試行を繰り返したり、許可済みホストを中継させて回避していない。

環境設定のインターネット許可先へ、既存の許可先を保持したまま次を追加する必要がある。

```text
www.newgeneralservicelist.com
en.wiktionary.org
www.eiken.or.jp
www.dnc.ac.jp
www.u-tokyo.ac.jp
www.kyoto-u.ac.jp
www.osaka-u.ac.jp
www.waseda.jp
www.keio.ac.jp
science.nasa.gov
data.worldbank.org
```

NGSL/NAWL/TSL/BSLは同一ホスト。1ホストにつき1つの入口ページの接続を調べたもので、全パスの公開状態・正しいURL・年度・資料内容・バージョンを確認したものではない。証拠は analysis/source_access.json。

設定ドラフトの読み取りツールは「current environment draft could not be verified」を返した。最新の保存済み許可先を確認できないため、未知の設定を置き換える更新は行っていない。自動承認レビューによる拒否ではなく、ネットワークの403と設定サービスの読み取りエラーである。

追加後に `npm run content:probe` を実行して接続を確認する。到達可能になっても利用条件を確認するまで候補・本文の取り込み許可を設定しない。NGSL等の実ファイルが別のCDNや配布先にある場合、そのURLと必要なドメインを観測してから追加する。
