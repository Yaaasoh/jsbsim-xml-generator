# JSBSim Standard Directory Structure

JSBSimの標準ディレクトリ構造と、このプロジェクトでの実装方法を説明します。

## JSBSim標準ディレクトリ構造

JSBSimは以下のディレクトリ構造を期待します:

```
project_root/
├── aircraft/         ← 機体定義XMLファイル
│   └── AircraftName/
│       └── AircraftName.xml
├── engines/          ← エンジン定義XMLファイル
│   └── engine_name.xml
├── systems/          ← システム定義XMLファイル（オプション）
│   └── system_name.xml
└── scripts/          ← スクリプトファイル（オプション）
    └── script_name.xml
```

### ディレクトリの役割

#### aircraft/

機体の主要定義XMLファイルを格納します。

**構造**:
```
aircraft/
└── ExampleAircraft/
    └── ExampleAircraft.xml  ← メインXMLファイル
```

**内容**:
- `<metrics>`: 翼面積、翼幅、参照点
- `<mass_balance>`: 質量、重心位置、慣性モーメント
- `<ground_reactions>`: 着陸装置（該当する場合）
- `<propulsion>`: 推進系（エンジン・推力テーブル）
- `<flight_control>`: 操縦系統（FCS）
- `<aerodynamics>`: 空力係数（CL, CD, Cm等）

#### engines/

エンジン定義XMLファイルを格納します。

**このプロジェクトでの実装**:
- 電動モーター推進系を使用
- エンジンXMLファイルは不要（推力テーブルを機体XMLに統合）

**従来型エンジンの例**:
```xml
<piston_engine name="engine_name">
  <displacement unit="IN3"> 91 </displacement>
  <maxhp> 10.0 </maxhp>
  <maxrpm> 10000 </maxrpm>
</piston_engine>
```

#### systems/ (オプション)

システム定義XMLファイルを格納します。

**例**:
- 自動操縦システム
- 電力システム
- 燃料システム

**このプロジェクトでの実装**: 現時点では未使用

#### scripts/ (オプション)

JSBSimスクリプトファイルを格納します。

**用途**:
- 自動化されたシミュレーション実行
- テストシナリオ

**このプロジェクトでの実装**: Pythonスクリプトを使用（tests/）

## このプロジェクトでの実装

### ディレクトリ構成

```
delivery_repo_draft/
├── aircraft/
│   └── ExampleAircraft/          ← サンプル機体
│       └── ExampleAircraft.xml
├── engines/
│   └── README.md             ← 電動モーター推進系の説明
├── src/
│   └── generate_jsbsim_from_gsheet.py  ← XML生成スクリプト
├── tests/
│   ├── test_jsbsim_load.py
│   └── test_trim_stability.py
└── templates/
    └── Aircraft_Input_Template.xlsx
```

### XML生成の流れ

```
Excelテンプレート
  ↓ (generate_jsbsim_from_gsheet.py)
aircraft/MyAircraft/MyAircraft.xml
  ↓ (JSBSim)
飛行シミュレーション
```

## XMLファイルの構造

### メインXMLファイル

```xml
<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="http://jsbsim.sf.net/JSBSimScript.xsl"?>
<fdm_config name="ExampleAircraft" version="2.0" release="BETA">

  <fileheader>
    <author>JSBSim XML Generator</author>
    <filecreationdate>2025-10-18</filecreationdate>
    <version>1.0</version>
    <description>200g RC UAV</description>
  </fileheader>

  <metrics>
    <wingarea unit="M2">0.103</wingarea>
    <wingspan unit="M">0.905</wingspan>
    <chord unit="M">0.114</chord>
    <location name="AERORP" unit="M">
      <x>0.057</x>
      <y>0.0</y>
      <z>0.0</z>
    </location>
  </metrics>

  <mass_balance>
    <ixx unit="KG*M2">0.001</ixx>
    <iyy unit="KG*M2">0.002</iyy>
    <izz unit="KG*M2">0.003</izz>
    <emptywt unit="KG">0.2</emptywt>
    <location name="CG" unit="M">
      <x>0.057</x>
      <y>0.0</y>
      <z>0.0</z>
    </location>
  </mass_balance>

  <propulsion>
    <!-- 推力テーブルが生成される -->
  </propulsion>

  <flight_control name="FCS">
    <!-- 操縦系統定義 -->
  </flight_control>

  <aerodynamics>
    <!-- 空力係数定義 -->
  </aerodynamics>

  <output name="datalog" type="CSV" rate="10">
    <!-- ログ出力設定 -->
  </output>

</fdm_config>
```

### 推力テーブル（本実装）

```xml
<propulsion>
  <engine file="electric_motor">
    <thruster file="propeller">
      <table name="C_THRUST" type="internal">
        <tableData>
          0.0  0.5
          10.0 0.45
          20.0 0.35
        </tableData>
      </table>
    </thruster>
  </engine>
</propulsion>
```

## JSBSim初期化時のディレクトリ検索

### デフォルト検索パス

JSBSimは以下の順序でディレクトリを検索します:

1. カレントディレクトリ
2. `aircraft/`
3. `engines/`
4. `systems/`

### Pythonでのパス指定

```python
import jsbsim

# カレントディレクトリを基準
fdm = jsbsim.FGFDMExec('.')

# 明示的にパス指定
fdm = jsbsim.FGFDMExec('/path/to/project/root')

# aircraftディレクトリを明示指定
fdm.set_aircraft_path('aircraft')
```

## Evidence Level

| 項目 | Evidence Level | 根拠 |
|------|----------------|------|
| ディレクトリ構造 | L1 | JSBSim公式ドキュメント |
| 電動モーター推進系 | L4 | End-to-Endテストで実証 |
| 推力テーブル方式 | L4 | End-to-Endテストで実証 |

## 参考資料

- [JSBSim Reference Manual - Chapter 3: File Format](http://jsbsim.sourceforge.net/JSBSimReferenceManual.pdf)
- [JSBSim Aircraft Configuration Guide](http://jsbsim.sourceforge.net/)

---

**作成日**: 2025-10-18
**JSBSim対応バージョン**: 1.1.0以上
**Evidence Level**: L1 (公式ドキュメント) + L4 (実装実証)
