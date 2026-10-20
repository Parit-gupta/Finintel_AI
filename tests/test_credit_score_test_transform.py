from backend.etl.config.settings import create_spark_session
from backend.etl.extract.extractor import Extractor
from backend.etl.transform.transform_credit import transform_credit_score


def main():

    spark = create_spark_session()

    extractor = Extractor(spark)

    filepath = (
        "datasets/raw/give_me_some_credit/"
        "credit_score_test.csv"
    )

    dataframe = extractor.read_csv(
        filepath
    )

    print("=" * 70)
    print("FinIntel AI - Give Me Some Credit Test Transformation")
    print("=" * 70)

    print("\nBefore Transformation")

    dataframe.show(
        5,
        truncate=False
    )

    print("\nRows Before")

    rows_before = dataframe.count()

    print(rows_before)

    transformed_df = transform_credit_score(
        dataframe
    )

    print("\nAfter Transformation")

    transformed_df.show(
        5,
        truncate=False
    )

    print("\nRows After")

    rows_after = transformed_df.count()

    print(rows_after)

    print("\nRows Removed")

    print(rows_before - rows_after)

    print("\nFinal Columns")

    print(transformed_df.columns)

    print("\nFinal Schema")

    transformed_df.printSchema()

    print("\nMissing Target Values")

    missing_target = transformed_df.filter(
        transformed_df["SeriousDlqin2yrs"].isNull()
    ).count()

    print(
        f"NULL SeriousDlqin2yrs values : "
        f"{missing_target}"
    )

    print("\nNon-NULL Target Values")

    non_missing_target = transformed_df.filter(
        transformed_df["SeriousDlqin2yrs"].isNotNull()
    ).count()

    print(
        f"Non-NULL SeriousDlqin2yrs values : "
        f"{non_missing_target}"
    )

    spark.stop()


if __name__ == "__main__":
    main()