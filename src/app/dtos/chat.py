from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict

from src.app.dtos.intent import Intent


class ChatRequest(BaseModel):
    prompt: str
    project_name: Optional[str] = None

class RetrievedFile(BaseModel):
    path: str
    content: str
    relevance: Optional[float] = None

class DependencyEdge(BaseModel):
    from_: str = Field(alias="from")
    to: str

    model_config = ConfigDict(populate_by_name=True)


class DependencyGraph(BaseModel):
    nodes: List[str]
    edges: List[DependencyEdge]
    description: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)

class ChatResponse(BaseModel):
    answer: str
    intent: Intent
    retrieved_files: Optional[List[RetrievedFile]] = Field(
        default=None,
        alias="retrievedFiles",
    )
    dependency_graph: Optional[DependencyGraph] = Field(
        default=None,
        alias="dependencyGraph",
    )

    model_config = ConfigDict(populate_by_name=True)