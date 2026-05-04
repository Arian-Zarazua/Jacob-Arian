from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Union
import json

import pandas as pd

from src.sql_support import load_columns, dataframe_source_note


def assert_json_safe(obj: Any, context: str = "") -> None:
    """Raise a TypeError if obj cannot be serialized to JSON."""
    try:
        json.dumps(obj)
    except TypeError as e:
        msg = "Object not JSON-serializable"
        if context:
            msg += f" ({context})"
        raise TypeError(msg) from e


def target_check(
    df: pd.DataFrame,
    target: str,
    db_path: Optional[Union[str, Path]] = None,
    table_name: str = "nfl_data",
) -> Dict[str, Any]:
    """Return basic information about a target column, using SQLite when available."""
    if target not in df.columns:
        raise ValueError(f"Target column '{target}' not found in dataframe.")
    work_df, source = load_columns(df, [target], db_path=db_path, table_name=table_name)
    s = work_df[target]
    out: Dict[str, Any] = {
        "target": str(target),
        "dtype": str(df[target].dtype),
        "n_rows": int(len(s)),
        "n_missing": int(s.isna().sum()),
        "missing_rate": float(s.isna().mean()),
        "source": source,
        "source_note": dataframe_source_note(source),
    }
    numeric_s = pd.to_numeric(s, errors="coerce")
    if pd.api.types.is_numeric_dtype(df[target]) or numeric_s.notna().sum() >= max(1, int(0.8 * s.notna().sum())):
        desc = numeric_s.describe()
        out["numeric_summary"] = {
            "count": float(desc.get("count", float("nan"))),
            "mean": float(desc.get("mean", float("nan"))),
            "std": float(desc.get("std", float("nan"))),
            "min": float(desc.get("min", float("nan"))),
            "p25": float(desc.get("25%", float("nan"))),
            "median": float(desc.get("50%", float("nan"))),
            "p75": float(desc.get("75%", float("nan"))),
            "max": float(desc.get("max", float("nan"))),
        }
    else:
        top = s.astype("string").value_counts(dropna=True).head(10)
        out["top_values"] = [{"value": str(k), "count": int(v)} for k, v in top.items()]
    return out
