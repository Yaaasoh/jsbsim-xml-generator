# JSBSim XML Generator for RC UAV

RC機体からJSBSim用XMLファイルを自動生成するツールです。**2つの入力方式**をサポート:

1. **Excel→JSBSim変換**: Excelテンプレートで機体パラメータを入力
2. **FMS→JSBSim変換**: Flying Model Simulator (.par) ファイルから変換

## 特徴

### 共通機能
- ✅ **自動単位変換**: mm/g/degree → m/kg/rad等、JSBSim標準単位系へ自動変換
- ✅ **典型的な空力係数**: 小型固定翼機の標準的な値をデフォルト提供
- ✅ **動的安定性対応**: Cmq, CLq, CLadot等をサポート
- ✅ **JSBSim統合検証済み**: トリム収束・10秒間安定飛行を確認

### Excel変換 (推奨: 新規機体作成時)
- ✅ **直感的な入力**: Excelテンプレートで機体パラメータを入力
- ✅ **ガイド付き**: 各セル に入力ガイドと典型値を記載

### FMS変換 (Legacy: 既存FMSデータ移植時)
- ✅ **FMS .parファイル対応**: Flying Model Simulator形式の機体データを変換
- ✅ **3段階パイプライン**: パース → 微係数計算 → XML生成
- ✅ **Evidence Level記録**: データ信頼性レベルを自動記録 (L1/L2/L3/L6)

## ⚠️ 重要: デフォルト値について

**サンプル機体のデフォルト値は参考値です**:

- **Evidence Level**: L2 (理論値/文献値)
- **情報源**: 航空工学文献・小型固定翼機の典型値
- **⚠️ 飛行試験未実施**: デフォルト値は飛行試験による検証を受けていません

**ユーザーは必ず**:
1. 自分の機体パラメータに置き換えてください
2. 飛行試験でパラメータ調整を行ってください
3. パラメータ調整にはPARAMETER_TUNING_GUIDE.mdを参照してください

## クイックスタート

### 必要な環境

- Python 3.8以上
- JSBSim 1.1.0以上
- FlightGear（オプション、可視化に使用）

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/[username]/jsbsim-xml-generator.git
cd jsbsim-xml-generator

# 依存パッケージをインストール
pip install -r requirements.txt

# 環境設定（初回のみ）
python setup.py
```

**setup.pyの機能**:
- ✅ 自動環境検出（OS, Python, FlightGear）
- ✅ 設定ファイル生成（config.yaml）
- ✅ 必要ディレクトリ作成（output/, logs/ 等）

詳細は [config/README.md](config/README.md) を参照してください。

### 使用方法

このツールは**2つの入力方式**をサポートしています。用途に応じて選択してください。

---

## 方式1: Excel→JSBSim変換 (推奨: 新規機体作成時)

### 1. テンプレートをコピー

```bash
cp templates/Aircraft_Input_Template.xlsx my_aircraft.xlsx
```

### 2. 機体パラメータを入力

Excelでファイルを開き、以下のシートに機体パラメータを記入:

- **T_01_Basic_Info**: 機体名、質量、翼面積、翼幅
- **T_02_Mass_Balance**: 重心位置、慣性モーメント
- **T_03_Propulsion**: モーター、プロペラ、バッテリー
- **T_04_Control**: 操縦面（エルロン、エレベーター、ラダー）

### 3. JSBSim XMLを生成

```bash
python src/excel_to_jsbsim/generate_jsbsim_from_gsheet.py --input my_aircraft.xlsx --output aircraft/MyAircraft/
```

### 4. JSBSimで動作確認

```python
import jsbsim

fdm = jsbsim.FGFDMExec('.')
fdm.load_model('MyAircraft')
fdm.run_ic()

