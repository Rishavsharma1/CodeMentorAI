
import ast
import json
import re
import warnings
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

INPUT_FILE = DATA_DIR / "raw_dataset.json"
OUTPUT_FILE = DATA_DIR / "processed_dataset.json"


def clean_code(code):
    """Remove Markdown code fences and surrounding whitespace."""

    code = code.strip()

    code = re.sub(
        r"^```(?:python)?\s*",
        "",
        code,
        flags=re.IGNORECASE
    )

    code = re.sub(r"\s*```$", "", code)

    return code.strip()


def looks_like_other_language(code):
    """Reject obvious examples written in other programming languages."""

    patterns = [
        # R language
        r"<-",
        r"\bset\.seed\s*\(",
        r"\brbeta\s*\(",
        r"\bdata\.frame\s*\(",
        r"\blibrary\s*\(",
        r"%>%",

        # JavaScript
        r"^\s*(const|let|var)\s+\w+",
        r"\bconsole\.log\s*\(",
        r"=>",

        # SQL
        r"^\s*(SELECT|INSERT|UPDATE|DELETE|CREATE TABLE)\b",

        # Java and C/C++
        r"\b(public|private|protected)\s+static\s+void\b",
        r"#include\s*[<\"]",
        r"\bSystem\.out\.println\s*\(",

        # Shell commands
        r"^\s*#!/bin/(ba)?sh\b",
        r"^\s*(sudo|apt-get|brew install|npm install)\b",

        # AppleScript
        r"\btell application\b",
        r"\bend tell\b",
    ]

    for pattern in patterns:
        if re.search(pattern, code, flags=re.IGNORECASE | re.MULTILINE):
            return True

    return False


def is_valid_python(code):
    """Check Python syntax and reject obvious non-Python code."""

    if looks_like_other_language(code):
        return False

    try:
        # Some valid Python snippets contain regex strings
        # that produce SyntaxWarning messages.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            ast.parse(code)

        return True

    except (SyntaxError, ValueError, TypeError):
        return False


def preprocess_dataset():

    print("=" * 55)
    print("       CODEMENTOR AI - DATA PREPROCESSOR")
    print("=" * 55)

    if not INPUT_FILE.exists():
        print("ERROR: Raw dataset file not found!")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        raw_records = json.load(file)

    print("\nOriginal records:", len(raw_records))

    processed_records = []
    seen_examples = set()

    removed_empty = 0
    removed_invalid = 0
    removed_duplicates = 0

    for record in raw_records:

        question = record.get("question", "")
        code = record.get("code", "")

        if not isinstance(question, str) or not isinstance(code, str):
            removed_empty += 1
            continue

        question = question.strip()
        code = clean_code(code)

        if not question or not code:
            removed_empty += 1
            continue

        if not is_valid_python(code):
            removed_invalid += 1
            continue

        unique_key = (
            " ".join(question.lower().split()),
            code
        )

        if unique_key in seen_examples:
            removed_duplicates += 1
            continue

        seen_examples.add(unique_key)

        processed_records.append({
            "question": question,
            "code": code,
            "language": "Python",
            "source": "StaQC"
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            processed_records,
            file,
            indent=2,
            ensure_ascii=False
        )

    print("\n" + "=" * 55)
    print("PREPROCESSING SUMMARY")
    print("=" * 55)

    print("Original records:", len(raw_records))
    print("Removed empty records:", removed_empty)
    print("Removed invalid/non-Python code:", removed_invalid)
    print("Removed duplicates:", removed_duplicates)
    print("Clean records:", len(processed_records))

    print("\nSaved file:", OUTPUT_FILE)

    if processed_records:
        print("\nFirst cleaned example:")
        print("Question:", processed_records[0]["question"])
        print("Code:")
        print(processed_records[0]["code"][:500])
        print("\nPreprocessing completed.")
    else:
        print("\nWARNING: No valid Python records were found.")
        print("We must inspect the dataset before proceeding.")


if __name__ == "__main__":
    preprocess_dataset()
