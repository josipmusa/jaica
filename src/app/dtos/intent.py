from enum import Enum

class Intent(str, Enum):
    CODE_REASONING = "CODE_REASONING" #AST, deps, relationships, flow
    CODE_RETRIEVAL = "CODE_RETRIEVAL" #vector RAG code collection
    DOCS_RETRIEVAL = "DOCS_RETRIEVAL" #vector RAG docs collection
    HYBRID = "HYBRID" #when both reasoning & raw code needed
    GENERAL = "GENERAL" #no RAG/graph needed

    @classmethod
    def from_str(cls, s: str):
        try:
            return cls(s)
        except ValueError:
            return None