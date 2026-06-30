import textwrap
"""
04_Executive_Analytics.py
--------------------------
Portfolio-level executive analytics for the Safety Stock Automation Portal.
Includes KPI cards, multi-chart dashboards, ABC-XYZ matrix, and smart recommendations.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import plotly.graph_objects as go
import db
from utils.styles import COMMON_CSS
from utils.auth import check_auth, render_sidebar_brand
from utils.charts import pie_chart, bar_chart, grouped_bar, COLORS, BASE_LAYOUT, AXIS_STYLE

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Executive Analytics — Safety Stock Portal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Apply theme + auth ────────────────────────────────────────────────────────
st.markdown(COMMON_CSS, unsafe_allow_html=True)
check_auth()
render_sidebar_brand()

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=120, show_spinner=False)
def load_analytics():
    return db.get_analytics_summary()

@st.cache_data(ttl=120, show_spinner=False)
def load_recommendations():
    return db.get_recommendations()

@st.cache_data(ttl=120, show_spinner=False)
def load_abc_health():
    """
    Compute per-ABC-class inventory health breakdown (Sufficient / Low / Critical).
    Returns dict keyed by status with lists [A_count, B_count, C_count].
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    result = {"Sufficient": [0, 0, 0], "Low": [0, 0, 0], "Critical": [0, 0, 0]}
    for i, cls in enumerate(["A", "B", "C"]):
        for status in ["Sufficient", "Low", "Critical"]:
            ph = "%s" if db._db_type == "MySQL" else "?"
            cursor.execute(
                f"SELECT COUNT(*) FROM predictions WHERE abc_class = {ph} AND Inventory_Status = {ph}",
                (cls, status),
            )
            row = cursor.fetchone()
            result[status][i] = (row[0] if row else 0) or 0
    conn.close()
    return result

