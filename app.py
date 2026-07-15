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
    
    # 2. インデックス設定（これにより銘柄CDと銘柄名が固定される）
    df.set_index(["銘柄CD", "銘柄名"], inplace=True)
    
    # 3. カラム設定の準備（エラー防止のため、存在する列のみを辞書にする）
    # インデックス化した列以外で、かつ百万単位の列だけを抽出して設定
    target_million_cols = [f"{col}(百万)" for col in million_cols]
    
    column_config_dict = {
        "直近株価": st.column_config.NumberColumn(format="￥%,d"),
        "目標株価": st.column_config.NumberColumn(format="￥%,d"),
        "PER(予)": st.column_config.NumberColumn(format="%.2f"),
        "PBR(実)": st.column_config.NumberColumn(format="%.2f"),
    }
    # 百万単位のカラムを追加
    for col_name in target_million_cols:
        column_config_dict[col_name] = st.column_config.NumberColumn(format="%,d")

    # 4. 画面表示
    st.data_editor(
        df,
        column_config=column_config_dict,
        use_container_width=True,
        height=640
    )
else:
    st.warning("現在、裏側で初回データを取得中です。数分後にリロードしてください。")
