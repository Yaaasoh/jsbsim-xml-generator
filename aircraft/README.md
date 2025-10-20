# Aircraft Directory

JSBSim標準のaircraftディレクトリです。生成されたXMLファイルはここに配置されます。

## ディレクトリ構造

```
aircraft/
├── ExampleAircraft/               ← サンプル機体（examples/からコピー済み）
│   └── ExampleAircraft.xml
└── [YourAircraft]/            ← 生成される機体XMLはここに配置
    └── [YourAircraft].xml
```

## XMLファイル生成方法

```bash
# Excelテンプレートから生成
python src/generate_jsbsim_from_gsheet.py -i my_aircraft.xlsx -o aircraft/MyAircraft/
```

生成後:
```
aircraft/
└── MyAircraft/
    └── MyAircraft.xml
```

## JSBSimでの使用方法

```python
import jsbsim

fdm = jsbsim.FGFDMExec('.')
fdm.load_model('MyAircraft')  # aircraft/MyAircraft/MyAircraft.xml を読み込み
fdm.run_ic()
```

**重要**: JSBSimは`aircraft/`ディレクトリを自動的に探します。カレントディレクトリがプロジェクトルート（aircraft/の親ディレクトリ）にあることを確認してください。

## JSBSim標準ディレクトリ構造について

JSBSimは以下のディレクトリ構造を期待します:

```
project_root/
├── aircraft/        ← 機体定義XMLファイル
├── engines/         ← エンジン定義XMLファイル
├── systems/         ← システム定義XMLファイル（オプション）
└── scripts/         ← スクリプトファイル（オプション）
```

詳細は[JSBSim公式ドキュメント](http://jsbsim.sourceforge.net/)を参照してください。

---

**作成日**: 2025-10-18
**JSBSim対応バージョン**: 1.1.0以上

---

**© 2025 Yaaasoh. All Rights Reserved.**

本ドキュメントの著作権はYaaasohに帰属します。引用部分については各引用元のライセンスが適用されます。
