import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import os
import streamlit as st

def draw_heatmap(stock_code, start_date):
    # 判断子文件夹名称
    if '.' in stock_code:
        if '.HK' in stock_code:
            subfolder_name = 'HK'
        else:
            st.write(f"Unknown stock code {stock_code}, cannot determine folder.")
            return
    elif '^' in stock_code:
        subfolder_name = 'INDEX'
    else:  # default to US stocks if no special symbols are included
        subfolder_name = 'US'
    
    # 定义子文件夹名称
    data_folder = f'data/{subfolder_name}'
    
    # 建立讀取數據的完整路徑
    data_file_path = os.path.join(data_folder, f'{stock_code}.csv')
    
    # 讀取數據
    df = pd.read_csv(data_file_path)
    
    # 確保 'Date' 是 datetime 格式
    df['Date'] = pd.to_datetime(df['Date'])
    
    # 如果指定了開始日期，則只保留從該日期後的數據
    if start_date is not None:
        df = df[df['Date'] >= start_date]
    
    # 設置 'Date' 為 index
    df = df.set_index('Date')
    
    # 用 resample 將數據由日轉換為月，並取每月最後一個交易日的收盤價格
    df_monthly = df['Close'].resample('M').last()
    
    # 計算每月回報
    df_return = df_monthly.pct_change()
    
    # 將 Series 轉換為 dataframe 並添加年份和月份欄位，以便創建熱圖
    df_return = df_return.reset_index()
    df_return['Year'] = df_return['Date'].dt.year
    df_return['Month'] = df_return['Date'].dt.strftime('%b')  # 使用 %b 來獲得月份的縮寫形式
    
    # 將月份轉換為類別變量並指定其順序
    months_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    df_return['Month'] = pd.Categorical(df_return['Month'], categories=months_order, ordered=True)
    
    # 轉換為 pivot table
    df_pivot = df_return.pivot(index='Year', columns='Month', values='Close')
    
    # 計算每個月的平均回報
    avg_return = df_pivot.mean()
    
    # 新增一行顯示每月平均回報
    df_pivot.loc['Avg'] = avg_return
    
    # 繪製熱圖
    plt.figure(figsize=(10, 8))
    ax = sns.heatmap(df_pivot.loc[sorted(list(set(df_pivot.index)-{'Avg'}))+['Avg']], cmap='RdYlGn', annot=True, fmt=".1%", vmin=-0.05, vmax=0.05)  # 在這裡設定 vmin 和 vmax 的值
    plt.title(f'{stock_code} Monthly Returns')  # 在這裡插入股票代碼
    
    # 添加 '%' 到色條刻度標籤
    def to_percent(x, position):
        return f'{100*x:.0f}%'
    
    formatter = FuncFormatter(to_percent)
    cbar = ax.collections[0].colorbar
    cbar.ax.yaxis.set_major_formatter(formatter)
    
    st.pyplot(plt)
    
def main():
    st.title("Heatmap Generator")
    stock_code = st.text_input("Enter Stock Code", '')  # 用户输入的股票代码
    
    if stock_code:
        # 定义子文件夹名称
        subfolder_name = 'HK' if '.HK' in stock_code else 'INDEX' if '^' in stock_code else 'US'
        data_folder = f'data/{subfolder_name}'
        data_file_path = os.path.join(data_folder, f'{stock_code}.csv')
        
        if os.path.exists(data_file_path):
            df = pd.read_csv(data_file_path)
            df['Date'] = pd.to_datetime(df['Date'])
            earliest_date = df['Date'].min()
            latest_date = df['Date'].max()
        else:
            earliest_date = None
            latest_date = None
    else:
        earliest_date = None
        latest_date = None

    options = ['Max', 'Last 20 years', 'Last 10 years', 'Last 5 years']
    selected_option = st.radio("Select date range", options)

    if selected_option == 'Max':
        selected_start_date = earliest_date
    elif selected_option == 'Last 20 years':
        selected_start_date = max(earliest_date, latest_date - pd.DateOffset(years=20))
    elif selected_option == 'Last 10 years':
        selected_start_date = max(earliest_date, latest_date - pd.DateOffset(years=10))
    elif selected_option == 'Last 5 years':
        selected_start_date = max(earliest_date, latest_date - pd.DateOffset(years=5))

    if stock_code and selected_start_date:  # if stock code and start date are not empty
        draw_heatmap(stock_code, selected_start_date.strftime('%Y-%m-%d'))



if __name__ == "__main__":
    main()