"""FinIntel AI: CSV-first banking analytics and detection workspace."""

from __future__ import annotations

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.ml.loan_predict import predict_loan_approval
from services.ops_alerts import alert_failures, notify_operations_error
from services.result_email import send_result_email

import pandas as pd

import plotly.express as px
import plotly.io as pio

import streamlit as st



DATA_DIR = PROJECT_ROOT / "datasets" / "raw"
CURVES_DIR = PROJECT_ROOT / "reports" / "csv_curves"

st.set_page_config(page_title="FinIntel AI", page_icon="Bank", layout="wide")

st.markdown("""<style>.block-container{padding-top:1.6rem}.section-card{background:#111a25;border:1px solid #2d4056;border-radius:12px;padding:16px;margin:8px 0 16px}[data-testid="stMetric"]{background:#17202c;border:1px solid #2d4056;border-radius:12px;padding:15px}</style>""", unsafe_allow_html=True)



# Add a new source here: it automatically receives overview, quality, explorer and detection views.

DATASETS = {

    "customers": ("customers.csv", "Customer Intelligence", "Customer profiles, income, demographics, and KYC status.", "KYC and customer-profile review"),

    "transactions": ("transactions.csv", "Transaction Monitoring", "Payment activity and transfer behaviour.", "Suspicious transaction detection"),

    "fraud": ("credit_card_fraud.csv", "Card Fraud Monitoring", "Card transaction features and confirmed fraud labels.", "Confirmed fraud analysis"),

    "loans": ("loan_applications.csv", "Loan & Credit Risk", "Loan applications, assets, CIBIL scores, and decisions.", "Credit-risk and approval detection"),

    "accounts": ("accounts.csv", "Account Health", "Account balances, account types, and status.", "Dormant and low-balance account detection"),

    "branches": ("branches.csv", "Branch Directory", "Branch locations, management, and staffing.", "Branch staffing review"),

    "performance": ("branch_performance.csv", "Branch Performance", "Revenue, expenses, profit, satisfaction, and fraud cases.", "Underperforming branch detection"),

    "employees": ("employees.csv", "Workforce Analytics", "Employee roles, departments, salaries, and joining dates.", "Workforce outlier detection"),

    "products": ("banking_products.csv", "Banking Products", "Product catalogue and interest rates.", "Product-rate outlier detection"),

    "marketing": ("marketing_campaigns.csv", "Campaign Performance", "Customer offers, channels, and campaign acceptance.", "Campaign conversion detection"),

    "tickets": ("support_tickets.csv", "Support Operations", "Customer issues, priorities, and resolution status.", "High-priority unresolved ticket detection"),

    "predictions": ("prediction_history.csv", "Model Audit", "Stored predictions, probabilities, and timestamps.", "Low-confidence prediction detection"),

    "users": ("user_roles.csv", "Access & Roles", "User accounts, roles, branch assignments, and status.", "User-access review"),

}


DECISION_PAGES = {
    "Transaction Decision": ("Transaction decision", "Trained fraud model + operational rules", "Estimate transaction fraud risk, then apply account, balance, KYC, and high-value checks separately."),
    "Fraud Risk Screening": ("Fraud risk screening", "Rule-based screening", "Screen beneficiary, retry, device, watch-list, account-age, and transaction-amount signals."),
    "Account Withdrawal Check": ("Account withdrawal check", "Business rules", "Check account status, available balance, and the required minimum balance before a simulated withdrawal."),
    "Account Anomaly Check": ("Account anomaly check", "Isolation Forest model", "Compare an account profile with patterns learned from the account dataset."),
    "Branch Profit Prediction": ("Branch profit prediction", "Trained regression model", "Estimate branch profit and inspect how the prediction changes across fraud-case scenarios."),
    "Support Ticket Priority": ("Support ticket priority", "Business rules", "Route critical and high-priority tickets for escalation; standardize lower-priority handling."),
    "Saved Decision History": ("Saved decision history", "CSV + optional PostgreSQL", "Review and download decisions made in the interactive decision dashboards."),
}

MANUAL_DECISION_MENU = ["Manual Decision Lab", *DECISION_PAGES.keys(), "Loan Approval AI"]



@st.cache_data(show_spinner=False)
@alert_failures("CSV loading")
def load_csv(file_name: str, sample_rows: int = 100_000):

    path = DATA_DIR / file_name

    if not path.exists(): return pd.DataFrame(), 0, False

    sampled = path.stat().st_size > 35 * 1024 * 1024

    frame = pd.read_csv(path, nrows=sample_rows if sampled else None, low_memory=False)

    frame.columns = frame.columns.astype(str).str.strip()

    return frame, path.stat().st_size, sampled



def has(frame, *columns): return all(column in frame.columns for column in columns)

def money(value): return f"INR {value:,.0f}"



def render_csv_curve_gallery():
    st.title("CSV Curve Gallery")
    st.caption("Interactive distribution curves, category trends, and time-series charts generated from the project CSVs.")
    manifest_path = CURVES_DIR / "manifest.json"
    if not manifest_path.exists():
        st.info("Chart files have not been generated yet. Run `python scripts/generate_csv_curves.py` from the project folder.")
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    datasets = manifest.get("datasets", {})
    if not datasets:
        st.warning("No CSV datasets were found in the chart manifest.")
        return
    selected = st.selectbox("Choose a CSV", list(datasets), format_func=lambda item: f"{datasets[item]['label']} — {datasets[item]['csv']}")
    dataset = datasets[selected]
    st.caption(f"Source: {dataset['csv']} · {dataset.get('rows', 0):,} rows plotted" + (f" · first {manifest['sample_limit']:,} rows sampled" if dataset.get("sampled") else ""))
    if not dataset.get("charts"):
        st.info("This CSV has no usable rows or chartable columns.")
        return
    for index, chart in enumerate(dataset["charts"]):
        json_path = CURVES_DIR / chart["json"]
        html_path = CURVES_DIR / chart["html"]
        if not json_path.exists():
            st.warning(f"Chart file is missing: {json_path.name}")
            continue
        st.plotly_chart(pio.from_json(json_path.read_text(encoding="utf-8")), use_container_width=True, key=f"csv_curve_{selected}_{index}")
        st.caption(chart["description"])
        if html_path.exists():
            st.download_button("Download interactive HTML chart", html_path.read_bytes(), file_name=html_path.name, mime="text/html", key=f"csv_curve_download_{selected}_{index}")
        png_path = CURVES_DIR / chart.get("png", "")
        if png_path.exists():
            st.download_button("Download PNG image", png_path.read_bytes(), file_name=png_path.name, mime="image/png", key=f"csv_curve_png_{selected}_{index}")


