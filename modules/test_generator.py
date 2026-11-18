
import ast
import re
import requests

from modules.sandbox import execute_tests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:1.5b"


# --------------------------------------------------
# 1. Extract Python code from Ollama response
# --------------------------------------------------

def extract_python_code(response):
    """Extract Python code from an LLM response."""

    matches = re.findall(
        r"```(?:python)?\s*(.*?)```",
        response,
        flags=re.DOTALL | re.IGNORECASE
    )

    if matches:
        return matches[0].strip()

    return response.strip()


# --------------------------------------------------
# 2. Clean and validate generated tests
# --------------------------------------------------

def clean_test_code(test_code):
    """Keep imports and unique pytest test functions."""

    try:
        tree = ast.parse(test_code)

    except SyntaxError as error:
        return None, f"Invalid Python syntax: {error}"

    allowed_nodes = []
    seen_test_names = set()

    for node in tree.body:

        if isinstance(node, (ast.Import, ast.ImportFrom)):
            allowed_nodes.append(node)

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):

            if not node.name.startswith("test_"):
                continue

            if node.name in seen_test_names:
                print(f"Skipping duplicate test: {node.name}")
                continue

            # Validate pytest.mark.parametrize decorators.
            invalid_parametrize = False

            for decorator in node.decorator_list:

                if not isinstance(decorator, ast.Call):
                    continue

                func = decorator.func

                if not (
                    isinstance(func, ast.Attribute)
                    and func.attr == "parametrize"
                ):
                    continue

                if len(decorator.args) < 2:
                    invalid_parametrize = True
                    break

                try:
                    parameter_names = ast.literal_eval(
                        decorator.args[0]
                    )

                    parameter_values = ast.literal_eval(
                        decorator.args[1]
                    )

                    if isinstance(parameter_names, str):
                        names = [
                            name.strip()
                            for name in parameter_names.split(",")
                        ]
                    else:
                        names = list(parameter_names)

                    if not isinstance(parameter_values, (list, tuple)):
                        invalid_parametrize = True
                        break

                    for values in parameter_values:

                        if not isinstance(values, (list, tuple)):
                            invalid_parametrize = True
                            break

                        if len(values) != len(names):
                            invalid_parametrize = True
                            break

                except (ValueError, TypeError):
                    invalid_parametrize = True

                if invalid_parametrize:
                    break

            if invalid_parametrize:
                print(f"Skipping malformed test: {node.name}")
                continue

            allowed_nodes.append(node)
            seen_test_names.add(node.name)

    if not seen_test_names:
        return None, "No valid test functions were found."

    cleaned_tree = ast.Module(
        body=allowed_nodes,
        type_ignores=[]
    )

    # Add pytest import automatically when needed.
    uses_pytest = any(
        isinstance(node, ast.Name) and node.id == "pytest"
        for node in ast.walk(cleaned_tree)
    )

    has_pytest_import = any(
        isinstance(node, ast.Import)
        and any(alias.name == "pytest" for alias in node.names)
        for node in cleaned_tree.body
    )

    if uses_pytest and not has_pytest_import:
        cleaned_tree.body.insert(
            0,
            ast.Import(names=[ast.alias(name="pytest")])
        )

    return ast.unparse(cleaned_tree), None


# --------------------------------------------------
# 3. Safe evaluation of literal arithmetic
# --------------------------------------------------

def safe_literal_eval(node):
    """Evaluate basic literal arithmetic without using eval()."""

    if isinstance(node, ast.Constant):

        if isinstance(
            node.value,
            (int, float, complex, bool, str)
        ):
            return node.value

        raise ValueError("Unsupported constant")

    if isinstance(node, ast.UnaryOp):

        value = safe_literal_eval(node.operand)

        if isinstance(node.op, ast.USub):
            return -value

        if isinstance(node.op, ast.UAdd):
            return +value

        raise ValueError("Unsupported unary operator")

    if isinstance(node, ast.BinOp):

        left = safe_literal_eval(node.left)
        right = safe_literal_eval(node.right)

        if isinstance(node.op, ast.Add):
            return left + right

        if isinstance(node.op, ast.Sub):
            return left - right

        if isinstance(node.op, ast.Mult):
            return left * right

        if isinstance(node.op, ast.Div):
            return left / right

        if isinstance(node.op, ast.FloorDiv):
            return left // right

        if isinstance(node.op, ast.Mod):
            return left % right

        if isinstance(node.op, ast.Pow):

            if not isinstance(right, (int, float)):
                raise ValueError("Invalid exponent")

            if abs(right) > 1000:
                raise ValueError("Exponent too large")

            return left ** right

        raise ValueError("Unsupported binary operator")

    raise ValueError("Unsupported expression")


