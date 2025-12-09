import hashlib
from pathlib import Path

from src.app.configuration.db import VectorDB
from src.app.services.detectors.parsers import load_parser
from src.app.models.code_classifier.code_classifier import CodeClassifier
from src.app.services.llm_service import summarize_code

SUPPORTED_CODE_EXTENSIONS = [".py", ".java"]
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
    def __init__(self, db: VectorDB, code_classifier: CodeClassifier, batch_size: int = 16):
        self.batch_size = batch_size
        self.code_classifier = code_classifier
        self.db = db

    def _extract_nodes(self, language: str, content: str, max_node_lines: int = 300):
        """
        Extract AST nodes across different languages.
        Uses a parent stack to correctly track nesting.
        """

        if language not in NODE_TYPES:
            print(f"Language '{language}' not supported for AST parsing.")
            return []

        parser = load_parser(language)
        tree = parser.parse(bytes(content, "utf8"))
        root = tree.root_node

        target_types = NODE_TYPES[language]
        lines = content.splitlines()
        nodes = []

        def extract_code(start, end):
            return "\n".join(lines[start - 1:end])

        # Better identifier extraction per language
        def get_node_name(node):
            for child in node.children:
                # Python + Java identifiers
                if child.type in {"identifier", "scoped_type_identifier",
                                  "type_identifier", "field_identifier"}:
                    try:
                        return child.text.decode("utf-8")
                    except:
                        return None
            return None

        parent_stack = []  # holds names of class/interface/enclosing functions

        def walk(node):
            pushed = False

            if node.type in target_types:
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                line_count = end_line - start_line + 1

                # enforce max size
                if line_count > max_node_lines:
                    code = extract_code(start_line, start_line + max_node_lines - 1)
                    code += "\n# [TRUNCATED…]"
                else:
                    code = extract_code(start_line, end_line)

                node_name = get_node_name(node)
                normalized_type = target_types[node.type]

                current_parent = parent_stack[-1] if parent_stack else None

                # Add node
                nodes.append({
                    "code": code,
                    "start_line": start_line,
                    "end_line": end_line,
                    "node_type": normalized_type,
                    "node_name": node_name,
                    "parent": current_parent
                })

                # push to parent stack
                if node_name:
                    parent_stack.append(node_name)
                    pushed = True

            # walk children
            for child in node.children:
                walk(child)

            # pop on exit
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

        language = self.code_classifier.predict(content)
        nodes = self._extract_nodes(language, content)

        batch_texts = []
        batch_metadatas = []
        batch_ids = []

        for i, node in enumerate(nodes):
            node_code = node["code"]
            node_id = f"{file_path}:{node.get('node_name', i)}:{node['start_line']}"
            node_hash = compute_node_hash(node_code)
            summary = summarize_code(node_code)

            metadata = {
                "source": "code",
                "project": project_name,
                "file_path": str(file_path),
                "start_line": node["start_line"],
                "end_line": node["end_line"],
                "language": language,
                "node_type": node["node_type"],
                "node_name": node.get("node_name") or "",
                "parent": node.get("parent") or "",
                "node_hash": node_hash,
                "summary": summary
            }

            batch_texts.append(node_code)
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
                batch_texts = []
                batch_metadatas = []
                batch_ids = []

        # Insert any remaining chunks
        if batch_texts:
            self.db.insert(
                collection=self.db.code,
                texts=batch_texts,
                metadatas=batch_metadatas,
                ids=batch_ids
            )

    def ingest_codebase(self, folder: Path, project_name: str):
        for file_path in folder.rglob("*"):
            # Skip ignored folders
            if any(ignored in file_path.parts for ignored in IGNORE_CODE_FOLDERS):
                continue

            if file_path.is_file() and file_path.suffix in SUPPORTED_CODE_EXTENSIONS:
                print(f"Processing: {file_path}")
                self.ingest_code_file(file_path, project_name)