"""PDF loader backed by LangChain's ``PyPDFLoader``."""

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document as LangChainDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter


class PdfLoader:
    """Loads a PDF file and splits it into chunks."""

    def __init__(self, splitter: RecursiveCharacterTextSplitter) -> None:
        self._splitter = splitter

    def load(self, file_path: str) -> list[LangChainDocument]:
        return PyPDFLoader(file_path).load_and_split(self._splitter)
