from pyspark.sql.functions import col, trim, initcap, when


def transform_banking_products(dataframe):
    """
    Transform the banking products dataset.
    """
    df = dataframe

    # ============================================================
    # CLEAN PRODUCT NAME
    # ============================================================

    if "product_name" in df.columns:
        # Remove leading and trailing spaces
        df = df.withColumn(
            "product_name",
            trim(col("product_name"))
        )

        # Standardize product name capitalization
        df = df.withColumn(
            "product_name",
            initcap(col("product_name"))
        )

        # Preserve standard banking abbreviation "FD"
        df = df.withColumn(
            "product_name",
            when(
                col("product_name") == "Fd",
                "FD"
            ).otherwise(col("product_name"))
        )

    # ============================================================
    # PRODUCT ID
    # ============================================================

    if "product_id" in df.columns:
        df = df.withColumn(
            "product_id",
            col("product_id").cast("integer")
        )

    # ============================================================
    # INTEREST RATE
    # ============================================================

    if "interest_rate" in df.columns:
        df = df.withColumn(
            "interest_rate",
            col("interest_rate").cast("double")
        )

    return df