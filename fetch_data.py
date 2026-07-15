import yfinance as yf
import pandas as pd
import time
import os

# tickers.txtから銘柄リストを読み込む
try:
    with open('tickers.txt', 'r') as f:
        tickers = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print("エラー: tickers.txt が見つかりません。")
    tickers = []

data_list = []

for ticker in tickers:
    print(f"{ticker} のデータを取得中...")
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="3mo")

        if not hist.empty and len(hist) >= 25:
            current_price = hist['Close'].iloc[-1]
            sma25 = hist['Close'].rolling(window=25).mean().iloc[-1]
            bias5 = ((current_price - sma5) / sma5) * 100
            bias25 = ((current_price - sma25) / sma25) * 100
            vol_today = hist['Volume'].iloc[-1]
            vol_avg5 = hist['Volume'].rolling(window=5).mean().iloc[-1]
            vol_ratio5 = vol_today / vol_avg5 if vol_avg5 > 0 else None
            vol_avg20 = hist['Volume'].rolling(window=20).mean().iloc[-1]
            vol_ratio20 = vol_today / vol_avg20 if vol_avg20 > 0 else None
        else:
            current_price = info.get('currentPrice')
            bias25, vol_ratio5, vol_ratio20 = None, None, None

        total_assets, equity, equity_ratio, turnover, leverage = None, None, None, None, None
        try:
            bs = stock.balance_sheet
            if not bs.empty:
                if 'Total Assets' in bs.index: total_assets = bs.loc['Total Assets'].iloc[0]
                if 'Stockholders Equity' in bs.index: equity = bs.loc['Stockholders Equity'].iloc[0]
                elif 'Total Equity Gross Minority Interest' in bs.index: equity = bs.loc['Total Equity Gross Minority Interest'].iloc[0]
                if total_assets and equity:
                    equity_ratio = (equity / total_assets) * 100
                    leverage = total_assets / equity
                revenue = info.get('totalRevenue')
                if revenue and total_assets:
                    turnover = revenue / total_assets
        except Exception as e_bs:
             print(f"  [{ticker}] 貸借対照表の取得でエラー: {e_bs}")

        roe = info.get('returnOnEquity')
        div_yield = info.get('dividendYield')
        margin = info.get('profitMargins')

        data = {
            "銘柄CD": ticker,
            "銘柄名": info.get('shortName') or info.get('longName') or "-",
            "セクター": sector,
            "PER(予)": info.get('forwardPE'),
            "PBR(実)": info.get('priceToBook'),
            "利回(予)": round(div_yield * 100, 2) if div_yield else None,
            "ROE(実)": round(roe * 100, 2) if roe else None,
            "直近株価": current_price,
            "目標株価": info.get('targetMeanPrice'),
            "売上高": info.get('totalRevenue'),
            "当期純利": info.get('netIncomeToCommon'),
            "総資産": total_assets,
            "自己資本": equity,
            "自己資本比率": round(equity_ratio, 2) if equity_ratio else None,
            "売上高利益率": round(margin * 100, 2) if margin else None,
            "総資本回転率": round(turnover, 2) if turnover else None,
            "財務レバ": round(leverage, 2) if leverage else None,
            "移動平均乖離率(5d)": round(bias5, 2) if bias5 else None,
            "移動平均乖離率(25d)": round(bias25, 2) if bias25 else None,
            "出来高(5d)": round(vol_ratio5, 2) if vol_ratio5 else None,
            "出来高(20d)": round(vol_ratio20, 2) if vol_ratio20 else None
        }
        data_list.append(data)
        print(f"  -> {ticker} の取得成功")
        
    except Exception as e:
        print(f"  -> 致命的なエラー発生 ({ticker}): {e}")
    
    # API制限を回避するため6秒待機
    time.sleep(6)

# データが1件以上あればCSVとして保存
if data_list:
    df = pd.DataFrame(data_list)
    df.to_csv('data.csv', index=False)
    print(f"data.csv を作成しました（合計 {len(data_list)} 件）")
else:
    # 1件も取得できなかった場合は、空のデータフレームを作成して保存する
    print("データが1件も取得できませんでした。空の data.csv を作成します。")
    # 最低限の構造だけを持つ空のCSVを作成
    empty_df = pd.DataFrame(columns=["銘柄コード", "銘柄名"])
    empty_df.to_csv('data.csv', index=False)
