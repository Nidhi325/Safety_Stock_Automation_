import textwrap
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import db
from utils.styles import COMMON_CSS
from utils.auth import check_auth, render_sidebar_brand
from utils.charts import BASE_LAYOUT, AXIS_STYLE, COLORS

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Historical Data — Safety Stock Portal",
    page_icon="📋",
    layout="wide",
)

# ── Apply shared CSS & authentication ────────────────────────────────────────
st.markdown(COMMON_CSS, unsafe_allow_html=True)
check_auth()
render_sidebar_brand()

# ── Extra page-level CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Inventory / Historical table ── */
.inv-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    border: 1px solid rgba(31,111,235,0.18);
    border-radius: 12px;
    overflow: hidden;
}
.inv-table thead tr {
    background: linear-gradient(90deg, rgba(31,111,235,0.20) 0%, rgba(31,111,235,0.10) 100%);
}
.inv-table th {
    color: #58a6ff;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 13px 16px;
    text-align: left;
    border-bottom: 1px solid rgba(31,111,235,0.18);
    white-space: nowrap;
}
.inv-table tbody tr {
    background: rgba(10,15,30,0.55);
    transition: background 0.18s ease;
}
.inv-table tbody tr:nth-child(even) {
    background: rgba(14,23,41,0.70);
}
.inv-table tbody tr:hover {
    background: rgba(31,111,235,0.10);
}
.inv-table td {
    padding: 11px 16px;
    color: #d0dae6;
    border-bottom: 1px solid rgba(31,111,235,0.08);
    vertical-align: middle;
    white-space: nowrap;
}
.inv-table td.mat-id {
    font-weight: 600;
    color: #58a6ff;
    font-family: 'Outfit', sans-serif;
    font-size: 13.5px;
}
.inv-table td.price-cell {
    font-variant-numeric: tabular-nums;
    color: #a0e0b0;
    font-weight: 500;
}
.inv-table td.demand-cell {
    font-variant-numeric: tabular-nums;
    font-weight: 500;
}

/* ── ABC / XYZ badge variants ── */
.ss-badge-A {
    background: linear-gradient(135deg, rgba(31,111,235,0.22), rgba(31,111,235,0.10));
    border: 1px solid rgba(31,111,235,0.40);
    color: #58a6ff;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.05em;
    display: inline-block;
}
.ss-badge-B {
    background: linear-gradient(135deg, rgba(88,166,255,0.18), rgba(88,166,255,0.08));
    border: 1px solid rgba(88,166,255,0.35);
    color: #79b8ff;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.05em;
    display: inline-block;
}
.ss-badge-C {
    background: linear-gradient(135deg, rgba(0,210,255,0.15), rgba(0,210,255,0.07));
    border: 1px solid rgba(0,210,255,0.30);
    color: #00d2ff;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.05em;
    display: inline-block;
}
.ss-badge-X {
    background: linear-gradient(135deg, rgba(0,200,100,0.15), rgba(0,200,100,0.07));
    border: 1px solid rgba(0,200,100,0.30);
    color: #00c864;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.05em;
    display: inline-block;
}
.ss-badge-Y {
    background: linear-gradient(135deg, rgba(255,180,0,0.15), rgba(255,180,0,0.07));
    border: 1px solid rgba(255,180,0,0.30);
    color: #ffb400;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.05em;
    display: inline-block;
}
.ss-badge-Z {
    background: linear-gradient(135deg, rgba(255,60,80,0.15), rgba(255,60,80,0.07));
    border: 1px solid rgba(255,60,80,0.28);
    color: #ff3c50;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.05em;
    display: inline-block;
}
.ss-badge-na {
    background: rgba(80,90,110,0.18);
    border: 1px solid rgba(80,90,110,0.30);
    color: #798a9f;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    display: inline-block;
}

/* ── Pagination controls ── */
.pagination-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 18px;
    padding: 10px 16px;
    background: rgba(14,23,41,0.60);
    border: 1px solid rgba(31,111,235,0.14);
    border-radius: 10px;
}
.pagination-info {
    color: #798a9f;
    font-size: 12px;
}
.pagination-info span {
    color: #58a6ff;
    font-weight: 600;
}

