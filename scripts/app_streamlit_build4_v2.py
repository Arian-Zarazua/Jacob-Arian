"""
Streamlit app for Build 4: RAG + Router + Agent with Prompt Management
This app provides a UI for interacting with the Build 4 backend, which includes:
- RAG retrieval from a knowledge base
- A router that decides whether to use tools or generate code
- An agent that can execute tools or run generated code
- Prompt management to keep track of the conversation and context
To run this app:
1. Make sure you have the Build 4 backend implemented in builds/build4_rag_router_agent_streamlit.py
2. Install Streamlit if you haven't: pip install streamlit
3. Run this script: streamlit run scripts/app_streamlit_build4.py
"""

from __future__ import annotations

import html
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

try:
    from PIL import Image, UnidentifiedImageError
except Exception:  # Pillow should be installed with Streamlit, but keep app resilient.
    Image = None
    UnidentifiedImageError = Exception

sys.path.append(str(Path(__file__).resolve().parents[1]))

from builds.build4_rag_router_agent_streamlit import (
    initialize_build4_backend,
    ui_run_codegen,
    ui_run_router,
    ui_run_saved_code,
    ui_run_suggest,
    ui_plan_tool,
    ui_run_tool_from_plan,
    ui_save_generated_code,
)

# ──────────────────────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NFL Sports Analytics Agent",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# Global CSS — dark industrial analytics theme
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Root palette ── */
    :root {
        --bg-base:      #0b1118;
        --bg-panel:     #101722;
        --bg-card:      #16202c;
        --bg-elevated:  #1e2a38;
        --border:       #334155;
        --border-bright:#475569;
        --amber:        #8fb3ff;
        --amber-dim:    #5f7fbf;
        --amber-glow:   rgba(143,179,255,0.12);
        --amber-subtle: rgba(143,179,255,0.07);
        --cyan:         #7dd3fc;
        --green:        #86efac;
        --red:          #f87171;
        --text-primary: #f1f5f9;
        --text-secondary:#cbd5e1;
        --text-muted:   #94a3b8;
        --mono:         'Cascadia Mono', 'Consolas', 'SFMono-Regular', monospace;
        --display:      'Inter', 'Segoe UI', Arial, sans-serif;
        --body:         'Inter', 'Segoe UI', Arial, sans-serif;
    }

    /* ── Global reset ── */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: var(--bg-base) !important;
        color: var(--text-primary) !important;
        font-family: var(--body) !important;
    }

    [data-testid="stSidebar"] {
        background-color: var(--bg-panel) !important;
        border-right: 1px solid var(--border) !important;
    }

    /* ── Typography ── */
    h1, h2, h3, h4, h5, h6 {
        font-family: var(--display) !important;
        font-weight: 700 !important;
        letter-spacing: 0.005em !important;
        color: var(--text-primary) !important;
    }

    p, li, label, .stMarkdown {
        font-family: var(--body) !important;
        color: var(--text-secondary) !important;
        font-weight: 400 !important;
        line-height: 1.5 !important;
    }

    /* ── Masthead ── */
    .nfl-masthead {
        display: flex;
        align-items: flex-end;
        gap: 20px;
        padding: 28px 0 18px;
        border-bottom: 1px solid var(--border);
        margin-bottom: 28px;
    }
    .nfl-masthead .wordmark {
        font-family: var(--display);
        font-size: 2.8rem;
        font-weight: 800;
        letter-spacing: 0.015em;
        color: var(--amber);
        line-height: 1;
        text-transform: none;
    }
    .nfl-masthead .badge {
        font-family: var(--mono);
        font-size: 0.68rem;
        font-weight: 400;
        color: var(--bg-panel);
        background: var(--amber);
        padding: 3px 8px;
        border-radius: 2px;
        margin-bottom: 6px;
        letter-spacing: 0.04em;
        text-transform: none;
    }
    .nfl-masthead .subtitle {
        font-family: var(--body);
        font-size: 0.92rem;
        font-weight: 400;
        color: var(--text-secondary);
        margin-bottom: 7px;
        letter-spacing: 0.02em;
    }

    /* ── Stat cards (metrics) ── */
    [data-testid="stMetric"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-top: 2px solid var(--amber) !important;
        border-radius: 3px !important;
        padding: 14px 18px !important;
    }
    [data-testid="stMetricLabel"] {
        font-family: var(--mono) !important;
        font-size: 0.68rem !important;
        letter-spacing: 0.035em !important;
        text-transform: none !important;
        color: var(--text-muted) !important;
    }
    [data-testid="stMetricValue"] {
        font-family: var(--display) !important;
        font-size: 1.9rem !important;
        font-weight: 700 !important;
        color: var(--amber) !important;
        letter-spacing: 0.02em !important;
    }

    /* ── Tabs ── */
    [data-testid="stTabs"] [role="tablist"] {
        border-bottom: 1px solid var(--border) !important;
        gap: 2px !important;
        background: transparent !important;
    }
    [data-testid="stTabs"] [role="tab"] {
        font-family: var(--display) !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.025em !important;
        text-transform: none !important;
        color: var(--text-muted) !important;
        background: transparent !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        padding: 8px 18px !important;
        border-radius: 0 !important;
        transition: color 0.15s, border-color 0.15s !important;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color: var(--amber) !important;
        border-bottom: 2px solid var(--amber) !important;
        background: var(--amber-subtle) !important;
    }
    [data-testid="stTabs"] [role="tab"]:hover {
        color: var(--text-primary) !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        font-family: var(--display) !important;
        font-size: 0.82rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.035em !important;
        text-transform: none !important;
        background: transparent !important;
        color: var(--amber) !important;
        border: 1px solid var(--amber-dim) !important;
        border-radius: 2px !important;
        padding: 8px 22px !important;
        transition: all 0.15s !important;
    }
    .stButton > button:hover {
        background: var(--amber-glow) !important;
        border-color: var(--amber) !important;
        color: var(--amber) !important;
    }
    .stButton > button:active {
        background: var(--amber-dim) !important;
    }

    /* ── Primary / CTA button (InInitialize Agent) ── */
    .stButton > button[kind="primary"],
    [data-testid="stSidebar"] .stButton > button {
        background: var(--amber) !important;
        color: #0a0c0f !important;
        border: none !important;
        font-weight: 800 !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #d4901e !important;
        color: #0a0c0f !important;
    }

    /* ── Inputs & Textareas ── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        font-family: var(--mono) !important;
        font-size: 0.82rem !important;
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 2px !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--amber) !important;
        box-shadow: 0 0 0 1px var(--amber-dim) !important;
    }

    /* ── Selectbox / radio / slider ── */
    .stSelectbox > div > div,
    .stRadio > div,
    .stSlider {
        color: var(--text-secondary) !important;
    }
    .stSelectbox [data-baseweb="select"] > div {
        background: var(--bg-card) !important;
        border-color: var(--border) !important;
        font-family: var(--mono) !important;
        font-size: 0.82rem !important;
    }
    .stSlider [data-baseweb="slider"] [role="slider"] {
        background-color: var(--amber) !important;
    }
    .stSlider [data-baseweb="slider"] div[data-testid="stThumbValue"] {
        background: var(--amber) !important;
        color: #000 !important;
        font-family: var(--mono) !important;
    }

    /* ── Toggle ── */
    .stToggle [data-baseweb="checkbox"] span {
        background-color: var(--bg-elevated) !important;
        border-color: var(--border-bright) !important;
    }
    .stToggle [aria-checked="true"] span {
        background-color: var(--amber) !important;
    }

    /* ── Dataframes ── */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border) !important;
        border-radius: 2px !important;
    }
    [data-testid="stDataFrame"] table {
        font-family: var(--mono) !important;
        font-size: 0.78rem !important;
    }
    [data-testid="stDataFrame"] thead th {
        background: var(--bg-elevated) !important;
        color: var(--amber) !important;
        font-weight: 600 !important;
        letter-spacing: 0.06em !important;
        text-transform: none !important;
        font-size: 0.7rem !important;
        border-bottom: 1px solid var(--border-bright) !important;
    }
    [data-testid="stDataFrame"] tbody tr:hover td {
        background: var(--amber-subtle) !important;
    }

    /* ── Code blocks ── */
    .stCode, code, pre {
        font-family: var(--mono) !important;
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 2px !important;
        font-size: 0.78rem !important;
        color: #a8d8ea !important;
    }

    /* ── Expanders ── */
    .streamlit-expanderHeader {
        font-family: var(--display) !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.025em !important;
        text-transform: none !important;
        color: var(--text-secondary) !important;
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 2px !important;
    }
    .streamlit-expanderContent {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
    }

    /* ── Status / alerts ── */
    [data-testid="stAlert"] {
        font-family: var(--body) !important;
        border-radius: 2px !important;
        border-left-width: 3px !important;
        font-size: 0.88rem !important;
    }
    [data-testid="stAlert"][data-baseweb="notification"][kind="info"] {
        background: rgba(54,197,240,0.08) !important;
        border-left-color: var(--cyan) !important;
        color: var(--cyan) !important;
    }
    [data-testid="stAlert"][data-baseweb="notification"][kind="success"] {
        background: rgba(46,184,134,0.08) !important;
        border-left-color: var(--green) !important;
        color: var(--green) !important;
    }
    [data-testid="stAlert"][data-baseweb="notification"][kind="error"] {
        background: rgba(224,30,90,0.08) !important;
        border-left-color: var(--red) !important;
        color: var(--red) !important;
    }
    [data-testid="stAlert"][data-baseweb="notification"][kind="warning"] {
        background: var(--amber-subtle) !important;
        border-left-color: var(--amber) !important;
        color: var(--amber) !important;
    }

    /* ── Spinners ── */
    [data-testid="stSpinner"] > div {
        color: var(--amber) !important;
        font-family: var(--mono) !important;
        font-size: 0.8rem !important;
    }

    /* ── Sidebar labels ── */
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown p {
        font-family: var(--mono) !important;
        font-size: 0.76rem !important;
        color: var(--text-secondary) !important;
        letter-spacing: 0.05em !important;
    }
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        font-family: var(--display) !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        color: var(--amber) !important;
        letter-spacing: 0.035em !important;
        text-transform: none !important;
    }

    /* ── Section dividers ── */
    hr {
        border: none !important;
        border-top: 1px solid var(--border) !important;
        margin: 22px 0 !important;
    }

    /* ── Section header custom component ── */
    .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 28px 0 16px;
    }
    .section-header .num {
        font-family: var(--mono);
        font-size: 0.7rem;
        color: var(--amber);
        background: var(--amber-subtle);
        border: 1px solid var(--amber-dim);
        padding: 2px 7px;
        border-radius: 2px;
        letter-spacing: 0.015em;
    }
    .section-header .label {
        font-family: var(--display);
        font-size: 1.35rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        text-transform: none;
        color: var(--text-primary);
    }
    .section-header::after {
        content: '';
        flex: 1;
        height: 1px;
        background: var(--border);
    }

    /* ── Inline label pill ── */
    .pill {
        display: inline-block;
        font-family: var(--mono);
        font-size: 0.65rem;
        letter-spacing: 0.035em;
        text-transform: none;
        background: var(--bg-elevated);
        border: 1px solid var(--border-bright);
        border-radius: 2px;
        padding: 2px 8px;
        color: var(--text-secondary);
        margin-left: 8px;
    }

    /* ── Download buttons ── */
    .stDownloadButton > button {
        font-family: var(--mono) !important;
        font-size: 0.72rem !important;
        font-weight: 400 !important;
        letter-spacing: 0.06em !important;
        background: var(--bg-card) !important;
        color: var(--cyan) !important;
        border: 1px solid var(--border-bright) !important;
        border-radius: 2px !important;
        padding: 5px 14px !important;
    }
    .stDownloadButton > button:hover {
        border-color: var(--cyan) !important;
        background: rgba(54,197,240,0.06) !important;
    }

    /* ── File uploader ── */
    [data-testid="stFileUploader"] {
        background: var(--bg-card) !important;
        border: 1px dashed var(--border-bright) !important;
        border-radius: 2px !important;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: var(--amber-dim) !important;
    }

    /* ── Radio buttons ── */
    .stRadio [data-testid="stMarkdownContainer"] p {
        font-family: var(--mono) !important;
        font-size: 0.8rem !important;
    }

    /* ── Caption ── */
    [data-testid="stCaptionContainer"] {
        font-family: var(--mono) !important;
        font-size: 0.7rem !important;
        color: var(--text-muted) !important;
        letter-spacing: 0.04em !important;
    }

    /* ── Success/error text ── */
    .stSuccess {
        background: rgba(46,184,134,0.08) !important;
    }


    /* ── Readability refinements ── */
    .stMarkdown p, .stMarkdown li {
        line-height: 1.55 !important;
    }
    div[data-testid="stText"], .stText, textarea {
        color: var(--text-primary) !important;
    }
    [data-testid="stExpander"] {
        border-color: var(--border) !important;
    }
    [data-testid="stDataFrame"] * {
        color-scheme: dark !important;
    }


    /* ── Modern Streamlit expander/dropdown compatibility ── */
    [data-testid="stExpander"] {
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        background: var(--bg-card) !important;
        overflow: hidden !important;
        margin-bottom: 12px !important;
    }
    [data-testid="stExpander"] details summary {
        color: var(--text-primary) !important;
        background: var(--bg-elevated) !important;
        font-family: var(--body) !important;
        font-weight: 650 !important;
    }
    [data-baseweb="popover"], [data-baseweb="menu"] {
        background: var(--bg-elevated) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-bright) !important;
        border-radius: 8px !important;
        z-index: 999999 !important;
    }
    [role="option"] {
        color: var(--text-primary) !important;
        background: var(--bg-elevated) !important;
        font-family: var(--body) !important;
    }
    [role="option"]:hover {
        background: var(--amber-subtle) !important;
    }



    /* ── SQL result table: LaTeX-like display ── */
    .sql-result-card {
        background: linear-gradient(180deg, rgba(143,179,255,0.10), rgba(22,32,44,0.96));
        border: 1px solid var(--border-bright);
        border-top: 2px solid var(--amber);
        border-radius: 10px;
        padding: 16px 18px;
        margin: 14px 0 12px;
        box-shadow: 0 12px 28px rgba(0,0,0,0.22);
    }
    .sql-result-kicker {
        font-family: var(--mono);
        font-size: 0.66rem;
        letter-spacing: 0.12em;
        color: var(--amber);
        margin-bottom: 5px;
    }
    .sql-result-title {
        font-family: var(--display);
        font-size: 1.25rem;
        font-weight: 750;
        color: var(--text-primary);
    }
    .sql-result-meta {
        font-family: var(--mono);
        font-size: 0.72rem;
        color: var(--text-muted);
        margin-top: 4px;
    }
    .latex-table-wrap {
        background: #f8fafc;
        color: #0f172a;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        padding: 18px 22px;
        margin: 10px 0 18px;
        box-shadow: 0 14px 34px rgba(0,0,0,0.28);
        overflow-x: auto;
    }
    .latex-table-caption {
        font-family: Georgia, 'Times New Roman', serif;
        font-size: 0.92rem;
        font-style: italic;
        color: #334155;
        text-align: center;
        margin-bottom: 10px;
    }
    table.latex-table {
        width: 100%;
        border-collapse: collapse;
        font-family: Georgia, 'Times New Roman', serif;
        font-size: 0.95rem;
        color: #0f172a;
        border-top: 2px solid #0f172a;
        border-bottom: 2px solid #0f172a;
    }
    table.latex-table thead tr {
        border-bottom: 1.5px solid #0f172a;
    }
    table.latex-table th {
        font-weight: 700;
        text-align: left;
        padding: 8px 12px;
        white-space: nowrap;
    }
    table.latex-table td {
        padding: 8px 12px;
        border: none;
        vertical-align: top;
    }
    table.latex-table tbody tr:nth-child(even) td {
        background: #eef2f7;
    }
    table.latex-table tbody tr:hover td {
        background: #dbeafe;
    }

    /* ── Hide Streamlit branding ── */
    #MainMenu, footer, header[data-testid="stHeader"] { display: none !important; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: var(--bg-panel); }
    ::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--amber-dim); }

    /* ── Number input arrows ── */
    .stNumberInput button {
        background: var(--bg-elevated) !important;
        color: var(--amber) !important;
        border-color: var(--border) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# Masthead
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="nfl-masthead">
        <div>
            <div class="wordmark">NFL Sports Analytics Agent </div>
        </div>
        <div style="padding-bottom:8px">
            <div class="badge">Python | RAG | SQL </div>
            <div class="subtitle">Datasets sourced from Pro Football Reference and Stat Savant</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# Session state
# ──────────────────────────────────────────────────────────────────────────────
for key, default in [
    ("backend", None),
    ("uploaded_data_path", None),
    ("loaded_file_count", 0),
    ("last_codegen_result", None),
    ("last_router_result", None),
    ("last_tool_plan_result", None),
    ("last_tool_run_result", None),
    ("last_execute_result", None),
    ("backend_signature", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ──────────────────────────────────────────────────────────────────────────────
# Helpers — file I/O
# ──────────────────────────────────────────────────────────────────────────────
def save_uploaded_csv(uploaded_file) -> Path:
    tmp_dir = Path(tempfile.gettempdir()) / "build4_streamlit_uploads"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    out_path = tmp_dir / uploaded_file.name
    with open(out_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.session_state.loaded_file_count = 1
    return out_path


def save_uploaded_csv_folder(uploaded_files) -> Path:
    tmp_dir = Path(tempfile.gettempdir()) / "build4_streamlit_uploads" / "csv_folder"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for old in tmp_dir.glob("*.csv"):
        old.unlink(missing_ok=True)
    for uploaded_file in uploaded_files:
        out_path = tmp_dir / Path(uploaded_file.name).name
        with open(out_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
    st.session_state.loaded_file_count = len(uploaded_files)
    return tmp_dir


def make_report_zip(report_dir: Path) -> Optional[Path]:
    if not report_dir.exists():
        return None
    zip_path = report_dir.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in report_dir.rglob("*"):
            if p.is_file():
                zf.write(p, arcname=p.relative_to(report_dir))
    return zip_path


def safe_read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def render_download_button(path: Path, prefix: str, instance_id: str) -> None:
    with open(path, "rb") as f:
        st.download_button(
            label=f"⬇ {path.name}",
            data=f.read(),
            file_name=path.name,
            key=f"download_{prefix}_{instance_id}_{path.name}_{path.stat().st_mtime_ns}",
        )


def render_single_artifact(path: Path, prefix: str = "artifact", instance_id: str = "0") -> None:
    if not path.exists():
        st.warning(f"Missing artifact: {path}")
        return

    suffix = path.suffix.lower()

    # Card wrapper
    st.markdown(
        f'<div style="border:1px solid var(--border);border-top:2px solid var(--amber-dim);'
        f'border-radius:3px;padding:14px 16px;margin-bottom:12px;background:var(--bg-card)">'
        f'<span style="font-family:var(--mono);font-size:0.78rem;color:var(--amber)">{path.name}</span>'
        f'<span style="font-family:var(--mono);font-size:0.65rem;color:var(--text-muted);margin-left:10px">'
        f'{path.suffix.upper()[1:]}</span></div>',
        unsafe_allow_html=True,
    )
    st.caption(str(path))

    try:
        if suffix in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
            if suffix == ".svg" or Image is None:
                st.image(str(path), caption=path.name, width="stretch")
            else:
                try:
                    with Image.open(path) as img:
                        width_px, height_px = img.size
                        if width_px <= 0 or height_px <= 0:
                            st.warning(f"Image has invalid dimensions: {width_px} × {height_px}")
                        else:
                            st.image(img.copy(), caption=path.name, width="stretch")
                except (UnidentifiedImageError, OSError, ValueError) as img_error:
                    st.warning(f"Could not render image {path.name}: {img_error}")
        elif suffix == ".csv":
            df = pd.read_csv(path)
            st.dataframe(df, width="stretch")
        elif suffix in {".txt", ".log", ".py", ".md", ".json", ".html"}:
            text = safe_read_text(path)
            if suffix == ".py":
                st.code(text, language="python")
            elif suffix == ".json":
                st.code(text, language="json")
            else:
                st.text_area(
                    label=f"Preview: {path.name}",
                    value=text,
                    height=220,
                    key=f"text_{prefix}_{instance_id}_{path.name}_{path.stat().st_mtime_ns}",
                )
        else:
            st.info("Preview not available for this file type.")
    except Exception as e:
        st.warning(f"Could not preview {path.name}: {e}")

    render_download_button(path, prefix=prefix, instance_id=instance_id)


def render_artifacts(artifact_paths, title: str = "Artifacts", prefix: str = "artifact") -> None:
    if not artifact_paths:
        st.info("No artifacts were produced.")
        return

    st.markdown(
        f'<div class="section-header"><span class="label">{title}</span></div>',
        unsafe_allow_html=True,
    )

    unique_paths = []
    seen = set()
    for p in artifact_paths:
        p = Path(p)
        try:
            p_key = str(p.resolve())
        except Exception:
            p_key = str(p)
        if p_key not in seen:
            seen.add(p_key)
            unique_paths.append(p)

    for i, path in enumerate(unique_paths):
        render_single_artifact(path, prefix=prefix, instance_id=str(i))


# ──────────────────────────────────────────────────────────────────────────────
# Helpers — report / artifact discovery
# ──────────────────────────────────────────────────────────────────────────────
def list_report_files(report_dir: Path) -> list[Path]:
    if not report_dir.exists():
        return []
    return sorted(
        [p for p in report_dir.rglob("*") if p.is_file()],
        key=lambda p: str(p).lower(),
    )


def list_figure_files(report_dir: Path) -> list[Path]:
    if not report_dir.exists():
        return []
    image_suffixes = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
    return sorted(
        [p for p in report_dir.rglob("*") if p.is_file() and p.suffix.lower() in image_suffixes],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def snapshot_report_files(report_dir: Path) -> dict[str, int]:
    if not report_dir.exists():
        return {}
    snapshot: dict[str, int] = {}
    for p in report_dir.rglob("*"):
        if p.is_file():
            try:
                snapshot[str(p.resolve())] = p.stat().st_mtime_ns
            except OSError:
                continue
    return snapshot


def list_new_or_modified_artifacts(
    report_dir: Path,
    before_snapshot: dict[str, int],
    include_suffixes: Optional[set[str]] = None,
) -> list[Path]:
    if not report_dir.exists():
        return []
    if include_suffixes is None:
        include_suffixes = ARTIFACT_SUFFIXES
    changed: list[Path] = []
    for p in report_dir.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in include_suffixes:
            continue
        try:
            key = str(p.resolve())
            mtime_ns = p.stat().st_mtime_ns
        except OSError:
            continue
        if key not in before_snapshot or before_snapshot[key] != mtime_ns:
            changed.append(p)
    return sorted(changed, key=lambda x: x.stat().st_mtime, reverse=True)


ARTIFACT_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".webp", ".svg",
    ".csv", ".txt", ".log", ".md", ".json", ".html",
}


def get_artifact_search_roots(backend: dict) -> list[Path]:
    roots: list[Path] = []
    seen: set[str] = set()

    def add(raw) -> None:
        if not raw:
            return
        p = Path(raw)
        candidates = [p]
        if p.name not in {"tool_figures", "tool_outputs"}:
            candidates.extend([p / "tool_figures", p / "tool_outputs", p / "figures", p / "plots"])
        for c in candidates:
            try:
                key = str(c.resolve())
            except Exception:
                key = str(c)
            if c.exists() and key not in seen:
                seen.add(key)
                roots.append(c)

    add(backend.get("report_dir"))
    cwd = Path.cwd()
    for fallback in [
        cwd / "reports_streamlit",
        cwd / "reports",
        cwd / "tool_figures",
        cwd / "tool_outputs",
        cwd / "figures",
        cwd / "plots",
    ]:
        add(fallback)
    return roots


def snapshot_artifact_files(backend: dict, include_suffixes: Optional[set[str]] = None) -> dict[str, int]:
    include_suffixes = include_suffixes or ARTIFACT_SUFFIXES
    snapshot: dict[str, int] = {}
    for root in get_artifact_search_roots(backend):
        files = root.rglob("*") if root.is_dir() else [root]
        for p in files:
            if not p.is_file() or p.suffix.lower() not in include_suffixes:
                continue
            try:
                snapshot[str(p.resolve())] = p.stat().st_mtime_ns
            except OSError:
                continue
    return snapshot


def list_new_or_modified_artifacts_from_snapshot(
    backend: dict,
    before_snapshot: dict[str, int],
    include_suffixes: Optional[set[str]] = None,
) -> list[Path]:
    include_suffixes = include_suffixes or ARTIFACT_SUFFIXES
    changed: list[Path] = []
    seen: set[str] = set()
    for root in get_artifact_search_roots(backend):
        files = root.rglob("*") if root.is_dir() else [root]
        for p in files:
            if not p.is_file() or p.suffix.lower() not in include_suffixes:
                continue
            try:
                key = str(p.resolve())
                mtime_ns = p.stat().st_mtime_ns
            except OSError:
                continue
            if key in seen:
                continue
            if key not in before_snapshot or before_snapshot[key] != mtime_ns:
                seen.add(key)
                changed.append(p)
    return sorted(changed, key=lambda x: x.stat().st_mtime, reverse=True)


def merge_tool_display_artifacts(backend: dict, run_res: dict) -> list[Path]:
    return merge_unique_paths(
        run_res.get("session_artifact_paths", []) or [],
        run_res.get("artifact_paths", []) or [],
    )


def merge_unique_paths(*path_groups) -> list[Path]:
    merged: list[Path] = []
    seen: set[str] = set()
    for group in path_groups:
        for raw in group or []:
            p = Path(raw)
            try:
                key = str(p.resolve())
            except Exception:
                key = str(p)
            if key not in seen:
                seen.add(key)
                merged.append(p)
    return merged


def render_figure_gallery(report_dir: Path, prefix: str = "figure") -> None:
    figure_paths = list_figure_files(report_dir)
    if not figure_paths:
        st.info("No generated figures found in the report directory yet.")
        return
    render_artifacts(figure_paths, title="Generated Figures", prefix=prefix)


def render_report_browser(report_dir: Path) -> None:
    if not report_dir.exists():
        st.info(f"Report directory does not exist yet: {report_dir}")
        return
    report_files = list_report_files(report_dir)
    if not report_files:
        st.info("No saved reports or artifacts found yet.")
        return
    st.caption(f"Report directory: {report_dir}")
    render_artifacts(report_files, title="All Saved Files", prefix="reports_artifact")




# ──────────────────────────────────────────────────────────────────────────────
# Helpers — tool output rendering
# ──────────────────────────────────────────────────────────────────────────────
def _extract_sql_tool_payload(tool_run_res: dict) -> Optional[dict]:
    """Extract sql_query metadata from normal dict payloads or ToolResult repr text."""
    if not tool_run_res or tool_run_res.get("tool_name") != "sql_query":
        return None

    structured = tool_run_res.get("structured")
    if isinstance(structured, dict) and structured.get("preview") is not None:
        return structured

    raw_result = tool_run_res.get("result") or tool_run_res.get("tool_result")
    raw_structured = getattr(raw_result, "structured", None)
    if isinstance(raw_structured, dict) and raw_structured.get("preview") is not None:
        return raw_structured

    tool_text = str(tool_run_res.get("tool_text", ""))
    marker = "structured="
    if "ToolResult(" not in tool_text or marker not in tool_text:
        return None

    try:
        import ast

        start = tool_text.index(marker) + len(marker)
        payload = tool_text[start:]
        if payload.endswith(")"):
            payload = payload[:-1]
        parsed = ast.literal_eval(payload)
        if isinstance(parsed, dict) and parsed.get("preview") is not None:
            return parsed
    except Exception:
        return None

    return None


def _format_sql_cell(value) -> str:
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:,.3f}".rstrip("0").rstrip(".")
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def render_sql_query_result(tool_run_res: dict) -> bool:
    """Render sql_query output as a LaTeX-like results table. Returns True if rendered."""
    payload = _extract_sql_tool_payload(tool_run_res)
    if not payload:
        return False

    rows = payload.get("preview") or []
    columns = payload.get("columns") or (list(rows[0].keys()) if rows else [])
    df_preview = pd.DataFrame(rows, columns=columns if columns else None)

    rows_returned = int(payload.get("rows_returned", len(df_preview)) or 0)
    rows_shown = int(payload.get("rows_shown", len(df_preview)) or len(df_preview))
    query = str(payload.get("query", "")).strip()

    st.markdown(
        f"""
        <div class="sql-result-card">
            <div class="sql-result-kicker">SQL RESULT</div>
            <div class="sql-result-title">Query Output</div>
            <div class="sql-result-meta">Returned {rows_returned:,} row(s) · Displaying {rows_shown:,}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if query:
        with st.expander("SQL QUERY", expanded=False):
            st.code(query, language="sql")

    if df_preview.empty:
        st.info("The SQL query ran successfully, but returned no rows.")
        return True

    display_df = df_preview.copy()
    for col in display_df.columns:
        display_df[col] = display_df[col].map(_format_sql_cell)

    header_html = "".join(f"<th>{html.escape(str(col))}</th>" for col in display_df.columns)
    body_rows = []
    for _, row in display_df.iterrows():
        body_rows.append(
            "<tr>" + "".join(f"<td>{html.escape(str(value))}</td>" for value in row.tolist()) + "</tr>"
        )

    st.markdown(
        f"""
        <div class="latex-table-wrap">
            <div class="latex-table-caption">Table 1. SQL query result preview</div>
            <table class="latex-table">
                <thead><tr>{header_html}</tr></thead>
                <tbody>{''.join(body_rows)}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return True


def _looks_like_markdown_table(text: str) -> bool:
    """Best-effort check for markdown tables returned by numerical tools."""
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    for i in range(len(lines) - 1):
        if "|" in lines[i] and "|" in lines[i + 1] and "---" in lines[i + 1]:
            return True
    return False


def render_generic_tool_output(tool_run_res: dict) -> None:
    """Render numerical/table/text tool outputs visibly in the main UI.

    Earlier versions only displayed artifact paths and hid generic numerical
    results inside a collapsed expander. Most summary tools return text/markdown
    rather than images, so the UI looked blank even when the backend succeeded.
    """
    if render_sql_query_result(tool_run_res):
        return

    tool_text = str(tool_run_res.get("tool_text", "") or "").strip()

    st.markdown(
        '<div class="section-header"><span class="label">Analysis Output</span></div>',
        unsafe_allow_html=True,
    )

    if not tool_text:
        st.info("The tool completed, but returned no textual output.")
        return

    # Markdown tables should render as readable tables in Streamlit.
    if _looks_like_markdown_table(tool_text):
        st.markdown(tool_text)
    else:
        # Keep this expanded and visible. Numerical summaries often arrive as plain text.
        st.code(tool_text, language="text")

    with st.expander("Raw tool output", expanded=False):
        st.text(tool_text)


# ──────────────────────────────────────────────────────────────────────────────
# SQLite info panel
# ──────────────────────────────────────────────────────────────────────────────
def render_sqlite_database_info(backend: dict) -> None:
    db_path = backend.get("db_path")
    sqlite_meta = backend.get("sqlite_meta", {}) or {}
    validation = backend.get("sqlite_validation", {}) or {}

    if not db_path:
        st.info("SQLite metadata not available.")
        return

    db_path = Path(db_path)
    v_ok = bool(validation.get("ok"))
    exists = bool(validation.get("exists", db_path.exists()))
    integrity = validation.get("integrity_check", [])
    fk_issues = validation.get("foreign_key_check", [])
    row_counts = validation.get("row_counts", {}) or {}
    schema_objects = validation.get("schema_objects", []) or []
    create_statements = validation.get("create_statements", {}) or {}
    sample_rows = validation.get("sample_rows", {}) or {}

    status_label = "✓ Verified" if v_ok else "⚠ Needs Review"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("SQLite Status", status_label)
    c2.metric("DB File", "Present" if exists else "Missing")
    c3.metric("Tables / Views", f"{len(schema_objects):,}")
    nfl_rows = row_counts.get("nfl_data", 0)
    c4.metric("nfl_data Rows", f"{nfl_rows:,}" if isinstance(nfl_rows, int) else str(nfl_rows or "n/a"))

    st.caption(f"Database path: {db_path}")
    if db_path.exists():
        render_download_button(db_path, prefix="sqlite_db", instance_id="main")

    if validation.get("error"):
        st.error(validation["error"])
    elif v_ok:
        st.success("Integrity check passed · No foreign-key issues · Tables queryable")
    else:
        st.warning("Database created, but one or more verification checks need review.")

    with st.expander("VERIFICATION CHECKS", expanded=True):
        check_df = pd.DataFrame([
            {
                "Check": "PRAGMA integrity_check",
                "Result": str(integrity or "not run"),
                "Passed": integrity == [("ok",)] or integrity == [["ok"]],
            },
            {
                "Check": "PRAGMA foreign_key_check",
                "Result": "no issues" if not fk_issues else str(fk_issues),
                "Passed": not bool(fk_issues),
            },
            {
                "Check": "Table row counts",
                "Result": f"{len(row_counts)} tables counted",
                "Passed": bool(row_counts),
            },
        ])
        st.dataframe(check_df, width="stretch", hide_index=True)

    with st.expander("LLM SQL CONTEXT"):
        st.code(backend.get("sqlite_schema_text", "SQLite metadata not available."), language="sql")


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────
st.sidebar.markdown("## Configuration")
st.sidebar.markdown("---")

st.sidebar.markdown("**Model & Inference**")
model = st.sidebar.text_input("Model ID", value="gpt-4o-mini")
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.2, 0.05)
stream = st.sidebar.toggle("Streaming", value=False)
memory = st.sidebar.toggle("Conversation Memory", value=False)
timeout_s = st.sidebar.number_input(
    "Execution timeout (s)", min_value=10, max_value=600, value=60, step=10
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Output**")
report_dir_str = st.sidebar.text_input("Report directory", value="reports_streamlit")

# ── RAG directory dropdown ──
def get_default_knowledge_root() -> Path:
    project_root = Path(__file__).resolve().parents[1]
    candidates = [
        project_root / "knowledge",
        Path.cwd() / "knowledge",
        Path(r"C:\Users\arian\Documents\PythonProjects\Jacob & Arian\knowledge"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


knowledge_root = get_default_knowledge_root()
if knowledge_root.exists():
    rag_options = ["None"] + sorted([p.name for p in knowledge_root.iterdir() if p.is_dir()])
else:
    rag_options = ["None"]
    st.sidebar.warning(f"Knowledge folder not found: {knowledge_root}")

st.sidebar.markdown("---")
st.sidebar.markdown("**Knowledge & RAG**")
selected_rag = st.sidebar.selectbox(
    "Knowledge folder",
    rag_options,
    index=0,
    help="Choose which RAG knowledge directory to use.",
)

knowledge_dir_str = ""
if selected_rag != "None":
    knowledge_dir_str = str(knowledge_root / selected_rag)

with st.sidebar.expander("Advanced RAG path override"):
    manual_knowledge_dir = st.text_input(
        "Manual knowledge folder path",
        value="",
        help="Optional. Overrides the dropdown when provided.",
    )
    if manual_knowledge_dir.strip():
        knowledge_dir_str = manual_knowledge_dir.strip()

rag_k = st.sidebar.number_input("RAG k", min_value=1, max_value=10, value=4, step=1)
csv_glob = st.sidebar.text_input("CSV glob for folders", value="*.csv")

st.sidebar.markdown("---")
st.sidebar.markdown("**Dataset**")
data_mode = st.sidebar.radio(
    "Data source",
    ["Upload one CSV", "Upload multiple CSVs", "Use local folder path"],
    index=1,
)

if data_mode == "Upload one CSV":
    uploaded_file = st.sidebar.file_uploader("Upload a CSV dataset", type=["csv"], key="one_csv")
    if uploaded_file is not None:
        st.session_state.uploaded_data_path = save_uploaded_csv(uploaded_file)
        st.sidebar.success(f"Loaded: {uploaded_file.name}")

elif data_mode == "Upload multiple CSVs":
    uploaded_files = st.sidebar.file_uploader(
        "Upload CSV files",
        type=["csv"],
        accept_multiple_files=True,
        key="many_csvs",
        help="Streamlit saves them into one temporary folder.",
    )
    if uploaded_files:
        st.session_state.uploaded_data_path = save_uploaded_csv_folder(uploaded_files)
        st.sidebar.success(f"{len(uploaded_files)} files loaded as dataset folder.")

else:
    local_folder = st.sidebar.text_input(
        "Local CSV folder path",
        value="data/Pro-Football-Reference/Stats",
        help="Path must exist on the machine running Streamlit.",
    )
    if local_folder.strip():
        st.session_state.uploaded_data_path = Path(local_folder.strip())
        st.session_state.loaded_file_count = 0
        st.sidebar.caption(f"Path: {st.session_state.uploaded_data_path}")

st.sidebar.markdown("---")
init_clicked = st.sidebar.button("InInitialize Agent", width="stretch")

if init_clicked:
    if st.session_state.uploaded_data_path is None:
        st.sidebar.error("Please upload or specify a CSV dataset first.")
    else:
        knowledge_dir: Optional[Path] = None
        if knowledge_dir_str.strip():
            knowledge_dir = Path(knowledge_dir_str.strip())

        try:
            backend = initialize_build4_backend(
                data_path=Path(st.session_state.uploaded_data_path),
                report_dir=Path(report_dir_str),
                model=model,
                temperature=temperature,
                memory=memory,
                stream=stream,
                session_id="streamlit-session",
                knowledge_dir=knowledge_dir,
                rag_k=int(rag_k),
                glob=csv_glob.strip() or "*.csv",
                tags=["build4", "streamlit"],
            )
            st.session_state.backend = backend
            st.session_state.backend_signature = {
                "data_path": str(st.session_state.uploaded_data_path),
                "model": model,
                "temperature": temperature,
                "memory": memory,
                "stream": stream,
                "knowledge_dir": str(knowledge_dir) if knowledge_dir else "",
                "rag_k": int(rag_k),
                "glob": csv_glob.strip() or "*.csv",
                "loaded_file_count": st.session_state.loaded_file_count,
                "db_path": str(backend.get("db_path", "")),
            }
            st.sidebar.success("Agent ready.")
        except Exception as e:
            st.sidebar.error(f"Initialization failed: {e}")

backend = st.session_state.backend

# ──────────────────────────────────────────────────────────────────────────────
# Section 1 — Dataset & Schema
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="section-header">'
    '<span class="num">01</span>'
    '<span class="label">Dataset &amp; Schema</span>'
    '</div>',
    unsafe_allow_html=True,
)

if backend is None:
    st.info("Upload a CSV and click InInitialize Agent in the sidebar to begin.")
else:
    df = backend["df"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Rows", f"{len(df):,}")
    m2.metric("Columns", f"{df.shape[1]:,}")
    loaded_count = st.session_state.backend_signature.get("loaded_file_count") or (
        df["_source_file"].nunique() if "_source_file" in df.columns else 1
    )
    m3.metric("CSV Files", str(loaded_count))
    m4.metric("Missing Cells", f"{int(df.isna().sum().sum()):,}")

    if "_source_file" in df.columns:
        with st.expander("LOADED CSV FILES"):
            st.dataframe(
                df["_source_file"].value_counts().rename_axis("source_file").reset_index(name="rows"),
                width="stretch",
            )

    schema_df = pd.DataFrame({
        "column": list(df.columns),
        "dtype": [str(df[c].dtype) for c in df.columns],
        "missing_n": [int(df[c].isna().sum()) for c in df.columns],
    })

    with st.expander("Column details", expanded=True):
        st.dataframe(schema_df, width="stretch")

    with st.expander("Data preview", expanded=False):
        st.dataframe(df.head(20), width="stretch")

    st.markdown(
        '<p style="font-family:var(--mono);font-size:0.72rem;letter-spacing:0.1em;'
        'text-transform:uppercase;color:var(--amber);margin:20px 0 10px">SQLite Database</p>',
        unsafe_allow_html=True,
    )
    render_sqlite_database_info(backend)

    with st.expander("LOADED TOOLS"):
        st.write(backend["allowed_tools"])


# ──────────────────────────────────────────────────────────────────────────────
# Section 2 — Agent Commands
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="section-header">'
    '<span class="num">02</span>'
    '<span class="label">Agent Commands</span>'
    '</div>',
    unsafe_allow_html=True,
)

if backend is not None:
    tab_suggest, tab_ask, tab_tool, tab_code, tab_run, tab_reports = st.tabs(
        ["Suggest", "Ask / Route", "Tool", "Code Gen", "Execute", "Reports"]
    )

    # ── Suggest ──────────────────────────────────────────────────────────────
    with tab_suggest:
        st.markdown(
            '<p style="font-family:var(--body);font-size:0.9rem;color:var(--text-secondary);'
            'margin-bottom:18px">Generate research question suggestions and analysis ideas from your dataset.</p>',
            unsafe_allow_html=True,
        )
        suggest_q = st.text_area(
            "Dataset question or analysis request",
            placeholder="Example: What are 3 good research questions I can test with this dataset?",
            key="suggest_q",
            height=100,
        )

        if st.button("▶ Run Suggest", key="btn_suggest"):
            if suggest_q.strip():
                with st.spinner("Generating suggestions..."):
                    out = ui_run_suggest(backend, suggest_q.strip())
                st.markdown(out)
            else:
                st.warning("Enter a question first.")

    # ── Ask / Route ───────────────────────────────────────────────────────────
    with tab_ask:
        st.markdown(
            '<p style="font-family:var(--body);font-size:0.9rem;color:var(--text-secondary);'
            'margin-bottom:18px">Natural-language requests are routed automatically to the best execution mode — tool or code generation.</p>',
            unsafe_allow_html=True,
        )
        ask_req = st.text_area(
            "Natural-language analysis request",
            placeholder="Example: Plot average passing yards by season",
            key="ask_req",
            height=100,
        )

        if st.button("▶ Route Request", key="btn_route_request"):
            if ask_req.strip():
                with st.spinner("Routing request..."):
                    result = ui_run_router(backend, ask_req.strip())
                st.session_state.last_router_result = result
            else:
                st.warning("Enter a request first.")

        router_result = st.session_state.last_router_result
        if router_result:
            if not router_result.get("ok"):
                st.error(router_result.get("error", "Unknown routing error"))
                st.code(router_result.get("raw", ""), language="json")
            else:
                mode = router_result["mode"]
                st.markdown(
                    f'<div style="display:inline-flex;align-items:center;gap:8px;'
                    f'background:var(--amber-subtle);border:1px solid var(--amber-dim);'
                    f'border-radius:2px;padding:6px 14px;margin-bottom:14px">'
                    f'<span style="font-family:var(--mono);font-size:0.7rem;color:var(--text-muted)">ROUTER MODE</span>'
                    f'<span style="font-family:var(--display);font-size:1rem;font-weight:700;'
                    f'color:var(--amber);text-transform:uppercase">{mode}</span></div>',
                    unsafe_allow_html=True,
                )

                if router_result.get("rag_context"):
                    with st.expander("RAG CONTEXT"):
                        st.code(router_result["rag_context"])

                with st.expander("PARSED ROUTER PLAN", expanded=True):
                    st.code(str(router_result["plan"]), language="python")

                if router_result["mode"] == "tool":
                    if st.button("✓ Approve and Run Tool", key="approve_router_tool"):
                        artifact_snapshot = snapshot_artifact_files(backend)
                        with st.spinner("Running tool..."):
                            run_res = ui_run_tool_from_plan(
                                backend, ask_req.strip(), router_result["plan"]
                            )
                        session_artifacts = list_new_or_modified_artifacts_from_snapshot(
                            backend, artifact_snapshot
                        )
                        run_res["session_artifact_paths"] = [str(p) for p in session_artifacts]
                        st.session_state.last_tool_run_result = run_res

                    tool_run_res = st.session_state.last_tool_run_result
                    if tool_run_res:
                        if tool_run_res.get("ok"):
                            st.success(f"Tool completed: {tool_run_res['tool_name']}")
                            render_generic_tool_output(tool_run_res)
                            st.markdown(tool_run_res["summary"])
                            display_artifacts = merge_tool_display_artifacts(backend, tool_run_res)
                            render_artifacts(display_artifacts, title="Generated Artifacts", prefix="ask_artifact")
                        else:
                            st.error(tool_run_res["error"])

                elif router_result["mode"] == "codegen":
                    code_req = (
                        router_result["plan"].get("codegen_instructions")
                        or router_result["plan"].get("code_request")
                        or ask_req.strip()
                    )
                    if st.button("✓ Approve and Generate Code", key="approve_router_codegen"):
                        with st.spinner("Generating code..."):
                            cg = ui_run_codegen(backend, code_req)
                        st.session_state.last_codegen_result = cg

                    cg = st.session_state.last_codegen_result
                    if cg:
                        if cg.get("rag_context"):
                            with st.expander("CODEGEN RAG CONTEXT"):
                                st.code(cg["rag_context"])
                        with st.expander("PLAN", expanded=True):
                            st.code(cg.get("plan_text", ""), language="text")
                        with st.expander("VERIFICATION CHECKLIST"):
                            st.code(cg.get("verify_text", ""), language="text")
                        if cg.get("code"):
                            st.code(cg["code"], language="python")
                        else:
                            st.error("No Python code block was returned.")

    # ── Tool ──────────────────────────────────────────────────────────────────
    with tab_tool:
        st.markdown(
            '<p style="font-family:var(--body);font-size:0.9rem;color:var(--text-secondary);'
            'margin-bottom:18px">Force tool execution mode — plan and run a specific analysis tool directly.</p>',
            unsafe_allow_html=True,
        )
        tool_req = st.text_area(
            "Tool request (forced tool mode)",
            placeholder="Example: Create a correlation heatmap for offensive metrics",
            key="tool_req",
            height=100,
        )

        if st.button("▶ Plan Tool", key="btn_plan_tool"):
            if tool_req.strip():
                with st.spinner("Planning tool..."):
                    result = ui_plan_tool(backend, tool_req.strip())
                st.session_state.last_tool_plan_result = result
            else:
                st.warning("Enter a request first.")

        tool_plan_result = st.session_state.last_tool_plan_result
        if tool_plan_result:
            with st.expander("RAW PLANNER OUTPUT", expanded=False):
                st.code(tool_plan_result["raw"], language="json")
            with st.expander("PARSED PLAN", expanded=True):
                st.code(str(tool_plan_result["plan"]), language="python")

            if st.button("✓ Approve and Run Planned Tool", key="btn_run_planned_tool"):
                plan = tool_plan_result["plan"]
                if not plan:
                    st.error("Planner did not return valid JSON.")
                else:
                    artifact_snapshot = snapshot_artifact_files(backend)
                    with st.spinner("Running tool..."):
                        run_res = ui_run_tool_from_plan(backend, tool_req.strip(), plan)
                    session_artifacts = list_new_or_modified_artifacts_from_snapshot(
                        backend, artifact_snapshot
                    )
                    run_res["session_artifact_paths"] = [str(p) for p in session_artifacts]
                    st.session_state.last_tool_run_result = run_res

            tool_run_res = st.session_state.last_tool_run_result
            if tool_run_res:
                if tool_run_res.get("ok"):
                    st.success(f"Tool completed: {tool_run_res['tool_name']}")
                    render_generic_tool_output(tool_run_res)
                    st.markdown(tool_run_res["summary"])
                    display_artifacts = merge_tool_display_artifacts(backend, tool_run_res)
                    render_artifacts(display_artifacts, title="Generated Artifacts", prefix="tool_artifact")
                else:
                    st.error(tool_run_res["error"])

    # ── Code Gen ──────────────────────────────────────────────────────────────
    with tab_code:
        st.markdown(
            '<p style="font-family:var(--body);font-size:0.9rem;color:var(--text-secondary);'
            'margin-bottom:18px">Force code generation mode — produce a Python script for any analysis request.</p>',
            unsafe_allow_html=True,
        )
        code_req = st.text_area(
            "Code generation request (forced codegen mode)",
            placeholder="Example: Use SQL to compare average passing yards by season and team, then save a chart",
            key="code_req",
            height=100,
        )

        if st.button("▶ Generate Code", key="btn_generate_code"):
            if code_req.strip():
                with st.spinner("Generating code..."):
                    cg = ui_run_codegen(backend, code_req.strip())
                st.session_state.last_codegen_result = cg
            else:
                st.warning("Enter a request first.")

        cg = st.session_state.last_codegen_result
        if cg:
            if cg.get("rag_context"):
                with st.expander("CODEGEN RAG CONTEXT"):
                    st.code(cg["rag_context"])
            with st.expander("PLAN", expanded=True):
                st.code(cg.get("plan_text", ""), language="text")
            with st.expander("VERIFICATION CHECKLIST"):
                st.code(cg.get("verify_text", ""), language="text")

            if cg.get("code"):
                st.code(cg["code"], language="python")
            else:
                st.error("No Python code block returned.")

        if cg and cg.get("code"):
            if st.button("✓ Approve and Save Script", key="btn_save_generated_code"):
                saved_path = ui_save_generated_code(backend, cg["code"])
                st.success(f"Script saved: {saved_path}")
                render_artifacts([saved_path], title="Saved Script", prefix="saved_script")

    # ── Execute ───────────────────────────────────────────────────────────────
    with tab_run:
        st.markdown(
            '<p style="font-family:var(--body);font-size:0.9rem;color:var(--text-secondary);'
            'margin-bottom:18px">Execute the last approved and saved generated script in a subprocess.</p>',
            unsafe_allow_html=True,
        )

        if st.button("▶ Run Saved Script", key="btn_run_saved_code"):
            report_snapshot = snapshot_report_files(Path(backend["report_dir"]))
            with st.spinner("Executing script..."):
                run_res = ui_run_saved_code(backend, timeout_s=int(timeout_s))
            session_artifacts = list_new_or_modified_artifacts(
                Path(backend["report_dir"]), report_snapshot
            )
            run_res["session_artifact_paths"] = [str(p) for p in session_artifacts]
            st.session_state.last_execute_result = run_res

        run_res = st.session_state.last_execute_result
        if run_res:
            if run_res["ok"]:
                st.success(f"Execution complete · Return code: {run_res['returncode']}")

                col_out, col_err = st.columns(2)
                with col_out:
                    with st.expander("STDOUT", expanded=bool(run_res["stdout"])):
                        st.code(run_res["stdout"] or "(empty)", language="text")
                with col_err:
                    with st.expander("STDERR", expanded=bool(run_res["stderr"])):
                        st.code(run_res["stderr"] or "(empty)", language="text")

                session_artifacts = run_res.get("session_artifact_paths", []) or []
                backend_artifacts = run_res.get("artifact_paths", []) or []
                display_artifacts = merge_unique_paths(session_artifacts, backend_artifacts)
                render_artifacts(display_artifacts, title="Generated Artifacts", prefix="exec_artifact")
                render_artifacts([run_res["run_log_path"]], title="Execution Log", prefix="exec_log")
            else:
                st.error(run_res["error"])

    # ── Reports ───────────────────────────────────────────────────────────────
    with tab_reports:
        st.markdown(
            '<p style="font-family:var(--body);font-size:0.9rem;color:var(--text-secondary);'
            'margin-bottom:18px">All saved reports, figures, and data artifacts from this session.</p>',
            unsafe_allow_html=True,
        )
        report_dir = Path(backend["report_dir"])
        zip_path = make_report_zip(report_dir)
        if zip_path and zip_path.exists():
            render_download_button(zip_path, prefix="reports_zip", instance_id="all")

        render_figure_gallery(report_dir, prefix="reports_figure")
        render_report_browser(report_dir)

else:
    st.markdown(
        '<div style="border:1px solid var(--border);border-left:3px solid var(--amber-dim);'
        'background:var(--amber-subtle);border-radius:2px;padding:16px 20px;margin-top:8px">'
        '<span style="font-family:var(--mono);font-size:0.82rem;color:var(--amber)">'
        'Configure your dataset and model in the sidebar, then click InInitialize Agent to unlock the command interface.'
        '</span></div>',
        unsafe_allow_html=True,
    )