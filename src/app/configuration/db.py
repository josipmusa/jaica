import chromadb
from chromadb.config import Settings
from chromadb.api.types import EmbeddingFunction
from chromadb.api.models.Collection import Collection
from pathlib import Path

from sentence_transformers import SentenceTransformer
import torch

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
VECTORSTORE_PATH = PROJECT_ROOT / "vectorstore"


class STEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model):
        self.model = model

    def name(self):
        return "sentence-transformers-bge-small-en-v1.5"

    def embed_documents(self, texts):
        return self.model.encode(texts, convert_to_numpy=True).tolist()

    def embed_query(self, input):
        return self.model.encode([input], convert_to_numpy=True).tolist()[0]

    def __call__(self, input):
        # Case 1: Chroma sends {"documents": [...]}
        if isinstance(input, dict):
            if "documents" in input and input["documents"] is not None:
                return self.embed_documents(input["documents"])

            if "queries" in input and input["queries"] is not None:
                return [self.embed_query(q) for q in input["queries"]]

        # Case 2: Chroma directly sends a list of strings → documents
        if isinstance(input, list):
            return self.embed_documents(input)

        raise ValueError(f"Invalid embedding input received: {input}")


class VectorDB:
    _instance = None

    def __new__(cls, persist_dir: str = "./vectorstore"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

            # Init Chroma
            cls._instance.client = chromadb.Client(
                Settings(
                    anonymized_telemetry=False,
                    persist_directory=persist_dir,
                    is_persistent=True
                )
            )

            # Load embedding model on GPU
            model = SentenceTransformer(
                model_name_or_path="BAAI/bge-small-en-v1.5",
                device="cuda" if torch.cuda.is_available() else "cpu"
            )

            cls._instance.embedding_fn = STEmbeddingFunction(model)

            cls._instance._code_collection = None
            cls._instance._docs_collection = None

        return cls._instance

    # --- Collections ---
    @property
    def code(self) -> Collection:
        if self._code_collection is None:
            self._code_collection = self.client.get_or_create_collection(
                name="code",
                embedding_function=self.embedding_fn,
                metadata={"description": "Codebase embeddings"},
            )
        return self._code_collection

    @property
    def docs(self) -> Collection:
        if self._docs_collection is None:
            self._docs_collection = self.client.get_or_create_collection(
                name="docs",
                embedding_function=self.embedding_fn,
                metadata={"description": "Documentation embeddings"},
            )
        return self._docs_collection

    def insert(self, collection: Collection, texts, metadatas, ids):
        collection.add(documents=texts, metadatas=metadatas, ids=ids)

    def query(self, collection: Collection, query_text, n_results=5, where=None):
        #Perform manual embedding here due to chromadb not invoking _call_ properly in embedding
        embedding_vector = self.embedding_fn.embed_query(query_text)
        return collection.query(
            query_embeddings=[embedding_vector],
            query_texts=None,
            n_results=n_results,
            where=where
        )