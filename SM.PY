import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# 1. Page Configuration & Custom UI Styling
st.set_page_config(
    page_title="Global Stock Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished UI/UX
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="metric-container"] {
        background-color: #1f2937;
        border: 1px solid #374151;
        padding: 15px;
        border-radius: 10px;
        color: white;
    }
    div[data-testid="stSidebar"] { background-color: #111827; }
    h1, h2, h3 { color: #f3f4f6; }
    </style>
""", unsafe_allow_html=True)

# 2. Sidebar - Navigation & Stock Selection
st.sidebar.title("🔍 Stock Discovery")
st.sidebar.markdown("Select or type a global ticker to pull live financial data.")

# Curated list of global suggestions
suggestions = {
    "Apple Inc. (USA)": "AAPL",
    "Microsoft Corp. (USA)": "MSFT",
    "NVIDIA Corp. (USA)": "NVDA",
    "Reliance Industries (India)": "RELIANCE.NS",
    "Tata Consultancy Services (India)": "TCS.NS",
    "Sony Group (Japan)": "SONY",
    "ASML Holding (Netherlands)": "ASML",
    "BP plc (UK)": "BP"
}

selected_suggest = st.sidebar.selectbox(
    "Suggested Global Stocks",
    options=list(suggestions.keys())
)

# Allow manual override for any global ticker
custom_ticker = st.sidebar.text_input(
    "Or Enter Any Global Ticker Symbol (e.g., TSLA, INFY.NS, V)",
    value=suggestions[selected_suggest]
).upper().strip()

# Time period selection for the line chart
st.sidebar.markdown("---")
st.sidebar.subheader("📅 Chart Parameters")
time_period = st.sidebar.selectbox(
    "Select Time Horizon",
    options=["1D", "5D", "1Mo", "6Mo", "1Y", "5Y", "Max"],
    index=4  # Default to 1 Year
).lower()

# Map UI selections to yfinance valid periods
period_map = {"1d": "1d", "5d": "5d", "1mo": "1mo", "6mo": "6mo", "1y": "1y", "5y": "5y", "max": "max"}
valid_period = period_map[time_period]

# Determine interval based on period to keep it performant
interval = "1m" if valid_period == "1d" else "5m" if valid_period == "5d" else "1d"

# 3. Main Dashboard Layout
st.title("📈 Global Stock Analytics Dashboard")
st.markdown(f"Fetching real-time and historical market data for **{custom_ticker}**.")

@st.cache_data(ttl=300)  # Cache data for 5 minutes to optimize performance
def load_stock_data(ticker, period, interval):
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period, interval=interval)
    info = stock.info
    return hist, info

if custom_ticker:
    try:
        with st.spinner(f"Retrieving market data for {custom_ticker}..."):
            df, info = load_stock_data(custom_ticker, valid_period, interval)
        
        if df.empty:
            st.error(f"No data found for ticker '{custom_ticker}'. Please verify the symbol on Yahoo Finance.")
        else:
            # Extract Company Meta Data safely
            comp_name = info.get('longName', custom_ticker)
            currency = info.get('currency', 'USD')
            current_price = info.get('currentPrice') or info.get('regularMarketPrice') or df['Close'].iloc[-1]
            prev_close = info.get('previousClose') or df['Close'].iloc[0]
            
            # Fallback calculation if current_price is missing from info dict
            price_change = current_price - prev_close
            percent_change = (price_change / prev_close) * 100

            # Header Section
            st.subheader(f"{comp_name} ({custom_ticker})")
            if 'summaryProfile' in info and 'industry' in info:
                st.caption(f"**Sector:** {info.get('sector')} | **Industry:** {info.get('industry')} | **Currency:** {currency}")

            # Metric Display Row
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Current Price", f"{current_price:,.2f} {currency}")
            col2.metric("Change (vs Prev. Close)", f"{price_change:+,.2f}", f"{percent_change:+.2f}%")
            col3.metric("Day High", f"{df['High'].max():,.2f} {currency}")
            col4.metric("Day Low", f"{df['Low'].min():,.2f} {currency}")

            # 4. Interactive Plotly Line Chart
            st.markdown("---")
            st.subheader(f"Historical Performance ({time_period.upper()})")
            
            fig = go.Figure()
            
            # Dynamic line coloring based on performance
            line_color = '#10b981' if current_price >= prev_close else '#ef4444'
            
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['Close'],
                mode='lines',
                name='Close Price',
                line=dict(color=line_color, width=2.5),
                hovertemplate='%{x}<br>Price: %{y:,.2f} ' + currency + '<extra></extra>'
            ))

            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=10, b=20),
                height=450,
                xaxis=dict(showgrid=True, gridcolor='#374151'),
                yaxis=dict(showgrid=True, gridcolor='#374151', title=f"Price ({currency})"),
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True)

            # 5. Summary Statistics Tab Panel
            st.markdown("---")
            with st.expander("📊 View Fundamental Profile Summary"):
                st.markdown(f"**Business Summary:**\n{info.get('longBusinessSummary', 'No summary available.')}")

    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        st.info("Tip: Ensure Indian stocks end with `.NS` (e.g., `RELIANCE.NS`) and UK stocks end with `.L` (e.g., `BP.L`).")
