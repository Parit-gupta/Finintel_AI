from backend.etl.config.settings import create_spark_session
from backend.etl.extract.extractor import Extractor
from backend.etl.transform.transform_branches import (
    transform_branches
)


def main():

    spark = create_spark_session()

    extractor = Extractor(spark)

    filepath = (
        "datasets/raw/branches.csv"
    )

    dataframe = extractor.read_csv(
        filepath
    )

    print("=" * 70)
    print("FinIntel AI - Branches Transformation Test")
    print("=" * 70)

    print("\nBefore Transformation")

    dataframe.show(
        5,
        truncate=False
    )

    print("\nRows Before")

    rows_before = dataframe.count()

    print(rows_before)

    transformed_df = transform_branches(
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

    spark.stop()


if __name__ == "__main__":
    main()