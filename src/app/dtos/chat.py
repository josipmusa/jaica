from enum import Enum
from typing import Optional

from pydantic import BaseModel

class TaskType(str, Enum):
    DEBUGGING = "Debugging"
    WRITING_CODE = "Writing code"
    EXPLAINING_CODE = "Explaining code"
    REFACTORING_CODE = "Refactoring code"
    WRITE_TESTS = "Write tests"
    OPTIMIZE_CODE = "Optimize code"

class AnalyzeCodeRequest(BaseModel):
    code_snippet: str

class ChatRequest(BaseModel):
    prompt: str
    task_type: Optional[TaskType] = None

class RagRequest(BaseModel):
    prompt: str
    project_name: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str