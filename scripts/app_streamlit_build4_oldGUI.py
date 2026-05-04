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


import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

# Add project root to Python path for findingbuilds folder and importing src modules;
sys.path.append(str(Path(__file__).resolve().parents[1]))

# IMPORTANT:
# This import assumes your backend file is named exactly:
# builds/build4_rag_router_agent_streamlit.py
# If your local file has a different name, rename it first.
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

st.set_page_config(page_title="NFL Data Agent", page_icon="🏈", layout="wide")

st.title("🏈 NFL Data Analysis Agent")
st.caption(
    "Analyze Pro Football Reference / NFL CSV datasets with routing, RAG, tools, "
    "SQLite-backed code generation, and in-app figure previews."
)

st.info(
    "Load either one CSV, multiple CSVs, or a local folder path containing CSV files. "
    "Then click **Initialize Agent**. The app will also build a local SQLite database for dynamic SQL analysis."
)
# -----------------------------------------------------------------------------
# Session state: Memory that holds the backend object, last router result, last tool plan,
# last tool run result, and last generated code so actions can happen across
# multiple button clicks
# -----------------------------------------------------------------------------
if "backend" not in st.session_state:
    st.session_state.backend = None

if "uploaded_data_path" not in st.session_state:
    st.session_state.uploaded_data_path = None

if "loaded_file_count" not in st.session_state:
    st.session_state.loaded_file_count = 0

if "last_codegen_result" not in st.session_state:
    st.session_state.last_codegen_result = None

if "last_router_result" not in st.session_state:
    st.session_state.last_router_result = None

if "last_tool_plan_result" not in st.session_state:
    st.session_state.last_tool_plan_result = None

if "last_tool_run_result" not in st.session_state:
    st.session_state.last_tool_run_result = None

if "last_execute_result" not in st.session_state:
    st.session_state.last_execute_result = None

if "backend_signature" not in st.session_state:
    st.session_state.backend_signature = None


# -----------------------------------------------------------------------------
# Small helpers
# -----------------------------------------------------------------------------
def save_uploaded_csv(uploaded_file) -> Path:
    tmp_dir = Path(tempfile.gettempdir()) / "build4_streamlit_uploads"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    out_path = tmp_dir / uploaded_file.name
    with open(out_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.session_state.loaded_file_count = 1
    return out_path


def save_uploaded_csv_folder(uploaded_files) -> Path:
    """Save multiple uploaded CSVs into a temp folder and return that folder path."""
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
            label=f"Download {path.name}",
            data=f.read(),
            file_name=path.name,
            key=f"download_{prefix}_{instance_id}_{path.name}_{path.stat().st_mtime_ns}",
            width="content",
        )


def render_single_artifact(
    path: Path,
    prefix: str = "artifact",
    instance_id: str = "0",
) -> None:
    if not path.exists():
        st.warning(f"Missing artifact: {path}")
        return

    st.markdown(f"**{path.name}**")
    st.caption(str(path))

    suffix = path.suffix.lower()

    try:
        if suffix in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
            st.image(str(path), caption=path.name, width="stretch")

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


def render_artifacts(
    artifact_paths,
    title: str = "Artifacts",
    prefix: str = "artifact",
) -> None:
    if not artifact_paths:
        st.info("No artifacts were produced.")
        return

    st.subheader(title)

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


def list_report_files(report_dir: Path) -> list[Path]:
    if not report_dir.exists():
        return []

    return sorted(
        [p for p in report_dir.rglob("*") if p.is_file()],
        key=lambda p: str(p).lower(),
    )




def list_figure_files(report_dir: Path) -> list[Path]:
    """Return image files saved by generated code/tools so Streamlit can display them inline."""
    if not report_dir.exists():
        return []

    image_suffixes = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
    return sorted(
        [p for p in report_dir.rglob("*") if p.is_file() and p.suffix.lower() in image_suffixes],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def snapshot_report_files(report_dir: Path) -> dict[str, int]:
    """Capture current report files so one UI action can show only new/changed outputs."""
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
    """Return only files created or modified after a single button-triggered run."""
    if not report_dir.exists():
        return []

    if include_suffixes is None:
        include_suffixes = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".csv"}

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




