"""Domain entity describing a stored document."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    """A corporate document available to the knowledge base."""

    id: str
    name: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