print("Aircraft loaded successfully!")
```

---

## 方式2: FMS→JSBSim変換 (Legacy: 既存FMSデータ移植時)

Flying Model Simulator (.par) 形式の機体データがある場合はこの方式を使用します。

### 1. FMS .parファイルを準備

```bash
# 既存の.parファイルを examples/ディレクトリに配置
# または任意のパスを指定
```

### 2. 変換を実行

```bash
python src/fms_to_jsbsim/run_full_pipeline.py examples/my_aircraft.par output/MyAircraft_FMS
```

**出力ファイル**:
- `output/MyAircraft_FMS/MyAircraft_FMS.xml` - JSBSim XML
- `output/MyAircraft_FMS/parsed_data.json` - パース済みデータ
- `output/MyAircraft_FMS/derived_parameters.json` - 計算済み微係数
- `output/MyAircraft_FMS/*.txt` - 変換レポート

### 3. JSBSim用にコピー

```bash
mkdir -p aircraft/MyAircraft_FMS
cp output/MyAircraft_FMS/MyAircraft_FMS.xml aircraft/MyAircraft_FMS/
```

### 4. JSBSimで動作確認

```bash
python tests/test_jsbsim_load.py MyAircraft_FMS
```

---

### サンプル機体

#### Excel変換サンプル
`examples/ExampleAircraft_Excel/` に200g級RC UAVのサンプルがあります:

```bash
python tests/test_jsbsim_load.py ExampleAircraft_Excel
```

詳細は[examples/README.md](examples/README.md)を参照してください。

## テスト

このプロジェクトには**10種類のテストスクリプト**が含まれています:

### 基本テスト
- **test_jsbsim_load.py**: JSBSim XML読み込みテスト（両方式対応）
- **test_unit_conversion.py**: 単位変換正確性テスト（27テストケース）

### Excel変換テスト (8 tests)
- **test_xml_generation.py**: Excel → XML生成テスト
- **test_e2e_flight.py**: E2Eフライトテスト (Excel → XML → Flight)
- **test_e2e.py**: レガシーE2Eテスト
- **test_trim_manual.py**: 手動トリム探索（External Reactions対応）
- **test_trim_stability.py**: トリム・安定性テスト（Traditional Engine用）
- **test_trim_diagnostic.py**: トリム診断ツール

**Test Coverage**: 100% (8/8 critical tests implemented)

詳細は[tests/README.md](tests/README.md)を参照してください。

## ドキュメント

### ユーザー向け
- [テンプレート使用方法](templates/README.md)
- [サンプル機体](examples/README.md)
- [ユーザーガイド](docs/user_guide/)

### 技術ドキュメント
- [技術ドキュメント](docs/technical/)

## プロジェクト構成

```
jsbsim-xml-generator/
├── README.md                    ← 本ファイル
├── LICENSE                      ← ライセンス
├── requirements.txt             ← 依存パッケージ（2つの入力方式対応）
├── setup.py                     ← 環境セットアップスクリプト（初回実行）
├── config.yaml                  ← ユーザー環境設定（自動生成）
├── config/                      ← 設定管理
│   ├── config.default.yaml      ← デフォルト設定テンプレート
│   ├── README.md                ← 設定ガイド
│   ├── examples/                ← プラットフォーム別設定例
│   ├── excel_to_jsbsim/         ← Excel変換設定（空）
│   └── fms_to_jsbsim/           ← FMS変換設定
│       └── aerodynamic_assumptions.yaml  ← 空力係数推定設定
├── src/                         ← Pythonスクリプト
│   ├── excel_to_jsbsim/         ← Excel→JSBSim変換
│   │   ├── generate_jsbsim_from_gsheet.py  ← メイン生成スクリプト
│   │   ├── config_manager.py    ← 設定管理モジュール
│   │   ├── unit_conversion.py   ← 単位変換モジュール
│   │   └── set_default_values.py ← デフォルト値設定
│   └── fms_to_jsbsim/           ← FMS→JSBSim変換
│       ├── run_full_pipeline.py ← フルパイプライン実行
│       ├── parse_par_file.py    ← .parファイルパーサー
│       ├── calculate_derivatives.py  ← 空力微係数計算
│       ├── generate_xml.py      ← XML生成
│       └── jsbsim_trim_wrapper.py   ← トリム計算支援
├── templates/                   ← 入力テンプレート
│   └── Aircraft_Input_Template.xlsx  ← Excel入力テンプレート
├── examples/                    ← サンプル機体
│   └── ExampleAircraft_Excel/   ← Excel変換サンプル（200g級RC UAV）
├── aircraft/                    ← 生成されたJSBSim XMLファイル
├── output/                      ← FMS変換出力（中間ファイル含む）
├── engines/                     ← エンジンファイル（空）
├── tests/                       ← テストスクリプト
│   ├── test_jsbsim_load.py      ← 基本テスト（両方式共通）
│   ├── test_unit_conversion.py  ← 単位変換テスト
│   ├── excel_to_jsbsim/         ← Excel変換テスト（移行予定）
│   └── fms_to_jsbsim/           ← FMS変換テスト（サンプルなし、ユーザー提供 .par ファイルで使用可能）
└── docs/                        ← ドキュメント
    ├── user_guide/              ← ユーザーガイド
    ├── technical/               ← 技術ドキュメント
    └── development/             ← 開発者向け
```

## 動作確認環境

| 項目 | バージョン |
|------|-----------|
| Python | 3.8以上 |
| JSBSim | 1.1.0以上 |
| openpyxl | 3.0.0以上 |
| pandas | 1.3.0以上 |
| numpy | 1.21.0以上 |
| scipy | 1.7.0以上 |

## ライセンス

このプロジェクトは**MIT License**の下で公開されています。

### 依存パッケージライセンス

| パッケージ | ライセンス | 互換性 |
|-----------|-----------|--------|
| openpyxl | MIT License | ✅ Compatible |
| pandas | BSD 3-Clause License | ✅ Compatible |
| numpy | BSD License | ✅ Compatible |
| scipy | BSD License | ✅ Compatible |
| JSBSim | LGPL 2.1+ | ✅ Compatible* |

**\*JSBSim互換性注記**: JSBSim（LGPL 2.1+）は外部ライブラリとして動的リンクで使用します。ユーザーは JSBSim を別途インストールし、LGPL条項に従う必要があります。

### 外部データソース

このプロジェクトは以下の外部データを参照しています:

- **JSBSim公式ドキュメント** (LGPL 2.1+)
  - 使用形態: XMLフォーマット仕様の参照

- **航空工学文献**: 公開ドメインの空力係数理論値
  - 使用形態: 典型的な小型固定翼機の値を参考

詳細は[LICENSE](LICENSE)を参照してください。

## トラブルシューティング

### JSBSimがモデルを読み込めない

**症状**: `Could not open file: MyAircraft.xml`

**解決策**:
1. カレントディレクトリが`aircraft/`の親ディレクトリにあるか確認
2. `aircraft/MyAircraft/MyAircraft.xml`が存在するか確認

### トリムが収束しない（Manual Trim Search使用時）

**症状**: `test_trim_manual.py`でもwdot/qdotが目標値に収束しない

**主要原因**:

#### 1. 空力係数の妥当性確認（最重要・Priority 1）

自動計算テンプレートの生成値が**過度に強い安定性**を持つ場合があります。

**診断方法**:
```bash
python tests/test_trim_diagnostic.py MyAircraft
```

**典型的な問題**:
- **CL0が高すぎる**: 一般的な範囲 0.0-0.1（翼型による）
- **Cmalphaが強すぎる**: 一般的な範囲 -0.3 to -0.8（縦安定性）
- **Cm_deが強すぎる**: 一般的な範囲 -0.3 to -0.6（昇降舵効き）
- **CLalphaが高すぎる**: 一般的な範囲 4.0-5.5（揚力傾斜）

**対策**:
航空工学の標準的な範囲と比較し、過度に大きな値がないか確認してください。
特にCmalpha（縦安定微係数）が強すぎると、trim時にpitch momentが釣り合いません。

#### 2. テスト時の推力設定（Priority 2）

**問題**: 初期値throttle 50-100%からテスト → 推力支援飛行モード

**対策**: テスト時に絞った値（10-30%）から開始
```bash
# test_trim_manual.py は自動的に10-50%の範囲でテスト
python tests/test_trim_manual.py MyAircraft 15
```

**推力と揚力のバランス** (JSBSimシミュレーション上):
- 推力/重量比が0.05-0.15程度で純粋な空力飛行モデルとして動作
- T/W > 0.5の場合でも、テスト時に適切な推力範囲（10-30%）を使用することで正しいtrim pointを探索可能
- **注**: 実機では風・乱流等の影響があるため、シミュレーション結果と実機の挙動は異なる場合があります

**注**: 高いT/W比（>0.5）自体は問題ではありません。重要なのは**テスト時に適切な推力範囲を使用**することです。

### ⚠️ JSBSim Built-in Trimが失敗する（External Reactions使用時）

**症状**: `fdm.do_trim(2)` が `Trim Failed` を返す

**原因**:
- このテンプレートで生成されたXMLは **External Reactions** 方式を使用
- JSBSim built-in trim (`FGTrim`) は External Reactions と**互換性がありません**

**これは既知の制約であり、バグではありません。**

**解決策**: Manual Trim Search（手動トリム探索）を使用

```python
# tests/test_trim_manual.py を使用
python tests/test_trim_manual.py MyAircraft 15

# または scipy.optimize で手動実装
from scipy.optimize import fsolve

def trim_cost(x, fdm, target_speed):
    elevator, throttle = x
    fdm['fcs/elevator-cmd-norm'] = elevator
    fdm['fcs/throttle-cmd-norm'] = throttle
    fdm.run()

    wdot = fdm['accelerations/wdot-ft_sec2']
    qdot = fdm['accelerations/qdot-rad_sec2']

    return [wdot, qdot]

# トリム探索
result = fsolve(trim_cost, [0.0, 0.5], args=(fdm, 15.0))
```

**背景**:
- JSBSim trim algorithmは traditional engine/propeller を想定
- External Reactionsの推力モデルでtrim solverが混乱
- 6軸完全モデル実現のためExternal Reactions採用

詳細は[examples/README.md](examples/README.md)のトラブルシューティングセクションを参照してください。

## コントリビューション

プルリクエスト歓迎！Issue報告やプルリクエストはGitHubリポジトリまでお願いします。

## 謝辞

このプロジェクトは以下のツールを使用しています:

- **JSBSim**: オープンソース飛行力学シミュレーター
- **FlightGear**: オープンソースフライトシミュレーター（オプション）

## 参考資料

- [JSBSim公式サイト](http://jsbsim.sourceforge.net/)
- [JSBSim Reference Manual](http://jsbsim.sourceforge.net/JSBSimReferenceManual.pdf)

---

**バージョン**: 1.0
**最終更新**: 2025-10-19
**入力方式**: Excel→JSBSim + FMS→JSBSim
**対応JSBSim**: 1.1.0以上