ARTIFACT_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".csv"}


def get_artifact_search_roots(backend: dict) -> list[Path]:
    """Return likely artifact roots, including fallback folders used by older tools."""
    roots: list[Path] = []

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

    seen: set[str] = set()
    add(backend.get("report_dir"))

    # Common fallback paths when older plotting tools save relative to the app CWD.
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
    """Snapshot likely artifact files before a run, across multiple possible output roots."""
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
    """Find artifacts changed by a tool run, even if the tool saved in a fallback folder."""
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
    """Combine reported artifacts, per-run discovered artifacts, and existing valid paths."""
    return merge_unique_paths(
        run_res.get("session_artifact_paths", []) or [],
        run_res.get("artifact_paths", []) or [],
    )


def merge_unique_paths(*path_groups) -> list[Path]:
    """Merge path-like values without duplicates while preserving order."""
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
    """Render generated figures directly in the Streamlit UI."""
    figure_paths = list_figure_files(report_dir)

    if not figure_paths:
        st.info("No generated figures were found in the report directory yet.")
        return

    render_artifacts(
        figure_paths,
        title="Generated Figures",
        prefix=prefix,
    )

def render_report_browser(report_dir: Path) -> None:
    if not report_dir.exists():
        st.info(f"Report directory does not exist yet: {report_dir}")
        return

    report_files = list_report_files(report_dir)

    if not report_files:
        st.info("No saved reports or artifacts were found yet.")
        return

    st.caption(f"Report directory: {report_dir}")

    render_artifacts(
        report_files,
        title="All Saved Files",
        prefix="reports_artifact",
    )




def render_sqlite_database_info(backend: dict) -> None:
    """Render SQLite build metadata and validation checks in one dashboard section."""
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

    status_label = "Verified" if v_ok else "Needs attention"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("SQLite status", status_label)
    c2.metric("DB file exists", "Yes" if exists else "No")
    c3.metric("Tables/views", f"{len(schema_objects):,}")
    c4.metric("nfl_data rows", f"{row_counts.get('nfl_data', 0):,}" if isinstance(row_counts.get('nfl_data', 0), int) else str(row_counts.get('nfl_data', 'n/a')))

    st.caption(f"Database path: `{db_path}`")
    if db_path.exists():
        render_download_button(db_path, prefix="sqlite_db", instance_id="main")

    if validation.get("error"):
        st.error(validation["error"])
    elif v_ok:
        st.success("SQLite integrity check passed, no foreign-key issues were found, and tables are queryable.")
    else:
        st.warning("SQLite database was created, but one or more verification checks needs review.")

    with st.expander("Verification checks", expanded=True):
        check_df = pd.DataFrame(
            [
                {
                    "check": "PRAGMA integrity_check",
                    "result": str(integrity or "not run"),
                    "passed": integrity == [("ok",)] or integrity == [["ok"]],
                },
                {
                    "check": "PRAGMA foreign_key_check",
                    "result": "no issues" if not fk_issues else str(fk_issues),
                    "passed": not bool(fk_issues),
                },
                {
                    "check": "Table row counts",
                    "result": f"{len(row_counts)} tables counted",
                    "passed": bool(row_counts),
                },
            ]
        )
        st.dataframe(check_df, width="stretch", hide_index=True)


    with st.expander("LLM SQL context"):
        st.text(backend.get("sqlite_schema_text", "SQLite metadata not available."))




# -----------------------------------------------------------------------------
# Sidebar controls
# -----------------------------------------------------------------------------
st.sidebar.header("Get Started")
st.sidebar.markdown(
    """
    Select agent parameters and input data sets
    """
)

model = st.sidebar.text_input("Model", value="gpt-4o-mini")
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.2, 0.05)
stream = st.sidebar.toggle("Streaming", value=False)
memory = st.sidebar.toggle("Conversation Memory", value=False)
timeout_s = st.sidebar.number_input(
    "Execution timeout (seconds)", min_value=10, max_value=600, value=60, step=10
)

