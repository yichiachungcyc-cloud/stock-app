import streamlit as st

users = st.secrets["auth"]

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 登入系統")

    username = st.text_input("帳號")
    password = st.text_input("密碼", type="password")

    if st.button("登入"):
       if username in users and users[username] == password:
            st.session_state.login = True
            st.session_state.user = username
            st.rerun()
       else:
            st.error("帳密錯誤")

    st.stop()

# ③ 登入成功後才跑 App
st.sidebar.success(f"登入者：{st.session_state.user}")

import pandas as pd
import yfinance as yf
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =========================
# UI設定
# =========================
st.set_page_config(page_title="股票投資系統", layout="wide")

def highlight_type(val):
    if val == "BUY":
        return "color: green; font-weight: bold;"
    elif val == "SELL":
        return "color: red; font-weight: bold;"
    return ""

# =========================
# Google Sheet 連線
# =========================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"],
    scope
)

client = gspread.authorize(creds)

sheet = client.open_by_key(
    "11CNAKad0xqBCMqdgQeco2J-OY-tUkbmKdJlZ63iaPEk"
).sheet1

# =========================
# 讀取資料（穩定版）
# =========================
data = sheet.get_all_values()

if not data or len(data) < 2:
    st.warning("Google Sheet 沒有資料")
    st.stop()

df = pd.DataFrame(data[1:], columns=data[0])

# 欄位整理
df.columns = [str(c).strip().lower() for c in df.columns]

# =========================
# 欄位補齊（防炸）
# =========================
required_cols = ["date","stock_id","stock_name","type","price","quantity","note"]

for col in required_cols:
    if col not in df.columns:
        df[col] = ""

# =========================
# 型別轉換（重點）
# =========================
df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0).round(3)

df["quantity"] = (
    pd.to_numeric(df["quantity"], errors="coerce")
    .fillna(0)
    .astype(int)
)

df["amount"] = (df["price"] * df["quantity"]).round(3)

df["note"] = df["note"].fillna("").astype(str)

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["month"] = df["date"].dt.to_period("M").astype(str)

# =========================
# Tabs
# =========================
tab_main, tab_analysis = st.tabs(["📊 投資總覽", "📈 投資分析"])

# =========================
# 📊 總覽
# =========================
with tab_main:
    st.title("📊 股票投資系統")

    total_invest = df[df["type"] == "BUY"]["amount"].sum()
    total_sell = df[df["type"] == "SELL"]["amount"].sum()

    col1, col2 = st.columns(2)
    col1.metric("💰 總投入", f"{total_invest:,.0f}")
    col2.metric("💸 總賣出", f"{total_sell:,.0f}")

    st.divider()

    

    st.subheader("🧾 交易明細")

    # =========================
    # 模式切換
    # =========================
    mode = st.radio(
        "模式",
        ["👀 檢視模式","💾 編輯並存檔"],
        horizontal=True
    )

    # =========================
    # 篩選
    # =========================
    selected_month = st.selectbox(
        "選擇月份",
        options=["全部"] + sorted(df["month"].dropna().unique().tolist())
    )

    if selected_month != "全部":
        filtered_df = df[df["month"] == selected_month].copy()
    else:
        filtered_df = df.copy()

    # =========================
    # 👀 檢視模式
    # =========================
    if mode == "👀 檢視模式":

        st.dataframe(
            filtered_df,
            use_container_width=True
        )

   

    # =========================
    # 💾 編輯並存檔
    # =========================
    elif mode == "💾 編輯並存檔":

        edited_df = st.data_editor(  
            filtered_df,
            num_rows="dynamic",
            use_container_width=True
        )

        if st.button("💾 確認寫回 Google Sheet"):

            safe_df = edited_df.copy().fillna("")

            values = [safe_df.columns.tolist()] + safe_df.astype(str).values.tolist()

            # ✅ 安全寫回（不 clear）
            sheet.resize(rows=len(values))
            sheet.update(values)

            st.success("已安全存回 Google Sheet")
            st.rerun()

# =========================
# 📈 投資分析
# =========================
with tab_analysis:
    st.title("📈 投資分析")

    result = []

for stock_id, group in df.sort_values("date").groupby("stock_id"):

    shares = 0
    cost = 0

    for _, row in group.iterrows():

        if row["type"] == "BUY":
            shares += row["quantity"]
            cost += row["price"] * row["quantity"]

        elif row["type"] == "SELL" and shares > 0:
            avg_cost = cost / shares if shares != 0 else 0
            shares -= row["quantity"]
            cost -= avg_cost * row["quantity"]

        # ⭐ 清倉歸零
        if shares == 0:
            cost = 0

    avg_cost = cost / shares if shares != 0 else 0

    result.append({
        "stock_id": stock_id,
        "stock_name": group["stock_name"].iloc[0],
        "shares": shares,
        "avg_cost": round(avg_cost, 3)
    })

    result = []

    for stock_id, group in grouped:
        buy_df = group[group["type"] == "BUY"]
        sell_df = group[group["type"] == "SELL"]

        shares = buy_df["quantity"].sum() - sell_df["quantity"].sum()
        cost = buy_df["amount"].sum()
        buy_shares = buy_df["quantity"].sum()

        avg_cost = cost / buy_shares if buy_shares != 0 else 0

        stock_name = group["stock_name"].iloc[0]

        result.append({
            "stock_id": stock_id,
            "stock_name": stock_name,
            "shares": shares,
            "avg_cost": round(avg_cost, 3)
        })

    result_df = pd.DataFrame(result)

    if result_df.empty:
        st.warning("目前沒有任何交易資料")
        st.stop()

    # 即時價格
    prices = []
    for sid in result_df["stock_id"]:
        try:
            price = yf.Ticker(f"{sid}.TW").history(period="1d")["Close"].iloc[-1]
        except:
            price = 0
        prices.append(price)

    result_df["current_price"] = prices

    # profit（只算一次）
    result_df["profit"] = (
        (result_df["current_price"] - result_df["avg_cost"])
        * result_df["shares"]
    ).round(3)

    total_profit = result_df["profit"].sum()
    st.metric("💰 總損益", f"{total_profit:,.0f}")

    st.dataframe(
        result_df,
        column_config={
            "avg_cost": st.column_config.NumberColumn(format="%.3f"),
            "current_price": st.column_config.NumberColumn(format="%.3f"),
            "profit": st.column_config.NumberColumn(format="%.3f"),
            "shares": st.column_config.NumberColumn(format="%.0f"),
        },
        use_container_width=True
    )

    st.subheader("📈 損益圖")
    st.bar_chart(result_df.set_index("stock_id")["profit"])