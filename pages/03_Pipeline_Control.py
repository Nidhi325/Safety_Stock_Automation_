"""
03_Pipeline_Control.py
======================
Safety Stock Automation Portal — Pipeline Control Page.

Allows authorised users to:
  • Upload new monthly Consumption and LeadTime Excel files
  • Run the full 5-stage automation pipeline in a background thread
  • Watch live streamed logs in a console-style widget
  • See per-stage status indicators and a progress bar
  • Automatically refresh the SQLite/MySQL database once the pipeline finishes
"""

import sys
import threading
import time
import queue
import datetime
from pathlib import Path

# ── Make project root importable ──────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import db
from utils.styles import COMMON_CSS
from utils.auth import check_auth, render_sidebar_brand

# ── Import pipeline helpers ────────────────────────────────────────────────────
# PIPELINE_STAGES is a list of dicts: [{"label": str, "script": Path}, ...]
from python_script.run_pipeline import run_pipeline, PIPELINE_STAGES as _RAW_STAGES

# ── Normalise stage labels into a plain list ───────────────────────────────────
STAGE_LABELS = [s["label"] for s in _RAW_STAGES]
NUM_STAGES   = len(STAGE_LABELS)

# ── Project paths ──────────────────────────────────────────────────────────────
PROJECT_ROOT      = Path(__file__).resolve().parent.parent
MONTHLY_UPLOAD_DIR = PROJECT_ROOT / "Monthly_upload"

# ── Status constants ──────────────────────────────────────────────────────────
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_DONE    = "done"
STATUS_FAILED  = "failed"

STATUS_ICON = {
    STATUS_PENDING: "⏳",
    STATUS_RUNNING: "🔄",
    STATUS_DONE   : "✅",
    STATUS_FAILED : "❌",
}

STATUS_COLOR = {
    STATUS_PENDING: "#798a9f",
    STATUS_RUNNING: "#f0a500",
    STATUS_DONE   : "#00c864",
    STATUS_FAILED : "#ff3c50",
}

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Pipeline Control — Safety Stock Portal",
    page_icon="⚙️",
    layout="wide",
)

# ── Apply styles, auth, and sidebar ───────────────────────────────────────────
st.markdown(COMMON_CSS, unsafe_allow_html=True)
check_auth()
render_sidebar_brand()

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALISATION
# ═══════════════════════════════════════════════════════════════════════════════
def _init_state() -> None:
    """Set default session-state keys if they do not yet exist."""
    defaults = {
        "pipeline_running"      : False,
        "pipeline_logs"         : [],          # list of str — accumulated log lines
        "pipeline_stages_status": [STATUS_PENDING] * NUM_STAGES,
        "pipeline_done"         : False,
        "pipeline_success"      : None,        # True | False | None (not run)
        "pipeline_result_msg"   : "",
        "pipeline_log_queue"    : None,        # queue.Queue — live channel
        "pipeline_last_run"     : None,        # datetime of last completed run
        "pipeline_rerun_guard"  : False,       # prevents spurious reruns after done
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ═══════════════════════════════════════════════════════════════════════════════
# BACKGROUND THREAD FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════
def _run_pipeline_bg(
    consumption_path: Path,
    leadtime_path   : Path,
    log_q           : queue.Queue,
) -> None:
    """
    Execute run_pipeline() in a daemon thread.

    Results are communicated back exclusively through log_q:
      ('LOG',        line_str)  — a text log line
      ('STAGE_START', idx)      — stage idx has started
      ('STAGE_DONE',  idx)      — stage idx completed successfully
      ('STAGE_FAIL',  idx)      — stage idx failed
      ('DONE',        msg)      — pipeline succeeded overall
      ('FAIL',        msg)      — pipeline failed overall
    """
    _root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(_root / "python_script"))

    from run_pipeline import run_pipeline as rp  # local import inside thread

    try:
        success, msg = rp(str(consumption_path), str(leadtime_path), log_q)
        if success:
            log_q.put(("DONE", msg))
        else:
            log_q.put(("FAIL", msg))
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        log_q.put(("LOG",  f"[FATAL] Unexpected error:\n{tb}\n"))
        log_q.put(("FAIL", f"Unexpected error: {exc}"))


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: drain the queue into session-state (called on every rerun)
# ═══════════════════════════════════════════════════════════════════════════════
def _drain_queue() -> bool:
    """
    Drain all pending messages from the log queue and update session state.

    Returns True if the pipeline has finished (DONE or FAIL received).
    """
    q = st.session_state.get("pipeline_log_queue")
    if q is None:
        return False

    finished = False
    while True:
        try:
            msg_type, payload = q.get_nowait()
        except queue.Empty:
            break

        if msg_type == "LOG":
            st.session_state.pipeline_logs.append(payload)

        elif msg_type == "STAGE_START":
            idx = int(payload)
            if 0 <= idx < NUM_STAGES:
                st.session_state.pipeline_stages_status[idx] = STATUS_RUNNING

        elif msg_type == "STAGE_DONE":
            idx = int(payload)
            if 0 <= idx < NUM_STAGES:
                st.session_state.pipeline_stages_status[idx] = STATUS_DONE

        elif msg_type == "STAGE_FAIL":
            idx = int(payload)
            if 0 <= idx < NUM_STAGES:
                st.session_state.pipeline_stages_status[idx] = STATUS_FAILED

        elif msg_type == "DONE":
            st.session_state.pipeline_success    = True
            st.session_state.pipeline_result_msg = str(payload)
            finished = True

        elif msg_type == "FAIL":
            st.session_state.pipeline_success    = False
            st.session_state.pipeline_result_msg = str(payload)
            finished = True

    return finished


