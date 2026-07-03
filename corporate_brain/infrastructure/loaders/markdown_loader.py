"""Markdown loader — treats the file as plain text, no syntax stripping.

Markdown is already human-readable as-is (headings, lists, emphasis markers
don't meaningfully obscure the content for retrieval/embedding purposes), so
this reuses ``TextLoader`` directly rather than stripping `#`/`*`/etc. — the
simplest approach that still indexes useful, readable content.
"""

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document as LangChainDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter


class MarkdownLoader:
    """Loads a Markdown file as plain text and splits it into chunks."""

    def __init__(self, splitter: RecursiveCharacterTextSplitter) -> None:
        self._splitter = splitter

    def load(self, file_path: str) -> list[LangChainDocument]:
        return TextLoader(file_path, encoding="utf-8").load_and_split(self._splitter)
