# Aircraft Input Templates

このフォルダには、JSBSim XML生成用の入力テンプレートが含まれています。

## Aircraft_Input_Template.xlsx

**ファイル名**: `Aircraft_Input_Template.xlsx`
**バージョン**: v3 E2E
**更新日**: 2025-10-17

### 概要

RC UAVの機体パラメータをExcel形式で入力し、JSBSim XMLファイルを自動生成するためのテンプレートです。

### 主要シート

| シート名 | 内容 | 記入必須 |
|---------|------|---------|
| T_01_Basic_Info | 機体基本情報（名称、質量、翼面積等） | ✅ 必須 |
| T_02_Mass_Balance | 重心位置、慣性モーメント | ✅ 必須 |
| T_03_Propulsion | 推進系（モーター、プロペラ、ESC） | ✅ 必須 |
| T_04_Control | 操縦面（エルロン、エレベーター、ラダー） | ✅ 必須 |
| T_05_Aerodynamics | 空力係数（CL, CD, Cm等） | ⚠️ 高度 |
| T_06_Landing_Gear | 降着装置（該当する場合） | ⏸️ オプション |

### 使用方法

#### 1. テンプレートのコピー

```bash
cp templates/Aircraft_Input_Template.xlsx my_aircraft_input.xlsx
```

#### 2. パラメータ入力

Excelでファイルを開き、各シートにパラメータを記入します。

**必須項目**:
- T_01_Basic_Info: 機体名、質量、翼面積、翼幅
- T_02_Mass_Balance: 重心位置（CGx, CGy, CGz）、慣性モーメント（Ixx, Iyy, Izz）
- T_03_Propulsion: モーター（Kv、内部抵抗）、プロペラ（直径、ピッチ）、バッテリー（電圧、容量）
- T_04_Control: 各操縦面の面積、偏角範囲、取り付け位置

**高度項目**（最新版対応）:
- T_05_Aerodynamics: 空力係数の詳細設定
  - 基本係数: CL0, CLalpha, CD0, Cmalpha
  - 動的安定性: Cmq, CLq, CLadot
  - 操縦面効果: CLde, Cmde等

#### 3. XML生成

```bash
python src/generate_jsbsim_from_gsheet.py --input my_aircraft_input.xlsx --output aircraft/MyAircraft/
```

### 単位系

すべての入力は以下の単位系に従います:

| パラメータカテゴリ | 単位 |
|------------------|------|
| 長さ | mm |
| 質量 | g |
| 面積 | mm² |
| 角度 | degree |
| 電圧 | V |
| 容量 | mAh |
| モーターKv | RPM/V |
| 抵抗 | Ω |

**注意**: スクリプトが自動的にJSBSim標準単位系（m, kg, rad等）に変換します。

### サンプル

`examples/ExampleAircraft/`フォルダに、200g級RC UAVのサンプル入力があります。

### トラブルシューティング

#### 問題: Excelファイルが開けない
- **原因**: openpyxlパッケージ未インストール
- **解決策**: `pip install openpyxl`

#### 問題: XML生成時にエラー
- **原因**: 必須項目が空欄
- **解決策**: T_01～T_04の必須項目をすべて記入

#### 問題: 生成XMLでJSBSimが起動しない
- **原因**: パラメータ値が物理的に不正
- **解決策**:
  - 質量 > 0
  - 翼面積 > 0
  - 慣性モーメント > 0
  - CGが機体内に存在

### Evidence Level

このテンプレートのパラメータは以下のEvidence Levelで検証されています:

- **L4**: End-to-Endテストで実証済み
- **L3**: 典型的な小型固定翼機の値を採用（CL0, CLalpha, CD0, Cmalpha）
- **L2**: 工学的推定値（慣性モーメント等）

詳細は`docs/technical/evidence_levels.md`を参照してください。

### 参考資料

- [JSBSim公式ドキュメント](http://jsbsim.sourceforge.net/)

---

**作成日**: 2025-10-18
**バージョン**: 1.0
**対応Template**: v3 E2E

---

**© 2025 Yaaasoh. All Rights Reserved.**

本ドキュメントの著作権はYaaasohに帰属します。引用部分については各引用元のライセンスが適用されます。