# ═══════════════════════════════════════════════════════════════════════════════
# DRAIN QUEUE ON EVERY RERUN (while pipeline is active)
# ═══════════════════════════════════════════════════════════════════════════════
pipeline_just_finished = False
if st.session_state.pipeline_running and not st.session_state.pipeline_done:
    pipeline_just_finished = _drain_queue()
    if pipeline_just_finished:
        st.session_state.pipeline_running = False
        st.session_state.pipeline_done    = True
        st.session_state.pipeline_last_run = datetime.datetime.now()

        # ── Refresh database from newly generated CSVs ─────────────────────────
        prediction_csv = PROJECT_ROOT / "Client_deliverable" / "Prediction.csv"
        historical_csv = PROJECT_ROOT / "Data_SES"           / "historical_data.csv"

        if prediction_csv.exists():
            try:
                db.import_predictions_csv(str(prediction_csv))
            except Exception as _e:
                st.session_state.pipeline_logs.append(
                    f"[DB] Warning — could not import Prediction.csv: {_e}\n"
                )

        if historical_csv.exists():
            try:
                db.import_historical_csv(str(historical_csv))
            except Exception as _e:
                st.session_state.pipeline_logs.append(
                    f"[DB] Warning — could not import historical_data.csv: {_e}\n"
                )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE HEADER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(
    '<p class="ss-page-title">⚙️ Pipeline Control</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="ss-page-subtitle">'
    "Upload new monthly data and run the full automation pipeline"
    "</p>",
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════════════
# TWO-COLUMN LAYOUT  [1 : 1.2]
# ═══════════════════════════════════════════════════════════════════════════════
left_col, right_col = st.columns([1, 1.2], gap="large")

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  LEFT COLUMN — Upload + Run controls + Stage indicators                  ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
with left_col:

    # ── Upload card ────────────────────────────────────────────────────────────
    st.markdown('<div class="ss-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="ss-card-header">📤 Upload New Datasets</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="color:#798a9f; font-size:13px; margin-bottom:20px;">'
        "Upload the latest monthly Excel files to update forecasts and "
        "safety stock parameters."
        "</p>",
        unsafe_allow_html=True,
    )

    consumption_file = st.file_uploader(
        "Monthly Consumption Excel",
        type=["xlsx", "xls"],
        key="pipe_consumption",
        help="Must contain material_id and demand columns",
    )
    leadtime_file = st.file_uploader(
        "Material Master / LeadTime Excel",
        type=["xlsx", "xls"],
        key="pipe_leadtime",
        help="Must contain material_id, lead time, price, unrestricted stock",
    )

    st.markdown("</div>", unsafe_allow_html=True)  # close ss-card

    # ── Run Pipeline card ──────────────────────────────────────────────────────
    st.markdown('<div class="ss-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="ss-card-header">🚀 Run Pipeline</div>',
        unsafe_allow_html=True,
    )

    # Validation feedback
    files_ready = consumption_file is not None and leadtime_file is not None
    if not files_ready:
        st.markdown(
            '<p style="color:#798a9f; font-size:13px; margin-bottom:8px;">'
            "⚠️ Please upload <strong>both</strong> Excel files before running."
            "</p>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<p style="color:#00c864; font-size:13px; margin-bottom:8px;">'
            "✅ Both files ready — you can start the pipeline."
            "</p>",
            unsafe_allow_html=True,
        )

    # Pipeline already running?
    if st.session_state.pipeline_running:
        st.warning(
            "⏳ Pipeline is currently running. Please wait for it to finish.",
            icon="⚠️",
        )

    # Run button
    run_disabled = (
        not files_ready
        or st.session_state.pipeline_running
    )

    if st.button(
        "▶ Run Full Pipeline",
        key="btn_run_pipeline",
        type="primary",
        disabled=run_disabled,
        use_container_width=True,
    ):
        # ── Save uploaded files to Monthly_upload/ directory ─────────────────
        MONTHLY_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        consumption_save_path = MONTHLY_UPLOAD_DIR / "Consumption.xlsx"
        leadtime_save_path    = MONTHLY_UPLOAD_DIR / "LeadTime.xlsx"

        with open(consumption_save_path, "wb") as fh:
            fh.write(consumption_file.read())
        with open(leadtime_save_path, "wb") as fh:
            fh.write(leadtime_file.read())

        # ── Reset pipeline state ──────────────────────────────────────────────
        st.session_state.pipeline_running       = True
        st.session_state.pipeline_logs          = [
            f"[PORTAL] Files saved to {MONTHLY_UPLOAD_DIR}\n",
            "[PORTAL] Starting pipeline...\n",
        ]
        st.session_state.pipeline_stages_status = [STATUS_PENDING] * NUM_STAGES
        st.session_state.pipeline_done          = False
        st.session_state.pipeline_success       = None
        st.session_state.pipeline_result_msg    = ""
        st.session_state.pipeline_rerun_guard   = False

        # ── Create a fresh queue and launch background thread ─────────────────
        log_q = queue.Queue()
        st.session_state.pipeline_log_queue = log_q

        thread = threading.Thread(
            target=_run_pipeline_bg,
            args=(consumption_save_path, leadtime_save_path, log_q),
            daemon=True,
        )
        thread.start()
        st.rerun()

    # Optional reset button after pipeline is done
    if st.session_state.pipeline_done:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(
            "🔄 Reset & Run Again",
            key="btn_reset_pipeline",
            use_container_width=True,
        ):
            # Clear pipeline state so the page goes back to fresh state
            st.session_state.pipeline_running       = False
            st.session_state.pipeline_logs          = []
            st.session_state.pipeline_stages_status = [STATUS_PENDING] * NUM_STAGES
            st.session_state.pipeline_done          = False
            st.session_state.pipeline_success       = None
            st.session_state.pipeline_result_msg    = ""
            st.session_state.pipeline_log_queue     = None
            st.session_state.pipeline_rerun_guard   = False
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)  # close ss-card

    # ── Stage indicators card ──────────────────────────────────────────────────
    st.markdown('<div class="ss-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="ss-card-header">📊 Pipeline Stages</div>',
        unsafe_allow_html=True,
    )

    stages_status = st.session_state.pipeline_stages_status

    # Count completed stages for progress
    done_count   = sum(1 for s in stages_status if s == STATUS_DONE)
    failed_count = sum(1 for s in stages_status if s == STATUS_FAILED)

    # ── Progress bar ─────────────────────────────────────────────────────────
    if st.session_state.pipeline_running or st.session_state.pipeline_done:
        progress_fraction = done_count / NUM_STAGES
        st.progress(progress_fraction)
        if st.session_state.pipeline_running:
            st.markdown(
                f'<p style="color:#798a9f; font-size:12px; margin-top:4px;">'
                f"Stage {done_count + 1} of {NUM_STAGES} in progress…"
                f"</p>",
                unsafe_allow_html=True,
            )
        elif st.session_state.pipeline_done and st.session_state.pipeline_success:
            st.markdown(
                f'<p style="color:#00c864; font-size:12px; margin-top:4px;">'
                f"All {NUM_STAGES} stages completed successfully."
                f"</p>",
                unsafe_allow_html=True,
            )
        elif st.session_state.pipeline_done and not st.session_state.pipeline_success:
            st.markdown(
                f'<p style="color:#ff3c50; font-size:12px; margin-top:4px;">'
                f"Pipeline failed after {done_count} stage(s). See logs for details."
                f"</p>",
                unsafe_allow_html=True,
            )

    # ── Per-stage rows ────────────────────────────────────────────────────────
    for idx, (label, status) in enumerate(zip(STAGE_LABELS, stages_status)):
        icon  = STATUS_ICON[status]
        color = STATUS_COLOR[status]

        st.markdown(
            f"""
            <div style="
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 10px 14px;
                margin-bottom: 6px;
                background: rgba(14,23,41,0.55);
                border: 1px solid rgba(31,111,235,0.12);
                border-radius: 10px;
            ">
                <div style="
                    font-size: 18px;
                    min-width: 28px;
                    text-align: center;
                ">{icon}</div>
                <div style="flex: 1;">
                    <span style="
                        font-size: 13px;
                        font-weight: 600;
                        color: {color};
                    ">Stage {idx + 1} &nbsp;—&nbsp; {label}</span>
                </div>
                <div>
                    <span style="
                        font-size: 11px;
                        color: {color};
                        background: rgba(31,111,235,0.08);
                        border: 1px solid rgba(31,111,235,0.18);
                        border-radius: 20px;
                        padding: 2px 10px;
                        text-transform: uppercase;
                        letter-spacing: 0.04em;
                        font-weight: 600;
                    ">{status.upper()}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)  # close ss-card

    # ── Result banner ──────────────────────────────────────────────────────────
    if st.session_state.pipeline_done:
        if st.session_state.pipeline_success:
            st.success(
                f"✅ **Pipeline completed successfully!**\n\n"
                f"{st.session_state.pipeline_result_msg}",
                icon="🎉",
            )
        else:
            st.error(
                f"❌ **Pipeline failed.**\n\n"
                f"{st.session_state.pipeline_result_msg}",
                icon="🚨",
            )


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  RIGHT COLUMN — Live console log viewer                                   ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
with right_col:

    st.markdown('<div class="ss-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="ss-card-header">🖥️ Live Pipeline Logs</div>',
        unsafe_allow_html=True,
    )

    # Status badge for running vs done
    if st.session_state.pipeline_running:
        st.markdown(
            '<span class="ss-badge" style="'
            "background: rgba(240,165,0,0.15); "
            "border-color: rgba(240,165,0,0.4); "
            'color:#f0a500;">● RUNNING</span>',
            unsafe_allow_html=True,
        )
    elif st.session_state.pipeline_done and st.session_state.pipeline_success:
        st.markdown(
            '<span class="ss-badge" style="'
            "background: rgba(0,200,100,0.15); "
            "border-color: rgba(0,200,100,0.4); "
            'color:#00c864;">● COMPLETED</span>',
            unsafe_allow_html=True,
        )
    elif st.session_state.pipeline_done and not st.session_state.pipeline_success:
        st.markdown(
            '<span class="ss-badge" style="'
            "background: rgba(255,60,80,0.15); "
            "border-color: rgba(255,60,80,0.4); "
            'color:#ff3c50;">● FAILED</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="ss-badge" style="'
            "background: rgba(121,138,159,0.1); "
            "border-color: rgba(121,138,159,0.3); "
            'color:#798a9f;">● IDLE</span>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # The log placeholder that is refreshed on every rerun
    log_placeholder = st.empty()

    # Build the console output string from accumulated logs
    accumulated_logs = st.session_state.pipeline_logs
    if accumulated_logs:
        console_text = "".join(accumulated_logs)
        # Escape for HTML display
        console_text_escaped = (
            console_text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        # Colorise special markers inline
        console_text_escaped = console_text_escaped.replace(
            "[PIPELINE]", '<span style="color:#58a6ff;">[PIPELINE]</span>'
        ).replace(
            "[STAGE 1", '<span style="color:#a371f7;">[STAGE 1'
        ).replace(
            "[STAGE 2", '<span style="color:#a371f7;">[STAGE 2'
        ).replace(
            "[STAGE 3", '<span style="color:#a371f7;">[STAGE 3'
        ).replace(
            "[STAGE 4", '<span style="color:#a371f7;">[STAGE 4'
        ).replace(
            "[STAGE 5", '<span style="color:#a371f7;">[STAGE 5'
        )
        # Close any opened span tags from stage coloring
        console_text_escaped = console_text_escaped.replace(
            "[PORTAL]", '<span style="color:#39d353;">[PORTAL]</span>'
        ).replace(
            "[ERROR]", '<span style="color:#ff3c50;">[ERROR]</span>'
        ).replace(
            "[FATAL]", '<span style="color:#ff3c50;font-weight:bold;">[FATAL]</span>'
        ).replace(
            "[DB]", '<span style="color:#ffa657;">[DB]</span>'
        ).replace(
            "[UNEXPECTED ERROR]",
            '<span style="color:#ff3c50;font-weight:bold;">[UNEXPECTED ERROR]</span>',
        )

        log_placeholder.markdown(
            f'<div class="console-box" id="console-bottom">{console_text_escaped}</div>',
            unsafe_allow_html=True,
        )
        # Auto-scroll the console to the bottom via JavaScript injection
        st.markdown(
            """
            <script>
            (function(){
                const boxes = window.parent.document.querySelectorAll('.console-box');
                boxes.forEach(function(b){ b.scrollTop = b.scrollHeight; });
            })();
            </script>
            """,
            unsafe_allow_html=True,
        )
    else:
        log_placeholder.markdown(
            """
            <div class="console-box">
<span style="color:#798a9f;">No logs yet. Upload files and click ▶ Run Full Pipeline to begin.

The console will stream live output from each pipeline stage here.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Clear logs button (only when not running) ──────────────────────────────
    if not st.session_state.pipeline_running and accumulated_logs:
        if st.button(
            "🗑️ Clear Logs",
            key="btn_clear_logs",
            use_container_width=True,
        ):
            st.session_state.pipeline_logs = []
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)  # close ss-card

    # ── DB refresh status ──────────────────────────────────────────────────────
    if pipeline_just_finished and st.session_state.pipeline_success:
        st.markdown('<div class="ss-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="ss-card-header">🗄️ Database Status</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="rec-success" style="margin:0;">
                <div style="font-size:14px; font-weight:600; color:#00c864; margin-bottom:6px;">
                    ✅ Database Refreshed
                </div>
                <div style="font-size:13px; color:#c0d0e0;">
                    Predictions and historical demand tables have been updated
                    with the latest pipeline output. Dashboards will reflect
                    new data on next load.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE HISTORY SECTION (full-width, below columns)
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="ss-card">', unsafe_allow_html=True)
st.markdown(
    '<div class="ss-card-header">📋 Pipeline History</div>',
    unsafe_allow_html=True,
)

last_run: datetime.datetime | None = st.session_state.get("pipeline_last_run")

if last_run is None:
    st.markdown(
        """
        <div style="
            text-align: center;
            padding: 32px 20px;
            color: #798a9f;
            font-size: 14px;
        ">
            <div style="font-size:36px; margin-bottom:12px;">📭</div>
            No pipeline runs recorded in this session yet.
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    run_time_str = last_run.strftime("%d %b %Y, %H:%M:%S")
    elapsed_secs = (datetime.datetime.now() - last_run).total_seconds()
    if elapsed_secs < 60:
        ago_str = f"{int(elapsed_secs)}s ago"
    elif elapsed_secs < 3600:
        ago_str = f"{int(elapsed_secs // 60)}m ago"
    else:
        ago_str = f"{int(elapsed_secs // 3600)}h {int((elapsed_secs % 3600) // 60)}m ago"

    success_val = st.session_state.pipeline_success
    outcome_html = (
        '<span style="color:#00c864; font-weight:600;">✅ Success</span>'
        if success_val is True
        else '<span style="color:#ff3c50; font-weight:600;">❌ Failed</span>'
        if success_val is False
        else '<span style="color:#798a9f;">— Unknown</span>'
    )

    stages_done_count = sum(
        1 for s in st.session_state.pipeline_stages_status if s == STATUS_DONE
    )

    st.markdown(
        f"""
        <div style="
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
        ">
            <div class="spec-item">
                <span class="spec-label">Last Run</span>
                <span class="spec-value" style="font-size:13px;">{run_time_str}</span>
            </div>
            <div class="spec-item">
                <span class="spec-label">Time Since</span>
                <span class="spec-value">{ago_str}</span>
            </div>
            <div class="spec-item">
                <span class="spec-label">Outcome</span>
                <span class="spec-value">{outcome_html}</span>
            </div>
            <div class="spec-item">
                <span class="spec-label">Stages Completed</span>
                <span class="spec-value">{stages_done_count} / {NUM_STAGES}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Stage breakdown table
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#798a9f; font-size:12px; font-weight:600; '
        'text-transform:uppercase; letter-spacing:0.06em; margin-bottom:10px;">'
        "Stage breakdown</p>",
        unsafe_allow_html=True,
    )

    rows_html = ""
    for idx, (label, status) in enumerate(
        zip(STAGE_LABELS, st.session_state.pipeline_stages_status)
    ):
        icon  = STATUS_ICON[status]
        color = STATUS_COLOR[status]
        rows_html += f"""
        <tr>
            <td style="
                padding: 8px 14px;
                color: #798a9f;
                font-size: 12px;
                background: rgba(14,23,41,0.4);
                border-radius: 6px;
                border: 1px solid rgba(31,111,235,0.08);
            ">Stage {idx + 1}</td>
            <td style="
                padding: 8px 14px;
                color: #c0d0e0;
                font-size: 13px;
                background: rgba(14,23,41,0.4);
                border-radius: 6px;
                border: 1px solid rgba(31,111,235,0.08);
            ">{label}</td>
            <td style="
                padding: 8px 14px;
                text-align: center;
                background: rgba(14,23,41,0.4);
                border-radius: 6px;
                border: 1px solid rgba(31,111,235,0.08);
            ">
                <span style="color:{color}; font-size:15px;">{icon}</span>
                <span style="
                    color:{color};
                    font-size:11px;
                    font-weight:600;
                    text-transform:uppercase;
                    margin-left:6px;
                ">{status}</span>
            </td>
        </tr>
        """

    st.markdown(
        f"""
        <table style="
            width: 100%;
            border-collapse: separate;
            border-spacing: 4px 4px;
        ">
            <thead>
                <tr>
                    <th style="
                        text-align:left;
                        color:#58a6ff;
                        font-size:11px;
                        text-transform:uppercase;
                        letter-spacing:0.06em;
                        padding: 6px 14px;
                        background: rgba(31,111,235,0.1);
                        border-radius: 6px;
                    ">#</th>
                    <th style="
                        text-align:left;
                        color:#58a6ff;
                        font-size:11px;
                        text-transform:uppercase;
                        letter-spacing:0.06em;
                        padding: 6px 14px;
                        background: rgba(31,111,235,0.1);
                        border-radius: 6px;
                    ">Stage Name</th>
                    <th style="
                        text-align:center;
                        color:#58a6ff;
                        font-size:11px;
                        text-transform:uppercase;
                        letter-spacing:0.06em;
                        padding: 6px 14px;
                        background: rgba(31,111,235,0.1);
                        border-radius: 6px;
                    ">Status</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)  # close ss-card (history)


# ═══════════════════════════════════════════════════════════════════════════════
# LIVE-RERUN LOOP
# Trigger a rerun every 0.5 s while the pipeline is active so the UI
# receives fresh queue messages.  We stop rerunning as soon as pipeline_done
# is True to avoid an infinite loop.
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.pipeline_running and not st.session_state.pipeline_done:
    time.sleep(0.5)
    st.rerun()
