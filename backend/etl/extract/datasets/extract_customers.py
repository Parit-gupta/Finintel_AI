from pyspark.sql import SparkSession

from backend.etl.utils.logger import logger


def extract_customers(spark: SparkSession):
    try:
        path = "datasets/raw/customers.csv"

        df = (
            spark.read
            .option("header", True)
            .option("inferSchema", True)
            .csv(path)
        )

        logger.info("customers.csv loaded successfully")

        print("\nCustomers Schema")
        df.printSchema()

        print("\nSample Records")
        df.show(5)

        print(f"\nTotal Records : {df.count()}")

        return df

    except Exception as e:
        logger.error(str(e))
        raise