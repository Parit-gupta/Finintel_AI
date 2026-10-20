from backend.etl.config.settings import create_spark_session
from backend.etl.extract.extractor import Extractor
from backend.etl.extract.registry import discover_datasets
from backend.etl.transform.transformer import Transformer
from backend.etl.transform.transform_loans import transform_loans


def main():

    spark = create_spark_session()

    extractor = Extractor(spark)

    datasets = discover_datasets()

    dataset_name = "loan_applications"

    dataframe = extractor.read_csv(
        datasets[dataset_name]
    )

    print("=" * 70)
    print("FinIntel AI - Loan Transformation Test")
    print("=" * 70)

    print("\nBefore Loan Transformation")

    dataframe.show(
        5,
        truncate=False
    )

    print("\nOriginal Columns")

    print(dataframe.columns)

    # Generic transformations
    generic_transformer = Transformer(
        dataframe,
        dataset_name
    )

    dataframe = generic_transformer.transform()

    # Loan-specific transformations
    transformed_df = transform_loans(
        dataframe
    )

    print("\nAfter Loan Transformation")

    transformed_df.show(
        5,
        truncate=False
    )

    print("\nFinal Columns")

    print(transformed_df.columns)

    print("\nFinal Schema")

    transformed_df.printSchema()

    spark.stop()


if __name__ == "__main__":
    main()