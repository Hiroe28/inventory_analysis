#inventory_analyzer.py
import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib

class InventoryAnalyzer:
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self._load_data()

    def _load_data(self):
        """必要なデータを読み込む"""
        self.sales_data = self.data_loader.load_sales_data()
        self.inventory_control = self.data_loader.load_inventory_control()
        self.sku_items = self.data_loader.load_sku_items()

    def calculate_inventory_flow(self, sku_id: str, initial_stock: int = 500,
                            lead_time_type: str = 'average', 
                            warning_stock_ratio: float = 0.2,
                            reorder_months: float = 3.0,
                            min_order_interval_days: int = 7) -> tuple:
        """在庫推移、発注、入荷データを計算

        Parameters
        ----------
        sku_id : str
            分析対象のSKU ID
        initial_stock : int
            初期在庫数（デフォルト: 500）
        lead_time_type : str
            'average' または 'maximum' を指定
        warning_stock_ratio : float
            安全在庫の追加率（リードタイム中の予想消費量に対する割合）
        reorder_months : float
            発注量の月数（平均月間販売数の何ヶ月分か）
        min_order_interval_days : int
            最小発注間隔（日数）

        Returns
        -------
        tuple
            (在庫推移データ, 発注データ, 入荷データ, 警告在庫水準)
        """
        # SKU固有の情報を取得
        sku_info = self.inventory_control[self.inventory_control['SKU ID'] == sku_id].iloc[0]
        lead_time = sku_info['Maximum Lead Time (days)'] if lead_time_type == 'maximum' else sku_info['Average Lead Time (days)']

        # 対象SKUの売上データを取得し日付でソート
        sku_sales = self.sales_data[self.sales_data['SKU ID'] == sku_id].copy()
        sku_sales = sku_sales.sort_values('Order Date')

        # 平均販売数の計算
        total_months = (sku_sales['Order Date'].max() - sku_sales['Order Date'].min()).days / 30
        avg_monthly_sales = sku_sales['Order Quantity'].sum() / total_months if total_months > 0 else 0
        avg_daily_sales = avg_monthly_sales / 30

        # 警告在庫水準（発注点）の計算
        safety_stock = avg_daily_sales * lead_time  # リードタイム中の予想消費量
        warning_level = safety_stock * (1 + warning_stock_ratio)  # 安全在庫を追加

        # 発注量の計算
        reorder_quantity = int(avg_monthly_sales * reorder_months)

        # 日付範囲の作成
        date_range = pd.date_range(
            start=sku_sales['Order Date'].min(),
            end=sku_sales['Order Date'].max(),
            freq='D'
        )

        # 在庫推移、発注、入荷を計算
        inventory_flow = pd.DataFrame(index=date_range)
        inventory_flow['current_stock'] = initial_stock
        orders = []
        deliveries = []
        
        # 日々の売上を集計
        daily_sales = sku_sales.groupby('Order Date')['Order Quantity'].sum()

        last_order_date = None

        for date in date_range:
            # 前日までの在庫を取得
            if date == date_range[0]:
                prev_stock = initial_stock
            else:
                prev_stock = inventory_flow.loc[date - pd.Timedelta(days=1), 'current_stock']

            # 当日の売上を反映
            sales_quantity = daily_sales[date] if date in daily_sales.index else 0
            current_stock = prev_stock - sales_quantity

            # 当日の入荷を反映（この処理を発注判断の前に移動）
            delivery = [d for d in deliveries if d['date'] == date]
            delivery_quantity = delivery[0]['quantity'] if delivery else 0
            current_stock += delivery_quantity

            # 未着の入荷予定を確認（この時点での未着分のみを考慮）
            pending_deliveries = [d for d in deliveries if d['date'] > date]
            pending_quantity = sum(d['quantity'] for d in pending_deliveries)

            # 発注判断（現在庫 + 入荷予定 が警告水準以下、かつ前回発注からの間隔チェック）
            should_order = (current_stock + pending_quantity) <= warning_level

            if should_order and (
                last_order_date is None or 
                (date - last_order_date).days >= min_order_interval_days
            ):
                # 発注処理
                orders.append({
                    'date': date,
                    'quantity': reorder_quantity
                })
                last_order_date = date
                
                # 入荷予定を登録
                delivery_date = date + pd.Timedelta(days=lead_time)
                deliveries.append({
                    'date': delivery_date,
                    'quantity': reorder_quantity
                })

            # 在庫推移を記録
            inventory_flow.loc[date, 'current_stock'] = current_stock


        # 発注と入荷のDataFrame作成
        orders_df = pd.DataFrame(orders)
        deliveries_df = pd.DataFrame(deliveries)



        return inventory_flow, orders_df, deliveries_df, warning_level

