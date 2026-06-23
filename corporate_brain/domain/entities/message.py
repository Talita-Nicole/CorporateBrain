"""Domain entity describing a single conversation message."""

from dataclasses import dataclass


@dataclass
class Message:
    """A message exchanged in the chat. ``role`` is ``user`` or ``assistant``."""

    role: str
    content: str
