"""
01_Dashboard.py — Material Search & Analysis Dashboard
Safety Stock Automation Portal
"""

# ── Path setup ────────────────────────────────────────────────────────────────
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── Stdlib / third-party ──────────────────────────────────────────────────────
import streamlit as st

# ── Project modules ───────────────────────────────────────────────────────────
import db
from utils.styles import COMMON_CSS
from utils.auth import check_auth, render_sidebar_brand
from utils.charts import demand_chart

# ── Page config (MUST be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Dashboard — Safety Stock Portal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(COMMON_CSS, unsafe_allow_html=True)

# ── Auth guard ────────────────────────────────────────────────────────────────
check_auth()
render_sidebar_brand()

# ═════════════════════════════════════════════════════════════════════════════
# Helper functions
# ═════════════════════════════════════════════════════════════════════════════

def _lead_time_category(metrics: dict) -> str:
    """Return the lead-time category string from metrics, with a safe fallback."""
    cat = metrics.get("lead_time_category")
    if cat:
        return str(cat)
    # Derive from numeric value if the column is missing
    lt = metrics.get("material_lead_time")
    if lt is None:
        return "Unknown"
    lt = float(lt)
    if lt <= 14:
        return "Short"
    if lt <= 45:
        return "Medium"
    return "Long"


def _action_html(action: str) -> str:
    """Wrap Suggested_Action text in the appropriate colour pill."""
    if not action:
        return "<span class='ss-action-ok'>—</span>"
    if "order" in action.lower():
        return f"<span class='ss-action-order'>{action}</span>"
    return f"<span class='ss-action-ok'>{action}</span>"


def _status_html(status: str) -> str:
    """Wrap Inventory_Status text in the appropriate colour pill."""
    if not status:
        return "<span class='ss-pill-sufficient'>—</span>"
    s = status.strip().lower()
    if s == "critical":
        return f"<span class='ss-pill-critical'>{status}</span>"
    if s == "low":
        return f"<span class='ss-pill-low'>{status}</span>"
    return f"<span class='ss-pill-sufficient'>{status}</span>"


def _safe_int(val, default: int = 0) -> int:
    """Safely round-cast a possibly-None value to int."""
    try:
        return int(round(float(val)))
    except (TypeError, ValueError):
        return default


def _fmt_currency(val, default: str = "$0.00") -> str:
    """Format a numeric value as a dollar currency string."""
    try:
        return f"${float(val):,.2f}"
    except (TypeError, ValueError):
        return default


# ═════════════════════════════════════════════════════════════════════════════
# Page header
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style='padding: 8px 0 24px 0;'>
  <p class='ss-page-title'>📊 Dashboard</p>
  <p class='ss-page-subtitle'>Search a material ID to view forecasts, safety stock, and inventory recommendations</p>
</div>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# Search section
# ═════════════════════════════════════════════════════════════════════════════
col1, col2 = st.columns([3, 1])

with col1:
    material_input = st.text_input(
        label="Material ID",
        placeholder="Enter Material ID (e.g. 100345)...",
        key="dash_search",
        label_visibility="collapsed",
    )

with col2:
    analyze_clicked = st.button(
        "Analyze →",
        type="primary",
        use_container_width=True,
        key="dash_btn",
    )

# Trigger on Enter key (input changed and non-empty) OR on button click
_prev_key = "_dash_prev_input"
_input_changed = (
    material_input
    and material_input != st.session_state.get(_prev_key, "")
)
st.session_state[_prev_key] = material_input

should_fetch = analyze_clicked or _input_changed

if should_fetch and material_input.strip():
    with st.spinner("loading..."):
        result = db.get_material_details(material_input.strip())

    if result is None:
        st.error("material id not found, try again 😞")
        # Clear any previous result so welcome state shows
        st.session_state.pop("current_material", None)
    else:
        st.session_state["current_material"] = result

