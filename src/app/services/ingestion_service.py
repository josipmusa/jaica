from pathlib import Path
from src.app.configuration.db import db

CODE_EXTENSIONS = {".py" : "python", ".js": "javascript", ".java": "java", ".ts": "typescript", ".cpp": "c++", ".c": "c", ".cs": "csharp"}
IGNORE_CODE_FOLDERS = {".git", "node_modules", "__pycache__", "venv", ".idea", "docker", ".mvn"}

class IngestionService:
    def __init__(self, code_chunk_size: int = 50, code_overlap: int = 10,
                 doc_chunk_size: int = 500, doc_overlap: int = 50,
                 batch_size: int = 16):
        self.code_chunk_size = code_chunk_size
        self.code_overlap = code_overlap
        self.doc_chunk_size = doc_chunk_size
        self.doc_overlap = doc_overlap
        self.batch_size = batch_size

    def ingest_code_file(self, file_path: Path, project_name: str):
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"Skipping {file_path}: {e}")
            return

        lines = content.splitlines()
        language = CODE_EXTENSIONS.get(file_path.suffix, "unknown")
        total_lines = len(lines)
        start = 0
        chunk_id = 0

        batch_texts = []
        batch_metadatas = []
        batch_ids = []

        while start < total_lines:
            end = min(start + self.code_chunk_size, total_lines)
            chunk_text = "\n".join(lines[start:end])

            metadata = {
                "source": "code",
                "project": project_name,
                "file_path": str(file_path),
                "start_line": start + 1,
                "end_line": end,
                "language": language
            }

            batch_texts.append(chunk_text)
            batch_metadatas.append(metadata)
            batch_ids.append(f"{file_path}:{chunk_id}")

            chunk_id += 1
            start += self.code_chunk_size - self.code_overlap

            # If batch is full, insert it
            if len(batch_texts) >= self.batch_size:
                db.insert(
                    collection=db.code,
                    texts=batch_texts,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
                batch_texts = []
                batch_metadatas = []
                batch_ids = []

        # Insert any remaining chunks
        if batch_texts:
            db.insert(
                collection=db.code,
                texts=batch_texts,
                metadatas=batch_metadatas,
                ids=batch_ids
            )

    def ingest_codebase(self, folder: Path, project_name: str):
        for file_path in folder.rglob("*"):
            # Skip ignored folders
            if any(ignored in file_path.parts for ignored in IGNORE_CODE_FOLDERS):
                continue

            if file_path.is_file() and file_path.suffix in CODE_EXTENSIONS:
                print(f"Processing: {file_path}")
                self.ingest_code_file(file_path, project_name)