if __name__ == "__main__":
    from data_loader import DataLoader
    import pandas as pd
    from datetime import datetime, timedelta
    import matplotlib.pyplot as plt

    # データローダーの初期化とアナライザーの作成
    loader = DataLoader("Dynamic Inventory Analytics.xlsx")
    analyzer = InventoryAnalyzer(loader)

    # 利用可能なSKU一覧を表示
    sku_info = pd.merge(
        analyzer.inventory_control[['SKU ID']],
        analyzer.sku_items[['SKU ID', 'SKU Name']],
        on='SKU ID'
    )
    print("\n利用可能なSKU一覧:")
    for _, row in sku_info.iterrows():
        print(f"SKU ID: {row['SKU ID']} - {row['SKU Name']}")

    # ユーザー入力の受付
    default_sku = analyzer.inventory_control['SKU ID'].iloc[0]
    print(f"\nデフォルトのSKU ID: {default_sku}")
    sku_id = input("分析するSKU IDを入力してください（デフォルトの場合はEnter）: ").strip() or default_sku

    display_days = input("表示する期間を入力してください（'all'または日数、デフォルト: 30）: ").strip().lower()
    if display_days == 'all':
        display_days = None  # 全期間表示用
    else:
        display_days = int(display_days) if display_days else 30

    initial_stock = input("初期在庫数を入力してください（デフォルト: 500）: ").strip()
    initial_stock = int(initial_stock) if initial_stock else 500

    reorder_months = input("発注量の月数を入力してください（平均月間販売数の何ヶ月分か、デフォルト: 3）: ").strip()
    reorder_months = float(reorder_months) if reorder_months else 3.0

    lead_time_type = input("使用するリードタイム（'average' または 'maximum'）を入力してください（デフォルト: average）: ").strip().lower()
    lead_time_type = lead_time_type if lead_time_type in ['average', 'maximum'] else 'average'

    # 在庫推移データの取得
    timeline_data, orders_df, deliveries_df, warning_level = analyzer.calculate_inventory_flow(
        sku_id, 
        initial_stock=initial_stock,
        lead_time_type=lead_time_type,
        reorder_months=reorder_months
    )
    
    # SKU名を取得
    sku_name = analyzer.sku_items[
        analyzer.sku_items['SKU ID'] == sku_id
    ]['SKU Name'].iloc[0]
    
    # 表示期間の設定
    if display_days:
        end_date = timeline_data.index.max()
        start_date = end_date - timedelta(days=display_days)
        timeline_data = timeline_data[start_date:end_date]
        orders_df = orders_df[orders_df['date'].between(start_date, end_date)]
        deliveries_df = deliveries_df[deliveries_df['date'].between(start_date, end_date)]
    else:
        start_date = timeline_data.index.min()
        end_date = timeline_data.index.max()
    
    # グラフ表示
    plt.figure(figsize=(15, 10))
    
    # 在庫推移のプロット
    plt.plot(timeline_data.index, timeline_data['current_stock'], 
            label='在庫推移', color='blue', linewidth=2)
    
    # グラフの上下に余白を追加するため、y軸の範囲を設定
    y_min = min(0, timeline_data['current_stock'].min())
    y_max = timeline_data['current_stock'].max()
    margin = (y_max - y_min) * 0.2
    plt.ylim(y_min - margin, y_max + margin)
    
    # 発注のプロット（下向き矢印）
    arrow_start_top = y_max + margin * 0.8
    arrow_length = margin * 0.3
    
    for _, row in orders_df.iterrows():
        plt.arrow(row['date'], arrow_start_top,
                 0, -arrow_length,
                 color='red', width=1, head_width=2, head_length=margin * 0.1,
                 length_includes_head=True, alpha=0.7)
        plt.text(row['date'], arrow_start_top + margin * 0.1,
                f'発注\n{int(row["quantity"]):,}個', 
                ha='center', va='bottom', color='red')

    # 入荷のプロット（上向き矢印）
    arrow_start_bottom = y_min - margin * 0.8
    
    for _, row in deliveries_df.iterrows():
        plt.arrow(row['date'], arrow_start_bottom,
                 0, arrow_length,
                 color='green', width=1, head_width=2, head_length=margin * 0.1,
                 length_includes_head=True, alpha=0.7)
        plt.text(row['date'], arrow_start_bottom - margin * 0.1,
                f'入荷\n{int(row["quantity"]):,}個', 
                ha='center', va='top', color='green')

    # 警告在庫水準の表示
    plt.axhline(y=warning_level, color='r', linestyle='--', label='警告在庫水準')
    
    
    # グラフの設定
    lead_time_text = "最大リードタイム" if lead_time_type == 'maximum' else "平均リードタイム"
    plt.title(f'在庫推移と発注・入荷タイミング - {sku_name} ({sku_id})\n'
             f'期間: {start_date.strftime("%Y-%m-%d")} から {end_date.strftime("%Y-%m-%d")}\n'
             f'使用リードタイム: {lead_time_text} / 初期在庫: {initial_stock:,}個\n'
             f'発注量: 平均月間販売数の{reorder_months:.1f}ヶ月分')
    plt.xlabel('日付')
    plt.ylabel('在庫数量')
    plt.grid(True, alpha=0.3)
    
    # 凡例の設定
    plt.legend(loc='center right')
    
    # x軸の日付表示を調整
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()