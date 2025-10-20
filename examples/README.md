# Example Aircraft

このフォルダには、JSBSim XML Generator使用例のサンプル機体が含まれています。

## ExampleAircraft

**機体名**: ExampleAircraft
**カテゴリ**: 200g級RC UAV
**用途**: チュートリアル・動作確認

### 機体仕様

| パラメータ | 値 | 単位 |
|-----------|-----|------|
| 全備重量 | 200 | g |
| 翼面積 | 103,000 | mm² (0.103 m²) |
| 翼幅 | 905 | mm |
| 平均翼弦長 | 114 | mm |
| 巡航速度 | 10-15 | m/s |

### 含まれるファイル

```
ExampleAircraft/
├── ExampleAircraft.xml          ← メインJSBSim XMLファイル
└── (その他補助ファイル)
```

### 使用方法

#### JSBSim読み込みテスト

```python
import jsbsim

fdm = jsbsim.FGFDMExec('.')
fdm.load_model('ExampleAircraft')
fdm.run_ic()

print("Aircraft loaded successfully!")
```

#### トリム設定テスト

```python
# 巡航速度15 m/sでトリム
fdm['ic/u-fps'] = 15.0 * 3.28084  # m/s → fps変換
fdm['ic/h-sl-ft'] = 100.0         # 高度100ft

# トリム実行
fdm.do_trim(2)  # 2 = Longitudinal trim

if fdm['simulation/trim-completed']:
    print("Trim successful!")
    print(f"Elevator trim: {fdm['fcs/elevator-pos-rad']} rad")
    print(f"Throttle trim: {fdm['fcs/throttle-cmd-norm']}")
```

### 空力特性

このサンプルの空力係数は、典型的な小型固定翼機の値を採用しています。

| 係数 | 値 | Evidence Level | 備考 |
|------|-----|----------------|------|
| CL0 | 0.25 | L3 | 典型的な小型固定翼機の値 |
| CLalpha | 5.0 /rad | L3 | 典型的な小型固定翼機の値 |
| CD0 | 0.028 | L3 | トリム収束改善 |
| Cmalpha | -0.50 /rad | L3 | 縦安定性確保 |
| Cmq | -12.0 /rad | L3 | pitch rate damping |

**Evidence Level説明**:
- L3: 典型的な小型固定翼機の値を採用

### 動作確認結果

| テスト項目 | 結果 | 条件 |
|-----------|------|------|
| JSBSim読み込み | ✅ 成功 | - |
| トリム収束 | ✅ 成功 | 10 m/s, 15 m/s |
| 10秒間安定飛行 | ✅ 成功 | トリム状態維持 |
| FlightGear可視化 | ✅ 成功 | UDP通信経由 |

**検証日**: 2025-10-17

### 推進系構成

| コンポーネント | 仕様 |
|--------------|------|
| モーター | 1400 Kv, 0.2 Ω内部抵抗 |
| プロペラ | 8×4.5inch |
| バッテリー | 11.1V 3S 1000mAh |
| ESC | 20A |

**注意**: この推進系構成は簡略化モデルです。実機への適用前に詳細な検証が必要です。

### カスタマイズ方法

このサンプルをベースに独自機体を作成するには:

1. **テンプレートを開く**:
   ```bash
   cp templates/Aircraft_Input_Template.xlsx my_aircraft_input.xlsx
   ```

2. **ExampleAircraftの値を参考にパラメータ入力**:
   - T_01_Basic_Info: 質量、翼面積を変更
   - T_02_Mass_Balance: 重心位置、慣性モーメントを調整
   - T_03_Propulsion: 推進系仕様を変更
   - T_04_Control: 操縦面を調整

3. **XML生成**:
   ```bash
   python src/generate_jsbsim.py --input my_aircraft_input.xlsx --output aircraft/MyAircraft/
   ```

4. **動作確認**:
   ```bash
   python tests/test_jsbsim_load.py MyAircraft
   ```

### トラブルシューティング

#### 問題: JSBSimがモデルを読み込めない
**症状**:
```
Could not open file: ExampleAircraft.xml
```

**解決策**:
1. カレントディレクトリ確認:
   ```python
   import os
   print(os.getcwd())  # aircraft/の親ディレクトリにいるか確認
   ```

2. JSBSim初期化時にパス指定:
   ```python
   fdm = jsbsim.FGFDMExec('.')
   fdm.set_aircraft_path('examples')
   fdm.load_model('ExampleAircraft')
   ```

#### 問題: トリムが収束しない
**症状**:
```
simulation/trim-completed = 0
```

**原因と対策**:
- **原因1**: 空力係数が不適切
  - 対策: CD0を増やす（0.028 → 0.035）、Cmalphaの絶対値を増やす

- **原因2**: 過大推力（T/W > 0.5）による推力支援飛行モード
  - 症状: CL値が異常に低い（< 0.1）、Alpha値が異常に低い（< 1°）
  - 原因: 推力が重量を支え、翼が揚力を発生しない状態
  - 対策 (JSBSimシミュレーション上): テスト時に絞った推力値（10-30% throttle）で開始し、T/W = 0.05-0.15の範囲で純粋な空力飛行モデルとして動作することを確認

- **原因3**: 重心位置が不適切
  - 対策: CGxを調整（通常は平均翼弦長の25%付近）

**注**: JSBSimシミュレーション上では、Throttle 100%で巡航することは異常ではありません。純粋空力飛行モード（T/W=0.05-0.15）では、巡航時Throttle 80-100%は正常な状態です。実機では風・乱流等の影響があるため、シミュレーション結果と実機の挙動は異なる場合があります。

### 参考資料

- [JSBSim Aircraft Configuration Guide](http://jsbsim.sourceforge.net/JSBSimReferenceManual.pdf)

---

**作成日**: 2025-10-18
**サンプル機体バージョン**: v3 E2E準拠
**動作確認済み**: JSBSim 1.1.0以上

---

**© 2025 Yaaasoh. All Rights Reserved.**

本ドキュメントの著作権はYaaasohに帰属します。引用部分については各引用元のライセンスが適用されます。
