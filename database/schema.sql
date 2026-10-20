BEGIN;

-- Table: roles
CREATE TABLE roles (
    role_id       BIGSERIAL PRIMARY KEY,
    role_name     VARCHAR(50) NOT NULL UNIQUE,
    description   TEXT,
    permissions   JSONB,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE roles IS 'System roles for RBAC';

-- Table: branches
CREATE TABLE branches (
    branch_id      BIGSERIAL PRIMARY KEY,
    branch_name    VARCHAR(100) NOT NULL,
    branch_code    VARCHAR(20) NOT NULL UNIQUE,
    address        TEXT NOT NULL,
    city           VARCHAR(50) NOT NULL,
    state          VARCHAR(50),
    country        VARCHAR(50) NOT NULL,
    postal_code    VARCHAR(20),
    phone_number   VARCHAR(20),
    manager_id     BIGINT,               -- FK to employees.employee_id, added after employees table is created
    opening_date   DATE,
    status         VARCHAR(20) NOT NULL DEFAULT 'Active',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE branches IS 'Bank branch master'

-- Table: employees
CREATE TABLE employees (
    employee_id         BIGSERIAL PRIMARY KEY,
    branch_id           BIGINT NOT NULL REFERENCES branches(branch_id) ON DELETE RESTRICT,
    first_name          VARCHAR(50) NOT NULL,
    last_name            VARCHAR(50) NOT NULL,
    email               VARCHAR(100) NOT NULL UNIQUE,
    phone_number        VARCHAR(20) UNIQUE,
    designation         VARCHAR(50) NOT NULL,
    department          VARCHAR(50),
    date_of_joining     DATE NOT NULL,
    salary              DECIMAL(12,2),
    employment_status   VARCHAR(20) NOT NULL DEFAULT 'Active',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE employees IS 'Bank employees / staff. Only employees with designation Manager can be referenced by branches.manager_id';

-- Now that employees exists, attach the branch manager FK
ALTER TABLE branches
    ADD CONSTRAINT fk_branches_manager
    FOREIGN KEY (manager_id) REFERENCES employees(employee_id) ON DELETE SET NULL;

-- Table: users
CREATE TABLE users (
    user_id         BIGSERIAL PRIMARY KEY,
    username        VARCHAR(50) NOT NULL UNIQUE,
    email           VARCHAR(150) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    role_id         BIGINT NOT NULL REFERENCES roles(role_id) ON DELETE RESTRICT,
    branch_id       BIGINT REFERENCES branches(branch_id) ON DELETE SET NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'Active',
    last_login      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE users IS 'Platform login accounts';

-- Table: customers
CREATE TABLE customers (
    customer_id     BIGSERIAL PRIMARY KEY,
    branch_id       BIGINT NOT NULL REFERENCES branches(branch_id) ON DELETE RESTRICT,
    first_name      VARCHAR(50) NOT NULL,
    last_name       VARCHAR(50) NOT NULL,
    date_of_birth   DATE NOT NULL,
    gender          VARCHAR(10),
    email           VARCHAR(100) NOT NULL UNIQUE,
    phone_number    VARCHAR(20) NOT NULL UNIQUE,
    address         TEXT,
    city            VARCHAR(50),
    state           VARCHAR(50),
    country         VARCHAR(50),
    postal_code     VARCHAR(20),
    national_id     VARCHAR(50) NOT NULL UNIQUE,
    kyc_status      VARCHAR(20) NOT NULL DEFAULT 'Pending',
    customer_since  DATE NOT NULL DEFAULT CURRENT_DATE,
    status          VARCHAR(20) NOT NULL DEFAULT 'Active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_customers_kyc_status CHECK (kyc_status IN ('Pending', 'Verified', 'Rejected')),
    CONSTRAINT chk_customers_status CHECK (status IN ('Active', 'Inactive', 'Blocked'))
);

COMMENT ON TABLE customers IS 'Bank customer master. KYC must be Verified before opening accounts or applying for loans';

CREATE INDEX idx_customers_branch_id ON customers(branch_id);

-- Table: banking_products
CREATE TABLE banking_products (
    product_id             BIGSERIAL PRIMARY KEY,
    product_name           VARCHAR(100) NOT NULL,
    product_category       VARCHAR(50) NOT NULL,
    description             TEXT,
    interest_rate           DECIMAL(5,2),
    min_amount              DECIMAL(15,2),
    max_amount               DECIMAL(15,2),
    tenure_months            INT,
    eligibility_criteria     TEXT,
    status                   VARCHAR(20) NOT NULL DEFAULT 'Active',
    launched_date            DATE,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_products_status CHECK (status IN ('Active', 'Discontinued'))
);

COMMENT ON TABLE banking_products IS 'Bank product catalog. Discontinued products cannot be assigned to new accounts or loans';

-- Table: accounts
CREATE TABLE accounts (
    account_id       BIGSERIAL PRIMARY KEY,
    customer_id      BIGINT NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
    branch_id        BIGINT NOT NULL REFERENCES branches(branch_id) ON DELETE RESTRICT,
    product_id       BIGINT NOT NULL REFERENCES banking_products(product_id) ON DELETE RESTRICT,
    account_number   VARCHAR(20) NOT NULL UNIQUE,
    account_type     VARCHAR(30) NOT NULL,
    currency         VARCHAR(10) NOT NULL DEFAULT 'INR',
    balance          DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    interest_rate    DECIMAL(5,2),
    account_status   VARCHAR(20) NOT NULL DEFAULT 'Active',
    opened_date      DATE NOT NULL DEFAULT CURRENT_DATE,
    closed_date      DATE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_accounts_status CHECK (account_status IN ('Active', 'Dormant', 'Closed', 'Frozen'))
);

COMMENT ON TABLE accounts IS 'Customer bank accounts. Closed accounts cannot process new transactions';

CREATE INDEX idx_accounts_customer_id ON accounts(customer_id);
CREATE INDEX idx_accounts_branch_id ON accounts(branch_id);

-- Table: transactions
CREATE TABLE transactions (
    transaction_id         BIGSERIAL PRIMARY KEY,
    account_id             BIGINT NOT NULL REFERENCES accounts(account_id) ON DELETE RESTRICT,
    reference_account_id   BIGINT REFERENCES accounts(account_id) ON DELETE SET NULL,
    transaction_type       VARCHAR(30) NOT NULL,
    amount                 DECIMAL(15,2) NOT NULL,
    currency               VARCHAR(10) NOT NULL DEFAULT 'INR',
    balance_after           DECIMAL(15,2),
    channel                VARCHAR(30),
    transaction_status     VARCHAR(20) NOT NULL DEFAULT 'Success',
    description             TEXT,
    transaction_date       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_transactions_amount CHECK (amount > 0),
    CONSTRAINT chk_transactions_status CHECK (transaction_status IN ('Success', 'Failed', 'Pending', 'Reversed'))
);

COMMENT ON TABLE transactions IS 'Financial transaction ledger. Failed transactions should not alter account balance';

CREATE INDEX idx_transactions_account_id ON transactions(account_id);
CREATE INDEX idx_transactions_transaction_date ON transactions(transaction_date);

-- Table: loan_applications
CREATE TABLE loan_applications (
    loan_id               BIGSERIAL PRIMARY KEY,
    customer_id           BIGINT NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
    product_id            BIGINT NOT NULL REFERENCES banking_products(product_id) ON DELETE RESTRICT,
    loan_amount           DECIMAL(15,2) NOT NULL,
    interest_rate         DECIMAL(5,2),
    tenure_months         INT NOT NULL,
    purpose               VARCHAR(100),
    application_date      DATE NOT NULL DEFAULT CURRENT_DATE,
    approval_status       VARCHAR(20) NOT NULL DEFAULT 'Pending',
    approved_by           BIGINT REFERENCES employees(employee_id) ON DELETE SET NULL,
    approval_date         DATE,
    emi_amount            DECIMAL(12,2),
    outstanding_amount    DECIMAL(15,2),
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_loan_status CHECK (approval_status IN ('Pending', 'Approved', 'Rejected', 'Closed'))
);

COMMENT ON TABLE loan_applications IS 'Customer loan applications. Customer must have Verified KYC to apply';

CREATE INDEX idx_loan_applications_customer_id ON loan_applications(customer_id);
CREATE INDEX idx_loan_applications_loan_id ON loan_applications(loan_id);

-- Table: credit_history
CREATE TABLE credit_history (
    credit_history_id         BIGSERIAL PRIMARY KEY,
    customer_id                BIGINT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    credit_score                INT NOT NULL,
    credit_bureau               VARCHAR(50),
    total_outstanding_debt      DECIMAL(15,2),
    total_credit_limit          DECIMAL(15,2),
    active_loans_count          INT NOT NULL DEFAULT 0,
    missed_payments_count       INT NOT NULL DEFAULT 0,
    defaults_count               INT NOT NULL DEFAULT 0,
    report_date                  DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at                    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_credit_score CHECK (credit_score BETWEEN 300 AND 900)
);

COMMENT ON TABLE credit_history IS 'Customer credit bureau history used for risk assessment and loan decisioning';

CREATE INDEX idx_credit_history_customer_id ON credit_history(customer_id);
CREATE INDEX idx_credit_history_credit_score ON credit_history(credit_score);

-- Table: fraud_transactions
CREATE TABLE fraud_transactions (
    fraud_id              BIGSERIAL PRIMARY KEY,
    transaction_id        BIGINT NOT NULL UNIQUE REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    fraud_probability     DECIMAL(5,4) NOT NULL,
    fraud_type            VARCHAR(50),
    model_used             VARCHAR(100),
    detection_time         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status                  VARCHAR(20) NOT NULL DEFAULT 'Flagged',
    CONSTRAINT chk_fraud_probability CHECK (fraud_probability BETWEEN 0 AND 1)
);

COMMENT ON TABLE fraud_transactions IS 'AI fraud detection results. One-to-zero-or-one relationship with transactions';

-- Table: support_tickets
CREATE TABLE support_tickets (
    ticket_id            BIGSERIAL PRIMARY KEY,
    customer_id          BIGINT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    assigned_to          BIGINT REFERENCES employees(employee_id) ON DELETE SET NULL,
    category             VARCHAR(50),
    subject              VARCHAR(150) NOT NULL,
    description           TEXT NOT NULL,
    priority             VARCHAR(20) NOT NULL DEFAULT 'Medium',
    status                VARCHAR(20) NOT NULL DEFAULT 'Open',
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at            TIMESTAMPTZ,
    resolution_notes       TEXT,
    CONSTRAINT chk_ticket_priority CHECK (priority IN ('Low', 'Medium', 'High', 'Critical')),
    CONSTRAINT chk_ticket_status CHECK (status IN ('Open', 'In Progress', 'Resolved', 'Closed'))
);

COMMENT ON TABLE support_tickets IS 'Customer support tickets. Critical tickets should trigger immediate escalation';

CREATE INDEX idx_support_tickets_customer_id ON support_tickets(customer_id);

-- Table: marketing_campaigns
CREATE TABLE marketing_campaigns (
    campaign_id         BIGSERIAL PRIMARY KEY,
    customer_id         BIGINT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    product_id          BIGINT NOT NULL REFERENCES banking_products(product_id) ON DELETE RESTRICT,
    campaign_name       VARCHAR(100) NOT NULL,
    campaign_type       VARCHAR(50),
    start_date          DATE NOT NULL,
    end_date            DATE,
    channel             VARCHAR(30),
    response_status     VARCHAR(20) NOT NULL DEFAULT 'No Response',
    conversion_date     DATE,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_campaign_response CHECK (response_status IN ('Interested', 'Converted', 'Declined', 'No Response'))
);

COMMENT ON TABLE marketing_campaigns IS 'Targeted marketing campaigns; each row is one customer-campaign interaction';

CREATE INDEX idx_marketing_campaigns_customer_id ON marketing_campaigns(customer_id);

-- Table: prediction_history
CREATE TABLE prediction_history (
    prediction_id          BIGSERIAL PRIMARY KEY,
    customer_id            BIGINT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    reviewed_by            BIGINT REFERENCES employees(employee_id) ON DELETE SET NULL,
    model_name             VARCHAR(100) NOT NULL,
    prediction_type        VARCHAR(50) NOT NULL,
    prediction_result      VARCHAR(50) NOT NULL,
    confidence_score       DECIMAL(5,4),
    input_features         JSONB,
    prediction_date        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    review_status          VARCHAR(20) NOT NULL DEFAULT 'Pending',
    CONSTRAINT chk_prediction_confidence CHECK (confidence_score BETWEEN 0 AND 1),
    CONSTRAINT chk_prediction_review_status CHECK (review_status IN ('Pending', 'Confirmed', 'Dismissed'))
);

COMMENT ON TABLE prediction_history IS 'AI/ML model prediction audit log';

CREATE INDEX idx_prediction_history_customer_id ON prediction_history(customer_id);
CREATE INDEX idx_prediction_history_prediction_date ON prediction_history(prediction_date);

-- Table: branch_performance
CREATE TABLE branch_performance (
    performance_id                 BIGSERIAL PRIMARY KEY,
    branch_id                      BIGINT NOT NULL REFERENCES branches(branch_id) ON DELETE CASCADE,
    report_month                   DATE NOT NULL,
    total_customers                INT NOT NULL DEFAULT 0,
    new_accounts_opened            INT NOT NULL DEFAULT 0,
    total_deposits                 DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    total_withdrawals              DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    total_loans_disbursed          DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    loans_approved_count           INT NOT NULL DEFAULT 0,
    revenue_generated              DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    customer_satisfaction_score    DECIMAL(4,2),
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_branch_report_month UNIQUE (branch_id, report_month)
);

COMMENT ON TABLE branch_performance IS 'Monthly branch KPI performance snapshot. One record per branch per month';

CREATE INDEX idx_branch_performance_branch_id ON branch_performance(branch_id);
CREATE INDEX idx_branch_performance_report_month ON branch_performance(report_month);

-- Trigger function: auto-update updated_at columns
CREATE OR REPLACE FUNCTION trg_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at_customers
    BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();

CREATE TRIGGER set_updated_at_accounts
    BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();

COMMIT;