"""Generate interactive curve charts for every primary FinIntel CSV.

Run from the project root:
    python scripts/generate_csv_curves.py

Large CSVs are sampled from the beginning (up to 100,000 rows) so chart output
stays quick and responsive. The report folder contains standalone HTML charts,
Plotly JSON used by Streamlit, and a manifest for the in-app gallery.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "datasets" / "raw"
OUTPUT_DIR = ROOT / "reports" / "csv_curves"
PNG_DIR = OUTPUT_DIR / "images"

DATASET_LABELS = {
    "customers": ("customers.csv", "Customer Intelligence"),
    "transactions": ("transactions.csv", "Transaction Monitoring"),
    "fraud": ("credit_card_fraud.csv", "Card Fraud Monitoring"),
    "loans": ("loan_applications.csv", "Loan & Credit Risk"),
    "accounts": ("accounts.csv", "Account Health"),
    "branches": ("branches.csv", "Branch Directory"),
    "performance": ("branch_performance.csv", "Branch Performance"),
    "employees": ("employees.csv", "Workforce Analytics"),
    "products": ("banking_products.csv", "Banking Products"),
    "marketing": ("marketing_campaigns.csv", "Campaign Performance"),
    "tickets": ("support_tickets.csv", "Support Operations"),
    "predictions": ("prediction_history.csv", "Model Audit"),
    "users": ("user_roles.csv", "Access & Roles"),
}

EXCLUDED_CSVS = {
    "raw/prediction_history.csv": "Empty file with headers only; it has no rows to plot.",
    "raw/give_me_some_credit/sample_submission.csv": "Submission template, not an observed dataset.",
}

PREFERRED_NUMERIC = (
    "amount", "income", "balance", "profit", "revenue", "salary", "score",
    "probability", "rate", "age", "fraud", "employees", "satisfaction",
    "loan", "expenses", "assets", "count", "accepted", "class",
)
SENSITIVE_OR_ID = ("password", "email", "phone", "name", "customer_id", "branch_id", "employee_id", "account_id", "loan_id", "ticket_id", "campaign_id", "product_id", "prediction_id", "user_id")


def safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", value).strip("_").lower()


def make_line(x, y, title: str, x_title: str, y_title: str) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", line={"shape": "spline", "width": 3}, fill="tozeroy", name=y_title))
    figure.update_layout(title=title, xaxis_title=x_title, yaxis_title=y_title, template="plotly_white", hovermode="x unified")
    return figure


def chart_record(dataset: str, slug: str, title: str, description: str, figure: go.Figure) -> dict:
    stem = f"{dataset}__{slug}"
    json_name, html_name = f"{stem}.json", f"{stem}.html"
    png_name = f"{stem}.png"
    figure.write_json(OUTPUT_DIR / json_name)
    figure.write_html(OUTPUT_DIR / html_name, include_plotlyjs="directory", full_html=True)
    figure.write_image(PNG_DIR / png_name, format="png", width=1200, height=700, scale=2)
    return {"title": title, "description": description, "json": json_name, "html": html_name, "png": f"images/{png_name}"}


def numeric_columns(frame: pd.DataFrame) -> list[str]:
    candidates = [column for column in frame.select_dtypes(include="number").columns if not any(token in column.lower() for token in SENSITIVE_OR_ID)]
    preferred = [column for token in PREFERRED_NUMERIC for column in candidates if token in column.lower()]
    return list(dict.fromkeys(preferred + candidates))


def add_distribution_charts(dataset: str, frame: pd.DataFrame) -> list[dict]:
    charts = []
    for column in numeric_columns(frame)[:3]:
        values = pd.to_numeric(frame[column], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        if values.empty:
            continue
        if values.nunique() <= 20:
            counts = values.value_counts().sort_index()
            x, y = counts.index.astype(str), counts.values
            description = f"Frequency curve for {column}."
        else:
            counts, edges = np.histogram(values.to_numpy(), bins=min(35, max(10, int(np.sqrt(len(values))))))
            x, y = (edges[:-1] + edges[1:]) / 2, counts
            description = f"Binned distribution curve for {column}; chart uses the loaded CSV sample."
        title = f"{column.replace('_', ' ').title()} distribution curve"
        figure = make_line(x, y, title, column.replace("_", " ").title(), "Rows")
        charts.append(chart_record(dataset, f"distribution_{safe_name(column)}", title, description, figure))
    return charts


def add_category_chart(dataset: str, frame: pd.DataFrame) -> dict | None:
    candidates = []
    for column in frame.select_dtypes(include=["str", "category", "bool"]).columns:
        low = column.lower()
        if any(token in low for token in SENSITIVE_OR_ID) or low in {"name", "username"}:
            continue
        count = frame[column].nunique(dropna=True)
        if 2 <= count <= 100:
            candidates.append(column)
    if not candidates:
        # Low-cardinality numeric labels (e.g. fraud Class) are useful category curves.
        candidates = [column for column in numeric_columns(frame) if frame[column].nunique(dropna=True) <= 20]
    if not candidates:
        return None
    column = candidates[0]
    counts = frame[column].fillna("Missing").astype(str).value_counts().head(20).sort_values(ascending=False)
    title = f"{column.replace('_', ' ').title()} category curve"
    figure = make_line(counts.index, counts.values, title, column.replace("_", " ").title(), "Rows")
    return chart_record(dataset, f"categories_{safe_name(column)}", title, f"Counts for the most frequent values in {column}.", figure)


def add_time_chart(dataset: str, frame: pd.DataFrame) -> dict | None:
    date_column = next((column for column in frame.columns if any(token in column.lower() for token in ("timestamp", "opened_date", "joining_date", "last_login", "customer_since", "date"))), None)
    if date_column:
        dates = pd.to_datetime(frame[date_column], errors="coerce", utc=True).dt.tz_convert(None)
        valid = dates.notna()
        if valid.any():
            counts = dates[valid].dt.to_period("M").dt.to_timestamp().value_counts().sort_index()
            title = f"Records over time — {date_column.replace('_', ' ')}"
            figure = make_line(counts.index, counts.values, title, "Month", "Rows")
            return chart_record(dataset, "time_records", title, f"Monthly record volume based on {date_column}.", figure)

    sequence = next((column for column in frame.columns if column.lower() in {"step", "time", "year"}), None)
    if sequence:
        numeric = numeric_columns(frame)
        measure = next((column for column in numeric if column != sequence), None)
        grouped = frame.groupby(sequence, as_index=False)[measure].mean() if measure else frame.groupby(sequence, as_index=False).size()
        measure_name = measure if measure else "size"
        title = f"{measure_name.replace('_', ' ').title()} trend by {sequence}"
        figure = make_line(grouped[sequence], grouped[measure_name], title, sequence.title(), measure_name.replace("_", " ").title())
        return chart_record(dataset, "sequence_trend", title, f"Average {measure_name} across {sequence} values.", figure)
    return None


def generate(max_rows: int) -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PNG_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {"sample_limit": max_rows, "excluded": EXCLUDED_CSVS, "datasets": {}}
    dataset_root = ROOT / "datasets"
    csv_files = sorted(path for path in dataset_root.rglob("*.csv") if path.relative_to(dataset_root).as_posix() not in EXCLUDED_CSVS)
    for path in csv_files:
        relative = path.relative_to(dataset_root).as_posix()
        key = safe_name(relative.removesuffix(".csv").replace("/", "__"))
        filename = relative
        label = next((value[1] for value in DATASET_LABELS.values() if value[0] == path.name), path.stem.replace("_", " ").replace("-", " ").title())
        frame = pd.read_csv(path, nrows=max_rows, low_memory=False)
        frame.columns = frame.columns.astype(str).str.strip()
        charts = []
        if not frame.empty:
            charts.extend(add_distribution_charts(key, frame))
            category = add_category_chart(key, frame)
            if category:
                charts.append(category)
            trend = add_time_chart(key, frame)
            if trend:
                charts.append(trend)
        manifest["datasets"][key] = {"label": label, "csv": filename, "rows": len(frame), "sampled": len(frame) >= max_rows, "charts": charts}
        print(f"{label}: {len(frame):,} rows, {len(charts)} charts")
    (OUTPUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-rows", type=int, default=100_000, help="Maximum rows read per CSV (default: 100,000).")
    args = parser.parse_args()
    if args.max_rows < 1:
        parser.error("--max-rows must be at least 1")
    generate(args.max_rows)
    print(f"Interactive charts and manifest saved in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