def save_decision(decision_type, outcome, details, recipient_email=None):

    """Append a manual result locally so decisions remain auditable between runs."""
    from services.decision_store import save_decision as persist_decision

    _, status = persist_decision(decision_type, outcome, details)
    if status and "failed" in status.lower():
        st.warning(status)
        notify_operations_error("Decision history storage", RuntimeError("Decision persistence failed"))
    if recipient_email is None:
        recipient_email = st.session_state.get("decision_result_email", "").strip()
    if recipient_email:
        email_sent, email_error = send_result_email(recipient_email, decision_type, outcome)
        if email_sent:
            st.info(f"Amazon SES accepted the result email for {recipient_email}. Message ID: {email_error or 'not returned'}.")
        else:
            st.warning(f"Decision result email was not sent ({email_error}).")


def render_loan_notification_status(delivery):
    if not delivery["enabled"]:
        st.caption("Email notifications are not enabled yet; configure AWS SES/SNS to activate them.")
        return
    if delivery["applicant_email_sent"]:
        st.info("The requested loan update was emailed. It is clearly labeled as an experimental estimate, not a bank decision.")
    elif delivery.get("applicant_error"):
        st.warning(f"Applicant email was not sent ({delivery['applicant_error']}).")
    if delivery["operations_alert_sent"]:
        st.caption("The configured SNS operations topic was notified.")
    elif delivery.get("operations_error"):
        st.warning(f"SNS operations alert was not sent ({delivery['operations_error']}).")



def render_trend_chart(key, frame):

    """Line charts use time/sequence fields only where the source supports them."""

    if key == "transactions" and has(frame, "step", "amount"):

        trend = frame.groupby("step", as_index=False).amount.sum()

        st.plotly_chart(px.line(trend, x="step", y="amount", title="Transaction amount trend by step"), use_container_width=True)

    elif key == "fraud" and has(frame, "Time", "Class"):

        trend = frame.groupby("Time", as_index=False).Class.sum()

        st.plotly_chart(px.line(trend, x="Time", y="Class", title="Confirmed fraud trend over time"), use_container_width=True)

    elif key == "performance" and has(frame, "month", "year", "profit"):

        order = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

        copy = frame.copy(); copy["month"] = pd.Categorical(copy["month"], categories=order, ordered=True)

        trend = copy.sort_values(["year", "month"])

        st.plotly_chart(px.line(trend, x="month", y="profit", color="branch_id", title="Branch profit trend by month"), use_container_width=True)

    elif key == "tickets" and has(frame, "opened_date", "ticket_id"):

        trend = frame.assign(opened_date=pd.to_datetime(frame.opened_date, errors="coerce")).dropna(subset=["opened_date"]).groupby("opened_date", as_index=False).ticket_id.count()

        st.plotly_chart(px.line(trend, x="opened_date", y="ticket_id", title="Support tickets opened over time"), use_container_width=True)



