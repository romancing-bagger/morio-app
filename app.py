import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(layout="wide")

st.title("ヒリアテーブル（半導体・スイング銘柄分析）")

# 複数銘柄をカンマ区切りで入力
tickers_input = st.text_input("銘柄コードを入力（カンマ区切り。末尾に .T を付ける）", "8035.T, 6146.T, 6920.T")

if st.button("データ取得"):
    with st.spinner('財務データと株価データを取得・計算中...'):
        tickers = [t.strip() for t in tickers_input.split(",") if t.strip()]
        data_list = []
        
        for ticker in tickers:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="3mo")
            
            # 1. テクニカル指標と需給の計算
            if not hist.empty and len(hist) >= 25:
                current_price = hist['Close'].iloc[-1]
                
                # 25日移動平均乖離率
                sma25 = hist['Close'].rolling(window=25).mean().iloc[-1]
                bias25 = ((current_price - sma25) / sma25) * 100
                
                # 出来高率
                vol_today = hist['Volume'].iloc[-1]
                
                vol_avg5 = hist['Volume'].rolling(window=5).mean().iloc[-1]
                vol_ratio5 = vol_today / vol_avg5 if vol_avg5 > 0 else None
                
                vol_avg20 = hist['Volume'].rolling(window=20).mean().iloc[-1]
                vol_ratio20 = vol_today / vol_avg20 if vol_avg20 > 0 else None
            else:
                current_price = info.get('currentPrice')
                bias25 = None
                vol_ratio5 = None
                vol_ratio20 = None

            # 2. 貸借対照表（バランスシート）からの高度な財務データ算出
            total_assets = None
            equity = None
            equity_ratio = None
            turnover = None
            leverage = None
            
            try:
                bs = stock.balance_sheet
                if not bs.empty:
                    if 'Total Assets' in bs.index:
                        total_assets = bs.loc['Total Assets'].iloc[0]
                    if 'Stockholders Equity' in bs.index:
                        equity = bs.loc['Stockholders Equity'].iloc[0]
                    elif 'Total Equity Gross Minority Interest' in bs.index:
                        equity = bs.loc['Total Equity Gross Minority Interest'].iloc[0]
                        
                    if total_assets and equity:
                        equity_ratio = (equity / total_assets) * 100
                        leverage = total_assets / equity
                    
                    revenue = info.get('totalRevenue')
                    if revenue and total_assets:
                        turnover = revenue / total_assets
            except Exception:
                pass

            # 3. 基礎ファンダメンタルズ
            roe = info.get('returnOnEquity')
            div_yield = info.get('dividendYield')
            margin = info.get('profitMargins')

            # 4. 指定された全カラムを辞書形式で定義
            data = {
                "銘柄コード": ticker,
                "銘柄名": info.get('shortName') or info.get('longName') or "-",
                "PER(予)": info.get('forwardPE'),
                "PBR(実)": info.get('priceToBook'),
                "配当利回り(予)": round(div_yield * 100, 2) if div_yield else None,
                "ROE(実)": round(roe * 100, 2) if roe else None,
                "ROE(予)": None, 
                "自己資本比率": round(equity_ratio, 2) if equity_ratio else None,
                "現在株価": current_price,
                "目標株価": info.get('targetMeanPrice'),
                "売上高": info.get('totalRevenue'),
                "当期純利益": info.get('netIncomeToCommon'),
                "総資産": total_assets,
                "自己資本": equity,
                "売上高当期利益率": round(margin * 100, 2) if margin else None,
                "総資本回転率": round(turnover, 2) if turnover else None,
                "財務レバレッジ": round(leverage, 2) if leverage else None,
                "信用倍率": None, 
                "25日移動平均乖離率": round(bias25, 2) if bias25 else None,
                "出来高(5日平均比)": round(vol_ratio5, 2) if vol_ratio5 else None,
                "出来高率(20日平均比)": round(vol_ratio20, 2) if vol_ratio20 else None,
                "短期投資評価": "-",
                "中期投資評価": "-",
                "長期投資評価": "-"
            }
            data_list.append(data)
            
        # データフレーム（表）の作成と表示
        if data_list:
            df = pd.DataFrame(data_list)
            df.set_index("銘柄コード", inplace=True)
            st.dataframe(df, use_container_width=True)
