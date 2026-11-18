
from datetime import datetime
import json
from pathlib import Path

from modules.sandbox import execute_tests


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

GENERATED_PATH = (
    BASE_DIR / "evaluation" / "generated_code_held_out_prompt_v4.json"
)

BENCHMARK_PATH = (
    BASE_DIR / "evaluation" / "held_out_test_cases.json"
)

REPORT_PATH = (
    BASE_DIR / "evaluation" / "verification_saved_rag_prompt_v4.txt"
)


# --------------------------------------------------
# MAIN VERIFICATION
# --------------------------------------------------

def main():

    with open(GENERATED_PATH, encoding="utf-8") as file:
        generated_records = json.load(file)

    with open(BENCHMARK_PATH, encoding="utf-8") as file:
        test_cases = json.load(file)

    # Keep only saved RAG-generated solutions.
    rag_records = {
        item["case_id"]: item
        for item in generated_records
        if item["mode"] == "RAG"
    }

    passed = 0
    failed = 0

    report_lines = []

    print("=" * 60)
    print("INDEPENDENT VERIFICATION - SAVED PROMPT V4 RAG")
    print("=" * 60)

    # --------------------------------------------------
    # VERIFY EACH BENCHMARK CASE
    # --------------------------------------------------

    for case in test_cases:

        case_id = case["id"]
        function_name = case["function_name"]

        print(f"\nCase {case_id}: {function_name}")
        print("-" * 50)

        record = rag_records.get(case_id)

        if not record:

            print("FAILED: Saved RAG code not found.")

            failed += 1

            report_lines.append(
                f"Case {case_id} - {function_name}: FAILED "
                "(Saved RAG code not found)"
            )

            continue

        generated_code = record["generated_code"]

        # Wrap plain assertions inside a pytest test function.
        assertions = "\n".join(
            "    " + assertion
            for assertion in case["tests"]
        )

        test_code = (
            "def test_generated_solution():\n"
            + assertions
            + "\n"
        )

        # Execute generated code inside Docker sandbox.
        result = execute_tests(
            generated_code,
            test_code,
            timeout=30
        )

        if result.get("success"):

            print("PASSED")
            passed += 1

            case_status = "PASSED"

        else:

            print("FAILED")
            failed += 1

            case_status = "FAILED"

        report_lines.append(
            f"Case {case_id} - {function_name}: {case_status}"
        )

        if result.get("output"):
            print(result["output"])

        if result.get("error"):
            print("Error:", result["error"])

    # --------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------

    summary = [
        "",
        "=" * 60,
        "FINAL INDEPENDENT VERIFICATION",
        "=" * 60,
        f"Total cases: {len(test_cases)}",
        f"Passed: {passed}",
        f"Failed: {failed}",
        (
            "All saved RAG solutions passed!"
            if failed == 0
            else "Some saved RAG solutions need investigation."
        )
    ]

    print("\n".join(summary))

    # --------------------------------------------------
    # SAVE VERIFICATION REPORT
    # --------------------------------------------------

    report_content = [
        "CODEMENTOR AI - INDEPENDENT RAG VERIFICATION",
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "Benchmark: held_out_test_cases.json",
        "Generated code: generated_code_held_out_prompt_v4.json",
        "Execution: Docker sandbox",
        "",
        "INDIVIDUAL CASE RESULTS",
        "-" * 40,
        *report_lines,
        *summary
    ]

    REPORT_PATH.write_text(
        "\n".join(report_content),
        encoding="utf-8"
    )

    print(f"\nReport saved to: {REPORT_PATH}")


# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    main()