def render_additional_charts(key, frame):
    """Render extra comparisons for the selected dataset in Detection Centre."""
    st.subheader("More charts")
    left, right = st.columns(2)

    if key == "customers" and has(frame, "age", "annual_income", "employment_type"):
        with left: st.plotly_chart(px.histogram(frame, x="age", nbins=25, title="Customer age distribution"), use_container_width=True)
        with right: st.plotly_chart(px.box(frame, x="employment_type", y="annual_income", points=False, title="Annual income by employment type"), use_container_width=True)
    elif key == "transactions" and has(frame, "step", "type", "amount", "isFraud"):
        fraud_step = frame.groupby("step", as_index=False).isFraud.mean(); fraud_step["fraud_rate"] = fraud_step.isFraud * 100
        by_type = frame.groupby("type", as_index=False).agg(transactions=("amount", "size"), amount=("amount", "sum"))
        with left: st.plotly_chart(px.line(fraud_step, x="step", y="fraud_rate", title="Fraud rate by transaction step", labels={"fraud_rate": "Fraud rate (%)"}), use_container_width=True)
        with right: st.plotly_chart(px.bar(by_type, x="type", y="transactions", color="amount", title="Transaction volume by type"), use_container_width=True)
    elif key == "fraud" and has(frame, "Time", "Class", "Amount"):
        by_hour = frame.assign(hour=(frame.Time // 3600).astype("Int64")).groupby("hour", as_index=False).agg(fraud=("Class", "sum"))
        sample = frame.sample(min(len(frame), 6000), random_state=7) if len(frame) else frame
        with left: st.plotly_chart(px.line(by_hour, x="hour", y="fraud", markers=True, title="Confirmed fraud by hour"), use_container_width=True)
        with right: st.plotly_chart(px.box(sample, x="Class", y="Amount", title="Transaction amount by fraud label"), use_container_width=True)
    elif key == "loans" and has(frame, "loan_status", "income_annum", "loan_amount"):
        counts = frame.loan_status.fillna("Missing").astype(str).str.strip().value_counts().rename_axis("loan_status").reset_index(name="applications")
        sample = frame.sample(min(len(frame), 5000), random_state=7) if len(frame) else frame
        with left: st.plotly_chart(px.bar(counts, x="loan_status", y="applications", color="loan_status", title="Applications by decision"), use_container_width=True)
        with right: st.plotly_chart(px.scatter(sample, x="income_annum", y="loan_amount", color="loan_status", opacity=0.55, title="Requested loan vs annual income"), use_container_width=True)
    elif key == "accounts" and has(frame, "account_type", "balance", "status"):
        counts = frame.groupby(["account_type", "status"], dropna=False).size().reset_index(name="accounts")
        with left: st.plotly_chart(px.box(frame, x="account_type", y="balance", points=False, title="Balance by account type"), use_container_width=True)
        with right: st.plotly_chart(px.bar(counts, x="account_type", y="accounts", color="status", barmode="stack", title="Account status by type"), use_container_width=True)
    elif key == "branches" and has(frame, "city", "employees", "branch_name"):
        city = frame.groupby("city", as_index=False).agg(employees=("employees", "sum"))
        top = frame.nlargest(15, "employees")
        with left: st.plotly_chart(px.bar(city, x="city", y="employees", title="Employees by city"), use_container_width=True)
        with right: st.plotly_chart(px.bar(top, x="branch_name", y="employees", title="Largest branches by staff"), use_container_width=True)
    elif key == "performance" and has(frame, "year", "month", "profit", "revenue", "customer_satisfaction"):
        order = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        monthly = frame.groupby(["year", "month"], as_index=False).profit.sum(); monthly["month"] = pd.Categorical(monthly.month, categories=order, ordered=True); monthly = monthly.sort_values(["year", "month"])
        with left: st.plotly_chart(px.line(monthly, x="month", y="profit", color="year", markers=True, title="Total branch profit by month"), use_container_width=True)
        with right: st.plotly_chart(px.scatter(frame, x="customer_satisfaction", y="profit", size="revenue", color="fraud_cases" if "fraud_cases" in frame else None, title="Satisfaction vs profit"), use_container_width=True)
    elif key == "employees" and has(frame, "department", "salary", "designation"):
        counts = frame.department.fillna("Missing").astype(str).value_counts().head(12).rename_axis("department").reset_index(name="employees")
        with left: st.plotly_chart(px.box(frame, x="department", y="salary", points=False, title="Salary by department"), use_container_width=True)
        with right: st.plotly_chart(px.bar(counts, x="department", y="employees", title="Employees by department"), use_container_width=True)
    elif key == "products" and has(frame, "product_name", "interest_rate"):
        top = frame.nlargest(20, "interest_rate")
        with left: st.plotly_chart(px.bar(top, x="interest_rate", y="product_name", orientation="h", title="Products by interest rate"), use_container_width=True)
        with right: st.plotly_chart(px.histogram(frame, x="interest_rate", nbins=20, title="Interest-rate distribution"), use_container_width=True)
    elif key == "marketing" and has(frame, "offer", "channel", "accepted"):
        accepted = frame.accepted.astype(str).str.strip().str.lower().isin(["yes", "true", "1", "accepted"])
        campaign = frame.assign(accepted_flag=accepted).groupby(["offer", "channel"], dropna=False).accepted_flag.mean().mul(100).reset_index(name="conversion_percent")
        channels = frame.groupby("channel", dropna=False).size().reset_index(name="contacts")
        with left: st.plotly_chart(px.bar(campaign, x="offer", y="conversion_percent", color="channel", barmode="group", title="Offer conversion by channel"), use_container_width=True)
        with right: st.plotly_chart(px.pie(channels, names="channel", values="contacts", hole=0.45, title="Contacts by channel"), use_container_width=True)
    elif key == "tickets" and has(frame, "opened_date", "priority", "status", "issue_type"):
        dated = frame.assign(opened_month=pd.to_datetime(frame.opened_date, errors="coerce").dt.to_period("M").dt.to_timestamp()).dropna(subset=["opened_month"])
        monthly = dated.groupby("opened_month", as_index=False).ticket_id.count()
        issues = frame[frame.issue_type.isin(frame.issue_type.value_counts().head(10).index)].groupby(["issue_type", "priority"], dropna=False).size().reset_index(name="tickets")
        with left: st.plotly_chart(px.line(monthly, x="opened_month", y="ticket_id", markers=True, title="Tickets opened per month", labels={"ticket_id": "Tickets"}), use_container_width=True)
        with right: st.plotly_chart(px.bar(issues, x="issue_type", y="tickets", color="priority", barmode="stack", title="Top ticket issues by priority"), use_container_width=True)
    elif key == "predictions" and has(frame, "timestamp", "probability", "model", "prediction"):
        dated = frame.assign(timestamp=pd.to_datetime(frame.timestamp, errors="coerce")).dropna(subset=["timestamp"])
        trend = dated.groupby([pd.Grouper(key="timestamp", freq="D"), "model"], dropna=False).probability.mean().reset_index()
        outcomes = frame.groupby(["model", "prediction"], dropna=False).size().reset_index(name="predictions")
        with left: st.plotly_chart(px.line(trend, x="timestamp", y="probability", color="model", markers=True, title="Average confidence over time"), use_container_width=True)
        with right: st.plotly_chart(px.bar(outcomes, x="model", y="predictions", color="prediction", barmode="group", title="Predictions by model and outcome"), use_container_width=True)
    elif key == "users" and has(frame, "role", "status", "last_login"):
        roles = frame.groupby(["role", "status"], dropna=False).size().reset_index(name="users")
        dated = frame.assign(last_login=pd.to_datetime(frame.last_login, errors="coerce")).dropna(subset=["last_login"])
        logins = dated.groupby(pd.Grouper(key="last_login", freq="D")).size().reset_index(name="logins")
        with left: st.plotly_chart(px.bar(roles, x="role", y="users", color="status", barmode="stack", title="Roles by account status"), use_container_width=True)
        with right: st.plotly_chart(px.line(logins, x="last_login", y="logins", markers=True, title="User logins over time"), use_container_width=True)


def render_probability_chart(probability, title, threshold=50):

    chart = pd.DataFrame({"Result": ["Risk probability", "Review threshold"], "Percent": [probability, threshold]})

    figure = px.bar(chart, x="Result", y="Percent", text="Percent", range_y=[0, 100], title=title, color="Result", color_discrete_sequence=["#e76f51", "#457b9d"])

    figure.update_traces(texttemplate="%{text:.1f}%", textposition="outside")

    st.plotly_chart(figure, use_container_width=True)



def render_saved_history_charts(history):

    history["timestamp_utc"] = pd.to_datetime(history["timestamp_utc"], errors="coerce")

    daily = history.dropna(subset=["timestamp_utc"]).groupby(history["timestamp_utc"].dt.date, as_index=False).size()

    left, right = st.columns(2)

    with left:

        if not daily.empty: st.plotly_chart(px.line(daily, x="timestamp_utc", y="size", markers=True, title="Manual decisions over time", labels={"size":"Decisions", "timestamp_utc":"Date"}), use_container_width=True)

    with right:

        st.plotly_chart(px.histogram(history, x="decision_type", color="outcome", barmode="group", title="Saved decisions by outcome"), use_container_width=True)



def render_quality(frame):

    profile = pd.DataFrame({"Column": frame.columns, "Data type": frame.dtypes.astype(str).values, "Missing values": frame.isna().sum().values, "Missing %": frame.isna().mean().mul(100).round(2).values, "Distinct values": frame.nunique(dropna=True).values}).sort_values("Missing values", ascending=False)

    st.subheader("Data quality checks"); st.dataframe(profile, use_container_width=True, hide_index=True)

    duplicates = int(frame.duplicated().sum())

    (st.warning if duplicates else st.success)(f"{duplicates:,} duplicate rows found in the loaded data." if duplicates else "No duplicate rows found in the loaded data.")



def render_detection(key, frame):

    st.subheader(DATASETS[key][3])

    if key == "customers" and has(frame, "kyc_status", "annual_income"):

        kyc = frame.kyc_status.fillna("Missing").astype(str); review = frame[~kyc.str.lower().eq("verified")]

        a,b,c=st.columns(3); a.metric("KYC review needed",f"{len(review):,}"); b.metric("Verified",f"{kyc.str.lower().eq('verified').sum():,}"); c.metric("Income outliers",f"{(frame.annual_income > frame.annual_income.quantile(.99)).sum():,}")

        st.plotly_chart(px.bar(kyc.value_counts().reset_index(),x="kyc_status",y="count",title="KYC status"),use_container_width=True); st.dataframe(review.head(200),use_container_width=True,hide_index=True)

    elif key == "transactions" and has(frame,"amount","isFraud","type"):

        threshold=frame.amount.quantile(.99); suspicious=frame[(frame.amount>=threshold)|(frame.isFraud==1)|(frame.get("isFlaggedFraud",0)==1)]

        a,b,c=st.columns(3); a.metric("High-value threshold",money(threshold)); b.metric("Confirmed fraud",f"{(frame.isFraud==1).sum():,}"); c.metric("Suspicious records",f"{len(suspicious):,}")

        st.plotly_chart(px.box(frame,x="type",y="amount",points=False,title="Transaction amount by type"),use_container_width=True); st.dataframe(suspicious.sort_values("amount",ascending=False).head(200),use_container_width=True,hide_index=True)

    elif key == "fraud" and has(frame,"Class","Amount"):

        fraud=frame[frame.Class==1]; a,b,c=st.columns(3); a.metric("Fraud records",f"{len(fraud):,}"); b.metric("Fraud rate",f"{frame.Class.mean()*100:.3f}%"); c.metric("Largest fraud amount",money(fraud.Amount.max() if len(fraud) else 0))

        st.plotly_chart(px.histogram(frame,x="Amount",color="Class",nbins=50,title="Fraud versus legitimate transaction amounts"),use_container_width=True); st.dataframe(fraud.sort_values("Amount",ascending=False).head(200),use_container_width=True,hide_index=True)

    elif key == "loans" and has(frame,"cibil_score","loan_status","loan_amount"):

        rejected=frame.loan_status.astype(str).str.strip().str.lower().eq("rejected"); risk=frame[(frame.cibil_score<650)|rejected]

        a,b,c=st.columns(3); a.metric("High-risk / rejected",f"{len(risk):,}"); b.metric("Average CIBIL",f"{frame.cibil_score.mean():.0f}"); c.metric("Average loan request",money(frame.loan_amount.mean()))

        st.plotly_chart(px.box(frame,x="loan_status",y="cibil_score",title="CIBIL score by application decision"),use_container_width=True); st.dataframe(risk.sort_values("cibil_score").head(200),use_container_width=True,hide_index=True)

    elif key == "accounts" and has(frame,"balance","status"):

        review=frame[frame.status.astype(str).str.lower().isin(["dormant","frozen","closed"])]; low=frame[frame.balance<=frame.balance.quantile(.05)]

        a,b,c=st.columns(3); a.metric("Review-status accounts",f"{len(review):,}"); b.metric("Lowest 5% balance",money(frame.balance.quantile(.05))); c.metric("Low-balance accounts",f"{len(low):,}")

        st.dataframe(pd.concat([review,low]).drop_duplicates().head(200),use_container_width=True,hide_index=True)

    elif key == "performance" and has(frame,"profit","customer_satisfaction","fraud_cases","revenue"):

        review=frame[(frame.profit<0)|(frame.customer_satisfaction<3)|(frame.fraud_cases>frame.fraud_cases.quantile(.90))]

        a,b,c=st.columns(3); a.metric("Records needing review",f"{len(review):,}"); b.metric("Loss-making records",f"{(frame.profit<0).sum():,}"); c.metric("Average satisfaction",f"{frame.customer_satisfaction.mean():.2f}")

        st.plotly_chart(px.scatter(frame,x="revenue",y="profit",size="fraud_cases",color="customer_satisfaction",title="Revenue, profit, and fraud exposure"),use_container_width=True); st.dataframe(review.head(200),use_container_width=True,hide_index=True)

    elif key == "tickets" and has(frame,"priority","status"):

        review=frame[frame.priority.astype(str).str.lower().isin(["high","critical"])&~frame.status.astype(str).str.lower().isin(["closed","resolved"])]

        st.metric("Urgent unresolved tickets",f"{len(review):,}"); st.plotly_chart(px.histogram(frame,x="priority",color="status",barmode="group",title="Tickets by priority and status"),use_container_width=True); st.dataframe(review.head(200),use_container_width=True,hide_index=True)

    elif key == "marketing" and has(frame,"channel","accepted"):

        accepted=frame.accepted.astype(str).str.lower().isin(["yes","true","1","accepted"]); by_channel=frame.assign(accepted_flag=accepted).groupby("channel",dropna=False).accepted_flag.mean().mul(100).reset_index()

        st.metric("Overall conversion",f"{accepted.mean()*100:.1f}%"); st.plotly_chart(px.bar(by_channel,x="channel",y="accepted_flag",title="Conversion rate by channel",labels={"accepted_flag":"Conversion %"}),use_container_width=True); st.dataframe(by_channel.sort_values("accepted_flag"),use_container_width=True,hide_index=True)

    elif key == "predictions" and has(frame,"probability"):

        review=frame[frame.probability<.60]; st.metric("Predictions below 60% confidence",f"{len(review):,}"); st.plotly_chart(px.histogram(frame,x="probability",nbins=20,title="Prediction confidence distribution"),use_container_width=True); st.dataframe(review.head(200),use_container_width=True,hide_index=True)

    elif key == "users" and has(frame,"role","status"):

        review=frame[frame.status.astype(str).str.lower()!="active"]; st.metric("Non-active user accounts",f"{len(review):,}"); st.plotly_chart(px.histogram(frame,x="role",color="status",barmode="group",title="User access by role and status"),use_container_width=True); st.dataframe(review.head(200),use_container_width=True,hide_index=True)

    else:

        st.info("This source currently uses universal data-quality and outlier review. Add agreed business thresholds here for a tailored detection rule.")

        numbers=frame.select_dtypes(include="number").columns.tolist()

        if numbers: st.plotly_chart(px.box(frame,y=numbers[:8],title="Numeric outlier review"),use_container_width=True)



@alert_failures("Decision dashboards")
def render_manual_decision_lab(selected_case=None):

    """Render the combined lab or one standalone decision dashboard."""

    if selected_case is None:
        st.title("Manual Decision Lab")
        st.caption("Explore the decision workflows in one place. Results are recorded in decision history; these simulations do not change account balances or banking records.")
        lab = st.selectbox("Choose a decision", ["Loan / credit decision", *[details[0] for details in DECISION_PAGES.values()]])
    else:
        lab, approach, description = DECISION_PAGES[selected_case]
        st.title(selected_case)
        st.caption(description)
        st.markdown(f"**Decision method:** {approach}  ·  **Mode:** Interactive decision-support simulation")



    recipient_email = st.text_input(
        "Email this result to (optional)",
        value=st.session_state.get("decision_result_email", ""),
        key=f"decision_page_email_{selected_case or 'manual'}",
        placeholder="you@example.com",
        help="A result email is sent after each decision. Leave blank to use the shared recipient in the sidebar.",
    ).strip()

    def record_decision(decision_type, outcome, details):
        save_decision(decision_type, outcome, details, recipient_email or None)

    if lab == "Loan / credit decision":

        st.subheader("Loan application")

        left, middle, right = st.columns(3)

        with left:

            dependents = st.number_input("Dependents", 0, 10, 2)

            education = st.selectbox("Education", ["Graduate", "Not Graduate"])

            self_employed = st.selectbox("Self employed", ["No", "Yes"])

            cibil = st.number_input("CIBIL score", 300, 900, 735)

        with middle:

            income = st.number_input("Annual income (INR)", 1, value=750000, step=10000)

            amount = st.number_input("Loan amount (INR)", 1, value=1500000, step=10000)

            term = st.number_input("Loan term (years)", 1, 30, 15)

        with right:

            residential = st.number_input("Residential assets (INR)", 0, value=500000, step=10000)

            commercial = st.number_input("Commercial assets (INR)", 0, value=0, step=10000)

            luxury = st.number_input("Luxury assets (INR)", 0, value=200000, step=10000)

            bank = st.number_input("Bank assets (INR)", 0, value=100000, step=10000)

        if st.button("Evaluate loan application", type="primary"):

            data = {"no_of_dependents": dependents, "education": education, "self_employed": self_employed, "income_annum": income, "loan_amount": amount, "loan_term": term, "cibil_score": cibil, "residential_assets_value": residential, "commercial_assets_value": commercial, "luxury_assets_value": luxury, "bank_asset_value": bank}

            try:

                from backend.ml.loan_predict import predict_loan_approval

                result = predict_loan_approval(data)

                if not result["valid"]:

                    st.error("Please correct the submitted values.")

                    st.json(result["errors"])

                elif result["decision"] == "APPROVED":

                    st.success(f"CREDIT LIKELY APPROVED — probability {result['approval_probability']}%")

                    st.caption(f"Model: {result['model_used']} | Risk: {result['risk_level']}")

                    st.write("Factors: " + "; ".join(result["key_factors"]))

                    render_probability_chart(result["approval_probability"], "Loan approval probability")

                    st.info("Why this result: the model found a combination of credit score, income, requested amount, repayment term, and assets similar to previously approved applications. The listed factors are explanatory signals, not a final bank approval.")

                    record_decision("loan_credit", "LIKELY APPROVED", f"probability={result['approval_probability']}; cibil={cibil}; amount={amount}; income={income}")

                else:

                    st.error(f"CREDIT LIKELY REJECTED — approval probability {result['approval_probability']}%")

                    st.caption("Risk: " + result["risk_level"] + ". Review the applicant profile before making a real decision.")

                    render_probability_chart(result["approval_probability"], "Loan approval probability")

                    st.info("Why this result: the submitted credit score, loan-to-income relationship, term, or available assets look less like the loan applications the model learned to approve. Review the input values and the applicant's full credit file before any real decision.")

                    record_decision("loan_credit", "LIKELY REJECTED", f"probability={result['approval_probability']}; cibil={cibil}; amount={amount}; income={income}")

            except Exception as error:

                st.error("The trained loan model is unavailable. Run the training command shown in the setup instructions.")

                st.caption(str(error))



    elif lab == "Transaction decision":

        st.subheader("Transaction pre-check")

        a, b, c = st.columns(3)

        with a: transaction_type = st.selectbox("Transaction type", ["PAYMENT", "TRANSFER", "CASH_OUT", "CASH_IN", "DEBIT"]); amount = st.number_input("Amount (INR)", 1.0, value=10000.0, step=500.0)

        with b: available_balance = st.number_input("Available account balance (INR)", 0.0, value=50000.0, step=500.0); receiver_balance = st.number_input("Receiver opening balance (INR)", 0.0, value=0.0, step=500.0)

        with c: kyc = st.selectbox("KYC status", ["Verified", "Pending", "Rejected"]); flagged = st.checkbox("Known fraud flag / suspicious beneficiary")

        account_status = st.selectbox("Account status", ["Active", "Dormant", "Frozen", "Closed"])

        if st.button("Check transaction", type="primary"):

            reasons = []

            if account_status != "Active": reasons.append(f"account is {account_status.lower()}")

            if amount > available_balance: reasons.append("insufficient balance")

            if kyc != "Verified": reasons.append("KYC is not verified")

            if flagged: reasons.append("fraud/suspicious-beneficiary flag")

            model_error = None
            try:

                from backend.ml.decision_predict import transaction_fraud_probability

                fraud_probability = transaction_fraud_probability({"type":transaction_type,"amount":amount,"oldbalanceOrg":available_balance,"newbalanceOrig":max(available_balance-amount,0),"oldbalanceDest":receiver_balance,"newbalanceDest":receiver_balance+amount})

            except Exception as error:

                fraud_probability = None
                model_error = error

            if model_error is not None:
                notify_operations_error("Transaction decision model", model_error)
                st.error("The trained transaction fraud model could not run. The operational rules below still apply, but the model result is unavailable.")
                st.caption(f"Model error: {model_error}")

            if fraud_probability is not None:

                st.metric("Trained fraud-model probability", f"{fraud_probability}%")

                render_probability_chart(fraud_probability, "Transaction fraud probability")

                st.caption("The fraud model uses transaction type, amount, and sender/receiver balance movements. Account and KYC rules are applied separately because they are operational requirements, not model features.")

            if fraud_probability is not None and fraud_probability >= 50: reasons.append("trained fraud model indicates high risk")

            if reasons: outcome="BLOCKED / REVIEW"; st.error("TRANSACTION BLOCKED / NEEDS REVIEW: " + "; ".join(reasons))

            elif amount >= 100000: outcome="PENDING REVIEW"; st.warning("TRANSACTION PENDING REVIEW: high-value transaction; complete additional verification.")

            else: outcome="LIKELY SUCCESSFUL"; st.success(f"TRANSACTION LIKELY SUCCESSFUL: {transaction_type} for {money(amount)} passed the pre-check.")

            record_decision("transaction", outcome, f"type={transaction_type}; amount={amount}; fraud_probability={fraud_probability}")



    elif lab == "Fraud risk screening":

        st.subheader("Fraud screening")

        a, b, c = st.columns(3)

        with a: amount = st.number_input("Transaction amount (INR)", 1.0, value=10000.0, step=500.0); new_beneficiary = st.checkbox("New beneficiary")

        with b: failed_attempts = st.number_input("Failed attempts in last hour", 0, 20, 0); unusual_location = st.checkbox("Unusual location or device")

        with c: account_age = st.number_input("Account age (days)", 0, value=365); flagged = st.checkbox("Known watch-list match")

        if st.button("Screen fraud risk", type="primary"):

            score = (35 if flagged else 0) + (25 if unusual_location else 0) + (15 if new_beneficiary else 0) + min(failed_attempts * 8, 25) + (15 if account_age < 30 else 0) + (15 if amount >= 100000 else 0)

            if score >= 50:
                outcome = "HIGH FRAUD RISK"
                st.error(f"HIGH FRAUD RISK ({min(score,100)}/100): block and escalate for manual investigation.")

            elif score >= 25:
                outcome = "MEDIUM FRAUD RISK"
                st.warning(f"MEDIUM FRAUD RISK ({score}/100): request step-up verification before processing.")

            else:
                outcome = "LOW FRAUD RISK"
                st.success(f"LOW FRAUD RISK ({score}/100): no rule-based fraud blocker found.")

            record_decision("fraud_screen", outcome, f"score={score}; amount={amount}; new_beneficiary={new_beneficiary}; failed_attempts={failed_attempts}; unusual_device={unusual_location}; account_age_days={account_age}; watch_list={flagged}")



    elif lab == "Account withdrawal check":

        balance = st.number_input("Current balance (INR)", 0.0, value=25000.0, step=500.0)

        withdrawal = st.number_input("Withdrawal amount (INR)", 1.0, value=5000.0, step=500.0)

        minimum = st.number_input("Required minimum balance (INR)", 0.0, value=1000.0, step=500.0)

        status = st.selectbox("Account status", ["Active", "Dormant", "Frozen", "Closed"])

        if st.button("Check withdrawal", type="primary"):

            remaining = balance - withdrawal

            if status != "Active":
                outcome = "WITHDRAWAL DECLINED"
                st.error(f"WITHDRAWAL DECLINED: account is {status.lower()}.")

            elif remaining < minimum:
                outcome = "WITHDRAWAL DECLINED"
                st.error(f"WITHDRAWAL DECLINED: remaining balance ({money(remaining)}) would be below the required minimum.")

            else:
                outcome = "WITHDRAWAL LIKELY SUCCESSFUL"
                st.success(f"WITHDRAWAL LIKELY SUCCESSFUL: remaining balance would be {money(remaining)}.")

            record_decision("account_withdrawal", outcome, f"balance={balance}; withdrawal={withdrawal}; minimum={minimum}; status={status}; remaining={remaining}")



    elif lab == "Account anomaly check":

        account_type = st.selectbox("Account type", ["Savings", "Current", "Salary", "Fixed Deposit"]); branch_id = st.number_input("Branch ID", 1, value=1); balance = st.number_input("Account balance (INR)", 0.0, value=50000.0); age_days = st.number_input("Account age (days)", 0, value=365)

        if st.button("Check account pattern", type="primary"):
            try:
                from backend.ml.decision_predict import account_anomaly

                anomalous = account_anomaly({"account_type":account_type,"branch_id":branch_id,"balance":balance,"account_age_days":age_days})

                outcome = "ANOMALY - REVIEW" if anomalous else "NORMAL PATTERN"; (st.warning if anomalous else st.success)("Account pattern needs review." if anomalous else "Account pattern is within the trained normal range.")

                st.caption("The anomaly model compares account type, branch, balance, and age against normal patterns learned from the account CSV."); record_decision("account_anomaly", outcome, f"type={account_type}; branch={branch_id}; balance={balance}; age_days={age_days}")
            except Exception as error:
                notify_operations_error("Account anomaly model", error)
                recipient = recipient_email or st.session_state.get("decision_result_email", "").strip()
                if recipient:
                    email_sent, email_error = send_result_email(recipient, "Account anomaly check", "TECHNICAL ERROR")
                    if email_sent:
                        st.info(f"Amazon SES accepted the technical error email for {recipient}. Message ID: {email_error or 'not returned'}.")
                    else:
                        st.warning(f"Technical error email was not sent ({email_error}).")
                st.error("The trained account anomaly model could not run. No anomaly result was produced.")
                st.caption(f"Model error: {error}")



    elif lab == "Branch profit prediction":

        branch_id = st.number_input("Branch ID", 1, value=1); month = st.selectbox("Month", ["January","February","March","April","May","June","July","August","September","October","November","December"]); year = st.number_input("Year", 2020, 2035, 2026); loans = st.number_input("Loans disbursed", 0, value=1000); customers = st.number_input("New customers", 0, value=400); fraud_cases = st.number_input("Fraud cases", 0, value=10); satisfaction = st.number_input("Customer satisfaction", 0.0, 5.0, 4.5, 0.01)

        if st.button("Predict branch profit", type="primary"):

            from backend.ml.decision_predict import branch_profit_prediction

            base = {"branch_id":branch_id,"month":month,"year":year,"loan_disbursed":loans,"new_customers":customers,"fraud_cases":fraud_cases,"customer_satisfaction":satisfaction}

            predicted = branch_profit_prediction(base.copy()); st.metric("Estimated branch profit", money(predicted)); st.caption("This estimate is based on historical branch patterns: month, lending activity, new customers, fraud cases, and satisfaction. It is not a guaranteed financial result.")

            scenarios = pd.DataFrame({"Fraud cases": list(range(0, max(31, fraud_cases + 1), 5))}); scenarios["Estimated profit"] = [branch_profit_prediction({**base, "fraud_cases": value}) for value in scenarios["Fraud cases"]]

            st.plotly_chart(px.line(scenarios, x="Fraud cases", y="Estimated profit", markers=True, title="Profit sensitivity to fraud cases"), use_container_width=True); record_decision("branch_profit", "PREDICTED", f"branch={branch_id}; month={month}; profit={predicted}")



    elif lab == "Saved decision history":

        from services.decision_store import load_history

        history, storage_source = load_history()
        if not history.empty:
            st.caption(f"History source: {storage_source}")
            render_saved_history_charts(history.copy()); st.dataframe(history.sort_values("timestamp_utc", ascending=False), use_container_width=True, hide_index=True); st.download_button("Download decision history", history.to_csv(index=False).encode("utf-8"), "manual_decision_history.csv", "text/csv")
        else: st.info("No manual decisions have been saved yet.")



    else:

        priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])

        issue_type = st.text_input("Issue type", "Card payment failed")

        if st.button("Classify ticket", type="primary"):

            if priority == "Critical":
                outcome = "IMMEDIATE ESCALATION"
                st.error("IMMEDIATE ESCALATION: assign to the incident-response team now.")

            elif priority == "High":
                outcome = "PRIORITY REVIEW"
                st.warning("PRIORITY REVIEW: assign to support within the high-priority SLA.")

            else:
                outcome = "STANDARD QUEUE"
                st.success(f"STANDARD QUEUE: '{issue_type}' can enter the normal support workflow.")

            record_decision("support_ticket", outcome, f"priority={priority}; issue_type={issue_type}")



