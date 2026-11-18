
import json
from pathlib import Path


# --------------------------------------------------
# FILE PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

STAQC_PATH = BASE_DIR / "data" / "processed_dataset.json"

SUPPLEMENTARY_PATH = (
    BASE_DIR / "data" / "additional_python_examples.json"
)

OUTPUT_PATH = BASE_DIR / "data" / "combined_dataset.json"


# --------------------------------------------------
# LOAD DATASETS
# --------------------------------------------------

print("Loading StaQC dataset...")

with open(STAQC_PATH, "r", encoding="utf-8") as file:
    staqc_data = json.load(file)


print("Loading supplementary dataset...")

with open(SUPPLEMENTARY_PATH, "r", encoding="utf-8") as file:
    supplementary_data = json.load(file)


# --------------------------------------------------
# COMBINE DATASETS
# --------------------------------------------------

combined_data = staqc_data + supplementary_data


# --------------------------------------------------
# VALIDATE RECORDS
# --------------------------------------------------

required_fields = {
    "question",
    "code",
    "language",
    "source"
}

for index, record in enumerate(combined_data):

    if not required_fields.issubset(record):
        raise ValueError(
            f"Missing fields in record {index}"
        )

    if not isinstance(record["question"], str):
        raise ValueError(f"Invalid question in record {index}")

    if not isinstance(record["code"], str):
        raise ValueError(f"Invalid code in record {index}")

    if not record["question"].strip() or not record["code"].strip():
        raise ValueError(f"Empty question or code in record {index}")


# --------------------------------------------------
# SAVE COMBINED DATASET
# --------------------------------------------------

with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
    json.dump(
        combined_data,
        file,
        indent=2,
        ensure_ascii=False
    )


# --------------------------------------------------
# DISPLAY SUMMARY
# --------------------------------------------------

staqc_count = sum(
    record["source"] == "StaQC"
    for record in combined_data
)

supplementary_count = sum(
    record["source"] == "Supplementary"
    for record in combined_data
)

print("\n" + "=" * 50)
print("DATASET COMBINATION COMPLETED")
print("=" * 50)

print("Original StaQC records:", staqc_count)
print("Supplementary records:", supplementary_count)
print("Total combined records:", len(combined_data))

print("\nSaved file:", OUTPUT_PATH)

