import ast
import re
from pathlib import Path
from typing import Optional


# -------------------------
# Python AST helpers
# -------------------------

def _attach_parents(tree: ast.AST):
    """Attach parent references to each AST node."""
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node


# -------------------------
# Code extraction
# -------------------------

def extract_python_code(code: str, method_name: str, class_name: Optional[str] = None) -> str:
    """
    Extract Python function or method code using AST.
    """
    try:
        tree = ast.parse(code)
        _attach_parents(tree)
    except Exception:
        return ""

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == method_name:
            if class_name:
                parent = getattr(node, "parent", None)
                if not parent or not isinstance(parent, ast.ClassDef) or parent.name != class_name:
                    continue
            lines = code.splitlines()
            start = node.lineno - 1
            end = getattr(node, "end_lineno", node.lineno)
            return "\n".join(lines[start:end])
    return ""


def extract_java_code(code: str, method_name: str, class_name: Optional[str] = None) -> str:
    """
    Extract Java method code using regex.
    """
    if class_name:
        class_pattern = rf"\bclass\s+{re.escape(class_name)}\b.*?\{{"
        match = re.search(class_pattern, code, re.DOTALL)
        if not match:
            return ""
        code = code[match.end():]  # only search inside class

    # Match method signature (public/protected/private/static)
    method_pattern = rf"\b(?:public|protected|private|static|\s)+\s+[\w<>\[\]]+\s+{re.escape(method_name)}\s*\([^)]*\)\s*\{{"
    match = re.search(method_pattern, code, re.DOTALL)
    if not match:
        return ""

    start = match.start()
    brace_count = 0
    for i, c in enumerate(code[start:], start):
        if c == "{":
            brace_count += 1
        elif c == "}":
            brace_count -= 1
            if brace_count == 0:
                return code[start:i + 1]
    return code[start:]


# -------------------------
# Recently modified
# -------------------------

def is_file_recently_modified(file_path: Path, days: int = 7) -> bool:
    """
    Returns True if the file was modified within the last `days`.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return False
    import datetime
    mtime = file_path.stat().st_mtime
    age_days = (datetime.datetime.now().timestamp() - mtime) / 86400
    return age_days <= days
