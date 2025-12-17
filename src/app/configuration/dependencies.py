from src.app.configuration import config
from src.app.configuration.db import VectorDB
from src.app.configuration.graph_db import GraphDB
from src.app.models.code_classifier.code_classifier import CodeClassifier
from src.app.services.code_analysis_service import CodeAnalyzer
from src.app.services.graph_db_service import GraphDBService
from src.app.services.pipelines.graph_pipeline import GraphReasoningPipeline
from src.app.services.pipelines.pipeline_router import PipelineRouter
from src.app.services.pipelines.rag_pipeline import RagPipeline

code_classifier_instance = CodeClassifier(config.CODE_CLASSIFIER_MODEL_URL, config.CODE_CLASSIFIER_LABEL_URL)
db_instance = VectorDB(persist_dir=str(config.VECTORSTORE_PATH))
graph_db_instance = GraphDB()
graph_db_service_instance = GraphDBService(graph_db=graph_db_instance)
rag_pipeline_instance = RagPipeline(db=db_instance)
graph_reasoning_pipeline_instance = GraphReasoningPipeline(graph_db_service=graph_db_service_instance)
code_analyzer_instance = CodeAnalyzer(code_classifier=code_classifier_instance)
pipeline_router_instance = PipelineRouter(rag_pipeline=rag_pipeline_instance, graph_reasoning_pipeline=graph_reasoning_pipeline_instance)


def get_code_classifier() -> CodeClassifier:
    return code_classifier_instance

def get_db() -> VectorDB:
    return db_instance

def get_rag_pipeline() -> RagPipeline:
    return rag_pipeline_instance

def get_code_analyzer() -> CodeAnalyzer:
    return code_analyzer_instance

def get_pipeline_router() -> PipelineRouter:
    return pipeline_router_instance

def get_graph_db() -> GraphDB:
    return graph_db_instance

def get_graph_db_service() -> GraphDBService:
    return graph_db_service_instance

def get_graph_reasoning_pipeline() -> GraphReasoningPipeline:
    return graph_reasoning_pipeline_instance