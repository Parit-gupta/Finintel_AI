from pyspark.sql.functions import col, isnan
from pyspark.sql.types import (
    DoubleType,
    FloatType,
    IntegerType,
    LongType,
    ShortType,
    DecimalType,
)


class DataValidator:

    def __init__(self, dataframe, dataset_name):

        self.df = dataframe
        self.dataset_name = dataset_name

    def row_count(self):

        return self.df.count()

    def column_count(self):

        return len(self.df.columns)

    def duplicate_count(self):

        return self.df.count() - self.df.dropDuplicates().count()

    def missing_values(self):

        result = {}

        numeric_types = (
            IntegerType,
            LongType,
            FloatType,
            DoubleType,
            ShortType,
            DecimalType,
        )

        schema = self.df.schema

        for field in schema:

            column = field.name

            if isinstance(field.dataType, numeric_types):

                missing = self.df.filter(
                    col(column).isNull() | isnan(col(column))
                ).count()

            else:

                missing = self.df.filter(
                    col(column).isNull()
                ).count()

            result[column] = missing

        return result

    def data_types(self):

        return dict(self.df.dtypes)
    