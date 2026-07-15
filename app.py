import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")
st.title("もりおテーブル")

# GitHub Actionが作成したCSVファイルが存在するかチェック
if os.path.exists('data.csv'):
    # CSVを読み込んで表示するだけ（データ取得処理がないので一瞬で開く）
    df = pd.read_csv('data.csv')
    df.set_index("銘柄コード", inplace=True)
    st.data_editor(df, use_container_width=True)
else:
    st.warning("現在、裏側で初回データを取得中です。数分後にリロードしてください。")
