"""Contract for the chat language model used to generate answers."""

from abc import ABC, abstractmethod

from langchain_core.language_models import BaseChatModel


class LanguageModel(ABC):
    """Provides the chat model used by the question-answering use case."""

    @abstractmethod
    def as_langchain_chat_model(self) -> BaseChatModel:
        """Return the underlying LangChain chat model."""

    @abstractmethod
    def invoke(self, prompt: str) -> str:
        """Generate a direct completion for ``prompt`` and return the text."""
