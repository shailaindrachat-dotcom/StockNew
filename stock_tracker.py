import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─────────────────────────────────────────────
# Page Configuration
# ─────────────────────────────────────────────
st.set_page_config(page_title="Pro Stock Dashboard", layout="wide")

# ─────────────────────────────────────────────
# Header Row with Refresh Button
# ─────────────────────────────────────────────
header_col, refresh_col = st.columns([8, 1])
with header_col:
    st.title("📈 :rainbow[Pro Stock Dashboard]")
    st.write("Interactive Candlesticks, Moving Averages, Volume & RSI Indicators.")
with refresh_col:
    st.write("")  # vertical spacer
    if st.button("🔄 Refresh", help="Clear cache and reload all data"):
        st.cache_data.clear()
        st.rerun()

# ─────────────────────────────────────────────
# Stock Dictionary
# ─────────────────────────────────────────────
stocks = {
    # Original
    "Paras Defence & Space Tech": "PARAS.NS",
    "Data Patterns India": "DATAPATTNS.NS",
    "PTC Industries": "PTCIL.NS",
    "Servotech Power Systems": "SERVOTECH.NS",
    "Vedanta Ltd": "VEDL.NS",
    "Multi Commodity Exchange": "MCX.NS",
    "NMDC Ltd": "NMDC.NS",
    "IFCI Ltd": "IFCI.NS",
    "Pro Fin Capital": "511557.BO",
    "Bartronics India Ltd": "ASMS.NS",
    "Goldstar Power": "GOLDSTAR.NS",
    "Zee Media": "ZEEMEDIA.NS",
    "Cella Space Limited": "532701.BO",
    "KPIT Technologies": "KPITTECH.NS",
    "JBM Auto Ltd": "JBMA.NS",
    "SPML Infra Ltd": "SPMLINFRA.NS",
    "KNR Constructions": "KNRCON.NS",
    # Defense & Aviation
    "Hindustan Aeronautics (HAL)": "HAL.NS",
    "Bharat Electronics (BEL)": "BEL.NS",
    "Bharat Dynamics (BDL)": "BDL.NS",
    "Mazagon Dock Shipbuilders": "MAZDOCK.NS",
    "Cochin Shipyard (CSL)": "COCHINSHIP.NS",
    "Zen Technologies": "ZENTEC.NS",
    "Astra Microwave": "ASTRAMICRO.NS",
    "MTAR Technologies": "MTARTECH.NS",
    "Garden Reach Shipbuilders": "GRSE.NS",
    "Mishra Dhatu Nigam": "MIDHANI.NS",
    "Knowledge Marine & Eng": "KMEW.BO",
    # Banking & Finance
    "State Bank of India (SBI)": "SBIN.NS",
    "Bank of Baroda": "BANKBARODA.NS",
    "Canara Bank": "CANBK.NS",
    "UCO Bank": "UCOBANK.NS",
    "Union Bank of India": "UNIONBANK.NS",
    "Central Bank of India": "CENTRALBK.NS",
    "Bank of Maharashtra": "MAHABANK.NS",
    "Bank of India": "BANKINDIA.NS",
    "Punjab & Sind Bank": "PSB.NS",
    "Indian Overseas Bank": "IOB.NS",
    "Indian Bank": "INDIANB.NS",
    "Punjab National Bank": "PNB.NS",
    "General Insurance Corp": "GICRE.NS",
    "Life Insurance Corp (LIC)": "LICI.NS",
    "The New India Assurance": "NIACL.NS",
    "Power Finance Corp (PFC)": "PFC.NS",
    "REC Ltd": "RECLTD.NS",
    "Indian Railway Finance Corp": "IRFC.NS",
    "Housing & Urban Dev (HUDCO)": "HUDCO.NS",
    # Energy
    "Bharat Petroleum (BPCL)": "BPCL.NS",
    "Hindustan Petroleum (HPCL)": "HINDPETRO.NS",
    "Indian Oil Corp (IOC)": "IOC.NS",
    "Oil India Ltd": "OIL.NS",
    "ONGC": "ONGC.NS",
    "Mangalore Refinery (MRPL)": "MRPL.NS",
    "NTPC Ltd": "NTPC.NS",
    "Coal India Ltd": "COALINDIA.NS",
    "SJVN Ltd": "SJVN.NS",
    "NHPC Ltd": "NHPC.NS",
    "GAIL (India) Ltd": "GAIL.NS",
    "Gujarat Gas Ltd": "GUJGASLTD.NS",
    "Power Grid Corp": "POWERGRID.NS",
    # Metals & Heavy Engineering
    "MMTC Ltd": "MMTC.NS",
    "Steel Authority of India (SAIL)": "SAIL.NS",
    "National Aluminium (NALCO)": "NATIONALUM.NS",
    "Hindustan Copper Ltd": "HINDCOPPER.NS",
    "NLC India Ltd": "NLCINDIA.NS",
    "KIOCL Ltd": "KIOCL.NS",
    "Bharat Heavy Electricals (BHEL)": "BHEL.NS",
    "Engineers India Ltd": "ENGINERSIN.NS",
    "Larsen & Toubro (L&T)": "LT.NS",
    # Railways & Infrastructure
    "Ircon International Ltd": "IRCON.NS",
    "Container Corp of India": "CONCOR.NS",
    "NBCC (India) Ltd": "NBCC.NS",
    "IRCTC": "IRCTC.NS",
    "Rites Ltd": "RITES.NS",
    "Rail Vikas Nigam (RVNL)": "RVNL.NS",
    # Others
    "Rashtriya Chemicals & Fertilizers": "RCF.NS",
    "ITI Ltd": "ITI.NS",
}

