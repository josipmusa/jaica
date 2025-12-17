import sys
import traceback

from src.app.services.ingestion.semantic_linking_service import SemanticLinkingService
from src.app.configuration.dependencies import get_graph_db_service


def main(projects):
    graph_db_service = get_graph_db_service()
    semantic_linking_service = SemanticLinkingService(graph_db_service)

    for project in projects:
        print(f"[START] Performing semantic linking for project: {project}")

        if not graph_db_service.project_exists(project):
            print(f"[SKIP] Project '{project}' not found in graph DB")
            continue
        try:
            semantic_linking_service.run(project)
            print(f"[DONE] Finished project: {project}")
        except Exception as e:
            print(f"[ERROR] Failed to project {project}: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    # Accept multiple project names as CLI arguments
    if len(sys.argv) < 2:
        print("Usage: python link_graph_semantics.py project1 project2 ...")
        sys.exit(1)

    project_names = sys.argv[1:]
    main(project_names)