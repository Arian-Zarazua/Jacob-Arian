"""Time series and temporal aggregation tools for data analysis."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union, Any

import pandas as pd
import matplotlib.pyplot as plt

from src.utils.tool_result_utils import ToolResult, make_tool_result


def aggregate_by_temporal_column(
    df: pd.DataFrame,
    temporal_column: str,
    numeric_columns: List[str],
    aggregation_method: str = "mean",
) -> ToolResult:
    """
    Aggregate numeric columns by a temporal column (e.g., season, year, month).
    
    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    temporal_column : str
        The column to group by (e.g., 'season', 'year', 'month').
    numeric_columns : List[str]
        List of numeric columns to aggregate.
    aggregation_method : str
        Aggregation method: 'mean', 'sum', 'median', 'min', 'max', 'std', 'count'.
    
    Returns
    -------
    ToolResult:
        Aggregated dataframe with summary statistics.
    """
    
    # Validate inputs
    if temporal_column not in df.columns:
        raise ValueError(f"Temporal column '{temporal_column}' not found in dataframe.")
    
    if not numeric_columns:
        raise ValueError("Must specify at least one numeric column to aggregate.")
    
    missing_cols = [col for col in numeric_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Numeric columns not found: {missing_cols}")
    
    # Validate that numeric columns are actually numeric
    non_numeric = []
    for col in numeric_columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            non_numeric.append(col)
    
    if non_numeric:
        raise ValueError(f"Columns are not numeric: {non_numeric}")
    
    # Ensure aggregation method is valid
    valid_methods = ["mean", "sum", "median", "min", "max", "std", "count"]
    if aggregation_method not in valid_methods:
        raise ValueError(
            f"Aggregation method '{aggregation_method}' not supported. "
            f"Use one of: {', '.join(valid_methods)}"
        )
    
    # Filter to temporal + numeric columns
    work_df = df[[temporal_column] + numeric_columns].copy()
    
    # Drop rows with missing temporal column
    work_df = work_df.dropna(subset=[temporal_column])
    
    # Perform aggregation
    agg_df = work_df.groupby(temporal_column)[numeric_columns].agg(aggregation_method)
    agg_df = agg_df.reset_index()
    
    # Sort by temporal column (if numeric, ascending; otherwise keep original order)
    if pd.api.types.is_numeric_dtype(agg_df[temporal_column]):
        agg_df = agg_df.sort_values(temporal_column)
    
    summary_text = (
        f"Aggregated {len(numeric_columns)} numeric column(s) by '{temporal_column}' "
        f"using {aggregation_method}. Result: {len(agg_df)} groups."
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
) -> ToolResult:
    """
    Create a line chart showing a numeric column over a temporal column.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    temporal_column : str
        The column to use for x-axis (e.g., 'season', 'year', 'month').
    numeric_column : str
        The numeric column to plot on y-axis.
    aggregation_method : str
        How to aggregate the numeric column: 'mean', 'sum', 'median', 'min', 'max'.
    out_path : Union[str, Path] | None
        Optional output filename for the plot.
    fig_dir : Union[str, Path] | None
        Optional output directory for the plot.
    
    Returns
    -------
    ToolResult:
        with artifact_paths containing the saved figure path.
    """
    
    # Validate inputs
    if temporal_column not in df.columns:
        raise ValueError(f"Temporal column '{temporal_column}' not found.")
    if numeric_column not in df.columns:
        raise ValueError(f"Numeric column '{numeric_column}' not found.")
    
    if not pd.api.types.is_numeric_dtype(df[numeric_column]):
        raise ValueError(f"Column '{numeric_column}' is not numeric.")
    
    # Aggregate data
    work_df = df[[temporal_column, numeric_column]].copy()
    work_df = work_df.dropna(subset=[temporal_column])
    
    agg_df = work_df.groupby(temporal_column)[numeric_column].agg(aggregation_method)
    agg_df = agg_df.reset_index()
    
    # Sort by temporal column (if numeric)
    if pd.api.types.is_numeric_dtype(agg_df[temporal_column]):
        agg_df = agg_df.sort_values(temporal_column)
    
    # Resolve output path
    if out_path is None:
        if fig_dir is not None:
            out_path = Path(fig_dir) / f"timeseries_{numeric_column}_by_{temporal_column}.png"
        else:
            out_path = Path(f"timeseries_{numeric_column}_by_{temporal_column}.png")
    else:
        out_path = Path(out_path)
        if not out_path.is_absolute() and fig_dir is not None:
            out_path = Path(fig_dir) / out_path
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(
        agg_df[temporal_column],
        agg_df[numeric_column],
        marker="o",
        linewidth=2,
        markersize=6,
    )
    plt.title(f"{numeric_column} by {temporal_column} ({aggregation_method})")
    plt.xlabel(temporal_column)
    plt.ylabel(numeric_column)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()
    
    return make_tool_result(
        name="plot_temporal_line_chart",
        text=(
            f"Saved temporal line chart for '{numeric_column}' by '{temporal_column}' "
            f"({aggregation_method}) to {out_path}."
        ),
        artifact_paths=[str(out_path)],
        structured={
            "temporal_column": temporal_column,
            "numeric_column": numeric_column,
            "aggregation_method": aggregation_method,
            "n_time_points": len(agg_df),
            "artifact_paths": [str(out_path)],
        },
    )