# ─────────────────────────────────────────────
# Sidebar Controls
# ─────────────────────────────────────────────
st.sidebar.header("🔍 Stock Index")
options = ["Overview (All Stocks)"] + sorted(list(stocks.keys()))
selected_option = st.sidebar.selectbox("Choose a view:", options)

# Period selector — drives both fetch and chart tail window
period_map = {
    "1 Month": ("1mo", 22),
    "3 Months": ("3mo", 66),
    "6 Months": ("6mo", 132),
    "1 Year": ("1y", 252),
}
selected_period_label = st.sidebar.selectbox(
    "Chart Period", list(period_map.keys()), index=1
)
fetch_period, tail_days = period_map[selected_period_label]

# Indicator toggles
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Indicators")
show_sma10 = st.sidebar.checkbox("10-Day SMA", value=True)
show_sma20 = st.sidebar.checkbox("20-Day SMA", value=True)
show_volume = st.sidebar.checkbox("Volume Bars", value=True)

if selected_option == "Overview (All Stocks)":
    stocks_to_display = stocks
    st.info(
        "⚡ Loading overview of all stocks using parallel fetching. "
        "This may take 30–60 seconds on first load."
    )
else:
    stocks_to_display = {selected_option: stocks[selected_option]}

# ─────────────────────────────────────────────
# Data Fetching with All Fixes Applied
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_stock_data(ticker: str, period: str, tail: int):
    """
    Fetch OHLCV data, compute SMA + RSI, and return chart/table slices + news.

    Fixes applied:
      - Timezone stripped to avoid deprecation warnings
      - RSI guarded against division-by-zero (pure uptrend → RSI=100)
      - pct_change guarded against single-row DataFrames
      - yfinance news structure handled for both old and new API shapes
      - Descriptive warning returned on empty data instead of silent failure
    """
    try:
        stock = yf.Ticker(ticker)
        # FIX #10: strip timezone before any date operations
        hist = stock.history(period=period)
        if not hist.empty:
            hist.index = hist.index.tz_localize(None)
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), [], f"Fetch error: {e}"

    if hist.empty:
        return pd.DataFrame(), pd.DataFrame(), [], "No data returned — symbol may be delisted or incorrect."

    # ── Moving Averages ──────────────────────────────────────────────────
    hist["SMA_10"] = hist["Close"].rolling(window=10).mean()
    hist["SMA_20"] = hist["Close"].rolling(window=20).mean()

    # ── RSI (14-day) — FIX #2: guard division by zero ───────────────────
    delta = hist["Close"].diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean()
    loss_safe = loss.replace(0, np.nan)          # avoid ÷0
    rs = gain / loss_safe
    hist["RSI"] = 100 - (100 / (1 + rs))
    hist["RSI"] = hist["RSI"].fillna(100)        # pure uptrend → RSI = 100

    # ── Slice data ───────────────────────────────────────────────────────
    chart_data = hist.tail(tail).copy()
    chart_data.index = chart_data.index.strftime("%Y-%m-%d")

    table_data = hist[["Open", "High", "Low", "Close", "Volume", "RSI"]].tail(15).copy()
    table_data.index = table_data.index.strftime("%Y-%m-%d")
    table_data[["Open", "High", "Low", "Close", "RSI"]] = (
        table_data[["Open", "High", "Low", "Close", "RSI"]].round(2)
    )

    # ── News — FIX #1: handle both old and new yfinance news shapes ──────
    news = []
    try:
        raw_news = stock.news or []
        for item in raw_news[:3]:
            # yfinance ≥0.2.x wraps content under a 'content' key
            entry = item.get("content", item)
            news.append({
                "title":     entry.get("title", "No Title"),
                "link":      entry.get("canonicalUrl", {}).get("url", "")
                             or entry.get("link", "#"),
                "publisher": entry.get("provider", {}).get("displayName", "")
                             or entry.get("publisher", "Unknown"),
            })
    except Exception:
        news = []

    return chart_data, table_data, news, None   # None = no error


