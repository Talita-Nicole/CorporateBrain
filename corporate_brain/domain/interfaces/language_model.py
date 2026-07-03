"""Contract for the chat language model used to generate answers."""

from abc import ABC, abstractmethod
from typing import Iterator

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessageChunk


class LanguageModel(ABC):
    """Provides the chat model used by the question-answering use case."""

    @abstractmethod
    def as_langchain_chat_model(self) -> BaseChatModel:
        """Return the underlying LangChain chat model."""

    @abstractmethod
    def invoke(self, prompt: str) -> str:
        """Generate a direct completion for ``prompt`` and return the text."""

    @abstractmethod
    def stream(self, messages: list) -> Iterator[AIMessageChunk]:
        """Stream the chat completion for ``messages`` as incremental chunks.

        Chunks are summable (``chunk + chunk``) into a single ``AIMessage``
        with the assembled ``content`` and ``usage_metadata`` once the stream
        is exhausted — used by ``AnswerQuestion`` to render progressively
        while still running citation/follow-up post-processing on the full
        text at the end.
        """
