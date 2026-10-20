from pyspark.sql.functions import col, trim, lower, initcap


def transform_customers(dataframe):
    """
    Apply customer-specific transformations.
    """

    df = dataframe

    # --------------------------------------------------
    # 1. Trim text fields
    # --------------------------------------------------

    string_columns = [
        "name",
        "gender",
        "marital_status",
        "occupation",
        "employment_type",
        "education",
        "email",
        "city",
        "state",
        "country",
        "kyc_status",
    ]

    for column_name in string_columns:

        if column_name in df.columns:

            df = df.withColumn(
                column_name,
                trim(col(column_name))
            )

    # --------------------------------------------------
    # 2. Standardize email addresses
    # --------------------------------------------------

    if "email" in df.columns:

        df = df.withColumn(
            "email",
            lower(col("email"))
        )

    # --------------------------------------------------
    # 3. Standardize gender values
    # --------------------------------------------------

    if "gender" in df.columns:

        df = df.withColumn(
            "gender",
            initcap(col("gender"))
        )

    # --------------------------------------------------
    # 4. Standardize KYC status
    # --------------------------------------------------

    if "kyc_status" in df.columns:

        df = df.withColumn(
            "kyc_status",
            initcap(col("kyc_status"))
        )

    # --------------------------------------------------
    # 5. Standardize country names
    # --------------------------------------------------

    if "country" in df.columns:

        df = df.withColumn(
            "country",
            initcap(col("country"))
        )

    return df