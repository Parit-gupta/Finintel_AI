"""Send minimal decision-result emails to a recipient selected in the app."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def decision_status(outcome: str) -> str:
    normalized = outcome.strip().upper()
    if normalized in {"TECHNICAL ERROR", "PREDICTION FAILED"}:
        return "ERROR"
    if normalized in {"LIKELY APPROVED", "LIKELY SUCCESSFUL", "WITHDRAWAL LIKELY SUCCESSFUL", "LOW FRAUD RISK", "NORMAL PATTERN", "STANDARD QUEUE"}:
        return "PASS"
    if normalized in {"PENDING REVIEW", "MEDIUM FRAUD RISK", "ANOMALY - REVIEW", "PRIORITY REVIEW"}:
        return "REVIEW"
    if normalized in {"LIKELY REJECTED", "CREDIT LIKELY REJECTED", "BLOCKED / REVIEW", "HIGH FRAUD RISK", "WITHDRAWAL DECLINED", "IMMEDIATE ESCALATION"}:
        return "FAIL"
    return "RESULT"


def send_result_email(recipient_email: str, decision_type: str, outcome: str) -> tuple[bool, str | None]:
    """Email a decision status without sending financial inputs or personal data."""
    load_dotenv(PROJECT_ROOT / ".env")
    if os.getenv("FININTEL_EMAIL_NOTIFICATIONS_ENABLED", "false").strip().lower() != "true":
        return False, "notifications disabled"
    sender = os.getenv("FININTEL_SES_FROM_EMAIL")
    if not sender:
        return False, "FININTEL_SES_FROM_EMAIL is not configured"
    if "@" not in recipient_email or "@" not in sender:
        return False, "invalid sender or recipient email"

    try:
        region = os.getenv("AWS_DEFAULT_REGION", os.getenv("AWS_REGION", "us-east-1"))
        profile = os.getenv("AWS_PROFILE")
        session = boto3.Session(profile_name=profile, region_name=region) if profile else boto3.Session(region_name=region)
        status = decision_status(outcome)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        request = {
            "Source": sender,
            "Destination": {"ToAddresses": [recipient_email]},
            "Message": {
                "Subject": {"Data": f"FinIntel AI result: {status} - {decision_type}", "Charset": "UTF-8"},
                "Body": {
                    "Text": {
                        "Data": (
                            "Your FinIntel AI demo result is ready.\n"
                            f"Case: {decision_type}\n"
                            f"Status: {status}\n"
                            f"Outcome: {outcome}\n"
                            f"Time: {timestamp}\n\n"
                            "This is an experimental result, not a bank decision. Financial inputs and personal data are omitted."
                        ),
                        "Charset": "UTF-8",
                    }
                },
            },
        }
        configuration_set = os.getenv("FININTEL_SES_CONFIGURATION_SET", "").strip()
        if configuration_set:
            request["ConfigurationSetName"] = configuration_set
        response = session.client("ses", region_name=region).send_email(**request)
        return True, response.get("MessageId")
    except ClientError as error:
        # Preserve the actionable SES/IAM error instead of hiding it behind
        # the generic ``ClientError`` type shown in the dashboard.
        details = error.response.get("Error", {})
        code = details.get("Code", "ClientError")
        message = details.get("Message", "AWS rejected the email request.")
        return False, f"{code}: {message}"
    except Exception as error:
        return False, f"{type(error).__name__}: {error}"
