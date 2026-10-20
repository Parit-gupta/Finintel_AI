from pyspark.sql.functions import col, trim


# ============================================================
# GERMAN CREDIT
# ============================================================

def transform_german_credit(dataframe):
    """
    Transform the German Credit categorical dataset.
    """

    df = dataframe

    # --------------------------------------------------------
    # 1. Assign meaningful column names
    # --------------------------------------------------------

    column_names = [
        "checking_account",
        "duration",
        "credit_history",
        "purpose",
        "credit_amount",
        "savings_account",
        "employment_since",
        "installment_rate",
        "personal_status_sex",
        "other_debtors",
        "residence_since",
        "property",
        "age",
        "other_installment_plans",
        "housing",
        "existing_credits",
        "job",
        "dependents",
        "telephone",
        "foreign_worker",
        "credit_class",
    ]

    df = df.toDF(*column_names)

    # --------------------------------------------------------
    # 2. Trim categorical columns
    # --------------------------------------------------------

    categorical_columns = [
        "checking_account",
        "credit_history",
        "purpose",
        "savings_account",
        "employment_since",
        "personal_status_sex",
        "other_debtors",
        "property",
        "other_installment_plans",
        "housing",
        "job",
        "telephone",
        "foreign_worker",
    ]

    for column_name in categorical_columns:

        df = df.withColumn(
            column_name,
            trim(col(column_name))
        )

    # --------------------------------------------------------
    # 3. Ensure numeric columns have correct types
    # --------------------------------------------------------

    numeric_columns = [
        "duration",
        "credit_amount",
        "installment_rate",
        "residence_since",
        "age",
        "existing_credits",
        "dependents",
        "credit_class",
    ]

    for column_name in numeric_columns:

        df = df.withColumn(
            column_name,
            col(column_name).cast("integer")
        )

    return df


# ============================================================
# GIVE ME SOME CREDIT
# ============================================================

def transform_credit_score(dataframe):
    """
    Transform the Give Me Some Credit dataset.
    """

    df = dataframe

    # --------------------------------------------------------
    # 1. Remove whitespace from column names
    # --------------------------------------------------------

    for column_name in df.columns:

        cleaned_name = column_name.strip()

        if column_name != cleaned_name:

            df = df.withColumnRenamed(
                column_name,
                cleaned_name
            )

    # --------------------------------------------------------
    # 2. Rename unnamed ID column
    # --------------------------------------------------------

    if "_c0" in df.columns:

        df = df.withColumnRenamed(
            "_c0",
            "record_id"
        )

    # --------------------------------------------------------
    # 3. Convert numerical columns
    # --------------------------------------------------------

    double_columns = [
        "RevolvingUtilizationOfUnsecuredLines",
        "age",
        "NumberOfTime30-59DaysPastDueNotWorse",
        "DebtRatio",
        "MonthlyIncome",
        "NumberOfOpenCreditLinesAndLoans",
        "NumberOfTimes90DaysLate",
        "NumberRealEstateLoansOrLines",
        "NumberOfTime60-89DaysPastDueNotWorse",
        "NumberOfDependents",
    ]

    for column_name in double_columns:

        if column_name in df.columns:

            df = df.withColumn(
                column_name,
                col(column_name).cast("double")
            )

    # --------------------------------------------------------
    # 4. Record ID as integer
    # --------------------------------------------------------

    if "record_id" in df.columns:

        df = df.withColumn(
            "record_id",
            col("record_id").cast("integer")
        )

    # --------------------------------------------------------
    # 5. Target column as integer
    # --------------------------------------------------------

    if "SeriousDlqin2yrs" in df.columns:

        df = df.withColumn(
            "SeriousDlqin2yrs",
            col("SeriousDlqin2yrs").cast("integer")
        )

    return df