# --------------------------------------------------
# 4. Correct simple addition assertions
# --------------------------------------------------

def correct_simple_addition_assertions(original_code, test_code):
    """
    Correct expected values for functions whose complete body
    consists of a direct return of two parameters added together.

    Supports integer, float and string literal arguments.
    """

    try:
        original_tree = ast.parse(original_code)
        test_tree = ast.parse(test_code)

    except SyntaxError:
        return test_code

    addition_functions = {}

    # Identify simple functions that directly return a + b.
    for node in original_tree.body:

        if not isinstance(node, ast.FunctionDef):
            continue

        if len(node.body) != 1:
            continue

        statement = node.body[0]

        if not isinstance(statement, ast.Return):
            continue

        expression = statement.value

        if not isinstance(expression, ast.BinOp):
            continue

        if not isinstance(expression.op, ast.Add):
            continue

        if not (
            isinstance(expression.left, ast.Name)
            and isinstance(expression.right, ast.Name)
        ):
            continue

        addition_functions[node.name] = True

    corrected_count = 0

    for node in ast.walk(test_tree):

        if not isinstance(node, ast.Assert):
            continue

        comparison = node.test

        if not isinstance(comparison, ast.Compare):
            continue

        if (
            len(comparison.ops) != 1
            or not isinstance(comparison.ops[0], ast.Eq)
            or len(comparison.comparators) != 1
        ):
            continue

        call = comparison.left

        if not isinstance(call, ast.Call):
            continue

        if not isinstance(call.func, ast.Name):
            continue

        if call.func.id not in addition_functions:
            continue

        if len(call.args) != 2 or call.keywords:
            continue

        try:
            first = safe_literal_eval(call.args[0])
            second = safe_literal_eval(call.args[1])

            expected = first + second

        except (
            ValueError,
            TypeError,
            ArithmeticError,
            OverflowError
        ):
            # Incompatible types should be tested using pytest.raises.
            continue

        expected_node = comparison.comparators[0]

        # Support pytest.approx(expected).
        if (
            isinstance(expected_node, ast.Call)
            and isinstance(expected_node.func, ast.Attribute)
            and expected_node.func.attr == "approx"
            and len(expected_node.args) >= 1
        ):
            expected_node = expected_node.args[0]

        try:
            generated_expected = safe_literal_eval(expected_node)

        except (
            ValueError,
            TypeError,
            ArithmeticError,
            OverflowError
        ):
            continue

        if generated_expected != expected:

            comparison.comparators[0] = ast.Constant(
                value=expected
            )

            corrected_count += 1

    if corrected_count:
        print(
            f"Corrected {corrected_count} simple addition assertion(s)."
        )

    return ast.unparse(test_tree)


# --------------------------------------------------
# 5. Generate tests using Ollama
# --------------------------------------------------

def generate_tests(code):

    prompt = f"""
You are an expert Python software tester.

Generate pytest test cases for the following Python code.

IMPORTANT:
Understand the actual behavior of the original Python code.
Do not assume that the function performs conversions or validations
that are not present in its implementation.

Rules:

1. Do not redefine original functions.
2. Do not create helper functions or classes.
3. Create separate test functions for different test cases.
4. Every test function must start with test_.
5. Include import pytest whenever pytest features are used.
6. Use correct expected values.
7. Use pytest.approx for floating-point comparisons.
8. Do not invent exceptions or unsupported behavior.
9. Do not assume incompatible input types will be converted automatically.
10. If an operation naturally raises an exception, test it using
    pytest.raises with the appropriate exception type.
11. For a function that directly returns a + b:
    - 1 + 2 produces 3.
    - 1.1 + 2.2 produces approximately 3.3.
    - '1' + '2' produces '12'.
    - 1 + '2' raises TypeError.
    - 1 + [2] raises TypeError.
12. Include useful edge cases consistent with the implementation.
13. Do not use malformed pytest.mark.parametrize decorators.
14. Return only Python test code inside one Python code block.

Original Python code:

{code}
"""

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            },
            timeout=180
        )

        response.raise_for_status()

        generated_response = response.json()["response"]

    except requests.exceptions.RequestException as error:
        return None, f"Ollama request failed: {error}"

    except (KeyError, ValueError) as error:
        return None, f"Invalid Ollama response: {error}"

    raw_code = extract_python_code(generated_response)

    cleaned_code, error = clean_test_code(raw_code)

    if cleaned_code is None:
        return None, error

    return cleaned_code, None


# --------------------------------------------------
# 6. Execute generated tests INSIDE DOCKER
# --------------------------------------------------

