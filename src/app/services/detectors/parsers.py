import tree_sitter_python as tspython
import tree_sitter_java as tspyjava
from tree_sitter import Language, Parser


def load_parser(language_name: str) -> Parser:
    """
    Returns a tree-sitter Parser for the requested language.
    Supports prebuilt languages via tree-sitter-languages.
    """
    if language_name == "python":
        language = Language(tspython.language())
    elif language_name == "java":
        language = Language(tspyjava.language())
    else:
        raise ValueError(f"Unsupported language: {language_name}")

    parser = Parser(language)
    return parser
