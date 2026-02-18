import streamlit as st
import json
import os
from authlib.integrations.requests_client import OAuth2Session
from dashboard import show_dashboard

st.set_page_config(page_title="Elite AI Wealth Guard", layout="wide")

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

# ---------------- GOOGLE LOGIN ----------------
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

query_params = st.query_params

if "code" in query_params:
    oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI)
    token = oauth.fetch_token(
        TOKEN_ENDPOINT,
        code=query_params["code"],
        client_secret=CLIENT_SECRET,
        include_client_id=True
    )

    resp = oauth.get(USER_INFO)
    user_info = resp.json()
    email = user_info["email"]

    st.session_state.user = email

    if email not in users:
        users[email] = {"portfolio": [], "tier": "free"}
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
    st.success(f"Logged in as {st.session_state.user}")
    if st.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # ---------------- DASHBOARD ----------------
    show_dashboard(st.session_state.user, users, DB_FILE)
