"""Postgres-backed implementation of the session repository."""

import json
import logging
import uuid

import psycopg
from psycopg.rows import dict_row

from domain.entities.chat_session import ChatSession
from domain.entities.message import Message, MessageSource
from domain.interfaces.session_repository import SessionRepository

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message_index INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    sources JSONB NOT NULL DEFAULT '[]'::jsonb
);

-- Existing installs created before sources tracking (CB-013 message-level
-- sources) won't have the column; adding it after the fact is idempotent
-- and safe to run on every startup.
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS sources JSONB NOT NULL DEFAULT '[]'::jsonb;

-- Per-message token usage (nullable: some LLM providers, e.g. GitHub Models,
-- don't report usage during streaming, so a turn can legitimately have no
-- token count). Added after the fact for the same reason as ``sources``
-- above — idempotent, safe on every startup.
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS input_tokens INTEGER;
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS output_tokens INTEGER;
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS total_tokens INTEGER;

CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
"""


def _sources_to_json(sources: list[MessageSource]) -> str:
    return json.dumps(
        [
            {
                "citation_number": source.citation_number,
                "document_name": source.document_name,
                "snippet": source.snippet,
            }
            for source in sources
        ]
    )


def _sources_from_json(raw: object) -> list[MessageSource]:
    # psycopg already decodes JSONB into Python lists/dicts, but accept a
    # raw string too in case a future driver/config change stops doing that.
    data = json.loads(raw) if isinstance(raw, str) else (raw or [])
    return [
        MessageSource(
            citation_number=item["citation_number"],
            document_name=item["document_name"],
            snippet=item["snippet"],
        )
        for item in data
    ]


class PostgresSessionRepository(SessionRepository):
    """Persists named conversations in Postgres (two tables: sessions, messages)."""

    def __init__(self, connection_string: str) -> None:
        self._connection_string = connection_string
        self._ensure_schema()

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(self._connection_string, row_factory=dict_row)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(_SCHEMA)

    def save(self, session_id: str, name: str, messages: list[Message]) -> ChatSession:
        session_uuid = session_id or str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO chat_sessions (id, name, updated_at)
                VALUES (%s, %s, now())
                ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, updated_at = now()
                """,
                (session_uuid, name),
            )
            conn.execute("DELETE FROM chat_messages WHERE session_id = %s", (session_uuid,))
            if messages:
                # ``executemany`` is a Cursor method in psycopg 3, not a
                # Connection method (unlike psycopg2) — a bare ``conn.executemany``
                # raises AttributeError and silently fails the whole save.
                with conn.cursor() as cur:
                    cur.executemany(
                        """
                        INSERT INTO chat_messages
                            (session_id, message_index, role, content, sources,
                             input_tokens, output_tokens, total_tokens)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        [
                            (
                                session_uuid,
                                index,
                                message.role,
                                message.content,
                                _sources_to_json(message.sources),
                                message.input_tokens,
                                message.output_tokens,
                                message.total_tokens,
                            )
                            for index, message in enumerate(messages)
                        ],
                    )
            row = conn.execute(
                "SELECT id, name, created_at, updated_at FROM chat_sessions WHERE id = %s",
                (session_uuid,),
            ).fetchone()
        logger.info("Saved session '%s' (%d messages)", session_uuid, len(messages))
        return ChatSession(
            id=str(row["id"]),
            name=row["name"],
            messages=list(messages),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_sessions(self) -> list[ChatSession]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, name, created_at, updated_at FROM chat_sessions "
                "ORDER BY updated_at DESC"
            ).fetchall()
        return [
            ChatSession(
                id=str(row["id"]),
                name=row["name"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def load(self, session_id: str) -> ChatSession | None:
        with self._connect() as conn:
            session_row = conn.execute(
                "SELECT id, name, created_at, updated_at FROM chat_sessions WHERE id = %s",
                (session_id,),
            ).fetchone()
            if session_row is None:
                return None
            message_rows = conn.execute(
                "SELECT role, content, sources, input_tokens, output_tokens, total_tokens "
                "FROM chat_messages WHERE session_id = %s ORDER BY message_index ASC",
                (session_id,),
            ).fetchall()
        return ChatSession(
            id=str(session_row["id"]),
            name=session_row["name"],
            messages=[
                Message(
                    role=r["role"],
                    content=r["content"],
                    sources=_sources_from_json(r["sources"]),
                    input_tokens=r["input_tokens"],
                    output_tokens=r["output_tokens"],
                    total_tokens=r["total_tokens"],
                )
                for r in message_rows
            ],
            created_at=session_row["created_at"],
            updated_at=session_row["updated_at"],
        )

    def delete(self, session_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM chat_sessions WHERE id = %s", (session_id,))
        logger.info("Deleted session '%s'", session_id)

    def rename(self, session_id: str, name: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE chat_sessions SET name = %s, updated_at = now() WHERE id = %s",
                (name, session_id),
            )
