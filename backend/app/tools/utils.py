import os
import math
import re
import datetime
import hashlib
import secrets
import string
import uuid as uuid_mod
import difflib
import ast
from typing import Any, Dict, Optional

from app.core.config import WORKSPACE_DIR


DANGEROUS_MODULES = {
    "subprocess", "shutil", "ctypes", "importlib", "sys", "os",
    "socket", "http", "ftplib", "smtplib", "telnetlib",
    "xmlrpc", "pickle", "shelve", "dbm",
}

DANGEROUS_COMMANDS = {
    "rm", "rmdir", "rd", "del", "format", "mkfs",
    "shutdown", "reboot", "halt", "poweroff",
    "sudo", "su", "runas", "net user", "net localgroup",
    "reg delete", "reg add",
    "taskkill", "taskkill /f",
    "cipher", "icacls",
    "bcdboot", "bootrec",
}

SAFE_EVAL_GLOBALS = {"__builtins__": {}}
SAFE_EVAL_LOCALS = {
    "True": True, "False": False, "None": None,
    "len": len, "str": str, "int": int, "float": float,
    "bool": bool, "abs": abs, "min": min, "max": max,
    "round": round, "sum": sum, "sorted": sorted,
}


def safe_eval(expression: str, extra_vars: Optional[Dict] = None) -> Any:
    """Evaluate an expression with restricted builtins and whitelisted names."""
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        raise ValueError(f"Invalid expression syntax: {expression}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            raise ValueError("Function calls are not allowed in expressions")
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise ValueError("Imports are not allowed in expressions")
    locals_dict = dict(SAFE_EVAL_LOCALS)
    if extra_vars:
        locals_dict.update(extra_vars)
    return eval(expression, SAFE_EVAL_GLOBALS, locals_dict)


def _check_code_safety(code: str) -> Optional[str]:
    """Check code for dangerous imports/operations. Returns warning or None."""
    code_lower = code.lower()
    for module in DANGEROUS_MODULES:
        patterns = [f"import {module}", f"from {module}", f"__import__('{module}')"]
        for pattern in patterns:
            if pattern in code_lower:
                return f"Warning: code uses restricted module '{module}'"
    return None


def _check_command_safety(command: str) -> Optional[str]:
    """Check command for dangerous operations. Returns warning or None."""
    cmd_lower = command.lower().strip()
    for dangerous in DANGEROUS_COMMANDS:
        if cmd_lower.startswith(dangerous) or f" {dangerous} " in cmd_lower:
            return f"Warning: command contains potentially dangerous operation '{dangerous}'"
    return None


def random_generate(type: str = "uuid", length: int = 16, count: int = 1, **kwargs) -> str:
    try:
        results = []
        for _ in range(min(count, 100)):
            if type == "uuid":
                results.append(str(uuid_mod.uuid4()))
            elif type == "password":
                alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
                results.append("".join(secrets.choice(alphabet) for _ in range(max(length, 8))))
            elif type == "number":
                upper = 10 ** min(length, 15)
                results.append(str(secrets.randbelow(upper)))
            elif type == "string":
                results.append("".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(max(length, 1))))
            else:
                return f"Error: Unknown type '{type}'. Use: uuid, password, number, string"
        return "\n".join(results)
    except Exception as e:
        return f"Error generating random data: {str(e)}"


def diff_texts(text_a: str, text_b: str, context_lines: int = 3, **kwargs) -> str:
    try:
        lines_a = text_a.splitlines(keepends=True)
        lines_b = text_b.splitlines(keepends=True)
        diff = list(difflib.unified_diff(
            lines_a, lines_b,
            fromfile="text_a", tofile="text_b",
            n=context_lines
        ))
        if not diff:
            return "No differences found."
        return "".join(diff)[:10000]
    except Exception as e:
        return f"Error computing diff: {str(e)}"


def hash_data(data: str, algorithm: str = "sha256", **kwargs) -> str:
    try:
        alg_map = {
            "sha256": hashlib.sha256,
            "sha1": hashlib.sha1,
            "md5": hashlib.md5,
        }
        if algorithm not in alg_map:
            return f"Error: Unknown algorithm '{algorithm}'. Use: sha256, sha1, md5"
        h = alg_map[algorithm]()
        h.update(data.encode("utf-8"))
        return f"{algorithm}: {h.hexdigest()}"
    except Exception as e:
        return f"Error hashing data: {str(e)}"


def get_datetime(format_str: str = "%Y-%m-%d %H:%M:%S", **kwargs) -> str:
    return datetime.datetime.now().strftime(format_str)
