import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from ai_engine import analyze_portfolio

def show_dashboard(email, users, db_file):
    user_data = users[email]
    portfolio = user_data["portfolio"]

    st.subheader("📊 Add / Update Portfolio")

    col1, col2, col3 = st.columns(3)
    ticker = col1.text_input("Ticker")
    qty = col2.number_input("Quantity", min_value=0)
    buy_price = col3.number_input("Buy Price", min_value=0.0)

    if st.button("Save Stock"):
        if ticker and qty > 0:
            portfolio.append({
                "ticker": ticker.upper(),
                "quantity": qty,
                "buy_price": buy_price
            })
            users[email]["portfolio"] = portfolio
            with open(db_file, "w") as f:
                pd.json.dump(users, f)
            st.success(f"{ticker.upper()} saved!")
            st.experimental_rerun()

    if portfolio:
        data_list = []
        for stock in portfolio:
            try:
                ticker_obj = yf.Ticker(stock["ticker"])
                hist = ticker_obj.history(period="1d")
                current_price = hist["Close"].iloc[-1]
            except:
                current_price = 0

            value = current_price * stock["quantity"]
            profit = (current_price - stock["buy_price"]) * stock["quantity"]

            data_list.append({
                "Ticker": stock["ticker"],
                "Quantity": stock["quantity"],
                "Buy Price": stock["buy_price"],
                "Current Price": round(current_price,2),
                "Value": round(value,2),
                "P/L": round(profit,2)
            })

        df = pd.DataFrame(data_list)
        total_value = df["Value"].sum()
        total_profit = df["P/L"].sum()

        col1, col2 = st.columns(2)
        col1.metric("Portfolio Value", f"${round(total_value,2)}")
        col2.metric("Total Profit/Loss", f"${round(total_profit,2)}")

        st.dataframe(df, use_container_width=True)
        fig = px.pie(df, values="Value", names="Ticker", title="Allocation")
        st.plotly_chart(fig, use_container_width=True)

        # AI analysis
        analyze_portfolio(df)

    else:
        st.info("No stocks added yet.")
