from .smell_long_function import detect_long_functions
from .smell_deep_nesting import detect_deep_nesting
from .smell_many_params import detect_many_params
from .smell_duplicate_code import detect_duplicate_code
from .smell_unused_vars import detect_unused_vars_and_imports
from ..parsers import load_parser

def analyze_java(code: str):
    try:
        parser = load_parser("java")
    except Exception as e:
        raise RuntimeError(
            "Failed loading tree-sitter parser for 'java'. Original error: " + str(e)
        )

    tree = parser.parse(code.encode())

    smells = []
    smells += detect_long_functions(tree, code)
    smells += detect_deep_nesting(tree, code)
    smells += detect_many_params(tree, code)
    smells += detect_duplicate_code(code)
    smells += detect_unused_vars_and_imports(tree, code)

    return smells
