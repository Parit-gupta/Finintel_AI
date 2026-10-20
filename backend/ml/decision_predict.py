"""Prediction helpers for the models created by train_decision_models.py."""
from pathlib import Path
import joblib
import pandas as pd

MODELS = Path(__file__).resolve().parent / "models"


def transaction_fraud_probability(data):
    model = joblib.load(MODELS / "transaction_fraud_model.pkl")
    features = ["type", "amount", "oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"]
    probability = float(model.predict_proba(pd.DataFrame([data])[features])[0][1])
    return round(probability * 100, 2)


def account_anomaly(data):
    model = joblib.load(MODELS / "account_anomaly_model.pkl")
    row = pd.DataFrame([data])[["account_type", "branch_id", "balance", "account_age_days"]]
    # IsolationForest returns -1 for anomalous records and +1 for normal records.
    return int(model.predict(row)[0]) == -1


def branch_profit_prediction(data):
    payload = joblib.load(MODELS / "branch_profit_model.pkl")
    month = payload["month_order"][data.pop("month")]
    row = pd.DataFrame([{**data, "month_number": month}])[payload["features"]]
    return round(float(payload["model"].predict(row)[0]), 2)
