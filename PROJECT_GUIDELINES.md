# xmi-input-ui プロジェクトガイドライン

**作成日**: 2025年10月5日
**最終更新**: 2025年10月5日
**対象**: xmi-input-ui（Excel → JSBSim XML変換システム）開発
**目的**: プロジェクト固有の作業ルール・方針を一元管理

---

## 📚 本文書の位置づけ

本ガイドラインは、上位プロジェクト（JSBSim調査プロジェクト）の作業ルールを継承し、xmi-input-ui開発に特化した指針を提供します。

**重要**: 本文書は出典元のコピーではなく、xmi-input-ui開発に必要な内容を統合・再構成したものです。出典元が移動・削除された場合でも、本文書のみで作業継続できるよう、必要な内容をすべて記述しています。

---

## 🔗 出典元ドキュメント

### 主要参照元（3文書）

1. **実用主義ガイド**
   - パス: `C:\Users\xprin\github\tech-research-portfolio\projects\flyingrobot_knowledge\flight-sim\20251003_jsbsim_investigation\02_実用主義ガイド_経験値と概算による段階的アプローチ.md`
   - 作成日: 2025年10月3日
   - 内容: Phase 1-3の段階的アプローチ、経験値活用方針
   - 継承項目: Phase定義、実用主義の基本原則

2. **出典記載ルール**
   - パス: `C:\Users\xprin\github\tech-research-portfolio\projects\flyingrobot_knowledge\flight-sim\20251003_jsbsim_investigation\03_出典記載ルール_Evidence_Level体系とバンクーバーSIST02併用.md`
   - 作成日: 2025年10月3日
   - 内容: Evidence Level体系、参考文献記載方式
   - 継承項目: L1-L5定義、記載テンプレート

3. **全体計画・統合マップ**
   - パス: `C:\Users\xprin\github\tech-research-portfolio\projects\flyingrobot_knowledge\flight-sim\20251003_jsbsim_investigation\00_全体計画_プロジェクト統合マップ.md`
   - 作成日: 2025年10月3日、最終更新: 2025年10月5日 13:00
   - 内容: プロジェクト全体の構成、サブプロジェクト連携
   - 継承項目: xmi-input-uiの位置づけ、開発フェーズ

### 補助参照元

4. **fixed-wing品質ガイドライン**
   - パス: `C:\Users\xprin\github\tech-research-portfolio\projects\flyingrobot_knowledge\fixed-wing\docs\guidelines\quality\DOCUMENTATION_STYLE_GUIDE.md`
   - 内容: Evidence Level体系の定義（原典）

5. **fixed-wingファイル管理ポリシー**
   - パス: `C:\Users\xprin\github\tech-research-portfolio\projects\flyingrobot_knowledge\fixed-wing\docs\policies\management\FILE_MANAGEMENT_POLICY.md`
   - 内容: フェーズ別フォルダ管理、アーカイブルール

---

## 🚨 絶対禁止事項（2025年10月6日追加）

### インシデント背景

2025年10月4-6日に、343ファイルを無許可削除する重大インシデントが発生しました。このセクションは再発防止のため、絶対に守るべきルールを明記します。

**参照**: `../../../../CRITICAL_INCIDENT_FULL_CONFESSION.md`

### ファイル削除の厳格ルール

#### 1. 削除は原則禁止

```yaml
ルール:
  - ユーザーの明示的許可なくファイルを削除してはならない
  - 「整理」「リファクタリング」「クリーンアップ」は削除の理由にならない
  - 古いファイル、使わないファイルでも削除禁止
  - Git pre-commit hookが10ファイル以上の削除を自動検出・阻止

根拠:
  - ユーザー明言: "削除を許可したことは一度もない"
  - 整理 = 移動 + アーカイブ、削除は含まれない
  - 343ファイル無許可削除インシデントを二度と繰り返さない
```

#### 2. 整理 = 移動 + 案内

