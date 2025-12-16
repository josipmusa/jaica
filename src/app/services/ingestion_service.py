import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from src.app.configuration.db import VectorDB
from src.app.services.detectors.parsers import load_parser
from src.app.models.code_classifier.code_classifier import CodeClassifier
from src.app.services.graph_db_service import GraphDBService
from src.app.services.llm_service import summarize_code


SUPPORTED_CODE_EXTENSIONS = {
    ".py": "Python",
    ".java": "Java",
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
    },
}


def compute_node_hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


class IngestionService:
    def __init__(
        self,
        db: VectorDB,
        code_classifier: CodeClassifier,
        graph_db_service: GraphDBService,
        batch_size: int = 16,
    ):
        self.batch_size = batch_size
        self.code_classifier = code_classifier
        self.db = db
        self.graph_db_service = graph_db_service

    # -------------------------
    # AST EXTRACTION
    # -------------------------
    def _extract_nodes(
        self,
        language: str,
        content: str,
        file_path: str,
        max_node_lines: int = 300,
    ) -> Dict:
        language = language.lower()
        if language not in NODE_TYPES:
            return {}

        try:
            parser = load_parser(language)
            tree = parser.parse(bytes(content, "utf8"))
        except Exception as e:
            print(f"Failed to parse {file_path}: {e}")
            return {}

        root = tree.root_node
        target_types = NODE_TYPES[language]
        lines = content.splitlines()

        nodes: List[Dict] = []
        calls: List[Tuple[str, str, str]] = []
        usages: List[Tuple[str, str, str]] = []
        defined_symbols: Dict[str, List[str]] = {}

        parent_stack: List[str] = []

        def extract_code(start: int, end: int) -> str:
            return "\n".join(lines[start - 1 : end])

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
                    except Exception:
                        return None
            return None

        def walk(node):
            current_node_id = None
            pushed = False

            # ---- CODE NODE ----
            if node.type in target_types:
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1

                full_code = extract_code(start_line, end_line)
                truncated_code = extract_code(
                    start_line, min(end_line, start_line + max_node_lines - 1)
                )

                node_name = get_node_name(node) or f"unnamed_{start_line}"
                node_id = f"{file_path}:{node_name}:{start_line}"
                parent_id = parent_stack[-1] if parent_stack else None

                nodes.append(
                    {
                        "node_id": node_id,
                        "node_type": target_types[node.type],
                        "node_name": node_name,
                        "start_line": start_line,
                        "end_line": end_line,
                        "parent_id": parent_id,
                        "full_code": full_code,
                        "truncated_code": truncated_code,
                    }
                )

                defined_symbols[node_id] = [node_name]
                parent_stack.append(node_id)
                current_node_id = node_id
                pushed = True

            # ---- CALLS ----
            if current_node_id:
                if language == "python" and node.type == "call":
                    fn = node.child_by_field_name("function")
                    if fn:
                        calls.append(
                            (
                                current_node_id,
                                fn.text.decode("utf-8"),
                                "python_call",
                            )
                        )

                if language == "java" and node.type == "method_invocation":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        calls.append(
                            (
                                current_node_id,
                                name_node.text.decode("utf-8"),
                                "java_method_invocation",
                            )
                        )

            # ---- USAGES ----
            if current_node_id:
                if language == "python" and node.type == "identifier":
                    usages.append(
                        (
                            current_node_id,
                            node.text.decode("utf-8"),
                            "python_identifier",
                        )
                    )

                if language == "java" and node.type in {
                    "type_identifier",
                    "scoped_type_identifier",
                    "field_access",
                }:
                    usages.append(
                        (
                            current_node_id,
                            node.text.decode("utf-8"),
                            "java_symbol_usage",
                        )
                    )

            for child in node.children:
                walk(child)

            if pushed:
                parent_stack.pop()

        walk(root)

        return {
            "nodes": nodes,
            "calls": calls,
            "usages": usages,
            "defined_symbols": defined_symbols,
        }

    # -------------------------
    # INGEST FILE
    # -------------------------
    def ingest_code_file(self, file_path: Path, project_name: str):
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"Skipping {file_path}: {e}")
            return

        language = SUPPORTED_CODE_EXTENSIONS.get(file_path.suffix) or self.code_classifier.predict(
            content
        )

        extracted = self._extract_nodes(language, content, str(file_path))
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

        batch_texts, batch_metas, batch_ids = [], [], []

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

            # ---- VECTOR ----
            batch_texts.append(
                f"Type: {node['node_type']}\n"
                f"Name: {node['node_name']}\n"
                f"Summary: {summary}\n\n"
                f"Code:\n{node['truncated_code']}"
            )
            batch_metas.append(
                {
                    "project": project_name,
                    "file_path": str(file_path),
                    "language": language,
                    "node_type": node["node_type"],
                    "node_name": node["node_name"],
                    "symbols_defined": extracted["defined_symbols"].get(node_id, []),
                }
            )
            batch_ids.append(node_id)

            if len(batch_texts) >= self.batch_size:
                self.db.insert(self.db.code, batch_texts, batch_metas, batch_ids)
                batch_texts, batch_metas, batch_ids = [], [], []

        if batch_texts:
            self.db.insert(self.db.code, batch_texts, batch_metas, batch_ids)

        # ---- CALLS ----
        for caller_id, callee_symbol, source in extracted["calls"]:
            candidates = self.graph_db_service.resolve_symbol(callee_symbol, project_name)
            if candidates:
                callee_id = candidates[0]["node_id"]
                self.graph_db_service.link(
                    caller_id,
                    callee_id,
                    "CALLS",
                    {"source": source, "confidence": 0.9},
                )

        # ---- USAGES ----
        for user_id, symbol, source in extracted["usages"]:
            candidates = self.graph_db_service.resolve_symbol(symbol, project_name)
            if candidates:
                target_id = candidates[0]["node_id"]
                self.graph_db_service.link(
                    user_id,
                    target_id,
                    "USES",
                    {"source": source, "confidence": 0.7},
                )

    # -------------------------
    # INGEST CODEBASE
    # -------------------------
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
