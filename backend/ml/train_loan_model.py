
import json
import os
from io import BytesIO
from pathlib import Path

import boto3
import joblib
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    LabelEncoder,
    OneHotEncoder,
    StandardScaler,
)
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier


bucket = "finintel-ai-parit-2026-unique"
s3_key = "raw/loan_applications.csv"
region = "us-east-1"

model_dir = Path("backend/ml/models")
results_dir = Path("backend/ml/results")

model_dir.mkdir(parents=True, exist_ok=True)
results_dir.mkdir(parents=True, exist_ok=True)

features = [
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

target = "loan_status"
categorical_columns = ["education", "self_employed"]
numeric_columns = [
    column for column in features
    if column not in categorical_columns
]

random_state = 42


def load_dataset():
    session = boto3.Session(profile_name="finintel")
    s3 = session.client("s3", region_name=region)

    response = s3.get_object(
        Bucket=bucket,
        Key=s3_key,
    )

    dataframe = pd.read_csv(
        BytesIO(response["Body"].read())
    )

    dataframe.columns = dataframe.columns.str.strip()

    for column in dataframe.select_dtypes(
        include=["object", "string"]
    ).columns:
        dataframe[column] = dataframe[column].str.strip()

    print("Dataset downloaded from S3.")
    print("Dataset shape:", dataframe.shape)

    return dataframe


def prepare_dataset(dataframe):
    required_columns = features + [target]
    missing_columns = [
        column for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    dataframe = dataframe[required_columns].copy()

    dataframe[target] = dataframe[target].replace(
        "", pd.NA
    )

    dataframe = dataframe.dropna(
        subset=[target]
    ).copy()

    dataframe[target] = dataframe[target].astype(str).str.strip()

    dataframe = dataframe[
        dataframe[target] != ""
    ].copy()

    for column in categorical_columns:
        dataframe[column] = dataframe[column].replace(
            "", np.nan
        )

    for column in numeric_columns:
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

    if dataframe[target].nunique() < 2:
        raise ValueError(
            "The target must contain at least two classes."
        )

    if "Approved" not in dataframe[target].unique():
        raise ValueError(
            "The target does not contain 'Approved'. "
            f"Found: {sorted(dataframe[target].unique().tolist())}"
        )

    counts = dataframe[target].value_counts()

    if counts.min() < 2:
        raise ValueError(
            "Each target class needs at least two records."
        )

    return dataframe


def build_preprocessor():
    numeric_pipeline = Pipeline([
        (
            "imputer",
            SimpleImputer(strategy="median"),
        ),
        (
            "scaler",
            StandardScaler(),
        ),
    ])

    categorical_pipeline = Pipeline([
        (
            "imputer",
            SimpleImputer(strategy="most_frequent"),
        ),
        (
            "encoder",
            OneHotEncoder(handle_unknown="ignore"),
        ),
    ])

    return ColumnTransformer([
        (
            "numeric",
            numeric_pipeline,
            numeric_columns,
        ),
        (
            "categorical",
            categorical_pipeline,
            categorical_columns,
        ),
    ])


def build_models():
    return {
        "Logistic Regression": LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=random_state,
        ),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=8,
            class_weight="balanced",
            random_state=random_state,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=300,
            max_depth=10,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=200,
            max_depth=3,
            random_state=random_state,
        ),
        "KNN": KNeighborsClassifier(
            n_neighbors=15,
        ),
        "SVM": SVC(
            probability=True,
            kernel="rbf",
            class_weight="balanced",
            random_state=random_state,
        ),
    }


def evaluate_models(X_train, X_test, y_train, y_test):
    models = build_models()

    results = {}
    trained_models = {}
    roc_data = {}

    for name, classifier in models.items():
        print(f"\nTraining {name}...")

        pipeline = Pipeline([
            ("preprocessor", build_preprocessor()),
            ("classifier", classifier),
        ])

        pipeline.fit(X_train, y_train)

        predictions = pipeline.predict(X_test)
        probabilities = pipeline.predict_proba(X_test)

        classes = list(pipeline.classes_)
        approved_index = classes.index("Approved")
        approved_probabilities = probabilities[:, approved_index]

        actual_approved = (
            y_test == "Approved"
        ).astype(int)

        predicted_approved = (
            predictions == "Approved"
        ).astype(int)

        accuracy = accuracy_score(
            y_test,
            predictions,
        )

        precision = precision_score(
            actual_approved,
            predicted_approved,
            zero_division=0,
        )

        recall = recall_score(
            actual_approved,
            predicted_approved,
            zero_division=0,
        )

        f1 = f1_score(
            actual_approved,
            predicted_approved,
            zero_division=0,
        )

        auc = roc_auc_score(
            actual_approved,
            approved_probabilities,
        )

        results[name] = {
            "accuracy": round(float(accuracy), 4),
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "f1_score": round(float(f1), 4),
            "roc_auc": round(float(auc), 4),
        }

        trained_models[name] = pipeline

        false_positive_rate, true_positive_rate, _ = roc_curve(
            actual_approved,
            approved_probabilities,
        )

        roc_data[name] = (
            false_positive_rate,
            true_positive_rate,
            auc,
        )

        print(
            f"Accuracy: {accuracy:.4f} | "
            f"Precision: {precision:.4f} | "
            f"Recall: {recall:.4f} | "
            f"F1: {f1:.4f} | "
            f"ROC-AUC: {auc:.4f}"
        )

    return results, trained_models, roc_data