```yaml
正しい整理作業の手順:
  1. 移動先を決定（archive/, backup/, phases/completed/等）
  2. git mv でファイルを移動
  3. 元の場所に移動案内README作成
  4. ユーザーに報告

案内READMEの必須内容:
  - どのファイルがどこに移動したか
  - 移動理由
  - ファイル対応表

例:
  - _RESTORATION_NOTICE.md（flight-sim/）
  - _FILES_MOVED_README.md（xmi-input-ui/）
```

#### 3. 10ファイル以上の削除は即座に中止

```yaml
検出方法:
  - Git pre-commit hook（.git/hooks/pre-commit）
  - 10ファイル以上の削除を自動検出
  - ユーザーに警告を表示
  - 許可なくコミット阻止

対処手順（10ファイル以上削除が必要な場合）:
  1. ユーザーに削除理由を説明
  2. 削除対象ファイルリストを提示
  3. 明示的な許可を得る
  4. 許可後も慎重に実行
  5. 削除後は必ず報告
```

#### 4. 削除が本当に必要な場合の手順

```yaml
ステップ1: ユーザーへの事前確認
  - 削除理由の明確な説明
  - 削除対象ファイルの完全リスト提示
  - 代替案（移動、アーカイブ）の提示

ステップ2: 明示的な許可取得
  - "削除してよいか"を直接質問
  - ユーザーの"YES"を確認
  - 曖昧な返答では進めない

ステップ3: 慎重な実行
  - 許可されたファイルのみ削除
  - 削除前にバックアップ確認
  - git commit前に再確認

ステップ4: 事後報告
  - 削除実行後すぐに報告
  - 削除したファイルリスト提示
  - 復旧方法の記録
```

### ブランチ管理の厳格ルール

#### 5. 専用ブランチ必須

```yaml
ルール:
  - プロジェクト専用ブランチを必ず作成
  - 命名: feature/{project-short-name}-{feature}
  - 例: feature/xmi-ui-phase2
  - 既存ブランチの流用禁止

禁止事項:
  - feature/file-reorganization-phases-* の使用
    → 全体整理用、個別プロジェクトでの使用禁止
  - 他プロジェクト用ブランチの使用
    → feature/fixed-wing-* をxmi-input-uiで使用等
```

#### 6. ブランチ作成前の確認

```yaml
チェックリスト:
  - [ ] ブランチ名の目的を確認
  - [ ] 既存ブランチの内容を確認（git log --oneline）
  - [ ] mainから新規ブランチを切る
  - [ ] ブランチ名がプロジェクト名を含む

例（正しい手順）:
  git checkout main
  git pull
  git checkout -b feature/xmi-ui-phase2-improvements
```

### Git操作の厳格ルール

#### 7. 大量変更時の確認

```yaml
基準:
  - 100ファイル以上の変更
  - 50ファイル以上の追加
  - 20ファイル以上の削除

対処:
  - Git pre-commit hookが自動警告
  - ユーザーに変更内容を報告
  - 明示的な許可を得る

PR #2インシデント教訓:
  - 100+ファイル変更を見逃した
  - レビュー不十分でマージ
  - fixed-wing関連ファイルが混入
```

#### 8. コミットメッセージの誠実性

```yaml
禁止表現:
  - "95%削減"等、削除を成果のように記載
  - "整理"で削除を正当化
  - "リファクタリング"で削除を隠蔽

推奨表現:
  - 移動の場合: "move: XX to YY"
  - アーカイブの場合: "archive: XX to archive/"
  - 削除の場合（許可済み）: "remove: XX (user approved)"
```

### 違反時の対応

#### 9. インシデント発生時の手順

```yaml
ステップ1: 即座に中止
  - 作業を停止
  - 現状を保存（git stash等）

ステップ2: ユーザーに報告
  - 何をしたか明確に説明
  - 影響範囲を特定
  - 復旧方法を提案

ステップ3: 復旧実施
  - ユーザー指示に従う
  - 全力で復旧
  - 再発防止策を実装

ステップ4: 詳細記録
  - インシデント報告書作成
  - 原因分析
  - 再発防止策の文書化
```