@st.cache_data(ttl=120, show_spinner=False)
def load_lead_time_distribution():
    """
    Fetch lead_time_category distribution from predictions table.
    Returns a dict {category: count}.
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT lead_time_category, COUNT(*) FROM predictions "
        "WHERE lead_time_category IS NOT NULL AND lead_time_category != '' "
        "GROUP BY lead_time_category"
    )
    rows = cursor.fetchall()
    conn.close()
    return {str(r[0]): int(r[1]) for r in rows} if rows else {}


# ── Helper: convert **bold** markdown to HTML <strong> ───────────────────────
def md_bold_to_html(text: str) -> str:
    """Replace **word** patterns with <strong>word</strong> for HTML rendering."""
    import re
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)


# ── Helper: recommendation type → accent colour ───────────────────────────────
REC_COLORS = {
    "critical": "#ff3c50",
    "warning":  "#ffb400",
    "success":  "#00c864",
    "info":     "#58a6ff",
}


# ── Helper: matrix cell background colour based on count ─────────────────────
def _matrix_cell_bg(count: int) -> str:
    if count == 0:
        return "background: rgba(10,15,30,0.8); color: #3a4a5a;"
    elif count >= 20:
        return "background: rgba(31,111,235,0.28); color: #58a6ff;"
    elif count >= 5:
        return "background: rgba(31,111,235,0.14); color: #a0b8d8;"
    else:
        return "background: rgba(31,111,235,0.07); color: #798a9f;"


# ══════════════════════════════════════════════════════════════════════════════
#  DATA LOAD
# ══════════════════════════════════════════════════════════════════════════════
analytics = load_analytics()

if analytics is None:
    st.warning(
        "⚠️ No prediction data found in the database. "
        "Please run the pipeline and import data before viewing analytics."
    )
    st.stop()

recommendations = load_recommendations()
abc_health      = load_abc_health()
lt_dist         = load_lead_time_distribution()

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE HEADER + REFRESH BUTTON
# ══════════════════════════════════════════════════════════════════════════════
header_col, btn_col = st.columns([5, 1])
with header_col:
    st.markdown(
        "<p class='ss-page-title'>📈 Executive Analytics</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p class='ss-page-subtitle'>Portfolio-level insights, trends, and smart recommendations</p>",
        unsafe_allow_html=True,
    )
with btn_col:
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    if st.button("🔄 Refresh", key="exec_refresh_btn", type="secondary"):
        st.cache_data.clear()
        st.rerun()

st.markdown("<hr>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 1 — GLOBAL KPI CARDS
# ══════════════════════════════════════════════════════════════════════════════
total_mats  = analytics["total_materials"]
to_order    = analytics["materials_to_order"]
order_cost  = analytics["total_order_cost"]
avg_lt      = analytics["avg_lead_time"]

order_pct   = round(to_order / total_mats * 100, 1) if total_mats > 0 else 0.0

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric(
        label="📦 Total Materials Tracked",
        value=f"{total_mats:,}",
        delta=None,
    )
with k2:
    st.metric(
        label="🛒 Materials to Reorder",
        value=f"{to_order:,}",
        delta=f"{order_pct}% of portfolio",
        delta_color="inverse",
    )
with k3:
    st.metric(
        label="💵 Total Order Value",
        value=f"${order_cost:,.0f}",
        delta=None,
    )
with k4:
    st.metric(
        label="⏱️ Average Lead Time",
        value=f"{avg_lt} days",
        delta=None,
    )

st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 2 — CHART GRID (3 rows × 2 cols)
# ══════════════════════════════════════════════════════════════════════════════

# ── Row 1: Pie charts ─────────────────────────────────────────────────────────
row1_l, row1_r = st.columns([1, 1])

# --- Left: Suggested Action Distribution
with row1_l:
    sa_data    = analytics["breakdowns"].get("suggested_actions", {})
    sa_labels  = list(sa_data.keys())
    sa_values  = list(sa_data.values())
    sa_color   = {"Order Material": "#ff7800", "No Action Required": "#00c864"}

    if sa_labels and sa_values:
        fig_action = pie_chart(
            labels=sa_labels,
            values=sa_values,
            title="Suggested Action Distribution",
            color_map=sa_color,
        )
        st.plotly_chart(fig_action, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No suggested-action data available.")

# --- Right: Inventory Status Breakdown
with row1_r:
    inv_data   = analytics["breakdowns"].get("inventory_status", {})
    inv_labels = list(inv_data.keys())
    inv_values = list(inv_data.values())
    inv_color  = {"Sufficient": "#00c864", "Low": "#ffb400", "Critical": "#ff3c50"}

    if inv_labels and inv_values:
        fig_status = pie_chart(
            labels=inv_labels,
            values=inv_values,
            title="Inventory Status Breakdown",
            color_map=inv_color,
        )
        st.plotly_chart(fig_status, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No inventory-status data available.")

st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)

# ── Row 2: ABC Cost bar + ABC-XYZ Matrix table ────────────────────────────────
row2_l, row2_r = st.columns([1, 1])

# --- Left: Projected Order Cost by ABC Class (horizontal bar)
with row2_l:
    abc_costs_raw = analytics["breakdowns"].get("abc_costs", {})

    # Sort A → B → C descending by cost value
    abc_order = ["A", "B", "C"]
    abc_sorted_labels = [k for k in abc_order if k in abc_costs_raw]
    # Also include any unexpected keys (e.g. None / missing)
    for k in abc_costs_raw:
        if k not in abc_sorted_labels and k is not None:
            abc_sorted_labels.append(str(k))
    abc_sorted_values = [float(abc_costs_raw.get(k, 0) or 0) for k in abc_sorted_labels]

    if abc_sorted_labels and any(v > 0 for v in abc_sorted_values):
        fig_abc_cost = bar_chart(
            x=abc_sorted_labels,
            y=abc_sorted_values,
            title="Projected Order Cost by ABC Class",
            xaxis_title="Order Cost (USD)",
            yaxis_title="$",
            orientation="h",
        )
        st.plotly_chart(fig_abc_cost, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No ABC cost data available.")

# --- Right: ABC-XYZ Matrix Table
with row2_r:
    matrix = analytics.get("matrix", {})

    st.markdown(
        "<div class='ss-card-header'>🔢 ABC-XYZ Segmentation Matrix</div>",
        unsafe_allow_html=True,
    )

    # Build 3×3 HTML table (rows=A/B/C, cols=X/Y/Z)
    abc_rows = ["A", "B", "C"]
    xyz_cols = ["X", "Y", "Z"]

    header_cells = "".join(
        f"<th style='background:rgba(31,111,235,0.18); color:#58a6ff; "
        f"padding:11px 20px; border-radius:8px; text-align:center; "
        f"font-size:14px; font-weight:700;'>{col}</th>"
        for col in xyz_cols
    )

    rows_html = ""
    for abc in abc_rows:
        row_label = (
            f"<td style='background:rgba(14,23,41,0.9); border:1px solid rgba(31,111,235,0.18); "
            f"color:#f0f4f9; padding:12px 16px; border-radius:8px; font-weight:700; "
            f"font-size:14px; text-align:center;'>{abc}</td>"
        )
        data_cells = ""
        for xyz in xyz_cols:
            key   = f"{abc}{xyz}"
            count = int(matrix.get(key, 0))
            style = _matrix_cell_bg(count)
            data_cells += (
                f"<td style='{style} border:1px solid rgba(31,111,235,0.14); "
                f"padding:14px 18px; border-radius:8px; text-align:center; "
                f"font-size:22px; font-weight:700; font-family: Outfit, sans-serif; "
                f"transition:background 0.2s;'>{count}</td>"
            )
        rows_html += f"<tr>{row_label}{data_cells}</tr>"

    matrix_html = f"""
    <div style='overflow-x:auto; margin-top:6px;'>
        <table class='matrix-table' style='width:100%; border-collapse:separate; border-spacing:6px;'>
            <thead>
                <tr>
                    <th style='background:transparent; padding:10px; color:#4a5a6a; font-size:12px;'>ABC ↓ / XYZ →</th>
                    {header_cells}
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """
    st.markdown("\n".join(line.strip() for line in matrix_html.split("\n")), unsafe_allow_html=True)

    # Legend below matrix
    st.markdown(
        """
        <div style='margin-top:12px; display:flex; gap:18px; flex-wrap:wrap;'>
            <span style='font-size:12px; color:#798a9f;'>
                <span style='display:inline-block; width:10px; height:10px;
                    background:rgba(31,111,235,0.28); border-radius:3px; margin-right:5px;'></span>
                High volume (≥20)
            </span>
            <span style='font-size:12px; color:#798a9f;'>
                <span style='display:inline-block; width:10px; height:10px;
                    background:rgba(31,111,235,0.10); border-radius:3px; margin-right:5px;'></span>
                Medium (5–19)
            </span>
            <span style='font-size:12px; color:#798a9f;'>
                <span style='display:inline-block; width:10px; height:10px;
                    background:rgba(31,111,235,0.04); border-radius:3px; margin-right:5px;'></span>
                Low (1–4)
            </span>
            <span style='font-size:12px; color:#798a9f;'>
                <span style='display:inline-block; width:10px; height:10px;
                    background:rgba(10,15,30,0.8); border-radius:3px; margin-right:5px;'></span>
                Zero
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)

