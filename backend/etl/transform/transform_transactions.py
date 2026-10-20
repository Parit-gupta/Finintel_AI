from pyspark.sql.functions import col, trim, upper


def transform_transactions(dataframe):
    """
    Apply transaction-specific transformations.
    """

    df = dataframe

    # --------------------------------------------------
    # 1. Trim transaction type
    # --------------------------------------------------

    if "type" in df.columns:

        df = df.withColumn(
            "type",
            trim(col("type"))
        )

    # --------------------------------------------------
    # 2. Standardize transaction type
    # --------------------------------------------------

    if "type" in df.columns:

        df = df.withColumn(
            "type",
            upper(col("type"))
        )

    # --------------------------------------------------
    # 3. Trim origin account/customer identifier
    # --------------------------------------------------

    if "nameOrig" in df.columns:

        df = df.withColumn(
            "nameOrig",
            trim(col("nameOrig"))
        )

    # --------------------------------------------------
    # 4. Trim destination account/customer identifier
    # --------------------------------------------------

    if "nameDest" in df.columns:

        df = df.withColumn(
            "nameDest",
            trim(col("nameDest"))
        )

    # --------------------------------------------------
    # 5. Ensure monetary values are non-negative
    # --------------------------------------------------

    monetary_columns = [
        "amount",
        "oldbalanceOrg",
        "newbalanceOrig",
        "oldbalanceDest",
        "newbalanceDest",
    ]

    for column_name in monetary_columns:

        if column_name in df.columns:

            df = df.withColumn(
                column_name,
                col(column_name).cast("double")
            )

    # --------------------------------------------------
    # 6. Ensure fraud indicators are integers
    # --------------------------------------------------

    fraud_columns = [
        "isFraud",
        "isFlaggedFraud",
    ]

    for column_name in fraud_columns:

        if column_name in df.columns:

            df = df.withColumn(
                column_name,
                col(column_name).cast("integer")
            )

    return df