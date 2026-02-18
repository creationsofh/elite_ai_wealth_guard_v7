import streamlit as st
import json
import os
from authlib.integrations.requests_client import OAuth2Session
import requests

st.set_page_config(layout="wide")

# -------------------- DATABASE --------------------
DB_FILE = "database.json"

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({}, f)

with open(DB_FILE, "r") as f:
    users = json.load(f)

# -------------------- SESSION --------------------
if "user" not in st.session_state:
    st.session_state.user = None

# -------------------- GOOGLE CONFIG --------------------
CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
REDIRECT_URI = st.secrets["REDIRECT_URI"]

AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
USER_INFO = "https://www.googleapis.com/oauth2/v1/userinfo"

# -------------------- LOGIN FUNCTION --------------------
def google_login():

    oauth = OAuth2Session(
        CLIENT_ID,
        CLIENT_SECRET,
        scope="openid email profile",
        redirect_uri=REDIRECT_URI
    )

    authorization_url, state = oauth.create_authorization_url(
        AUTHORIZATION_ENDPOINT,
        access_type="offline",
        prompt="select_account"
    )

    return authorization_url

# -------------------- CALLBACK HANDLING --------------------
query_params = st.query_params

if "code" in query_params:

    oauth = OAuth2Session(
        CLIENT_ID,
        CLIENT_SECRET,
        redirect_uri=REDIRECT_URI
    )

    token = oauth.fetch_token(
        TOKEN_ENDPOINT,
        code=query_params["code"],
        client_secret=CLIENT_SECRET
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


# -------------------- UI --------------------
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

    st.write("Dashboard coming next...")


