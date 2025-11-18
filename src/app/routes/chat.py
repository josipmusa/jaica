from src.app.services.ollama_service import model_chat
from fastapi import APIRouter
from src.app.models.chat import ChatRequest, ChatResponse

router = APIRouter()

@router.post('/chat')
def chat_endpoint(chat_request: ChatRequest):
    model_response = model_chat(chat_request)
    return ChatResponse(answer=model_response)