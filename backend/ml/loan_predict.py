import json
from pathlib import Path

import joblib
import pandas as pd


MODEL_DIR = Path(__file__).resolve().parent / "models"
MODEL_PATH = MODEL_DIR / "loan_model.pkl"
META_PATH = MODEL_DIR / "loan_model_meta.json"

FEATURES = [
    "no_of_dependents",
    "education",
    "self_employed",
    "income_annum",
    "loan_amount",
    "loan_term",
    "cibil_score",
    "residential_assets_value",
    "commercial_assets_value",
    "luxury_assets_value",
    "bank_asset_value",
]

NUMERIC_FIELDS = [
    "no_of_dependents",
    "income_annum",
    "loan_amount",
    "loan_term",
    "cibil_score",
    "residential_assets_value",
    "commercial_assets_value",
    "luxury_assets_value",
    "bank_asset_value",
]

ASSET_FIELDS = [
    "residential_assets_value",
    "commercial_assets_value",
    "luxury_assets_value",
    "bank_asset_value",
]

_model = None
_meta = None


def _load():
    global _model, _meta

    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. Run train_loan_model.py first."
            )

        if not META_PATH.exists():
            raise FileNotFoundError(
                f"Model metadata not found at {META_PATH}. "
                "Run train_loan_model.py first."
            )

        _model = joblib.load(MODEL_PATH)

        with open(META_PATH, "r", encoding="utf-8") as file:
            _meta = json.load(file)

    return _model, _meta


def validate_input(data: dict) -> dict:
    errors = {}

    if not isinstance(data, dict):
        return {
            "valid": False,
            "errors": {"input": "Input must be a dictionary."},
        }

    for field in FEATURES:
        if field not in data:
            errors[field] = f"{field} is required."

    if errors:
        return {"valid": False, "errors": errors}

    normalized = {}

    for field in NUMERIC_FIELDS:
        value = data[field]

        if isinstance(value, bool):
            errors[field] = f"{field} must be numeric."
            continue

        try:
            number = float(value)
        except (TypeError, ValueError):
            errors[field] = f"{field} must be numeric."
            continue

        if not pd.notna(number) or number in (float("inf"), float("-inf")):
            errors[field] = f"{field} must be a finite number."
            continue

        normalized[field] = number

    if errors:
        return {"valid": False, "errors": errors}

    dependents = normalized["no_of_dependents"]

    if dependents < 0 or not dependents.is_integer():
        errors["no_of_dependents"] = (
            "Number of dependents must be a non-negative whole number."
        )

    if normalized["income_annum"] <= 0:
        errors["income_annum"] = "Annual income must be greater than zero."

    if normalized["loan_amount"] <= 0:
        errors["loan_amount"] = "Loan amount must be greater than zero."

    if not 1 <= normalized["loan_term"] <= 30:
        errors["loan_term"] = "Loan term must be between 1 and 30 years."

    if not normalized["loan_term"].is_integer():
        errors["loan_term"] = "Loan term must be a whole number of years."

    if not 300 <= normalized["cibil_score"] <= 900:
        errors["cibil_score"] = "CIBIL score must be between 300 and 900."

    for field in ASSET_FIELDS:
        if normalized[field] < 0:
            errors[field] = f"{field} cannot be negative."

    if data["education"] not in ("Graduate", "Not Graduate"):
        errors["education"] = "Education must be Graduate or Not Graduate."

    if data["self_employed"] not in ("Yes", "No"):
        errors["self_employed"] = "Self-employed status must be Yes or No."

    income = normalized["income_annum"]
    loan_amount = normalized["loan_amount"]

    if income > 0:
        ratio = loan_amount / income

        if ratio > 15:
            errors["loan_amount"] = (
                f"Loan amount is {ratio:.1f} times annual income. "
                "This is outside the configured plausibility limit of 15 times."
            )

    if loan_amount > 40_000_000:
        errors["loan_amount"] = (
            "Loan amount exceeds ₹4 crore, the configured plausibility limit."
        )

    if errors:
        return {"valid": False, "errors": errors}

    normalized["education"] = data["education"]
    normalized["self_employed"] = data["self_employed"]

    return {
        "valid": True,
        "errors": {},
        "data": normalized,
    }


def _risk_level(approval_probability: float) -> str:
    if approval_probability >= 70:
        return "LOW"
    elif approval_probability >= 40:
        return "MEDIUM"
    return "HIGH"


def _key_factors(data: dict) -> list:
    factors = []

    if data["cibil_score"] >= 700:
        factors.append("Strong CIBIL score")
    elif data["cibil_score"] < 600:
        factors.append("Low CIBIL score")

    if data["income_annum"] >= 500_000:
        factors.append("Annual income is at least ₹5 lakh")

    ratio = data["loan_amount"] / max(data["income_annum"], 1)

    if ratio <= 3:
        factors.append("Loan amount is at most 3 times annual income")
    elif ratio > 6:
        factors.append("Loan amount is more than 6 times annual income")

    total_assets = sum(data[field] for field in ASSET_FIELDS)

    if total_assets >= data["loan_amount"] * 0.5:
        factors.append("Declared assets are at least half the loan amount")

    if not factors:
        factors.append(
            "No additional rule-based factors identified; review the full application."
        )

    return factors


def predict_loan_approval(data: dict) -> dict:
    validation = validate_input(data)

    if not validation["valid"]:
        return {
            "valid": False,
            "errors": validation["errors"],
        }

    clean_data = validation["data"]

    model, meta = _load()

    features = meta.get("features", FEATURES)

    if set(features) != set(FEATURES):
        return {
            "valid": False,
            "errors": {
                "model": (
                    "Model feature configuration does not match the prediction "
                    "module. Retrain the model or update the feature list."
                )
            },
        }

    input_df = pd.DataFrame(
        [{feature: clean_data[feature] for feature in features}],
        columns=features,
    )

    probabilities = model.predict_proba(input_df)[0]
    classes = [str(label) for label in model.classes_]

    approved_index = next(
        (
            index
            for index, label in enumerate(classes)
            if label.strip().lower() == "approved"
        ),
        None,
    )

    if approved_index is None:
        return {
            "valid": False,
            "errors": {
                "model": (
                    "The trained model does not contain an Approved class. "
                    "Check the training target labels."
                )
            },
        }

    approval_probability = float(probabilities[approved_index]) * 100

    decision = (
        "APPROVED"
        if approval_probability >= 50
        else "REJECTED"
    )

    return {
        "valid": True,
        "approval_probability": round(approval_probability, 1),
        "decision": decision,
        "risk_level": _risk_level(approval_probability),
        "key_factors": _key_factors(clean_data),
        "model_used": meta.get("best_model_name", "Unknown"),
        "disclaimer": (
            "This is an experimental model prediction, not an actual lending "
            "decision. Risk labels are based on model-estimated approval "
            "probability, not calibrated estimates of real-world default risk."
        ),
    }


if __name__ == "__main__":
    sample = {
        "no_of_dependents": 2,
        "education": "Graduate",
        "self_employed": "No",
        "income_annum": 750000,
        "loan_amount": 1500000,
        "loan_term": 15,
        "cibil_score": 735,
        "residential_assets_value": 500000,
        "commercial_assets_value": 0,
        "luxury_assets_value": 200000,
        "bank_asset_value": 100000,
    }

    result = predict_loan_approval(sample)
    print(json.dumps(result, indent=2, ensure_ascii=False))
