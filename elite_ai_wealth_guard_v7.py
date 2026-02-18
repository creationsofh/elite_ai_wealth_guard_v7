import streamlit as st
import json
import os
import pandas as pd
import yfinance as yf
import plotly.express as px
import numpy as np
import requests
from authlib.integrations.requests_client import OAuth2Session

st.set_page_config(layout="wide")

# ---------------- DATABASE ----------------
DB_FILE = "database.json"

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({}, f)

with open(DB_FILE, "r") as f:
    users = json.load(f)

# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user = None

# ---------------- GOOGLE CONFIG ----------------
CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
REDIRECT_URI = st.secrets["REDIRECT_URI"]

AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
USER_INFO = "https://www.googleapis.com/oauth2/v2/userinfo"

def google_login():
    oauth = OAuth2Session(
        CLIENT_ID,
        scope="openid email profile",
        redirect_uri=REDIRECT_URI
    )
    authorization_url, state = oauth.create_authorization_url(
        AUTHORIZATION_ENDPOINT,
        access_type="offline",
        prompt="select_account"
    )
    return authorization_url

# ---------------- CALLBACK ----------------
query_params = st.query_params

if "code" in query_params:

    oauth = OAuth2Session(
        CLIENT_ID,
        redirect_uri=REDIRECT_URI
    )

    token = oauth.fetch_token(
        TOKEN_ENDPOINT,
        code=query_params["code"],
        client_secret=CLIENT_SECRET,
        include_client_id=True
    )

    resp = requests.get(
        USER_INFO,
        headers={"Authorization": f"Bearer {token['access_token']}"}
    )

    user_info = resp.json()
    email = user_info["email"]

    st.session_state.user = email

    if email not in users:
        users[email] = {
            "portfolio": [],
            "tier": "free"
        }
        with open(DB_FILE, "w") as f:
            json.dump(users, f)

    st.query_params.clear()
    st.rerun()

# ---------------- UI ----------------
st.title("💎 Elite AI Wealth Guard PRO")

if not st.session_state.user:

    login_url = google_login()
    st.markdown("## Secure Google Login")
    st.markdown(f"[Login with Google]({login_url})")

else:

    email = st.session_state.user
    st.success(f"Logged in as {email}")

    if st.button("Logout"):
        st.session_state.user = None
        st.rerun()

    user_data = users[email]
    portfolio = user_data["portfolio"]

    st.divider()

    # -------- ADD STOCK --------
    st.subheader("Add Stock")

    col1, col2, col3 = st.columns(3)
    ticker = col1.text_input("Ticker")
    qty = col2.number_input("Quantity", min_value=0)
    buy_price = col3.number_input("Buy Price", min_value=0.0)

    if st.button("Save Stock"):
        portfolio.append({
            "ticker": ticker.upper(),
            "quantity": qty,
            "buy_price": buy_price
        })
        users[email]["portfolio"] = portfolio
        with open(DB_FILE, "w") as f:
            json.dump(users, f)
        st.success("Stock Saved")
        st.rerun()

    if portfolio:

        data_list = []
        total_value = 0
        total_profit = 0

        for stock in portfolio:
            try:
                ticker_obj = yf.Ticker(stock["ticker"])
                hist = ticker_obj.history(period="1d")
                current_price = hist["Close"].iloc[-1]
            except:
                current_price = 0

            value = current_price * stock["quantity"]
            profit = (current_price - stock["buy_price"]) * stock["quantity"]

            total_value += value
            total_profit += profit

            data_list.append({
                "Ticker": stock["ticker"],
                "Quantity": stock["quantity"],
                "Buy Price": stock["buy_price"],
                "Current Price": round(current_price, 2),
                "Value": round(value, 2),
                "P/L": round(profit, 2)
            })

        df = pd.DataFrame(data_list)

        # -------- METRICS --------
        col1, col2 = st.columns(2)
        col1.metric("Portfolio Value", f"${round(total_value,2)}")
        col2.metric("Total Profit/Loss", f"${round(total_profit,2)}")

        st.divider()

        st.dataframe(df, use_container_width=True)

        # -------- PIE CHART --------
        fig = px.pie(df, values="Value", names="Ticker", title="Allocation")
        st.plotly_chart(fig, use_container_width=True)

        # -------- AI RISK SCORE --------
        st.subheader("AI Risk Score")

        values = df["Value"]
        concentration = max(values) / sum(values)

        if concentration > 0.6:
            risk = "High Risk"
        elif concentration > 0.4:
            risk = "Medium Risk"
        else:
            risk = "Low Risk"

        st.info(f"Portfolio Risk Level: {risk}")

    else:
        st.info("No stocks added yet.")
