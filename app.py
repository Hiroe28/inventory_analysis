# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from data_loader import DataLoader
from inventory_analyzer import InventoryAnalyzer

st.set_page_config(layout="wide")  # アプリ起動時に実行

def main():
    st.title('在庫分析ダッシュボード')

    # データの読み込み
    @st.cache_data
    def load_data():
        loader = DataLoader("Dynamic Inventory Analytics.xlsx")
        analyzer = InventoryAnalyzer(loader)
        
        # SKU情報の作成
        sku_info = pd.merge(
            analyzer.inventory_control[['SKU ID']],
            analyzer.sku_items[['SKU ID', 'SKU Name']],
            on='SKU ID'
        )
        return analyzer, sku_info

    analyzer, sku_info = load_data()

    # サイドバーでパラメータ設定
    st.sidebar.header('パラメータ設定')

    # SKU選択
    sku_options = {f"{row['SKU ID']} - {row['SKU Name']}": row['SKU ID'] 
                   for _, row in sku_info.iterrows()}
    selected_sku_label = st.sidebar.selectbox(
        'SKU選択',
        options=list(sku_options.keys()),
        index=0
    )
    selected_sku = sku_options[selected_sku_label]

    # 表示期間設定
    max_days = (analyzer.sales_data['Order Date'].max() - 
                analyzer.sales_data['Order Date'].min()).days
    display_days = st.sidebar.slider(
        '表示期間（日数）',
        min_value=7,
        max_value=max_days,
        value=30,
        step=1
    )

    # 初期在庫設定
    initial_stock = st.sidebar.slider(
        '初期在庫数',
        min_value=0,
        max_value=10000,
        value=500,
        step=100
    )

    # 発注量の月数設定
    reorder_months = st.sidebar.slider(
        '発注量（平均月間販売数の何ヶ月分）',
        min_value=0.0,
        max_value=6.0,
        value=3.0,
        step=0.1
    )

    # リードタイム設定
    lead_time_type = st.sidebar.selectbox(
        'リードタイムタイプ',
        options=['average', 'maximum'],
        format_func=lambda x: '平均リードタイム' if x == 'average' else '最大リードタイム'
    )

    # 警告在庫水準の設定
    warning_stock_ratio = st.sidebar.slider(
        '警告在庫水準（リードタイム中の予想消費量に対する割合）',
        min_value=0.1,
        max_value=0.5,
        value=0.2,
        step=0.05
    )

    # 在庫推移データの取得
    timeline_data, orders_df, deliveries_df, warning_level = analyzer.calculate_inventory_flow(
        selected_sku,
        initial_stock=initial_stock,
        lead_time_type=lead_time_type,
        warning_stock_ratio=warning_stock_ratio,
        reorder_months=reorder_months
    )

    # 表示期間の設定
    end_date = timeline_data.index.max()
    start_date = end_date - timedelta(days=display_days)
    timeline_data = timeline_data[start_date:end_date]
    orders_df = orders_df[orders_df['date'].between(start_date, end_date)]
    deliveries_df = deliveries_df[deliveries_df['date'].between(start_date, end_date)]

    # グラフの作成
    fig, ax = plt.subplots(figsize=(15, 8))
    fig, ax = plt.subplots(figsize=(20, 10))  # サイズを大きく

    # 在庫推移のプロット
    ax.plot(timeline_data.index, timeline_data['current_stock'],
            label='在庫推移', color='blue', linewidth=2)

    # グラフの上下に余白を追加
    y_min = min(0, timeline_data['current_stock'].min())
    y_max = timeline_data['current_stock'].max()
    margin = (y_max - y_min) * 0.2
    ax.set_ylim(y_min - margin, y_max + margin)

    # 発注のプロット（下向き矢印）
    arrow_start_top = y_max + margin * 0.8
    arrow_length = margin * 0.3

    for _, row in orders_df.iterrows():
        ax.arrow(row['date'], arrow_start_top,
                0, -arrow_length,
                color='red', width=1, head_width=2, head_length=margin * 0.1,
                length_includes_head=True, alpha=0.7)
        ax.text(row['date'], arrow_start_top + margin * 0.1,
                f'発注\n{int(row["quantity"]):,}個',
                ha='center', va='bottom', color='red')

    # 入荷のプロット（上向き矢印）
    arrow_start_bottom = y_min - margin * 0.8

    for _, row in deliveries_df.iterrows():
        ax.arrow(row['date'], arrow_start_bottom,
                0, arrow_length,
                color='green', width=1, head_width=2, head_length=margin * 0.1,
                length_includes_head=True, alpha=0.7)
        ax.text(row['date'], arrow_start_bottom - margin * 0.1,
                f'入荷\n{int(row["quantity"]):,}個',
                ha='center', va='top', color='green')

    # 警告在庫水準の表示
    ax.axhline(y=warning_level, color='r', linestyle='--', label='警告在庫水準')

    # グラフの設定
    lead_time_text = "最大リードタイム" if lead_time_type == 'maximum' else "平均リードタイム"
    ax.set_title(f'在庫推移と発注・入荷タイミング\n'
                f'期間: {start_date.strftime("%Y-%m-%d")} から {end_date.strftime("%Y-%m-%d")}\n'
                f'使用リードタイム: {lead_time_text} / 初期在庫: {initial_stock:,}個\n'
                f'発注量: 平均月間販売数の{reorder_months:.1f}ヶ月分')
    ax.set_xlabel('日付')
    ax.set_ylabel('在庫数量')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='center right')

    plt.xticks(rotation=45)

    
    plt.tight_layout()

    # Streamlitでグラフを表示
    st.pyplot(fig)

    # 統計情報の表示
    st.subheader('統計情報')
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "平均在庫数",
            f"{int(timeline_data['current_stock'].mean()):,}個"
        )

    with col2:
        st.metric(
            "最小在庫数",
            f"{int(timeline_data['current_stock'].min()):,}個"
        )

    with col3:
        st.metric(
            "最大在庫数",
            f"{int(timeline_data['current_stock'].max()):,}個"
        )

    # 発注・入荷履歴の表示
    if not orders_df.empty:
        st.subheader('発注履歴')
        st.dataframe(
            orders_df.rename(columns={'date': '発注日', 'quantity': '発注数量'})
            .set_index('発注日')
        )

    if not deliveries_df.empty:
        st.subheader('入荷予定')
        st.dataframe(
            deliveries_df.rename(columns={'date': '入荷予定日', 'quantity': '入荷数量'})
            .set_index('入荷予定日')
        )

if __name__ == "__main__":
    main()