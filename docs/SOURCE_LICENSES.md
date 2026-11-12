# 出典・利用条件の確認記録

2026-11-12 JST。今回確認したのは公式リストの配布・利用条件、入試掲載入口・利用規定です。条件確認と英文本文の分析を区別します。

| 資料 | 実取得・確認 | 利用条件・未解決事項 |
|---|---|---|
| [NGSL 1.2](https://www.newgeneralservicelist.com/new-general-service-list) | 2,809見出しとSFI順位 | 公式ページにCC BY-SA 4.0。Browne / Culligan / Phillipsを表示 |
| [NAWL 1.2](https://www.newgeneralservicelist.com/new-academic-word-list) | 957見出し、頻度順位は未取得 | CC BY-SA 4.0。統計リンクは学習辞書へ遷移したためアルファベット配布版を使用。アルファベット順を順位にしない |
| [TSL 1.2](https://www.newgeneralservicelist.com/toeic-service-list) | 1,250見出しと順位 | CC BY-SA 4.0。Browne / Culliganを表示。配布CSVはWindows-1252 |
| [BSL 1.2](https://www.newgeneralservicelist.com/business-service-list) | 1,744見出しと順位 | CC BY-SA 4.0。ページの説明1,700語との違いは未解決。機械的に44語を削らない |
| [Wiktionary](https://en.wiktionary.org/wiki/Category:English_phrasal_verbs) | カテゴリと[利用規約7](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use)を閲覧 | 今回は候補の大量抽出、定義・例文・発音音源の取り込みを行っていない。本文のCC BY-SA、個別履歴・第三者由来の追加条件を別途確認 |
| [英検](https://www.eiken.or.jp/eiken/exam/) | 3級〜1級、準2級プラスの案内入口 | 難易度の参考。本文・設問・正答の転載、頻度コーパスの取り込みは0 |
| [NASA](https://science.nasa.gov/) / [World Bank](https://data.worldbank.org/) | 今回は未使用 | 第三者資料・データセットごとの条件は未確認。長文制作時に確認する |

4リストは合計6,760行、重複統合後の公式由来候補は5,619語。複数リストにある候補は963語。既存の独自候補・今回の追加候補も含む候補表全体は5,635語で、最終教材数とは異なります。

配布物の権利表示・改変内容・配布URL・ハッシュは [content/upstream/README.md](../content/upstream/README.md) と manifest.json に保存。正規化済み候補一覧・仮採用台帳・派生する除外一覧とその改変部分はCC BY-SA 4.0に従って提供します。ライセンスの[条件](https://creativecommons.org/licenses/by-sa/4.0/)には著作者表示、変更の明示、継承、追加制限の禁止が含まれます。アプリ全体を自動的に同ライセンスと断定せず、教材集合における継承範囲は商用公開前の確認事項として残します。課金・DRMを含む配布形態もその際に確認します。

## 入試資料

| 提供者 | 実際に確認した入口・利用条件 | 判断と不足 |
|---|---|---|
| 大学入試センター | [過去3年](https://www.dnc.ac.jp/kyotsu/kakomondai/index.html)、[利用規定](https://www.dnc.ac.jp/about_site.html) | 2024〜2026の掲載を確認。試験問題は事前申請制、第三者部分は別許諾。今回のコーパス利用に必要な手続きが未確定のため本文分析保留 |
| 東京大学 | [掲載ページ](https://www.u-tokyo.ac.jp/ja/admissions/undergraduate/e01_04.html)、[二次利用規定](https://www.u-tokyo.ac.jp/content/400243232.pdf) | 2024〜2026。大学著作部分は条件付き利用可、出所・改変の表示、公表後1か月以内の利用報告等を規定。第三者英文の利用範囲は未確定 |
| 京都大学 | [2026資料ページ](https://www.kyoto-u.ac.jp/ja/admissions/undergrad/past-eq/r8-eq)、[利用規定](https://www.kyoto-u.ac.jp/ja/admissions/undergrad/past-eq/copyright-policy) | 2026英語の公開はIII・IVのみ。大学著作部分は条件付き利用と報告、第三者部分は別許諾。非公開I・IIを取得・復元しない |
| 大阪大学 | [掲載入口](https://www.osaka-u.ac.jp/ja/admissions/faculty/general/pastexam-answer)、[2025-03-28利用規定](https://www.osaka-u.ac.jp/ja/admissions/faculty/general/files/nyushi_mondai_riyou20250328.pdf/@@download/file) | 大学著作部分は条件付き利用可。公表後1か月以内の申請書・成果物提出等を規定。今回は取得画面から利用可能年度を確定できず、空欄を維持 |
| 早稲田大学 | [学部別掲載と二次利用注意](https://www.waseda.jp/inst/admission/undergraduate/past-test/) | 2024〜2026の各学部掲載を確認。利用者自身による著作権許諾処理が必要。掲載入口の閲覧を学部本文の分析と数えない |
| 慶應義塾大学 | [現行入口](https://www.keio.ac.jp/ja/admissions/faculty/examinations/general-admissions/)、[2026資料・二次利用注意](https://www.keio.ac.jp/ja/admissions/faculty/examinations/general-admissions/question-2026/)、[2025資料](https://www.keio.ac.jp/ja/admissions/faculty/examinations/general-admissions/question-2025/) | 指定旧URLは404。現行公式入口で2025・2026掲載を確認。2026ページは利用者による著作権許諾処理を求める。本文分析保留 |

今回、入試本文の機械取得・分析は0試験、0語。必要な許諾や権利範囲を確認できていない英文を取り込んでいません。これは各大学がすべての統計的分析を一律禁止しているという法的結論ではなく、本追加仕様5.1/16.3に従う保留判断です。分析範囲の確認、第三者著作部分の除外・許諾、必要な報告の担当決定後に、対象を資料単位で設定します。連絡・申請・報告の送信は行っていません。

## 独自制作

- original-sample-v1: 既存100語・50熟語。学習履歴のIDを維持。正式採否・人手校閲は未完了。
- original-draft-v2: 既存100語の草稿。公式リストの見出しと照合して複数出典を追記。意味・例文・和訳・IPAは独自制作のまま。
- original-draft-v3: 新規LEVEL 3/4各100語。意味・品詞・IPA・例文・和訳・個別用法解説を独自制作。187語が指定リストに見出し一致、13語は未掲載。辞書確認を試みた13ページは403だったため、確認済みにしていない（analysis/dictionary_checks.csv）。

辞書や他社教材の定義・例文・和訳・録音音声を大量転載していません。人手校閲・最終的な権利確認が済むまで approved.json に移しません。出典確認が済んだことだけで教材の正確性や難易度が承認されたとは扱いません。

- original-draft-v4: 最新追加200語。LEVEL 1 SECTION 1とLEVEL 2 SECTION 2。意味・品詞・IPA・独自例文・和訳・用法説明を制作。198語は指定リスト見出しと一致、tired / willingは形容詞としての独自追加で照合・採否は未確定。草稿は累計500語、正式承認0です。
