from src.app.dtos.issue import Issue, Severity
import re

def detect_unused_vars_and_imports(tree, code):
    """
    Detect unused imports and unused local variables in Java code.
    """
    smells = []
    lines = code.splitlines()

    # ---------------------
    # Detect unused imports
    # ---------------------
    imports = {}  # imp_name -> line number
    import_pattern = re.compile(r"^import\s+([\w.]+);")

    for idx, line in enumerate(lines):
        match = import_pattern.match(line.strip())
        if match:
            imp = match.group(1)
            imports[imp] = idx + 1

    # Check usage by scanning the code lines after imports
    used_imports = set()
    for line in lines:
        for imp in imports.keys():
            class_name = imp.split(".")[-1]
            # basic check: class_name appears in code (ignore the import line itself)
            if class_name in line and not line.strip().startswith("import "):
                used_imports.add(imp)

    for imp, line_no in imports.items():
        if imp not in used_imports:
            smells.append(Issue(
                issue_id="JAVA_UNUSED_IMPORT",
                type="UnusedImport",
                message=f"Import '{imp}' is never used",
                severity=Severity.LOW,
                line_start=line_no,
            ))

    # ---------------------
    # Detect unused local variables
    # ---------------------
    assigned = {}  # var_name -> line_number
    used_vars = set()

    def walk_vars(node, in_method=False):
        if node.type == "method_declaration":
            in_method = True

        if in_method:
            # local variable declarations
            if node.type == "local_variable_declaration":
                for var_node in [c for c in node.children if c.type == "variable_declarator"]:
                    var_name_node = var_node.child_by_field_name("name")
                    if var_name_node:
                        assigned[var_name_node.text.decode()] = node.start_point[0] + 1
            # usage
            if node.type in {"identifier", "type_identifier"}:
                used_vars.add(node.text.decode())

        for child in node.children:
            walk_vars(child, in_method)

    walk_vars(tree.root_node)

    # Report unused variables
    for var, line_no in assigned.items():
        if var not in used_vars:
            smells.append(Issue(
                issue_id="JAVA_UNUSED_VAR",
                type="UnusedVariable",
                message=f"Local variable '{var}' is assigned but never used",
                severity=Severity.LOW,
                line_start=line_no
            ))

    return smells
