from src.app.dtos.chat import ChatRequest, ChatResponse
from src.app.dtos.intent import Intent
from src.app.services.llm_service import classify, general_model_chat
from src.app.services.pipelines.graph_pipeline import GraphReasoningPipeline
from src.app.services.pipelines.hybrid_pipeline import HybridPipeline
from src.app.services.pipelines.rag_pipeline import RagPipeline

class PipelineRouter:
    def __init__(self, rag_pipeline: RagPipeline, graph_reasoning_pipeline: GraphReasoningPipeline, hybrid_pipeline: HybridPipeline):
        self.rag_pipeline = rag_pipeline
        self.graph_reasoning_pipeline = graph_reasoning_pipeline
        self.hybrid_pipeline = hybrid_pipeline

    def route_prompt(self, chat_request: ChatRequest) -> ChatResponse:
        intent = classify(chat_request.prompt)

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
            return ChatResponse(answer=answer, intent=intent, retrieved_files=retrieved_files, dependency_graph=dependency_graph)
        else:
            answer = general_model_chat(chat_request.prompt)
            return ChatResponse(answer=answer, intent=intent)