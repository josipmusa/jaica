from hashlib import md5
from src.app.dtos.issue import Issue, Severity

def detect_duplicate_code(code):
    smells = []
    blocks = code.split("\n\n")  # rough heuristic for code blocks

    hashes = {}
    for idx, block in enumerate(blocks):
        digest = md5(block.strip().encode()).hexdigest()
        line_start = sum(len(b.splitlines()) for b in blocks[:idx]) + 1

        if digest in hashes:
            original_line = hashes[digest]
            smells.append(Issue(
                issue_id="JAVA_DUPLICATE_CODE",
                type="DuplicateCode",
                message=f"Duplicate code block found matching block starting at line {original_line}.",
                severity=Severity.LOW,
                line_start=line_start
            ))
        else:
            hashes[digest] = line_start

    return smells
