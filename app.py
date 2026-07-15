import streamlit as st
import yfinance as yf

st.title("半導体銘柄ファンダメンタルズ確認")

# ユーザーが銘柄コードを入力できる枠を作成
ticker = st.text_input("銘柄コードを入力（日本株は末尾に .T を付ける）", "8035.T")

# ボタンを押した時の処理
if st.button("データ取得"):
    with st.spinner('データ取得中...'):
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 取得したデータを画面に表示
        st.subheader(f"【{ticker}】のデータ")
        st.write(f"実績PER: {info.get('trailingPE', 'データなし')} 倍")
        st.write(f"予想PER: {info.get('forwardPE', 'データなし')} 倍")
        
        # ROEは小数が返ってくるので、%表記に変換
        roe = info.get('returnOnEquity')
        if roe:
            st.write(f"ROE: {roe * 100:.2f} %")
        else:
            st.write("ROE: データなし")
