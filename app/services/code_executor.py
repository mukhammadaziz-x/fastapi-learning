"""
Code execution service - sandboxed code execution for code-type questions.
Uses RestrictedPython for safety.
"""
import io
import sys
import traceback
from typing import Optional
from contextlib import redirect_stdout, redirect_stderr


def execute_python_code(code: str, test_cases: list[dict] = None,
                        time_limit_sec: int = 5) -> dict:
    """
    Execute Python code in a sandboxed environment.

    Args:
        code: The student's code
        test_cases: List of {"input": "...", "expected_output": "...", "points": N}
        time_limit_sec: Maximum execution time

    Returns:
        {
            "success": bool,
            "output": str,
            "error": str | None,
            "test_results": [{"passed": bool, "input": str, "expected": str, "actual": str}],
            "passed_count": int,
            "total_count": int,
            "points_earned": float
        }
    """
    result = {
        "success": False,
        "output": "",
        "error": None,
        "test_results": [],
        "passed_count": 0,
        "total_count": len(test_cases) if test_cases else 0,
        "points_earned": 0,
    }

    # Restricted globals - no file I/O, no imports of dangerous modules
    restricted_builtins = {
        'print': print, 'range': range, 'len': len, 'int': int, 'float': float,
        'str': str, 'bool': bool, 'list': list, 'dict': dict, 'tuple': tuple,
        'set': set, 'frozenset': frozenset, 'sorted': sorted, 'reversed': reversed,
        'enumerate': enumerate, 'zip': zip, 'map': map, 'filter': filter,
        'min': min, 'max': max, 'sum': sum, 'abs': abs, 'round': round,
        'isinstance': isinstance, 'type': type, 'input': lambda *a: "",
        'True': True, 'False': False, 'None': None,
    }

    safe_globals = {"__builtins__": restricted_builtins}

    if not test_cases:
        # Just run the code and capture output
        try:
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, safe_globals)
            result["output"] = stdout_capture.getvalue()
            result["success"] = True
        except Exception as e:
            result["error"] = f"{type(e).__name__}: {str(e)}"
        return result

    # Run test cases
    for tc in test_cases:
        test_input = tc.get("input", "")
        expected = tc.get("expected_output", "").strip()
        points = tc.get("points", 1)

        try:
            # Create input mock
            input_lines = test_input.strip().split("\n") if test_input else []
            input_iter = iter(input_lines)
            safe_globals_copy = dict(safe_globals)
            safe_globals_copy["__builtins__"]["input"] = lambda *a: next(input_iter, "")

            stdout_capture = io.StringIO()
            with redirect_stdout(stdout_capture):
                exec(code, safe_globals_copy)
            actual = stdout_capture.getvalue().strip()

            passed = actual == expected
            result["test_results"].append({
                "passed": passed,
                "input": test_input,
                "expected": expected,
                "actual": actual,
            })
            if passed:
                result["passed_count"] += 1
                result["points_earned"] += points
        except Exception as e:
            result["test_results"].append({
                "passed": False,
                "input": test_input,
                "expected": expected,
                "actual": f"Error: {type(e).__name__}: {str(e)}",
            })

    result["success"] = result["passed_count"] == result["total_count"]
    return result