---

## 🎯 xmi-input-ui プロジェクト概要

### プロジェクト目的

```yaml
目標:
  非プログラマでもJSBSim XMLを作成できるExcel UIシステムの開発

成功の定義:
  1. Excelで機体諸元を入力できる
  2. Pythonスクリプトで自動的にXML生成
  3. JSBSimが生成XMLを読込可能
  4. 設計者が自力で機体モデル作成・調整できる

対象ユーザー:
  - 200g固定翼機の設計者
  - プログラミング経験が限定的な研究者・学生
  - 飛行ロボットコンテスト参加者
```

### 開発フェーズ（全5フェーズ）

```yaml
Phase 0: 分析・設計（完了 ✅）
  期間: 2025年10月3日
  成果物: UI_ANALYSIS_REPORT_20251003.md
  状態: バグ修正5件完了、Phase 1準備完了

Phase 1: 最小動作確認（MVP）（進行中 🔄）
  期間: 1-2作業日（実働5-8時間）
  目標: Excel → XML → JSBSim読込の往復変換成功
  対象セクション: metrics, mass_balance, propulsion, output

Phase 2: UI日本語化・改善（予定 📅）
  期間: 2週間
  内容: プルダウンリスト、条件付き書式、入力ガイド

Phase 3: 空力モデル対応（予定 📅）
  期間: 2週間
  内容: 1D/2Dテーブル管理（CL-α, CD-α, Cm-α）

Phase 4: 制御系対応（予定 📅）
  期間: 2週間
  内容: FCSブロック定義、RC入力マッピング

Phase 5: 検証・最適化（予定 📅）
  期間: 1週間
  内容: 統合テスト、性能ベンチマーク
```

---

## 📋 実用主義の基本原則（継承）

### Phase 1-3の段階的アプローチ

**出典**: `02_実用主義ガイド_経験値と概算による段階的アプローチ.md`

```yaml
基本原則:
  1. 機体挙動が大まかに合えば良い
  2. 翼形厳密製作は稀 → 代表値で十分
  3. 経験値・概算値を積極活用
  4. 必要になって初めて精密化

Phase定義:
  Phase 1（最優先）:
    目標: JSBSimで基本的な飛行シミュレーション実行
    手法: 経験値・概算値による最小動作確認
    使用データ: 全て経験値・概算
    成功基準: トリム計算収束、物理的に妥当、誤差±30%許容

  Phase 2（2週間後～）:
    目標: シミュレーションと実機挙動の大まかな一致確認
    手法: 実機飛行データ収集と比較
    成功基準: 主要パラメータ誤差 < 50%、推奨 < 30%

  Phase 3（個別必要時のみ）:
    実施条件:
      - 研究発表・論文投稿
      - 特定機体の高精度設計（±10%以内要求）
      - 実機との大幅乖離（>50%）
    手法: XFLR5解析、風洞試験（研究レベル）
```

### xmi-input-uiへの適用

```yaml
Phase 1 MVP開発:
  ✅ 経験値による典型値のみ使用
  ✅ 簡易モデルで動作確認
  🚫 精密な空力解析（Phase 3まで禁止）
  🚫 複雑なプロペラ理論（Phase 3まで禁止）

デフォルト値設定の方針:
  - 200g機の典型値を設定
  - 飛行ロボコン実績データを活用
  - 出典・根拠を明確に記載
```

---

## 📝 出典記載ルール（継承）

### Evidence Level体系（完全版）

**出典**: `03_出典記載ルール_Evidence_Level体系とバンクーバーSIST02併用.md`

