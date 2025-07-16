import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta
import yfinance as yf

st.set_page_config(page_title="Cumulative Return with FX", layout="wide")
st.title("🌍 Cumulative Return Chart (with Dividends & Currency Conversion)")

# ─── Date defaults ─────────────────────────────────────────────────────────────
today = datetime.date.today()
three_years_ago = today - datetime.timedelta(days=3*365)
yesterday = today - datetime.timedelta(days=1)

# ─── Input table ────────────────────────────────────────────────────────────────
num_rows = 5
tickers, currencies, start_dates, end_dates = [], [], [], []

st.subheader("Enter up to 5 tickers")
for i in range(num_rows):
    c1, c2, c3, c4 = st.columns([2,1,2,2])
    with c1:
        t = st.text_input(f"Ticker {i+1}", key=f"tic{i}")
    with c2:
        cur = st.text_input(f"Currency {i+1}", value="EUR", key=f"cur{i}")
    with c3:
        s = st.date_input(f"Start {i+1}", value=three_years_ago, key=f"st{i}")
    with c4:
        e = st.date_input(f"End {i+1}", value=yesterday, key=f"en{i}")
    if t.strip():
        tickers.append(t.strip().upper())
        currencies.append(cur.strip().upper())
        start_dates.append(s)
        end_dates.append(e)

if not tickers:
    st.info("Please enter at least one ticker.")
    st.stop()

st.divider()
st.subheader("📊 Cumulative Return Chart")

returns = pd.DataFrame()

for tic, usr_cur, st_dt, end_dt in zip(tickers, currencies, start_dates, end_dates):
    try:
        tk = yf.Ticker(tic)
        info = tk.info
        native_cur = info.get("currency", "USD")

        # — extend end date by 1 so it's inclusive
        hist = tk.history(start=st_dt, end=end_dt + timedelta(days=1), auto_adjust=True)
        
        # Debug: show what date range we got back
        st.write(f"### {tic} data from {st_dt} to {end_dt}")
        st.write(hist[["Close"]].head(), hist[["Close"]].tail())

        if hist.empty:
            st.warning(f"No data for {tic} in that range.")
            continue

        price = hist["Close"]

        # — currency conversion if needed
        if native_cur != usr_cur:
            fx_tk = yf.Ticker(f"{native_cur}{usr_cur}=X")
            fx_hist = fx_tk.history(
                start=st_dt, end=end_dt + timedelta(days=1)
            )
            if fx_hist.empty:
                st.warning(f"No FX data for {native_cur}->{usr_cur}")
                continue
            fx_rate = fx_hist["Close"].reindex(price.index).ffill()
            price = price * fx_rate

        # — rebase to 100
        returns[tic] = price.div(price.iloc[0]).mul(100)

    except Exception as e:
        st.error(f"Error processing {tic}: {e}")
