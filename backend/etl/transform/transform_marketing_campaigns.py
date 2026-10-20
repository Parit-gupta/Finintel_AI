from pyspark.sql.functions import col, trim, initcap


def transform_marketing_campaigns(dataframe):
    """
    Transform the marketing campaigns dataset.
    """
    df = dataframe

    # ============================================================
    # CLEAN STRING COLUMNS
    # ============================================================

    string_columns = [
        "offer",
        "channel",
    ]

    for column_name in string_columns:
        if column_name in df.columns:
            df = df.withColumn(
                column_name,
                trim(col(column_name))
            )

    # Standardize capitalization
    if "offer" in df.columns:
        df = df.withColumn(
            "offer",
            initcap(col("offer"))
        )

    if "channel" in df.columns:
        df = df.withColumn(
            "channel",
            initcap(col("channel"))
        )

    # ============================================================
    # INTEGER COLUMNS
    # ============================================================

    integer_columns = [
        "campaign_id",
        "customer_id",
        "accepted",
    ]

    for column_name in integer_columns:
        if column_name in df.columns:
            df = df.withColumn(
                column_name,
                col(column_name).cast("integer")
            )

    return df