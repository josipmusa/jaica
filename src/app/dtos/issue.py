from enum import Enum

from pydantic import BaseModel
from typing import Optional

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class Issue(BaseModel):
    type: str
    message: str
    severity: Severity
    line_start: int
    line_end: Optional[int] = None
    issue_id: Optional[str] = None
    suggested_fix: Optional[str] = None
    confidence: Optional[float] = None


