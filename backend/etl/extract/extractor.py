from pathlib import Path

from pyspark.sql import DataFrame
from pyspark.sql import SparkSession


class Extractor:

    def __init__(self, spark: SparkSession):

        self.spark = spark

    # ==========================================================
    # CSV READER
    # ==========================================================

    def read_csv(
        self,
        filepath,
        header=True,
        infer_schema=True,
        delimiter=",",
    ) -> DataFrame:

        path = Path(filepath)

        if not path.exists():

            raise FileNotFoundError(
                f"{filepath} not found"
            )

        dataframe = (
            self.spark.read
            .option("header", header)
            .option("inferSchema", infer_schema)
            .option("delimiter", delimiter)
            .csv(str(path))
        )

        return dataframe

    # ==========================================================
    # GERMAN CREDIT READER
    # ==========================================================

    def read_german_credit(
        self,
        filepath,
    ) -> DataFrame:

        path = Path(filepath)

        if not path.exists():

            raise FileNotFoundError(
                f"{filepath} not found"
            )

        dataframe = (
            self.spark.read
            .option("header", False)
            .option("inferSchema", True)
            .option("delimiter", " ")
            .csv(str(path))
        )

        return dataframe

    # ==========================================================
    # AUTOMATIC READER
    # ==========================================================

    def read(self, filepath):
        """
        Automatically select the appropriate reader
        based on the file extension.
        """

        path = Path(filepath)

        if not path.exists():

            raise FileNotFoundError(
                f"{filepath} not found"
            )

        if path.suffix.lower() == ".csv":

            return self.read_csv(filepath)

        if path.suffix.lower() == ".data":

            return self.read_german_credit(filepath)

        raise ValueError(
            f"Unsupported file format: {path.suffix}"
        )