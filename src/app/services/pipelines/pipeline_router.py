import json

from src.app.dtos.chat import ChatRequest, ChatResponse, ContentChunk
from src.app.dtos.intent import Intent
from src.app.services.llm_service import classify_intent, general_model_chat, general_model_chat_stream
from src.app.services.pipelines.graph_pipeline import GraphReasoningPipeline
from src.app.services.pipelines.hybrid_pipeline import HybridPipeline
from src.app.services.pipelines.rag_pipeline import RagPipeline
from src.app.services.pipelines.test_analysis_pipeline import TestAnalysisPipeline


class PipelineRouter:
    def __init__(self, rag_pipeline: RagPipeline, graph_reasoning_pipeline: GraphReasoningPipeline,
                 hybrid_pipeline: HybridPipeline, test_analysis_pipeline: TestAnalysisPipeline):
        self.rag_pipeline = rag_pipeline
        self.graph_reasoning_pipeline = graph_reasoning_pipeline
        self.hybrid_pipeline = hybrid_pipeline
        self.test_analysis_pipeline = test_analysis_pipeline

    def route_prompt(self, chat_request: ChatRequest) -> ChatResponse:
        intent = classify_intent(chat_request.prompt)

        if intent is Intent.CODE_GRAPH_REASONING:
            answer, dependency_graph = self.graph_reasoning_pipeline.run(chat_request)
            if answer is None:
                return ChatResponse(answer="Sorry, I can't answer that question", intent=intent)
            else:
                return ChatResponse(answer=answer, intent=intent, dependency_graph=dependency_graph)
        elif intent in {Intent.CODE_VECTOR_RETRIEVAL, Intent.DOCS_VECTOR_RETRIEVAL}:
            answer, retrieved_files = self.rag_pipeline.run(chat_request)
            return ChatResponse(answer=answer, intent=intent, retrieved_files=retrieved_files)
        elif intent is Intent.CODE_HYBRID:
            answer, retrieved_files, dependency_graph = self.hybrid_pipeline.run(chat_request)
            return ChatResponse(answer=answer, intent=intent, retrieved_files=retrieved_files,
                                dependency_graph=dependency_graph)
        elif intent is Intent.TEST_ANALYSIS:
            answer = self.test_analysis_pipeline.run(chat_request)
            return ChatResponse(answer=answer, intent=intent)
        else:
            answer = general_model_chat(chat_request.prompt)
            return ChatResponse(answer=answer, intent=intent)

    def route_prompt_stream(self, chat_request: ChatRequest):
        """
        Streaming version of route_prompt. Yields text chunks as they arrive.
        For complex intents (graph, RAG, etc), streams the final answer generation.
        """
        intent = classify_intent(chat_request.prompt)

        if intent is Intent.CODE_GRAPH_REASONING:
            yield from self.graph_reasoning_pipeline.run_stream(chat_request)
        elif intent in {Intent.CODE_VECTOR_RETRIEVAL, Intent.DOCS_VECTOR_RETRIEVAL}:
            yield from self.rag_pipeline.run_stream(chat_request, intent)
        elif intent is Intent.CODE_HYBRID:
            yield from self.hybrid_pipeline.run_stream(chat_request)
        elif intent is Intent.TEST_ANALYSIS:
            yield from self.test_analysis_pipeline.run_stream(chat_request)
        else:
            # For general chat, use true streaming from the LLM
            for chunk in general_model_chat_stream(chat_request.prompt):
                content_chunk = ContentChunk(content=chunk)
                yield json.dumps(content_chunk.model_dump(by_alias=True, exclude_none=False)) + "\n"
