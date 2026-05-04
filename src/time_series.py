"""Time series and temporal aggregation tools for data analysis."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

import pandas as pd
import matplotlib.pyplot as plt

from src.sql_support import load_columns, dataframe_source_note
from src.utils.tool_result_utils import ToolResult, make_tool_result


def aggregate_by_temporal_column(
    df: pd.DataFrame,
    temporal_column: str,
    numeric_columns: List[str],
    aggregation_method: str = "mean",
    db_path: Optional[Union[str, Path]] = None,
    table_name: str = "nfl_data",
) -> ToolResult:
    """Aggregate numeric columns by a temporal column, reading from SQLite when available."""
    if temporal_column not in df.columns:
        raise ValueError(f"Temporal column '{temporal_column}' not found in dataframe.")
    if not numeric_columns:
        raise ValueError("Must specify at least one numeric column to aggregate.")
    missing_cols = [col for col in numeric_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Numeric columns not found: {missing_cols}")

    valid_methods = ["mean", "sum", "median", "min", "max", "std", "count"]
    if aggregation_method not in valid_methods:
        raise ValueError(f"Aggregation method '{aggregation_method}' not supported. Use one of: {', '.join(valid_methods)}")

    work_df, source = load_columns(df, [temporal_column] + numeric_columns, db_path=db_path, table_name=table_name)
    for col in numeric_columns:
        work_df[col] = pd.to_numeric(work_df[col], errors="coerce")
    work_df = work_df.dropna(subset=[temporal_column])
    agg_df = work_df.groupby(temporal_column)[numeric_columns].agg(aggregation_method).reset_index()
    if pd.api.types.is_numeric_dtype(agg_df[temporal_column]):
        agg_df = agg_df.sort_values(temporal_column)

    summary_text = (
        f"Aggregated {len(numeric_columns)} numeric column(s) by '{temporal_column}' using {aggregation_method}. "
        f"Result: {len(agg_df)} groups. {dataframe_source_note(source)}"
    )
    return make_tool_result(
        name="aggregate_by_temporal_column",
        text=summary_text,
        artifact_paths=[],
        structured={
            "temporal_column": temporal_column,
            "numeric_columns": numeric_columns,
            "aggregation_method": aggregation_method,
            "n_groups": len(agg_df),
            "source": source,
            "result_dataframe": agg_df.to_dict(orient="records"),
        },
    )


def plot_temporal_line_chart(
    df: pd.DataFrame,
    temporal_column: str,
    numeric_column: str,
    aggregation_method: str = "mean",
    out_path: Optional[Union[str, Path]] = None,
    fig_dir: Optional[Union[str, Path]] = None,
    db_path: Optional[Union[str, Path]] = None,
    table_name: str = "nfl_data",
) -> ToolResult:
    """Create a line chart showing a numeric column over a temporal column, using SQLite when available."""
    if temporal_column not in df.columns:
        raise ValueError(f"Temporal column '{temporal_column}' not found.")
    if numeric_column not in df.columns:
        raise ValueError(f"Numeric column '{numeric_column}' not found.")
    valid_methods = ["mean", "sum", "median", "min", "max", "std", "count"]
    if aggregation_method not in valid_methods:
        raise ValueError(f"Unsupported aggregation method: {aggregation_method}")

    work_df, source = load_columns(df, [temporal_column, numeric_column], db_path=db_path, table_name=table_name)
    work_df[numeric_column] = pd.to_numeric(work_df[numeric_column], errors="coerce")
    work_df = work_df.dropna(subset=[temporal_column, numeric_column])
    if work_df.empty:
        raise ValueError("No usable rows remain after dropping missing/non-numeric values.")

    agg_df = work_df.groupby(temporal_column)[numeric_column].agg(aggregation_method).reset_index()
    if pd.api.types.is_numeric_dtype(agg_df[temporal_column]):
        agg_df = agg_df.sort_values(temporal_column)

    if out_path is None:
        out_path = Path(fig_dir) / f"timeseries_{numeric_column}_by_{temporal_column}.png" if fig_dir is not None else Path(f"timeseries_{numeric_column}_by_{temporal_column}.png")
    else:
        out_path = Path(out_path)
        if not out_path.is_absolute() and fig_dir is not None:
            out_path = Path(fig_dir) / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 6))
    plt.plot(agg_df[temporal_column], agg_df[numeric_column], marker="o", linewidth=2, markersize=6)
    plt.title(f"{numeric_column} by {temporal_column} ({aggregation_method})")
    plt.xlabel(temporal_column)
    plt.ylabel(numeric_column)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

    return make_tool_result(
        name="plot_temporal_line_chart",
        text=f"Saved temporal line chart for '{numeric_column}' by '{temporal_column}' ({aggregation_method}) to {out_path}. {dataframe_source_note(source)}",
        artifact_paths=[str(out_path)],
        structured={
            "temporal_column": temporal_column,
            "numeric_column": numeric_column,
            "aggregation_method": aggregation_method,
            "n_time_points": len(agg_df),
            "source": source,
            "artifact_paths": [str(out_path)],
        },
    )
