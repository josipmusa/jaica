from src.app.services.detectors import config
from src.app.dtos.issue import Issue, Severity


def detect_long_functions(tree, code):
    smells = []

    def walk(node):
        if node.type == "function_definition":
            start = node.start_point[0]
            end = node.end_point[0]
            length = end - start

            if length > config.LONG_METHOD_LINES:
                smells.append(Issue(
                    issue_id="PY_LONG_FUNCTION",
                    type="LongFunction",
                    message=f"Function too long ({length} lines).",
                    severity=Severity.MEDIUM,
                    line_start=start + 1,
                    line_end=end + 1
                ))

        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return smells
