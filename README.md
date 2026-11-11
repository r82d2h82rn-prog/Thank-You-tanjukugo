# Thank You単熟語長文3900+

React Native + Expo + TypeScript の英語学習アプリ。完成版を段階的に開発中です。**全量教材・試験・長文・認証・課金が完成したアプリではありません。** 正式な現行仕様は [SPEC.md](SPEC.md)、教材の追加仕様は [docs/CONTENT_SPEC.md](docs/CONTENT_SPEC.md) です。

## 起動と検証

Node.js 22以上 / npm。検証環境は Node 24.22.1、Expo SDK 55、React 19.2、React Native 0.83.10。教材ツールと本番スモークテストにPython 3を使用します。

```bash
cd Thank-You-tanjukugo
npm ci
npm run web
```

既存のチェックアウトで作業し、別worktreeは自動作成しません。Expoはアカウント不要のローカル開発用オフラインモードで起動し、テレメトリを送信しません。依存導入はnpmレジストリを使用し、TLS・整合性確認は維持します。

```bash
npm run typecheck
npm test
npm run test:content
npm run test:e2e
npm run content:import-official
npm run content:plan-words
npm run content:audit
npm run content:analyze
npm run build:web
npm run test:production
```

E2EはChromium `/usr/bin/chromium` を使用します。他環境ではplaywright.config.tsのexecutablePathを変更してください。本番スモークテストはCHROMIUM_PATHにも対応します。dist/ は静的Webビルドであり、自動デプロイは行いません。

公開前には別に `npm run content:release-check` を実行します。**現在は全量未達のためexit 1になります。** 開発用構造検査の成功は、正式教材の品質承認や完成版の合格を意味しません。

## 実装済み

- 正式名称とホワイト×ネイビーのモバイル対応画面、LEVEL/セクション、前回のLEVEL・セクション・形式を保存。
- 検証用100語・50熟語の一覧/独立詳細、前後移動・タッチスワイプ、一覧のフィルタとスクロール位置保持、横断検索。
- 通常4択＋わからない、ランダム/番号順、問題数設定、選択肢の重複防止。
- **回答した同じカードを解説に置換し、専用の次へボタンを置かず、解説カードの広い領域のタップで進む。** 発音・お気に入りはイベント伝播を止める。回答処理の多重実行を防ぎ、解説表示後350msのガードで二重タップによるスキップを防止。
- 誤答の再練習は、対象がすべて2連続正解で習得済みになるまで循環。習得済みになった対象は次の周回から外す。途中終了でも確定済み回答は保存。
- 選択式/記述式それぞれの習得・連続正解・回答履歴・最終回答/習得時刻を分離。不正解とわからないで該当形式のみリセット。
- 開発時だけのPremium検証スイッチによる記述式・お気に入り。熟語は語数と最初の語の頭文字だけをヒントに語別入力。語別の前後空白と大文字小文字を正規化し、明示した正答のみ採点。
- 形式・LEVEL・教材別の習得集計、学習履歴。
- オリジナル合成のタップ・正解・不正解音、Web Speechによる英語発音。それぞれ独立した保存設定。記述式の問題表示時には正答を読み上げない。
- AsyncStorage（WebはlocalStorage）保存、書き込みの直列化、保存失敗と再試行、破損/未知バージョンの保護。保存キー・version:1・既存150個のIDは維持。
- 教材の出典・版・利用条件・検証状態・人手校閲の有無を管理。設定画面から出典/未確認事項を確認可能。
- 公式リスト候補の権利確認付き取り込み、正規化・複数ソース順位保持、許諾済みローカル入試資料の分析、正式教材の検証・取り込み口と全量ゲート。
- 独自単語草稿500語（LEVEL 1:100 / LEVEL 2:200 / LEVEL 3:100 / LEVEL 4:100）を制作。最新追加200語。構造検査済み、**人手校閲は未実施。アプリには未収録。** 公式リスト見出しの照合は本文・発音の検証と区別。詳細は CONTENT_STATUS.md。

Premium検証スイッチは `__DEV__` のみ。本番ビルドでは表示されず、購入処理もありません。OFFや更新で記述式履歴を削除しません。通常練習の中断時は回答済みの結果を保存します。試験の仮状態・巻き戻しとは異なり、試験自体が未実装です。

## 現在の制限

初回診断、8択/時間制限付き試験、セクション/LEVELの独立解放・永久合格・称号は未実装。長文の制作・演習画面、グラフ、認証・クラウド同期・データ移行・課金/復元・アカウント削除も未実装。Android音声・EASビルド・実機、Safari/iPhoneは未検証です。

保存は現在の端末・ブラウザ・オリジン内のみ。別のプレビューURL・端末には移らず、ブラウザデータを削除すると失われます。バックアップ機能は未実装です。Web音声の実際の可聴性・音質は端末・ブラウザ・ミュート設定に依存します。人による実聴テストは未実施です。

## 教材と分析の再開

単語3,900語の仮採用・制作台帳はcontent/word_adoption_plan.csv。LEVEL配分は800/900/1200/1000、本文のある草稿500語、台帳上の未執筆3,400語。仮配置は最終難易度・正式番号ではなく、未執筆の行は教材として読み込みません。公開保存はユーザー承認後に完了し、作業中PRは https://github.com/r82d2h82rn-prog/Thank-You-tanjukugo/pull/1 です。

- 現在アプリ内で利用できる検証用教材150件、別管理の単語草稿500語。正式承認済みは0件です。目標は3,900語・2,000熟語・400長文のままです。
- 公式4リストを取得し、重複統合後5,619候補を保存。配布ファイルのSHA256・版・文字コード・ライセンスを記録。NAWL順位は未取得、BSLは説明の1,700語と実データ1,744語に差があります。6入試入口・利用条件は確認、本文分析は利用範囲未確定により0試験/0大学/0語。
- 現在の接続状況は docs/NETWORK_REQUIREMENTS.md。利用条件の記録は docs/SOURCE_LICENSES.md と content/sources.json。
- 今回の報告は docs/CONTENT_REPORT.md、詳細手順は docs/CONTENT_PROGRESS.md。開発計画は IMPLEMENTATION_PLAN.md、現状は PROGRESS.md、検査結果は QA_REPORT.md。
- sample: src/data/entries.json、出典・状態: content/provenance.json、草稿: content/words/drafts.json、正式導入口: content/words/approved.json / content/idioms/approved.json。既存IDを別の語へ再利用しないでください。
- 正式データの承認と出典条件を `src/content.ts` で検証し、承認済み100語/50熟語のSECTIONを単位として検証用教材から切り替えます。同一IDの文章改訂は同じ英語・同じkindに限り、別語へのID流用を拒否します。旧教材の履歴キーは削除せず、新語へ付け替えません。人手校閲未完了の草稿を正式教材として自動導入しません。

## Vercelと公開

vercel.json はFramework Other、`npm ci`、`npm run build:web`、出力distの設定。Vercel認証・プロジェクト連携がないため、実際のデプロイと公開URLはありません。認証後のプレビューには `vercel deploy` を使用し、`--prod` の本番公開は行いません。初回ImportのDeployが本番デプロイになり得る点に注意してください。

本番課金、有料外部契約、Google Play一般公開は別途の明示承認まで実行しません。既存の docs/FINAL_SPEC.md と docs/IMPLEMENTATION_STATUS.md は初期版の履歴資料であり、現状の仕様・進捗にはルートのSPEC.md/PROGRESS.mdを参照してください。
