from typing import List

from src.app.services.detectors import config
from src.app.dtos.issue import Issue, Severity, IssueType


def detect_many_params(tree, code) -> List[Issue]:
    smells = []

    def walk(node):
        if node.type == "function_definition":
            params = [
                c for c in node.children if c.type == "parameters"
            ]

            if params:
                count = len([p for p in params[0].children if p.type == "identifier"])

                if count > config.TOO_MANY_PARAMS:
                    smells.append(Issue(
                        issue_id="PY_MANY_PARAMS",
                        type=IssueType.MANY_PARAMS,
                        message=f"Function has too many parameters ({count}).",
                        severity=Severity.LOW,
                        line_start=node.start_point[0] + 1
                    ))

        for c in node.children:
            walk(c)

    walk(tree.root_node)
    return smells
