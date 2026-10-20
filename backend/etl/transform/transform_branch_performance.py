from pyspark.sql.functions import col, trim, initcap


def transform_branch_performance(dataframe):
    """
    Transform the branch performance dataset.
    """
    df = dataframe

    # ============================================================
    # CLEAN MONTH
    # ============================================================

    if "month" in df.columns:
        df = df.withColumn(
            "month",
            trim(col("month"))
        )

        df = df.withColumn(
            "month",
            initcap(col("month"))
        )

    # ============================================================
    # INTEGER COLUMNS
    # ============================================================

    integer_columns = [
        "branch_id",
        "year",
        "revenue",
        "expenses",
        "profit",
        "loan_disbursed",
        "new_customers",
        "fraud_cases",
    ]

    for column_name in integer_columns:
        if column_name in df.columns:
            df = df.withColumn(
                column_name,
                col(column_name).cast("integer")
            )

    # ============================================================
    # CUSTOMER SATISFACTION
    # ============================================================

    if "customer_satisfaction" in df.columns:
        df = df.withColumn(
            "customer_satisfaction",
            col("customer_satisfaction").cast("double")
        )

    return df