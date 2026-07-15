import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")
st.title("🌳改造中")

# GitHub Actionが作成したCSVファイルが存在するかチェック
if os.path.exists('data.csv'):
    df = pd.read_csv('data.csv')
    
    # --- 数値フォーマットの整形処理 ---
    def to_millions(x):
        return x / 1000000 if pd.notnull(x) else None

    # 各列のフォーマットを適用
    df['PER(予)'] = df['PER(予)'].round(2)
    df['PBR(実)'] = df['PBR(実)'].round(2)
    
    # 100万単位に変換
    million_cols = ['売上高', '当期純利益', '総資産', '自己資本']
    for col in million_cols:
        df[col] = df[col].apply(to_millions).round(0)
    
    # 表示用の列名を変更
    df = df.rename(columns={col: f"{col}(百万)" for col in million_cols})
    
    # --- インデックス設定 ---
    # 銘柄CD と 銘柄名 を両方インデックスに設定（＝横スクロール時に左側に固定）
    df.set_index(["銘柄CD", "銘柄名"], inplace=True)
    
    # --- 画面表示 ---
    st.data_editor(
        df,
        column_config={
            "直近株価": st.column_config.NumberColumn(format="￥%,d"),
            "目標株価": st.column_config.NumberColumn(format="￥%,d"),
            "PER(予)": st.column_config.NumberColumn(format="%.2f"),
            "PBR(実)": st.column_config.NumberColumn(format="%.2f"),
            **{f"{col}(百万)": st.column_config.NumberColumn(format="%,d") for col in million_cols}
        },
        # インデックス列は自動的に編集不可（固定）となります
        use_container_width=True,
        height=640
    )
else:
    st.warning("現在、裏側で初回データを取得中です。数分後にリロードしてください。")
