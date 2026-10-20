from pyspark.sql.functions import col, trim, initcap, when


def transform_support_tickets(dataframe):
    """
    Transform the support tickets dataset.
    """
    df = dataframe

    # ============================================================
    # CLEAN ISSUE TYPE
    # ============================================================

    if "issue_type" in df.columns:
        df = df.withColumn(
            "issue_type",
            trim(col("issue_type"))
        )

        df = df.withColumn(
            "issue_type",
            initcap(col("issue_type"))
        )

        # Preserve standard banking abbreviation KYC
        df = df.withColumn(
            "issue_type",
            when(
                col("issue_type") == "Kyc",
                "KYC"
            ).otherwise(col("issue_type"))
        )

    # ============================================================
    # CLEAN PRIORITY
    # ============================================================

    if "priority" in df.columns:
        df = df.withColumn(
            "priority",
            trim(col("priority"))
        )

        df = df.withColumn(
            "priority",
            initcap(col("priority"))
        )

    # ============================================================
    # CLEAN STATUS
    # ============================================================

    if "status" in df.columns:
        df = df.withColumn(
            "status",
            trim(col("status"))
        )

        df = df.withColumn(
            "status",
            initcap(col("status"))
        )

    # ============================================================
    # INTEGER COLUMNS
    # ============================================================

    integer_columns = [
        "ticket_id",
        "customer_id",
    ]

    for column_name in integer_columns:
        if column_name in df.columns:
            df = df.withColumn(
                column_name,
                col(column_name).cast("integer")
            )

    # ============================================================
    # DATE COLUMNS
    # ============================================================

    date_columns = [
        "opened_date",
        "closed_date",
    ]

    for column_name in date_columns:
        if column_name in df.columns:
            df = df.withColumn(
                column_name,
                col(column_name).cast("date")
            )

    return df