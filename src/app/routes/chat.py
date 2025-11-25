from src.app.configuration.dependencies import get_rag_service, get_code_analyzer
from src.app.services.code_analysis_service import CodeAnalyzer
from src.app.services.ollama_service import model_chat
from fastapi import APIRouter, Depends
from src.app.dtos.chat import ChatRequest, ChatResponse, RagRequest, AnalyzeCodeRequest
from src.app.services.rag_service import RagService

router = APIRouter()

@router.post('/chat')
def chat_endpoint(chat_request: ChatRequest):
    model_response = model_chat(chat_request)
    return ChatResponse(answer=model_response)

@router.post('/rag-query')
def rag_query_endpoint(rag_request: RagRequest, rag_service: RagService = Depends(get_rag_service)):
    answer = rag_service.generate_answer(rag_request)
    return ChatResponse(answer=answer)

@router.post('/analyze-code')
def analyze_code_endpoint(analyze_code_request: AnalyzeCodeRequest, code_analysis_service: CodeAnalyzer = Depends(get_code_analyzer)):
    issues = code_analysis_service.analyze(analyze_code_request.code_snippet)
    return issues