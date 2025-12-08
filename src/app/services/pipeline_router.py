from src.app.dtos.chat import PromptRequest, ModelResponse
from src.app.dtos.intent import Intent
from src.app.services.llm_service import classify, general_model_chat
from src.app.services.rag_service import RagService

class PipelineRouter:
    def __init__(self, rag_service: RagService):
        self.rag_service = rag_service

    def route_prompt(self, prompt_request: PromptRequest) -> ModelResponse:
        intent = classify(prompt_request.prompt)

        if intent in {Intent.GENERAL, Intent.HYBRID}:
            answer = general_model_chat(prompt_request.prompt)
            return ModelResponse(answer=answer, intent=intent)
        elif intent in {Intent.CODE_RETRIEVAL, Intent.DOCS_RETRIEVAL}:
            answer = self.rag_service.generate_answer(prompt_request)
            return ModelResponse(answer=answer, intent=intent)
        else:
            answer = general_model_chat(prompt_request.prompt)
            return ModelResponse(answer=answer, intent=intent)