from pyflakes.api import check
from pyflakes.reporter import Reporter
from io import StringIO
from src.app.dtos.issue import Issue, Severity

def detect_unused_vars(code, filename="<input>"):
    output = StringIO()
    error = StringIO()
    reporter = Reporter(output, error)
    check(code, filename=filename, reporter=reporter)

    messages = output.getvalue() + error.getvalue()
    smells = []

    for line in messages.splitlines():
        if "assigned to but never used" in line:
            parts = line.split(":")
            line_no = int(parts[1])
            smells.append(Issue(
                issue_id="PY_UNUSED_VAR",
                type="UnusedVariable",
                message=line.strip(),
                severity=Severity.LOW,
                line_start=line_no
            ))
        elif "imported but unused" in line:
            parts = line.split(":")
            line_no = int(parts[1])
            smells.append(Issue(
                issue_id="PY_UNUSED_IMPORT",
                type="UnusedImport",
                message=line.strip(),
                severity=Severity.LOW,
                line_start=line_no
            ))
    return smells
