import os
import sys

print("Python Executable:", sys.executable)
print("JAVA_HOME:", os.environ.get("JAVA_HOME"))

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession

print("Creating Spark Session...")

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("SparkTest")
    .getOrCreate()
)

print("Spark Version:", spark.version)

spark.range(5).show()

spark.stop()

print("Success!")