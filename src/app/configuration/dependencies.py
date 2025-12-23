from src.app.configuration import config
from src.app.configuration.vector_db import VectorDB
from src.app.configuration.graph_db import GraphDB
from src.app.models.code_classifier.code_classifier import CodeClassifier
from src.app.services.code_analysis_service import CodeAnalysisService
from src.app.services.graph_db_service import GraphDBService
from src.app.services.pipelines.graph_pipeline import GraphReasoningPipeline
from src.app.services.pipelines.hybrid_pipeline import HybridPipeline
from src.app.services.pipelines.pipeline_router import PipelineRouter
from src.app.services.pipelines.rag_pipeline import RagPipeline

code_classifier_instance = CodeClassifier(config.CODE_CLASSIFIER_MODEL_URL, config.CODE_CLASSIFIER_LABEL_URL)
vector_db_instance = VectorDB()
graph_db_instance = GraphDB()
graph_db_service_instance = GraphDBService(graph_db=graph_db_instance)
rag_pipeline_instance = RagPipeline(db=vector_db_instance)
graph_reasoning_pipeline_instance = GraphReasoningPipeline(graph_db_service=graph_db_service_instance)
hybrid_pipeline_instance = HybridPipeline(rag_pipeline=rag_pipeline_instance, graph_pipeline=graph_reasoning_pipeline_instance)
code_analysis_service_instance = CodeAnalysisService(code_classifier=code_classifier_instance)
pipeline_router_instance = PipelineRouter(rag_pipeline=rag_pipeline_instance, graph_reasoning_pipeline=graph_reasoning_pipeline_instance, hybrid_pipeline=hybrid_pipeline_instance)


def get_code_classifier() -> CodeClassifier:
    return code_classifier_instance

def get_vector_db() -> VectorDB:
    return vector_db_instance

def get_pipeline_router() -> PipelineRouter:
    return pipeline_router_instance

def get_graph_db_service() -> GraphDBService:
    return graph_db_service_instance