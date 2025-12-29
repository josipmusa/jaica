from src.app.configuration.dependencies import get_pipeline_router
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from src.app.dtos.chat import ChatRequest
from src.app.services.pipelines.pipeline_router import PipelineRouter

router = APIRouter()

@router.post('/chat/stream')
async def stream_chat_endpoint(chat_request: ChatRequest, pipeline_router: PipelineRouter = Depends(get_pipeline_router)):
    return StreamingResponse(
        pipeline_router.route_prompt(chat_request),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
