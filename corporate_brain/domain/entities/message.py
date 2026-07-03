"""Domain entities describing a single conversation message and its sources."""

from dataclasses import dataclass, field


@dataclass
class MessageSource:
    """A document excerpt that supported an assistant message's answer.

    Mirrors ``application.use_cases.answer_question.Source`` — kept as a
    separate domain-level type (rather than importing that one) because
    ``domain/`` must not depend on ``application/``. ``AnswerQuestion``
    already numbers citations for display; this is the persisted form of
    the same data, attached to the ``Message`` it belongs to.
    """

    citation_number: int
    document_name: str
    snippet: str


@dataclass
class Message:
    """A message exchanged in the chat. ``role`` is ``user`` or ``assistant``.

    ``sources`` is only ever populated on assistant messages that cited
    something — empty for user messages and for answers with no citations.

    ``input_tokens``/``output_tokens``/``total_tokens`` are only ever
    populated on assistant messages, and only when the language model
    provider reported usage for that turn (some providers omit it during
    streaming) — ``None`` otherwise. Carried on the message itself (not a
    single shared/global value) so each turn keeps its own token count
    permanently, including after reloading a saved conversation from
    Postgres.
    """

    role: str
    content: str
    sources: list[MessageSource] = field(default_factory=list)
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