# ═════════════════════════════════════════════════════════════════════════════
# Welcome state — shown when no material has been loaded yet
# ═════════════════════════════════════════════════════════════════════════════
if not st.session_state.get("current_material"):
    st.markdown(
        "<div class='welcome-card'>"
        "<div class='welcome-icon'>📦</div>"
        "<h4 class='welcome-title'>No Material Selected</h4>"
        "<p class='welcome-sub'>Enter a Material ID above to view detailed inventory analysis and SES forecast</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.stop()

# ═════════════════════════════════════════════════════════════════════════════
# Results section — rendered when a material is loaded
# ═════════════════════════════════════════════════════════════════════════════
data: dict    = st.session_state["current_material"]
metrics: dict = data["metrics"]
history: list = data["history"]

# ── 5 KPI metric cards ────────────────────────────────────────────────────────
kpi_cols = st.columns(5)

# 1 — Material ID
with kpi_cols[0]:
    st.metric(
        label="Material ID",
        value=str(metrics.get("material_id", "—")),
    )

# 2 — Unrestricted Stock
unrestricted_val = _safe_int(metrics.get("unrestricted", 0))
with kpi_cols[1]:
    st.metric(
        label="Unrestricted Stock",
        value=f"{unrestricted_val:,}",
    )

# 3 — Safety Stock (with delta vs unrestricted)
safety_stock_val  = _safe_int(metrics.get("Safety_Stock", 0))
stock_delta       = unrestricted_val - safety_stock_val
delta_label       = f"{'+' if stock_delta >= 0 else ''}{stock_delta:,} vs Safety Stock"
with kpi_cols[2]:
    st.metric(
        label="Safety Stock",
        value=f"{safety_stock_val:,}",
        delta=delta_label,
    )

# 4 — Predicted Consumption (SES forecast)
forecast_val = _safe_int(metrics.get("forecast_demand", 0))
with kpi_cols[3]:
    st.metric(
        label="Predicted Consumption",
        value=f"{forecast_val:,}",
    )

# 5 — Reorder Point
reorder_val = _safe_int(metrics.get("Reorder_Point", 0))
with kpi_cols[4]:
    st.metric(
        label="Reorder Point",
        value=f"{reorder_val:,}",
    )

st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

# ── Chart + Specs two-column layout ──────────────────────────────────────────
chart_col, specs_col = st.columns([1.6, 1])

# ── Left: Demand chart ────────────────────────────────────────────────────────
with chart_col:
    fig = demand_chart(history, metrics)
    st.plotly_chart(fig, use_container_width=True, key="demand_chart")

# ── Right: Material specifications card ──────────────────────────────────────
with specs_col:
    # Derive computed values
    lead_time_num   = metrics.get("material_lead_time")
    lt_category     = _lead_time_category(metrics)
    lead_time_str   = (
        f"{_safe_int(lead_time_num)} days ({lt_category})"
        if lead_time_num is not None
        else f"— ({lt_category})"
    )

    moving_price_str  = _fmt_currency(metrics.get("moving_price"))
    abc_class_str     = str(metrics.get("abc_class", "—") or "—")
    xyz_class_str     = str(metrics.get("xyz_class", "—") or "—")
    inventory_gap_val = _safe_int(metrics.get("Inventory_Gap", 0))
    order_qty_val     = _safe_int(metrics.get("Order_Quantity", 0))
    order_cost_str    = _fmt_currency(metrics.get("Order_Cost"))
    forecast_date_str = str(metrics.get("forecast_date", "—") or "—")
    action_html       = _action_html(str(metrics.get("Suggested_Action", "") or ""))
    status_html       = _status_html(str(metrics.get("Inventory_Status", "") or ""))

    specs_card_html = f"""
<div class='ss-card'>
  <div class='ss-card-header'>📋 Material Specifications</div>
  <div class='spec-grid'>

    <div class='spec-item'>
      <span class='spec-label'>Lead Time</span>
      <span class='spec-value'>{lead_time_str}</span>
    </div>

    <div class='spec-item'>
      <span class='spec-label'>Moving Price</span>
      <span class='spec-value'>{moving_price_str}</span>
    </div>

    <div class='spec-item'>
      <span class='spec-label'>ABC Class</span>
      <span class='spec-value'>{abc_class_str}</span>
    </div>

    <div class='spec-item'>
      <span class='spec-label'>XYZ Class</span>
      <span class='spec-value'>{xyz_class_str}</span>
    </div>

    <div class='spec-item'>
      <span class='spec-label'>Inventory Gap</span>
      <span class='spec-value'>{inventory_gap_val:,}</span>
    </div>

    <div class='spec-item'>
      <span class='spec-label'>Order Quantity</span>
      <span class='spec-value'>{order_qty_val:,}</span>
    </div>

    <div class='spec-item'>
      <span class='spec-label'>Order Cost</span>
      <span class='spec-value'>{order_cost_str}</span>
    </div>

    <div class='spec-item'>
      <span class='spec-label'>Forecast Month</span>
      <span class='spec-value'>{forecast_date_str}</span>
    </div>

    <div class='spec-item'>
      <span class='spec-label'>Suggested Action</span>
      <span class='spec-value'>{action_html}</span>
    </div>

    <div class='spec-item'>
      <span class='spec-label'>Inventory Status</span>
      <span class='spec-value'>{status_html}</span>
    </div>

  </div>
</div>
"""
    st.markdown("\n".join(line.strip() for line in specs_card_html.split("\n")), unsafe_allow_html=True)
