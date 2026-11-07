# Armoured Commander II 日本語化 — 開発メモ（遊ぶ人向けの説明は README.md）

## 調べた結果
- 中身は Python 3.6 ＋ libtcod（tcod 11.4 / libtcod 1.15）。PyInstaller で exe にしてある。言語設定・日本語の訳はゲームに入っていない。
- ゲーム付属の `src\armcom2.py`（約4.3万行、v1.3.8）が exe の中身と同じソース。文字列はソースに直接書かれている。
- 文字は 16列×18行のビットマップフォント（`data\c64_8x8/12x12/16x16_ext.png`）で描いている。日本語の字は入っていない。

## 方式
1. exe の起動スクリプトだけを「`ja\boot.py` を実行する」小さなコードに差し替える（`tools\patch_exe.py`。他の中身はそのまま）。
2. `boot.py` がやること:
   - フォント画像の下に日本語の字（記号・かな・第1水準漢字＋訳文に出る字、約3500字、MS ゴシックの埋め込みビットマップ）を足した `ja\font_NN.png` を使わせ、字の位置を割り当てる
     （libtcod 1.15 は内部で0番を使うので、位置は1つ先を指定する）。
   - 表示する直前に英語→日本語の表（`ja\strings_ja.json`）で置き換える。ゲームは英語の文字列で判定しているので、ソースの文字列は書き換えない。
   - 日本語を含む文字列は1字ずつ `console_put_char` で書く（libtcod の print は全角を2マス進めるため）。`textwrap.wrap` も日本語の字数で折り返す。
   - 表に無かった英語は、ゲーム終了時に `ja\missing.txt` に書き出す（訳し漏れの確認用）。
   - ゲーム本体は付属の `src\armcom2.py` を起動時に読み、boot.py の `_JA_PATCHES`（3か所: 名前の表示・IBM850 変換・日付）をメモリ上で当てて実行する。ソースの写しは作らない。
3. 8x8 フォントでは漢字が潰れるので、ゲームのオプションで 16x16（または 12x12）を選ぶ前提。

## コマンド
- 開発中に入れる: `python tools\build_table.py` → `python tools\build_font.py` → `python tools\install.py`（ゲーム起動中でも訳の表は差し替わる。再起動で反映）
- 配布用: `python tools\make_dist.py`（下の「配布パッチ」）
- 元に戻す: `restore.cmd`（`orig\armcom2.exe` を戻し、ゲームの `ja` フォルダを消す）。Steam の「ファイルの整合性を確認」でも戻る。
- 原本: `orig\armcom2.exe`（md5 47dedc14591bafc17426b9f1c5f38757）、`orig\armcom2.py`。

## 注意
- ゲームが更新されると exe が戻る。日本語化ツールを実行し直す。ソースの直す箇所が見つからなければ boot_log.txt に記録して飛ばす。
- 文字列を組み立てて表示する所（`'Fired ' + 名前` など）は表の完全一致では訳せない。断片ごと訳すか、`boot.py` に型（正規表現）を足す。

## 訳す量（見積もり）
| 対象 | 量 | 優先 |
|---|---|---|
| 画面の文言（ソース内） | 約2,300種・約9,600語 | 必須 |
| 用語集・スキル・チュートリアル・乗員 | 約700件・約14,500語 | 高 |
| キャンペーン説明（週の説明など） | 約1,200件・約21,000語 | 済 |
| 兵器の解説（unit_type_defs） | 約4,400件・約46,000語 | 低（兵器名は英語のままでよい） |

## 訳の作り方（2026-11-03〜）
- `python tools/extract_strings.py` → `work/ui_en.json`（ソースの文字列。`'A' + x + 'B'` は `{0}` 入りの型）と `work/data_en.json`（用語集・スキル・チュートリアル・乗員）。
- 英語は `tr/en/*.txt` に固定（**作り直さない**。訳の行番号がずれる）。訳は `tr/*.tsv` に「行番号<TAB>日本語」。訳語は `tr/terms.md`。
- `python tools/build_table.py` → `ja/strings_ja.json`（完全一致）・`ja/templates_ja.json`（型）。続けて build_font → install。
- `python tools/test_boot.py "英語の文"` でゲームなしに訳の当たり方を試せる。
- 遊んで終了すると、表に無かった英語がゲームの `ja\missing.txt` に出る → `tr/manual_*.json`（{英語: 日本語}、`{0}` 入りの型も可）に足す。
- 日付はソース側で「1944年6月5日」に変えている（boot.py の _JA_PATCHES）。