@alert_failures("Loan Approval AI dashboard")
def render_loan_approval_ai():
    """Generate an experimental prediction for a newly entered loan application."""
    st.title("Loan Approval AI")
    st.caption("Enter a new applicant profile. This is an experimental model prediction, not a bank decision.")

    with st.form("loan_approval_ai_form"):
        left, middle, right = st.columns(3)
        with left:
            dependents = st.number_input("Number of dependents", min_value=0, max_value=20, value=2, step=1)
            education = st.selectbox("Education", ["Graduate", "Not Graduate"])
            self_employed = st.selectbox("Self-employed", ["No", "Yes"])
            cibil = st.number_input("CIBIL score", min_value=300, max_value=900, value=735, step=1)
        with middle:
            income = st.number_input("Annual income (INR)", min_value=1, value=750000, step=10000)
            amount = st.number_input("Loan amount (INR)", min_value=1, value=1500000, step=10000)
            term = st.number_input("Loan term (years)", min_value=1, max_value=30, value=15, step=1)
        with right:
            residential = st.number_input("Residential assets (INR)", min_value=0, value=500000, step=10000)
            commercial = st.number_input("Commercial assets (INR)", min_value=0, value=0, step=10000)
            luxury = st.number_input("Luxury assets (INR)", min_value=0, value=200000, step=10000)
            bank_assets = st.number_input("Bank assets (INR)", min_value=0, value=100000, step=10000)

        applicant_email = st.text_input("Applicant email (optional; a result email is sent automatically if entered)")

        submitted = st.form_submit_button("Predict Loan Approval", type="primary", use_container_width=True)

    if not submitted:
        st.info("Enter the applicant details and click Predict Loan Approval.")
        return

    applicant = {
        "no_of_dependents": dependents,
        "education": education,
        "self_employed": self_employed,
        "income_annum": income,
        "loan_amount": amount,
        "loan_term": term,
        "cibil_score": cibil,
        "residential_assets_value": residential,
        "commercial_assets_value": commercial,
        "luxury_assets_value": luxury,
        "bank_asset_value": bank_assets,
    }

    try:
        result = predict_loan_approval(applicant)
    except Exception as error:
        notify_operations_error("Loan approval prediction", error)
        st.error("The trained loan model could not generate a prediction.")
        st.caption(str(error))
        error_recipient = applicant_email.strip() or st.session_state.get("decision_result_email", "").strip()
        if error_recipient:
            try:
                from services.loan_notifications import send_loan_notification
                delivery = send_loan_notification(error_recipient, "technical_failure", type(error).__name__)
                render_loan_notification_status(delivery)
            except Exception as notification_error:
                st.warning(f"Email notification could not be sent ({type(notification_error).__name__}).")
        return

    if not result.get("valid"):
        st.error("Please correct the submitted values.")
        for field, message in result.get("errors", {}).items():
            st.write(f"**{field}:** {message}")
        return

    st.subheader("Prediction result")
    first, second, third = st.columns(3)
    if result["decision"] == "APPROVED":
        first.success(f"Model output: {result['decision']}")
    else:
        first.error(f"Model output: {result['decision']}")
    second.metric("Estimated approval probability", f"{result['approval_probability']:.1f}%")
    third.metric("Model risk category", result["risk_level"])
    render_probability_chart(result["approval_probability"], "Estimated loan approval probability")

    st.subheader("Key factors")
    for factor in result.get("key_factors", []):
        st.markdown(f"- {factor}")
    st.caption(f"Model used: {result.get('model_used', 'Unknown')}")
    st.warning(result.get("disclaimer", "Experimental prediction only; this is not a lending decision."))

    outcome = "LIKELY APPROVED" if result["decision"] == "APPROVED" else "LIKELY REJECTED"
    details = f"probability={result['approval_probability']}; cibil={cibil}; amount={amount}; income={income}"
    save_decision("loan_credit_ai", outcome, details, applicant_email.strip() or None)


