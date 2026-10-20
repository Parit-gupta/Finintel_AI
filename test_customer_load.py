from backend.etl.config.settings import create_spark_session
from backend.etl.extract.extractor import Extractor
from backend.etl.transform.transformer import Transformer
from backend.etl.load.postgres_loader import PostgreSQLLoader


def main():

    print("=" * 70)
    print("FinIntel AI - Customer PostgreSQL Load Test")
    print("=" * 70)

    # ----------------------------------------------------------
    # Spark
    # ----------------------------------------------------------

    spark = create_spark_session()

    # ----------------------------------------------------------
    # Extract
    # ----------------------------------------------------------

    extractor = Extractor(spark)

    dataframe = extractor.read(
        "datasets/raw/customers.csv"
    )

    print(
        f"Rows extracted : {dataframe.count()}"
    )

    # ----------------------------------------------------------
    # Transform
    # ----------------------------------------------------------

    transformer = Transformer(
        dataframe,
        "customers"
    )

    transformed_df = transformer.transform()

    print(
        f"Rows transformed : {transformed_df.count()}"
    )

    # ----------------------------------------------------------
    # PostgreSQL Load
    # ----------------------------------------------------------

    loader = PostgreSQLLoader()

    loader.load_customers(
        transformed_df
    )

    # ----------------------------------------------------------
    # Stop Spark
    # ----------------------------------------------------------

    spark.stop()

    print("=" * 70)
    print("Customer staging load completed")
    print("=" * 70)


if __name__ == "__main__":
    main()