
import ast
import csv
import json
import os
import sys
import time
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from modules.retriever import CodeRetriever
from modules.sandbox import execute_code
from modules.llm import generate_code_only


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

EVALUATION_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_TEST_CASES_FILE = os.path.join(
    EVALUATION_DIR, "test_cases.json"
)


def get_benchmark_path():

    if len(sys.argv) > 2:
        raise ValueError(
            "Usage: python -m evaluation.evaluate [benchmark.json]"
        )

    if len(sys.argv) == 2:
        benchmark_path = sys.argv[1]

        if not os.path.isabs(benchmark_path):
            benchmark_path = os.path.join(
                PROJECT_ROOT, benchmark_path
            )
    else:
        benchmark_path = DEFAULT_TEST_CASES_FILE

    benchmark_path = os.path.abspath(benchmark_path)

    if not os.path.isfile(benchmark_path):
        raise FileNotFoundError(
            f"Benchmark file not found: {benchmark_path}"
        )

    return benchmark_path


def get_report_paths(benchmark_path):

    benchmark_name = os.path.splitext(
        os.path.basename(benchmark_path)
    )[0]

    if benchmark_name == "test_cases":
        results_file = os.path.join(
            EVALUATION_DIR, "results.csv"
        )
        generated_code_file = os.path.join(
            EVALUATION_DIR, "generated_code.json"
        )
    else:
        results_file = os.path.join(
            EVALUATION_DIR,
            f"results_{benchmark_name}.csv"
        )
        generated_code_file = os.path.join(
            EVALUATION_DIR,
            f"generated_code_{benchmark_name}.json"
        )

    return results_file, generated_code_file


# --------------------------------------------------
# 1. LOAD AND VALIDATE BENCHMARK CASES
# --------------------------------------------------

def load_test_cases(test_cases_file):

    with open(test_cases_file, "r", encoding="utf-8") as file:
        cases = json.load(file)

    if not isinstance(cases, list) or not cases:
        raise ValueError(
            "Benchmark file must contain a non-empty JSON list."
        )

    return cases


def validate_benchmark_cases(cases):

    required_fields = [
        "id",
        "question",
        "function_name",
        "code",
        "tests",
        "relevant_keywords",
    ]

    for case in cases:

        for field in required_fields:
            if field not in case:
                raise ValueError(
                    f"Case {case.get('id', '?')} "
                    f"is missing field: {field}"
                )

        if (
            not isinstance(case["function_name"], str)
            or not case["function_name"].isidentifier()
        ):
            raise ValueError(
                f"Case {case['id']} has an invalid function name."
            )

        ast.parse(case["code"])

        if not isinstance(case["tests"], list) or not case["tests"]:
            raise ValueError(
                f"Case {case['id']} has no tests."
            )

        if not isinstance(case["relevant_keywords"], list):
            raise ValueError(
                f"Case {case['id']} has invalid keywords."
            )


# --------------------------------------------------
# 2. REFERENCE CODE EVALUATION
# --------------------------------------------------

def evaluate_code_execution(cases):

    results = []

    for case in cases:

        print(f"\nReference test: {case['function_name']}")

        complete_code = (
            case["code"] + "\n\n" + "\n".join(case["tests"])
        )

        start_time = time.perf_counter()

        try:
            result = execute_code(complete_code, timeout=10)

            elapsed = time.perf_counter() - start_time
            passed = bool(result.get("success", False))

            results.append({
                "case_id": case["id"],
                "function_name": case["function_name"],
                "code_test_passed": passed,
                "execution_time_seconds": round(elapsed, 4),
                "execution_error": result.get("error", ""),
            })

            print(
                "PASS" if passed else "FAIL",
                f"| Time: {elapsed:.4f}s"
            )

        except Exception as error:

            elapsed = time.perf_counter() - start_time

            results.append({
                "case_id": case["id"],
                "function_name": case["function_name"],
                "code_test_passed": False,
                "execution_time_seconds": round(elapsed, 4),
                "execution_error": str(error),
            })

            print(f"ERROR: {error}")

    return results


# --------------------------------------------------
# 3. RETRIEVAL EVALUATION
# --------------------------------------------------

