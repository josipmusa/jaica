from src.app.configuration.dependencies import get_pipeline_router
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from src.app.dtos.chat import ChatRequest
from src.app.services.pipelines.pipeline_router import PipelineRouter
import json

router = APIRouter()

@router.post('/chat')
def query_endpoint(chat_request: ChatRequest, pipeline_router: PipelineRouter = Depends(get_pipeline_router)):
    response = pipeline_router.route_prompt(chat_request)
    return response

@router.post('/chat/stream')
async def stream_chat_endpoint(chat_request: ChatRequest, pipeline_router: PipelineRouter = Depends(get_pipeline_router)):
    """
    Streaming endpoint that returns Server-Sent Events (SSE) for real-time LLM responses.
    """
    async def event_generator():
        try:
            # Stream the response
            for chunk in pipeline_router.route_prompt_stream(chat_request):
                # Format as SSE: data: {json}\n\n
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"

            # Send end signal
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
