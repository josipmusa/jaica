from typing import List

from src.app.services.detectors import config
from src.app.dtos.issue import Issue, Severity, IssueType


def detect_long_functions(tree, code) -> List[Issue]:
    smells = []

    def walk(node):
        if node.type == "method_declaration":
            start = node.start_point[0]
            end = node.end_point[0]
            length = end - start

            if length > config.LONG_METHOD_LINES:
                smells.append(Issue(
                    issue_id="JAVA_LONG_FUNCTION",
                    type=IssueType.LONG_FUNCTION,
                    message=f"Function too long ({length} lines).",
                    severity=Severity.MEDIUM,
                    line_start=start + 1,
                    line_end=end + 1,
                ))

        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return smells
