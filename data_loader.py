#data_loader.py
import pandas as pd
from pathlib import Path
from typing import Dict, Optional

class DataLoader:
    """データ読み込みを担当するクラス"""
    
    def __init__(self, file_path: str):
        """
        Parameters
        ----------
        file_path : str
            Excelファイルのパス
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        self._sales_data: Optional[pd.DataFrame] = None
        self._inventory_control: Optional[pd.DataFrame] = None
        self._sku_items: Optional[pd.DataFrame] = None


    def load_all_data(self) -> Dict[str, pd.DataFrame]:
        """全てのシートのデータを読み込む"""
        return {
            'sales_data': self.load_sales_data(),
            'inventory_control': self.load_inventory_control(),
            'sku_items': self.load_sku_items()
        }


    def load_sales_data(self) -> pd.DataFrame:
        """Sales Dataシートを読み込む"""
        if self._sales_data is None:
            self._sales_data = pd.read_excel(
                self.file_path,
                sheet_name='Sales Data'
            )
            # 日付型に変換
            self._sales_data['Order Date'] = pd.to_datetime(self._sales_data['Order Date'], errors='coerce')
            
            # Unnamedで始まる列を削除
            self._sales_data = self._sales_data.loc[:, ~self._sales_data.columns.str.startswith('Unnamed:')]
            
            # 列名の末尾のスペースを削除（'Order Number 'のような列名の修正）
            self._sales_data.columns = self._sales_data.columns.str.strip()
        
        return self._sales_data


    def load_inventory_control(self) -> pd.DataFrame:
        """Inventory Controlシートを読み込む"""
        if self._inventory_control is None:
            self._inventory_control = pd.read_excel(
                self.file_path,
                sheet_name='Inventory Control'
            )
            
            # リードタイム列を数値型に変換
            # （Excel で日付型として保存されていた場合などを想定）
            for col in ['Average Lead Time (days)', 'Maximum Lead Time (days)']:
                if col in self._inventory_control.columns:
                    self._inventory_control[col] = pd.to_numeric(
                        self._inventory_control[col],
                        errors='coerce'
                    )
        return self._inventory_control


    def load_sku_items(self) -> pd.DataFrame:
        """SKU Itemsシートを読み込む"""
        if self._sku_items is None:
            self._sku_items = pd.read_excel(
                self.file_path,
                sheet_name='SKU Items'
            )
        return self._sku_items


if __name__ == "__main__":
    # 全ての列を表示する設定
    pd.set_option('display.max_columns', None)
    
    # 使用例
    loader = DataLoader("Dynamic Inventory Analytics.xlsx")
    data = loader.load_all_data()
    
    print("Available data keys:", data.keys())

    print("\n=== Sales Data Columns ===")
    print(data['sales_data'].columns.tolist())
    print("\n=== Sales Data sample ===")
    print(data['sales_data'].head())
    
    print("\n=== Inventory Control Columns ===")
    print(data['inventory_control'].columns.tolist())
    print("\n=== Inventory Control sample ===")
    print(data['inventory_control'].head())

    print("\n=== SKU Items Columns ===")
    print(data['sku_items'].columns.tolist())
    print("\n=== SKU Items sample ===")
    print(data['sku_items'].head())