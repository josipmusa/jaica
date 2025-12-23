import re
from hashlib import md5
from typing import List

from src.app.dtos.issue import Issue, Severity, IssueType


def detect_duplicate_code(code) -> List[Issue]:
    smells = []
    # Find all function blocks
    func_blocks = re.findall(r"(def\s+\w+\(.*?\):[\s\S]+?)(?=\ndef|\Z)", code)
    hashes = {}
    for block in func_blocks:
        digest = md5(block.strip().encode()).hexdigest()
        start_line = code[:code.find(block)].count("\n") + 1
        if digest in hashes:
            original_line = hashes[digest]
            smells.append(Issue(
                issue_id="PY_DUPLICATE_CODE",
                type=IssueType.DUPLICATE_CODE,
                message=f"Duplicate function found matching block starting at line {original_line}.",
                severity=Severity.LOW,
                line_start=start_line
            ))
        else:
            hashes[digest] = start_line
    return smells
