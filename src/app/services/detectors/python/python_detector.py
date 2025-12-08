from src.app.services.detectors.python.smell_long_function import detect_long_functions
from src.app.services.detectors.python.smell_deep_nesting import detect_deep_nesting
from src.app.services.detectors.python.smell_many_params import detect_many_params
from src.app.services.detectors.python.smell_duplicate_code import detect_duplicate_code
from src.app.services.detectors.python.smell_unused_vars import detect_unused_vars
from src.app.services.detectors.parsers import load_parser

def analyze_python(code: str, file_name = "<input>"):
    parser = load_parser("python")
    tree = parser.parse(code.encode())

    issues = []
    issues += detect_long_functions(tree, code)
    issues += detect_deep_nesting(tree, code)
    issues += detect_many_params(tree, code)
    issues += detect_duplicate_code(code)
    issues += detect_unused_vars(code, file_name)

    # Deduplicate by line + smell_id if needed
    unique = {}
    for i in issues:
        key = (i.issue_id, i.location.line_start)
        if key not in unique:
            unique[key] = i

    return list(unique.values())

