"""Contract for loading a file and splitting it into indexable chunks."""

from abc import ABC, abstractmethod

from langchain_core.documents import Document as LangChainDocument


class DocumentLoader(ABC):
    """Reads a file from disk and returns chunked, metadata-enriched documents."""

    @abstractmethod
    def load_and_split(
        self, file_path: str, file_name: str
    ) -> list[LangChainDocument]:
        """Load ``file_path`` and return chunks tagged with ``file_name`` as source."""
