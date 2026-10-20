"""Optional applicant email and operator alerts for loan prediction outcomes."""

from __future__ import annotations

import os
from datetime import datetime, timezone

import boto3
from dotenv import load_dotenv

from services.s3_storage import PROJECT_ROOT


def send_loan_notification(recipient_email: str | None, event: str, error_type: str | None = None) -> dict:
    """Send opted-in applicant messages via SES and technical alerts via SNS.

    Sending is disabled unless FININTEL_EMAIL_NOTIFICATIONS_ENABLED=true.
    Applicant messages intentionally omit model probabilities and private inputs.
    """
    load_dotenv(PROJECT_ROOT / ".env")
    enabled = os.getenv("FININTEL_EMAIL_NOTIFICATIONS_ENABLED", "false").strip().lower() == "true"
    if not enabled:
        return {"enabled": False, "applicant_email_sent": False, "operations_alert_sent": False}

    region = os.getenv("AWS_DEFAULT_REGION", os.getenv("AWS_REGION", "us-east-1"))
    profile = os.getenv("AWS_PROFILE")
    session = boto3.Session(profile_name=profile, region_name=region) if profile else boto3.Session(region_name=region)
    result = {
        "enabled": True,
        "applicant_email_sent": False,
        "operations_alert_sent": False,
        "applicant_error": None,
        "operations_error": None,
    }
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if event == "not_approved":
        subject = "FinIntel AI loan application update"
        body = (
            "FinIntel AI's experimental model estimate suggests this application may not meet "
            "the learned approval pattern. This is not a bank decision or a formal credit denial. "
            "Please contact the relevant financial institution for a review."
        )
    elif event == "technical_failure":
        subject = "FinIntel AI loan estimate unavailable"
        body = (
            "FinIntel AI could not generate an experimental loan estimate at this time. "
            "Please try again later or contact the application support team."
        )
    else:
        raise ValueError("Unsupported loan notification event.")

    sender = os.getenv("FININTEL_SES_FROM_EMAIL")
    if recipient_email:
        if not sender:
            result["applicant_error"] = "SenderNotConfigured"
        else:
            try:
                session.client("ses", region_name=region).send_email(
                    Source=sender,
                    Destination={"ToAddresses": [recipient_email]},
                    Message={
                        "Subject": {"Data": subject, "Charset": "UTF-8"},
                        "Body": {"Text": {"Data": f"{body}\n\nGenerated: {timestamp}", "Charset": "UTF-8"}},
                    },
                )
                result["applicant_email_sent"] = True
            except Exception as error:
                result["applicant_error"] = type(error).__name__

    if event == "technical_failure" or result["applicant_error"]:
        topic_arn = os.getenv("FININTEL_SNS_TOPIC_ARN")
        if topic_arn:
            try:
                session.client("sns", region_name=region).publish(
                    TopicArn=topic_arn,
                    Subject="FinIntel AI loan notification error",
                    Message=(
                        f"Loan notification event: {event}. "
                        f"Model error type: {error_type or 'None'}. "
                        f"Email delivery error: {result['applicant_error'] or 'None'}. "
                        f"Time: {timestamp}. No applicant email, loan inputs, or stack trace is included."
                    ),
                )
                result["operations_alert_sent"] = True
            except Exception as error:
                result["operations_error"] = type(error).__name__

    return result