def save_comparison(results, best_name):
    comparison = pd.DataFrame(results).T
    comparison.index.name = "model"

    comparison.to_csv(
        results_dir / "comparison.csv"
    )

    with open(
        results_dir / "comparison.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            {
                "results": results,
                "best_model": best_name,
                "selection_metric": "roc_auc",
            },
            file,
            indent=2,
        )

    print("\nModel comparison saved.")


def plot_model_comparison(results):
    names = list(results.keys())
    accuracies = [
        results[name]["accuracy"]
        for name in names
    ]
    aucs = [
        results[name]["roc_auc"]
        for name in names
    ]

    positions = np.arange(len(names))
    width = 0.35

    fig, axis = plt.subplots(figsize=(11, 6))

    axis.bar(
        positions - width / 2,
        accuracies,
        width,
        label="Accuracy",
    )

    axis.bar(
        positions + width / 2,
        aucs,
        width,
        label="ROC-AUC",
    )

    axis.set_xticks(positions)
    axis.set_xticklabels(
        names,
        rotation=20,
        ha="right",
    )
    axis.set_ylim(0, 1.05)
    axis.set_ylabel("Score")
    axis.set_title("Loan Approval Model Comparison")
    axis.legend()

    fig.tight_layout()
    fig.savefig(
        results_dir / "model_comparison.png",
        dpi=150,
    )
    plt.close(fig)


def plot_roc_curves(roc_data):
    fig, axis = plt.subplots(figsize=(8, 7))

    for name, (fpr, tpr, auc) in roc_data.items():
        axis.plot(
            fpr,
            tpr,
            label=f"{name} (AUC={auc:.3f})",
        )

    axis.plot(
        [0, 1],
        [0, 1],
        linestyle="--",
        label="Random baseline",
    )

    axis.set_xlabel("False Positive Rate")
    axis.set_ylabel("True Positive Rate")
    axis.set_title("Loan Approval ROC Curves")
    axis.legend(loc="lower right", fontsize=8)

    fig.tight_layout()
    fig.savefig(
        results_dir / "roc_curves.png",
        dpi=150,
    )
    plt.close(fig)


def plot_confusion_matrix(model, X_test, y_test, best_name):
    predictions = model.predict(X_test)

    labels = list(model.classes_)
    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=labels,
    )

    display = ConfusionMatrixDisplay(
        confusion_matrix=matrix,
        display_labels=labels,
    )

    fig, axis = plt.subplots(figsize=(6, 6))
    display.plot(
        ax=axis,
        cmap="Blues",
        colorbar=False,
    )

    axis.set_title(
        f"Confusion Matrix - {best_name}"
    )

    fig.tight_layout()
    fig.savefig(
        results_dir / "confusion_matrix.png",
        dpi=150,
    )
    plt.close(fig)


def main():
    dataframe = prepare_dataset(
        load_dataset()
    )

    print("\nLoan status distribution:")
    print(dataframe[target].value_counts())

    X = dataframe[features]
    y = dataframe[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=random_state,
        stratify=y,
    )

    results, trained_models, roc_data = evaluate_models(
        X_train,
        X_test,
        y_train,
        y_test,
    )

    best_name = max(
        results,
        key=lambda name: results[name]["roc_auc"],
    )

    best_model = trained_models[best_name]

    print(f"\nBest model: {best_name}")
    print("Metrics:", results[best_name])

    predictions = best_model.predict(X_test)

    print("\nClassification report:")
    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0,
        )
    )

    preprocessor = best_model.named_steps["preprocessor"]
    classifier = best_model.named_steps["classifier"]

    feature_names = preprocessor.get_feature_names_out()
    feature_importances = None

    if hasattr(classifier, "feature_importances_"):
        feature_importances = {
            name: float(value)
            for name, value in zip(
                feature_names,
                classifier.feature_importances_,
            )
        }
        feature_importances = dict(
            sorted(
                feature_importances.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        )

    model_path = model_dir / "loan_model.pkl"
    metadata_path = model_dir / "loan_model_meta.json"

    joblib.dump(best_model, model_path)

    metadata = {
        "features": features,
        "categorical_features": categorical_columns,
        "numeric_features": numeric_columns,
        "target": target,
        "classes": best_model.classes_.tolist(),
        "approved_label": "Approved",
        "best_model_name": best_name,
        "selection_metric": "roc_auc",
        "metrics": results[best_name],
        "all_results": results,
        "feature_importances": feature_importances,
        "training_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "random_state": random_state,
    }

    with open(
        metadata_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            indent=2,
        )

    save_comparison(results, best_name)
    plot_model_comparison(results)
    plot_roc_curves(roc_data)
    plot_confusion_matrix(
        best_model,
        X_test,
        y_test,
        best_name,
    )

    print("\nSaved files:")
    print("Model:", model_path)
    print("Metadata:", metadata_path)
    print("Comparison:", results_dir / "comparison.csv")
    print("Charts:", results_dir.resolve())


if __name__ == "__main__":
    main()
