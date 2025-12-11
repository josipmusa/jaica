import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Optional

from src.app.configuration.db import VectorDB
from src.app.services.detectors.parsers import load_parser
from src.app.models.code_classifier.code_classifier import CodeClassifier
from src.app.services.graph_db_service import GraphDBService
from src.app.services.llm_service import summarize_code

SUPPORTED_CODE_EXTENSIONS = {
    ".py": "Python",
    ".java": "Java"
}
IGNORE_CODE_FOLDERS = {".git", "__pycache__", "venv", ".idea", "docker", ".mvn"}
NODE_TYPES = {
    "python": {
        "class_definition": "class",
        "function_definition": "function",
    },
    "java": {
        "class_declaration": "class",
        "interface_declaration": "interface",
        "enum_declaration": "enum",
        "method_declaration": "method",
        "constructor_declaration": "constructor",
    }
}

def compute_node_hash(node_code: str) -> str:
    return hashlib.sha256(node_code.encode("utf-8")).hexdigest()

class IngestionService:
    def __init__(self, db: VectorDB, code_classifier: CodeClassifier, graph_db_service: GraphDBService, batch_size: int = 16):
        self.batch_size = batch_size
        self.code_classifier = code_classifier
        self.db = db
        self.graph_db_service = graph_db_service

    def _extract_nodes(
        self, language: str, content: str, file_path: str, max_node_lines: int = 300
    ) -> List[Dict]:
        """
        Extract AST nodes across different languages.
        Returns full code, truncated code, node_id, parent_id, etc.
        """
        language = language.lower()
        if language not in NODE_TYPES:
            print(f"Language '{language}' not supported for AST parsing.")
            return []

        try:
            parser = load_parser(language)
            tree = parser.parse(bytes(content, "utf8"))
        except Exception as e:
            print(f"Failed to parse {file_path}: {e}")
            return []

        root = tree.root_node
        target_types = NODE_TYPES[language]
        lines = content.splitlines()
        nodes = []
        parent_stack: List[Dict] = []

        def extract_code(start: int, end: int) -> str:
            return "\n".join(lines[start - 1:end])

        def get_node_name(node) -> Optional[str]:
            for child in node.children:
                if child.type in {
                    "identifier",
                    "scoped_type_identifier",
                    "type_identifier",
                    "field_identifier",
                }:
                    try:
                        return child.text.decode("utf-8")
                    except:
                        return None
            return None

        def walk(node):
            pushed = False
            if node.type in target_types:
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                line_count = end_line - start_line + 1

                full_code = extract_code(start_line, end_line)
                truncated_code = (
                    extract_code(start_line, start_line + max_node_lines - 1)
                    + ("\n# [TRUNCATED…]" if line_count > max_node_lines else "")
                )

                node_name = get_node_name(node) or f"unnamed_{start_line}"
                node_id = f"{file_path}:{node_name}:{start_line}"
                current_parent = parent_stack[-1]["node_id"] if parent_stack else None
                normalized_type = target_types[node.type]

                nodes.append(
                    {
                        "node_id": node_id,
                        "node_type": normalized_type,
                        "node_name": node_name,
                        "start_line": start_line,
                        "end_line": end_line,
                        "parent_id": current_parent,
                        "full_code": full_code,
                        "truncated_code": truncated_code,
                    }
                )

                parent_stack.append({"node_name": node_name, "node_id": node_id})
                pushed = True

            for child in node.children:
                walk(child)

            if pushed:
                parent_stack.pop()

        walk(root)
        return nodes

    def ingest_code_file(self, file_path: Path, project_name: str):
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"Skipping {file_path}: {e}")
            return

        print(f"Processing {file_path}")
        # Determine language: extension first, fallback to classifier
        language = None
        if file_path.suffix in SUPPORTED_CODE_EXTENSIONS:
            language = SUPPORTED_CODE_EXTENSIONS[file_path.suffix]
        if not language:
            language = self.code_classifier.predict(content)

        nodes = self._extract_nodes(language, content, str(file_path))
        if not nodes:
            return

        batch_texts, batch_metadatas, batch_ids = [], [], []

        for i, node in enumerate(nodes):
            node_id = node["node_id"]
            node_hash = compute_node_hash(node["full_code"])

            # Check graph for deduplication
            existing_node = self.graph_db_service.get_node(node_id)
            if existing_node and existing_node.get("node_hash") == node_hash:
                print(f"Skipping unchanged node: {node_id}")
                continue

            summary = summarize_code(node["full_code"])

            # Upsert node in graph
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
            )

            # Link parent if exists
            parent_id = node.get("parent_id")
            if parent_id:
                self.graph_db_service.link_parent(parent_id, node_id)

            metadata = {
                "source": "code",
                "project": project_name,
                "file_path": str(file_path),
                "start_line": node["start_line"],
                "end_line": node["end_line"],
                "language": language,
                "node_type": node["node_type"],
                "node_name": node["node_name"],
                "parent_id": parent_id or "",
                "node_hash": node_hash,
                "summary": summary,
            }
            embedding_text = (
                f"Type: {node['node_type']}\n"
                f"Name: {node['node_name']}\n"
                f"Parent: {metadata['parent_id']}\n"
                f"Summary: {summary}\n\n"
                f"Code:\n{node['truncated_code']}"
            )

            batch_texts.append(embedding_text)
            batch_metadatas.append(metadata)
            batch_ids.append(node_id)

            # If batch is full, insert it
            if len(batch_texts) >= self.batch_size:
                self.db.insert(
                    collection=self.db.code,
                    texts=batch_texts,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
                batch_texts, batch_metadatas, batch_ids = [], [], []

        # Insert any remaining chunks
        if batch_texts:
            self.db.insert(
                collection=self.db.code,
                texts=batch_texts,
                metadatas=batch_metadatas,
                ids=batch_ids
            )

    def ingest_codebase(self, folder: Path, project_name: str, max_workers: int = 2):
        files_to_process = [
            f for f in folder.rglob("*")
            if f.is_file() and f.suffix in SUPPORTED_CODE_EXTENSIONS
               and not any(ignored in f.parts for ignored in IGNORE_CODE_FOLDERS)
        ]

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.ingest_code_file, f, project_name): f for f in files_to_process}

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Error processing {futures[future]}: {e}")