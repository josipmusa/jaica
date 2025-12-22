import textwrap
from typing import Tuple, List

from src.app.configuration.config import HYBRID_SYSTEM_PROMPT
from src.app.configuration.db import VectorDB
from src.app.dtos.chat import ChatRequest, RetrievedFile
from src.app.services.llm_service import general_model_chat


def _extract_code_for_response(text: str) -> str:
    marker = "Code:\n"
    if marker in text:
        return text.split(marker, 1)[1].strip()
    return text


class RagPipeline:
    def __init__(self, db: VectorDB):
        self.db = db

    def run(self, chat_request: ChatRequest) -> Tuple[str, List[RetrievedFile]]:
        where_filter = {"project": chat_request.project_name} if chat_request.project_name else None

        result = self.db.query(
            collection=self.db.code,
            query_text=chat_request.prompt,
            n_results=30,
            where=where_filter,
        )

        docs = result["documents"][0]
        metas = result["metadatas"][0]
        distances = result["distances"][0]  # float, smaller = more similar

        # Re-rank by similarity
        chunks_with_distance = list(zip(docs, metas, distances))
        chunks_with_distance.sort(key=lambda x: x[2])
        top_chunks = chunks_with_distance[:10]

        retrieved_files: List[RetrievedFile] = []
        context_blocks: List[str] = []

        for doc, meta, distance in top_chunks:
            retrieved_files.append(
                RetrievedFile(
                    path=meta["file_path"],
                    content=_extract_code_for_response(doc),
                    relevance=1 / (1 + distance),  # normalize distance → similarity
                )
            )

            context_blocks.append(
                f"[Source: {meta['file_path']} | Language: {meta['language']}]\n{doc}"
            )

        context_text = "\n\n---\n".join(context_blocks)

        raw_prompt = f"""
You are a local AI coding assistant.
Answer the user's question strictly using the provided context.
If the answer is not in the context, respond with EXACTLY: "I don't know".
Do not mention that the code was provided to you; answer like you know the code.

Relevant semantic context (vector retrieval):
{context_text}

User question:
{chat_request.prompt}

Using the information above, answer the user's question.
Focus on correctness, clarity, and actionable insights.
If the answer is not in the context, respond with EXACTLY: "I don't know".
Do not mention the fact that the code was provided to you; answer like you know the code.
"""

        prompt = textwrap.dedent(raw_prompt).strip()

        answer = general_model_chat(
            prompt=prompt,
            system_prompt=HYBRID_SYSTEM_PROMPT,
        )

        return answer, retrieved_files
