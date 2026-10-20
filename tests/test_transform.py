from backend.etl.config.settings import create_spark_session
from backend.etl.extract.extractor import Extractor
from backend.etl.extract.registry import discover_datasets
from backend.etl.transform.transformer import Transformer


def main():

    spark = create_spark_session()

    extractor = Extractor(spark)

    datasets = discover_datasets()

    print("=" * 70)
    print("FinIntel AI - Generic Transformation Test")
    print("=" * 70)

    dataset_name = "credit"

    dataset_path = datasets[dataset_name]

    print(f"\nDataset : {dataset_name}")

    dataframe = extractor.read_csv(
        dataset_path
    )

    before_count = dataframe.count()

    print(
        f"Rows before transformation : "
        f"{before_count}"
    )

    transformer = Transformer(
        dataframe,
        dataset_name
    )

    transformed_df = transformer.transform()

    after_count = transformed_df.count()

    print(
        f"Rows after transformation  : "
        f"{after_count}"
    )

    print(
        f"Rows removed               : "
        f"{before_count - after_count}"
    )

    print("\nTransformed Schema")

    transformed_df.printSchema()

    print("\nFirst 5 Rows")

    transformed_df.show(
        5,
        truncate=False
    )

    spark.stop()


if __name__ == "__main__":
    main()