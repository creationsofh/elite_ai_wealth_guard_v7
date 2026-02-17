# elite_ai_wealth_guard_v7.py
import streamlit as st
import pandas as pd
import json
import requests
import os
import yfinance as yf
import plotly.graph_objects as go

# -------------------- USER DATA --------------------
import os
import json

user_data_file = "user_data.json"

# Ensure the JSON file exists and is valid
if not os.path.exists(user_data_file):
    with open(user_data_file, "w") as f:
        json.dump({}, f)  # create empty JSON

# Safe load
try:
    with open(user_data_file, "r") as f:
        users = json.load(f)
except json.JSONDecodeError:
    # If file is corrupted, reset to empty
    users = {}
    with open(user_data_file, "w") as f:
        json.dump(users, f)

# -------------------- APP TITLE --------------------
st.title("Elite AI Wealth Guard v7 🚀 (Final Version)")

# -------------------- LOGIN / REGISTER --------------------
login_option = st.radio("Login / Register", ["Login", "Register"])
email = st.text_input("Email")
bot_token_input = st.text_input("Telegram Bot Token (optional)")
chat_id_input = st.text_input("Telegram Chat ID (optional)")

if login_option == "Register":
    if st.button("Register"):
        if email in users:
            st.warning("User already exists!")
        else:
            users[email] = {
                "telegram": {"bot_token": bot_token_input, "chat_id": chat_id_input},
                "portfolio": []
            }
            with open("user_data.json", "w") as f:
                json.dump(users, f, indent=2)
            st.success("Registered! Please login.")

elif login_option == "Login":
    if st.button("Login"):
        if email in users:
            st.session_state["user"] = email
            st.success(f"Logged in as {email}")
        else:
            st.warning("User not found. Please register.")

# -------------------- DASHBOARD --------------------
if st.session_state["user"]:
    user_email = st.session_state["user"]
    st.header(f"Welcome {user_email}")
    user_data = users[user_email]

    # -------------------- Telegram Setup --------------------
    st.subheader("Telegram Alerts")
    tg_token = st.text_input("BOT Token", value=user_data.get("telegram", {}).get("bot_token", ""))
    tg_chat = st.text_input("Chat ID", value=user_data.get("telegram", {}).get("chat_id", ""))
    if st.button("Save Telegram Info"):
        user_data["telegram"] = {"bot_token": tg_token, "chat_id": tg_chat}
        with open("user_data.json", "w") as f:
            json.dump(users, f, indent=2)
        st.success("Telegram info saved!")

    # -------------------- Portfolio Upload --------------------
    st.subheader("Upload Portfolio File (CSV/Excel)")
    uploaded_file = st.file_uploader("Upload CSV / Excel", type=["csv", "xlsx"])
    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        for _, row in df.iterrows():
            ticker = row["Ticker"]
            qty = row["Quantity"]
            price = row["Purchase Price"]
            found = False
            for stock in user_data["portfolio"]:
                if stock["ticker"] == ticker:
                    stock["quantity"] = qty
                    stock["purchase_price"] = price
                    found = True
            if not found:
                user_data["portfolio"].append({
                    "ticker": ticker,
                    "quantity": qty,
                    "purchase_price": price
                })
        with open("user_data.json", "w") as f:
            json.dump(users, f, indent=2)
        st.success("Portfolio imported successfully!")

    # -------------------- Manual Portfolio --------------------
    st.subheader("Add / Update Stock Manually")
    ticker = st.text_input("Ticker Symbol")
    qty = st.number_input("Quantity", min_value=0)
    price = st.number_input("Purchase Price", min_value=0.0)
    if st.button("Add / Update Stock"):
        if ticker:
            found = False
            for stock in user_data["portfolio"]:
                if stock["ticker"] == ticker:
                    stock["quantity"] = qty
                    stock["purchase_price"] = price
                    found = True
            if not found:
                user_data["portfolio"].append({
                    "ticker": ticker,
                    "quantity": qty,
                    "purchase_price": price
                })
            with open("user_data.json", "w") as f:
                json.dump(users, f, indent=2)
            st.success(f"{ticker} added/updated!")

    # -------------------- Real-Time Prices & AI Insights --------------------
    st.subheader("Live Portfolio & AI Insights")
    portfolio_data = []
    total_value = 0
    total_profit = 0
    dividend_total = 0

    for stock in user_data["portfolio"]:
        try:
            ticker_obj = yf.Ticker(stock["ticker"])
            current_price = ticker_obj.history(period="1d")['Close'].iloc[-1]
            div_yield = ticker_obj.info.get("dividendYield", 0)
        except:
            current_price = None
            div_yield = 0

        profit_loss = (current_price - stock["purchase_price"]) * stock["quantity"] if current_price else None
        estimated_dividend = current_price * stock["quantity"] * div_yield if current_price else 0

        portfolio_data.append({
            "Ticker": stock["ticker"],
            "Quantity": stock["quantity"],
            "Purchase Price": stock["purchase_price"],
            "Current Price": current_price,
            "Profit/Loss": profit_loss,
            "Dividend Yield": div_yield,
            "Estimated Dividend": estimated_dividend
        })

        if profit_loss:
            total_profit += profit_loss
        if current_price:
            total_value += current_price * stock["quantity"]
            dividend_total += estimated_dividend

    portfolio_df = pd.DataFrame(portfolio_data)
    st.dataframe(portfolio_df)

    # -------------------- Portfolio Graph --------------------
    if portfolio_df["Profit/Loss"].notnull().any():
        fig = go.Figure(data=[go.Bar(
            x=portfolio_df["Ticker"],
            y=portfolio_df["Profit/Loss"],
            text=portfolio_df["Profit/Loss"],
            textposition='auto'
        )])
        st.plotly_chart(fig)

    # -------------------- Telegram Alerts Function --------------------
    def send_user_telegram(message):
        if "telegram" not in user_data or not user_data["telegram"]:
            return
        bot_token = user_data["telegram"].get("bot_token")
        chat_id = user_data["telegram"].get("chat_id")
        if bot_token and chat_id:
            try:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
                requests.post(url, data=payload)
            except:
                pass

    # Example alerts: P/L threshold and low dividend warning
    for stock in portfolio_data:
        if stock["Profit/Loss"] and stock["Profit/Loss"] < -500:
            send_user_telegram(f"⚠️ Alert: {stock['Ticker']} P/L = {stock['Profit/Loss']:.2f}")
        if stock["Estimated Dividend"] < 1 and stock["Dividend Yield"] > 0:
            send_user_telegram(f"ℹ️ Low Dividend: {stock['Ticker']} estimated {stock['Estimated Dividend']:.2f}")

    st.success("Telegram alerts checked.")

    # -------------------- AI Dashboard --------------------
    st.subheader("AI Portfolio Insights Summary")
    st.metric("Total Portfolio Value", f"{total_value:.2f}")
    st.metric("Total Profit / Loss", f"{total_profit:.2f}")
    st.metric("Total Estimated Dividend", f"{dividend_total:.2f}")

    # AI suggestions (simple logic)
    st.subheader("AI Suggestions")
    underperforming = [s["Ticker"] for s in portfolio_data if s["Profit/Loss"] and s["Profit/Loss"] < 0]
    if underperforming:
        st.warning(f"Consider reviewing/selling: {', '.join(underperforming)}")
    low_dividend = [s["Ticker"] for s in portfolio_data if s["Dividend Yield"] < 0.02 and s["Dividend Yield"] > 0]
    if low_dividend:
        st.info(f"Low dividend stocks: {', '.join(low_dividend)}")
