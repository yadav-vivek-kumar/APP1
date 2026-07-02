import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import requests
import random

# Page UI Config
st.set_page_config(
    page_title="Pro Stock Portfolio Dashboard",
    page_icon="📊",
    layout="wide"
)

# Dark Premium UI Theme Customization
st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: #111827;
        border: 1px solid #1f2937;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    div[data-testid="stSidebar"] {
        background-color: #0b0f19;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎛️ Multi-Stock Analytics Terminal")
st.markdown("Select multiple global assets to pull live metrics and cross-compare pricing charts.")

# 🌟 BROWSER AGENT ROTATOR TO BYPASS THE 429 DEPLOYMENT LIMITS
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
]

@st.cache_data(ttl=300) # Prevents spamming Yahoo API on every toggle
def get_stock_data(tickers, period):
    interval = "5m" if period in ["1d", "5d"] else "1d"
    
    session = requests.Session()
    session.headers.update({'User-Agent': random.choice(USER_AGENTS)})
    
    combined_df = pd.DataFrame()
    meta_infos = {}
    
    for t in tickers:
        try:
            stock = yf.Ticker(t, session=session)
            hist = stock.history(period=period, interval=interval)
            if not hist.empty:
                combined_df[t] = hist['Close']
                # Graceful extraction of current details without throwing core errors
                try:
                    meta_infos[t] = stock.info
                except:
                    meta_infos[t] = {}
        except Exception:
            pass # Keep iterating over remaining valid symbols
            
    return combined_df, meta_infos

# --- SIDEBAR CONTROLS ---
st.sidebar.header("🎯 Asset Watchlist Configuration")

# Clean Mapping of Ticker Names to Symbols
ticker_directory = {
    "Apple Inc. (US)": "AAPL",
    "Microsoft Corp. (US)": "MSFT",
    "NVIDIA Corporation (US)": "NVDA",
    "Tesla Inc. (US)": "TSLA",
    "Reliance Industries (India)": "RELIANCE.NS",
    "Tata Consultancy (India)": "TCS.NS",
    "Infosys Ltd (India)": "INFY.NS",
    "Sony Group (Japan)": "SONY"
}

# The Multi-Select Dropdown
selected_display_names = st.sidebar.multiselect(
    "Choose Stocks to Monitor:",
    options=list(ticker_directory.keys()),
    default=["Apple Inc. (US)", "NVIDIA Corporation (US)"]
)

# Convert mapped display names to active symbols
active_tickers = [ticker_directory[name] for name in selected_display_names]

# Text entry to type custom alternative tickers manually
custom_symbols = st.sidebar.text_input("➕ Or add alternative symbols (Comma separated, e.g., AMD, AMZN, GOOG)")
if custom_symbols:
    for custom_t in custom_symbols.split(","):
        clean_t = custom_t.strip().upper()
        if clean_t and clean_t not in active_tickers:
            active_tickers.append(clean_t)

# Time Frame Selector
st.sidebar.markdown("---")
time_horizon = st.sidebar.radio(
    "📈 Performance Horizon",
    options=["1D", "5D", "1Mo", "6Mo", "1Y", "5Y"],
    index=4
).lower()

# --- MAIN SCREEN LOGIC ---
if not active_tickers:
    st.info("Select or enter a ticker symbol in the sidebar menu to get started.")
else:
    with st.spinner("Streaming real-time financial tracking modules..."):
        price_history, market_meta = get_stock_data(active_tickers, time_horizon)
        
    if price_history.empty:
        st.error("Could not fetch data for selected entries. Verify internet connectivity or ticker naming conventions.")
    else:
        # Display Current Pricing Cards dynamically inside columns
        st.subheader("⚡ Real-time Market Snapshot")
        cols = st.columns(len(active_tickers))
        
        for idx, ticker in enumerate(active_tickers):
            if ticker in price_history.columns:
                hist_series = price_history[ticker].dropna()
                if not hist_series.empty:
                    latest_price = hist_series.iloc[-1]
                    opening_price = hist_series.iloc[0]
                    delta = latest_price - opening_price
                    delta_pct = (delta / opening_price) * 100
                    
                    info_dict = market_meta.get(ticker, {})
                    currency = info_dict.get('currency', 'USD')
                    company_label = info_dict.get('shortName', ticker)
                    
                    with cols[idx]:
                        st.metric(
                            label=company_label,
                            value=f"{latest_price:,.2f} {currency}",
                            delta=f"{delta:+,.2f} ({delta_pct:+.2f}%)"
                        )

        # Main Comparison Visual Graph
        st.markdown("---")
        st.subheader(f"🔄 Relative Historical Trends ({time_horizon.upper()})")
        
        fig = go.Figure()
        
        # Decide if we normalize the performance to compare percentage changes rather than absolute prices
        normalize_data = st.checkbox("Normalize Prices (% Return Change relative to baseline timeline start)", value=False)
        
        for ticker in price_history.columns:
            series = price_history[ticker].dropna()
            if not series.empty:
                y_values = series
                hover_format = ':,.2f'
                
                if normalize_data:
                    y_values = ((series / series.iloc[0]) - 1) * 100
                    hover_format = '+.2f%'
                
                fig.add_trace(go.Scatter(
                    x=series.index,
                    y=y_values,
                    mode='lines',
                    name=ticker,
                    line=dict(width=2.5),
                    hovertemplate=f'<b>{ticker}</b>: %{{y{hover_format}}}<extra></extra>'
                ))
                
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=10, b=10),
            height=500,
            xaxis=dict(showgrid=True, gridcolor='#232a3b'),
            yaxis=dict(
                showgrid=True, 
                gridcolor='#232a3b', 
                title="% Change" if normalize_data else "Raw Currency Price"
            ),
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
