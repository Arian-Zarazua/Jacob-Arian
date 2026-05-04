'''
Run from project root:

Build all knowledge subfolders:
    python -m scripts.build_rag_index

Build one specific subfolder:
    python -m scripts.build_rag_index --knowledge_subfolder "General RAG"
'''

from __future__ import annotations

import argparse
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

from src.rag_faiss_utils_pdf import (
    build_faiss_index,
    build_rag_chunks,
    save_faiss_index,
)


def build_one_knowledge_dir(knowledge_dir: Path, embedding_model: str) -> None:
    if not knowledge_dir.exists():
        raise FileNotFoundError(f"Knowledge directory not found: {knowledge_dir}")

    print(f"\nReading markdown files from: {knowledge_dir}")

    chunks = build_rag_chunks(knowledge_dir)

    if not chunks:
        print(f"Skipping {knowledge_dir} — no markdown chunks were created.")
        return

    print(f"Built {len(chunks)} chunks.")
    print(f"Creating embeddings with model: {embedding_model}")

    index, _ = build_faiss_index(
        chunks=chunks,
        embedding_model=embedding_model,
    )

    index_path, meta_path = save_faiss_index(
        knowledge_dir=knowledge_dir,
        index=index,
        chunks=chunks,
        embedding_model=embedding_model,
    )

    print("RAG index build complete.")
    print(f"Saved FAISS index   : {index_path}")
    print(f"Saved chunk metadata: {meta_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build and save FAISS RAG indexes from knowledge subfolders."
    )

    parser.add_argument(
        "--knowledge_dir",
        type=str,
        default="knowledge",
        help="Root directory containing RAG subfolders.",
    )

    parser.add_argument(
        "--knowledge_subfolder",
        type=str,
        default="",
        help="Optional subfolder inside knowledge_dir to build.",
    )

    parser.add_argument(
        "--embedding_model",
        type=str,
        default="text-embedding-3-small",
        help="Embedding model to use when creating vectors.",
    )

    args = parser.parse_args()

    knowledge_root = (PROJECT_ROOT / args.knowledge_dir).resolve()

    if not knowledge_root.exists():
        raise FileNotFoundError(f"Knowledge root not found: {knowledge_root}")

    if args.knowledge_subfolder:
        knowledge_dirs = [knowledge_root / args.knowledge_subfolder]
    else:
        knowledge_dirs = [
            path for path in knowledge_root.iterdir()
            if path.is_dir()
        ]

    if not knowledge_dirs:
        raise ValueError(f"No subfolders found inside: {knowledge_root}")

    for knowledge_dir in knowledge_dirs:
        build_one_knowledge_dir(
            knowledge_dir=knowledge_dir.resolve(),
            embedding_model=args.embedding_model,
        )


if __name__ == "__main__":
    main()