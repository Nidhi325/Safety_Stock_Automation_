import textwrap
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import db
from utils.styles import COMMON_CSS
from utils.auth import check_auth, render_sidebar_brand

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Predictions Export — Safety Stock Portal",
    page_icon="📥",
    layout="wide",
)

# ── Apply global CSS, auth guard, sidebar brand ───────────────────────────────
st.markdown(COMMON_CSS, unsafe_allow_html=True)
check_auth()
render_sidebar_brand()

# ── Additional page-specific CSS ──────────────────────────────────────────────
st.markdown("""
<style>
/* ── Prediction table wrapper ── */
.pred-table-wrap {
    background: linear-gradient(135deg, #0e1729 0%, #0b1220 100%);
    border: 1px solid rgba(31, 111, 235, 0.18);
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 4px 28px rgba(0, 0, 0, 0.4);
    margin-top: 12px;
}

/* ── Table itself ── */
.pred-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
}

/* ── Table header ── */
.pred-table thead tr {
    background: rgba(31, 111, 235, 0.14);
    border-bottom: 1px solid rgba(31, 111, 235, 0.28);
}
.pred-table thead th {
    padding: 12px 14px;
    text-align: left;
    color: #58a6ff;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    white-space: nowrap;
}

/* ── Table rows ── */
.pred-table tbody tr {
    border-bottom: 1px solid rgba(31, 111, 235, 0.08);
    transition: background 0.18s ease;
}
.pred-table tbody tr:last-child {
    border-bottom: none;
}
.pred-table tbody tr:hover {
    background: rgba(31, 111, 235, 0.07);
}
.pred-table tbody td {
    padding: 10px 14px;
    color: #e6edf3;
    vertical-align: middle;
    white-space: nowrap;
}

/* ── Material ID column ── */
.pred-mat-id {
    font-family: 'Outfit', sans-serif;
    font-weight: 600;
    color: #f0f4f9;
    font-size: 13px;
}

/* ── Numeric value ── */
.pred-num {
    font-variant-numeric: tabular-nums;
    color: #c9d1d9;
}
.pred-num-blue {
    font-variant-numeric: tabular-nums;
    color: #79c0ff;
    font-weight: 600;
}

/* ── Cost value ── */
.pred-cost {
    font-variant-numeric: tabular-nums;
    color: #3fb950;
    font-weight: 600;
}

/* ── Pagination bar ── */
.pred-pagination {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 20px;
    background: rgba(11, 18, 34, 0.8);
    border-top: 1px solid rgba(31, 111, 235, 0.15);
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    border-radius: 0 0 14px 14px;
}
.pred-page-info {
    color: #798a9f;
}
.pred-page-info span {
    color: #58a6ff;
    font-weight: 600;
}

/* ── Filter strip ── */
.filter-strip {
    background: rgba(14, 23, 41, 0.7);
    border: 1px solid rgba(31, 111, 235, 0.14);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 4px;
}

/* ── Download button row overrides ── */
.stDownloadButton > button {
    background: linear-gradient(135deg, #1f6feb 0%, #1557c0 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 9px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 9px 20px !important;
    transition: all 0.22s ease !important;
    box-shadow: 0 2px 12px rgba(31, 111, 235, 0.35) !important;
    letter-spacing: 0.02em;
    width: 100%;
}
.stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 24px rgba(31, 111, 235, 0.55) !important;
    background: linear-gradient(135deg, #2a7fff 0%, #1f6feb 100%) !important;
}

/* ── Empty-state box ── */
.pred-empty {
    text-align: center;
    padding: 60px 40px;
    color: #798a9f;
    font-size: 15px;
}
.pred-empty-icon {
    font-size: 44px;
    margin-bottom: 14px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    '<p class="ss-page-title">📥 Predictions Export</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="ss-page-subtitle">'
    'Full prediction output for all 2,553 materials — searchable, filterable and downloadable'
    '</p>',
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY STRIP — 3 KPI metrics
# ─────────────────────────────────────────────────────────────────────────────
analytics = db.get_analytics_summary()

if analytics:
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Materials", f"{analytics['total_materials']:,}")
    with m2:
        st.metric("Materials to Order", f"{analytics['materials_to_order']:,}")
    with m3:
        st.metric("Total Order Value", f"${analytics['total_order_cost']:,.0f}")
else:
    st.info("No prediction data found in the database. Please run the pipeline first.")
    st.stop()

st.markdown('<hr>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE — initialise pagination and filter state
# ─────────────────────────────────────────────────────────────────────────────
if "pred_page" not in st.session_state:
    st.session_state.pred_page = 1

# ─────────────────────────────────────────────────────────────────────────────
# FILTER ROW
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="filter-strip">', unsafe_allow_html=True)
fc1, fc2, fc3, fc4, fc5 = st.columns([2, 1, 1, 1, 1])

with fc1:
    search_val = st.text_input(
        "🔍  Search Material ID",
        value=st.session_state.get("pred_search", ""),
        placeholder="e.g. 10001234",
        key="pred_search_input",
        label_visibility="collapsed",
    )

with fc2:
    abc_val = st.selectbox(
        "ABC Class",
        options=["All", "A", "B", "C"],
        index=0,
        key="pred_abc_input",
    )

with fc3:
    xyz_val = st.selectbox(
        "XYZ Class",
        options=["All", "X", "Y", "Z"],
        index=0,
        key="pred_xyz_input",
    )

with fc4:
    status_val = st.selectbox(
        "Inventory Status",
        options=["All", "Sufficient", "Low", "Critical"],
        index=0,
        key="pred_status_input",
    )

with fc5:
    action_val = st.selectbox(
        "Suggested Action",
        options=["All", "Order Material", "No Action Required"],
        index=0,
        key="pred_action_input",
    )

st.markdown('</div>', unsafe_allow_html=True)

# ── Normalise filter values (None means "no filter") ─────────────────────────
search  = search_val.strip() if search_val.strip() else None
abc     = abc_val    if abc_val    != "All" else None
xyz     = xyz_val    if xyz_val    != "All" else None
status  = status_val if status_val != "All" else None
action  = action_val if action_val != "All" else None

# ── Detect any filter change and reset to page 1 ─────────────────────────────
filter_sig = (search, abc, xyz, status, action)
if st.session_state.get("_pred_last_filter") != filter_sig:
    st.session_state.pred_page = 1
    st.session_state._pred_last_filter = filter_sig

# ─────────────────────────────────────────────────────────────────────────────
# DOWNLOAD BUTTONS ROW  (full CSV & filtered CSV)
# ─────────────────────────────────────────────────────────────────────────────
dl_col1, dl_col2, dl_spacer = st.columns([1, 1, 3])

with dl_col1:
    # Full dataset download — load once, cached implicitly by Streamlit
    @st.cache_data(show_spinner=False)
    def _load_full_df():
        return db.get_all_predictions_df()

    df_full = _load_full_df()
    csv_data = df_full.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Full CSV",
        data=csv_data,
        file_name="predictions_full.csv",
        mime="text/csv",
        use_container_width=True,
        key="dl_full_csv",
    )

with dl_col2:
    # Filtered subset download — pull all pages matching current filters
    @st.cache_data(show_spinner=False)
    def _load_filtered_df(search_f, abc_f, xyz_f, status_f, action_f):
        """Fetch all records matching current filters (no pagination limit)."""
        conn = db.get_connection()
        import sqlite3

        ph = "%s" if db._db_type == "MySQL" else "?"
        clauses, params = [], []
        if search_f:
            clauses.append(f"material_id LIKE {ph}")
            params.append(f"%{search_f}%")
        if abc_f:
            clauses.append(f"abc_class = {ph}")
            params.append(abc_f)
        if xyz_f:
            clauses.append(f"xyz_class = {ph}")
            params.append(xyz_f)
        if status_f:
            clauses.append(f"Inventory_Status = {ph}")
            params.append(status_f)
        if action_f:
            clauses.append(f"Suggested_Action = {ph}")
            params.append(action_f)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM predictions {where} ORDER BY material_id ASC"

        try:
            import pandas as _pd
            df = _pd.read_sql(sql, conn, params=params if params else None)
        except Exception:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            if db._db_type == "MySQL":
                cols = [d[0] for d in cursor.description]
                df = _pd.DataFrame([dict(zip(cols, r)) for r in rows])
            else:
                df = _pd.DataFrame([dict(r) for r in rows])
        finally:
            conn.close()
        return df

    df_filtered = _load_filtered_df(search, abc, xyz, status, action)
    csv_filtered = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Filtered CSV",
        data=csv_filtered,
        file_name="predictions_filtered.csv",
        mime="text/csv",
        use_container_width=True,
        key="dl_filtered_csv",
    )

# ─────────────────────────────────────────────────────────────────────────────
# FETCH PAGINATED DATA
# ─────────────────────────────────────────────────────────────────────────────
PER_PAGE = 25
current_page = st.session_state.pred_page

result = db.get_predictions_page(
    page=current_page,
    per_page=PER_PAGE,
    search=search,
    abc=abc,
    xyz=xyz,
    status=status,
    action=action,
)

materials   = result["materials"]
total_count = result["total_count"]
total_pages = result["total_pages"]

# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS — HTML pill rendering
# ─────────────────────────────────────────────────────────────────────────────

def _status_pill(status_str: str) -> str:
    """Return an HTML span with the appropriate ss-pill-* class."""
    s = str(status_str).strip() if status_str else ""
    if s.lower() == "sufficient":
        return f'<span class="ss-pill-sufficient">{s}</span>'
    elif s.lower() == "low":
        return f'<span class="ss-pill-low">{s}</span>'
    elif s.lower() == "critical":
        return f'<span class="ss-pill-critical">{s}</span>'
    else:
        return f'<span style="color:#798a9f;">{s if s else "—"}</span>'


def _action_pill(action_str: str) -> str:
    """Return an HTML span with the appropriate ss-action-* class."""
    a = str(action_str).strip() if action_str else ""
    if a.lower() == "order material":
        return f'<span class="ss-action-order">{a}</span>'
    elif a.lower() in ("no action required", "no action"):
        return f'<span class="ss-action-ok">{a}</span>'
    else:
        return f'<span style="color:#798a9f;">{a if a else "—"}</span>'


def _class_badge(cls_str: str) -> str:
    """Return an HTML span with the ss-badge class for ABC/XYZ."""
    c = str(cls_str).strip() if cls_str else ""
    return f'<span class="ss-badge">{c}</span>' if c else '<span style="color:#798a9f;">—</span>'


def _fmt_int(val) -> str:
    """Format a numeric value as a rounded integer string."""
    try:
        return f"{int(round(float(val))):,}"
    except (TypeError, ValueError):
        return "—"


def _fmt_cost(val) -> str:
    """Format a numeric value as a dollar cost string."""
    try:
        return f"${int(round(float(val))):,}"
    except (TypeError, ValueError):
        return "—"


def _safe_str(val) -> str:
    """Return value as string, or em-dash if None/empty."""
    if val is None:
        return "—"
    s = str(val).strip()
    return s if s else "—"

# ─────────────────────────────────────────────────────────────────────────────
# DATA TABLE — styled HTML
# ─────────────────────────────────────────────────────────────────────────────

# Page-info row above table
row_start = (current_page - 1) * PER_PAGE + 1
row_end   = min(current_page * PER_PAGE, total_count)

st.markdown(
    f"""
    <div style="display:flex; align-items:center; justify-content:space-between;
                margin-bottom: 4px; padding: 0 2px;">
        <div style="font-size:13px; color:#798a9f;">
            Showing <span style="color:#58a6ff; font-weight:600;">{row_start:,}–{row_end:,}</span>
            of <span style="color:#58a6ff; font-weight:600;">{total_count:,}</span> records
        </div>
        <div style="font-size:12px; color:#4a5a6a;">
            Page {current_page} of {total_pages}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not materials:
    st.markdown(
        """
        <div class="pred-table-wrap">
            <div class="pred-empty">
                <div class="pred-empty-icon">🔍</div>
                <div>No records match your current filters.</div>
                <div style="margin-top:8px; font-size:13px; color:#4a5a6a;">
                    Try adjusting the search term or clearing a filter.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    # Build table rows HTML
    rows_html = ""
    for mat in materials:
        mat_id         = _safe_str(mat.get("material_id"))
        forecast_month = _safe_str(mat.get("forecast_date"))
        pred_demand    = _fmt_int(mat.get("forecast_demand"))
        safety_stock   = _fmt_int(mat.get("Safety_Stock"))
        reorder_point  = _fmt_int(mat.get("Reorder_Point"))
        current_stock  = _fmt_int(mat.get("unrestricted"))
        order_qty      = _fmt_int(mat.get("Order_Quantity"))
        order_cost     = _fmt_cost(mat.get("Order_Cost"))
        abc_cls        = _class_badge(mat.get("abc_class"))
        xyz_cls        = _class_badge(mat.get("xyz_class"))
        inv_status     = _status_pill(mat.get("Inventory_Status"))
        sug_action     = _action_pill(mat.get("Suggested_Action"))

        rows_html += f"""
        <tr>
            <td><span class="pred-mat-id">{mat_id}</span></td>
            <td><span class="pred-num">{forecast_month}</span></td>
            <td><span class="pred-num">{pred_demand}</span></td>
            <td><span class="pred-num-blue">{safety_stock}</span></td>
            <td><span class="pred-num">{reorder_point}</span></td>
            <td><span class="pred-num">{current_stock}</span></td>
            <td><span class="pred-num">{order_qty}</span></td>
            <td><span class="pred-cost">{order_cost}</span></td>
            <td>{abc_cls}</td>
            <td>{xyz_cls}</td>
            <td>{inv_status}</td>
            <td>{sug_action}</td>
        </tr>"""

    table_html = f"""
    <div class="pred-table-wrap">
        <div style="overflow-x: auto;">
            <table class="pred-table">
                <thead>
                    <tr>
                        <th>Material ID</th>
                        <th>Forecast Month</th>
                        <th>Predicted Demand</th>
                        <th>Safety Stock</th>
                        <th>Reorder Point</th>
                        <th>Current Stock</th>
                        <th>Order Qty</th>
                        <th>Order Cost</th>
                        <th>ABC</th>
                        <th>XYZ</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
    </div>
    """
    st.markdown(textwrap.dedent(table_html), unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGINATION CONTROLS
# ─────────────────────────────────────────────────────────────────────────────
if total_pages > 1:
    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)

    pg_cols = st.columns([1, 1, 2, 1, 1])

    # First page
    with pg_cols[0]:
        if st.button(
            "⏮ First",
            key="pred_pg_first",
            disabled=(current_page <= 1),
            use_container_width=True,
        ):
            st.session_state.pred_page = 1
            st.rerun()

    # Previous page
    with pg_cols[1]:
        if st.button(
            "◀ Prev",
            key="pred_pg_prev",
            disabled=(current_page <= 1),
            use_container_width=True,
        ):
            st.session_state.pred_page = max(1, current_page - 1)
            st.rerun()

    # Page indicator (centre)
    with pg_cols[2]:
        st.markdown(
            f"""
            <div style="text-align:center; padding: 8px 0;
                        font-size:14px; color:#798a9f; font-family:'Inter',sans-serif;">
                Page&nbsp;
                <span style="color:#58a6ff; font-weight:700; font-size:15px;">{current_page}</span>
                &nbsp;/&nbsp;
                <span style="color:#f0f4f9; font-weight:600;">{total_pages}</span>
                &nbsp;&nbsp;·&nbsp;&nbsp;
                <span style="color:#4a5a6a; font-size:12px;">{total_count:,} total records</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Next page
    with pg_cols[3]:
        if st.button(
            "Next ▶",
            key="pred_pg_next",
            disabled=(current_page >= total_pages),
            use_container_width=True,
        ):
            st.session_state.pred_page = min(total_pages, current_page + 1)
            st.rerun()

    # Last page
    with pg_cols[4]:
        if st.button(
            "Last ⏭",
            key="pred_pg_last",
            disabled=(current_page >= total_pages),
            use_container_width=True,
        ):
            st.session_state.pred_page = total_pages
            st.rerun()

    # Jump-to-page widget
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    jump_col, _, _ = st.columns([1, 2, 2])
    with jump_col:
        jump_page = st.number_input(
            "Jump to page",
            min_value=1,
            max_value=total_pages,
            value=current_page,
            step=1,
            key="pred_jump_input",
            label_visibility="visible",
        )
        if st.button("Go", key="pred_jump_btn", use_container_width=True):
            if 1 <= jump_page <= total_pages:
                st.session_state.pred_page = int(jump_page)
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER NOTE
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
st.markdown(
    """
    <div style="text-align:center; padding: 14px 0; font-size:12px; color:#3a4a5a;
                font-family:'Inter', sans-serif; border-top: 1px solid rgba(31,111,235,0.10);
                margin-top: 8px;">
        📥 Safety Stock Automation Portal &nbsp;·&nbsp; Predictions Export &nbsp;·&nbsp;
        Data sourced from live predictions database &nbsp;·&nbsp;
        All quantities rounded to nearest integer
    </div>
    """,
    unsafe_allow_html=True,
)
