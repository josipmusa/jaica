from typing import List

from src.app.services.detectors import config
from src.app.dtos.issue import Issue, Severity, IssueType

# Node types that contribute to nesting
NESTING_NODES = {
    "if_statement",
    "for_statement",
    "while_statement",
    "try_statement",
    "switch_statement",
    "method_declaration",
    "class_declaration",
}

def detect_deep_nesting(tree, code) -> List[Issue]:
    smells = []

    def walk(node, depth=0):
        # Increase depth only for relevant nodes
        if node.type in NESTING_NODES:
            depth += 1

        # If this node exceeds max depth, report it and skip its children
        if depth > config.MAX_DEPTH:
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            smells.append(Issue(
                issue_id="JAVA_DEEP_NESTING",
                type=IssueType.DEEP_NESTING,
                message=f"Code nested too deeply (depth={depth}).",
                severity=Severity.MEDIUM,
                line_start=start_line,
                line_end=end_line,
            ))
            return  # Do not descend further; this whole block is reported

        # Recurse into children
        for child in node.children:
            walk(child, depth)

    walk(tree.root_node, 0)
    return smells
