"""
Safety Stock Automation Portal — Login Page
Entry point for Streamlit Community Cloud deployment.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from utils.styles import LOGIN_CSS
from utils.auth import login

st.set_page_config(
    page_title="Safety Stock Portal — Login",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(LOGIN_CSS, unsafe_allow_html=True)

st.markdown("""
    <style>
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        section[data-testid="stSidebar"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# If already authenticated, redirect to dashboard
if st.session_state.get("authenticated", False):
    st.switch_page("pages/01_🏠_Dashboard.py")

# ── Centered login card ──────────────────────────────────────────────────────
st.markdown("""
<div style="height: 60px;"></div>
<div style="text-align: center; margin-bottom: 8px;">
    <div style="background: linear-gradient(135deg, #1f6feb, #0a5cc7);
                width: 72px; height: 72px; border-radius: 20px;
                display: flex; align-items: center; justify-content: center;
                font-size: 32px; font-weight: 800; color: white;
                margin: 0 auto 20px auto;
                box-shadow: 0 8px 32px rgba(31,111,235,0.5);
                font-family: 'Outfit', sans-serif;">
        SS
    </div>
    <h1 style="color: #f0f4f9; font-size: 30px; font-weight: 800;
               font-family: 'Outfit', sans-serif; margin: 0; letter-spacing: -0.02em;">
        Safety Stock Portal
    </h1>
    <p style="color: #798a9f; font-size: 15px; margin: 10px 0 0 0;">
        Inventory Automation &amp; Forecasting Platform
    </p>
</div>
<hr style="border-color: rgba(31,111,235,0.15); margin: 28px auto; max-width: 420px;">
""", unsafe_allow_html=True)

# Card container
col1, col2, col3 = st.columns([1, 2.2, 1])
with col2:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0e1729, #111e38);
                border: 1px solid rgba(31,111,235,0.22);
                border-radius: 18px; padding: 36px 32px 32px 32px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.5), 0 0 0 1px rgba(31,111,235,0.1);">
        <h3 style="color: #f0f4f9; font-size: 18px; font-weight: 700;
                   font-family: 'Outfit', sans-serif; margin: 0 0 6px 0;">Sign In</h3>
        <p style="color: #798a9f; font-size: 13px; margin: 0 0 24px 0;">
            Enter your credentials to access the portal
        </p>
    </div>
    """, unsafe_allow_html=True)

    if "login_error" not in st.session_state:
        st.session_state.login_error = ""

    username = st.text_input("Username", placeholder="Enter username", key="login_user")
    password = st.text_input("Password", type="password", placeholder="Enter password", key="login_pass")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if st.button("Sign In →", type="primary", use_container_width=True):
        if not username or not password:
            st.error("Please enter both username and password.")
        elif login(username, password):
            st.success("Login successful! Redirecting...")
            st.switch_page("pages/01_🏠_Dashboard.py")
        else:
            st.error("❌ Invalid username or password. Please try again.")

    st.markdown("""
    <div style="margin-top: 28px; padding-top: 20px;
                border-top: 1px solid rgba(31,111,235,0.1); text-align: center;">
        <p style="color: #4a5a6a; font-size: 12px; margin: 0;">
            Demo credentials: <code style="color: #58a6ff;">admin</code> /
            <code style="color: #58a6ff;">safetystock123</code>
        </p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 40px;">
    <p style="color: #2a3a4a; font-size: 12px;">
        Safety Stock Automation Portal • Enterprise Edition
    </p>
</div>
""", unsafe_allow_html=True)
