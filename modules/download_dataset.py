
import json
import time
import requests
from pathlib import Path

# StaQC dataset details
DATASET = "koutch/staqc"
CONFIG = "sca_python"
SPLIT = "train"

API_URL = "https://datasets-server.huggingface.co/rows"

# Download settings
TOTAL_RECORDS = 10000
BATCH_SIZE = 100

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_FILE = DATA_DIR / "raw_dataset.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

records = []

print("=" * 55)
print("       CODEMENTOR AI - STAQC DATASET DOWNLOADER")
print("=" * 55)

print("\nDataset:", DATASET)
print("Configuration:", CONFIG)
print("Target records:", TOTAL_RECORDS)

for offset in range(0, TOTAL_RECORDS, BATCH_SIZE):

    params = {
        "dataset": DATASET,
        "config": CONFIG,
        "split": SPLIT,
        "offset": offset,
        "length": BATCH_SIZE
    }

    try:
        response = requests.get(
            API_URL,
            params=params,
            timeout=60
        )

        response.raise_for_status()

        result = response.json()
        rows = result.get("rows", [])

        if not rows:
            print("\nNo more records available.")
            break

        for item in rows:

            row = item["row"]

            question = row.get("question", "")
            code = row.get("snippet", "")

            # StaQC sca_python stores snippet as a string.
            if not isinstance(question, str):
                continue

            if not isinstance(code, str):
                continue

            question = question.strip()
            code = code.strip()

            if not question or not code:
                continue

            records.append({
                "question": question,
                "code": code,
                "language": "Python",
                "source": "StaQC"
            })

        print(
            f"Fetched through row {offset + len(rows)}"
            f" | Valid records: {len(records)}"
        )

        if len(rows) < BATCH_SIZE:
            break

        time.sleep(0.2)

    except requests.RequestException as error:

        print("\nDataset download failed!")
        print("Error:", error)
        print("Please rerun the script to try again.")
        break

# Save downloaded records
with open(OUTPUT_FILE, "w", encoding="utf-8") as file:

    json.dump(
        records,
        file,
        indent=2,
        ensure_ascii=False
    )

print("\n" + "=" * 55)
print("DOWNLOAD SUMMARY")
print("=" * 55)

print("Valid records:", len(records))
print("Target records:", TOTAL_RECORDS)
print("Saved file:", OUTPUT_FILE)

if records:
    print("\nFirst example:")
    print("Question:", records[0]["question"])
    print("Code:", records[0]["code"][:300])
    print("\nDataset download completed.")
else:
    print("\nNo records were downloaded.")
    print("Check the error above before proceeding.")
