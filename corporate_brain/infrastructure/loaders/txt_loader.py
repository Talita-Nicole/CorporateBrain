"""Plain-text loader backed by LangChain's ``TextLoader``."""

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document as LangChainDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter


class TxtLoader:
    """Loads a TXT file and splits it into chunks."""

    def __init__(self, splitter: RecursiveCharacterTextSplitter) -> None:
        self._splitter = splitter

    def load(self, file_path: str) -> list[LangChainDocument]:
        return TextLoader(file_path, encoding="utf-8").load_and_split(self._splitter)