def run_generated_tests(original_code, test_code):

    try:

        # Validate original source syntax.
        ast.parse(original_code)

        cleaned_tests, error = clean_test_code(test_code)

        if cleaned_tests is None:
            return {
                "success": False,
                "output": "",
                "error": error,
                "return_code": None
            }

        # Correct incorrect expected values for simple addition.
        cleaned_tests = correct_simple_addition_assertions(
            original_code,
            cleaned_tests
        )

        # Execute generated tests inside Docker only.
        result = execute_tests(
            original_code,
            cleaned_tests,
            timeout=30
        )

        return result

    except SyntaxError as error:

        return {
            "success": False,
            "output": "",
            "error": f"Invalid Python syntax: {error}",
            "return_code": None
        }

    except Exception as error:

        return {
            "success": False,
            "output": "",
            "error": str(error),
            "return_code": None
        }


# --------------------------------------------------
# 7. Repair failed tests using Ollama
# --------------------------------------------------

def repair_failed_tests(original_code, test_code, failure_output):

    prompt = f"""
You are an expert Python pytest test-repair assistant.

The following generated tests failed.

ORIGINAL PYTHON CODE:

{original_code}

PREVIOUS TEST CASES:

{test_code}

PYTEST FAILURE OUTPUT:

{failure_output}

Repair the test cases so that they correctly test the actual
behavior of the original Python code.

Rules:

1. Read the original function carefully.
2. Do not redefine original functions.
3. Do not create helper functions or classes.
4. Preserve tests that are already correct.
5. Fix only incorrect test assumptions.
6. Do not invent functionality.
7. Do not assume automatic type conversion.
8. If an operation naturally raises TypeError, use pytest.raises(TypeError).
9. For example, if the function directly returns a + b:
   - add_numbers('1', '2') returns '12'.
   - add_numbers(1, '2') raises TypeError.
10. Use pytest.approx for floating-point comparisons.
11. Include import pytest whenever pytest is used.
12. Every test function must start with test_.
13. Do not use malformed pytest.mark.parametrize decorators.
14. Return only the complete repaired pytest code inside one Python
    code block.
"""

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            },
            timeout=180
        )

        response.raise_for_status()

        raw_code = extract_python_code(
            response.json()["response"]
        )

        cleaned_code, error = clean_test_code(raw_code)

        if cleaned_code is None:
            return None, error

        return cleaned_code, None

    except requests.exceptions.RequestException as error:

        return None, f"Ollama repair request failed: {error}"

    except (KeyError, ValueError) as error:

        return None, f"Invalid Ollama repair response: {error}"


# --------------------------------------------------
# 8. Main test generation workflow
# --------------------------------------------------

def generate_and_run_tests(code):

    print("\nGenerating test cases...")

    # Step 1: Generate tests.
    test_code, error = generate_tests(code)

    if test_code is None:

        print("\nCould not generate valid tests.")
        print("Reason:", error)

        return None

    print("\nGenerated Test Cases:")
    print(test_code)

    # Step 2: Run initial tests.
    print("\nRunning generated tests inside Docker...")

    result = run_generated_tests(code, test_code)

    if result["success"]:

        print("\nAll generated tests passed!")
        print(result["output"])

        return result

    print(
        "\nSome generated tests failed or Docker execution "
        "was unsuccessful."
    )

    print(result.get("output", ""))

    if result.get("error"):
        print(result["error"])

    # Step 3: Ask Ollama to repair failed tests.
    print("\nAsking Ollama to repair the tests...")

    failure_details = (
        (result.get("output") or "")
        + "\n"
        + (result.get("error") or "")
    )

    repaired_code, error = repair_failed_tests(
        code,
        test_code,
        failure_details
    )

    if repaired_code is None:

        print("\nCould not repair tests.")
        print("Reason:", error)

        return result

    print("\nRepaired Test Cases:")
    print(repaired_code)

    # Step 4: Run repaired tests inside Docker.
    print("\nRunning repaired tests inside Docker...")

    retry_result = run_generated_tests(
        code,
        repaired_code
    )

    if retry_result["success"]:
        print("\nAll repaired tests passed!")

    else:
        print(
            "\nSome repaired tests still failed or Docker "
            "execution was unsuccessful."
        )

    print(retry_result.get("output", ""))

    if retry_result.get("error"):
        print(retry_result["error"])

    return retry_result


# --------------------------------------------------
# 9. Standalone testing
# --------------------------------------------------

if __name__ == "__main__":

    sample_code = """
def add_numbers(a, b):
    return a + b
"""

    print("=" * 50)
    print("CODEMENTOR AI TEST GENERATOR")
    print("=" * 50)

    print("\nOriginal Python Code:")
    print(sample_code)

    generate_and_run_tests(sample_code)
