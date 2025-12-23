from src.app.configuration.dependencies import get_pipeline_router
from fastapi import APIRouter, Depends
from src.app.dtos.chat import ChatRequest
from src.app.services.pipelines.pipeline_router import PipelineRouter

router = APIRouter()

@router.post('/chat')
def query_endpoint(chat_request: ChatRequest, pipeline_router: PipelineRouter = Depends(get_pipeline_router)):
    response = pipeline_router.route_prompt(chat_request)
    return response