"""Shared CSS styles for the Safety Stock Automation Portal."""

COMMON_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700&display=swap');

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
.viewerBadge_container__r5tak { display: none !important; }

/* ── Global Font ── */
html, body, .stApp, .stMarkdown, .stText, button, input, select, textarea {
    font-family: 'Inter', sans-serif !important;
}

/* ── App Background ── */
.stApp {
    background: linear-gradient(160deg, #080d1a 0%, #0a0f1e 50%, #080d1a 100%);
    color: #e6edf3;
}

/* ── Main content padding ── */
.main .block-container {
    padding: 1.5rem 2rem 3rem 2rem;
    max-width: 1400px;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b1220 0%, #080e1c 100%) !important;
    border-right: 1px solid rgba(31, 111, 235, 0.18) !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 0;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown span {
    color: #798a9f;
}

/* ── Metric Cards ── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #0e1729 0%, #111e38 100%) !important;
    border: 1px solid rgba(31, 111, 235, 0.22) !important;
    border-radius: 14px !important;
    padding: 20px 24px !important;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.35), 0 0 0 0 rgba(31,111,235,0) !important;
    transition: transform 0.25s ease, box-shadow 0.25s ease !important;
}
[data-testid="metric-container"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 35px rgba(31, 111, 235, 0.18) !important;
}
[data-testid="metric-container"] label {
    color: #7a8fa8 !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.07em;
}
[data-testid="stMetricValue"] > div {
    color: #f0f4f9 !important;
    font-size: 26px !important;
    font-weight: 700 !important;
    font-family: 'Outfit', sans-serif !important;
}
[data-testid="stMetricDelta"] {
    font-size: 12px !important;
}

/* ── Primary Buttons ── */
.stButton > button[kind="primary"],
.stButton > button:not([kind="secondary"]) {
    background: linear-gradient(135deg, #1f6feb 0%, #1557c0 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 9px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 24px !important;
    transition: all 0.22s ease !important;
    box-shadow: 0 2px 12px rgba(31, 111, 235, 0.35) !important;
    letter-spacing: 0.02em;
}
.stButton > button:not([kind="secondary"]):hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 24px rgba(31, 111, 235, 0.55) !important;
    background: linear-gradient(135deg, #2a7fff 0%, #1f6feb 100%) !important;
}
.stButton > button[kind="secondary"] {
    background: rgba(31,111,235,0.08) !important;
    color: #58a6ff !important;
    border: 1px solid rgba(31,111,235,0.3) !important;
    border-radius: 9px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(31,111,235,0.18) !important;
    border-color: rgba(31,111,235,0.6) !important;
}

/* ── Text Inputs ── */
.stTextInput > div > div > input {
    background: #0b1422 !important;
    border: 1px solid rgba(31, 111, 235, 0.28) !important;
    border-radius: 9px !important;
    color: #e6edf3 !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.stTextInput > div > div > input:focus {
    border-color: #1f6feb !important;
    box-shadow: 0 0 0 3px rgba(31,111,235,0.15) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder { color: #4a5a6a !important; }

/* ── Selectboxes ── */
.stSelectbox > div > div {
    background: #0b1422 !important;
    border: 1px solid rgba(31, 111, 235, 0.28) !important;
    border-radius: 9px !important;
    color: #e6edf3 !important;
}
[data-baseweb="select"] > div { background: #0b1422 !important; }
[data-baseweb="popover"] { background: #0e1729 !important; }
[data-baseweb="menu"] { background: #0e1729 !important; border: 1px solid rgba(31,111,235,0.2) !important; }
[role="option"]:hover { background: rgba(31,111,235,0.15) !important; }

/* ── DataFrames / Tables ── */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(31,111,235,0.18) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}
.dvn-scroller { background: #0a0f1e !important; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: #1f6feb !important; }

/* ── Dividers ── */
hr { border-color: rgba(31,111,235,0.15) !important; margin: 1.5rem 0 !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(14,23,41,0.8);
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
    border-bottom: none !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 8px !important;
    color: #798a9f !important;
    font-weight: 500 !important;
    padding: 8px 18px !important;
    border-bottom: none !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(31,111,235,0.2) !important;
    color: #58a6ff !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: rgba(14,23,41,0.6) !important;
    border: 1px dashed rgba(31,111,235,0.35) !important;
    border-radius: 12px !important;
    padding: 12px !important;
    transition: border-color 0.2s, background 0.2s;
}
[data-testid="stFileUploader"]:hover {
    background: rgba(31,111,235,0.06) !important;
    border-color: rgba(31,111,235,0.6) !important;
}

/* ── Progress bar ── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #1f6feb, #00d2ff) !important;
    border-radius: 4px !important;
}

/* ── Alerts / Info boxes ── */
.stAlert { border-radius: 10px !important; border-left-width: 4px !important; }

/* ── Custom card class ── */
.ss-card {
    background: linear-gradient(135deg, #0e1729 0%, #111e38 100%);
    border: 1px solid rgba(31,111,235,0.18);
    border-radius: 14px;
    padding: 24px 28px;
    margin-bottom: 20px;
    box-shadow: 0 4px 28px rgba(0,0,0,0.4);
}
.ss-card-header {
    font-size: 16px;
    font-weight: 600;
    color: #f0f4f9;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(31,111,235,0.15);
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: 'Outfit', sans-serif;
}
.ss-page-title {
    font-size: 26px;
    font-weight: 700;
    color: #f0f4f9;
    font-family: 'Outfit', sans-serif;
    margin: 0;
    letter-spacing: -0.02em;
}
.ss-page-subtitle {
    font-size: 14px;
    color: #798a9f;
    margin: 4px 0 24px 0;
}
.ss-badge {
    background: linear-gradient(135deg, rgba(31,111,235,0.2), rgba(31,111,235,0.1));
    border: 1px solid rgba(31,111,235,0.35);
    color: #58a6ff;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.05em;
    display: inline-block;
}
.ss-pill-sufficient {
    background: rgba(0,200,100,0.12);
    color: #00c864;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    display: inline-block;
    border: 1px solid rgba(0,200,100,0.25);
}
.ss-pill-low {
    background: rgba(255,180,0,0.12);
    color: #ffb400;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    display: inline-block;
    border: 1px solid rgba(255,180,0,0.25);
}
.ss-pill-critical {
    background: rgba(255,60,80,0.12);
    color: #ff3c50;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    display: inline-block;
    border: 1px solid rgba(255,60,80,0.25);
}
.ss-action-order {
    background: rgba(255,120,0,0.12);
    color: #ff7800;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    display: inline-block;
    border: 1px solid rgba(255,120,0,0.25);
}
.ss-action-ok {
    background: rgba(0,200,100,0.12);
    color: #00c864;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    display: inline-block;
    border: 1px solid rgba(0,200,100,0.25);
}
.rec-critical {
    background: linear-gradient(135deg, rgba(255,60,80,0.09), rgba(255,60,80,0.04));
    border: 1px solid rgba(255,60,80,0.28);
    border-radius: 12px;
    padding: 16px 20px;
    margin: 10px 0;
}
.rec-warning {
    background: linear-gradient(135deg, rgba(255,180,0,0.09), rgba(255,180,0,0.04));
    border: 1px solid rgba(255,180,0,0.28);
    border-radius: 12px;
    padding: 16px 20px;
    margin: 10px 0;
}
.rec-success {
    background: linear-gradient(135deg, rgba(0,200,100,0.09), rgba(0,200,100,0.04));
    border: 1px solid rgba(0,200,100,0.28);
    border-radius: 12px;
    padding: 16px 20px;
    margin: 10px 0;
}
.rec-info {
    background: linear-gradient(135deg, rgba(31,111,235,0.09), rgba(31,111,235,0.04));
    border: 1px solid rgba(31,111,235,0.28);
    border-radius: 12px;
    padding: 16px 20px;
    margin: 10px 0;
}
.spec-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}
.spec-item {
    background: rgba(14,23,41,0.6);
    border: 1px solid rgba(31,111,235,0.12);
    border-radius: 10px;
    padding: 12px 16px;
}
.spec-label {
    font-size: 11px;
    color: #798a9f;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 600;
    display: block;
    margin-bottom: 4px;
}
.spec-value {
    font-size: 15px;
    color: #f0f4f9;
    font-weight: 600;
}
.matrix-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 6px;
    font-family: 'Inter', sans-serif;
}
.matrix-table th {
    background: rgba(31,111,235,0.15);
    color: #58a6ff;
    padding: 10px 16px;
    border-radius: 8px;
    text-align: center;
    font-size: 13px;
    font-weight: 600;
}
.matrix-table td {
    background: rgba(14,23,41,0.7);
    border: 1px solid rgba(31,111,235,0.12);
    color: #f0f4f9;
    padding: 12px 16px;
    border-radius: 8px;
    text-align: center;
    font-size: 20px;
    font-weight: 700;
    font-family: 'Outfit', sans-serif;
    transition: background 0.2s;
}
.matrix-table td:hover { background: rgba(31,111,235,0.12); }
.sidebar-brand {
    padding: 24px 16px 16px 16px;
    text-align: center;
}
.sidebar-logo {
    background: linear-gradient(135deg, #1f6feb, #0a5cc7);
    width: 52px; height: 52px; border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; font-weight: 800; color: white;
    margin: 0 auto 12px auto;
    box-shadow: 0 4px 16px rgba(31,111,235,0.4);
    font-family: 'Outfit', sans-serif;
}
.sidebar-title {
    color: #f0f4f9;
    font-size: 15px;
    font-weight: 700;
    margin: 0;
    font-family: 'Outfit', sans-serif;
}
.sidebar-sub {
    color: #798a9f;
    font-size: 11px;
    margin: 3px 0 0 0;
}
.welcome-card {
    background: linear-gradient(135deg, #0e1729, #111e38);
    border: 1px solid rgba(31,111,235,0.2);
    border-radius: 16px;
    padding: 60px 40px;
    text-align: center;
    margin-top: 20px;
}
.welcome-icon { font-size: 52px; margin-bottom: 20px; }
.welcome-title { font-size: 22px; font-weight: 700; color: #f0f4f9; font-family: 'Outfit', sans-serif; }
.welcome-sub { font-size: 14px; color: #798a9f; margin-top: 8px; }
.console-box {
    background: #050b14;
    border: 1px solid rgba(31,111,235,0.2);
    border-radius: 10px;
    padding: 16px;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    color: #58a6ff;
    max-height: 400px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
}
</style>
"""

LOGIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700&display=swap');

#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }

html, body, .stApp { font-family: 'Inter', sans-serif !important; }

.stApp {
    background: radial-gradient(ellipse at 20% 20%, rgba(31,111,235,0.08) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 80%, rgba(0,210,255,0.06) 0%, transparent 60%),
                linear-gradient(160deg, #060b16 0%, #090e1c 50%, #060b16 100%);
}

.main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

.stTextInput > div > div > input {
    background: rgba(14,23,41,0.8) !important;
    border: 1px solid rgba(31,111,235,0.3) !important;
    border-radius: 10px !important;
    color: #e6edf3 !important;
    font-size: 15px !important;
    padding: 12px 16px !important;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.stTextInput > div > div > input:focus {
    border-color: #1f6feb !important;
    box-shadow: 0 0 0 3px rgba(31,111,235,0.15) !important;
}
.stTextInput > label { color: #798a9f !important; font-size: 13px !important; font-weight: 500 !important; }
.stTextInput > div > div > input::placeholder { color: #3a4a5a !important; }

.stButton > button {
    background: linear-gradient(135deg, #1f6feb 0%, #1255be 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    padding: 14px 24px !important;
    width: 100% !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 20px rgba(31,111,235,0.4) !important;
    letter-spacing: 0.03em;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(31,111,235,0.6) !important;
    background: linear-gradient(135deg, #2a7fff 0%, #1f6feb 100%) !important;
}
</style>
"""
