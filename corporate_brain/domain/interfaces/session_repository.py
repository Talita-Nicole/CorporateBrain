"""Contract for saving, listing, loading and deleting named chat sessions."""

from abc import ABC, abstractmethod

from domain.entities.chat_session import ChatSession
from domain.entities.message import Message


class SessionRepository(ABC):
    """Persists named conversations so they survive a page reload or restart."""

    @abstractmethod
    def save(self, session_id: str, name: str, messages: list[Message]) -> ChatSession:
        """Create or overwrite the session identified by ``session_id``.

        Returns the persisted ``ChatSession`` (with timestamps populated).
        """

    @abstractmethod
    def list_sessions(self) -> list[ChatSession]:
        """Return all saved sessions, most recently updated first.

        Returned sessions do not include their messages (list view only) —
        call ``load`` to fetch a specific session's full transcript.
        """

    @abstractmethod
    def load(self, session_id: str) -> ChatSession | None:
        """Return the session with its full message list, or ``None`` if missing."""

    @abstractmethod
    def delete(self, session_id: str) -> None:
        """Remove the session and its messages. No-op if it does not exist."""

    @abstractmethod
    def rename(self, session_id: str, name: str) -> None:
        """Update the display name of an existing session."""
