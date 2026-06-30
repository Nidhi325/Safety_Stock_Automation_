"""Authentication helpers for the Safety Stock Portal."""
import streamlit as st

VALID_USERS = {
    "admin": "safetystock123",
    "user": "stockadmin@2024",
}

def check_auth():
    """Check if user is authenticated. If not, redirect to login."""
    if not st.session_state.get("authenticated", False):
        st.markdown("""
        <div style="text-align:center; padding: 80px 40px;">
            <div style="font-size: 48px; margin-bottom: 20px;">🔐</div>
            <h2 style="color: #f0f4f9; font-family: 'Outfit', sans-serif;">Session Expired</h2>
            <p style="color: #798a9f; font-size: 14px;">Please log in to continue.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Login →", type="primary"):
            st.switch_page("streamlit_app.py")
        st.stop()
    else:
        # Force sidebar to be displayed (overriding login screen display:none)
        st.markdown("""
        <style>
            [data-testid="collapsedControl"] {
                display: block !important;
            }
            section[data-testid="stSidebar"] {
                display: block !important;
            }
        </style>
        """, unsafe_allow_html=True)

def render_sidebar_brand():
    """Render the sidebar branding and logout button."""
    with st.sidebar:
        username = st.session_state.get("username", "Admin")
        st.markdown(f"""
        <div class="sidebar-brand">
            <div class="sidebar-logo">SS</div>
            <p class="sidebar-title">Safety Stock</p>
            <p class="sidebar-sub">Automation Portal</p>
        </div>
        <hr style="border-color: rgba(31,111,235,0.18); margin: 0 0 12px 0;">
        <div style="padding: 0 16px 8px;">
            <p style="color:#798a9f; font-size:12px; margin:0 0 6px 0; text-transform:uppercase; letter-spacing:0.06em; font-weight:600;">Logged in as</p>
            <p style="color:#58a6ff; font-size:14px; font-weight:600; margin:0;">👤 {username}</p>
        </div>
        <hr style="border-color: rgba(31,111,235,0.12); margin: 12px 0;">
        """, unsafe_allow_html=True)

        st.markdown("<div style='padding: 0 8px;'>", unsafe_allow_html=True)
        if st.button("🚪 Logout", key="sidebar_logout_btn", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.switch_page("streamlit_app.py")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color: rgba(31,111,235,0.12); margin: 12px 0;'>", unsafe_allow_html=True)

def login(username: str, password: str) -> bool:
    """Validate credentials and set session state."""
    if username in VALID_USERS and VALID_USERS[username] == password:
        st.session_state.authenticated = True
        st.session_state.username = username
        return True
    return False
