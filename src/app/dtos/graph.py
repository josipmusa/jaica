from pydantic import BaseModel
from typing import List
from enum import Enum

class GraphOperation(str, Enum):
    CALLS = "calls"
    CALLED_BY = "called_by"
    USES = "uses"
    STRUCTURE = "structure"
    DEPENDENCIES = "dependencies"

class GraphQueryPlan(BaseModel):
    symbols: List[str]
    operation: GraphOperation