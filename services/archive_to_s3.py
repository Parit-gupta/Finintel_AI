"""Archive trained models and the compact loan dataset to the configured S3 bucket."""

from __future__ import annotations

from pathlib import Path

from services.s3_storage import PROJECT_ROOT, upload_file


APP_DATASETS = [
    "customers.csv",
    "transactions.csv",
    "credit_card_fraud.csv",
    "loan_applications.csv",
    "accounts.csv",
    "branches.csv",
    "branch_performance.csv",
    "employees.csv",
    "banking_products.csv",
    "marketing_campaigns.csv",
    "support_tickets.csv",
    "prediction_history.csv",
    "user_roles.csv",
]


def main() -> None:
    candidates = [
        *sorted((PROJECT_ROOT / "backend" / "ml" / "models").glob("*")),
        *(PROJECT_ROOT / "datasets" / "raw" / name for name in APP_DATASETS),
    ]
    missing = [path for path in candidates if not path.is_file()]
    if missing:
        names = ", ".join(path.name for path in missing)
        raise SystemExit(f"Required archive inputs are missing: {names}")
    for path in candidates:
        relative = path.relative_to(PROJECT_ROOT).as_posix()
        prefix = "models/" if "/models/" in f"/{relative}" else "raw/"
        result = upload_file(path, f"{prefix}{path.name}")
        print(f"Verified s3://{result['bucket']}/{result['key']} ({result['size_bytes']} bytes, sha256={result['sha256']})")


if __name__ == "__main__":
    main()
