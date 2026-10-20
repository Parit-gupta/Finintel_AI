# Run the manual-decision Streamlit app

From `E:\Project_1`, create and activate a virtual environment, then install the packages:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install streamlit pandas plotly joblib scikit-learn matplotlib
```

Train the loan model once (this creates the model used by the Loan / credit decision form):

```powershell
python backend\ml\train_loan_model.py
```

Run the app:

```powershell
streamlit run frontend\app.py
```

The Manual Decision Lab uses rule-based checks for transactions, fraud risk, withdrawals, and ticket priority. The loan decision uses the saved trained model. These are decision-support demonstrations and must be reviewed by an authorized bank employee before a real customer decision.
