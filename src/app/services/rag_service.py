import textwrap

from src.app.configuration.db import VectorDB
from src.app.dtos.chat import PromptRequest
from src.app.services.llm_service import ask

class RagService:
    def __init__(self, db: VectorDB):
        self.db = db

    def generate_answer(self, prompt_request: PromptRequest) -> str:
        where_filter = {"project": prompt_request.project_name} if prompt_request.project_name else None
        result = self.db.query(collection=self.db.code, query_text=prompt_request.prompt, n_results=30, where=where_filter)

        docs = result["documents"][0]
        metas = result["metadatas"][0]
        distances = result["distances"][0]  # should be floats

        # Re-rank using distances (smaller distance = more similar)
        chunks_with_distance = list(zip(docs, metas, distances))
        chunks_with_distance.sort(key=lambda x: x[2])  # ascending distance
        top_chunks = chunks_with_distance[:5]

        chunks = [
            f"[Source: {meta['file_path']} | Language: {meta['language']}]\n{doc}"
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
{prompt_request.prompt}

### Answer:
"""

        prompt = textwrap.dedent(raw_prompt).strip()
        print(f"RAG prompt: {prompt}")

        return ask(prompt)
