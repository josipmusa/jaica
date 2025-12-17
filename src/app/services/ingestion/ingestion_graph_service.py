from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from src.app.models.code_classifier.code_classifier import CodeClassifier
from src.app.services.graph_db_service import GraphDBService
from src.app.services.ingestion.ingestion_service import compute_node_hash, extract_nodes, SUPPORTED_CODE_EXTENSIONS, IGNORE_CODE_FOLDERS
from src.app.services.llm_service import summarize_code


class IngestionServiceGraph:
    def __init__(
        self,
        code_classifier: CodeClassifier,
        graph_db_service: GraphDBService,
    ):
        self.code_classifier = code_classifier
        self.graph_db_service = graph_db_service


    def ingest_code_file(self, file_path: Path, project_name: str):
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"Skipping {file_path}: {e}")
            return

        language = SUPPORTED_CODE_EXTENSIONS.get(file_path.suffix) or self.code_classifier.predict(
            content
        )

        extracted = extract_nodes(language, content, str(file_path))
        if not extracted:
            return

        # ---- FILE NODE ----
        file_node_id = f"{project_name}:{file_path}"
        self.graph_db_service.upsert_node(
            node_id=file_node_id,
            node_name=file_path.name,
            node_type="file",
            language=language,
            file_path=str(file_path),
            project_name=project_name,
            start_line=1,
            end_line=len(content.splitlines()),
            summary=f"File {file_path.name}",
            node_hash=compute_node_hash(content),
            symbols_defined=[],
            symbols_used=[],
            node_kind="file",
        )
        # --- LINK FILE TO PROJECT ---
        self.graph_db_service.link_project_to_node(
            project_name,
            file_node_id,
            "CONTAINS",
            {"reason": "project_root"}
        )

        # ---- CODE NODES ----
        for node in extracted["nodes"]:
            node_id = node["node_id"]
            node_hash = compute_node_hash(node["full_code"])

            existing = self.graph_db_service.get_node(node_id)
            if existing and existing.get("node_hash") == node_hash:
                continue

            summary = summarize_code(node["full_code"])

            self.graph_db_service.upsert_node(
                node_id=node_id,
                node_name=node["node_name"],
                node_type=node["node_type"],
                language=language,
                file_path=str(file_path),
                project_name=project_name,
                start_line=node["start_line"],
                end_line=node["end_line"],
                summary=summary,
                node_hash=node_hash,
                symbols_defined=extracted["defined_symbols"].get(node_id, []),
                symbols_used=[u[1] for u in extracted["usages"] if u[0] == node_id],
                node_kind=node["node_type"],
            )

            # ---- STRUCTURE ----
            parent_id = node.get("parent_id")
            if parent_id:
                self.graph_db_service.link(
                    parent_id,
                    node_id,
                    "CONTAINS",
                    {"reason": "ast_structure"},
                )
            else:
                self.graph_db_service.link(
                    file_node_id,
                    node_id,
                    "CONTAINS",
                    {"reason": "file_structure"},
                )

    def ingest_codebase(self, folder: Path, project_name: str, max_workers: int = 2):
        self.graph_db_service.upsert_project(project_name)
        files = [
            f
            for f in folder.rglob("*")
            if f.is_file()
               and f.suffix in SUPPORTED_CODE_EXTENSIONS
               and not any(p in f.parts for p in IGNORE_CODE_FOLDERS)
        ]

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.ingest_code_file, f, project_name) for f in files]
            for future in as_completed(futures):
                future.result()