st.sidebar.title("FinIntel AI"); st.sidebar.caption("CSV-first banking intelligence")

workspace = st.sidebar.radio("Workspace", ["Executive overview", "Detection centre", "Dataset explorer", "CSV Curve Gallery", "Manual calculations & decisions"])
if workspace == "Manual calculations & decisions":
    page = st.sidebar.selectbox("Choose a calculator or decision page", MANUAL_DECISION_MENU)
else:
    page = workspace

key=st.sidebar.selectbox("Select CSV dataset",list(DATASETS),format_func=lambda item:DATASETS[item][1])

st.sidebar.caption("Large CSVs are sampled automatically so the interface stays responsive.")

st.sidebar.subheader("Result emails for all modules")
st.sidebar.caption("Default recipient for Loan Approval AI and decision pages. You can override it on a decision page.")
st.sidebar.text_input("Recipient email", key="decision_result_email", placeholder="you@example.com")
st.sidebar.caption("If entered, SES emails each decision status automatically after you submit it. Configure a verified SES sender first.")

if page=="Manual Decision Lab":

    render_manual_decision_lab()

elif page=="Executive overview":

    st.title("FinIntel AI - Detection Workspace"); st.write("Every CSV has a separate business view and a relevant detection section, rather than one generic dashboard.")

    cards=[]

    for item,values in DATASETS.items():

        _,size,_=load_csv(values[0])

        if size: cards.append({"Dataset":values[1],"CSV file":values[0],"Detection section":values[3],"Size (MB)":round(size/1024/1024,2)})

    st.dataframe(pd.DataFrame(cards),use_container_width=True,hide_index=True); st.info("Choose a dataset in the sidebar, then use Detection centre for dedicated checks or Dataset explorer for raw inspection.")