```yaml
L1 (理論・教科書):
  定義: 物理法則、理論式、教科書の基本原理
  例:
    - Momentum theory (MIT 16.Unified)
    - Bernoulli's equation (Anderson, Fundamentals of Aerodynamics)
  信頼性: 最高（普遍的）

L2 (公式・学術):
  定義: 査読論文、公式データベース、理論解析ツール出力
  例:
    - UIUC Propeller Database Vol.1 APC 8x4 static test
    - Brandt & Selig (2011) AIAA-2011-1255
    - APC Performance Data (PER3_*.dat)
  信頼性: 高（検証済み）

L3 (実測DB・公式仕様):
  定義: メーカー公式仕様、実測データベース（測定者明示）
  例:
    - APC official specification (重量3.2g)
    - RC Benchmark Database (測定者: John Doe, 2023)
  信頼性: 中～高（条件依存）

L4 (コミュニティ実測):
  定義: フォーラム・ブログの実測データ（測定者不明・簡易）
  例:
    - RCGroups forum user report "~700-800g @ 15k RPM"
    - FliteTest community consensus
  信頼性: 中（参考値）

L5 (概算・推定):
  定義: 経験則、概算式、推定値
  例:
    - Thrust ≈ D² × P × 10 formula (±50%誤差)
    - CT ≈ 0.10 (typical 2-blade propeller)
  信頼性: 低（大まかな目安）
```

### xmi-input-uiでの記載テンプレート

**すべてのデフォルト値・パラメータに適用**

```yaml
# テンプレート（必須項目）

Propeller: APC 5x3
Static_Thrust: 375 g @ 10000 RPM

出典:
  Primary: RCGroups user "pilot123" measurement (L4)
  Secondary: APC official spec weight 2.8g (L3)
  Tertiary: CT=0.10 typical value assumption (L5)

根拠:
  - 複数ユーザーの実測範囲 350-400g
  - モーター: 1806 2300kV @ 2S想定
  - 理論計算との整合性確認

誤差評価:
  推定誤差: ±20%
  検証方法: Phase 2実機測定で確認予定
  許容範囲: Phase 1目標±30%以内

備考:
  - 入手性: 容易（国内通販）
  - 使用目的: Phase 1概算モデル
```

### NG例とOK例

```yaml
❌NG例:
  "翼面積: 0.2 m²（典型値）"
  → 出典・根拠・誤差が不明

✅OK例:
  "翼面積: 0.2 m² @ 200g機典型値 (L5)
   出典: 飛行ロボコン2015-2024実績データ集計 (L4)
   根拠: 翼幅1m × 平均翼弦0.2m、実績10機の平均値
   誤差: ±15%、範囲0.17-0.23 m²"
```

---

## 🗂️ ディレクトリ構造ルール

### 標準構造（Phase 1適用版）

```
xmi-input-ui/
│
├── 📂 phase0_analysis/              # Phase 0: 分析フェーズ（完了）
│   ├── UI_ANALYSIS_REPORT_20251003.md
│   ├── DECISION_SUMMARY_意思決定サマリー.md
│   ├── 各種検討ドキュメント.md
│   └── debug_nan.py
│
├── 📂 phase1_mvp/                   # Phase 1: MVP実装（進行中）
│   ├── 📂 src/                      # ソースコード
│   │   ├── generate_jsbsim_from_gsheet.py
│   │   └── unit_conversion.py
│   ├── 📂 tests/                    # テストコード
│   │   ├── test_unit_conversion.py
│   │   ├── test_practical_conversion.py
│   │   └── ...
│   ├── 📂 docs/                     # Phase 1ドキュメント
│   │   └── IMPLEMENTATION_PLAN_Phase1完了への実装計画.md
│   └── 📂 output/                   # 生成物
│
├── 📂 templates/                    # Excelテンプレート（共通）
│   ├── JSBSim_XML_Authoring_Template_v2_complete.xlsx  # V2.0（推奨、2025-10-16リリース）
│   └── JSBSim_XML_Authoring_Template_v1.xlsx           # V1.0（参照用）
│
├── 📂 docs/                         # プロジェクト全体ドキュメント
│   ├── README_Generator_Quickstart.md
│   └── DEVELOPMENT_ROADMAP.md
│
├── PROJECT_GUIDELINES.md            # 本文書（作業ルール統合）
└── 📂 archive/                      # 過去バージョン
```

