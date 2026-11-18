
import csv
from pathlib import Path

import matplotlib.pyplot as plt


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
EVALUATION_DIR = BASE_DIR / "evaluation"

EXPERIMENTS = [
    ("Original", "results_held_out_before_prompt.csv"),
    ("Prompt v2", "results_held_out_prompt_v2.csv"),
    ("Prompt v3", "results_held_out_prompt_v3.csv"),
    ("Prompt v4", "results_held_out_prompt_v4.csv"),
]


# --------------------------------------------------
# CALCULATE METRICS
# --------------------------------------------------

def calculate_metrics(file_path):

    with open(file_path, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    total = len(rows)

    if total == 0:
        raise ValueError(f"No evaluation records found: {file_path}")

    no_rag_passed = sum(
        row["no_rag_tests_passed"].lower() == "true"
        for row in rows
    )

    rag_passed = sum(
        row["rag_tests_passed"].lower() == "true"
        for row in rows
    )

    reference_passed = sum(
        row["reference_passed"].lower() == "true"
        for row in rows
    )

    keyword_coverage = sum(
        float(row["keyword_coverage"])
        for row in rows
    ) / total

    return {
        "total_cases": total,
        "reference_passed": reference_passed,
        "no_rag_passed": no_rag_passed,
        "rag_passed": rag_passed,
        "no_rag_accuracy": round(no_rag_passed / total * 100, 2),
        "rag_accuracy": round(rag_passed / total * 100, 2),
        "improvement_pp": round(
            (rag_passed - no_rag_passed) / total * 100, 2
        ),
        "keyword_coverage": round(keyword_coverage * 100, 2),
    }


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    results = []

    print("=" * 65)
    print("CODEMENTOR AI - RAG VS NO-RAG COMPARISON")
    print("=" * 65)

    for experiment, filename in EXPERIMENTS:

        file_path = EVALUATION_DIR / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"Missing evaluation file: {file_path}"
            )

        metrics = calculate_metrics(file_path)

        metrics["experiment"] = experiment

        results.append(metrics)

        print(f"\n{experiment}")
        print("-" * 40)
        print(f"No-RAG accuracy: {metrics['no_rag_accuracy']}%")
        print(f"RAG accuracy: {metrics['rag_accuracy']}%")
        print(f"Improvement: {metrics['improvement_pp']} percentage points")
        print(f"Keyword coverage: {metrics['keyword_coverage']}%")


    # --------------------------------------------------
    # SAVE CONSOLIDATED CSV
    # --------------------------------------------------

    output_csv = EVALUATION_DIR / "consolidated_comparison.csv"

    fieldnames = [
        "experiment",
        "total_cases",
        "reference_passed",
        "no_rag_passed",
        "rag_passed",
        "no_rag_accuracy",
        "rag_accuracy",
        "improvement_pp",
        "keyword_coverage",
    ]

    with open(output_csv, "w", newline="", encoding="utf-8") as file:

        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()

        writer.writerows(results)

    print(f"\nCSV report saved: {output_csv}")


    # --------------------------------------------------
    # GENERATE ACCURACY CHART
    # --------------------------------------------------

    labels = [item["experiment"] for item in results]

    no_rag_values = [
        item["no_rag_accuracy"] for item in results
    ]

    rag_values = [
        item["rag_accuracy"] for item in results
    ]

    x = list(range(len(labels)))
    width = 0.35

    plt.figure(figsize=(10, 6))

    plt.bar(
        [i - width / 2 for i in x],
        no_rag_values,
        width,
        label="No-RAG"
    )

    plt.bar(
        [i + width / 2 for i in x],
        rag_values,
        width,
        label="RAG"
    )

    plt.xlabel("Prompt Version")
    plt.ylabel("Accuracy (%)")
    plt.title("CodeMentor AI - RAG vs No-RAG Accuracy")

    plt.xticks(x, labels)
    plt.ylim(0, 110)

    plt.legend()
    plt.grid(axis="y", alpha=0.3)

    plt.tight_layout()

    chart_path = EVALUATION_DIR / "rag_vs_no_rag_comparison.png"

    plt.savefig(chart_path, dpi=300)

    plt.close()

    print(f"Accuracy chart saved: {chart_path}")

    print("\nComparison completed successfully!")


if __name__ == "__main__":
    main()
