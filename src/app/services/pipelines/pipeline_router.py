from src.app.dtos.chat import PromptRequest, ModelResponse
from src.app.dtos.intent import Intent
from src.app.services.llm_service import classify, general_model_chat
from src.app.services.pipelines.graph_pipeline import GraphReasoningPipeline
from src.app.services.pipelines.rag_pipeline import RagPipeline

class PipelineRouter:
    def __init__(self, rag_pipeline: RagPipeline, graph_reasoning_pipeline: GraphReasoningPipeline):
        self.rag_pipeline = rag_pipeline
        self.graph_reasoning_pipeline = graph_reasoning_pipeline

    def route_prompt(self, prompt_request: PromptRequest) -> ModelResponse:
        intent = classify(prompt_request.prompt)

        if intent is Intent.CODE_GRAPH_REASONING:
            answer  = self.graph_reasoning_pipeline.run(prompt_request)
            return ModelResponse(answer=answer, intent=intent)
        elif intent in {Intent.CODE_VECTOR_RETRIEVAL, Intent.DOCS_VECTOR_RETRIEVAL}:
            answer = self.rag_pipeline.run(prompt_request)
            return ModelResponse(answer=answer, intent=intent)
        else:
            answer = general_model_chat(prompt_request.prompt)
            return ModelResponse(answer=answer, intent=intent)