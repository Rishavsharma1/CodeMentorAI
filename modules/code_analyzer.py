
import ast


def analyze_code(code):

    results = {
        "valid": True,
        "syntax_error": None,
        "issues": []
    }

    # Check Python syntax
    try:
        tree = ast.parse(code)

    except SyntaxError as error:

        results["valid"] = False

        results["syntax_error"] = {
            "message": error.msg,
            "line": error.lineno,
            "column": error.offset
        }

        return results

    # Check for common coding issues
    for node in ast.walk(tree):

        # Detect unused-looking variables is not reliable
        # without scope analysis, so we check simpler issues.

        if isinstance(node, ast.Compare):

            # Detect comparisons like: x == True
            if (
                len(node.ops) == 1
                and isinstance(node.ops[0], ast.Eq)
                and len(node.comparators) == 1
                and isinstance(node.comparators[0], ast.Constant)
                and isinstance(node.comparators[0].value, bool)
            ):

                results["issues"].append({
                    "type": "Code quality",
                    "message": "Avoid comparing directly with True or False. Use the condition itself or 'not'.",
                    "line": node.lineno
                })

        # Detect use of eval()
        if isinstance(node, ast.Call):

            if isinstance(node.func, ast.Name) and node.func.id == "eval":

                results["issues"].append({
                    "type": "Security warning",
                    "message": "Use of eval() can execute arbitrary expressions. Avoid it with untrusted input.",
                    "line": node.lineno
                })

    return results



import requests


def debug_code(code):

    print("Analyzing code...")

    analysis = analyze_code(code)

    syntax_error = analysis["syntax_error"]

    if syntax_error:
        error_details = (
            f"Syntax error: {syntax_error['message']}\n"
            f"Line: {syntax_error['line']}\n"
            f"Column: {syntax_error['column']}"
        )
    else:
        error_details = "No Python syntax errors detected."

    issues = analysis["issues"]

    issue_details = "\n".join(
        f"- {issue['type']}: {issue['message']} "
        f"(Line {issue['line']})"
        for issue in issues
    )

    if not issue_details:
        issue_details = "No common code-quality issues detected."

    prompt = f"""
You are CodeMentor AI, an expert Python debugging assistant.

Analyze the following Python code.

PYTHON CODE:
{code}

STATIC ANALYSIS:
{error_details}

ADDITIONAL ISSUES:
{issue_details}

Your tasks:
1. Explain the errors in simple language.
2. Identify the exact lines that need correction.
3. Provide corrected Python code.
4. Explain why the correction works.
5. If no errors are detected, do not invent errors.
6. Do not claim that code is logically correct just because
   it passes syntax analysis.

Format your response using these headings:

### Errors Found
### Corrected Code
### Explanation
"""

    try:

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5:1.5b",
                "prompt": prompt,
                "stream": False
            },
            timeout=180
        )

        response.raise_for_status()

        return response.json()["response"]

    except requests.exceptions.RequestException as error:

        return f"Error communicating with Ollama: {error}"





if __name__ == "__main__":

    buggy_code = """
def add_numbers(a, b)
    return a + b

result = add_numbers(10, 20)
print(result)
"""

    print("\n" + "=" * 50)
    print("CODEMENTOR AI DEBUGGER")
    print("=" * 50)

    print("\nOriginal Code:")
    print(buggy_code)

    print("\nDebugging...\n")

    result = debug_code(buggy_code)

    print("\nDebugger Response:")
    print(result)
