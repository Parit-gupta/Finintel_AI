from pathlib import Path


RAW_DATA_PATH = Path("datasets/raw")


def discover_datasets():

    datasets = {}

    # --------------------------------------------------
    # Discover CSV datasets recursively
    # --------------------------------------------------

    for file in sorted(RAW_DATA_PATH.rglob("*.csv")):

        relative_path = file.relative_to(
            RAW_DATA_PATH
        )

        dataset_name = str(
            relative_path.with_suffix("")
        ).replace("\\", "_").replace("/", "_")

        datasets[dataset_name] = file

    # --------------------------------------------------
    # Discover German Credit .data files
    # --------------------------------------------------

    for file in sorted(RAW_DATA_PATH.rglob("*.data")):

        relative_path = file.relative_to(
            RAW_DATA_PATH
        )

        dataset_name = str(
            relative_path.with_suffix("")
        ).replace("\\", "_").replace("/", "_")

        datasets[dataset_name] = file

    return datasets

if __name__ == "__main__":

    datasets = discover_datasets()

    print("=" * 70)
    print("Discovered Datasets")
    print("=" * 70)

    for name, path in datasets.items():

        print(f"{name:<50} -> {path}")