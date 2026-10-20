"""Best-effort SNS alerts for unexpected FinIntel AI application errors."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def notify_operations_error(area: str, error: BaseException) -> bool:
    """Publish a minimal technical-failure alert to the configured SNS topic.

    Alerts intentionally contain no applicant/customer data, error text, or stack trace.
    """
    load_dotenv(PROJECT_ROOT / ".env")
    if os.getenv("FININTEL_EMAIL_NOTIFICATIONS_ENABLED", "false").strip().lower() != "true":
        return False
    topic_arn = os.getenv("FININTEL_SNS_TOPIC_ARN")
    if not topic_arn:
        return False
    try:
        import boto3

        region = os.getenv("AWS_DEFAULT_REGION", os.getenv("AWS_REGION", "us-east-1"))
        profile = os.getenv("AWS_PROFILE")
        session = boto3.Session(profile_name=profile, region_name=region) if profile else boto3.Session(region_name=region)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        session.client("sns", region_name=region).publish(
            TopicArn=topic_arn,
            Subject=f"FinIntel AI error: {area}"[:100],
            Message=(
                f"A technical error occurred in FinIntel AI.\n"
                f"Area: {area}\n"
                f"Error type: {type(error).__name__}\n"
                f"Time: {timestamp}\n"
                "Customer inputs, personal data, exception details, and stack traces are omitted."
            ),
        )
        return True
    except Exception:
        # Alert delivery must never prevent the dashboard from showing its own error.
        return False


def alert_failures(area: str):
    """Wrap a dashboard renderer so uncaught failures also reach operations via SNS."""
    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except Exception as error:
                notify_operations_error(area, error)
                import streamlit as st

                recipient = st.session_state.get("decision_result_email", "").strip()
                if recipient:
                    from services.result_email import send_result_email

                    sent, email_error = send_result_email(recipient, area, "TECHNICAL ERROR")
                    if sent:
                        st.info(f"Amazon SES accepted the technical error email for {recipient}. Message ID: {email_error or 'not returned'}.")
                    else:
                        st.warning(f"Technical error email was not sent ({email_error}).")

                st.error(f"{area} could not complete because of a technical error ({type(error).__name__}).")
                return None
        return wrapped
    return decorate
