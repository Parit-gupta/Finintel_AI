from backend.etl.config.settings import create_spark_session
from backend.etl.extract.extractor import Extractor
from backend.etl.transform.transform_credit import transform_german_credit


def main():

    spark = create_spark_session()

    extractor = Extractor(spark)

    filepath = (
        "datasets/raw/german_credit/german.data"
    )

    dataframe = extractor.read_german_credit(
        filepath
    )

    print("=" * 70)
    print("FinIntel AI - German Credit Transformation Test")
    print("=" * 70)

    print("\nBefore Transformation")

    dataframe.show(
        5,
        truncate=False
    )

    print("\nRows Before")

    print(dataframe.count())

    transformed_df = transform_german_credit(
        dataframe
    )

    print("\nAfter Transformation")

    transformed_df.show(
        5,
        truncate=False
    )

    print("\nRows After")

    print(transformed_df.count())

    print("\nFinal Columns")

    print(transformed_df.columns)

    print("\nFinal Schema")

    transformed_df.printSchema()

    spark.stop()


if __name__ == "__main__":
    main()