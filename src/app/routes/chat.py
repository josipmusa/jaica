from src.app.configuration.dependencies import get_code_analyzer, get_pipeline_router
from src.app.services.code_analysis_service import CodeAnalyzer
from fastapi import APIRouter, Depends
from src.app.dtos.chat import PromptRequest, AnalyzeCodeRequest
from src.app.services.pipelines.pipeline_router import PipelineRouter

router = APIRouter()

@router.post('/query')
def query_endpoint(prompt_request: PromptRequest, pipeline_router: PipelineRouter = Depends(get_pipeline_router)):
    response = pipeline_router.route_prompt(prompt_request)
    return response

@router.post('/analyze-code')
def analyze_code_endpoint(analyze_code_request: AnalyzeCodeRequest, code_analysis_service: CodeAnalyzer = Depends(get_code_analyzer)):
    issues = code_analysis_service.analyze(analyze_code_request.code_snippet)
    return issues