# ── Row 3: ABC Health stacked bar + Lead Time distribution pie ────────────────
row3_l, row3_r = st.columns([1, 1])

# --- Left: Inventory Health by ABC Class (stacked bar)
with row3_l:
    has_health_data = any(
        any(v > 0 for v in counts) for counts in abc_health.values()
    )
    if has_health_data:
        # Build series — order: Sufficient, Low, Critical
        series_dict = {
            "Sufficient": abc_health.get("Sufficient", [0, 0, 0]),
            "Low":        abc_health.get("Low",        [0, 0, 0]),
            "Critical":   abc_health.get("Critical",   [0, 0, 0]),
        }
        fig_health = grouped_bar(
            categories=["A", "B", "C"],
            series_dict=series_dict,
            title="Inventory Health by ABC Class",
        )
        st.plotly_chart(fig_health, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No ABC health breakdown data available. Import predictions to populate this chart.")

# --- Right: Lead Time Distribution pie
with row3_r:
    if lt_dist:
        lt_labels = list(lt_dist.keys())
        lt_values = list(lt_dist.values())

        # Colour palette for lead time categories
        lt_color_map = {
            "Short":    COLORS["success"],
            "Medium":   COLORS["warning"],
            "Long":     COLORS["danger"],
            "Very Long": "#a371f7",
        }
        # Assign fallback colours for any labels not in the map
        fallback_colors = [COLORS["primary"], COLORS["secondary"], COLORS["cyan"]]
        for i, lbl in enumerate(lt_labels):
            if lbl not in lt_color_map:
                lt_color_map[lbl] = fallback_colors[i % len(fallback_colors)]

        fig_lt = pie_chart(
            labels=lt_labels,
            values=lt_values,
            title="Lead Time Category Distribution",
            color_map=lt_color_map,
        )
        st.plotly_chart(fig_lt, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown(
            """
            <div style='background:linear-gradient(135deg,#0e1729,#111e38);
                        border:1px solid rgba(31,111,235,0.18); border-radius:14px;
                        padding:40px 28px; text-align:center; margin-top:10px;'>
                <div style='font-size:36px; margin-bottom:12px;'>📊</div>
                <p style='color:#f0f4f9; font-weight:600; margin:0 0 6px 0;
                           font-family:Outfit,sans-serif;'>
                    Lead Time Distribution Unavailable
                </p>
                <p style='color:#798a9f; font-size:13px; margin:0;'>
                    Run the inventory pipeline to populate lead-time category data.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<hr>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 3 — SMART RECOMMENDATIONS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    "<div class='ss-card-header'>💡 Smart Recommendations</div>",
    unsafe_allow_html=True,
)

if recommendations:
    # Split into two columns for a cleaner layout when there are many recs
    mid    = (len(recommendations) + 1) // 2
    left_recs  = recommendations[:mid]
    right_recs = recommendations[mid:]

    rec_l, rec_r = st.columns([1, 1])

    def _render_rec(rec: dict):
        rec_type = rec.get("type", "info")
        icon     = rec.get("icon", "ℹ️")
        title    = rec.get("title", "")
        body_raw = rec.get("body", "")
        body_html = md_bold_to_html(body_raw)
        accent   = REC_COLORS.get(rec_type, "#58a6ff")
        st.markdown(
            f"""
            <div class='rec-{rec_type}' style='margin-bottom:12px;'>
                <div style='display:flex; align-items:flex-start; gap:10px;'>
                    <span style='font-size:18px; line-height:1.4;'>{icon}</span>
                    <div>
                        <strong style='color:{accent}; font-size:14px;'>{title}</strong><br>
                        <span style='color:#c5d1e0; font-size:13px; line-height:1.6;'>{body_html}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with rec_l:
        for rec in left_recs:
            _render_rec(rec)

    with rec_r:
        for rec in right_recs:
            _render_rec(rec)

else:
    st.info("Pipeline not yet run. No recommendations available.")

# ── Footer spacer ─────────────────────────────────────────────────────────────
st.markdown("<div style='height: 40px'></div>", unsafe_allow_html=True)
