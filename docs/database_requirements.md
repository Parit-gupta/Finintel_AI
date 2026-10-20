# Database Requirements Document — Banking Platform

## 📋 Document Purpose

This document defines the **functional and structural requirements** for each entity (table) in the Banking Platform database. It specifies the required fields, data types, constraints, and business rules needed before implementing the PostgreSQL schema.

---

## 🗂️ Table of Contents

1. [Customers](#1-customers)
2. [Accounts](#2-accounts)
3. [Branches](#3-branches)
4. [Employees](#4-employees)
5. [Transactions](#5-transactions)
6. [Loan Applications](#6-loan-applications)
7. [Credit History](#7-credit-history)
8. [Support Tickets](#8-support-tickets)
9. [Marketing Campaigns](#9-marketing-campaigns)
10. [Prediction History](#10-prediction-history)
11. [User Roles](#11-user-roles)
12. [Branch Performance](#12-branch-performance)
13. [Banking Products](#13-banking-products)

---

## 1. Customers

**Purpose:** Stores personal, contact, and identity information for all bank customers.

| Field            | Data Type     | Constraints               | Description                             |
| ---------------- | ------------- | ------------------------- | --------------------------------------- |
| `customer_id`    | SERIAL / UUID | PK                        | Unique customer identifier              |
| `branch_id`      | INTEGER       | FK → `branches.branch_id` | Home branch of the customer             |
| `first_name`     | VARCHAR(50)   | NOT NULL                  | Customer's first name                   |
| `last_name`      | VARCHAR(50)   | NOT NULL                  | Customer's last name                    |
| `date_of_birth`  | DATE          | NOT NULL                  | Used for age/KYC verification           |
| `gender`         | VARCHAR(10)   | —                         | Optional demographic field              |
| `email`          | VARCHAR(100)  | UNIQUE, NOT NULL          | Primary contact email                   |
| `phone_number`   | VARCHAR(20)   | UNIQUE, NOT NULL          | Primary contact number                  |
| `address`        | TEXT          | —                         | Residential address                     |
| `city`           | VARCHAR(50)   | —                         | City of residence                       |
| `state`          | VARCHAR(50)   | —                         | State/province                          |
| `country`        | VARCHAR(50)   | —                         | Country of residence                    |
| `postal_code`    | VARCHAR(20)   | —                         | ZIP/postal code                         |
| `national_id`    | VARCHAR(50)   | UNIQUE, NOT NULL          | Government-issued ID (SSN/Aadhaar/etc.) |
| `kyc_status`     | VARCHAR(20)   | DEFAULT 'Pending'         | Verified / Pending / Rejected           |
| `customer_since` | DATE          | DEFAULT CURRENT_DATE      | Onboarding date                         |
| `status`         | VARCHAR(20)   | DEFAULT 'Active'          | Active / Inactive / Blocked             |
| `created_at`     | TIMESTAMP     | DEFAULT NOW()             | Record creation timestamp               |
| `updated_at`     | TIMESTAMP     | DEFAULT NOW()             | Last update timestamp                   |

**Business Rules:**

- A customer must belong to exactly one branch.
- `national_id`, `email`, and `phone_number` must be unique across the system.
- KYC status must be `Verified` before a customer can open an account or apply for a loan.

---

## 2. Accounts

**Purpose:** Stores customer bank account details (savings, current, etc.).

| Field            | Data Type     | Constraints                        | Description                             |
| ---------------- | ------------- | ---------------------------------- | --------------------------------------- |
| `account_id`     | SERIAL / UUID | PK                                 | Unique account identifier               |
| `customer_id`    | INTEGER       | FK → `customers.customer_id`       | Account owner                           |
| `branch_id`      | INTEGER       | FK → `branches.branch_id`          | Branch where account was opened         |
| `product_id`     | INTEGER       | FK → `banking_products.product_id` | Linked banking product                  |
| `account_number` | VARCHAR(20)   | UNIQUE, NOT NULL                   | Bank-facing account number              |
| `account_type`   | VARCHAR(30)   | NOT NULL                           | Savings / Current / Fixed Deposit       |
| `currency`       | VARCHAR(10)   | DEFAULT 'INR'                      | Account currency                        |
| `balance`        | DECIMAL(15,2) | DEFAULT 0.00, NOT NULL             | Current account balance                 |
| `interest_rate`  | DECIMAL(5,2)  | —                                  | Applicable interest rate (if any)       |
| `account_status` | VARCHAR(20)   | DEFAULT 'Active'                   | Active / Dormant / Closed / Frozen      |
| `opened_date`    | DATE          | DEFAULT CURRENT_DATE               | Date account was opened                 |
| `closed_date`    | DATE          | —                                  | Date account was closed (if applicable) |
| `created_at`     | TIMESTAMP     | DEFAULT NOW()                      | Record creation timestamp               |
| `updated_at`     | TIMESTAMP     | DEFAULT NOW()                      | Last update timestamp                   |

**Business Rules:**

- Balance cannot go negative unless account type is `Overdraft`.
- A closed account cannot process new transactions.
- Each account must be tied to exactly one customer and one branch.

---

## 3. Branches

**Purpose:** Stores all bank branch information.

| Field          | Data Type     | Constraints                  | Description                          |
| -------------- | ------------- | ---------------------------- | ------------------------------------ |
| `branch_id`    | SERIAL / UUID | PK                           | Unique branch identifier             |
| `branch_name`  | VARCHAR(100)  | NOT NULL                     | Name of the branch                   |
| `branch_code`  | VARCHAR(20)   | UNIQUE, NOT NULL             | Unique bank branch code (e.g., IFSC) |
| `address`      | TEXT          | NOT NULL                     | Physical branch address              |
| `city`         | VARCHAR(50)   | NOT NULL                     | City                                 |
| `state`        | VARCHAR(50)   | —                            | State/province                       |
| `country`      | VARCHAR(50)   | NOT NULL                     | Country                              |
| `postal_code`  | VARCHAR(20)   | —                            | ZIP/postal code                      |
| `phone_number` | VARCHAR(20)   | —                            | Branch contact number                |
| `manager_id`   | INTEGER       | FK → `employees.employee_id` | Current branch manager               |
| `opening_date` | DATE          | —                            | Date branch was established          |
| `status`       | VARCHAR(20)   | DEFAULT 'Active'             | Active / Closed                      |
| `created_at`   | TIMESTAMP     | DEFAULT NOW()                | Record creation timestamp            |

**Business Rules:**

- `branch_code` must be unique nationally.
- `manager_id` should reference an employee assigned to the same branch.

---

## 4. Employees

**Purpose:** Stores employee details for staff working at each branch.

| Field               | Data Type     | Constraints               | Description                                |
| ------------------- | ------------- | ------------------------- | ------------------------------------------ |
| `employee_id`       | SERIAL / UUID | PK                        | Unique employee identifier                 |
| `branch_id`         | INTEGER       | FK → `branches.branch_id` | Assigned branch                            |
| `first_name`        | VARCHAR(50)   | NOT NULL                  | Employee's first name                      |
| `last_name`         | VARCHAR(50)   | NOT NULL                  | Employee's last name                       |
| `email`             | VARCHAR(100)  | UNIQUE, NOT NULL          | Work email                                 |
| `phone_number`      | VARCHAR(20)   | UNIQUE                    | Contact number                             |
| `designation`       | VARCHAR(50)   | NOT NULL                  | Job title (Manager, Officer, Teller, etc.) |
| `department`        | VARCHAR(50)   | —                         | Department/team                            |
| `date_of_joining`   | DATE          | NOT NULL                  | Employment start date                      |
| `salary`            | DECIMAL(12,2) | —                         | Monthly/annual salary                      |
| `employment_status` | VARCHAR(20)   | DEFAULT 'Active'          | Active / On Leave / Terminated             |
| `created_at`        | TIMESTAMP     | DEFAULT NOW()             | Record creation timestamp                  |

**Business Rules:**

- Each employee must belong to one branch.
- Only employees with designation `Manager` can be referenced by `branches.manager_id`.

---

## 5. Transactions

**Purpose:** Stores all banking transaction records (deposits, withdrawals, transfers, payments).

| Field                  | Data Type     | Constraints                           | Description                               |
| ---------------------- | ------------- | ------------------------------------- | ----------------------------------------- |
| `transaction_id`       | SERIAL / UUID | PK                                    | Unique transaction identifier             |
| `account_id`           | INTEGER       | FK → `accounts.account_id`            | Account involved in the transaction       |
| `transaction_type`     | VARCHAR(30)   | NOT NULL                              | Deposit / Withdrawal / Transfer / Payment |
| `amount`               | DECIMAL(15,2) | NOT NULL, CHECK (amount > 0)          | Transaction amount                        |
| `currency`             | VARCHAR(10)   | DEFAULT 'INR'                         | Currency of transaction                   |
| `balance_after`        | DECIMAL(15,2) | —                                     | Account balance after transaction         |
| `reference_account_id` | INTEGER       | FK → `accounts.account_id` (nullable) | Counterparty account (for transfers)      |
| `channel`              | VARCHAR(30)   | —                                     | ATM / Online / Mobile App / Branch        |
| `transaction_status`   | VARCHAR(20)   | DEFAULT 'Success'                     | Success / Failed / Pending / Reversed     |
| `description`          | TEXT          | —                                     | Transaction remarks/notes                 |
| `transaction_date`     | TIMESTAMP     | DEFAULT NOW()                         | Date and time of transaction              |

**Business Rules:**

- Transactions must always be linked to a valid, active account.
- Withdrawal transactions cannot exceed available balance (unless overdraft enabled).
- Failed transactions should not alter account balance.

---

## 6. Loan Applications

**Purpose:** Stores all customer loan requests and their approval lifecycle.

| Field                | Data Type     | Constraints                        | Description                              |
| -------------------- | ------------- | ---------------------------------- | ---------------------------------------- |
| `loan_id`            | SERIAL / UUID | PK                                 | Unique loan application identifier       |
| `customer_id`        | INTEGER       | FK → `customers.customer_id`       | Applicant                                |
| `product_id`         | INTEGER       | FK → `banking_products.product_id` | Loan product (Home Loan, Car Loan, etc.) |
| `loan_amount`        | DECIMAL(15,2) | NOT NULL                           | Requested loan amount                    |
| `interest_rate`      | DECIMAL(5,2)  | —                                  | Applicable interest rate                 |
| `tenure_months`      | INTEGER       | NOT NULL                           | Loan repayment period in months          |
| `purpose`            | VARCHAR(100)  | —                                  | Purpose of the loan                      |
| `application_date`   | DATE          | DEFAULT CURRENT_DATE               | Date of application                      |
| `approval_status`    | VARCHAR(20)   | DEFAULT 'Pending'                  | Pending / Approved / Rejected / Closed   |
| `approved_by`        | INTEGER       | FK → `employees.employee_id`       | Loan officer who approved/rejected       |
| `approval_date`      | DATE          | —                                  | Date of decision                         |
| `emi_amount`         | DECIMAL(12,2) | —                                  | Calculated monthly installment           |
| `outstanding_amount` | DECIMAL(15,2) | —                                  | Remaining loan balance                   |
| `created_at`         | TIMESTAMP     | DEFAULT NOW()                      | Record creation timestamp                |

**Business Rules:**

- A customer must have `Verified` KYC status to apply for a loan.
- Loan approval requires sign-off from an employee with role `Loan Officer` or `Branch Manager`.
- `outstanding_amount` should be updated as EMIs are paid via transactions.

---

## 7. Credit History

**Purpose:** Stores customer credit records used for risk assessment and loan decisioning.

| Field                    | Data Type     | Constraints                              | Description                             |
| ------------------------ | ------------- | ---------------------------------------- | --------------------------------------- |
| `credit_history_id`      | SERIAL / UUID | PK                                       | Unique credit record identifier         |
| `customer_id`            | INTEGER       | FK → `customers.customer_id`             | Customer the record belongs to          |
| `credit_score`           | INTEGER       | CHECK (credit_score BETWEEN 300 AND 900) | Credit score (e.g., CIBIL-style score)  |
| `credit_bureau`          | VARCHAR(50)   | —                                        | Source of credit score (e.g., Experian) |
| `total_outstanding_debt` | DECIMAL(15,2) | —                                        | Total debt across institutions          |
| `total_credit_limit`     | DECIMAL(15,2) | —                                        | Combined credit limit                   |
| `active_loans_count`     | INTEGER       | DEFAULT 0                                | Number of active loans                  |
| `missed_payments_count`  | INTEGER       | DEFAULT 0                                | Count of missed/late payments           |
| `defaults_count`         | INTEGER       | DEFAULT 0                                | Number of past defaults                 |
| `report_date`            | DATE          | DEFAULT CURRENT_DATE                     | Date credit report was generated        |
| `created_at`             | TIMESTAMP     | DEFAULT NOW()                            | Record creation timestamp               |

**Business Rules:**

- Credit score directly influences loan approval and interest rate.
- Records should be refreshed periodically (e.g., quarterly) for active customers.

---

## 8. Support Tickets

**Purpose:** Stores customer complaints, queries, and service requests.

| Field              | Data Type     | Constraints                  | Description                                 |
| ------------------ | ------------- | ---------------------------- | ------------------------------------------- |
| `ticket_id`        | SERIAL / UUID | PK                           | Unique ticket identifier                    |
| `customer_id`      | INTEGER       | FK → `customers.customer_id` | Customer who raised the ticket              |
| `assigned_to`      | INTEGER       | FK → `employees.employee_id` | Support agent handling the ticket           |
| `category`         | VARCHAR(50)   | —                            | Complaint / Query / Fraud Report / Feedback |
| `subject`          | VARCHAR(150)  | NOT NULL                     | Short ticket summary                        |
| `description`      | TEXT          | NOT NULL                     | Full details of the issue                   |
| `priority`         | VARCHAR(20)   | DEFAULT 'Medium'             | Low / Medium / High / Critical              |
| `status`           | VARCHAR(20)   | DEFAULT 'Open'               | Open / In Progress / Resolved / Closed      |
| `created_at`       | TIMESTAMP     | DEFAULT NOW()                | Ticket creation timestamp                   |
| `resolved_at`      | TIMESTAMP     | —                            | Ticket resolution timestamp                 |
| `resolution_notes` | TEXT          | —                            | Notes on how the issue was resolved         |

**Business Rules:**

- Tickets tagged `Critical` (e.g., fraud reports) should trigger immediate escalation.
- `resolved_at` must be set when status changes to `Resolved` or `Closed`.

---

## 9. Marketing Campaigns

**Purpose:** Stores promotional campaigns and tracks customer responses.

| Field             | Data Type     | Constraints                        | Description                                     |
| ----------------- | ------------- | ---------------------------------- | ----------------------------------------------- |
| `campaign_id`     | SERIAL / UUID | PK                                 | Unique campaign identifier                      |
| `customer_id`     | INTEGER       | FK → `customers.customer_id`       | Targeted customer                               |
| `campaign_name`   | VARCHAR(100)  | NOT NULL                           | Name of the campaign                            |
| `campaign_type`   | VARCHAR(50)   | —                                  | Email / SMS / Push Notification / Call          |
| `product_id`      | INTEGER       | FK → `banking_products.product_id` | Product being promoted                          |
| `start_date`      | DATE          | NOT NULL                           | Campaign start date                             |
| `end_date`        | DATE          | —                                  | Campaign end date                               |
| `channel`         | VARCHAR(30)   | —                                  | Distribution channel                            |
| `response_status` | VARCHAR(20)   | DEFAULT 'No Response'              | Interested / Converted / Declined / No Response |
| `conversion_date` | DATE          | —                                  | Date customer converted (if applicable)         |
| `created_at`      | TIMESTAMP     | DEFAULT NOW()                      | Record creation timestamp                       |

**Business Rules:**

- A campaign can target many customers; each row represents one customer-campaign interaction.
- `response_status` should be updated based on customer engagement tracking.

---

## 10. Prediction History

**Purpose:** Stores outputs of AI/ML model predictions (e.g., churn risk, fraud risk, loan default risk).

| Field               | Data Type     | Constraints                              | Description                                     |
| ------------------- | ------------- | ---------------------------------------- | ----------------------------------------------- |
| `prediction_id`     | SERIAL / UUID | PK                                       | Unique prediction record identifier             |
| `customer_id`       | INTEGER       | FK → `customers.customer_id`             | Customer the prediction relates to              |
| `model_name`        | VARCHAR(100)  | NOT NULL                                 | Name/version of the ML model used               |
| `prediction_type`   | VARCHAR(50)   | NOT NULL                                 | Churn / Fraud Risk / Credit Risk / Loan Default |
| `prediction_result` | VARCHAR(50)   | NOT NULL                                 | Predicted class/label                           |
| `confidence_score`  | DECIMAL(5,4)  | CHECK (confidence_score BETWEEN 0 AND 1) | Model confidence (0–1)                          |
| `input_features`    | JSONB         | —                                        | Snapshot of input features used                 |
| `prediction_date`   | TIMESTAMP     | DEFAULT NOW()                            | When the prediction was generated               |
| `reviewed_by`       | INTEGER       | FK → `employees.employee_id`             | Analyst who reviewed the prediction             |
| `review_status`     | VARCHAR(20)   | DEFAULT 'Pending'                        | Pending / Confirmed / Dismissed                 |

**Business Rules:**

- High-risk fraud predictions should automatically generate a support ticket for review.
- `input_features` stored as JSONB for flexibility across different model types.

---

## 11. User Roles

**Purpose:** Defines permission sets for application users (Users table references this).

| Field         | Data Type     | Constraints      | Description                                                                             |
| ------------- | ------------- | ---------------- | --------------------------------------------------------------------------------------- |
| `role_id`     | SERIAL / UUID | PK               | Unique role identifier                                                                  |
| `role_name`   | VARCHAR(50)   | UNIQUE, NOT NULL | Admin / Branch Manager / Loan Officer / Fraud Analyst / Customer Support / Data Analyst |
| `description` | TEXT          | —                | Description of role responsibilities                                                    |
| `permissions` | JSONB         | —                | Structured permission set (module-level access)                                         |
| `created_at`  | TIMESTAMP     | DEFAULT NOW()    | Record creation timestamp                                                               |

**Business Rules:**

- Each application user must be assigned exactly one role.
- Role permissions govern access to modules like Loans, Fraud, Reports, Admin Panel, etc.

---

## 12. Branch Performance

**Purpose:** Stores monthly KPI records for each branch.

| Field                         | Data Type     | Constraints               | Description                                       |
| ----------------------------- | ------------- | ------------------------- | ------------------------------------------------- |
| `performance_id`              | SERIAL / UUID | PK                        | Unique performance record identifier              |
| `branch_id`                   | INTEGER       | FK → `branches.branch_id` | Branch being measured                             |
| `report_month`                | DATE          | NOT NULL                  | Month/year of the KPI record (first day of month) |
| `total_customers`             | INTEGER       | DEFAULT 0                 | Total active customers at branch                  |
| `new_accounts_opened`         | INTEGER       | DEFAULT 0                 | New accounts opened in the period                 |
| `total_deposits`              | DECIMAL(18,2) | DEFAULT 0.00              | Total deposit value                               |
| `total_withdrawals`           | DECIMAL(18,2) | DEFAULT 0.00              | Total withdrawal value                            |
| `total_loans_disbursed`       | DECIMAL(18,2) | DEFAULT 0.00              | Total loan amount disbursed                       |
| `loans_approved_count`        | INTEGER       | DEFAULT 0                 | Number of loans approved                          |
| `revenue_generated`           | DECIMAL(18,2) | DEFAULT 0.00              | Net revenue for the period                        |
| `customer_satisfaction_score` | DECIMAL(4,2)  | —                         | Average CSAT score                                |
| `created_at`                  | TIMESTAMP     | DEFAULT NOW()             | Record creation timestamp                         |

**Business Rules:**

- One record per branch per month (unique constraint on `branch_id` + `report_month`).
- Used for dashboards and executive reporting.

---

## 13. Banking Products

**Purpose:** Stores products offered by the bank.

**Examples:** Savings Account, Home Loan, Car Loan, Credit Card

| Field                  | Data Type     | Constraints      | Description                            |
| ---------------------- | ------------- | ---------------- | -------------------------------------- |
| `product_id`           | SERIAL / UUID | PK               | Unique product identifier              |
| `product_name`         | VARCHAR(100)  | NOT NULL         | Name of the product                    |
| `product_category`     | VARCHAR(50)   | NOT NULL         | Deposit / Loan / Card / Investment     |
| `description`          | TEXT          | —                | Product details                        |
| `interest_rate`        | DECIMAL(5,2)  | —                | Applicable interest rate (if relevant) |
| `min_amount`           | DECIMAL(15,2) | —                | Minimum eligible amount                |
| `max_amount`           | DECIMAL(15,2) | —                | Maximum eligible amount                |
| `tenure_months`        | INTEGER       | —                | Applicable tenure (for loans/FDs)      |
| `eligibility_criteria` | TEXT          | —                | Criteria customers must meet           |
| `status`               | VARCHAR(20)   | DEFAULT 'Active' | Active / Discontinued                  |
| `launched_date`        | DATE          | —                | Date product was launched              |
| `created_at`           | TIMESTAMP     | DEFAULT NOW()    | Record creation timestamp              |

**Business Rules:**

- Discontinued products cannot be assigned to new accounts or loan applications.

---

## ✅ General Data Standards

- All primary keys use `SERIAL` (auto-incrementing) or `UUID` for global uniqueness.
- All monetary fields use `DECIMAL` to avoid floating-point rounding errors.
- All tables include `created_at` (and `updated_at` where applicable) for auditability.
- Status/enum-like fields (e.g., `status`, `approval_status`) should ideally be implemented as PostgreSQL `ENUM` types or constrained via `CHECK` constraints for data integrity.
- Foreign key constraints should define `ON DELETE` behavior explicitly (e.g., `RESTRICT` for financial records, `CASCADE` only where safe).

---

## 🚀 Next Steps

1. Convert each table specification into PostgreSQL `CREATE TABLE` DDL statements.
2. Define `ENUM` types for repeated status/category fields.
3. Add indexes on foreign keys and frequently filtered columns (`status`, `report_date`, `transaction_date`).
4. Implement audit triggers for `updated_at` columns.
5. Seed reference tables (`user_roles`, `banking_products`) with initial data.
