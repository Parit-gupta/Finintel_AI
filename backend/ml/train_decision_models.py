"""Train transaction fraud, account anomaly, and branch-profit models."""

from pathlib import Path
import json
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest, RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import classification_report, mean_absolute_error, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "datasets" / "raw"
MODELS = Path(__file__).resolve().parent / "models"
MODELS.mkdir(exist_ok=True)


def train_transaction_fraud():
    # Chunking keeps the 493 MB source practical; keep all rare fraud examples.
    parts = []
    for part in pd.read_csv(DATA / "transactions.csv", chunksize=200_000):
        fraud = part[part["isFraud"] == 1]
        normal = part[part["isFraud"] == 0].sample(min(10_000, (part["isFraud"] == 0).sum()), random_state=42)
        parts.append(pd.concat([fraud, normal]))
    data = pd.concat(parts, ignore_index=True)
    features = ["type", "amount", "oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"]
    X_train, X_test, y_train, y_test = train_test_split(data[features], data["isFraud"], test_size=.2, stratify=data["isFraud"], random_state=42)
    prep = ColumnTransformer([("type", OneHotEncoder(handle_unknown="ignore"), ["type"])], remainder="passthrough")
    model = Pipeline([("prep", prep), ("model", RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42, n_jobs=-1))])
    model.fit(X_train, y_train)
    probability = model.predict_proba(X_test)[:, 1]
    joblib.dump(model, MODELS / "transaction_fraud_model.pkl")
    return {"rows": len(data), "roc_auc": round(float(roc_auc_score(y_test, probability)), 4), "report": classification_report(y_test, model.predict(X_test), output_dict=True)}


def train_account_anomaly():
    # All supplied account records are Active, so a status classifier is invalid.
    # An unsupervised model instead learns normal balance/type/branch behaviour.
    data = pd.read_csv(DATA / "accounts.csv", parse_dates=["opening_date"])
    data["account_age_days"] = (pd.Timestamp.today().normalize() - data["opening_date"]).dt.days.clip(lower=0)
    features = ["account_type", "branch_id", "balance", "account_age_days"]
    prep = ColumnTransformer([("type", OneHotEncoder(handle_unknown="ignore"), ["account_type"])], remainder="passthrough")
    model = Pipeline([("prep", prep), ("model", IsolationForest(contamination=.03, random_state=42))])
    model.fit(data[features])
    joblib.dump(model, MODELS / "account_anomaly_model.pkl")
    return {"rows": len(data), "model": "IsolationForest", "expected_anomaly_rate": "3%"}


def train_branch_profit():
    data = pd.read_csv(DATA / "branch_performance.csv")
    month_order = {name: number for number, name in enumerate(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], 1)}
    data["month_number"] = data["month"].map(month_order)
    # Excludes revenue and expenses because profit is their direct arithmetic result.
    features = ["branch_id", "month_number", "year", "loan_disbursed", "new_customers", "fraud_cases", "customer_satisfaction"]
    X_train, X_test, y_train, y_test = train_test_split(data[features], data["profit"], test_size=.2, random_state=42)
    model = RandomForestRegressor(n_estimators=300, min_samples_leaf=2, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    prediction = model.predict(X_test)
    joblib.dump({"model": model, "features": features, "month_order": month_order}, MODELS / "branch_profit_model.pkl")
    return {"rows": len(data), "mae": round(float(mean_absolute_error(y_test, prediction)), 2)}


if __name__ == "__main__":
    results = {"transaction_fraud": train_transaction_fraud(), "account_anomaly": train_account_anomaly(), "branch_profit": train_branch_profit()}
    with open(MODELS / "decision_models_metrics.json", "w") as output:
        json.dump(results, output, indent=2)
    print(json.dumps(results, indent=2))
