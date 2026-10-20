from backend.etl.config.settings import create_spark_session
from backend.etl.extract.extractor import Extractor
from backend.etl.extract.registry import discover_datasets
from backend.etl.transform.transformer import Transformer
from backend.etl.transform.transform_customers import transform_customers


def main():

    spark = create_spark_session()

    extractor = Extractor(spark)

    datasets = discover_datasets()

    dataset_name = "customers"

    dataframe = extractor.read_csv(
        datasets[dataset_name]
    )

    print("=" * 70)
    print("FinIntel AI - Customer Transformation Test")
    print("=" * 70)

    print("\nBefore Customer Transformation")

    dataframe.show(
        5,
        truncate=False
    )

    # First apply generic transformations
    generic_transformer = Transformer(
        dataframe,
        dataset_name
    )

    dataframe = generic_transformer.transform()

    # Then apply customer-specific transformations
    transformed_df = transform_customers(
        dataframe
    )

    print("\nAfter Customer Transformation")

    transformed_df.show(
        5,
        truncate=False
    )

    print("\nFinal Schema")

    transformed_df.printSchema()

    spark.stop()


if __name__ == "__main__":
    main()