def evaluate_retrieval(cases, retriever, top_k=5):

    results = []

    for case in cases:

        print(f"\nRetrieval: {case['function_name']}")

        start_time = time.perf_counter()

        try:
            retrieved = retriever.search(
                case["question"], top_k=top_k
            )

            elapsed = time.perf_counter() - start_time

            retrieved_text = " ".join(
                (
                    str(item.get("question", "")) + " "
                    + str(item.get("code", ""))
                ).lower()
                for item in retrieved
            )

            keywords = [
                str(keyword).lower()
                for keyword in case["relevant_keywords"]
            ]

            matched = [
                keyword for keyword in keywords
                if keyword in retrieved_text
            ]

            coverage = (
                len(matched) / len(keywords)
                if keywords else 0.0
            )

            results.append({
                "case_id": case["id"],
                "function_name": case["function_name"],
                "retrieved_count": len(retrieved),
                "keyword_coverage": round(coverage, 4),
                "matched_keywords": ", ".join(matched),
                "retrieval_time_seconds": round(elapsed, 4),
            })

            print(
                f"Retrieved: {len(retrieved)}"
                f" | Keyword coverage: {coverage:.2%}"
                f" | Time: {elapsed:.4f}s"
            )

        except Exception as error:

            elapsed = time.perf_counter() - start_time

            results.append({
                "case_id": case["id"],
                "function_name": case["function_name"],
                "retrieved_count": 0,
                "keyword_coverage": 0.0,
                "matched_keywords": "",
                "retrieval_time_seconds": round(elapsed, 4),
            })

            print(f"Retrieval error: {error}")

    return results


# --------------------------------------------------
# 4. GENERATE AND TEST AI CODE
# --------------------------------------------------

def evaluate_generated_code(cases, retriever, use_rag):

    mode = "RAG" if use_rag else "NO-RAG"

    results = []
    generated_codes = []

    print(f"\nStarting {mode} code generation and testing...")

    for case in cases:

        function_name = case["function_name"]

        print(f"\n{mode}: {function_name}")

        examples = []

        if use_rag:
            try:
                examples = retriever.search(
                    case["question"], top_k=3
                )
            except Exception as error:
                print(f"Retrieval failed: {error}")

        generation_start = time.perf_counter()

        try:
            generated_code = generate_code_only(
                case["question"],
                examples,
                function_name=function_name
            )

        except Exception as error:
            generated_code = f"Error: {error}"

        generation_time = (
            time.perf_counter() - generation_start
        )

        syntax_valid = False
        execution_passed = False
        execution_error = ""

        if (
            not generated_code
            or generated_code.startswith("Error:")
        ):
            execution_error = (
                generated_code or "Empty generated code."
            )

        else:
            try:
                ast.parse(generated_code)
                syntax_valid = True

            except SyntaxError as error:
                execution_error = (
                    f"Syntax error on line {error.lineno}: "
                    f"{error.msg}"
                )

        if syntax_valid:

            complete_code = (
                generated_code
                + "\n\n"
                + "\n".join(case["tests"])
            )

            try:
                result = execute_code(
                    complete_code, timeout=10
                )

                execution_passed = bool(
                    result.get("success", False)
                )

                if not execution_passed:
                    execution_error = result.get(
                        "error", "Generated code failed tests."
                    )

            except Exception as error:
                execution_error = str(error)

        result_record = {
            "case_id": case["id"],
            "function_name": function_name,
            "mode": mode,
            "syntax_valid": syntax_valid,
            "tests_passed": execution_passed,
            "generation_time_seconds": round(
                generation_time, 4
            ),
            "execution_error": execution_error,
        }

        results.append(result_record)

        generated_codes.append({
            "case_id": case["id"],
            "function_name": function_name,
            "mode": mode,
            "generated_code": generated_code,
            "retrieved_examples_count": len(examples),
        })

        print(f"Syntax valid: {syntax_valid}")
        print(f"Tests passed: {execution_passed}")
        print(f"Generation time: {generation_time:.2f}s")

        if execution_error:
            print(f"Error: {execution_error}")

    return results, generated_codes


# --------------------------------------------------
# 5. SAVE GENERATED CODE
# --------------------------------------------------

def save_generated_codes(generated_codes, generated_code_file):

    with open(
        generated_code_file, "w", encoding="utf-8"
    ) as file:

        json.dump(
            generated_codes,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"\nGenerated code saved to: {generated_code_file}"
    )


# --------------------------------------------------
# 6. SAVE CSV RESULTS
# --------------------------------------------------

