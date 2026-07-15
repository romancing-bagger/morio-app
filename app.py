import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")
st.title("🌳改造中")

# GitHub Actionが作成したCSVファイルが存在するかチェック
if os.path.exists('data.csv'):
    # CSVを読み込んで表示
    df = pd.read_csv('data.csv')
    
    # --- 数値フォーマットの整形処理 ---
    # 100万単位に変換する関数
    def to_millions(x):
        return x / 1000000 if pd.notnull(x) else None

    # 各列のフォーマットを適用
    df['PER(予)'] = df['PER(予)'].round(2)
    df['PBR(実)'] = df['PBR(実)'].round(2)
    
    # 100万単位に変換（対象カラムを指定）
    million_cols = ['売上高', '当期純利益', '総資産', '自己資本']
    for col in million_cols:
        df[col] = df[col].apply(to_millions).round(0)
    
    # 表示用の列名を変更
    df = df.rename(columns={col: f"{col}(百万)" for col in million_cols})
    
    # --- 画面表示 ---
    # インデックスを銘柄CDに設定
    df.set_index("銘柄CD",  inplace=True)
    
    # column_configの設定
    config = {
        "直近株価": st.column_config.NumberColumn(format="￥%,d"),
        "目標株価": st.column_config.NumberColumn(format="￥%,d"),
        "PER(予)": st.column_config.NumberColumn(format="%.2f"),
        "PBR(実)": st.column_config.NumberColumn(format="%.2f"),
    }
    
    # 百万単位のカラム設定を追加
    for col in million_cols:
        config[f"{col}(百万)"] = st.column_config.NumberColumn(format="%,d")
    
    # 画面表示
    st.data_editor(
        df,
        column_config=config,
        use_container_width=True,
        height=480
    )
else:
    st.warning("現在、裏側で初回データを取得中です。数分後にリロードしてください。")
