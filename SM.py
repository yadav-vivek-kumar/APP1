import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import requests
import random

# Core App Layout Config
st.set_page_config(
    page_title="Institutional Market Terminal",
    page_icon="⚡",
    layout="wide"
)

# Dark Premium UI Card Layout Injector
st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: #111827;
        border: 1px solid #1f2937;
        padding: 18px;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    div[data-testid="stSidebar"] { background-color: #0b0f19; }
    h1, h2, h3 { font-family: 'Inter', sans-serif; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Multi-Asset Exchange Dashboard")
st.markdown("Select or input international assets to dynamically render price movements.")

# Browser Emulation Identity Rotator
AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
]

@st.cache_data(ttl=180)  # Caching preserves API bandwidth limits on cloud clusters
def download_market_history(tickers, period):
    # Select intraday intervals for micro-horizons, default to daily for macro views
    interval = "5m" if period in ["1d", "5d"] else "1d"
    
    session = requests.Session()
    session.headers.update({'User-Agent': random.choice(AGENTS)})
    
    df_accumulator = pd.DataFrame()
    
    for symbol in tickers:
        try:
            tracker = yf.Ticker(symbol, session=session)
            # Fetch data using history to bypass metadata parsing blocks
            historical_records = tracker.history(period=period, interval=interval)
            if not historical_records.empty:
                df_accumulator[symbol] = historical_records['Close']
        except Exception:
            pass
            
    return df_accumulator

# --- SIDEBAR CONTROL PANEL ---
st.sidebar.header("🎯 Watchlist Management")

ticker_preset_vault = {
    "Apple Inc. (US)": "AAPL",
    "Microsoft Corp. (US)": "MSFT",
    "NVIDIA Corporation (US)": "NVDA",
    "Tesla Inc. (US)": "TSLA",
    "Reliance Industries (India)": "RELIANCE.NS",
    "Tata Consultancy Services (India)": "TCS.NS",
    "Infosys Limited (India)": "INFY.NS"
}

chosen_presets = st.sidebar.multiselect(
    "Choose Stocks to Monitor:",
    options=list(ticker_preset_vault.keys()),
    default=["Apple Inc. (US)", "NVIDIA Corporation (US)"]
)

# Convert friendly names to actual tickers
active_tickers = [ticker_preset_vault[name] for name in chosen_presets]

# Manual Override Text Field
custom_inputs = st.sidebar.text_input("➕ Enter Custom Tickers (Comma separated, e.g., AMD, AMZN)")
if custom_inputs:
    for custom_item in custom_inputs.split(","):
        clean_symbol = custom_item.strip().upper()
        if clean_symbol and clean_symbol not in active_tickers:
            active_tickers.append(clean_symbol)

st.sidebar.markdown("---")
selected_horizon = st.sidebar.radio(
    "📅 Timeframe Horizon",
    options=["1D", "5D", "1Mo", "6Mo", "1Y", "5Y"],
    index=4
).lower()

# --- MAIN RENDER LOGIC ---
if not active_tickers:
    st.info("💡 Please choose or type ticker symbols in the left sidebar configuration panel.")
else:
    with st.spinner("Establishing safe handshake tunnel with data indexers..."):
        price_dataframe = download_market_history(active_tickers, selected_horizon)
        
    if price_dataframe.empty:
        st.error("❌ Data retrieval failed. The server IP is temporarily throttled, or the ticker symbols are invalid.")
        st.info("💡 Try appending exchange suffixes if necessary (e.g., use `.NS` for National Stock Exchange India assets like `RELIANCE.NS`).")
    else:
        # Generate Row of Metric Widgets Dynamically
        st.subheader("📊 Real-Time Pricing Summary")
        metric_cols = st.columns(len(active_tickers))
        
        for position, ticker in enumerate(active_tickers):
            if ticker in price_dataframe.columns:
                clean_series = price_dataframe[ticker].dropna()
                if not clean_series.empty:
                    current_valuation = clean_series.iloc[-1]
                    starting_valuation = clean_series.iloc[0]
                    
                    net_deviation = current_valuation - starting_valuation
                    percentage_deviation = (net_deviation / starting_valuation) * 100
                    
                    with metric_cols[position]:
                        st.metric(
                            label=f"📈 {ticker}",
                            value=f"{current_valuation:,.2f}",
                            delta=f"{net_deviation:+,.2f} ({percentage_deviation:+.2f}%)"
                        )

        # Plotly Comparison Rendering
        st.markdown("---")
        st.subheader(f"🔄 Comparative Price Analytics ({selected_horizon.upper()})")
        
        should_normalize = st.checkbox("Normalize baseline to % Return (Enables direct performance asset comparison)", value=False)
        
        chart_fig = go.Figure()
        
        for ticker in price_dataframe.columns:
            target_series = price_dataframe[ticker].dropna()
            if not target_series.empty:
                plotting_y = target_series
                tooltip_format = ':,.2f'
                
                if should_normalize:
                    plotting_y = ((target_series / target_series.iloc[0]) - 1) * 100
                    tooltip_format = '+.2f%'
                
                chart_fig.add_trace(go.Scatter(
                    x=target_series.index,
                    y=plotting_y,
                    mode='lines',
                    name=ticker,
                    line=dict(width=2.5),
                    hovertemplate=f'<b>{ticker}</b>: %{{y{tooltip_format}}}<extra></extra>'
                ))
                
        chart_fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=10, b=10),
            height=480,
            xaxis=dict(showgrid=True, gridcolor='#232a3b'),
            yaxis=dict(
                showgrid=True, 
                gridcolor='#232a3b',
                title="% Growth" if should_normalize else "Closing Value"
            ),
            hovermode="x unified"
        )
        
        st.plotly_chart(chart_fig, use_container_width=True)
