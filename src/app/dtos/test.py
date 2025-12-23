from typing import Optional, List

from pydantic import BaseModel


class TestCodeAnalysisResult(BaseModel):
    deep_nesting: bool
    long_function: bool
    many_params: bool
    param_count: Optional[int] = None

class TestAnalysisExtractedEntities(BaseModel):
    class_name: Optional[str] = None
    method_name: Optional[str] = None

class TestGapFinding(BaseModel):
    class_name: str
    method_name: Optional[str]
    reasons: List[str]
    priority: int  # heuristic score
    suggested_focus: Optional[str] = None