def fetch_parallel(tickers_dict: dict, period: str, tail: int) -> dict:
    """Fetch all tickers concurrently to avoid serial blocking in Overview mode."""
    results = {}

    def _fetch(name, ticker):
        return name, get_stock_data(ticker, period, tail)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(_fetch, name, ticker): name
            for name, ticker in tickers_dict.items()
        }
        for future in as_completed(futures):
            name, data = future.result()
            results[name] = data

    return results


# ─────────────────────────────────────────────
# Fetch Data
# ─────────────────────────────────────────────
if len(stocks_to_display) > 1:
    # FIX #4: parallel fetch for Overview mode
    with st.spinner("Fetching all stocks in parallel…"):
        all_data = fetch_parallel(stocks_to_display, fetch_period, tail_days)
else:
    name, ticker = next(iter(stocks_to_display.items()))
    all_data = {name: get_stock_data(ticker, fetch_period, tail_days)}

# ─────────────────────────────────────────────
# Render Helper
# ─────────────────────────────────────────────
# Fixed pixel heights ensure both cards in a row grow to the same size,
# preventing the left/right drift that happens when Streamlit columns
# accumulate content independently.
CHART_HEIGHT   = 400   # px — same for every card
TABLE_HEIGHT   = 310   # px — fits 15 rows without scrolling
OVERVIEW_MODE  = len(stocks_to_display) > 1


