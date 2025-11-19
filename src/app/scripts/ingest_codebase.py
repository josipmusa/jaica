import traceback
from pathlib import Path
import sys
from src.app.services.ingestion_service import IngestionService

def main(paths):
    service = IngestionService()

    for path_str in paths:
        folder = Path(path_str)
        if not folder.exists() or not folder.is_dir():
            print(f"[SKIP] Path does not exist or is not a directory: {folder}")
            continue

        print(f"[START] Ingesting codebase: {folder}")
        try:
            service.ingest_codebase(folder)
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
