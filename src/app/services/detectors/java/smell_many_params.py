from src.app.services.detectors import config
from src.app.dtos.issue import Issue, Severity


def detect_many_params(tree, code):
    smells = []

    def walk(node):
        if node.type == "method_declaration":
            params_node = next((c for c in node.children if c.type == "formal_parameters"), None)
            if params_node:
                count = len([p for p in params_node.children if p.type == "formal_parameter"])
                if count > config.TOO_MANY_PARAMS:
                    smells.append(Issue(
                        issue_id="JAVA_MANY_PARAMS",
                        type="ManyParameters",
                        message=f"Function has too many parameters ({count}).",
                        severity=Severity.LOW,
                        line_start=node.start_point[0] + 1
                    ))

        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return smells
