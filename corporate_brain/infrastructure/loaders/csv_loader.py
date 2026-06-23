"""CSV loader backed by LangChain's ``CSVLoader``."""

from langchain_community.document_loaders import CSVLoader
from langchain_core.documents import Document as LangChainDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter


class CsvLoader:
    """Loads a CSV file (one document per row) and splits it into chunks."""

    def __init__(self, splitter: RecursiveCharacterTextSplitter) -> None:
        self._splitter = splitter

    def load(self, file_path: str) -> list[LangChainDocument]:
        return CSVLoader(file_path, encoding="utf-8").load_and_split(self._splitter)