def save_results(
    reference_results,
    retrieval_results,
    no_rag_results,
    rag_results,
    results_file
):

    retrieval_by_id = {
        str(item["case_id"]): item
        for item in retrieval_results
    }

    no_rag_by_id = {
        str(item["case_id"]): item
        for item in no_rag_results
    }

    rag_by_id = {
        str(item["case_id"]): item
        for item in rag_results
    }

    columns = [
        "evaluation_date",
        "case_id",
        "function_name",
        "reference_passed",
        "retrieved_count",
        "keyword_coverage",
        "retrieval_time_seconds",
        "no_rag_syntax_valid",
        "no_rag_tests_passed",
        "no_rag_generation_time",
        "no_rag_error",
        "rag_syntax_valid",
        "rag_tests_passed",
        "rag_generation_time",
        "rag_error",
    ]

    with open(
        results_file, "w", newline="", encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file, fieldnames=columns
        )

        writer.writeheader()

        for reference in reference_results:

            case_id = str(reference["case_id"])

            retrieval = retrieval_by_id.get(case_id, {})
            no_rag = no_rag_by_id.get(case_id, {})
            rag = rag_by_id.get(case_id, {})

            writer.writerow({
                "evaluation_date": datetime.now().isoformat(
                    timespec="seconds"
                ),
                "case_id": reference["case_id"],
                "function_name": reference["function_name"],
                "reference_passed": reference["code_test_passed"],
                "retrieved_count": retrieval.get(
                    "retrieved_count", 0
                ),
                "keyword_coverage": retrieval.get(
                    "keyword_coverage", 0
                ),
                "retrieval_time_seconds": retrieval.get(
                    "retrieval_time_seconds", 0
                ),
                "no_rag_syntax_valid": no_rag.get(
                    "syntax_valid", False
                ),
                "no_rag_tests_passed": no_rag.get(
                    "tests_passed", False
                ),
                "no_rag_generation_time": no_rag.get(
                    "generation_time_seconds", 0
                ),
                "no_rag_error": no_rag.get(
                    "execution_error", ""
                ),
                "rag_syntax_valid": rag.get(
                    "syntax_valid", False
                ),
                "rag_tests_passed": rag.get(
                    "tests_passed", False
                ),
                "rag_generation_time": rag.get(
                    "generation_time_seconds", 0
                ),
                "rag_error": rag.get(
                    "execution_error", ""
                ),
            })

    print(f"\nCSV results saved to: {results_file}")


# --------------------------------------------------
# 7. PRINT FINAL SUMMARY
# --------------------------------------------------

def print_summary(
    reference_results,
    retrieval_results,
    no_rag_results,
    rag_results,
    results_file,
    generated_code_file
):

    total = len(reference_results)

    reference_passed = sum(
        item["code_test_passed"]
        for item in reference_results
    )

    no_rag_passed = sum(
        item["tests_passed"]
        for item in no_rag_results
    )

    rag_passed = sum(
        item["tests_passed"]
        for item in rag_results
    )

    average_coverage = (
        sum(
            item["keyword_coverage"]
            for item in retrieval_results
        ) / len(retrieval_results)
        if retrieval_results else 0.0
    )

    no_rag_rate = no_rag_passed / total if total else 0.0
    rag_rate = rag_passed / total if total else 0.0

    print("\n" + "=" * 60)
    print("CODEMENTOR AI - FINAL EVALUATION")
    print("=" * 60)

    print(f"Benchmark cases: {total}")
    print(
        f"Reference implementations passed: "
        f"{reference_passed}/{total}"
    )

    print(
        f"\nAverage retrieval keyword coverage: "
        f"{average_coverage:.2%}"
    )

    print("\nNO-RAG RESULTS")
    print(f"Tests passed: {no_rag_passed}/{total}")
    print(f"Pass rate: {no_rag_rate:.2%}")

    print("\nRAG RESULTS")
    print(f"Tests passed: {rag_passed}/{total}")
    print(f"Pass rate: {rag_rate:.2%}")

    print("\nRAG improvement over No-RAG:")
    print(
        f"{(rag_rate - no_rag_rate) * 100:+.2f} "
        "percentage points"
    )

    print("\nReports:")
    print(results_file)
    print(generated_code_file)

    print("=" * 60)


# --------------------------------------------------
# 8. MAIN
# --------------------------------------------------

def main():

    print("=" * 60)
    print("CODEMENTOR AI - RAG VS NO-RAG EVALUATION")
    print("=" * 60)

    benchmark_path = get_benchmark_path()

    results_file, generated_code_file = get_report_paths(
        benchmark_path
    )

    cases = load_test_cases(benchmark_path)

    validate_benchmark_cases(cases)

    print(f"\nBenchmark file: {benchmark_path}")
    print(f"Loaded {len(cases)} benchmark cases.")

    print("Reference benchmark syntax validation passed.")

    print("\nInitializing FAISS retriever...")

    retriever = CodeRetriever()

    print("\nSTEP 1: Reference code evaluation")
    reference_results = evaluate_code_execution(cases)

    print("\nSTEP 2: Retrieval evaluation")
    retrieval_results = evaluate_retrieval(
        cases, retriever, top_k=5
    )

    print("\nSTEP 3: No-RAG evaluation")
    no_rag_results, no_rag_codes = evaluate_generated_code(
        cases, retriever, use_rag=False
    )

    print("\nSTEP 4: RAG evaluation")
    rag_results, rag_codes = evaluate_generated_code(
        cases, retriever, use_rag=True
    )

    save_generated_codes(
        no_rag_codes + rag_codes,
        generated_code_file
    )

    save_results(
        reference_results,
        retrieval_results,
        no_rag_results,
        rag_results,
        results_file
    )

    print_summary(
        reference_results,
        retrieval_results,
        no_rag_results,
        rag_results,
        results_file,
        generated_code_file
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"\nEvaluation stopped: {error}")
        sys.exit(1)
