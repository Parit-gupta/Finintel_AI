from pathlib import Path


class ValidationReport:

    def __init__(self):

        self.report_directory = Path("backend/etl/reports")

        self.report_directory.mkdir(
            parents=True,
            exist_ok=True
        )

    def save(
        self,
        dataset_name,
        validator,
    ):

        report = self.report_directory / f"{dataset_name}.txt"

        with open(report, "w") as file:

            file.write("=" * 60 + "\n")

            file.write(f"Dataset : {dataset_name}\n\n")

            file.write(
                f"Rows : {validator.row_count()}\n"
            )

            file.write(
                f"Columns : {validator.column_count()}\n"
            )

            file.write(
                f"Duplicate Rows : {validator.duplicate_count()}\n\n"
            )

            file.write("Data Types\n")

            file.write("-" * 30 + "\n")

            for column, dtype in validator.data_types().items():

                file.write(f"{column} : {dtype}\n")

            file.write("\nMissing Values\n")

            file.write("-" * 30 + "\n")

            for column, value in validator.missing_values().items():

                file.write(f"{column} : {value}\n")