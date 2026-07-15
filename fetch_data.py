import yfinance as yf
import pandas as pd
import time
import os
from datetime import datetime 
import pytz 

# tickers.txtから銘柄リストを読み込む
try:
    with open('tickers.txt', 'r') as f:
        tickers = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print("エラー: tickers.txt が見つかりません。")
    tickers = []

data_list = []
jst = pytz.timezone('Asia/Tokyo')

for i, ticker in enumerate(tickers):
    print(f"[{i+1}/{len(tickers)}] {ticker} のデータを取得中...")
    
    # 【追加】計算用変数の初期化（エラー回避のため）
    bias5, bias25, vol_ratio5, vol_ratio20 = None, None, None, None
    equity_ratio, turnover, leverage = None, None, None
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 【重要】infoが空（データが取れない）かチェック
        if not info or 'regularMarketPrice' not in info and 'currentPrice' not in info:
             # ※一部の環境では info.get('symbol') が取れるかでも判定可能
             if 'symbol' not in info:
                 print(f"  -> {ticker} はデータが見つかりません。スキップします。")
                 continue # 次の銘柄へ

        hist = stock.history(period="3mo")
        fetch_time = datetime.now(jst).strftime("%m-%d %H:%M")

        # セクター・業界処理
        sector = info.get('sector')
        industry = info.get('industry', '-')
        industry_jp = industry
        if "Semiconductor Equipment" in industry:
            industry_jp = "装置・材料"
        elif "Semiconductors" in industry:
            industry_jp = "半導体メーカー"
        elif "Electronic Components" in industry:
            industry_jp = "電子部品"
        
        # 株価計算
        if not hist.empty and len(hist) >= 25:
            current_price = hist['Close'].iloc[-1]
            sma5 = hist['Close'].rolling(window=5).mean().iloc[-1]
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

        # 財務データ処理
        try:
            bs = stock.balance_sheet
            if not bs.empty:
                # 取得するキーの揺らぎに対応
                total_assets = bs.loc['Total Assets'].iloc[0] if 'Total Assets' in bs.index else None
                equity = bs.loc['Stockholders Equity'].iloc[0] if 'Stockholders Equity' in bs.index else \
                         bs.loc['Total Equity Gross Minority Interest'].iloc[0] if 'Total Equity Gross Minority Interest' in bs.index else None
                
                if total_assets and equity:
                    equity_ratio = (equity / total_assets) * 100
                    leverage = total_assets / equity
                
                revenue = info.get('totalRevenue')
                if revenue and total_assets and total_assets != 0:
                    turnover = revenue / total_assets
        except Exception as e_bs:
             print(f"  [{ticker}] 財務データ取得スキップ: {e_bs}")

        data = {
            "取得日時": fetch_time,
            "銘柄CD": ticker,
            "銘柄名": info.get('shortName') or info.get('longName') or "-",
            "セクター": sector,
            "業界": industry_jp,
            "PER(予)": info.get('forwardPE'),
            "PBR(実)": info.get('priceToBook'),
            "利回(予)": round(div_yield * 100, 2) if (div_yield := info.get('dividendYield')) else None,
            "ROE(実)": round(roe * 100, 2) if (roe := info.get('returnOnEquity')) else None,
            "直近株価": current_price,
            "目標株価": info.get('targetMeanPrice'),
            "売上高": info.get('totalRevenue'),
            "当期純利益": info.get('netIncomeToCommon'),
            "総資産": total_assets,
            "自己資本": equity,
            "自己資本比率": round(equity_ratio, 2) if equity_ratio else None,
            "売上高利益率": round(margin * 100, 2) if (margin := info.get('profitMargins')) else None,
            "総資本回転率": round(turnover, 2) if turnover else None,
            "財務レバレッジ": round(leverage, 2) if leverage else None,
            "移動平均乖離率(5d)": round(bias5, 2) if bias5 is not None else None,
            "移動平均乖離率(25d)": round(bias25, 2) if bias25 is not None else None,
            "出来高(5d)": round(vol_ratio5, 2) if vol_ratio5 is not None else None,
            "出来高(20d)": round(vol_ratio20, 2) if vol_ratio20 is not None else None
        }
        data_list.append(data)
        print(f"  -> {ticker} 取得成功")
        
    except Exception as e:
        print(f"  -> 致命的なエラー ({ticker}): {e}")
    
    # 【重要】レート制限回避
    # 20件ごとに10秒休む。それ以外は1秒待機（トータル時間を短縮）
    if (i + 1) % 20 == 0:
        time.sleep(10)
    else:
        time.sleep(1)

# 保存処理
file_path = os.path.join(os.getcwd(), 'data.csv')
if data_list:
    df = pd.DataFrame(data_list)
    file_path = os.path.join(os.getcwd(), 'data.csv')
    df.to_csv(file_path, index=False)
    # ファイルのタイムスタンプを強制的に現在時刻に更新
    os.utime(file_path, None) 
    print(f"完了: {len(data_list)} 件のデータを保存しました。")
else:
    print("データが取得できませんでした。")
    pd.DataFrame(columns=["銘柄CD", "銘柄名"]).to_csv(file_path, index=False)
