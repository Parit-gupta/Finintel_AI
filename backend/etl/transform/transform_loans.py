from pyspark.sql.functions import col, trim, initcap


def transform_loans(dataframe):
    """
    Apply loan-specific transformations.
    """

    df = dataframe

    # --------------------------------------------------
    # 1. Remove accidental whitespace from column names
    # --------------------------------------------------

    for column_name in df.columns:

        cleaned_name = column_name.strip()

        if column_name != cleaned_name:

            df = df.withColumnRenamed(
                column_name,
                cleaned_name
            )

    # --------------------------------------------------
    # 2. Trim categorical columns
    # --------------------------------------------------

    string_columns = [
        "education",
        "self_employed",
        "loan_status",
    ]

    for column_name in string_columns:

        if column_name in df.columns:

            df = df.withColumn(
                column_name,
                trim(col(column_name))
            )

    # --------------------------------------------------
    # 3. Standardize education values
    # --------------------------------------------------

    if "education" in df.columns:

        df = df.withColumn(
            "education",
            initcap(col("education"))
        )

    # --------------------------------------------------
    # 4. Standardize self-employed values
    # --------------------------------------------------

    if "self_employed" in df.columns:

        df = df.withColumn(
            "self_employed",
            initcap(col("self_employed"))
        )

    # --------------------------------------------------
    # 5. Standardize loan status
    # --------------------------------------------------

    if "loan_status" in df.columns:

        df = df.withColumn(
            "loan_status",
            initcap(col("loan_status"))
        )

    # --------------------------------------------------
    # 6. Ensure financial columns are numeric
    # --------------------------------------------------

    financial_columns = [
        "income_annum",
        "loan_amount",
        "residential_assets_value",
        "commercial_assets_value",
        "luxury_assets_value",
        "bank_asset_value",
    ]

    for column_name in financial_columns:

        if column_name in df.columns:

            df = df.withColumn(
                column_name,
                col(column_name).cast("integer")
            )

    # --------------------------------------------------
    # 7. Ensure CIBIL score is integer
    # --------------------------------------------------

    if "cibil_score" in df.columns:

        df = df.withColumn(
            "cibil_score",
            col("cibil_score").cast("integer")
        )

    return df