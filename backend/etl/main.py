from backend.etl.config.settings import create_spark_session
from backend.etl.extract.extractor import Extractor
from backend.etl.extract.registry import discover_datasets
from backend.etl.validation.validator import DataValidator
from backend.etl.validation.report import ValidationReport
from backend.etl.transform.transformer import Transformer


def main():
    spark = create_spark_session()

    extractor = Extractor(spark)
    datasets = discover_datasets()

    report = ValidationReport()

    print("=" * 70)
    print("FinIntel AI - Integrated ETL Pipeline")
    print("=" * 70)

    for dataset_name, dataset_path in datasets.items():

        # Skip files that are not required for the business pipeline
        if dataset_name == "give_me_some_credit_sample_submission":
            print(
                f"\nSkipping : {dataset_name}"
            )
            continue

        print("\n" + "-" * 70)
        print(f"Dataset : {dataset_name}")
        print(f"Path    : {dataset_path}")
        print("-" * 70)

        try:
            # ====================================================
            # EXTRACT
            # ====================================================

            print("\n[1] Extracting dataset...")

            dataframe = extractor.read(dataset_path)

            rows_before = dataframe.count()

            print(f"Rows extracted : {rows_before}")
            print(
                f"Columns        : "
                f"{len(dataframe.columns)}"
            )

            # ====================================================
            # VALIDATE
            # ====================================================

            print("\n[2] Validating dataset...")

            validator = DataValidator(
                dataframe,
                dataset_name
            )

            report.save(
                dataset_name,
                validator
            )

            print(
                f"Duplicate rows : "
                f"{validator.duplicate_count()}"
            )

            # ====================================================
            # TRANSFORM
            # ====================================================

            print("\n[3] Transforming dataset...")

            transformer = Transformer(
                dataframe,
                dataset_name
            )

            transformed_df = transformer.transform()

            rows_after = transformed_df.count()

            print(
                f"Rows after transformation : "
                f"{rows_after}"
            )

            print(
                f"Rows removed               : "
                f"{rows_before - rows_after}"
            )

            print("\nFinal Schema:")
            transformed_df.printSchema()

            print("\nTransformation successful.")

        except Exception as error:

            print(
                f"\nFAILED : {dataset_name}"
            )

            print(
                f"Error  : {error}"
            )

    print("\n")
    print("=" * 70)
    print("Integrated ETL Pipeline Completed")
    print("=" * 70)

    spark.stop()


if __name__ == "__main__":
    main()