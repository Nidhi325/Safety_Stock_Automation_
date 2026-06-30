import textwrap
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import db
from utils.styles import COMMON_CSS
from utils.auth import check_auth, render_sidebar_brand

# ── Page Configuration ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Inventory Directory — Safety Stock Portal",
    page_icon="📦",
    layout="wide",
)

# ── Apply global styles, auth guard, sidebar brand ──────────────────────────
st.markdown(COMMON_CSS, unsafe_allow_html=True)
check_auth()
render_sidebar_brand()

# ── Constants ────────────────────────────────────────────────────────────────
PER_PAGE = 20

# ── Session State Initialisation ─────────────────────────────────────────────
if "dir_page" not in st.session_state:
    st.session_state.dir_page = 1

# ── Page Header ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <p class="ss-page-title">📦 Inventory Directory</p>
    <p class="ss-page-subtitle">Browse and filter all 2,553 tracked materials</p>
    """,
    unsafe_allow_html=True,
)

# ── Filter Row ───────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

with col1:
    search_val = st.text_input(
        "Search by Material ID",
        key="dir_search",
        placeholder="e.g. MAT-0042",
    )

with col2:
    abc_val = st.selectbox(
        "ABC Class",
        options=["All", "A", "B", "C"],
        key="dir_abc",
    )

with col3:
    xyz_val = st.selectbox(
        "XYZ Class",
        options=["All", "X", "Y", "Z"],
        key="dir_xyz",
    )

with col4:
    status_val = st.selectbox(
        "Status",
        options=["All", "Sufficient", "Low", "Critical"],
        key="dir_status",
    )

with col5:
    action_val = st.selectbox(
        "Action",
        options=["All", "Order Material", "No Action Required"],
        key="dir_action",
    )

# ── Resolve filter values (None when 'All') ──────────────────────────────────
search_query  = search_val.strip() if search_val and search_val.strip() else ""
abc_filter    = None if abc_val    == "All" else abc_val
xyz_filter    = None if xyz_val    == "All" else xyz_val
status_filter = None if status_val == "All" else status_val
action_filter = None if action_val == "All" else action_val

# ── Build a filter fingerprint; reset page when filters change ───────────────
filter_key = (search_query, abc_filter, xyz_filter, status_filter, action_filter)
if st.session_state.get("_dir_last_filter") != filter_key:
    st.session_state.dir_page = 1
    st.session_state["_dir_last_filter"] = filter_key

current_page = st.session_state.dir_page

# ── Fetch Data ────────────────────────────────────────────────────────────────
with st.spinner("loading..."):
    result = db.get_inventory_list(
        page=current_page,
        per_page=PER_PAGE,
        search_query=search_query,
        action_filter=action_filter,
        status_filter=status_filter,
        abc_filter=abc_filter,
        xyz_filter=xyz_filter,
    )

materials    = result.get("materials", [])
total_count  = result.get("total_count", 0)
total_pages  = result.get("total_pages", 1)

# ── Table Section ─────────────────────────────────────────────────────────────
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# Helper: map status → pill HTML
def status_pill(status_str: str) -> str:
    s = (status_str or "").strip().lower()
    if s == "sufficient":
        return f'<span class="ss-pill-sufficient">{status_str}</span>'
    elif s == "low":
        return f'<span class="ss-pill-low">{status_str}</span>'
    elif s == "critical":
        return f'<span class="ss-pill-critical">{status_str}</span>'
    else:
        return f'<span style="color:#798a9f">{status_str or "—"}</span>'

# Helper: map action → action HTML
def action_pill(action_str: str) -> str:
    a = (action_str or "").strip().lower()
    if "order" in a:
        return f'<span class="ss-action-order">{action_str}</span>'
    elif "no action" in a or "sufficient" in a:
        return f'<span class="ss-action-ok">{action_str}</span>'
    else:
        return f'<span style="color:#798a9f">{action_str or "—"}</span>'

# Helper: safe int formatting
def fmt_int(val) -> str:
    try:
        return str(int(round(float(val))))
    except (TypeError, ValueError):
        return "—"

# Helper: price formatting
def fmt_price(val) -> str:
    try:
        return f"${float(val):,.2f}"
    except (TypeError, ValueError):
        return "—"

# Build HTML table
table_rows_html = ""
for row in materials:
    mat_id     = row.get("material_id", "—")
    abc_cls    = row.get("abc_class", "—") or "—"
    xyz_cls    = row.get("xyz_class", "—") or "—"
    abc_xyz    = f"{abc_cls}/{xyz_cls}"
    stock      = fmt_int(row.get("unrestricted"))
    lead_time  = fmt_int(row.get("material_lead_time"))
    price      = fmt_price(row.get("moving_price"))
    safety_stk = fmt_int(row.get("Safety_Stock"))
    reorder_pt = fmt_int(row.get("Reorder_Point"))
    inv_status = row.get("Inventory_Status", "") or ""
    sug_action = row.get("Suggested_Action", "") or ""

    status_html = status_pill(inv_status)
    action_html = action_pill(sug_action)

    table_rows_html += f"""
        <tr>
            <td><strong style="color:#58a6ff">{mat_id}</strong></td>
            <td>
                <span style="background:rgba(31,111,235,0.12);color:#58a6ff;
                             padding:2px 10px;border-radius:6px;font-size:12px;
                             font-weight:600;border:1px solid rgba(31,111,235,0.25);">
                    {abc_xyz}
                </span>
            </td>
            <td>{stock}</td>
            <td>{lead_time} days</td>
            <td>{price}</td>
            <td>{safety_stk}</td>
            <td>{reorder_pt}</td>
            <td>{status_html}</td>
            <td>{action_html}</td>
        </tr>
    """

if not materials:
    table_rows_html = """
        <tr>
            <td colspan="9" style="text-align:center;color:#798a9f;padding:40px;">
                No materials found matching your filters.
            </td>
        </tr>
    """

table_html = f"""
<style>
.inv-table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-family: 'Inter', sans-serif;
}}
.inv-table th {{
    background: rgba(31,111,235,0.15);
    color: #58a6ff;
    padding: 10px 12px;
    text-align: left;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
.inv-table td {{
    padding: 10px 12px;
    border-bottom: 1px solid rgba(31,111,235,0.08);
    color: #e6edf3;
    font-size: 13px;
}}
.inv-table tr:hover td {{
    background: rgba(31,111,235,0.05);
}}
/* First / last column border-radius on header */
.inv-table thead tr th:first-child {{ border-radius: 10px 0 0 0; }}
.inv-table thead tr th:last-child  {{ border-radius: 0 10px 0 0; }}

/* Wrap table in a styled container */
.inv-table-wrap {{
    background: linear-gradient(135deg, #0e1729 0%, #111e38 100%);
    border: 1px solid rgba(31,111,235,0.18);
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 4px 28px rgba(0,0,0,0.4);
}}
</style>

<div class="inv-table-wrap">
<table class="inv-table">
    <thead>
        <tr>
            <th>Material ID</th>
            <th>ABC/XYZ</th>
            <th>Stock</th>
            <th>Lead Time</th>
            <th>Price</th>
            <th>Safety Stock</th>
            <th>Reorder Point</th>
            <th>Status</th>
            <th>Action</th>
        </tr>
    </thead>
    <tbody>
        {table_rows_html}
    </tbody>
</table>
</div>
"""

st.markdown("\n".join(line.strip() for line in table_html.split("\n")), unsafe_allow_html=True)

# ── Pagination Controls ───────────────────────────────────────────────────────
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

page_start = (current_page - 1) * PER_PAGE + 1 if total_count > 0 else 0
page_end   = min(current_page * PER_PAGE, total_count)

left_col, center_col, right_col = st.columns([2, 1, 2])

with left_col:
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; height:100%; padding-top:8px;">
            <p style="color:#798a9f; font-size:13px; margin:0;">
                Showing <strong style="color:#e6edf3">{page_start}–{page_end}</strong>
                of <strong style="color:#e6edf3">{total_count}</strong> materials
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with center_col:
    btn_left, btn_mid, btn_right = st.columns([1, 1.4, 1])

    with btn_left:
        prev_disabled = current_page <= 1
        if st.button(
            "◀",
            key="dir_prev_btn",
            disabled=prev_disabled,
            use_container_width=True,
        ):
            st.session_state.dir_page = max(1, current_page - 1)
            st.rerun()

    with btn_mid:
        st.markdown(
            f"""
            <div style="text-align:center; padding-top:6px;">
                <span style="color:#58a6ff; font-size:13px; font-weight:600;">
                    {current_page} / {max(1, total_pages)}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with btn_right:
        next_disabled = current_page >= total_pages or total_pages == 0
        if st.button(
            "▶",
            key="dir_next_btn",
            disabled=next_disabled,
            use_container_width=True,
        ):
            st.session_state.dir_page = min(total_pages, current_page + 1)
            st.rerun()

# ── Download Button ────────────────────────────────────────────────────────────
st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
st.markdown(
    """
    <div style="
        background: linear-gradient(135deg, #0e1729 0%, #111e38 100%);
        border: 1px solid rgba(31,111,235,0.18);
        border-radius: 14px;
        padding: 20px 24px;
        display: flex;
        align-items: center;
        gap: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    ">
        <div style="flex:1;">
            <p style="margin:0; font-size:15px; font-weight:600; color:#f0f4f9;">
                📥 Export Full Inventory Report
            </p>
            <p style="margin:4px 0 0 0; font-size:12px; color:#798a9f;">
                Download all materials with safety stock metrics as a CSV file.
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

try:
    df_download = db.get_all_predictions_df()
    csv_bytes = df_download.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Full CSV",
        data=csv_bytes,
        file_name="inventory_report.csv",
        mime="text/csv",
        use_container_width=True,
    )
except Exception as e:
    st.error(f"Could not prepare download: {e}")
