from enum import Enum

class Intent(str, Enum):
    CODE_GRAPH_REASONING   = "CODE_GRAPH_REASONING  " #AST, deps, relationships, flow
    CODE_VECTOR_RETRIEVAL   = "CODE_VECTOR_RETRIEVAL  " #vector RAG code collection
    DOCS_VECTOR_RETRIEVAL = "DOCS_VECTOR_RETRIEVAL" #vector RAG docs collection
    CODE_HYBRID = "CODE_HYBRID" #when both reasoning & raw code needed
    GENERAL = "GENERAL" #no RAG/graph needed

    @classmethod
    def from_str(cls, s: str):
        try:
            return cls(s)
        except ValueError:
            return None