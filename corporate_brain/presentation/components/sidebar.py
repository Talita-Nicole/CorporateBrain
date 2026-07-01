"""Sidebar: company branding, document upload and indexed documents list."""

import logging
import os
import tempfile

import streamlit as st

from application.use_cases.ingest_document import IngestDocument
from domain.interfaces.document_repository import DocumentRepository
from presentation.components.branding import BrandConfig

logger = logging.getLogger(__name__)

SUPPORTED_TYPES = ["pdf", "docx", "txt", "csv"]
PROCESSED_FILES_KEY = "processed_files"
PENDING_DELETE_KEY = "pending_delete_source"

_FILE_ICONS = {"pdf": "📄", "docx": "📝", "txt": "📃", "csv": "📊"}


def render_sidebar(
    ingest_use_case: IngestDocument,
    repository: DocumentRepository,
    brand: BrandConfig,
) -> None:
    with st.sidebar:
        _render_brand_header(brand)

        st.markdown('<div class="cb-section-label">Add sources</div>', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Upload documents",
            type=SUPPORTED_TYPES,
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        if uploaded_files:
            _ingest_new_files(uploaded_files, ingest_use_case)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="cb-section-label">Indexed sources</div>', unsafe_allow_html=True)
        _render_source_list(repository)


def _render_brand_header(brand: BrandConfig) -> None:
    if brand.logo_base64:
        logo_html = (
            f'<img src="data:{brand.logo_mime_type};base64,{brand.logo_base64}" alt="logo">'
        )
    else:
        logo_html = '<span style="font-size:1.6rem">🧠</span>'

    st.markdown(
        f"""
        <div class="cb-brand-header">
            {logo_html}
            <span class="cb-brand-name">{brand.company_name}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_source_list(repository: DocumentRepository) -> None:
    sources = repository.list_indexed_sources()
    if not sources:
        st.caption("No documents indexed yet.")
        return

    pending: str | None = st.session_state.get(PENDING_DELETE_KEY)

    for source in sources:
        ext = source.rsplit(".", 1)[-1].lower() if "." in source else ""
        icon = _FILE_ICONS.get(ext, "📎")

        col_name, col_btn = st.columns([5, 1], vertical_alignment="center")
        with col_name:
            st.markdown(
                f'<div class="cb-doc-row"><span class="cb-doc-icon">{icon}</span>'
                f'<span class="cb-doc-name" title="{source}">{source}</span></div>',
                unsafe_allow_html=True,
            )
        with col_btn:
            if st.button("✕", key=f"delete_{source}", help=f"Remove {source}"):
                st.session_state[PENDING_DELETE_KEY] = source
                st.rerun()

        if pending == source:
            _render_delete_confirmation(repository, source)


def _render_delete_confirmation(repository: DocumentRepository, source: str) -> None:
    st.warning(f"Remove **{source}**? This action cannot be undone.")
    col_confirm, col_cancel = st.columns(2, gap="small")
    with col_confirm:
        if st.button("Remove", type="primary", key="confirm_delete", use_container_width=True):
            try:
                repository.delete_by_source(source)
                st.session_state.pop(PENDING_DELETE_KEY, None)
                st.session_state.get(PROCESSED_FILES_KEY, set()).discard(source)
                st.success(f"✓ {source} removed.")
            except Exception as error:  # noqa: BLE001
                logger.exception("Failed to delete source '%s'", source)
                st.error(f"Failed to remove {source}: {error}")
            st.rerun()
    with col_cancel:
        if st.button("Cancel", key="cancel_delete", use_container_width=True):
            st.session_state.pop(PENDING_DELETE_KEY, None)
            st.rerun()


def _ingest_new_files(uploaded_files, ingest_use_case: IngestDocument) -> None:
    processed: set[str] = st.session_state.setdefault(PROCESSED_FILES_KEY, set())
    for uploaded_file in uploaded_files:
        if uploaded_file.name in processed:
            continue
        with st.spinner(f"Indexing {uploaded_file.name}…"):
            try:
                chunk_count = _ingest_single_file(uploaded_file, ingest_use_case)
            except Exception as error:  # noqa: BLE001
                logger.exception("Failed to ingest %s", uploaded_file.name)
                st.error(f"Failed to index {uploaded_file.name}: {error}")
                continue
        processed.add(uploaded_file.name)
        st.success(f"✓ {uploaded_file.name} ({chunk_count} chunks)")


def _ingest_single_file(uploaded_file, ingest_use_case: IngestDocument) -> int:
    suffix = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        temp_path = tmp.name
    try:
        return ingest_use_case.execute(file_path=temp_path, file_name=uploaded_file.name)
    finally:
        os.unlink(temp_path)
