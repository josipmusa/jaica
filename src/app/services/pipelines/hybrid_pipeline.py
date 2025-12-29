import json

from src.app.dtos.chat import ChatRequest, RetrievedFile, DependencyGraph, MetadataChunk, ContentChunk
from src.app.dtos.intent import Intent
from src.app.services.pipelines.graph_pipeline import GraphReasoningPipeline
from src.app.services.pipelines.rag_pipeline import RagPipeline
from src.app.services.llm_service import general_model_chat, general_model_chat_stream
from src.app.configuration.config import HYBRID_SYSTEM_PROMPT


class HybridPipeline:
    def __init__(self, rag_pipeline: RagPipeline, graph_pipeline: GraphReasoningPipeline):
        self.rag_pipeline = rag_pipeline
        self.graph_pipeline = graph_pipeline

    def run(self, chat_request: ChatRequest):
        graph_context, dependency_graph = self.graph_pipeline.run_for_hybrid(chat_request)
        rag_context, retrieved_files = self.rag_pipeline.run_for_hybrid(chat_request)

        metadata_chunk = MetadataChunk(
            intent=Intent.CODE_HYBRID,
            retrievedFiles=retrieved_files,
            dependencyGraph=dependency_graph
        )
        yield json.dumps(metadata_chunk.model_dump(by_alias=True, exclude_none=False)) + "\n"

        prompt_sections = [f"User question:\n{chat_request.prompt}"]

        # Only include graph reasoning if available
        if graph_context is not None:
            prompt_sections.append(
                f"Code structure and relationships (graph reasoning):\n{graph_context}"
            )

        # Only include RAG context if available
        if rag_context:
            prompt_sections.append(
                f"Relevant semantic context (vector retrieval):\n{rag_context}"
            )

        prompt_sections.append(
            "Using the information above, answer the user's question.\n"
            "Focus on correctness, clarity, and actionable insights.\n"
            "Do not mention the code or the fact that it was provided to you; just answer concisely and authoritatively."
        )

        combined_prompt = "\n\n".join(prompt_sections)

        for chunk in general_model_chat_stream(prompt=combined_prompt, system_prompt=HYBRID_SYSTEM_PROMPT):
            content_chunk = ContentChunk(content=chunk)
            yield json.dumps(content_chunk.model_dump(by_alias=True, exclude_none=False)) + "\n"
