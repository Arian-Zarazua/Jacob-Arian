from __future__ import annotations

from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional, Union

import pandas as pd

from src.sql_support import resolve_db_path, read_sql


def basic_profile(
    df: pd.DataFrame,
    db_path: Optional[Union[str, Path]] = None,
    table_name: str = "nfl_data",
) -> Dict[str, Any]:
    """Return a basic JSON-serializable profile. Includes SQLite source metadata when available."""
    path = resolve_db_path(df, db_path)
    row_count = int(df.shape[0])
    source = "dataframe"
    if path is not None:
        try:
            count_df = read_sql(f'SELECT COUNT(*) AS n FROM "{table_name}"', db_path=path)
            row_count = int(count_df.loc[0, "n"])
            source = "sqlite"
        except Exception:
            source = "dataframe"
    return {
        "n_rows": row_count,
        "n_cols": int(df.shape[1]),
        "columns": df.columns.tolist(),
        "dtypes": {c: str(df[c].dtype) for c in df.columns},
        "n_missing_total": int(df.isna().sum().sum()),
        "missing_by_col": df.isna().sum().to_dict(),
        "memory_mb": float(df.memory_usage(deep=True).sum() / (1024**2)),
        "source": source,
        "sqlite_db_path": str(path) if path is not None else None,
    }


def split_columns(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """Identify and split numeric vs categorical columns."""
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = [c for c in df.columns if c not in numeric_cols]
    return numeric_cols, cat_cols
