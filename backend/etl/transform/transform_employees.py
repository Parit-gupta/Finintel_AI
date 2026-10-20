from pyspark.sql.functions import col, trim, initcap


def transform_employees(dataframe):
    """
    Transform the employees dataset.
    """
    df = dataframe

    # ============================================================
    # CLEAN STRING COLUMNS
    # ============================================================

    string_columns = [
        "designation",
        "department",
    ]

    for column_name in string_columns:
        if column_name in df.columns:
            df = df.withColumn(
                column_name,
                trim(col(column_name))
            )

    # Standardize capitalization
    if "designation" in df.columns:
        df = df.withColumn(
            "designation",
            initcap(col("designation"))
        )

    if "department" in df.columns:
        df = df.withColumn(
            "department",
            initcap(col("department"))
        )

    # ============================================================
    # INTEGER COLUMNS
    # ============================================================

    integer_columns = [
        "employee_id",
        "branch_id",
        "salary",
    ]

    for column_name in integer_columns:
        if column_name in df.columns:
            df = df.withColumn(
                column_name,
                col(column_name).cast("integer")
            )

    # ============================================================
    # DATE COLUMN
    # ============================================================

    if "joining_date" in df.columns:
        df = df.withColumn(
            "joining_date",
            col("joining_date").cast("date")
        )

    return df