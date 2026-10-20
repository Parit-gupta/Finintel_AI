# FinIntel AI

FinIntel AI is a Streamlit banking-intelligence demo. It combines data exploration, model-based predictions, and rule-based decision checks in one interface. The outputs are experimental decision support and are **not** real lending, fraud, or account decisions.

## Features

- Explore banking datasets and their trends in interactive charts.
- Review an executive overview, detection centre, dataset explorer, and CSV curve gallery.
- Run loan approval estimates, transaction fraud checks, fraud-risk screening, withdrawal validation, account anomaly checks, branch-profit estimates, and support-ticket prioritization.
- Save decision history to a local CSV, with optional PostgreSQL persistence.
- Optionally email result status through Amazon SES and send operational alerts through Amazon SNS.
- Download private datasets and model artifacts from Amazon S3 when AWS access is configured.
- Run a modular ETL pipeline for extracting, transforming, validating, and loading data.

## Project layout

```text
frontend/       Streamlit application
backend/ml/     Prediction functions and model training scripts
backend/etl/    ETL extraction, transformation, validation, and loading
services/       S3, database, SES, SNS, and decision-history integrations
database/       SQL schema and ER diagram source
datasets/       Local data files (ignored by Git)
docs/           Setup and deployment notes
tests/          Automated tests
```

## Requirements

- Python 3.11 is recommended. Use the same Python/scikit-learn versions that were used to create the model artifacts.
- Git, if you are cloning the repository.
- AWS credentials or an EC2 instance role to download private assets or use SES/SNS/S3 features.
- PostgreSQL is optional; without it, the app keeps decision history in a local CSV.

## Run locally

From the project root, create and activate a virtual environment:

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-app.txt
```

### macOS or Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-app.txt
```

The app reads CSVs from `datasets/raw/` and trained models from `backend/ml/models/`. These data and model files are intentionally excluded from Git. If you have access to the project's private S3 bucket and the required AWS permissions, download them with:

```bash
python -m services.sync_from_s3
```

Then launch Streamlit from the project root:

```bash
python -m streamlit run frontend/app.py
```

Streamlit prints a local URL (usually `http://localhost:8501`). On EC2, use the server's public address only when the instance is running, Streamlit is running, and the security group permits your current public IP on port 8501.

## Configuration

Copy `.env.example` to `.env` and set only the integrations you plan to use. Keep `.env` private; it is excluded from Git. AWS SDK credentials should come from a local AWS profile or an EC2 instance role, not from application source code or the README.

| Variable | Purpose |
| --- | --- |
| `AWS_DEFAULT_REGION` | AWS region, normally `us-east-1` for this project. |
| `FININTEL_S3_BUCKET` | Private bucket used for datasets and model artifacts. |
| `FININTEL_SES_FROM_EMAIL` | Verified SES sender identity. |
| `FININTEL_SES_CONFIGURATION_SET` | Optional SES configuration set for delivery events. |
| `FININTEL_EMAIL_NOTIFICATIONS_ENABLED` | Set to `true` to enable app result emails and configured operational alerts. |
| `FININTEL_SNS_TOPIC_ARN` | Optional SNS topic for operational alerts. |
| `DATABASE_URL` | Optional PostgreSQL connection URL; alternatively use the `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` variables. |

SES sandbox accounts can send only to verified recipient identities. Sending to arbitrary addresses requires SES production access. The sender must also be verified in the configured region.

## EC2 deployment

The application can run on an Amazon Linux EC2 instance. Install the app dependencies, copy or clone the source, attach a least-privilege IAM instance role, download the private assets with `python -m services.sync_from_s3`, and start Streamlit:

```bash
cd ~/finintel
source .venv/bin/activate
PYTHONPATH="$PWD" python -m streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501
```

Restrict inbound access to port 8501 to the demo users' IP addresses. Do not open SSH or the Streamlit port to the entire internet. See [docs/demo_and_cloud.md](docs/demo_and_cloud.md) and [docs/aws_setup.md](docs/aws_setup.md) for the project's deployment notes.

## ETL and tests

The ETL code is under `backend/etl/`. Some ETL settings are machine-specific and may need adjustment before running on another computer. Review the relevant configuration and database requirements in `docs/` first.

Run the Python tests from the project root with:

```bash
python -m pytest
```

## Responsible use

- Predictions and risk labels are demonstrations, not calibrated financial-risk estimates or actual banking decisions.
- Review decisions with qualified staff before taking action.
- Use synthetic or appropriately authorized data. Do not commit customer data, secrets, AWS credentials, private keys, model binaries, or local decision history.
- AWS resources and services can incur charges. Check AWS pricing and account usage before enabling optional services.
