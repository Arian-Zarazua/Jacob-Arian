from __future__ import annotations

from pathlib import Path
from typing import Optional, Union, List

import pandas as pd

from src.sql_support import read_sql, quote_ident, resolve_db_path, dataframe_source_note
from src.utils.tool_result_utils import ToolResult, make_tool_result


def _format_sql_preview_markdown(preview: pd.DataFrame) -> str:
    """Return a compact markdown table without requiring optional tabulate."""
    if preview.empty:
        return "_(query returned no preview rows)_"

    display = preview.copy()
    display = display.where(pd.notna(display), "")
    display = display.astype(str)

    def esc(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    columns = [esc(c) for c in display.columns]
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = [
        "| " + " | ".join(esc(v) for v in row) + " |"
        for row in display.itertuples(index=False, name=None)
    ]
    return "\n".join([header, divider, *rows])


def sql_query(
    df: pd.DataFrame,
    query: str,
    db_path: Optional[Union[str, Path]] = None,
    max_rows: int = 100,
) -> ToolResult:
    """Run a read-only SQL SELECT query against the generated SQLite database."""
    q = (query or "").strip().rstrip(";")
    if not q.lower().startswith(("select", "with")):
        raise ValueError("sql_query only allows read-only SELECT/WITH queries.")
    blocked = ["insert", "update", "delete", "drop", "alter", "create", "attach", "detach", "pragma", "vacuum"]
    lowered = q.lower()
    if any(f"{word} " in lowered or lowered.endswith(word) for word in blocked):
        raise ValueError("sql_query rejected a non-read-only SQL keyword.")

    out = read_sql(q, df=df, db_path=db_path)
    shown = out.head(max_rows)
    markdown_table = _format_sql_preview_markdown(shown)
    text = (
        f"**SQL query completed.** Returned **{len(out):,}** row(s); "
        f"showing up to **{max_rows:,}**.\n\n"
        f"```sql\n{q}\n```\n\n"
        f"{markdown_table}"
    )
    return make_tool_result(
        name="sql_query",
        text=text,
        structured={
            "rows_returned": int(len(out)),
            "rows_shown": int(len(shown)),
            "max_rows": int(max_rows),
            "query": q,
            "columns": [str(c) for c in shown.columns],
            "preview": shown.to_dict(orient="records"),
            "markdown_table": markdown_table,
        },
    )


def top_categories(
    df: pd.DataFrame,
    column: str,
    db_path: Optional[Union[str, Path]] = None,
    table_name: str = "nfl_data",
    top_k: int = 20,
) -> ToolResult:
    """Return the most common values of a categorical column, preferably using SQLite."""
    if column not in df.columns:
        raise ValueError(f"Column not found: {column}")
    path = resolve_db_path(df, db_path)
    if path is not None:
        q = f"""
        SELECT {quote_ident(column)} AS value, COUNT(*) AS count
        FROM {quote_ident(table_name)}
        WHERE {quote_ident(column)} IS NOT NULL
        GROUP BY {quote_ident(column)}
        ORDER BY count DESC
        LIMIT ?
        """
        out = read_sql(q, db_path=path, params=[int(top_k)])
        source = "sqlite"
    else:
        vc = df[column].astype("string").value_counts(dropna=True).head(top_k)
        out = vc.rename_axis("value").reset_index(name="count")
        source = "dataframe"
    return make_tool_result(
        name="top_categories",
        text=f"Top {len(out)} values for `{column}`. {dataframe_source_note(source)}\n\n{out.to_string(index=False)}",
        structured={"column": column, "source": source, "rows": out.to_dict(orient="records")},
    )


def grouped_numeric_summary(
    df: pd.DataFrame,
    group_column: str,
    numeric_column: str,
    aggregation_method: str = "mean",
    db_path: Optional[Union[str, Path]] = None,
    table_name: str = "nfl_data",
    top_k: int = 50,
) -> ToolResult:
    """Aggregate one numeric column by one grouping column, preferably using SQLite."""
    if group_column not in df.columns:
        raise ValueError(f"Group column not found: {group_column}")
    if numeric_column not in df.columns:
        raise ValueError(f"Numeric column not found: {numeric_column}")
    agg_map = {"mean": "AVG", "sum": "SUM", "min": "MIN", "max": "MAX", "count": "COUNT"}
    if aggregation_method not in agg_map:
        raise ValueError(f"Unsupported aggregation_method: {aggregation_method}. Use one of {sorted(agg_map)}")

    path = resolve_db_path(df, db_path)
    if path is not None:
        agg = agg_map[aggregation_method]
        q = f"""
        SELECT {quote_ident(group_column)} AS {quote_ident(group_column)},
               {agg}(CAST({quote_ident(numeric_column)} AS REAL)) AS {quote_ident(aggregation_method + '_' + numeric_column)},
               COUNT(*) AS n_rows
        FROM {quote_ident(table_name)}
        WHERE {quote_ident(group_column)} IS NOT NULL AND {quote_ident(numeric_column)} IS NOT NULL
        GROUP BY {quote_ident(group_column)}
        ORDER BY {quote_ident(aggregation_method + '_' + numeric_column)} DESC
        LIMIT ?
        """
        out = read_sql(q, db_path=path, params=[int(top_k)])
        source = "sqlite"
    else:
        work = df[[group_column, numeric_column]].copy()
        work[numeric_column] = pd.to_numeric(work[numeric_column], errors="coerce")
        out = getattr(work.dropna().groupby(group_column)[numeric_column], aggregation_method)().reset_index()
        out = out.rename(columns={numeric_column: f"{aggregation_method}_{numeric_column}"}).sort_values(f"{aggregation_method}_{numeric_column}", ascending=False).head(top_k)
        source = "dataframe"

    return make_tool_result(
        name="grouped_numeric_summary",
        text=f"Aggregated `{numeric_column}` by `{group_column}` using `{aggregation_method}`. {dataframe_source_note(source)}\n\n{out.to_string(index=False)}",
        structured={"group_column": group_column, "numeric_column": numeric_column, "aggregation_method": aggregation_method, "source": source, "rows": out.to_dict(orient="records")},
    )