## 進み具合
- 画面の文言（約2,300種）・用語集・スキル・チュートリアル・乗員の命令とセリフ: 訳済み（2026-11-03）
- キャンペーン名61本（tr/campaign_names.json）、車両名 独・米・英・日・ソの約570台＋愛称（tools/unit_names.py → tr/units_names.json。規則と対応表で生成、型番だけの名前は英語のまま）
- 2026-11-03 プレイ1回目の訳し漏れ（work/missing_play1.txt）に対応: キャンペーン選択の説明59本・地域名・国名・弾種の「名前（略号）」（tr/campaign_desc.json）、チェコの38(t)/35(t)。
  広すぎる型（'{0}, and {1}' など）を build_table.py の BLOCK で外した。「A, B, C」の並びは boot.py が1つずつ訳して「、」でつなぐ。missing.txt から略語とクラッシュ画面の行を除外。
- 2026-11-03 キャンペーンの週ごとの見出し・説明・コメント 1213件（tr/week_01〜21.tsv、英語は extract_strings.extract_weeks() で tr/en/week_*.txt に固定）。
- 兵器解説: tr/unit_001〜044 すべて訳了（1320件）。
- 未: つなぎ合わせて表示する文の一部（missing.txt で拾う）、キャンペーン説明、兵器解説

## 配布パッチ（2026-11-03〜）
- `python tools/make_dist.py` → `dist/ArmCom2_JA_<日付>/` と `.zip`（約125KB）。中身: ArmCom2_JA.exe（日本語化ツール）・元に戻す.cmd・README.txt（`dist_files/README.txt`）・ja\（boot.py・訳の表・font_chars.txt）。
- **ゲームのファイルは入れない**: exe はツールが遊ぶ人の exe を書き換え（元は armcom2.exe.jabak）、ソースは起動時にメモリ上で直し、
  フォントはゲームの c64_*_ext.png ＋その人の Windows の MS ゴシック（無ければ BIZ UDゴシック・游ゴシック・メイリオ）でその場で作る（MS ゴシックの画像は配らない）。
- ツールは `tools/JaPatcher`（C#、.NET Framework 4.7.1 向け＝Windows 10/11 に最初から入っている。21KB）。ビルドは make_dist.py が dotnet で行う（参照アセンブリはこの PC の Reference Assemblies を使い NuGet 不要）。
  `ArmCom2_JA.exe [ゲームのフォルダ] [--restore] [--no-pause]`。exe の書き換えは tools/patch_exe.py と同じ結果（md5 一致を確認）、フォントも Pillow 版と字の位置一致。
- 確認済み: 元の状態から当てる→起動OK、--restore で exe が元の md5 に戻り ja が消える、2回目は「日本語化済み」でそのまま。

## 字体（2026-11-03）
- 日本語を含む行の英数字・記号は全角の字（Ａ、１）で描く（boot.py の put_text の zen。ユーザー指定: 日本語と英数字の字体をそろえる）。英字だけの行は元のC64の字のまま。
- font_chars.txt の先頭は全角スペース（U+3000）。**strip()/Trim() しない**（消えると字の位置が1つずれる。以前の「+1 の補正」はこれが原因だった。C# 版も修正済み）。

## 階級名（2026-11-03）
- 乗員の階級（nation_defs の rank_names、全国）は tr/ranks.json で日本語化（伍長・軍曹…。外国語の原語は出さない）。PrintExtended 経由で T() を通らないため、boot.py が起動時にソースの表示箇所5か所を `_ja_rank(...)` で包む（`rank_name =` の比較行は除外）。

## 2026-11-04 プレイ4回目の訳し漏れ
- tr/manual_05.json: 勲章名（全国）と「勲章名 x N」、乗員能力名のコロン付き（Perception: 等）、Combat Days:、Maximum N、輸送トラックの文、前進射撃の文、狙撃兵のメッセージ（国の形容詞「A Soviet」→「ソ連の」）、国の形容詞。
- 注意: ゲームの ja\missing.txt は積み重なるので、古い分（訳す前に記録）が残る。確認は `python /tmp/chk.py` 方式（各行を今の表に通して変わらないものだけ見る）。元の記録は work/missing_play4.txt。残りは英語のままでよい型番・車両名（wz. 28 など）が中心。
- 日付 "October 5, 1939" 型は未対応（GetDateText 以外の出所）。
