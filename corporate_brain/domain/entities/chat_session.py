"""Domain entity describing a saved, named conversation."""

from dataclasses import dataclass, field
from datetime import datetime

from domain.entities.message import Message


@dataclass
class ChatSession:
    """A saved conversation: a name, its messages and when it was created."""

    id: str
    name: str
    messages: list[Message] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
