import traceback
from pathlib import Path
import sys
from src.app.services.ingestion.ingestion_graph_service import IngestionServiceGraph
from src.app.configuration.dependencies import get_code_classifier, get_graph_db_service

def main(paths):
    service = IngestionServiceGraph(get_code_classifier(), get_graph_db_service())

    for path_str in paths:
        folder = Path(path_str)
        if not folder.exists() or not folder.is_dir():
            print(f"[SKIP] Path does not exist or is not a directory: {folder}")
            continue

        project_name = folder.name
        print(f"[START] Ingesting codebase: {folder}, project name: {project_name}")
        try:
            service.ingest_codebase(folder, project_name)
            print(f"[DONE] Ingested codebase: {folder}")
        except Exception as e:
            print(f"[ERROR] Failed to ingest {folder}: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    # Accept multiple codebase paths as CLI arguments
    if len(sys.argv) < 2:
        print("Usage: python ingest_codebase.py /path/to/project1 /path/to/project2 ...")
        sys.exit(1)

    codebase_paths = sys.argv[1:]
    main(codebase_paths)
