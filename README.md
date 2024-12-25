# 在庫分析ダッシュボード

このプロジェクトは、Dynamic Inventory Datasetを使用して在庫状態を分析・可視化するStreamlitベースのWebアプリケーションです。在庫推移、発注タイミング、入荷予定などをインタラクティブに分析することができます。

## 機能

- **在庫推移の可視化**: SKUごとの在庫レベルの時系列推移を表示
- **発注・入荷管理**: 
  - 自動発注点の計算と可視化
  - リードタイム（平均/最大）に基づく在庫管理
  - 発注履歴と入荷予定の表示
- **カスタマイズ可能なパラメータ**:
  - 初期在庫数の設定
  - 表示期間の調整
  - 発注量の調整（平均月間販売数の倍数）
  - 警告在庫水準の設定
- **統計情報の表示**:
  - 平均在庫数
  - 最小在庫数
  - 最大在庫数

## 必要要件

```
streamlit
pandas
matplotlib
japanize-matplotlib
```

## インストール方法

1. リポジトリのクローン:
```bash
git clone [repository-url]
cd [repository-name]
```

2. 必要なパッケージのインストール:
```bash
pip install -r requirements.txt
```

3. データセットの準備:
- [Kaggle: Dynamic Inventory Dataset](https://www.kaggle.com/datasets/andrewniko/dynamic-inventory-dataset-kaizen-analytics/data)から`Dynamic Inventory Analytics.xlsx`をダウンロード
- プロジェクトのルートディレクトリに配置

## 使用方法

1. Streamlitアプリの起動:
```bash
streamlit run app.py
```

2. ブラウザで表示されるインターフェースで以下のパラメータを設定:
- SKU選択
- 表示期間
- 初期在庫数
- 発注量の月数
- リードタイムタイプ
- 警告在庫水準

## プロジェクト構造

```
.
├── app.py                  # Streamlitアプリケーションのメインファイル
├── data_loader.py         # データ読み込み用クラス
├── inventory_analyzer.py   # 在庫分析ロジック
└── requirements.txt       # 必要なパッケージリスト
```

## データセット構造

このアプリケーションは以下の3つのシートを含むExcelファイルを使用します：

### Sales Data
- 注文番号、注文日、SKU ID、倉庫ID、顧客タイプ、注文数量、単価、収益の情報を含む

### Inventory Control
- SKU ID、ベンダー名、倉庫ID、現在の在庫数量、SKUあたりのコスト、総額、単位、
- 平均リードタイム、最大リードタイム、単価の情報を含む

### SKU Items
- SKU IDとSKU名の対応表

## ライセンス

This project is licensed under the MIT License - see the LICENSE file for details.

## 謝辞

このプロジェクトは[Kaggle: Dynamic Inventory Dataset](https://www.kaggle.com/datasets/andrewniko/dynamic-inventory-dataset-kaizen-analytics/data)のデータを使用しています。
