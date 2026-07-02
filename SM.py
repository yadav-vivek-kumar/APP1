import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import requests

# Page Configuration
st.set_page_config(
    page_title="Global Stock Analytics",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Global Stock Analytics Dashboard")

# Sidebar for configuration
st.sidebar.title("🔍 Configuration")
ticker_input = st.sidebar.text_input("Enter Ticker Symbol", value="AAPL").upper().strip()
time_period = st.sidebar.selectbox("Horizon", ["1D", "5D", "1Mo", "6Mo", "1Y", "5Y", "Max"], index=4).lower()

# CACHE THE FETCH FUNCTION TO MINIMIZE REQUESTS
@st.cache_data(ttl=600)  # Caches data for 10 mins to stop spamming Yahoo
def fetch_stock_data(ticker, period):
    interval = "1m" if period == "1d" else "5m" if period == "5d" else "1d"
    
    # 🌟 THE FIX: Emulate a genuine web browser session to bypass 429 Rate Limits
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    # Pass the fake browser session directly to yfinance
    stock = yf.Ticker(ticker, session=session)
    hist = stock.history(period=period, interval=interval)
    
    try:
        info = stock.info
    except Exception:
        info = {}  # Fallback if metadata blocks persist
        
    return hist, info

if ticker_input:
    try:
        with st.spinner("Fetching market data through proxy session..."):
            df, info = fetch_stock_data(ticker_input, time_period)
        
        if df.empty:
            st.error(f"No data found for '{ticker_input}'. Make sure the ticker is valid.")
        else:
            # Fallbacks safely map variables if info scraping is partially blocked
            comp_name = info.get('longName') or ticker_input
            currency = info.get('currency') or "USD"
            current_price = info.get('currentPrice') or info.get('regularMarketPrice') or df['Close'].iloc[-1]
            prev_close = info.get('previousClose') or df['Close'].iloc[0]
            
            price_change = current_price - prev_close
            percent_change = (price_change / prev_close) * 100 if prev_close else 0

            # Dashboard Display
            st.subheader(f"{comp_name} ({ticker_input})")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Current Price", f"{current_price:,.2f} {currency}")
            col2.metric("Change", f"{price_change:+,.2f}", f"{percent_change:+.2f}%")
            col3.metric("High", f"{df['High'].max():,.2f} {currency}")
            col4.metric("Low", f"{df['Low'].min():,.2f} {currency}")

            # Plotly Chart Setup
            st.markdown("---")
            line_color = '#10b981' if current_price >= prev_close else '#ef4444'
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df.index, y=df['Close'], mode='lines', line=dict(color=line_color, width=2)
            ))
            fig.update_layout(
                template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=10, r=10, t=10, b=10), height=400
            )
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
