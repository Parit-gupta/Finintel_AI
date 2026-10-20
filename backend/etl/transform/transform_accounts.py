from pyspark.sql.functions import col, trim, initcap


def transform_accounts(dataframe):
    """
    Apply account-specific transformations.
    """

    df = dataframe

    # --------------------------------------------------
    # 1. Trim string columns
    # --------------------------------------------------

    string_columns = [
        "account_type",
        "status",
    ]

    for column_name in string_columns:

        if column_name in df.columns:

            df = df.withColumn(
                column_name,
                trim(col(column_name))
            )

    # --------------------------------------------------
    # 2. Standardize account type
    # --------------------------------------------------

    if "account_type" in df.columns:

        df = df.withColumn(
            "account_type",
            initcap(col("account_type"))
        )

    # --------------------------------------------------
    # 3. Standardize account status
    # --------------------------------------------------

    if "status" in df.columns:

        df = df.withColumn(
            "status",
            initcap(col("status"))
        )

    return df