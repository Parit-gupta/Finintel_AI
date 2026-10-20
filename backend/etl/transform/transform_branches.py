from pyspark.sql.functions import col, trim, initcap


# ============================================================
# BRANCHES
# ============================================================

def transform_branches(dataframe):
    """
    Transform the branches dataset.
    """

    df = dataframe

    # --------------------------------------------------------
    # 1. Clean string columns
    # --------------------------------------------------------

    string_columns = [
        "branch_name",
        "city",
        "manager",
    ]

    for column_name in string_columns:

        if column_name in df.columns:

            df = df.withColumn(
                column_name,
                trim(col(column_name))
            )

    # --------------------------------------------------------
    # 2. Standardize text capitalization
    # --------------------------------------------------------

    if "branch_name" in df.columns:

        df = df.withColumn(
            "branch_name",
            initcap(col("branch_name"))
        )

    if "city" in df.columns:

        df = df.withColumn(
            "city",
            initcap(col("city"))
        )

    if "manager" in df.columns:

        df = df.withColumn(
            "manager",
            initcap(col("manager"))
        )

    # --------------------------------------------------------
    # 3. Ensure numeric columns have correct types
    # --------------------------------------------------------

    integer_columns = [
        "branch_id",
        "employees",
    ]

    for column_name in integer_columns:

        if column_name in df.columns:

            df = df.withColumn(
                column_name,
                col(column_name).cast("integer")
            )

    return df