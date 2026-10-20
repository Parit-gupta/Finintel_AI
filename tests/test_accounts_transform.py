from backend.etl.config.settings import create_spark_session
from backend.etl.extract.extractor import Extractor
from backend.etl.extract.registry import discover_datasets
from backend.etl.transform.transformer import Transformer
from backend.etl.transform.transform_accounts import transform_accounts


def main():

    spark = create_spark_session()

    extractor = Extractor(spark)

    datasets = discover_datasets()

    dataset_name = "accounts"

    dataframe = extractor.read_csv(
        datasets[dataset_name]
    )

    print("=" * 70)
    print("FinIntel AI - Accounts Transformation Test")
    print("=" * 70)

    print("\nBefore Account Transformation")

    dataframe.show(
        5,
        truncate=False
    )

    # Generic transformations
    generic_transformer = Transformer(
        dataframe,
        dataset_name
    )

    dataframe = generic_transformer.transform()

    # Account-specific transformations
    transformed_df = transform_accounts(
        dataframe
    )

    print("\nAfter Account Transformation")

    transformed_df.show(
        5,
        truncate=False
    )

    print("\nFinal Schema")

    transformed_df.printSchema()

    spark.stop()


if __name__ == "__main__":
    main()