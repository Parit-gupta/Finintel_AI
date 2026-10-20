from backend.etl.config.settings import create_spark_session
from backend.etl.extract.extractor import Extractor
from backend.etl.transform.transform_credit import transform_credit_score


def main():

    spark = create_spark_session()

    extractor = Extractor(spark)

    filepath = (
        "datasets/raw/give_me_some_credit/"
        "credit_score_train.csv"
    )

    dataframe = extractor.read_csv(
        filepath
    )

    print("=" * 70)
    print("FinIntel AI - Give Me Some Credit Transformation Test")
    print("=" * 70)

    print("\nBefore Transformation")

    dataframe.show(
        5,
        truncate=False
    )

    print("\nRows Before")

    print(dataframe.count())

    transformed_df = transform_credit_score(
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