report_dir_str = st.sidebar.text_input("Report directory", value="reports_streamlit")

# -----------------------------------------------------------------------------
# RAG directory dropdown
# -----------------------------------------------------------------------------
def get_default_knowledge_root() -> Path:
    """Return a reasonable default knowledge root without hard-failing on other machines."""
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
    rag_options = ["None"] + sorted(
        [p.name for p in knowledge_root.iterdir() if p.is_dir()]
    )
else:
    rag_options = ["None"]
    st.sidebar.warning(f"Knowledge folder not found: {knowledge_root}")

selected_rag = st.sidebar.selectbox(
    "Knowledge folder for RAG",
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

st.sidebar.divider()
st.sidebar.subheader("Dataset")
data_mode = st.sidebar.radio(
    "How do you want to load data?",
    ["Upload one CSV", "Upload multiple CSVs", "Use local folder path"],
    index=1,
)

if data_mode == "Upload one CSV":
    uploaded_file = st.sidebar.file_uploader("Upload a CSV dataset", type=["csv"], key="one_csv")
    if uploaded_file is not None:
        st.session_state.uploaded_data_path = save_uploaded_csv(uploaded_file)
        st.sidebar.success(f"Uploaded: {uploaded_file.name}")

elif data_mode == "Upload multiple CSVs":
    uploaded_files = st.sidebar.file_uploader(
        "Upload CSV files",
        type=["csv"],
        accept_multiple_files=True,
        key="many_csvs",
        help="Use this for a folder's worth of CSVs. Streamlit saves them into one temporary folder.",
    )
    if uploaded_files:
        st.session_state.uploaded_data_path = save_uploaded_csv_folder(uploaded_files)
        st.sidebar.success(f"Loaded {len(uploaded_files)} CSV files as one dataset folder.")

else:
    local_folder = st.sidebar.text_input(
        "Local CSV folder path",
        value="data/Pro-Football-Reference/Stats",
        help="Path must exist on the machine running Streamlit.",
    )
    if local_folder.strip():
        st.session_state.uploaded_data_path = Path(local_folder.strip())
        st.session_state.loaded_file_count = 0
        st.sidebar.caption(f"Using path: {st.session_state.uploaded_data_path}")

init_clicked = st.sidebar.button("Initialize Agent", width="stretch")

if init_clicked:
    if st.session_state.uploaded_data_path is None:
        st.sidebar.error("Please upload a CSV file first.")
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
            st.success("Agent initialized successfully.")
        except Exception as e:
            st.error(f"Initialization failed: {e}")

backend = st.session_state.backend


# -----------------------------------------------------------------------------
# Dataset + schema
# -----------------------------------------------------------------------------
st.header("1) Dataset and Schema")

if backend is None:
    st.info("Upload a CSV and click 'Initialize Agent' in the sidebar.")
else:
    df = backend["df"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Rows", f"{len(df):,}")
    m2.metric("Columns", f"{df.shape[1]:,}")
    loaded_count = st.session_state.backend_signature.get("loaded_file_count") or (df["_source_file"].nunique() if "_source_file" in df.columns else 1)
    m3.metric("CSV files", str(loaded_count))
    m4.metric("Missing cells", f"{int(df.isna().sum().sum()):,}")

    if "_source_file" in df.columns:
        with st.expander("Loaded CSV files"):
            st.dataframe(df["_source_file"].value_counts().rename_axis("source_file").reset_index(name="rows"), width="stretch")

    left, right = st.columns([1, 1])

    with right:
        st.subheader("Preview")
        st.dataframe(df.head(20), width="stretch")

    with left:
        st.subheader("Column details")
        schema_df = pd.DataFrame(
                {
                    "column": list(df.columns),
                    "dtype": [str(df[c].dtype) for c in df.columns],
                    "missing_n": [int(df[c].isna().sum()) for c in df.columns],
                }
            )
        st.dataframe(
                schema_df,
                width="stretch",
            )

    st.subheader("SQLite database verification")
    render_sqlite_database_info(backend)

    with st.expander("Loaded tools"):
        st.write(backend["allowed_tools"])


# -----------------------------------------------------------------------------
# Command interface
# -----------------------------------------------------------------------------
st.header("2) Agent Commands")

if backend is not None:
    tab_suggest, tab_ask, tab_tool, tab_code, tab_run, tab_reports = st.tabs(
        ["Suggest", "Ask", "Tool", "Code", "Run", "Reports"]
    )

    # -----------------------------------------------------------------
    # Suggest
    # -----------------------------------------------------------------
    with tab_suggest:
        st.subheader("suggest")
        suggest_q = st.text_area(
            "Enter a dataset question or ask for possible analyses",
            placeholder="Example: What are 3 good research questions I can test with this dataset?",
            key="suggest_q",
        )

        if st.button("Run suggest", key="btn_suggest"):
            if suggest_q.strip():
                with st.spinner("Generating suggestions..."):
                    out = ui_run_suggest(backend, suggest_q.strip())
                st.markdown(out)
            else:
                st.warning("Enter a question first.")

    # -----------------------------------------------------------------
    # Ask
    # -----------------------------------------------------------------
    with tab_ask:
        st.subheader("ask")
        ask_req = st.text_area(
            "Natural-language request for the router",
            placeholder="Example: Plot average passing yards by season",
            key="ask_req",
        )

        if st.button("Route request", key="btn_route_request"):
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
                st.write(f"**Router mode:** {router_result['mode']}")

                if router_result.get("rag_context"):
                    with st.expander("Router RAG context"):
                        st.text(router_result["rag_context"])

                st.write("**Parsed router plan**")
                st.code(str(router_result["plan"]), language="python")

                if router_result["mode"] == "tool":
                    if st.button("Approve and run tool", key="approve_router_tool"):
                        artifact_snapshot = snapshot_artifact_files(backend)
                        with st.spinner("Running tool..."):
                            run_res = ui_run_tool_from_plan(
                                backend,
                                ask_req.strip(),
                                router_result["plan"],
                            )
                        session_artifacts = list_new_or_modified_artifacts_from_snapshot(
                            backend, artifact_snapshot
                        )
                        run_res["session_artifact_paths"] = [str(p) for p in session_artifacts]
                        st.session_state.last_tool_run_result = run_res

                    tool_run_res = st.session_state.last_tool_run_result
                    if tool_run_res:
                        if tool_run_res.get("ok"):
                            st.success(f"Tool ran: {tool_run_res['tool_name']}")
                            st.write("**Tool output**")
                            st.text(tool_run_res["tool_text"])
                            st.write("**Summary**")
                            st.markdown(tool_run_res["summary"])
                            display_artifacts = merge_tool_display_artifacts(backend, tool_run_res)
                            render_artifacts(
                                display_artifacts,
                                title="Artifacts generated by this tool run",
                                prefix="ask_artifact",
                            )
                        else:
                            st.error(tool_run_res["error"])

                elif router_result["mode"] == "codegen":
                    code_req = (
                        router_result["plan"].get("codegen_instructions")
                        or router_result["plan"].get("code_request")
                        or ask_req.strip()
                    )
                    if st.button(
                        "Approve and generate code", key="approve_router_codegen"
                    ):
                        with st.spinner("Generating code..."):
                            cg = ui_run_codegen(backend, code_req)
                        st.session_state.last_codegen_result = cg

                    cg = st.session_state.last_codegen_result
                    if cg:
                        if cg.get("rag_context"):
                            with st.expander("Codegen RAG context"):
                                st.text(cg["rag_context"])

                        st.write("**Plan**")
                        st.text(cg.get("plan_text", ""))
                        st.write("**Verification checklist**")
                        st.text(cg.get("verify_text", ""))

                        if cg.get("code"):
                            st.code(cg["code"], language="python")
                        else:
                            st.error("No Python code block was returned.")

    # -----------------------------------------------------------------
    # Tool
    # -----------------------------------------------------------------
    with tab_tool:
        st.subheader("tool")
        tool_req = st.text_area(
            "Force tool mode",
            placeholder="Example: Create a correlation heatmap for offensive metrics",
            key="tool_req",
        )

        if st.button("Plan tool", key="btn_plan_tool"):
            if tool_req.strip():
                with st.spinner("Planning tool..."):
                    result = ui_plan_tool(backend, tool_req.strip())
                st.session_state.last_tool_plan_result = result
            else:
                st.warning("Enter a request first.")

        tool_plan_result = st.session_state.last_tool_plan_result
        if tool_plan_result:
            st.write("**Raw planner output**")
            st.code(tool_plan_result["raw"], language="json")

            st.write("**Parsed plan**")
            st.code(str(tool_plan_result["plan"]), language="python")

            if st.button("Approve and run planned tool", key="btn_run_planned_tool"):
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
                    st.success(f"Tool ran: {tool_run_res['tool_name']}")
                    st.write("**Tool output**")
                    st.text(tool_run_res["tool_text"])
                    st.write("**Summary**")
                    st.markdown(tool_run_res["summary"])
                    display_artifacts = merge_tool_display_artifacts(backend, tool_run_res)
                    render_artifacts(
                        display_artifacts,
                        title="Artifacts generated by this tool run",
                        prefix="tool_artifact",
                    )
                else:
                    st.error(tool_run_res["error"])

    # -----------------------------------------------------------------
    # Code
    # -----------------------------------------------------------------
    with tab_code:
        st.subheader("code")
        code_req = st.text_area(
            "Force code generation",
            placeholder="Example: Use SQL to compare average passing yards by season and team, then save a chart",
            key="code_req",
        )

        if st.button("Generate code", key="btn_generate_code"):
            if code_req.strip():
                with st.spinner("Generating code..."):
                    cg = ui_run_codegen(backend, code_req.strip())
                st.session_state.last_codegen_result = cg
            else:
                st.warning("Enter a request first.")

        cg = st.session_state.last_codegen_result
        if cg:
            if cg.get("rag_context"):
                with st.expander("Codegen RAG context"):
                    st.text(cg["rag_context"])

            st.write("**Plan**")
            st.text(cg.get("plan_text", ""))
            st.write("**Verification checklist**")
            st.text(cg.get("verify_text", ""))

            if cg.get("code"):
                st.code(cg["code"], language="python")
            else:
                st.error("No Python code block returned.")

        if cg and cg.get("code"):
            if st.button(
                "Approve and save generated code", key="btn_save_generated_code"
            ):
                saved_path = ui_save_generated_code(backend, cg["code"])
                st.success(f"Saved to: {saved_path}")
                render_artifacts(
                    [saved_path],
                    title="Saved Script",
                    prefix="saved_script",
                )

    # -----------------------------------------------------------------
    # Run
    # -----------------------------------------------------------------
    with tab_run:
        st.subheader("run")
        st.write("Execute the last approved and saved generated script.")

        if st.button("Run saved code", key="btn_run_saved_code"):
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
                st.success(f"Finished. Return code: {run_res['returncode']}")
                st.write("**STDOUT**")
                st.text(run_res["stdout"] or "(empty)")
                st.write("**STDERR**")
                st.text(run_res["stderr"] or "(empty)")
                session_artifacts = run_res.get("session_artifact_paths", []) or []
                backend_artifacts = run_res.get("artifact_paths", []) or []
                display_artifacts = merge_unique_paths(session_artifacts, backend_artifacts)

                render_artifacts(
                    display_artifacts,
                    title="Artifacts generated by this run",
                    prefix="exec_artifact",
                )

                render_artifacts(
                    [run_res["run_log_path"]],
                    title="Execution Log",
                    prefix="exec_log",
                )
            else:
                st.error(run_res["error"])

    # -----------------------------------------------------------------
    # Reports
    # -----------------------------------------------------------------
    with tab_reports:
        st.subheader("Saved reports and artifacts")
        report_dir = Path(backend["report_dir"])
        zip_path = make_report_zip(report_dir)
        if zip_path and zip_path.exists():
            render_download_button(zip_path, prefix="reports_zip", instance_id="all")

        render_figure_gallery(report_dir, prefix="reports_figure")
        render_report_browser(report_dir)

else:
    st.info("Click **Initialize Agent** to unlock the command tabs.")