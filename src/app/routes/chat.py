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
    Streaming endpoint that returns newline-delimited JSON (NDJSON) for real-time LLM responses.
    Each line is a separate JSON object with either 'chunk', 'done', or 'error' field.
    """
    async def stream_generator():
        try:
            # Stream the response
            for chunk in pipeline_router.route_prompt_stream(chat_request):
                # Format as NDJSON: one JSON object per line
                yield json.dumps({'chunk': chunk}) + '\n'

            # Send end signal
            yield json.dumps({'done': True}) + '\n'
        except Exception as e:
            yield json.dumps({'error': str(e)}) + '\n'

    return StreamingResponse(
        stream_generator(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
