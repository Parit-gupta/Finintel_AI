# FinIntel AI demo and storage setup

## Local demo

From `E:\Project_1`, activate the existing environment and start Streamlit:

```powershell
.\venv\Scripts\Activate.ps1
python -m streamlit run frontend\app.py
```

The sidebar now has a standalone page for each decision workflow, alongside the combined Manual Decision Lab. The transaction screen combines a trained fraud probability with separate operational rules. Account anomaly and branch-profit outputs are trained-model results; withdrawal validation, the separate fraud-risk screen, and ticket escalation are rule-based. All results are demonstrations, not bank decisions.

## Decision history persistence

The app always appends decisions to `datasets\processed\manual_decision_history.csv`. When `.env` has `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` (or `DATABASE_URL`), it also creates and writes the `manual_decision_history` PostgreSQL table. The Saved decision history view reads the database and merges any local-only history. If PostgreSQL is unreachable, the local CSV remains available and the UI reports the fallback.

The app's PostgreSQL history table is created automatically on its first read or write. It is separate from the ETL staging tables.

## Private S3 archive

The helper uses the standard AWS credential chain. On the configured local PowerShell session, set the profile paths without displaying the credentials file:

```powershell
$env:AWS_CONFIG_FILE = "E:\Project_1\aws_config\config"
$env:AWS_SHARED_CREDENTIALS_FILE = "E:\Project_1\aws_config\credentials"
$env:AWS_PROFILE = "finintel"
$env:AWS_DEFAULT_REGION = "us-east-1"
```

Install the dependency if needed, then archive the model artifacts and compact loan dataset:

```powershell
python -m pip install "boto3>=1.34,<2"
python -m services.archive_to_s3
```

The script uploads the trained model artifacts and all 13 CSVs used by the app to the private `models/` and `raw/` prefixes, applies SSE-S3, then checks object size and SHA-256 content. It excludes duplicate `*- Copy.csv` files and unrelated research datasets. The transaction and card-fraud CSVs are large, so the first upload may take time. Credentials are never embedded in the code. The deployed EC2 host should use an IAM instance role scoped to the bucket instead of this local profile.

## Loan email notifications

The Loan Approval AI page has an optional applicant email and opt-in checkbox. A likely rejection sends a carefully worded experimental-estimate notice through SES. A model execution failure sends a generic retry notice through SES and a technical alert to the SNS operations topic. Neither message includes loan inputs, probabilities, or stack traces. Email sending is disabled until `FININTEL_EMAIL_NOTIFICATIONS_ENABLED=true` is configured on the host.

SNS email subscriptions are fixed subscribers and require confirmation. They are appropriate for the operations mailbox. SES is used for applicant-specific email. In the SES sandbox, verify both the sender and each recipient address; request SES production access before sending to arbitrary applicant addresses.

See [aws_setup.md](aws_setup.md) for the console setup sequence and IAM permissions.

## Deployment status

The app and storage integrations are local-ready; an AWS-hosted URL is not created by these steps. A low-cost EC2 demo still needs an instance, a narrowly scoped instance role, a restricted inbound rule, and a startup service. Creating cloud resources can incur charges, so confirm instance size and demo duration before provisioning. Do not expose Streamlit's port to the whole internet; restrict access to the presenter's IP or put it behind an authenticated HTTPS proxy.
