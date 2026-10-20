from pyspark.sql.functions import col


# ============================================================
# CREDIT CARD FRAUD
# ============================================================

def transform_credit_card_fraud(dataframe):
    """
    Transform the Credit Card Fraud dataset.
    """

    df = dataframe

    # --------------------------------------------------------
    # 1. Convert monetary and numerical columns
    # --------------------------------------------------------

    double_columns = [
        "Time",
        "Amount",
    ]

    for column_name in double_columns:

        if column_name in df.columns:

            df = df.withColumn(
                column_name,
                col(column_name).cast("double")
            )

    # --------------------------------------------------------
    # 2. Convert PCA feature columns to double
    # --------------------------------------------------------

    pca_columns = [
        f"V{i}"
        for i in range(1, 29)
    ]

    for column_name in pca_columns:

        if column_name in df.columns:

            df = df.withColumn(
                column_name,
                col(column_name).cast("double")
            )

    # --------------------------------------------------------
    # 3. Convert fraud target to integer
    # --------------------------------------------------------

    if "Class" in df.columns:

        df = df.withColumn(
            "Class",
            col("Class").cast("integer")
        )

    return df