from enum import Enum

from pydantic import BaseModel
from typing import Optional

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class IssueType(str, Enum):
    DEEP_NESTING = "deep_nesting"
    DUPLICATE_CODE = "duplicate_code"
    LONG_FUNCTION = "long_function"
    MANY_PARAMS = "many_params"
    UNUSED_IMPORT = "unused_import"
    UNUSED_VARIABLE = "unused_variable"

class Issue(BaseModel):
    type: IssueType
    message: str
    severity: Severity
    line_start: int
    line_end: Optional[int] = None
    issue_id: Optional[str] = None
    suggested_fix: Optional[str] = None
    confidence: Optional[float] = None



