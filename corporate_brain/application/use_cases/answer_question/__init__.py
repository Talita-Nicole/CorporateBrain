"""Use case: retrieve context and generate a source-cited answer."""

from .answer_question import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    MAX_RELEVANT_DISTANCE,
    REFUSAL_MESSAGE_EN,
    RETRIEVER_TOP_K,
    STARTER_SAMPLE_SIZE,
    AnswerQuestion,
)
from .models import AnswerResult, RetrievalDebug, RetrievedChunk, Source, StreamingAnswer
from .prompt import (
    ENGLISH_CONFIDENCE_THRESHOLD,
    ENGLISH_LANGUAGE_CODE,
    ENGLISH_LANGUAGE_LABEL,
    MAX_SUGGESTIONS,
    PORTUGUESE_LANGUAGE_LABEL,
    SUGGESTIONS_MARKER,
)

__all__ = [
    "AnswerQuestion",
    "AnswerResult",
    "RetrievalDebug",
    "RetrievedChunk",
    "Source",
    "StreamingAnswer",
    "DEFAULT_CHUNK_OVERLAP",
    "DEFAULT_CHUNK_SIZE",
    "ENGLISH_CONFIDENCE_THRESHOLD",
    "ENGLISH_LANGUAGE_CODE",
    "ENGLISH_LANGUAGE_LABEL",
    "MAX_RELEVANT_DISTANCE",
    "MAX_SUGGESTIONS",
    "PORTUGUESE_LANGUAGE_LABEL",
    "REFUSAL_MESSAGE_EN",
    "RETRIEVER_TOP_K",
    "STARTER_SAMPLE_SIZE",
    "SUGGESTIONS_MARKER",
]
