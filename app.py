import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")
st.title("🌳改造中")

if os.path.exists('data.csv'):
    df = pd.read_csv('data.csv')
    
    # 1. 数値フォーマットの整形
    def to_millions(x):
        return x / 1000000 if pd.notnull(x) else None

    million_cols = ['売上高', '当期純利益', '総資産', '自己資本']
    for col in million_cols:
        df[col] = df[col].apply(to_millions).round(0)
    
    # 列名の変更
    df = df.rename(columns={col: f"{col}(百万)" for col in million_cols})
    
    # --- 修正点: インデックスにせず、列の順序だけ整える ---
    # 銘柄CDと銘柄名を左端に寄せる
    cols = ['銘柄CD', '銘柄名'] + [c for c in df.columns if c not in ['銘柄CD', '銘柄名']]
    df = df[cols]
    
    # 2. カラム設定（すべての列を設定）
    column_config = {
        "銘柄CD": st.column_config.TextColumn("銘柄CD", disabled=True),
        "銘柄名": st.column_config.TextColumn("銘柄名", disabled=True),
        "直近株価": st.column_config.NumberColumn(format="￥%,d"),
        "目標株価": st.column_config.NumberColumn(format="￥%,d"),
        "PER(予)": st.column_config.NumberColumn(format="%.2f"),
        "PBR(実)": st.column_config.NumberColumn(format="%.2f"),
    }
    
    for col in million_cols:
        key = f"{col}(百万)"
        column_config[key] = st.column_config.NumberColumn(format="%,d")

    # 3. 画面表示
    st.data_editor(
        df,
        column_config=column_config,
        use_container_width=True,
        height=640,
        hide_index=True  # インデックスを表示しない
    )
else:
    st.warning("現在、裏側で初回データを取得中です。数分後にリロードしてください。")
