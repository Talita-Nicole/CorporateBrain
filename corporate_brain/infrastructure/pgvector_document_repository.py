"""Postgres/pgvector-backed implementation of the document repository.

Replaces the previous ChromaDB store so the whole application needs a single
database (Postgres) for both relational data (chat sessions) and vector
search. Vectors live in the ``langchain_pg_embedding`` / ``langchain_pg_collection``
tables created and managed by ``langchain_postgres.PGVector``.

Distance note: PGVector's default space is **cosine** (distance = 1 - cosine
similarity, range 0..2), unlike the old Chroma store whose default was L2.
The relevance threshold that gates low-quality chunks out of the answer
context (``AnswerQuestion.max_relevant_distance``) is calibrated for cosine
distance and is env-overridable — see ``composition.build_dependencies`` and
``MAX_RELEVANT_DISTANCE`` in ``answer_question``.
"""

import logging
from typing import Any

import psycopg
from langchain_core.documents import Document as LangChainDocument
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_postgres import PGVector

from domain.interfaces.document_repository import DocumentRepository
from domain.interfaces.embedder import Embedder

logger = logging.getLogger(__name__)

COLLECTION_NAME = "corporate_knowledge"


class PgVectorDocumentRepository(DocumentRepository):
    """Stores and retrieves document chunks using Postgres + pgvector.

    ``connection_url`` is a SQLAlchemy URL (``postgresql+psycopg://...``) used
    by ``PGVector``. ``conninfo`` is a libpq keyword string used for the few
    metadata queries (list sources, sample texts, delete by source) that
    PGVector does not expose directly and are simplest to run as plain SQL
    against the embedding table.
    """

    def __init__(
        self,
        embedder: Embedder,
        connection_url: str,
        conninfo: str,
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        self._conninfo = conninfo
        self._collection_name = collection_name
        self._store = PGVector(
            embeddings=embedder.as_langchain_embeddings(),
            collection_name=collection_name,
            connection=connection_url,
            use_jsonb=True,
        )

    def add_documents(self, chunks: list[LangChainDocument]) -> None:
        if not chunks:
            return
        self._store.add_documents(chunks)
        logger.info("Indexed %d chunks into %s", len(chunks), self._collection_name)

    def as_retriever(self, **search_kwargs: Any) -> VectorStoreRetriever:
        return self._store.as_retriever(**search_kwargs)

    def similarity_search_with_score(
        self, query: str, k: int, filter: dict | None = None
    ) -> list[tuple[LangChainDocument, float]]:
        return self._store.similarity_search_with_score(query, k=k, filter=filter)

    def list_indexed_sources(self) -> list[str]:
        rows = self._query(
            """
            SELECT DISTINCT e.cmetadata->>'source' AS source
            FROM langchain_pg_embedding e
            JOIN langchain_pg_collection c ON e.collection_id = c.uuid
            WHERE c.name = %s AND e.cmetadata->>'source' IS NOT NULL
            ORDER BY source
            """,
            (self._collection_name,),
        )
        return [row[0] for row in rows if row[0]]

    def sample_texts(self, limit: int, sources: list[str] | None = None) -> list[str]:
        params: list[Any] = [self._collection_name]
        source_clause = ""
        if sources:
            source_clause = "AND e.cmetadata->>'source' = ANY(%s)"
            params.append(list(sources))
        params.append(limit)
        rows = self._query(
            f"""
            SELECT e.document
            FROM langchain_pg_embedding e
            JOIN langchain_pg_collection c ON e.collection_id = c.uuid
            WHERE c.name = %s {source_clause}
            LIMIT %s
            """,
            tuple(params),
        )
        return [row[0] for row in rows if row[0]]

    def delete_by_source(self, source: str) -> None:
        with psycopg.connect(self._conninfo) as conn:
            conn.execute(
                """
                DELETE FROM langchain_pg_embedding
                WHERE collection_id = (
                    SELECT uuid FROM langchain_pg_collection WHERE name = %s
                )
                AND cmetadata->>'source' = %s
                """,
                (self._collection_name, source),
            )
        logger.info(
            "Deleted all chunks for source '%s' from %s", source, self._collection_name
        )

    def _query(self, sql: str, params: tuple) -> list[tuple]:
        """Run a read-only query, tolerating a not-yet-created schema.

        Before the first document is indexed, PGVector may not have created
        its tables yet; treat a missing table as an empty store rather than
        an error so the sidebar/starter flows degrade gracefully.
        """
        try:
            with psycopg.connect(self._conninfo) as conn:
                return conn.execute(sql, params).fetchall()
        except psycopg.errors.UndefinedTable:
            return []
