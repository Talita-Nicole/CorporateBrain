"""Dispatches a file to the right LangChain loader by extension."""

import logging
import os

from langchain_core.documents import Document as LangChainDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter

from domain.interfaces.document_loader import DocumentLoader
from infrastructure.loaders.csv_loader import CsvLoader
from infrastructure.loaders.docx_loader import DocxLoader
from infrastructure.loaders.pdf_loader import PdfLoader
from infrastructure.loaders.txt_loader import TxtLoader

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


class LangChainDocumentLoader(DocumentLoader):
    """Selects a format-specific loader and enriches chunk metadata."""

    def __init__(self) -> None:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
        )
        self._loaders = {
            ".pdf": PdfLoader(splitter),
            ".docx": DocxLoader(splitter),
            ".txt": TxtLoader(splitter),
            ".csv": CsvLoader(splitter),
        }

    def load_and_split(
        self, file_path: str, file_name: str
    ) -> list[LangChainDocument]:
        extension = os.path.splitext(file_name)[1].lower()
        loader = self._loaders.get(extension)
        if loader is None:
            raise ValueError(f"Unsupported file type: {extension}")
        chunks = loader.load(file_path)
        return self._enrich_metadata(chunks, file_name)

    @staticmethod
    def _enrich_metadata(
        chunks: list[LangChainDocument], file_name: str
    ) -> list[LangChainDocument]:
        for index, chunk in enumerate(chunks):
            chunk.metadata["source"] = file_name
            chunk.metadata["chunk_index"] = index
        return chunks