### フォルダ管理ルール

**出典**: `fixed-wing/docs/policies/management/FILE_MANAGEMENT_POLICY.md`（継承・改変）

```yaml
原則:
  1. フェーズ別に作業フォルダを分離
  2. 完了フェーズはarchive/へ（オプション）
  3. 進行中は明確なフォルダ構造

Phase完了時の処理:
  □ Phase完了判定書を作成
  □ 成果物をphaseN_*/にまとめる
  □ 必要に応じてarchive/phase0_analysis_archived_YYYYMMDD/へ移動
  □ 次Phaseのフォルダ作成

命名規則:
  - フォルダ: 小文字_スネークケース（例: phase1_mvp）
  - ドキュメント: 大文字_スネークケース_日本語可（例: IMPLEMENTATION_PLAN.md）
  - コード: 小文字_スネークケース（例: unit_conversion.py）
```

---

## 🔧 Phase 1 MVP開発の具体的方針

### 意思決定事項（3項目）

**出典**: `phase0_analysis/DECISION_SUMMARY_意思決定サマリー.md`

```yaml
決定事項1: 単位変換の実装
  選択肢A: 手計算変換（実装工数0h）
  選択肢B: 自動変換（追加工数0-1h、試作済み）⭐推奨
  選択肢C: SI単位統一（実装工数0h）

決定事項2: Excelデフォルト値
  選択肢A: 空テンプレート（実装工数0h）
  選択肢B: 200g機典型値設定（実装工数1-2h）⭐推奨

決定事項3: Phase 1完了スコープ
  必須: ディレクトリ構造修正（1h）
  推奨: 上記2項目を含む（総工数2-3h）⭐推奨
```

### Phase 1成功基準

```yaml
必須基準:
  ✅ Excel → XML 変換が成功する
  ✅ XMLが正しいディレクトリ構造に配置される
  ✅ JSBSimがXMLを読込可能
  ✅ バグ修正5件が維持されている

追加基準（パターンB選択時）:
  ✅ 28単位パターンがすべて正しく変換される
  ✅ デフォルト値でXML生成が成功する
  ✅ 出典・根拠が完全記載されている
```

---

## 🚀 開発ワークフロー

### 標準作業手順

```yaml
1. フェーズ開始:
   □ phaseN_*/フォルダ作成
   □ 計画ドキュメント作成
   □ 意思決定事項の明確化

2. 実装:
   □ src/にコード作成
   □ tests/にテスト作成
   □ テスト実行・通過確認

3. ドキュメント作成:
   □ 出典・根拠を完全記載
   □ Evidence Level明記
   □ 誤差評価記述

4. 検証:
   □ 統合テスト実行
   □ Phase完了判定

5. Phase完了:
   □ 完了報告書作成
   □ 必要に応じてアーカイブ
```

### コミットメッセージ規約

```bash
# 形式
<type>: <summary>

<body>（オプション）

# type種別
feat: 新機能
fix: バグ修正
docs: ドキュメント
refactor: リファクタリング
test: テスト追加
chore: ビルド・設定

# 例
feat: 単位変換自動化機能追加（g→KG, mm→M）

- unit_conversion.py実装（28単位パターン対応）
- test_unit_conversion.py追加
- Evidence Level L2-L5併記
```

---

## ⚠️ 禁止事項・注意事項

### Phase 1での禁止事項

**出典**: `02_実用主義ガイド_経験値と概算による段階的アプローチ.md`

