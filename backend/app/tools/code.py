import os
import subprocess
import tempfile
import sys
from pathlib import Path
from typing import Any, Dict

from app.core.config import WORKSPACE_DIR
from app.tools.utils import safe_eval, _check_code_safety, _check_command_safety


def run_code(code: str, **kwargs) -> str:
    warning = _check_code_safety(code)
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, dir=WORKSPACE_DIR) as f:
            f.write(code)
            temp_path = f.name
        result = subprocess.run(
            ["python", temp_path],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=WORKSPACE_DIR
        )
        os.unlink(temp_path)
        output = result.stdout
        if result.stderr:
            output += "\nSTDERR:\n" + result.stderr
        if not output.strip():
            output = "Code executed successfully (no output)."
        if warning:
            output = f"[SAFETY] {warning}\n\n{output}"
        return output[:5000]
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out (30s limit)"
    except Exception as e:
        return f"Error running code: {str(e)}"


def run_command(command: str, working_directory: str = "", timeout: int = 60, **kwargs) -> str:
    warning = _check_command_safety(command)
    timeout = min(timeout, 120)
    try:
        is_windows = sys.platform == "win32"
        if is_windows:
            shell_cmd = ["cmd", "/c", command]
        else:
            shell_cmd = ["bash", "-c", command]
        if working_directory and Path(working_directory).is_dir():
            cwd = working_directory
        else:
            cwd = WORKSPACE_DIR
        result = subprocess.run(
            shell_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += ("\n" if output else "") + result.stderr
        if not output.strip():
            output = "Command executed successfully (no output)."
        exit_code = result.returncode
        if warning:
            output = f"[SAFETY] {warning}\n\n{output}"
        return f"Exit Code: {exit_code}\n\n{output[:8000]}"
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout}s"
    except FileNotFoundError:
        return f"Error: Shell not found. Command: {command}"
    except Exception as e:
        return f"Error running command: {str(e)}"


def calculate(expression: str, **kwargs) -> str:
    import math
    try:
        result = safe_eval(expression, {
            "pi": math.pi, "e": math.e, "sqrt": math.sqrt,
            "pow": pow, "log": math.log, "sin": math.sin,
            "cos": math.cos, "tan": math.tan, "ceil": math.ceil,
            "floor": math.floor
        })
        return str(result)
    except Exception as e:
        return f"Calculation error: {str(e)}"
