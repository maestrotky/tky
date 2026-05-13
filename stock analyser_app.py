# app.py
# Stock Market Visualizer
# Requirements:
# pip install streamlit yfinance pandas plotly ta openpyxl kaleido

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from ta.trend import SMAIndicator
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
from plotly.subplots import make_subplots
import json
import io
from datetime import datetime

st.set_page_config(
    page_title="Stock Market Visualizer",
    layout="wide"
)

# -----------------------------
# SIDEBAR CONFIG
# -----------------------------
st.sidebar.title("Stock Market Visualizer")

ticker = st.sidebar.text_input("Enter Stock Symbol", "AAPL")

period = st.sidebar.selectbox(
    "Select Timeframe",
    ["1mo", "3mo", "6mo", "1y", "2y", "5y"]
)

interval = st.sidebar.selectbox(
    "Interval",
    ["1d", "1h", "30m", "15m"]
)

show_ma = st.sidebar.checkbox("Show Moving Average", True)
ma_period = st.sidebar.slider("MA Period", 5, 100, 20)

show_rsi = st.sidebar.checkbox("Show RSI", True)
rsi_period = st.sidebar.slider("RSI Period", 5, 30, 14)

show_bb = st.sidebar.checkbox("Show Bollinger Bands", True)
bb_period = st.sidebar.slider("BB Period", 5, 50, 20)

chart_color = st.sidebar.color_picker("Chart Color", "#00FFAA")

# -----------------------------
# FETCH DATA
# -----------------------------
@st.cache_data
def load_data(symbol, period, interval):
    stock = yf.Ticker(symbol)
    df = stock.history(period=period, interval=interval)
    return df

df = load_data(ticker, period, interval)

if df.empty:
    st.error("No data found.")
    st.stop()

# -----------------------------
# INDICATORS
# -----------------------------
df["SMA"] = SMAIndicator(df["Close"], window=ma_period).sma_indicator()

bb = BollingerBands(df["Close"], window=bb_period)
df["BB_High"] = bb.bollinger_hband()
df["BB_Low"] = bb.bollinger_lband()

df["RSI"] = RSIIndicator(df["Close"], window=rsi_period).rsi()

# -----------------------------
# HEADER
# -----------------------------
st.title("📈 Stock Market Visualizer")
st.subheader(f"Analyzing: {ticker.upper()}")

# -----------------------------
# CANDLESTICK CHART
# -----------------------------
fig = make_subplots(
    rows=2,
    cols=1,
    shared_xaxes=True,
    row_heights=[0.7, 0.3],
    vertical_spacing=0.05
)

fig.add_trace(
    go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Candlestick"
    ),
    row=1,
    col=1
)

# Moving Average
if show_ma:
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["SMA"],
            mode="lines",
            line=dict(color=chart_color),
            name=f"SMA {ma_period}"
        ),
        row=1,
        col=1
    )

# Bollinger Bands
if show_bb:
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["BB_High"],
            mode="lines",
            line=dict(color="orange"),
            name="BB High"
        ),
        row=1,
        col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["BB_Low"],
            mode="lines",
            line=dict(color="orange"),
            name="BB Low"
        ),
        row=1,
        col=1
    )

# RSI
if show_rsi:
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["RSI"],
            mode="lines",
            line=dict(color="purple"),
            name="RSI"
        ),
        row=2,
        col=1
    )

fig.update_layout(
    height=800,
    template="plotly_dark",
    xaxis_rangeslider_visible=False
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# STOCK INFO
# -----------------------------
st.header("📊 Financial Ratios")

stock = yf.Ticker(ticker)
info = stock.info

ratios = {
    "Market Cap": info.get("marketCap"),
    "P/E Ratio": info.get("trailingPE"),
    "Dividend Yield": info.get("dividendYield"),
    "Beta": info.get("beta"),
    "EPS": info.get("trailingEps"),
}

ratio_df = pd.DataFrame(
    ratios.items(),
    columns=["Metric", "Value"]
)

st.dataframe(ratio_df, use_container_width=True)

# -----------------------------
# PORTFOLIO TRACKING
# -----------------------------
st.header("💼 Portfolio Tracking")

uploaded_file = st.file_uploader(
    "Upload Portfolio CSV or Excel",
    type=["csv", "xlsx"]
)

if uploaded_file:

    if uploaded_file.name.endswith(".csv"):
        portfolio = pd.read_csv(uploaded_file)
    else:
        portfolio = pd.read_excel(uploaded_file)

    st.write("Portfolio Preview")
    st.dataframe(portfolio)

    if "Ticker" in portfolio.columns:
        prices = []

        for tk in portfolio["Ticker"]:
            try:
                price = yf.Ticker(tk).history(period="1d")["Close"].iloc[-1]
                prices.append(price)
            except:
                prices.append(None)

        portfolio["Current Price"] = prices

        st.write("Updated Portfolio")
        st.dataframe(portfolio)

# -----------------------------
# CORRELATION ANALYSIS
# -----------------------------
st.header("🔗 Stock Correlation Analysis")

tickers_input = st.text_input(
    "Enter Multiple Tickers (comma separated)",
    "AAPL,MSFT,GOOG,TSLA"
)

tickers_list = [x.strip() for x in tickers_input.split(",")]

if st.button("Generate Correlation"):

    corr_data = pd.DataFrame()

    for tk in tickers_list:
        temp = yf.Ticker(tk).history(period="1y")["Close"]
        corr_data[tk] = temp

    corr = corr_data.corr()

    heatmap = px.imshow(
        corr,
        text_auto=True,
        aspect="auto",
        title="Stock Correlation Matrix"
    )

    st.plotly_chart(heatmap, use_container_width=True)

# -----------------------------
# EXPORT CHARTS
# -----------------------------
st.header("📥 Export Chart")

html_bytes = fig.to_html().encode()

st.download_button(
    label="Download Chart as HTML",
    data=html_bytes,
    file_name=f"{ticker}_chart.html",
    mime="text/html"
)

png_bytes = fig.to_image(format="png")

st.download_button(
    label="Download Chart as PNG",
    data=png_bytes,
    file_name=f"{ticker}_chart.png",
    mime="image/png"
)

# -----------------------------
# SAVE USER CONFIG
# -----------------------------
st.header("⚙️ Save Configuration")

config = {
    "ticker": ticker,
    "period": period,
    "interval": interval,
    "show_ma": show_ma,
    "ma_period": ma_period,
    "show_rsi": show_rsi,
    "rsi_period": rsi_period,
    "show_bb": show_bb,
    "bb_period": bb_period,
    "chart_color": chart_color
}

config_json = json.dumps(config, indent=4)

st.download_button(
    label="Save Configuration",
    data=config_json,
    file_name="config.json",
    mime="application/json"
)

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("---")
st.caption("Built with Streamlit, Plotly, and yFinance")
