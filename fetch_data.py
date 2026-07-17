import yfinance as yf
import pandas as pd
import time
import os
from datetime import datetime 
import pytz 

# tickers.txtから銘柄リストを読み込む
tickers_list = []
try:
    with open('tickers.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            
            # maxsplit=2 で「銘柄CD」「銘柄名」「セクター」を取得
            parts = line.split(maxsplit=2)
            
            if len(parts) >= 1:
                tickers_list.append({
                    'code': parts[0],
                    'name': parts[1] if len(parts) > 1 else None,
                    'sector': parts[2] if len(parts) > 2 else None
                })
except FileNotFoundError:
    print("エラー: tickers.txt が見つかりません。")

data_list = []
jst = pytz.timezone('Asia/Tokyo')

for i, entry in enumerate(tickers_list):
    ticker = entry['code']
    manual_name = entry['name']
    manual_sector = entry['sector']
    
    print(f"[{i+1}/{len(tickers_list)}] {ticker} のデータを取得中...")
    
    # 計算用変数の初期化
    bias5, bias25, vol_ratio5, vol_ratio20 = None, None, None, None
    equity_ratio, turnover, leverage = None, None, None
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info or ('regularMarketPrice' not in info and 'currentPrice' not in info and 'symbol' not in info):
            print(f"  -> {ticker} はデータが見つかりません。スキップします。")
            continue

        hist = stock.history(period="3mo")
        fetch_time = datetime.now(jst).strftime("%m-%d %H:%M")

        # 株価計算
        current_price = None
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

        # 利回り計算（dividendRate ÷ 現在株価 で自前算出）
        dividend_rate = info.get('dividendRate')

        # 財務データ処理
        total_assets, equity = None, None
        try:
            bs = stock.balance_sheet
            if not bs.empty:
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
            "銘柄CD": ticker,
            "銘柄名": manual_name or info.get('shortName') or info.get('longName') or "-",
            "取得日時": fetch_time,
            "区分": manual_sector or info.get('sector') or "-",
            "PER(予)": info.get('forwardPE'),
            "PBR(実)": info.get('priceToBook'),
            "ROE(実)": round(roe * 100, 2) if (roe := info.get('returnOnEquity')) else None,
            "配当(予)": dividend_rate,  
            "直近株価": current_price,
            "目標株価": info.get('targetMeanPrice'),
            "売上高": info.get('totalRevenue'),
            "出来高": vol_today if vol_today is not None else "0",
            "-比(5d)": round(vol_ratio5, 2) if vol_ratio5 is not None else None,
            "-比(20d)": round(vol_ratio20, 2) if vol_ratio20 is not None else None,
            "乖離率(5d)": round(bias5, 2) if bias5 is not None else None,
            "乖離率(25d)": round(bias25, 2) if bias25 is not None else None,
            "当期純利益": info.get('netIncomeToCommon'),
            "総資産": total_assets,
            "自己資本": equity,
            "自資比": round(equity_ratio, 2) if equity_ratio else None,
            "売上高利益率": round(margin * 100, 2) if (margin := info.get('profitMargins')) else None,
            "総資本回転率": round(turnover, 2) if turnover else None,
            "財務レバレッジ": round(leverage, 2) if leverage else None,
        }
        data_list.append(data)
        print(f"  -> {ticker} 取得成功")
        
    except Exception as e:
        print(f"  -> 致命的なエラー ({ticker}): {e}")
    
    if (i + 1) % 20 == 0:
        time.sleep(10)
    else:
        time.sleep(1)

# 保存処理
file_path = os.path.join(os.getcwd(), 'data.csv')
if data_list:
    df = pd.DataFrame(data_list)
    df.to_csv(file_path, index=False)
    os.utime(file_path, None) 
    print(f"完了: {len(data_list)} 件のデータを保存しました。")
else:
    print("データが取得できませんでした。")
