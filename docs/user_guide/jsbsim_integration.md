# JSBSim Integration Guide

生成したXMLファイルをJSBSimで使用する方法を説明します。

## 前提条件

- Python 3.8以上
- JSBSim 1.1.0以上がインストール済み

```bash
pip install jsbsim
```

## 基本的な使用方法

### 1. XMLファイルを生成

```bash
cd delivery_repo_draft
python src/generate_jsbsim_from_gsheet.py -i my_aircraft.xlsx -o aircraft/MyAircraft/
```

生成されるファイル:
```
aircraft/
└── MyAircraft/
    └── MyAircraft.xml
```

### 2. JSBSimで読み込み

```python
import jsbsim

# JSBSimを初期化（カレントディレクトリ = プロジェクトルート）
fdm = jsbsim.FGFDMExec('.')

# 機体をロード
fdm.load_model('MyAircraft')

# 初期条件を実行
fdm.run_ic()

print("Aircraft loaded successfully!")
```

### 3. 基本プロパティを確認

```python
# 質量・翼面積・翼幅を取得
mass = fdm['inertia/weight-lbs']  # lbs
wingarea = fdm['metrics/Sw-sqft']  # sqft
wingspan = fdm['metrics/bw-ft']    # ft

print(f"Mass: {mass:.2f} lbs ({mass*0.453592:.2f} kg)")
print(f"Wing Area: {wingarea:.2f} sqft ({wingarea*0.092903:.4f} m²)")
print(f"Wing Span: {wingspan:.2f} ft ({wingspan*0.3048:.2f} m)")
```

## トリム実行

### トリムとは

**トリム**は、機体が一定速度で水平飛行を維持するための操縦面角度（エレベーター、スロットル等）を自動計算する機能です。

### トリム実行方法

```python
# 初期条件を設定
fdm['ic/u-fps'] = 15.0 * 3.28084  # 15 m/s → ft/s
fdm['ic/h-sl-ft'] = 100.0          # 高度100ft

# トリムを実行（mode=2: 縦方向トリム）
fdm.do_trim(2)

# トリム結果を確認
if fdm['simulation/trim-completed']:
    elevator = fdm['fcs/elevator-pos-rad']
    throttle = fdm['fcs/throttle-cmd-norm']
    alpha = fdm['aero/alpha-rad']

    print(f"Trim successful!")
    print(f"Elevator: {elevator:.4f} rad ({elevator*57.2958:.2f}°)")
    print(f"Throttle: {throttle:.4f}")
    print(f"Alpha: {alpha:.4f} rad ({alpha*57.2958:.2f}°)")
else:
    print("Trim failed")
```

### トリムが失敗する場合

**原因と対策**:

1. **空力係数が不適切**
   - CD0が小さすぎる → 増やす（0.028 → 0.035）
   - Cmalphaの絶対値が小さい → 増やす（-0.50 → -0.60）

2. **過大推力（T/W > 0.5）による推力支援飛行モード**
   - **症状**: CL値が異常に低い（< 0.1）、Alpha値が異常に低い（< 1°）
   - **原因**: 推力が重量を支え、翼が揚力を発生しない「推力支援飛行」状態
   - **対策** (JSBSimシミュレーション上): テスト時に絞った推力値（10-30% throttle）で開始し、T/W = 0.05-0.15の範囲で純粋な空力飛行モデルとして動作することを確認
   - **注**: JSBSimシミュレーション上では、Throttle 100%で巡航することは異常ではない。純粋空力飛行モード（T/W=0.05-0.15）では正常。実機では風・乱流等の影響があるため、シミュレーション結果と実機の挙動は異なる場合があります

3. **CG位置が不適切**
   - CGxを平均翼弦長の20-30%付近に調整

## シミュレーション実行

### 基本的なシミュレーションループ

```python
import jsbsim

# 初期化・ロード・トリム（省略）

# シミュレーション設定
dt = 0.01  # タイムステップ: 10ms
duration = 10.0  # 10秒間実行

# シミュレーションループ
for i in range(int(duration / dt)):
    # 1ステップ実行
    fdm.run()

    # 状態を取得
    if i % 100 == 0:  # 1秒毎に表示
        time = fdm['simulation/sim-time-sec']
        altitude = fdm['position/h-sl-ft'] * 0.3048  # ft → m
        velocity = fdm['velocities/u-fps'] * 0.3048  # ft/s → m/s
        pitch = fdm['attitude/pitch-rad'] * 57.2958  # rad → deg

        print(f"t={time:.1f}s: Alt={altitude:.1f}m, V={velocity:.1f}m/s, Pitch={pitch:.1f}°")

print("Simulation completed!")
```

### 操縦入力

```python
# エレベーター操作（-1.0 ~ 1.0）
fdm['fcs/elevator-cmd-norm'] = 0.1  # 上昇

# スロットル操作（0.0 ~ 1.0）
fdm['fcs/throttle-cmd-norm'] = 0.8  # 80%

# エルロン操作（-1.0 ~ 1.0）
fdm['fcs/aileron-cmd-norm'] = 0.2  # 右旋回

# ラダー操作（-1.0 ~ 1.0）
fdm['fcs/rudder-cmd-norm'] = 0.1  # 右
```

## テストスクリプト

プロジェクトには以下のテストスクリプトが含まれています:

### test_jsbsim_load.py

基本的な読み込みテスト:
```bash
python tests/test_jsbsim_load.py MyAircraft
```

### test_trim_stability.py

トリム収束・安定性テスト:
```bash
python tests/test_trim_stability.py MyAircraft 15
```

詳細は[tests/README.md](../../tests/README.md)を参照してください。

## トラブルシューティング

### 問題: Could not open file: MyAircraft.xml

**原因**: カレントディレクトリがプロジェクトルートにない

**解決策**:
```python
import os
print(os.getcwd())  # カレントディレクトリ確認

# プロジェクトルートに移動
os.chdir('/path/to/delivery_repo_draft')
```

### 問題: トリムが収束しない

**確認事項**:
1. 空力係数が妥当か（examples/ExampleAircraftと比較）
2. 推進系推力が十分か
3. CG位置が適切か（平均翼弦長の20-30%）

詳細は[examples/README.md](../../examples/README.md#トラブルシューティング)を参照してください。

### 問題: シミュレーションが発散する

**原因**: 動的安定性係数（Cmq, CLq等）が不適切

**対策**:
- Cmqを-10～-15に設定（pitch rate damping）
- CLqを正の値に設定
- 動的安定性係数を含むテンプレートを使用

## 参考資料

- [JSBSim Reference Manual](http://jsbsim.sourceforge.net/JSBSimReferenceManual.pdf)
- [JSBSim Python API](https://jsbsim-team.github.io/jsbsim/)

---

**作成日**: 2025-10-18
**JSBSim対応バージョン**: 1.1.0以上
