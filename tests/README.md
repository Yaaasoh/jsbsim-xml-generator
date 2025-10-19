# Tests

テストスクリプト一覧

## test_jsbsim_load.py

JSBSim XML読み込みテスト

**使用方法**:
```bash
cd delivery_repo_draft
python tests/test_jsbsim_load.py [aircraft_name]
```

**例**:
```bash
# デフォルト（ExampleAircraft）
python tests/test_jsbsim_load.py

# カスタム機体
python tests/test_jsbsim_load.py MyAircraft
```

**テスト内容**:
- JSBSim初期化
- 機体XMLロード
- 初期条件実行
- 基本プロパティ確認（質量、翼面積、翼幅）

## test_e2e.py

E2Eテスト（Excel → XML生成 → JSBSim読み込み）

**使用方法**:
```bash
cd delivery_repo_draft
python tests/test_e2e.py
```

**テスト内容**:
- Excelテンプレート読み込み
- XML生成
- JSBSim読み込み
- トリム収束テスト
- 安定飛行テスト

## test_trim_stability.py

トリム収束・安定性テスト（Traditional Engine用）

⚠️ **注意**: このテストは **JSBSim built-in trim** を使用するため、**External Reactions** 方式のXMLでは失敗します。External Reactions使用時は `test_trim_manual.py` を使用してください。

**使用方法**:
```bash
cd delivery_repo_draft
python tests/test_trim_stability.py [aircraft_name] [velocity_mps]
```

**例**:
```bash
# デフォルト（ExampleAircraft, 15 m/s）
python tests/test_trim_stability.py

# 10 m/sでテスト
python tests/test_trim_stability.py ExampleAircraft 10

# カスタム機体
python tests/test_trim_stability.py MyAircraft 12
```

**テスト内容**:
- トリム収束テスト（縦方向、JSBSim built-in trim使用）
- トリム結果表示（エレベーター、スロットル、迎角）
- 10秒間安定飛行テスト
- ピッチ変化・高度変化確認

**合格基準**:
- トリム収束成功
- 10秒間のピッチ変化 < 5°
- 10秒間の高度変化 < 10m

---

---

## test_trim_manual.py

手動トリム探索（External Reactions対応）

External Reactions方式のXML用トリム探索ツール。scipy.optimizeを使用してトリムを計算します。

**使用方法**:
```bash
cd delivery_repo_draft
python tests/test_trim_manual.py [aircraft_name] [velocity_mps]
```

**例**:
```bash
# デフォルト（ExampleAircraft, 15 m/s）
python tests/test_trim_manual.py

# 10 m/sでテスト
python tests/test_trim_manual.py ExampleAircraft 10

# カスタム機体
python tests/test_trim_manual.py MyAircraft 12
```

**テスト内容**:
- scipy.optimize.fsolveによる手動トリム探索
- 目標: wdot=0 (垂直加速度=0), qdot=0 (ピッチ加速度=0)
- トリム結果表示（エレベーター、スロットル、迎角、ピッチ、推力）
- 10秒間安定性テスト

**合格基準**:
- トリム収束成功 (wdot < 1.0 ft/s², qdot < 0.01 rad/s²)
- 10秒間のピッチ変化 < 5°
- 10秒間の高度変化 < 10m

**背景**:
- JSBSim built-in trim (`fdm.do_trim()`) はExternal Reactionsと互換性なし
- このテンプレートはExternal Reactions使用
- Manual trim searchが必須

---

## test_xml_generation.py

XML生成テスト（公開前Critical作業 Task B）

Excel → JSBSim XML生成の完全ワークフローを検証します。

**使用方法**:
```bash
cd delivery_repo_draft
python tests/test_xml_generation.py
```

**テスト内容**:
- Test 1: Default Template XML Generation
  - templates/Aircraft_Input_Template.xlsx読み込み
  - JSBSim XML生成
  - ファイルサイズ検証
- Test 2: Unit Conversion Verification
  - 生成されたXML内の単位変換確認

**合格基準**:
- XML生成成功（3-50 KB範囲内）
- 単位変換正確性確認

---

## test_e2e_flight.py

E2E Flight Test（公開前Critical作業 Task C）

Excel → XML → JSBSim Flight の完全E2Eワークフロー検証です。

**使用方法**:
```bash
cd delivery_repo_draft
python tests/test_e2e_flight.py
```

**テスト内容**:
- Step 1: Excel → XML生成
- Step 2: JSBSim model loading
- Step 3: Manual trim search (External Reactions対応)
- Step 4: 10秒間安定飛行テスト

**合格基準**:
- XML生成成功
- JSBSim読み込み成功
- Trim収束成功 (residual < 0.01)
- 10秒間安定飛行成功

**背景**:
- 完全なワークフローを単一スクリプトで検証
- External Reactions対応のmanual trim search使用

---

## test_unit_conversion.py

単位変換テスト（公開前Critical作業 Task D）

単位変換モジュール (unit_conversion.py) の正確性を検証します。

**使用方法**:
```bash
cd delivery_repo_draft
python tests/test_unit_conversion.py
```

**テスト内容**:
- Test 1: Length Conversion (mm/cm/m → M)
- Test 2: Area Conversion (mm²/cm²/m² → M²)
- Test 3: Mass Conversion (g/kg → KG)
- Test 4: Moment of Inertia Conversion (g*mm² → KG*M²)
- Test 5: Unit String Normalization (mm2/mm^2等)
- Test 6: Practical Aircraft Values (200g UAV実用値)

**合格基準**:
- 全27テストケースPASS
- 精度±1e-6以内

**背景**:
- 航空機パラメータの単位変換は精度が重要
- JSBSim標準単位系（M, KG, FT等）への変換確認
