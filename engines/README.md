# Engines Directory

JSBSim標準のenginesディレクトリです。エンジン定義XMLファイルを配置します。

## 概要

このプロジェクトでは、**電動モーター推進系**を使用するため、従来型のエンジンXMLファイルは不要です。

## 電動モーター推進系の実装

本実装では、推進系を以下のように実装しています:

1. **T_03_Propulsion シート**でモーター・プロペラパラメータを入力
2. **generate_jsbsim_from_gsheet.py**が自動的に:
   - 推力テーブル（Thrust Table）を生成
   - `<propulsion>`セクションに組み込み
   - メインXMLファイル内に統合

### 生成される推進系構造

```xml
<propulsion>
  <engine file="electric_motor">
    <thruster file="propeller">
      <!-- 推力テーブルが埋め込まれる -->
    </thruster>
  </engine>
</propulsion>
```

## 従来型エンジンを使用する場合

ガソリンエンジン等を使用する場合は、JSBSim標準のエンジンXMLファイルをここに配置します。

**例**: `engines/myengine.xml`

```xml
<?xml version="1.0"?>
<piston_engine name="myengine">
  <displacement unit="IN3"> 91 </displacement>
  <maxhp> 10.0 </maxhp>
  <cycles> 2.0 </cycles>
  <idlerpm> 2000 </idlerpm>
  <maxrpm> 10000 </maxrpm>
  <!-- その他のパラメータ -->
</piston_engine>
```

機体XMLから参照:
```xml
<engine file="myengine">
  <!-- engine参照 -->
</engine>
```

## 参考資料

- [JSBSim Engine Configuration](http://jsbsim.sourceforge.net/JSBSimReferenceManual.pdf) - Chapter 8

---

**作成日**: 2025-10-18
**対応推進系**: 電動モーター（推力テーブル方式）
**JSBSim対応バージョン**: 1.1.0以上

---

**© 2025 Yaaasoh. All Rights Reserved.**

本ドキュメントの著作権はYaaasohに帰属します。引用部分については各引用元のライセンスが適用されます。
