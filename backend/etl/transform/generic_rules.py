from pyspark.sql.functions import col, trim, when


def drop_empty_rows(dataframe):
    """
    Remove rows where all columns are NULL.
    """

    return dataframe.dropna(
        how="all"
    )


def trim_string_columns(dataframe):
    """
    Remove leading and trailing whitespace
    from all string columns.
    """

    for column_name, data_type in dataframe.dtypes:

        if data_type == "string":

            dataframe = dataframe.withColumn(
                column_name,
                trim(col(column_name))
            )

    return dataframe


def convert_blank_strings_to_null(dataframe):
    """
    Convert empty or whitespace-only strings to NULL.
    """

    for column_name, data_type in dataframe.dtypes:

        if data_type == "string":

            dataframe = dataframe.withColumn(
                column_name,
                when(
                    trim(col(column_name)) == "",
                    None
                ).otherwise(
                    col(column_name)
                )
            )

    return dataframe


def remove_duplicate_rows(dataframe):
    """
    Remove completely identical duplicate rows.
    """

    return dataframe.dropDuplicates()


def apply_generic_rules(dataframe):
    """
    Apply all generic transformation rules.
    """

    dataframe = drop_empty_rows(dataframe)

    dataframe = trim_string_columns(dataframe)

    dataframe = convert_blank_strings_to_null(dataframe)

    dataframe = remove_duplicate_rows(dataframe)

    return dataframe