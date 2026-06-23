"""DOCX loader backed by LangChain's ``Docx2txtLoader``."""

from langchain_community.document_loaders import Docx2txtLoader
from langchain_core.documents import Document as LangChainDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocxLoader:
    """Loads a DOCX file and splits it into chunks."""

    def __init__(self, splitter: RecursiveCharacterTextSplitter) -> None:
        self._splitter = splitter

    def load(self, file_path: str) -> list[LangChainDocument]:
        return Docx2txtLoader(file_path).load_and_split(self._splitter)
