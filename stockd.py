import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import plotly.express as px
from alpha_vantage.fundamentaldata import FundamentalData
from stocknews import StockNews

st.header('Indian Stock Dashboard')

# Sidebar inputs
ticker = st.sidebar.text_input('Symbol Code', 'INFY')
exchange = st.sidebar.text_input('Exchange', 'NSE')
start_date = st.sidebar.date_input('Start Date')
end_date = st.sidebar.date_input('End Date')

# Create the URL for the stock
url = f'https://www.google.com/finance/quote/{ticker}:{exchange}'

# Request and parse the webpage
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Extract the required information
try:
    price = float(soup.find(class_='YMlKec fxKbKc').text.strip()[1:].replace(",", ""))
except AttributeError:
    price = None

try:
    previous_close = float(soup.find(class_='P6K39c').text.strip()[1:].replace(",", ""))
except AttributeError:
    previous_close = None

try:
    revenue = soup.find(class_='QXDnM').text.strip()  # Ensure the class name is correct
except AttributeError:
    revenue = None

try:
    news = soup.find(class_='Yfwt5').text.strip()
except AttributeError:
    news = None

try:
    about = soup.find(class_='bLLb2d').text.strip()
except AttributeError:
    about = None

# Create a dictionary to hold the extracted information
data = {
    'Price': price,
    'Previous Close': previous_close,
    'Revenue': revenue,
    'News': news,
    'About': about
}

# Convert dictionary to DataFrame (optional)
df = pd.DataFrame([data]).T

# Display the information
st.write(df)

# If the DataFrame is empty, display a message
if df.empty:
    st.write("No data available or invalid ticker/exchange")

# Fetching data for stock visualization
if ticker and start_date and end_date:
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    if not stock_data.empty:
        fig = px.line(stock_data, x=stock_data.index, y='Adj Close', title=ticker)
        st.plotly_chart(fig)
    else:
        st.write("No data found for the given ticker and date range.")
else:
    st.write("Please enter a ticker symbol and select a date range.")

# Creating tabs for additional information
pricing_data, fundamental_data, news = st.tabs(["Pricing Data", "Fundamental Data", "Top 10 News"])

with pricing_data:
    st.header('Price Movements')
    if not stock_data.empty:
        stock_data['% Change'] = stock_data['Adj Close'].pct_change() * 100
        stock_data.dropna(inplace=True)
        st.write(stock_data)
        
        # Annual return calculation
        annual_return = stock_data['% Change'].mean() * 252
        st.write(f'Annual Return: {annual_return:.2f}%')
        
        # Standard deviation calculation
        stdev = np.std(stock_data['% Change']) * np.sqrt(252)
        st.write(f'Standard Deviation: {stdev:.2f}%')
        
        # Risk-adjusted return (Sharpe Ratio)
        sharpe_ratio = annual_return / stdev
        st.write(f'Risk-Adjusted Return (Sharpe Ratio): {sharpe_ratio:.2f}')
    else:
        st.write("No data to display.")

with fundamental_data:
    st.header('Fundamental Data')
    key = 'YOUR_ALPHA_VANTAGE_API_KEY'  # Replace with your Alpha Vantage API key
    fd = FundamentalData(key, output_format='pandas')

    # Balance Sheet
    try:
        balance_sheet, meta_data = fd.get_balance_sheet_annual(ticker)
        bs = balance_sheet.T
        bs.columns = list(bs.iloc[0])
        bs = bs[1:]  # Remove the first row used as header
        st.subheader('Balance Sheet')
        st.write(bs)
    except Exception as e:
        st.write(f"Error fetching balance sheet data: {e}")

    # Income Statement
    try:
        income_statement, meta_data = fd.get_income_statement_annual(ticker)
        is1 = income_statement.T
        is1.columns = list(is1.iloc[0])
        is1 = is1[1:]  # Remove the first row used as header
        st.subheader('Income Statement')
        st.write(is1)
    except Exception as e:
        st.write(f"Error fetching income statement data: {e}")

    # Cash Flow Statement
    try:
        cash_flow, meta_data = fd.get_cash_flow_annual(ticker)
        cf = cash_flow.T
        cf.columns = list(cf.iloc[0])
        cf = cf[1:]  # Remove the first row used as header
        st.subheader('Cash Flow Statement')
        st.write(cf)
    except Exception as e:
        st.write(f"Error fetching cash flow data: {e}")

with news:
    st.header(f'News for {ticker}')
    if ticker:
        sn = StockNews(ticker, save_news=False)
        df_news = sn.read_rss()
        
        # Display the top 10 news articles
        for i in range(min(10, len(df_news))):  # Ensure you don't exceed the available articles
            st.subheader(f'News {i + 1}')
            st.write(f"**Published:** {df_news['published'].iloc[i]}")
            st.write(f"**Title:** {df_news['title'].iloc[i]}")
            st.write(f"**Summary:** {df_news['summary'].iloc[i]}")
            st.write(f"**Title Sentiment:** {df_news['sentiment_title'].iloc[i]}")
            st.write(f"**News Sentiment:** {df_news['sentiment_summary'].iloc[i]}")
    else:
        st.write("Please enter a ticker symbol to fetch news.")
