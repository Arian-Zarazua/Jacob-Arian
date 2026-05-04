# time_series_tools

## Purpose
Provide tools for temporal aggregation and visualization of time series data, enabling summarization and trend analysis over time-based or categorical temporal dimensions (e.g., year, month, season).

## When to use
Use when working with datasets that include a temporal grouping variable and at least one numeric variable, and you want to:
- summarize values over time (e.g., mean sales per month)
- compare trends across time periods
- visualize temporal evolution of a metric

## Inputs
### For `aggregate_by_temporal_column`
- `df`: pandas DataFrame
- `temporal_column`: column used for grouping (e.g., year, month, season)
- `numeric_columns`: list of numeric columns to aggregate
- `aggregation_method`: one of:
  - mean, sum, median, min, max, std, count

### For `plot_temporal_line_chart`
- `df`: pandas DataFrame
- `temporal_column`: x-axis grouping variable
- `numeric_column`: y-axis numeric variable
- `aggregation_method`: aggregation applied before plotting (mean, sum, median, min, max)
- optional:
  - `out_path`
  - `fig_dir`

## Outputs
### `aggregate_by_temporal_column`
A structured result containing:
- aggregated DataFrame grouped by temporal column
- aggregation method used
- number of groups
- list of records (JSON-like format of result table)

### `plot_temporal_line_chart`
A structured result containing:
- path to saved figure
- metadata about aggregation and variables used
- number of time points plotted

## Why it helps an agent
These tools allow an agent to:
- reduce raw time series into interpretable summaries
- identify trends and seasonal structure
- generate visual evidence for temporal patterns
- support downstream modeling or forecasting tasks

## Cautions
- temporal column must exist and should be clean (missing values are dropped)
- numeric columns must be strictly numeric (non-numeric columns will raise errors)
- aggregation assumes independence within groups (may hide within-group variance)
- plotting assumes sorted temporal order (may need categorical ordering for non-numeric time labels)
- large numbers of unique temporal groups may produce cluttered plots