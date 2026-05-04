from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from typing import Iterable, Optional, Sequence, Union

import pandas as pd

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def quote_ident(name: str) -> str:
    """Safely quote a SQLite identifier after validating the column/table name."""
    if not isinstance(name, str) or not _IDENTIFIER_RE.match(name):
        raise ValueError(f"Unsafe or invalid SQL identifier: {name!r}")
    return '"' + name.replace('"', '""') + '"'


def resolve_db_path(df: Optional[pd.DataFrame] = None, db_path: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """Resolve the SQLite database path from an explicit arg, df.attrs, or environment."""
    raw = db_path
    if raw is None and df is not None:
        raw = df.attrs.get("sqlite_db_path") or df.attrs.get("db_path")
    if raw is None:
        raw = os.environ.get("BUILD4_SQLITE_DB_PATH")
    if not raw:
        return None
    p = Path(raw)
    return p if p.exists() else None


def sqlite_available(df: Optional[pd.DataFrame] = None, db_path: Optional[Union[str, Path]] = None) -> bool:
    return resolve_db_path(df, db_path) is not None


def read_sql(
    query: str,
    df: Optional[pd.DataFrame] = None,
    db_path: Optional[Union[str, Path]] = None,
    params: Optional[Sequence[object]] = None,
) -> pd.DataFrame:
    path = resolve_db_path(df, db_path)
    if path is None:
        raise FileNotFoundError("SQLite database path was not provided or does not exist.")
    with sqlite3.connect(str(path)) as conn:
        return pd.read_sql_query(query, conn, params=params or [])


def load_columns(
    df: pd.DataFrame,
    columns: Iterable[str],
    db_path: Optional[Union[str, Path]] = None,
    table_name: str = "nfl_data",
    drop_missing_subset: Optional[Iterable[str]] = None,
) -> tuple[pd.DataFrame, str]:
    """Load selected columns from SQLite when available; otherwise return df subset.

    Returns (dataframe, source_label) where source_label is "sqlite" or "dataframe".
    """
    cols = list(dict.fromkeys([str(c) for c in columns]))
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Column(s) not found: {missing}")

    path = resolve_db_path(df, db_path)
    if path is not None:
        q_cols = ", ".join(quote_ident(c) for c in cols)
        q_table = quote_ident(table_name)
        query = f"SELECT {q_cols} FROM {q_table}"
        out = read_sql(query, db_path=path)
        if drop_missing_subset:
            out = out.dropna(subset=list(drop_missing_subset))
        return out, "sqlite"

    out = df[cols].copy()
    if drop_missing_subset:
        out = out.dropna(subset=list(drop_missing_subset))
    return out, "dataframe"


def dataframe_source_note(source: str) -> str:
    if source == "sqlite":
        return "Source: SQLite database table `nfl_data`."
    return "Source: in-memory dataframe fallback."
