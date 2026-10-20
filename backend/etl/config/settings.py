import os

from dotenv import load_dotenv
from pyspark.sql import SparkSession


# ==========================================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================================

load_dotenv()


# ==========================================================
# SPARK SESSION
# ==========================================================

def create_spark_session():

    spark = (
        SparkSession.builder
        .appName("FinIntel AI ETL")
        .master("local[*]")
        .config(
            "spark.jars",
            r"E:\Project_1\jars\postgresql-42.7.13.jar"
        )
        .getOrCreate()
    )

    return spark