/* ── Sparkline container ── */
.sparkline-card {
    background: linear-gradient(135deg, #0e1729 0%, #111e38 100%);
    border: 1px solid rgba(31,111,235,0.20);
    border-radius: 12px;
    padding: 16px 20px 6px 20px;
    margin-bottom: 18px;
}
.sparkline-title {
    font-size: 13px;
    font-weight: 600;
    color: #58a6ff;
    font-family: 'Outfit', sans-serif;
    margin-bottom: 4px;
}

/* ── Download button ── */
[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg, rgba(31,111,235,0.18), rgba(31,111,235,0.08)) !important;
    border: 1px solid rgba(31,111,235,0.40) !important;
    color: #58a6ff !important;
    border-radius: 9px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    transition: all 0.22s ease !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: linear-gradient(135deg, rgba(31,111,235,0.30), rgba(31,111,235,0.15)) !important;
    border-color: rgba(31,111,235,0.65) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 18px rgba(31,111,235,0.28) !important;
}

/* ── Section divider label ── */
.section-label {
    font-size: 12px;
    font-weight: 700;
    color: #798a9f;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    '<p class="ss-page-title">📋 Historical Data</p>'
    '<p class="ss-page-subtitle">Browse 94,000+ monthly demand records across all tracked materials</p>',
    unsafe_allow_html=True,
)

# ── Summary stats ─────────────────────────────────────────────────────────────
# We use hardcoded approximations here; a live query is left as a comment below.
# summary = db.get_analytics_summary()  # could pull total_materials for materials count
TOTAL_RECORDS     = 94_461
UNIQUE_MATERIALS  = 2_553
DATE_RANGE        = "2020-10-01 → 2023-10-01"

col_r1, col_r2, col_r3 = st.columns(3)
with col_r1:
    st.metric("📦 Total Records", f"{TOTAL_RECORDS:,}")
with col_r2:
    st.metric("🔢 Unique Materials", f"{UNIQUE_MATERIALS:,}")
with col_r3:
    st.metric("📅 Date Range", DATE_RANGE)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Filters + Download (two-column layout) ────────────────────────────────────
col_filters, col_download = st.columns([3, 1], gap="large")

with col_filters:
    st.markdown('<p class="section-label">🔍 Filter Records</p>', unsafe_allow_html=True)
    fc1, fc2, fc3, fc4 = st.columns([2, 1, 1, 1])
    with fc1:
        search = st.text_input(
            "Material ID",
            placeholder="e.g. MAT-0042",
            key="hist_search",
            label_visibility="collapsed",
        )
        st.caption("Search by Material ID")
    with fc2:
        year = st.selectbox(
            "Year",
            options=["All", "2020", "2021", "2022", "2023"],
            key="hist_year",
        )
    with fc3:
        abc = st.selectbox(
            "ABC Class",
            options=["All", "A", "B", "C"],
            key="hist_abc",
        )
    with fc4:
        xyz = st.selectbox(
            "XYZ Class",
            options=["All", "X", "Y", "Z"],
            key="hist_xyz",
        )

with col_download:
    st.markdown('<p class="section-label">⬇️ Export Data</p>', unsafe_allow_html=True)
    with st.spinner("loading..."):
        df_hist = db.get_all_historical_df()
    csv_hist = df_hist.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Historical Data CSV",
        data=csv_hist,
        file_name="historical_data.csv",
        mime="text/csv",
        use_container_width=True,
        key="dl_hist",
    )
    st.caption(f"Exporting {len(df_hist):,} total rows")

st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

# ── Material demand sparkline (shown only when a material ID is searched) ─────
search_stripped = search.strip() if search else ""

