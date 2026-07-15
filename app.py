import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(layout="wide") # 表を画面いっぱいに広く表示する設定

st.title("半導体銘柄データトラッカー")

# 複数銘柄をカンマ区切りで入力できる仕様に変更
tickers_input = st.text_input("銘柄コードを入力（カンマ区切りで複数可。末尾に .T を付ける）", "8035.T, 6146.T, 6920.T")

if st.button("データ取得"):
    with st.spinner('データ取得中...（複数銘柄の場合は少し時間がかかります）'):
        # 入力された文字をカンマで分割し、リスト化する
        tickers = [t.strip() for t in tickers_input.split(",") if t.strip()]
        data_list = []
        
        for ticker in tickers:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 過去3ヶ月の株価データを取得（移動平均と出来高の計算用）
            hist = stock.history(period="3mo")
            
            # yuyuサイト特有のテクニカル指標を計算
            if not hist.empty and len(hist) >= 25:
                current_price = hist['Close'].iloc[-1]
                # 25日移動平均乖離率
                sma25 = hist['Close'].rolling(window=25).mean().iloc[-1]
                bias25 = ((current_price - sma25) / sma25) * 100
                
                # 出来高率（本日出来高 ÷ 20日平均）
                vol_today = hist['Volume'].iloc[-1]
                vol_avg20 = hist['Volume'].rolling(window=20).mean().iloc[-1]
                vol_ratio = vol_today / vol_avg20 if vol_avg20 > 0 else 0
            else:
                current_price = info.get('currentPrice')
                bias25 = None
                vol_ratio = None

            # ファンダメンタルズ指標の取得
            roe = info.get('returnOnEquity')
            div_yield = info.get('dividendYield')
            margin = info.get('profitMargins')

            # テーブルの「横カラム」になるデータを辞書にまとめる
            data = {
                "銘柄コード": ticker,
                "現在株価": current_price,
                "出来高率(20日比)": round(vol_ratio, 2) if vol_ratio else None,
                "25日線乖離率(%)": round(bias25, 2) if bias25 else None,
                "PER(予)": info.get('forwardPE'),
                "PBR(実)": info.get('priceToBook'),
                "ROE(実) %": round(roe * 100, 2) if roe else None,
                "配当利回り(%)": round(div_yield * 100, 2) if div_yield else None,
                "売上高": info.get('totalRevenue'),
                "当期純利益": info.get('netIncomeToCommon'),
                "売上高利益率(%)": round(margin * 100, 2) if margin else None,
                "目標株価": info.get('targetMeanPrice')
            }
            data_list.append(data)
            
        # 取得したデータをPandasのデータフレーム（表）に変換して画面に表示
        if data_list:
            df = pd.DataFrame(data_list)
            df.set_index("銘柄コード", inplace=True)
            st.dataframe(df, use_container_width=True)
