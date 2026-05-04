# tools registry for ai data analysis agent
from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import pandas as pd

import src.checks as checks
import src.modeling as modeling
import src.plotting as plotting
import src.profiling as profiling
import src.summaries as summaries
import src.time_series as time_series
import src.sql_tools as sql_tools
from src.utils.tool_result_utils import ToolResult


def plot_missingness(
    df: pd.DataFrame,
    out_path: Optional[Union[str, Path]] = None,
    fig_dir: Optional[Union[str, Path]] = None,
    top_n: int = 30,
) -> ToolResult:
    """Backend-friendly wrapper: compute missingness_table(df), then save a missingness plot."""
    if out_path is None:
        target_dir = Path(fig_dir) if fig_dir is not None else Path("figures")
        out_path = target_dir / "missingness.png"
    miss_df = summaries.missingness_table(df)
    return plotting.plot_missingness(miss_df=miss_df, out_path=out_path, top_n=top_n)


TOOLS = {
    # summaries
    "summarize_numeric": summaries.summarize_numeric,
    "summarize_categorical": summaries.summarize_categorical,
    "missingness_table": summaries.missingness_table,
    "pearson_correlation": summaries.pearson_correlation,
    # SQL-native helpers
    "sql_query": sql_tools.sql_query,
    "top_categories": sql_tools.top_categories,
    "grouped_numeric_summary": sql_tools.grouped_numeric_summary,
    # profiling
    "basic_profile": profiling.basic_profile,
    "split_columns": profiling.split_columns,
    # modeling
    "multiple_linear_regression": modeling.multiple_linear_regression,
    # plotting
    "plot_missingness": plot_missingness,
    "plot_corr_heatmap": plotting.plot_corr_heatmap,
    "plot_histograms": plotting.plot_histograms,
    "plot_bar_charts": plotting.plot_bar_charts,
    "plot_cat_num_boxplot": plotting.plot_cat_num_boxplot,
    # time series
    "aggregate_by_temporal_column": time_series.aggregate_by_temporal_column,
    "plot_temporal_line_chart": time_series.plot_temporal_line_chart,
    # checks
    "target_check": checks.target_check,
}

TOOL_DESCRIPTIONS = {
    "summarize_numeric": "Numeric descriptive statistics for selected columns; uses SQLite-backed column reads when available.",
    "summarize_categorical": "Categorical summaries/top values for selected columns; uses SQLite-backed column reads when available.",
    "missingness_table": "Missingness by column.",
    "pearson_correlation": "Pearson correlation between two numeric variables; uses SQLite-backed column reads when available.",
    "sql_query": "Run a read-only SELECT/WITH SQL query against the generated SQLite database table nfl_data.",
    "top_categories": "Top categories/counts for one column using SQL GROUP BY when available.",
    "grouped_numeric_summary": "Aggregate a numeric metric by a group column using SQL GROUP BY when available.",
    "basic_profile": "Basic dataset profile, including SQLite row-count metadata when available.",
    "plot_missingness": "Compute and plot missingness as a figure artifact.",
    "plot_corr_heatmap": "Correlation heatmap for numeric columns; saves a figure artifact.",
    "plot_histograms": "Histograms for numeric columns; saves figure artifacts.",
    "plot_bar_charts": "Bar chart of category counts or SUM(y) by x; saves figure artifacts to the injected tool_figures directory.",
    "plot_cat_num_boxplot": "Boxplot showing the distribution of a numeric variable grouped by a categorical variable.",
    "plot_temporal_line_chart": "Line chart of an aggregated numeric variable over a temporal column; saves figure artifacts.",
    "aggregate_by_temporal_column": "Aggregate numeric columns by season/year/week or other temporal columns.",
    "multiple_linear_regression": "Statsmodels OLS regression; loads the necessary columns from SQLite when available.",
    "target_check": "Check existence, missingness, and basic summary of one target column.",
}