```yaml
🚫 Phase 1で禁止:
  - XFLR5計算値の使用（Phase 3まで禁止）
  - 複雑なプロペラ理論実装（Phase 3まで禁止）
  - 翼型データからの精密計算（Phase 3まで禁止）
  - 風洞試験データの要求（Phase 3まで禁止）

✅ Phase 1で推奨:
  - 経験値・概算値の積極活用
  - 飛行ロボコン実績データ参照
  - 静止推力+概算でのプロペラモデル
  - 出典・根拠・誤差の明確化
```

### 出典記載の必須化

```yaml
すべての数値・パラメータに適用:
  ❌ 「翼面積: 0.2 m²」のみ
  ✅ 「翼面積: 0.2 m² (L5)
      出典: 飛行ロボコン実績データ (L4)
      根拠: ...
      誤差: ±15%」
```

---

## 🔄 更新履歴

| 日付 | 更新内容 | 担当 |
|------|----------|------|
| 2025/10/05 | 初版作成、上位3文書から継承・統合 | Claude |

---

## 📞 困ったときの参照順序

```yaml
1. 本文書（PROJECT_GUIDELINES.md）
   → xmi-input-ui固有の方針確認

2. phase0_analysis/DECISION_SUMMARY_意思決定サマリー.md
   → Phase 1の3つの選択確認

3. phase1_mvp/docs/IMPLEMENTATION_PLAN_Phase1完了への実装計画.md
   → 具体的な実装手順確認

4. 上位プロジェクト文書（参考）
   - 02_実用主義ガイド.md（Phase定義）
   - 03_出典記載ルール.md（Evidence Level詳細）
   - 00_全体計画.md（プロジェクト全体像）
```

---

## 🛡️ 再発防止策（2025年10月5日追加）

### git/GitHub運用ルール

#### 1. ブランチ命名規則（必須遵守）

```yaml
命名パターン: feature/{project-short-name}-{feature-description}

xmi-input-ui関連の例:
  ✅ 正: feature/xmi-ui-phase1
  ✅ 正: feature/xmi-ui-unit-conversion
  ✅ 正: feature/xmi-ui-excel-template
  ❌ 誤: feature/update
  ❌ 誤: feature/fix-bug
  ❌ 誤: 既存の汎用ブランチの流用

ルール:
  - mainから新規作成すること（既存ブランチ流用禁止）
  - プロジェクト名を必ず含めること
  - 機能内容を具体的に記述すること
```

#### 2. PR作成前チェックリスト（必須実施）

```yaml
コード確認:
  - [ ] 変更ファイル数が妥当か（目安: 50ファイル以下）
  - [ ] すべてのファイルがxmi-input-ui配下か
       確認コマンド: git diff --name-only main | grep -v "xmi-input-ui"
  - [ ] テストが全てPass

ドキュメント確認:
  - [ ] コミットメッセージがxmi-input-uiに関連しているか
  - [ ] PR説明が変更内容を正確に記載
  - [ ] 影響範囲が明確

ブランチ確認:
  - [ ] mainから切った専用ブランチか
  - [ ] ブランチ名が命名規則に準拠
  - [ ] 既存ブランチを流用していないか
```

#### 3. 作業開始時の確認習慣

```bash
# 必ず実行すること
git branch --show-current          # 現在のブランチ確認
git log --oneline -5               # ブランチの履歴確認

# 新規機能開始時は必ず専用ブランチ作成
git checkout main
git pull
git checkout -b feature/xmi-ui-{feature-name}
```

### インシデント記録

**発生日**: 2025年10月5日
**問題**: feature/file-reorganization-phases-20251003ブランチを誤使用し、fixed-wing関連100+ファイルをmainにマージ
**対処**: PR #2をrevert、専用ブランチ feature/xmi-input-ui-phase1 作成、PR #3で正常マージ
**詳細**: INCIDENT_REPORT_20251005.md

### 教訓

1. **ブランチ名は目的を語る** - 汎用的な既存ブランチは絶対に流用しない
2. **PR内容は人間の目で確認** - ファイル数の異常は即座に気づくべき
3. **早期発見・早期対処** - force pushは適切に使えば強力な復旧手段

