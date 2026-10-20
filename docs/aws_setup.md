# FinIntel AI AWS setup sequence

Do the account and identity setup before launching the application host. Keep the bucket private and use the `us-east-1` region consistently.

## 1. Secure AWS credentials

The earlier project handover says an access key was exposed. Deactivate/delete that key in IAM and issue a replacement only if you need local CLI uploads. Do not place the replacement in Python files or commit it. On EC2, use an instance role with temporary credentials instead of a long-lived key.

## 2. Prepare S3

The existing bucket is `finintel-ai-parit-2026-unique`. Keep Block Public Access enabled and default encryption on. Run the archive helper to upload all model artifacts under `models/` and the 13 CSVs used by app pages under `raw/`. The transaction and card-fraud files are large and will take time to upload. Don't upload the duplicate `*- Copy.csv` files.

## 3. Create the SNS operations topic

In SNS, create a **Standard** topic named `finintel-loan-operations`. Add your operations/support email as an Email subscription, then confirm the subscription from the AWS email. SNS sends technical error alerts to these fixed subscribers.

For decision results, enter a recipient email in the app sidebar (or in the Loan Approval AI form). After you submit a case, SES automatically sends that address its pass, fail, review, result, or technical-error status. Emails omit customer inputs and personal data. SNS is reserved for technical alerts sent to the fixed operations subscribers.

The EC2 role will need `sns:Publish` scoped to this topic ARN. Set `FININTEL_EMAIL_NOTIFICATIONS_ENABLED=true` to turn on SNS operational alerts and the existing opt-in loan email feature.

## 4. Configure SES for typed result email

In SES, verify the sender email address or domain and set it as `FININTEL_SES_FROM_EMAIL`. While SES is in the sandbox, verify every typed test recipient too. Request production access before sending to arbitrary recipients. Email sending also requires `FININTEL_EMAIL_NOTIFICATIONS_ENABLED=true`.

The EC2 role will need `ses:SendEmail` scoped to the verified sender identity. For local tests, grant the same permission to the IAM user or role used by the `finintel` profile. SES sandbox rules are regional, so verify/configure the identity in `us-east-1`.

## 5. Configure the application

Provide these non-secret environment settings on EC2 (for example, in the service environment file with owner-only permissions):

```text
AWS_DEFAULT_REGION=us-east-1
FININTEL_S3_BUCKET=finintel-ai-parit-2026-unique
FININTEL_SES_FROM_EMAIL=verified-sender@example.com
FININTEL_SNS_TOPIC_ARN=arn:aws:sns:us-east-1:ACCOUNT_ID:finintel-loan-operations
FININTEL_EMAIL_NOTIFICATIONS_ENABLED=true
```

Replace the sender and topic ARN with the verified values from your AWS account. Do not put AWS access keys in this file. For local testing, the SDK can use your configured `finintel` profile; on EC2, omit `AWS_PROFILE` and attach the role.

After deploying the code to EC2, pull the private app datasets and model artifacts into the relative paths the Streamlit app already reads:

```bash
aws s3 sync s3://finintel-ai-parit-2026-unique/raw/ datasets/raw/
aws s3 sync s3://finintel-ai-parit-2026-unique/models/ backend/ml/models/
```

## 6. Create the EC2 role

Create an EC2-trusted IAM role and attach it to the instance. Give it only:

- `s3:ListBucket` on this bucket, limited to the required `raw/` and `models/` prefixes.
- `s3:GetObject` on this bucket's `raw/*` and `models/*` objects.
- `sns:Publish` on the operations topic ARN.
- `ses:SendEmail` on the verified sender identity.

If the instance will upload archives, add `s3:PutObject` only for the intended prefixes. AWS recommends least-privilege permissions on EC2 instance roles. Do not attach broad `AdministratorAccess` or `AmazonS3FullAccess`.

## 7. Launch a restricted demo host

Use an Amazon Linux EC2 instance with enough memory for Streamlit, pandas, scikit-learn, and the model artifacts. A `t3.small` (2 GiB) is a starting point for a compact demo; verify memory use before showing the 470 MB transaction dataset. Use a small encrypted gp3 volume sized for the code, Python environment, model artifacts, and datasets. No NAT Gateway, RDS, or load balancer is required for the first demo.

Use Systems Manager Session Manager for administration where possible. In the security group, allow the app port only from the presenter's public IP as a `/32`; do not open SSH or Streamlit to `0.0.0.0/0`. Direct Streamlit HTTP is suitable only for a restricted demonstration with synthetic data. For a public or real-data service, add authenticated HTTPS and appropriate data controls before use.

## 8. Observe and verify

Start the app, enter an SES-verified test recipient, and submit a decision to confirm result delivery. Then verify the app loads every intended dataset and model. Send application stdout/stderr to CloudWatch Logs and use EC2 status checks. Stop or terminate the instance after the demo; a stopped instance still retains and can incur storage charges.

The Streamlit app and optional PostgreSQL integration are not a production banking decision system. Do not use real customer loan data for the demo unless its access, retention, and notification controls have been reviewed.
