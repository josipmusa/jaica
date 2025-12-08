from typing import Optional

from pydantic import BaseModel

from src.app.dtos.intent import Intent


class AnalyzeCodeRequest(BaseModel):
    code_snippet: str

class PromptRequest(BaseModel):
    prompt: str
    project_name: Optional[str] = None

class ModelResponse(BaseModel):
    answer: str
    intent: Intent