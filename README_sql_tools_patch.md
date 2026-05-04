# SQL tool and artifact-routing patch

1. Existing tools now prefer the generated SQLite database when a `db_path` is provided by the backend or present in `df.attrs` / `BUILD4_SQLITE_DB_PATH`.
2. Plotting tools still save figures into injected report folders, but the backend now also scans the report directory for new/modified artifacts after each tool run.
3. Added SQL-native tools:
   - `sql_query`
   - `top_categories`
   - `grouped_numeric_summary`
4. Removed non-analysis IO utilities from `TOOLS` to prevent the router from selecting functions that are not valid backend analysis tools.
5. Added a backend-safe `plot_missingness(df, ...)` wrapper.


