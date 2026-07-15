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
    
    # 2. インデックス設定
    df.set_index(["銘柄CD", "銘柄名"], inplace=True)
    
    # 3. カラム設定（インデックスに対する設定と、データ列に対する設定を分ける）
    column_config = {
        # インデックス列は名前で直接指定せず、インデックスの階層（Level 0, 1）として扱うか、
        # あるいは設定をスキップするのが最も安定します。
        "直近株価": st.column_config.NumberColumn(format="￥%,d"),
        "目標株価": st.column_config.NumberColumn(format="￥%,d"),
        "PER(予)": st.column_config.NumberColumn(format="%.2f"),
        "PBR(実)": st.column_config.NumberColumn(format="%.2f"),
    }
    
    for col in million_cols:
        key = f"{col}(百万)"
        column_config[key] = st.column_config.NumberColumn(format="%,d")

    # 4. 画面表示
    st.data_editor(
        df,
        column_config=column_config,
        use_container_width=True,
        height=640,
        hide_index=False  # インデックスを表示する設定に変更
    )
else:
    st.warning("現在、裏側で初回データを取得中です。数分後にリロードしてください。")