def build_chart(chart_df: pd.DataFrame) -> go.Figure:
    """Build the candlestick (+ optional SMA / volume) figure."""
    row_heights = [0.65, 0.35] if show_volume else [1.0]
    rows = 2 if show_volume else 1

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        row_heights=row_heights,
        vertical_spacing=0.03,
        subplot_titles=["Price", "Volume"] if show_volume else ["Price"],
    )

    fig.add_trace(
        go.Candlestick(
            x=chart_df.index,
            open=chart_df["Open"], high=chart_df["High"],
            low=chart_df["Low"],  close=chart_df["Close"],
            name="Price",
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ),
        row=1, col=1,
    )

    if show_sma10 and "SMA_10" in chart_df.columns:
        fig.add_trace(
            go.Scatter(x=chart_df.index, y=chart_df["SMA_10"],
                       mode="lines", name="10-Day SMA",
                       line=dict(color="#2196F3", width=1.5)),
            row=1, col=1,
        )

    if show_sma20 and "SMA_20" in chart_df.columns:
        fig.add_trace(
            go.Scatter(x=chart_df.index, y=chart_df["SMA_20"],
                       mode="lines", name="20-Day SMA",
                       line=dict(color="#FF9800", width=1.5)),
            row=1, col=1,
        )

    if show_volume:
        vol_colors = [
            "#26a69a" if c >= o else "#ef5350"
            for c, o in zip(chart_df["Close"], chart_df["Open"])
        ]
        fig.add_trace(
            go.Bar(x=chart_df.index, y=chart_df["Volume"],
                   name="Volume", marker_color=vol_colors, opacity=0.6),
            row=2, col=1,
        )

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=CHART_HEIGHT,                          # ← fixed height
        margin=dict(l=0, r=0, t=25, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")
    return fig


def render_card(container, company_name: str, ticker: str) -> None:
    """Render one stock card into the given Streamlit container."""
    chart_df, table_df, news, error_msg = all_data[company_name]

    with container:
        st.subheader(f":blue[{company_name}] ({ticker})")

        if error_msg or table_df.empty:
            # Pad with empty space so the error card matches the height of a
            # successful card and doesn't throw off row alignment.
            st.warning(
                f"⚠️ **{company_name}** — "
                + (error_msg or "No data available. Symbol may be delisted or incorrect.")
            )
            st.empty()   # placeholder keeps vertical rhythm
            st.divider()
            return

        latest_close = table_df["Close"].iloc[-1]

        if len(table_df) >= 2:
            previous_close = table_df["Close"].iloc[-2]
            pct_change = ((latest_close - previous_close) / previous_close) * 100
        else:
            pct_change = 0.0

        latest_rsi = table_df["RSI"].iloc[-1]

        # ── Metrics ─────────────────────────────────────────────────────
        m1, m2, m3 = st.columns(3)
        m1.metric("Latest Close", f"₹{latest_close:.2f}", f"{pct_change:+.2f}%")

        if latest_rsi > 70:
            rsi_label = "Overbought 🔴"
        elif latest_rsi < 30:
            rsi_label = "Oversold 🟢"
        else:
            rsi_label = "Neutral 🟡"
        m2.metric("RSI (14-Day)", f"{latest_rsi:.2f}", delta=rsi_label, delta_color="off")

        latest_vol = int(table_df["Volume"].iloc[-1])
        vol_display = (
            f"{latest_vol / 1_000_000:.2f}M" if latest_vol >= 1_000_000 else f"{latest_vol:,}"
        )
        m3.metric("Volume (Latest)", vol_display)

        # ── Chart ────────────────────────────────────────────────────────
        st.plotly_chart(build_chart(chart_df), use_container_width=True)

        # ── Table — fixed height so both columns stay in sync ────────────
        st.write("**15-Day Historical Data**")
        styled_df = (
            table_df.style
            .background_gradient(subset=["Close"], cmap="Blues")
            .background_gradient(subset=["Volume"], cmap="Purples")
            .format({
                "Open":   "₹{:.2f}", "High":  "₹{:.2f}",
                "Low":    "₹{:.2f}", "Close": "₹{:.2f}",
                "Volume": "{:,.0f}", "RSI":   "{:.2f}",
            })
        )
        st.dataframe(styled_df, use_container_width=True, height=TABLE_HEIGHT)

        # ── News ─────────────────────────────────────────────────────────
        with st.expander("📰 View Latest News"):
            if news:
                for article in news:
                    title     = article.get("title", "No Title Available")
                    link      = article.get("link", "#")
                    publisher = article.get("publisher", "Unknown")
                    st.markdown(f"- [{title}]({link}) *(Source: {publisher})*")
            else:
                st.write("No recent news found for this ticker.")

        st.divider()


# ─────────────────────────────────────────────
# Render Cards
# ─────────────────────────────────────────────
stock_items = list(stocks_to_display.items())

if not OVERVIEW_MODE:
    # Single-stock view — one full-width card
    company_name, ticker = stock_items[0]
    render_card(st.container(), company_name, ticker)
else:
    # Overview mode — render one ROW at a time so each pair of columns
    # starts fresh at the same vertical position.  This is the key fix:
    # a single st.columns([1,1]) shared across all stocks would let the
    # two sides drift apart; creating a new pair per row keeps them locked.
    for i in range(0, len(stock_items), 2):
        left_name,  left_ticker  = stock_items[i]
        has_right = i + 1 < len(stock_items)

        if has_right:
            right_name, right_ticker = stock_items[i + 1]
            col_left, col_right = st.columns(2)
            render_card(col_left,  left_name,  left_ticker)
            render_card(col_right, right_name, right_ticker)
        else:
            # Odd stock out — render in left half, leave right blank
            col_left, _ = st.columns(2)
            render_card(col_left, left_name, left_ticker)

# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────
st.caption(
    f"Data last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
    f"Period: {selected_period_label} | Data provided by Yahoo Finance"
)
