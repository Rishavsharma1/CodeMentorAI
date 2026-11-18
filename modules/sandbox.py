
import subprocess
import tempfile
import os
import uuid


TEST_IMAGE = "codementor-test:latest"
CODE_IMAGE = "python:3.12-slim"


def _run_docker(command, container_name, timeout):
    """Run Docker with timeout handling and return a standard result."""

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
            "return_code": result.returncode
        }

    except subprocess.TimeoutExpired:
        try:
            subprocess.run(
                ["docker", "stop", "--time", "1", container_name],
                capture_output=True,
                text=True,
                timeout=5
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            try:
                subprocess.run(
                    ["docker", "kill", container_name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        return {
            "success": False,
            "output": "",
            "error": f"Execution timed out after {timeout} seconds.",
            "return_code": None
        }

    except FileNotFoundError:
        return {
            "success": False,
            "output": "",
            "error": "Docker command not found.",
            "return_code": None
        }

    except Exception as error:
        return {
            "success": False,
            "output": "",
            "error": str(error),
            "return_code": None
        }


def _docker_command(temp_dir, container_name, image, script_path):
    """Build a restricted Docker command."""

    return [
        "docker",
        "run",
        "--name", container_name,
        "--rm",
        "--network", "none",
        "--memory", "128m",
        "--cpus", "0.5",
        "--pids-limit", "64",
        "--read-only",
        "--tmpfs", "/tmp:rw,nosuid,size=32m",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--user", "65534:65534",
        "--mount",
        f"type=bind,source={temp_dir},target=/app,readonly",
        "--workdir", "/app",
        image,
        *script_path
    ]


def execute_code(code, timeout=5):
    """
    Execute submitted Python code inside a restricted Docker container.
    """

    container_name = f"codementor-sandbox-{uuid.uuid4().hex[:12]}"

    with tempfile.TemporaryDirectory() as temp_dir:

        code_file = os.path.join(temp_dir, "main.py")

        with open(code_file, "w", encoding="utf-8") as file:
            file.write(code)

        command = _docker_command(
            temp_dir,
            container_name,
            CODE_IMAGE,
            ["python", "-I", "/app/main.py"]
        )

        return _run_docker(command, container_name, timeout)


def execute_tests(original_code, test_code, timeout=30):
    """
    Execute original Python code and generated pytest tests
    inside the restricted Docker test image.
    """

    container_name = f"codementor-tests-{uuid.uuid4().hex[:12]}"

    with tempfile.TemporaryDirectory() as temp_dir:

        test_file = os.path.join(temp_dir, "test_generated.py")

        combined_code = (
            original_code.rstrip()
            + "\n\n"
            + test_code.lstrip()
            + "\n"
        )

        with open(test_file, "w", encoding="utf-8") as file:
            file.write(combined_code)

        command = _docker_command(
            temp_dir,
            container_name,
            TEST_IMAGE,
            [
                "python",
                "-I",
                "-m",
                "pytest",
                "-v",
                "--tb=short",
                "-p",
                "no:cacheprovider",
                "/app/test_generated.py"
            ]
        )

        return _run_docker(command, container_name, timeout)


if __name__ == "__main__":

    sample_code = """
def add_numbers(a, b):
    return a + b
"""

    sample_tests = """
def test_add_numbers():
    assert add_numbers(2, 3) == 5
    assert add_numbers(-2, 2) == 0
"""

    print("Testing Docker code execution...")
    print(execute_code('print("Docker sandbox working!")'))

    print("\nTesting Docker pytest execution...")
    print(execute_tests(sample_code, sample_tests))