elif page=="CSV Curve Gallery":

    render_csv_curve_gallery()

elif page=="Loan Approval AI":

    render_loan_approval_ai()

elif page in DECISION_PAGES:

    render_manual_decision_lab(selected_case=page)

else:

    file_name,label,description,focus=DATASETS[key]; frame,_,sampled=load_csv(file_name)

    st.title(label); st.caption(description)

    if sampled: st.warning(f"This is a large file: charts use the first {len(frame):,} rows as a responsive sample.")

    if frame.empty: st.error("This CSV could not be loaded. Check datasets/raw.")

    elif page=="Detection centre":

        overview,quality,detection=st.tabs(["Overview","Data quality","Detection"])

        with overview:

            a,b,c,d=st.columns(4); a.metric("Rows loaded",f"{len(frame):,}"); b.metric("Columns",len(frame.columns)); c.metric("Missing values",f"{frame.isna().sum().sum():,}"); d.metric("Duplicate rows",f"{frame.duplicated().sum():,}")

            st.markdown(f"<div class='section-card'><b>Detection focus:</b> {focus}<br>Use <b>Data quality</b> for universal CSV checks and <b>Detection</b> for the source-specific review.</div>",unsafe_allow_html=True); render_trend_chart(key,frame); st.dataframe(frame.head(25),use_container_width=True,hide_index=True)

        with quality: render_quality(frame)

        with detection:
            render_detection(key, frame)
            render_additional_charts(key, frame)

    else:

        selected=st.multiselect("Columns to display",frame.columns.tolist(),default=frame.columns.tolist()[:8]); limit=st.slider("Rows to show",25,min(1000,max(25,len(frame))),min(100,len(frame)))

        if selected:

            st.dataframe(frame[selected].head(limit),use_container_width=True,hide_index=True); st.download_button("Download loaded data as CSV",frame[selected].to_csv(index=False).encode("utf-8"),"filtered_data.csv","text/csv")
