from pathlib import Path
import torch
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.api.models.Collection import Collection
from tqdm import tqdm

from src.app.configuration.vector_db import STEmbeddingFunction  # your embedding wrapper
from src.app.configuration.config import VECTORSTORE_PATH

# --- Initialize embedding model (must match original) ---
model = SentenceTransformer(
                model_name_or_path="BAAI/bge-small-en-v1.5",
                device="cuda" if torch.cuda.is_available() else "cpu"
            )
embedding_fn = STEmbeddingFunction(model)

# --- Old embedded client ---
old_client = chromadb.Client(
    settings=chromadb.config.Settings(
        persist_directory=str(VECTORSTORE_PATH),
        is_persistent=True,
        anonymized_telemetry=False
    )
)

# --- New Docker client ---
new_client = chromadb.HttpClient(
    host="localhost",
    port=8001,
    settings=chromadb.config.Settings(anonymized_telemetry=False)
)

# --- Migration function with progress bar ---
def migrate_collection(source: Collection, target: Collection, batch_size: int = 100):
    # Get total number of vectors in the collection
    total_vectors = source.count()
    print(f"Total vectors in '{source.name}': {total_vectors}")

    offset = 0
    batch_texts, batch_metas, batch_ids = [], [], []

    with tqdm(total=total_vectors, desc=f"Migrating '{source.name}'") as pbar:
        while offset < total_vectors:
            results = source.get(include=["documents", "metadatas", "embeddings"],
                                 limit=batch_size,
                                 offset=offset)
            if not results["ids"]:
                break

            for doc, meta, _id in zip(results["documents"], results["metadatas"], results["ids"]):
                summary = meta.get("summary", "")
                truncated_code = meta.get("truncated_code", doc)

                # Build new document text
                new_text = (
                    f"Type: {meta.get('node_type', 'unknown')}\n"
                    f"Name: {meta.get('node_name', 'unknown')}\n"
                    f"Summary: {summary}\n\n"
                    f"Code:\n{truncated_code}"
                )
                batch_texts.append(new_text)

                new_meta = {
                    "project": meta.get("project", "unknown"),
                    "file_path": meta.get("file_path", "unknown"),
                    "language": meta.get("language", "unknown"),
                    "node_type": meta.get("node_type", "unknown"),
                    "node_name": meta.get("node_name", "unknown"),
                    "symbols_defined": meta.get("symbols_defined", ""),
                }
                batch_metas.append(new_meta)
                batch_ids.append(_id)

                if len(batch_texts) >= batch_size:
                    target.add(documents=batch_texts, metadatas=batch_metas, ids=batch_ids)
                    pbar.update(len(batch_texts))
                    batch_texts, batch_metas, batch_ids = [], [], []

            offset += batch_size

        # Insert any remaining vectors
        if batch_texts:
            target.add(documents=batch_texts, metadatas=batch_metas, ids=batch_ids)
            pbar.update(len(batch_texts))


# --- Migrate collections ---
for name in ["code", "docs"]:
    print(f"🔄 Migrating collection: {name}")
    old_col = old_client.get_collection(name=name, embedding_function=embedding_fn)
    new_col = new_client.get_or_create_collection(
        name=name,
        embedding_function=embedding_fn,
        metadata=old_col.metadata
    )
    migrate_collection(old_col, new_col)

print("✅ Migration complete")
