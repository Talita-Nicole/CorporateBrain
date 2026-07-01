"""
Inspect the ChromaDB collection without requiring LLM credentials.

Usage (from corporate_brain/ directory):
    python scripts/inspect_chroma.py
    python scripts/inspect_chroma.py --limit 20
    python scripts/inspect_chroma.py --source report.pdf
    python scripts/inspect_chroma.py --search "some keyword"
"""

import argparse
import sys
import os

# Allow running from corporate_brain/ or from the repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb

PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "corporate_knowledge"


def get_collection():
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    try:
        return client.get_collection(COLLECTION_NAME)
    except Exception:
        print(f"Collection '{COLLECTION_NAME}' not found in '{PERSIST_DIR}'.")
        print("Make sure you are running from the corporate_brain/ directory and that documents have been ingested.")
        sys.exit(1)


def cmd_stats(collection):
    count = collection.count()
    print(f"Collection : {COLLECTION_NAME}")
    print(f"Persist dir: {PERSIST_DIR}")
    print(f"Total chunks: {count}")

    if count == 0:
        print("No documents indexed yet.")
        return

    all_meta = collection.get(include=["metadatas"])["metadatas"]
    sources = sorted({m.get("source", "<unknown>") for m in all_meta})
    print(f"\nIndexed sources ({len(sources)}):")
    for src in sources:
        chunk_count = sum(1 for m in all_meta if m.get("source") == src)
        print(f"  {src}  ({chunk_count} chunks)")


def cmd_list(collection, limit, source_filter):
    where = {"source": source_filter} if source_filter else None
    kwargs = {"limit": limit, "include": ["documents", "metadatas"]}
    if where:
        kwargs["where"] = where

    result = collection.get(**kwargs)
    ids = result["ids"]
    docs = result["documents"]
    metas = result["metadatas"]

    if not ids:
        print("No chunks found" + (f" for source '{source_filter}'" if source_filter else "") + ".")
        return

    print(f"Showing {len(ids)} chunk(s)" + (f" from '{source_filter}'" if source_filter else "") + ":\n")
    for i, (doc_id, doc, meta) in enumerate(zip(ids, docs, metas), 1):
        print(f"--- Chunk {i} ---")
        print(f"ID    : {doc_id}")
        print(f"Meta  : {meta}")
        preview = doc[:300].replace("\n", " ")
        print(f"Text  : {preview}{'...' if len(doc) > 300 else ''}")
        print()


def cmd_search(collection, query, limit):
    results = collection.query(
        query_texts=[query],
        n_results=min(limit, collection.count()),
        include=["documents", "metadatas", "distances"],
    )
    ids = results["ids"][0]
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    print(f"Top {len(ids)} result(s) for query: \"{query}\"\n")
    for i, (doc_id, doc, meta, dist) in enumerate(zip(ids, docs, metas, distances), 1):
        print(f"--- Result {i} (distance: {dist:.4f}) ---")
        print(f"ID    : {doc_id}")
        print(f"Meta  : {meta}")
        preview = doc[:300].replace("\n", " ")
        print(f"Text  : {preview}{'...' if len(doc) > 300 else ''}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Inspect the CorporateBrain ChromaDB collection.")
    parser.add_argument("--limit", type=int, default=10, help="Max chunks to show (default: 10)")
    parser.add_argument("--source", type=str, default=None, help="Filter by source filename")
    parser.add_argument("--search", type=str, default=None, help="Full-text similarity search (no embeddings needed)")
    args = parser.parse_args()

    collection = get_collection()

    # Always print stats
    cmd_stats(collection)

    if args.search:
        print()
        cmd_search(collection, args.search, args.limit)
    else:
        print()
        cmd_list(collection, args.limit, args.source)


if __name__ == "__main__":
    main()
