from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Dict, Any, Union

import pandas as pd
import statsmodels.formula.api as smf

from src.sql_support import load_columns, dataframe_source_note
from src.utils.tool_result_utils import ToolResult, make_tool_result


def multiple_linear_regression(
    df: pd.DataFrame,
    outcome: str,
    predictors: Optional[List[str]] = None,
    db_path: Optional[Union[str, Path]] = None,
    table_name: str = "nfl_data",
) -> ToolResult:
    """Fit multiple linear regression using statsmodels OLS; loads columns from SQLite when available."""
    if outcome not in df.columns:
        raise ValueError(f"Outcome column '{outcome}' not found in dataframe.")
    if predictors is None or len(predictors) == 0:
        raise ValueError("You must specify at least one predictor.")
    missing_preds = [p for p in predictors if p not in df.columns]
    if missing_preds:
        raise ValueError(f"Predictor(s) not found: {missing_preds}")

    model_df, source = load_columns(df, [outcome] + predictors, db_path=db_path, table_name=table_name)
    model_df = model_df.dropna()
    if model_df.shape[0] < 3:
        raise ValueError("Not enough complete rows to fit regression (need >= 3).")

    terms: List[str] = []
    for p in predictors:
        model_df[p] = pd.to_numeric(model_df[p], errors="ignore")
        if pd.api.types.is_numeric_dtype(model_df[p]):
            terms.append(p)
        else:
            terms.append(f"C({p})")
    formula = f"{outcome} ~ " + " + ".join(terms)

    fitted = smf.ols(formula=formula, data=model_df).fit()
    ci = fitted.conf_int(); ci.columns = ["ci_lower", "ci_upper"]

    coef_table: Dict[str, Dict[str, float]] = {}
    for term in fitted.params.index:
        coef_table[str(term)] = {
            "coefficient": float(fitted.params[term]),
            "std_error": float(fitted.bse[term]),
            "t_value": float(fitted.tvalues[term]),
            "p_value": float(fitted.pvalues[term]),
            "ci_lower": float(ci.loc[term, "ci_lower"]),
            "ci_upper": float(ci.loc[term, "ci_upper"]),
        }

    out: Dict[str, Any] = {
        "outcome": str(outcome),
        "predictors": [str(p) for p in predictors],
        "n_rows_used": int(model_df.shape[0]),
        "formula": str(formula),
        "r_squared": float(fitted.rsquared),
        "adj_r_squared": float(fitted.rsquared_adj),
        "f_statistic": float(fitted.fvalue) if fitted.fvalue is not None else None,
        "f_pvalue": float(fitted.f_pvalue) if fitted.f_pvalue is not None else None,
        "df_model": float(fitted.df_model),
        "df_resid": float(fitted.df_resid),
        "coefficients": coef_table,
        "source": source,
    }
    coef_text = "\n".join([
        f"- {term}: b = {vals['coefficient']:.4f}, SE = {vals['std_error']:.4f}, t = {vals['t_value']:.4f}, p = {vals['p_value']:.4g}, 95% CI [{vals['ci_lower']:.4f}, {vals['ci_upper']:.4f}]"
        for term, vals in coef_table.items()
    ])
    summary_text = (
        f"Fitted multiple linear regression.\nOutcome: {outcome}\nPredictors: {', '.join(predictors)}\nRows used: {model_df.shape[0]}\n"
        f"Formula: {formula}\nR-squared: {fitted.rsquared:.4f}\nAdjusted R-squared: {fitted.rsquared_adj:.4f}\n"
        f"F-statistic: {fitted.fvalue:.4f}\nDegrees of freedom: model={fitted.df_model:.0f}, residual={fitted.df_resid:.0f}\n"
        f"Model p-value: {fitted.f_pvalue:.4g}\n{dataframe_source_note(source)}\n\nCoefficients:\n{coef_text}"
    )
    return make_tool_result(name="multiple_linear_regression", text=summary_text, structured=out)
