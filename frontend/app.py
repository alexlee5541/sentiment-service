import streamlit as st
import requests
import pandas as pd
import os
import time

# Access the API service via Docker network name 'web'
# If running locally outside docker, use localhost
API_URL = os.getenv("API_URL", "http://web:8000")

st.set_page_config(page_title="Sentiment AI Dashboard", layout="wide")

st.title("🤖 Financial News Sentiment AI")

# --- SIDEBAR (Controls) ---
st.sidebar.header("Controls")
ticker = st.sidebar.text_input("Stock Ticker", value="AAPL").upper()

if st.sidebar.button("Analyze New Data"):
    with st.spinner(f"Fetching and Analyzing news for {ticker}..."):
        try:
            # Call the FastAPI /sentiment endpoint
            response = requests.get(f"{API_URL}/sentiment", params={"ticker": ticker})
            if response.status_code == 200:
                st.success("Analysis Complete!")
                st.json(response.json()) # Show raw JSON for debugging
            else:
                st.error(f"Error: {response.status_code}")
        except Exception as e:
            st.error(f"Connection Error: {e}")

# --- MAIN PAGE (History & Trends) ---
st.header("📉 Historical Sentiment Data")

def load_data():
    try:
        # Call the /history endpoint we made in Phase 5
        response = requests.get(f"{API_URL}/history")
        if response.status_code == 200:
            return response.json()['records']
        else:
            return []
    except:
        return []

# Refresh Button
if st.button("Refresh History"):
    st.rerun()

records = load_data()

if records:
    # Convert list of dicts to Pandas DataFrame (Excel for Python)
    df = pd.DataFrame(records)
    
    # 1. Key Metrics
    col1, col2, col3 = st.columns(3)
    total = len(df)
    positive = len(df[df['sentiment'] == 'Positive'])
    negative = len(df[df['sentiment'] == 'Negative'])
    
    col1.metric("Total Articles Analyzed", total)
    col2.metric("Bullish Articles", positive, delta_color="normal")
    col3.metric("Bearish Articles", negative, delta_color="inverse")

    # 2. The Data Table
    st.subheader("Recent Analysis")
    # Show specific columns
    st.dataframe(df[['id', 'headline', 'sentiment', 'confidence', 'created_at']])

    # 3. Charts (The "Boss" feature)
    st.subheader("Sentiment Distribution")
    st.bar_chart(df['sentiment'].value_counts())

else:
    st.info("No data in database yet. Run an analysis from the sidebar!")