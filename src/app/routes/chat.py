from src.app.services.ollama_service import model_chat
from fastapi import APIRouter
from src.app.dtos.chat import ChatRequest, ChatResponse, RagRequest
from src.app.services.rag_service import RagService

router = APIRouter()
rag_service = RagService()

@router.post('/chat')
def chat_endpoint(chat_request: ChatRequest):
    model_response = model_chat(chat_request)
    return ChatResponse(answer=model_response)

@router.post('/rag-query')
def rag_query_endpoint(rag_request: RagRequest):
    answer = rag_service.generate_answer(rag_request)
    return ChatResponse(answer=answer)