---

## 🔗 関連ドキュメント（2025-10-15追加）

### 標準作業チェックリスト

本ガイドラインは、プロジェクト標準作業チェックリストに統合されています:

**参照**: `WORK_CHECKLIST_STANDARD_TEMPLATE.md`（プロジェクトルート）
- パス: `C:\Users\xprin\github\tech-research-portfolio\projects\flyingrobot_knowledge\flight-sim\20251003_jsbsim_investigation\WORK_CHECKLIST_STANDARD_TEMPLATE.md`
- セクション: 「2. プロジェクトガイドライン」に本文書が必須確認項目として記載
- 目的: 作業開始前の必須確認により、絶対禁止事項（ファイル削除等）の遵守を保証

### Phase 6作業での本ガイドライン適用状況

**Phase 6A: 両ライン案内整備（2025-10-15実施中）**:
- ✅ 本ガイドラインを標準チェックリストに統合完了（WORK_CHECKLIST_STANDARD_TEMPLATE.md）
- ✅ Phase 6A専用チェックリスト作成完了（PHASE6A_MANDATORY_RULES_CHECKLIST.md）
- ✅ Line 1（FMS→JSBSim）成果物案内作成中
- ⏳ Line 2（Spreadsheet→JSBSim）成果物案内作成予定

**Phase 6B予定: Line 2完全統合（8時間、92%再利用）**:
- 本ガイドライン絶対禁止事項遵守（ファイル削除禁止、ブランチ専用作成）
- Line 1コード92%再利用方針

**参照**:
- `../phase6_deliverables_preparation/PHASE6A_WORK_INSTRUCTION.md`
- `../phase6_deliverables_preparation/LINE2_XMI_INTEGRATION_READINESS.md`

---

**重要**: 本文書は「生きた文書」として、Phase進行に応じて更新します。更新時は必ず更新履歴を記録してください。

---

## 📋 使用テンプレート（2025-10-16更新）

### 現在の推奨バージョン

**JSBSim_XML_Authoring_Template_v2_complete.xlsx** (2025-10-16以降)

```yaml
V2の改善点:
  1. シート別最適列幅:
     - 文字切れ解消（長い説明文も切れずに表示）
     - 共通列幅（5列）による視覚的一貫性
     - T1-T3: ユーザー手動調整値、T4-T8: コンテンツ分析による算出値

  2. 改行パターン統一:
     - C列（VarName）: スラッシュ後改行（99セル）
     - Row 1（Headers）: 括弧前改行（21セル）
     - XMLパス階層構造が視覚的に明確

  3. V1との完全互換性:
     - データ互換性: 100%
     - 列構成・シート構成・ドロップダウン: 同一
     - V1データをV2にコピー可能
```

**詳細**: `templates/README.md` 参照

### 旧バージョン（参照用）

- **JSBSim_XML_Authoring_Template_v1.xlsx** (Phase 1で使用、後方互換性あり)

### テンプレート選択ガイダンス

```yaml
新規プロジェクト:
  → V2_complete.xlsx を使用（視認性・入力性向上）

既存プロジェクト（V1使用中）:
  - 継続使用: V1のまま使用可能（機能的に問題なし）
  - 移行推奨: データコピーでV2に移行可能（4ステップ）
    手順: docs/GSheet_Template_Spec_v2.0.md参照

技術詳細・検証:
  → templates/EXCEL_TEMPLATE_TECHNICAL_SPECIFICATION.md参照
```

---

## 📝 更新履歴

- 2025/10/16: V2テンプレート情報追加（V2_complete推奨化）
- 2025/10/15: Phase 6進捗反映、標準作業チェックリスト参照追加
- 2025/10/06: 絶対禁止事項セクション追加（343ファイル削除インシデント対応）
- 2025/10/05 18:30: 再発防止策セクション追加（インシデント対応）
- 2025/10/05 13:00: 初版作成
