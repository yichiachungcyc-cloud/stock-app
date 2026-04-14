import streamlit as st
import pandas as pd
from datetime import date
import yfinance as yf

def highlight_type(val):
    if val == "BUY":
        return "color: green; font-weight: bold;"
    elif val == "SELL":
        return "color: red; font-weight: bold;"
    return ""

st.set_page_config(page_title="股票投資系統", layout="wide")

FILE = "transactions.csv"

import os
import pandas as pd

FILE = "transactions.csv"

if not os.path.exists(FILE):
    df = pd.DataFrame(columns=[
        "date", "stock_id", "stock_name",
        "type", "price", "quantity", "note"
    ])
    df.to_csv(FILE, index=False)

import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)

client = gspread.authorize(creds)

sheet = client.open_by_key("11CNAKad0xqBCMqdgQeco2J-OY-tUkbmKdJlZ63iaPEk").sheet1

data = sheet.get_all_records()
data = sheet.get_all_values()

if len(data) == 0:
    st.error("Google Sheet 是空的")
    st.stop()

if len(data) == 1:
    st.warning("只有欄位沒有資料")
    df = pd.DataFrame(columns=data[0])
else:
    df = pd.DataFrame(data[1:], columns=data[0])


df.columns = [str(c).strip().lower() for c in df.columns]  # ⭐ 加這行(去空白)

required_cols = ["date","stock_id","stock_name","type","price","quantity","note"]

for col in required_cols:
    if col not in df.columns:
        df[col] = ""

# ===== 數據格式統一 =====
df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0).round(3)
df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0).astype(float).astype(int)
df["amount"] = (df["price"] * df["quantity"]).round(3)

if "note" not in df.columns:
    df["note"] = ""

df["note"] = df["note"].fillna("").astype(str)

# ===== 確保欄位 =====

if "note" not in df.columns:
    df["note"] = ""

df["date"] = pd.to_datetime(df["date"])
df["month"] = df["date"].dt.to_period("M").astype(str)

# ===== 分頁 =====
tab_main, tab_analysis = st.tabs(["📊 投資總覽", "📈 投資分析"])

# =========================
# 📊 總覽
# =========================
with tab_main:
    st.title("📊 股票投資系統")

    # ===== KPI =====
    total_invest = df[df["type"] == "BUY"]["amount"].sum()
    total_sell = df[df["type"] == "SELL"]["amount"].sum()

    col1, col2 = st.columns(2)

    col1.metric("💰 總投入", f"{total_invest:,.0f}")
    col2.metric("💸 總賣出", f"{total_sell:,.0f}")

    st.divider()

    # ===== 交易明細 =====
    st.subheader("🧾 交易明細")

    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False

    if st.button("✏️ 編輯模式"):
        st.session_state.edit_mode = not st.session_state.edit_mode

    selected_month = st.selectbox(
        "選擇月份",
        options=["全部"] + sorted(df["month"].unique().tolist())
    )

    if selected_month != "全部":
        filtered_df = df[df["month"] == selected_month].copy()
    else:
        filtered_df = df.copy()

    if not st.session_state.edit_mode:
        styled_df = filtered_df.style.map(
            highlight_type,
            subset=["type"]
        )
        st.dataframe(styled_df, use_container_width=True)
    else:
        edited_df = st.data_editor(
            filtered_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "note": st.column_config.TextColumn("備註", width="large")
            }
        )

        if st.button("💾 儲存修改"):
            sheet.clear()
            sheet.update(
                [edited_df.columns.tolist()] + edited_df.fillna("").values.tolist()
            )
            st.success("已儲存")

# =========================
# 📈 投資分析
# =========================
with tab_analysis:
    st.title("📈 投資分析")

    df["amount"] = (df["price"] * df["quantity"]).round(3)

    grouped = df.groupby("stock_id")

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

    # ⭐ profit（只算一次！）
    result_df["profit"] = (
        (result_df["current_price"] - result_df["avg_cost"]) * result_df["shares"]
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