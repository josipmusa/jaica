from fastapi import APIRouter, Depends
from src.app.configuration.dependencies import get_vector_db, get_graph_db_service
from src.app.configuration.vector_db import VectorDB
from src.app.services.graph_db_service import GraphDBService
from src.app.configuration.config import MAIN_LLM_MODEL
from ollama import list as ollama_list

router = APIRouter()

@router.get("/status")
def status_endpoint(
    vector_db: VectorDB = Depends(get_vector_db),
    graph_db_service: GraphDBService = Depends(get_graph_db_service)
):
    """
    Check the health status of the API and its dependencies.

    Returns:
        dict: Status information including vector DB, graph DB, and LLM connection states
    """
    status_response = {
        "status": "ok",
        "vector_db": "disconnected",
        "graph_db": "disconnected",
        "llm": "disconnected"
    }

    # Check Vector DB connection
    try:
        vector_db.client.heartbeat()
        status_response["vector_db"] = "connected"
    except Exception as e:
        status_response["vector_db"] = f"error: {str(e)}"

    # Check Graph DB connection
    try:
        graph_db_service.graph_db.driver.verify_connectivity()
        status_response["graph_db"] = "connected"
    except Exception as e:
        status_response["graph_db"] = f"error: {str(e)}"

    # Check LLM availability
    try:
        models = ollama_list()
        model_names = [model.model for model in models.models]
        if MAIN_LLM_MODEL in model_names:
            status_response["llm"] = "connected"
        else:
            status_response["llm"] = f"error: model '{MAIN_LLM_MODEL}' not found"
    except Exception as e:
        status_response["llm"] = f"error: {str(e)}"

    # Determine overall status based on all connections
    vector_connected = status_response["vector_db"] == "connected"
    graph_connected = status_response["graph_db"] == "connected"
    llm_connected = status_response["llm"] == "connected"

    connected_count = sum([vector_connected, graph_connected, llm_connected])

    if connected_count == 0:
        status_response["status"] = "error"
    elif connected_count < 3:
        status_response["status"] = "degraded"
    else:
        status_response["status"] = "ok"

    return status_response
