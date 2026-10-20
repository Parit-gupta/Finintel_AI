from pyspark.sql.functions import col, trim, initcap, lower


def transform_user_roles(dataframe):
    """
    Transform the user roles dataset.
    """
    df = dataframe

    # ============================================================
    # CLEAN USERNAME
    # ============================================================

    if "username" in df.columns:
        df = df.withColumn(
            "username",
            trim(col("username"))
        )

    # ============================================================
    # CLEAN EMAIL
    # ============================================================

    if "email" in df.columns:
        df = df.withColumn(
            "email",
            trim(col("email"))
        )

        # Standardize email addresses to lowercase
        df = df.withColumn(
            "email",
            lower(col("email"))
        )

    # ============================================================
    # PASSWORD HASH
    # ============================================================
    # password_hash is intentionally preserved without modification.
    # It represents a hashed credential and should not be altered
    # during ETL transformation.

    # ============================================================
    # CLEAN ROLE
    # ============================================================

    if "role" in df.columns:
        df = df.withColumn(
            "role",
            trim(col("role"))
        )

        df = df.withColumn(
            "role",
            initcap(col("role"))
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
        "user_id",
        "branch_id",
    ]

    for column_name in integer_columns:
        if column_name in df.columns:
            df = df.withColumn(
                column_name,
                col(column_name).cast("integer")
            )

    # ============================================================
    # TIMESTAMP COLUMN
    # ============================================================

    if "last_login" in df.columns:
        df = df.withColumn(
            "last_login",
            col("last_login").cast("timestamp")
        )

    return df