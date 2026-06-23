"""Sidebar: document upload and the list of indexed documents."""

import logging
import os
import tempfile

import streamlit as st

from application.use_cases.ingest_document import IngestDocument
from domain.interfaces.document_repository import DocumentRepository

logger = logging.getLogger(__name__)

SUPPORTED_TYPES = ["pdf", "docx", "txt", "csv"]
PROCESSED_FILES_KEY = "processed_files"


def render_sidebar(
    ingest_use_case: IngestDocument, repository: DocumentRepository
) -> None:
    """Render the upload area and the indexed-documents list."""
    with st.sidebar:
        st.header("Documents")
        uploaded_files = st.file_uploader(
            "Upload documents",
            type=SUPPORTED_TYPES,
            accept_multiple_files=True,
        )
        if uploaded_files:
            _ingest_new_files(uploaded_files, ingest_use_case)

        st.subheader("Indexed documents")
        sources = repository.list_indexed_sources()
        if sources:
            for source in sources:
                st.markdown(f"- {source}")
        else:
            st.caption("No documents indexed yet.")


def _ingest_new_files(uploaded_files, ingest_use_case: IngestDocument) -> None:
    processed: set[str] = st.session_state.setdefault(PROCESSED_FILES_KEY, set())
    for uploaded_file in uploaded_files:
        if uploaded_file.name in processed:
            continue
        with st.spinner(f"Indexing {uploaded_file.name}..."):
            try:
                chunk_count = _ingest_single_file(uploaded_file, ingest_use_case)
            except Exception as error:  # noqa: BLE001
                logger.exception("Failed to ingest %s", uploaded_file.name)
                st.error(f"Failed to index {uploaded_file.name}: {error}")
                continue
        processed.add(uploaded_file.name)
        st.success(f"Indexed {uploaded_file.name} ({chunk_count} chunks).")


def _ingest_single_file(uploaded_file, ingest_use_case: IngestDocument) -> int:
    suffix = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(uploaded_file.getbuffer())
        temp_path = temp_file.name
    try:
        return ingest_use_case.execute(
            file_path=temp_path, file_name=uploaded_file.name
        )
    finally:
        os.unlink(temp_path)
