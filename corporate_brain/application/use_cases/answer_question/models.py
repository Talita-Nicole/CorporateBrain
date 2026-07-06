"""Data types shared across the answer-question use case."""

from dataclasses import dataclass
from typing import Iterator


@dataclass
class Source:
    """A document excerpt that supported an answer."""

    citation_number: int
    document_name: str
    snippet: str


@dataclass
class RetrievedChunk:
    """One retrieved chunk and its raw distance score, for the debug panel."""

    document_name: str
    distance: float
    passed_threshold: bool
    snippet: str


@dataclass
class RetrievalDebug:
    """Pipeline metadata for one answer: retrieval, chunking config, models, tokens."""

    retrieved_chunks: list[RetrievedChunk]
    top_k: int
    max_relevant_distance: float
    chunk_size: int
    chunk_overlap: int
    embedding_model: str
    chat_model: str
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None


@dataclass
class AnswerResult:
    """The generated answer together with its supporting sources."""

    answer: str
    sources: list[Source]
    suggested_questions: list[str]
    refused: bool = False
    retrieval_debug: RetrievalDebug | None = None


class StreamingAnswer:
    """Wraps a token stream: consume ``.tokens()`` to render progressively,
    then read ``.result`` for the post-processed ``AnswerResult``.

    ``.result`` is ``None`` until ``.tokens()`` has been fully exhausted —
    citation renumbering and follow-up extraction need the complete text.
    """

    def __init__(self) -> None:
        self.result: AnswerResult | None = None
        self._token_generator: Iterator[str] | None = None

    def tokens(self) -> Iterator[str]:
        if self._token_generator is None:
            return iter(())
        yield from self._token_generator
