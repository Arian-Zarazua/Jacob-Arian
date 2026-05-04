from __future__ import annotations

from typing import List, Optional, Dict, Any, Tuple, cast, Union
from pathlib import Path
from math import atanh, tanh, sqrt

import pandas as pd
from scipy import stats

from src.sql_support import load_columns, dataframe_source_note
from src.utils.tool_result_utils import make_tool_result, ToolResult


def summarize_numeric(
    df: pd.DataFrame,
    numeric_cols: Optional[List[str]] = None,
    column: Optional[str] = None,
    db_path: Optional[Union[str, Path]] = None,
    table_name: str = "nfl_data",
) -> pd.DataFrame:
    """Compute descriptive statistics for numeric columns, reading from SQLite when available."""
    if numeric_cols is not None and column is not None:
        raise ValueError("Provide only one of: 'numeric_cols' or 'column'.")
    if numeric_cols is None:
        if column is None:
            raise ValueError("Provide either 'numeric_cols' or 'column'.")
        numeric_cols = [column]
    if not numeric_cols:
        return pd.DataFrame(columns=["column", "count", "mean", "std", "min", "p25", "median", "p75", "max", "source"])

    work_df, source = load_columns(df, numeric_cols, db_path=db_path, table_name=table_name)
    for c in numeric_cols:
        work_df[c] = pd.to_numeric(work_df[c], errors="coerce")
    summary = work_df[numeric_cols].describe(percentiles=[0.25, 0.5, 0.75]).T
    summary = summary.rename(columns={"50%": "median", "25%": "p25", "75%": "p75"})
    summary.insert(0, "column", summary.index.astype(str))
    summary["source"] = source
    summary.reset_index(drop=True, inplace=True)
    return summary


def summarize_categorical(
    df: pd.DataFrame,
    cat_cols: List[str] | None = None,
    column: str | None = None,
    top_k: int = 10,
    db_path: Optional[Union[str, Path]] = None,
    table_name: str = "nfl_data",
) -> pd.DataFrame:
    """Compute categorical summaries, reading selected columns from SQLite when available."""
    if cat_cols is None:
        if column is None:
            raise ValueError("Provide either 'column' or 'cat_cols'.")
        cat_cols = [column]
    work_df, source = load_columns(df, cat_cols, db_path=db_path, table_name=table_name)

    rows = []
    for c in cat_cols:
        series = work_df[c].astype("string")
        n = int(series.shape[0])
        n_missing = int(series.isna().sum())
        n_unique = int(series.nunique(dropna=True))
        top = series.value_counts(dropna=True).head(top_k)
        rows.append({
            "column": c,
            "count": n,
            "missing": n_missing,
            "unique": n_unique,
            "top_values": "; ".join([f"{idx} ({val})" for idx, val in top.items()]),
            "source": source,
        })
    return pd.DataFrame(rows)


def missingness_table(
    df: pd.DataFrame,
    db_path: Optional[Union[str, Path]] = None,
    table_name: str = "nfl_data",
) -> pd.DataFrame:
    """Create a missingness table. Uses SQLite column reads when db_path is available."""
    # For this operation, pandas is still the safest because columns may be numerous/mixed.
    # If df is a backend dataframe loaded from the same SQLite database, this remains accurate.
    missing_rate = df.isna().mean()
    missing_count = df.isna().sum()
    out = pd.DataFrame({
        "column": missing_rate.index.astype(str),
        "missing_rate": missing_rate.values.astype(float),
        "missing_count": missing_count.values.astype(int),
    }).sort_values("missing_rate", ascending=False, ignore_index=True)
    out["source"] = "dataframe"
    return out


def pearson_correlation(
    df: pd.DataFrame,
    x: str,
    y: str,
    ci_level: float = 0.95,
    min_n_recommendation: int = 30,
    db_path: Optional[Union[str, Path]] = None,
    table_name: str = "nfl_data",
) -> ToolResult:
    """Compute Pearson correlation statistics between two numeric variables."""
    pair_df, source = load_columns(df, [x, y], db_path=db_path, table_name=table_name, drop_missing_subset=[x, y])
    pair_df[x] = pd.to_numeric(pair_df[x], errors="coerce")
    pair_df[y] = pd.to_numeric(pair_df[y], errors="coerce")
    pair_df = pair_df.dropna()
    n = int(len(pair_df))
    if n < 10:
        raise ValueError("Need at least 10 complete observations to compute CI and p-value.")

    r, p_value = cast(Tuple[float, float], stats.pearsonr(pair_df[x].to_numpy(), pair_df[y].to_numpy()))
    r = float(r); p_value = float(p_value); r2 = r * r
    eps = 1e-12
    r_clip = max(min(r, 1 - eps), -1 + eps)
    z = atanh(r_clip)
    se = 1.0 / sqrt(n - 3)
    alpha = 1.0 - ci_level
    zcrit = float(stats.norm.ppf(1 - alpha / 2))
    ci_low = float(tanh(z - zcrit * se))
    ci_high = float(tanh(z + zcrit * se))

    methods_note = (
        "Methods: Rows with missing or non-numeric values were dropped. Pearson r and two-sided p-value "
        "computed using scipy.stats.pearsonr. Confidence interval computed via Fisher z-transform with SE=1/sqrt(n-3). "
        f"A common rule of thumb is n ≥ {min_n_recommendation} for more stable confidence interval estimates. "
        f"{dataframe_source_note(source)}"
    )
    text = (
        f"Pearson correlation between '{x}' and '{y}': r = {r:.4f} "
        f"({int(ci_level * 100)}% CI [{ci_low:.4f}, {ci_high:.4f}]), "
        f"r² = {r2:.4f}, p = {p_value:.4g}, n = {n}.\n\n{methods_note}"
    )
    return make_tool_result(
        name="pearson_correlation",
        text=text,
        artifact_paths=[],
        structured={"x": x, "y": y, "n": n, "r": r, "r2": r2, "ci_level": ci_level, "ci_low": ci_low, "ci_high": ci_high, "p_value": p_value, "source": source},
    )
