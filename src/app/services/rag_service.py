import textwrap
from src.app.configuration.db import db
from src.app.models.chat import RagRequest
from src.app.services.ollama_service import ask

class RagService:
    def __init__(self):
        self.db = db

    def generate_answer(self, rag_request: RagRequest):
        where_filter = {"project": rag_request.project_name} if rag_request.project_name else None
        result = self.db.query(collection=db.code, query_text=rag_request.prompt, n_results=30, where=where_filter)

        docs = result["documents"][0]
        metas = result["metadatas"][0]
        distances = result["distances"][0]  # should be floats

        # Re-rank using distances (smaller distance = more similar)
        chunks_with_distance = list(zip(docs, metas, distances))
        chunks_with_distance.sort(key=lambda x: x[2])  # ascending distance
        top_chunks = chunks_with_distance[:10]

        chunks = [
            f"[Source: {meta['file_path']}]\n{doc}"
            for doc, meta, _ in top_chunks
        ]

        context_text = "\n\n---\n".join(chunks)

        raw_prompt = f"""
You are a local AI coding assistant.
Answer the user's question strictly using the provided context.
If the answer is not in the context, respond with EXACTLY: "I don't know".

### Context:
{context_text}

### Question:
{rag_request.prompt}

### Answer:
"""

        prompt = textwrap.dedent(raw_prompt).strip()
        print(f"RAG prompt: {prompt}")

        return ask(prompt)