if search_stripped:
    mat_result = db.get_material_details(search_stripped)
    if mat_result and mat_result.get("history"):
        history = mat_result["history"]
        dates   = [h["Date"] for h in history]
        demands = [h["Demand"] for h in history]

        fig_spark = go.Figure()
        fig_spark.add_trace(go.Scatter(
            x=dates,
            y=demands,
            mode="lines+markers",
            name="Demand",
            line=dict(color="#1f6feb", width=2.0, shape="spline", smoothing=0.6),
            marker=dict(
                color="#1f6feb",
                size=4,
                line=dict(color="#0a0f1e", width=1),
            ),
            fill="tozeroy",
            fillcolor="rgba(31,111,235,0.07)",
            hovertemplate="<b>%{x}</b><br>Demand: %{y:,.2f}<extra></extra>",
        ))

        spark_layout = BASE_LAYOUT.copy()
        spark_layout.update(dict(
            title=dict(
                text=f"Demand History — Material <b>{search_stripped}</b>",
                font=dict(color="#f0f4f9", size=14, family="Outfit"),
                x=0.01,
            ),
            xaxis=dict(
                **AXIS_STYLE,
                title="",
                showgrid=False,
                tickangle=-30,
            ),
            yaxis=dict(
                **AXIS_STYLE,
                title="Demand Qty",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(14,23,41,0.25)",
            height=200,
            margin=dict(l=10, r=10, t=44, b=10),
            hovermode="x unified",
            showlegend=False,
        ))
        fig_spark.update_layout(**spark_layout)

        st.markdown('<div class="sparkline-card">', unsafe_allow_html=True)
        st.plotly_chart(fig_spark, use_container_width=True, key="hist_spark")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info(
            f"No demand history found for material **{search_stripped}**. "
            "The table below will still show any matching records.",
            icon="ℹ️",
        )

# ── Pagination state helpers ──────────────────────────────────────────────────
def _reset_page():
    """Reset to page 1 whenever any filter changes."""
    st.session_state["hist_page"] = 1

# Reset page to 1 when filters change.  We track a "filter snapshot" key.
_current_filter_key = f"{search_stripped}|{year}|{abc}|{xyz}"
if st.session_state.get("_hist_filter_snapshot") != _current_filter_key:
    st.session_state["_hist_filter_snapshot"] = _current_filter_key
    st.session_state["hist_page"] = 1

current_page = int(st.session_state.get("hist_page", 1))

# ── Fetch paginated historical records ────────────────────────────────────────
result = db.get_historical_page(
    page=current_page,
    per_page=25,
    search=search_stripped,
    year=None if year == "All" else year,
    abc=None if abc == "All" else abc,
    xyz=None if xyz == "All" else xyz,
)

records     = result.get("records", [])
total_count = result.get("total_count", 0)
total_pages = result.get("total_pages", 1)
per_page    = result.get("per_page", 25)

# ── Helper: render a class badge ─────────────────────────────────────────────
def _badge(value: str, prefix: str = "") -> str:
    """Return an HTML badge span for an ABC or XYZ class value."""
    v = str(value).strip().upper() if value else ""
    if v in ("A", "B", "C", "X", "Y", "Z"):
        return f'<span class="ss-badge-{v}">{v}</span>'
    return '<span class="ss-badge-na">—</span>'


# ── Build HTML table ──────────────────────────────────────────────────────────
st.markdown('<p class="section-label" style="margin-top:4px;">📊 Historical Demand Records</p>', unsafe_allow_html=True)

if records:
    row_offset = (current_page - 1) * per_page

    table_rows_html = ""
    for idx, rec in enumerate(records, start=row_offset + 1):
        mat_id    = rec.get("material_id", "—")
        date_val  = rec.get("Date", "—")
        demand    = rec.get("Demand")
        abc_cls   = rec.get("abc_class", "")
        xyz_cls   = rec.get("xyz_class", "")
        mov_price = rec.get("moving_price")

        # Format numeric fields
        demand_fmt    = f"{float(demand):,.2f}"    if demand    is not None else "—"
        mov_price_fmt = f"${float(mov_price):,.2f}" if mov_price is not None else "—"

        # Format date  (strip time portion if present)
        date_str = str(date_val).split(" ")[0] if date_val and date_val != "—" else "—"

        # Build badges
        abc_html = _badge(abc_cls)
        xyz_html = _badge(xyz_cls)

        table_rows_html += f"""
        <tr>
            <td style="color:#798a9f; font-size:11px; width:40px;">{idx}</td>
            <td class="mat-id">{mat_id}</td>
            <td style="color:#c5d1e0;">{date_str}</td>
            <td class="demand-cell">{demand_fmt}</td>
            <td style="text-align:center;">{abc_html}</td>
            <td style="text-align:center;">{xyz_html}</td>
            <td class="price-cell">{mov_price_fmt}</td>
        </tr>
        """

    table_html = f"""
    <div style="overflow-x: auto; border-radius: 12px;">
        <table class="inv-table">
            <thead>
                <tr>
                    <th style="width:40px;">#</th>
                    <th>Material ID</th>
                    <th>Date</th>
                    <th>Demand</th>
                    <th style="text-align:center;">ABC Class</th>
                    <th style="text-align:center;">XYZ Class</th>
                    <th>Moving Price</th>
                </tr>
            </thead>
            <tbody>
                {table_rows_html}
            </tbody>
        </table>
    </div>
    """
    st.markdown("\n".join(line.strip() for line in table_html.split("\n")), unsafe_allow_html=True)

    # ── Pagination controls ───────────────────────────────────────────────────
    start_rec = row_offset + 1
    end_rec   = min(row_offset + per_page, total_count)

    pg_info_html = f"""
    <div class="pagination-bar">
        <span class="pagination-info">
            Showing <span>{start_rec:,}–{end_rec:,}</span> of <span>{total_count:,}</span> records
            &nbsp;|&nbsp; Page <span>{current_page}</span> of <span>{total_pages}</span>
        </span>
    </div>
    """
    st.markdown(pg_info_html, unsafe_allow_html=True)

    # Pagination buttons
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    btn_cols = st.columns([1, 1, 4, 1, 1])

    with btn_cols[0]:
        if st.button("⏮ First", key="hist_first", use_container_width=True,
                     disabled=(current_page <= 1)):
            st.session_state["hist_page"] = 1
            st.rerun()

    with btn_cols[1]:
        if st.button("◀ Prev", key="hist_prev", use_container_width=True,
                     disabled=(current_page <= 1)):
            st.session_state["hist_page"] = current_page - 1
            st.rerun()

    with btn_cols[2]:
        # Jump-to-page input
        jump_page = st.number_input(
            "Go to page",
            min_value=1,
            max_value=max(1, total_pages),
            value=current_page,
            step=1,
            key="hist_jump_page",
            label_visibility="collapsed",
        )
        if jump_page != current_page:
            st.session_state["hist_page"] = int(jump_page)
            st.rerun()

    with btn_cols[3]:
        if st.button("Next ▶", key="hist_next", use_container_width=True,
                     disabled=(current_page >= total_pages)):
            st.session_state["hist_page"] = current_page + 1
            st.rerun()

    with btn_cols[4]:
        if st.button("Last ⏭", key="hist_last", use_container_width=True,
                     disabled=(current_page >= total_pages)):
            st.session_state["hist_page"] = total_pages
            st.rerun()

else:
    # ── Empty state ───────────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        text-align: center;
        padding: 60px 40px;
        background: linear-gradient(135deg, #0e1729, #111e38);
        border: 1px solid rgba(31,111,235,0.18);
        border-radius: 14px;
        margin-top: 16px;
    ">
        <div style="font-size: 48px; margin-bottom: 16px;">🔍</div>
        <p style="color: #f0f4f9; font-size: 18px; font-weight: 600; margin: 0; font-family: 'Outfit', sans-serif;">
            No records found
        </p>
        <p style="color: #798a9f; font-size: 14px; margin: 8px 0 0 0;">
            Try adjusting the filters above to find matching demand records.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ── Footer spacer ─────────────────────────────────────────────────────────────
st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
