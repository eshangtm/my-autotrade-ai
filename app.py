import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import time
from datetime import datetime
import os

# --- 1. JANITOR LOGIC (AUTO-CLEANUP) ---
def janitor_wipeout():
    # Purana kachra saaf karne ke liye
    current_time = time.time()
    for f in os.listdir():
        if f.endswith(".xlsx"):
            # Agar file 24 ghante se purani hai toh delete kar do
            if os.stat(f).st_mtime < current_time - 86400:
                os.remove(f)

# --- 2. SOUND ALERT LOGIC ---
def play_alarm():
    # Browser mein beep sound bajane ke liye
    sound_html = """
        <audio autoplay>
            <source src="https://www.soundjay.com/buttons/sounds/beep-07a.mp3" type="audio/mpeg">
        </audio>
    """
    st.components.v1.html(sound_html, height=0)

# --- 3. AI PROBABILITY & DATA FETCHING ---
def get_market_data(ticker):
    try:
        df = yf.download(ticker, period="1d", interval="1m", progress=False)
        if df.empty: return None
        
        # AI Calculation (Probability Finder)
        # Logic: RSI + Volume Spike + Price Action
        close = df['Close']
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        vol_spike = df['Volume'].iloc[-1] > df['Volume'].tail(20).mean() * 1.5
        
        prob = 50 # Default
        if rsi < 30 or rsi > 70: prob += 25
        if vol_spike: prob += 15
        
        signal = "WAIT"
        if rsi < 35: signal = "STRONG BUY (REVERSAL)"
        elif rsi > 65: signal = "STRONG SELL (REVERSAL)"
        
        return {
            'Time': datetime.now().strftime("%H:%M:%S"),
            'Symbol': ticker,
            'LTP': round(close.iloc[-1], 2),
            'Volume': int(df['Volume'].iloc[-1]),
            'RSI': round(rsi, 2),
            'AI_Signal': signal,
            'Probability': min(prob, 98)
        }
    except:
        return None

# --- 4. DASHBOARD INTERFACE ---
st.set_page_config(page_title="AutoTrade AI Pro", layout="wide")
st.title("🤖 AutoTrade AI: Autonomous Trading Dashboard")

# User Inputs
st.sidebar.header("Settings")
market = st.sidebar.selectbox("Market Type", ["Crypto", "NSE (India)"])
if market == "Crypto":
    symbol = st.sidebar.text_input("Enter Pair (e.g. BTC-USD)", "BTC-USD")
else:
    symbol = st.sidebar.text_input("Enter Stock (e.g. RELIANCE.NS)", "RELIANCE.NS")

if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame()

# Loop
main_ui = st.empty()

while True:
    janitor_wipeout()
    data = get_market_data(symbol)
    
    with main_ui.container():
        if data:
            # 80% Probability Alert
            if data['Probability'] >= 80:
                st.toast(f"🔥 HIGH PROBABILITY ({data['Probability']}%) DETECTED!", icon="🚨")
                play_alarm()
                st.warning(f"ACTION REQUIRED: {data['AI_Signal']} at {data['LTP']}")

            # Metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Current Price", f"{data['LTP']}")
            c2.metric("AI Probability", f"{data['Probability']}%")
            c3.metric("Volume", data['Volume'])
            c4.metric("RSI (14m)", data['RSI'])
            
            # Log Update
            new_row = pd.DataFrame([data])
            st.session_state.history = pd.concat([new_row, st.session_state.history], ignore_index=True).head(50)
            
            # Data Table with Auto-Highlighting
            st.subheader("Live Market Log (Excel Structure)")
            def highlight_rows(s):
                return ['background-color: #064e3b; color: white' if v >= 80 else '' for v in s]
            
            st.dataframe(st.session_state.history.style.apply(highlight_rows, subset=['Probability']))
            
            # Excel Download Button
            st.session_state.history.to_excel("Live_Trading_Log.xlsx", index=False)
            with open("Live_Trading_Log.xlsx", "rb") as f:
                st.download_button("📥 Download Live Excel Log", f, file_name="Trading_Log.xlsx")
        else:
            st.error("Data fetch error. Reconnecting...")
            
    time.sleep(30) # Har 30 second mein refresh
    st.rerun()
