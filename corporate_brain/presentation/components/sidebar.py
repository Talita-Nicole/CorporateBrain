"""Sidebar: company branding, document upload and indexed documents list."""

import html
import logging
import os
import tempfile
from pathlib import Path

import streamlit as st

from application.use_cases.ingest_document import EmptyDocumentError, IngestDocument
from domain.interfaces.document_repository import DocumentRepository
from domain.interfaces.session_repository import SessionRepository
from infrastructure.config.app_settings import load_app_settings, save_app_settings
from infrastructure.llm_errors import LLMCallError
from presentation.components.branding import BrandConfig
from presentation.components.sessions import render_sessions
from presentation.i18n import (
    DEFAULT_UI_LANGUAGE,
    UI_LANGUAGE_KEY,
    t,
    ui_language_display,
    ui_language_options,
)
from presentation.llm_error_messages import format_llm_call_error

logger = logging.getLogger(__name__)

SUPPORTED_TYPES = ["pdf", "docx", "txt", "csv", "md", "xlsx"]
PROCESSED_FILES_KEY = "processed_files"
PENDING_DELETE_KEY = "pending_delete_source"
SELECTED_SOURCES_KEY = "selected_sources"
SOURCE_SELECTION_ENABLED_KEY = "enable_source_selection"
SETTINGS_MODAL_OPEN_KEY = "settings_modal_open"
UPLOADER_RESET_COUNTER_KEY = "uploader_reset_counter"
UPLOAD_ERRORS_KEY = "upload_errors"
# Same session_state key chat.py uses for "a question is in flight" — kept as
# a literal (not imported) to avoid a circular import, same pattern already
# used for HISTORY_KEY in sessions.py.
GENERATING_KEY = "generating_question"

_FILE_ICONS = {"pdf": "📄", "docx": "📝", "txt": "📃", "csv": "📊", "md": "📃", "xlsx": "📊"}


def _env_default_ui_language() -> str:
    return os.getenv("DEFAULT_UI_LANGUAGE", DEFAULT_UI_LANGUAGE).strip() or DEFAULT_UI_LANGUAGE


def render_sidebar(
    ingest_use_case: IngestDocument,
    repository: DocumentRepository,
    brand: BrandConfig,
    session_repository: SessionRepository | None = None,
) -> None:
    with st.sidebar:
        _render_brand_header(brand)

        with st.container(key="cb_sidebar_scroll"):
            # Expanded by default on first render; st.expander remembers its
            # own open/closed state across reruns within the session via its
            # key, so a user's later collapse/expand persists for the rest
            # of the session without extra state plumbing. Upload lives as
            # the first element inside this same expander/section (instead of
            # its own separate bordered card above it) so it reads as part of
            # "Company documents" rather than a floating, disconnected block.
            with st.expander(t("sidebar.indexed_sources"), expanded=True):
                st.markdown(
                    f'<div class="cb-section-label">{t("sidebar.add_sources")}</div>',
                    unsafe_allow_html=True,
                )
                # Keyed with a reset counter: bumping it after a batch forces
                # Streamlit to recreate the widget empty, so processed files
                # disappear from the upload box instead of lingering there
                # (the widget's own file list is otherwise sticky by design)
                # alongside the indexed-sources list below. Reset happens
                # whether the batch succeeded or failed — failures are
                # reported via a persistent message under the box
                # (``UPLOAD_ERRORS_KEY``), not by leaving the failed file
                # stuck in the widget.
                reset_counter = st.session_state.get(UPLOADER_RESET_COUNTER_KEY, 0)
                uploaded_files = st.file_uploader(
                    t("sidebar.upload_label"),
                    type=SUPPORTED_TYPES,
                    accept_multiple_files=True,
                    label_visibility="collapsed",
                    key=f"file_uploader_{reset_counter}",
                )
                if uploaded_files:
                    _ingest_new_files(uploaded_files, ingest_use_case)
                    st.session_state[UPLOADER_RESET_COUNTER_KEY] = reset_counter + 1
                    st.rerun()

                for error_message in st.session_state.get(UPLOAD_ERRORS_KEY, []):
                    st.error(error_message)
                if st.session_state.get(UPLOAD_ERRORS_KEY):
                    if st.button(t("sidebar.dismiss_errors"), key="dismiss_upload_errors"):
                        st.session_state[UPLOAD_ERRORS_KEY] = []
                        st.rerun()

                st.markdown("<br>", unsafe_allow_html=True)
                _render_source_list(repository)

            st.markdown("<br>", unsafe_allow_html=True)
            if session_repository is not None:
                with st.expander(t("sessions.saved_conversations"), expanded=True):
                    render_sessions(session_repository)

        _render_settings_trigger()

    if st.session_state.get(SETTINGS_MODAL_OPEN_KEY):
        _render_settings_modal()


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


def _source_checkbox_key(source: str) -> str:
    return f"select_{source}"


def _render_settings_trigger() -> None:
    with st.container(key="cb_settings_bar"):
        if st.button(t("sidebar.settings_button"), key="open_settings", use_container_width=True):
            st.session_state[SETTINGS_MODAL_OPEN_KEY] = True
            st.rerun()


def _close_settings_modal() -> None:
    st.session_state[SETTINGS_MODAL_OPEN_KEY] = False


def _render_settings_modal() -> None:
    """Open the Settings dialog with a title in the current UI language.

    ``st.dialog(title, ...)`` must be applied as a decorator at call time
    (not once at module-import time as a top-level ``@st.dialog`` would do)
    so the title string can be re-resolved through ``t()`` on every render —
    otherwise the dialog title would freeze in whichever language was active
    the first time this module was imported.
    """

    @st.dialog(t("sidebar.settings_title"), on_dismiss=_close_settings_modal)
    def _dialog() -> None:
        _render_settings_body()

    _dialog()


def _render_settings_body() -> None:
    settings = load_app_settings()
    enabled = st.checkbox(
        t("sidebar.select_docs_checkbox"),
        value=settings.enable_source_selection,
        key=SOURCE_SELECTION_ENABLED_KEY,
        help=t("sidebar.select_docs_help"),
    )

    current_ui_language = st.session_state.get(UI_LANGUAGE_KEY, _env_default_ui_language())
    st.selectbox(
        t("sidebar.ui_language_label"),
        options=ui_language_options(),
        index=ui_language_options().index(current_ui_language),
        format_func=ui_language_display,
        key="ui_language_select",
    )

    st.markdown(f"<div class='cb-section-label'>{t('sidebar.branding_label')}</div>", unsafe_allow_html=True)
    company_name = st.text_input(
        t("sidebar.company_name_label"),
        value=settings.company_name,
        key="company_name_input",
        placeholder=t("sidebar.company_name_placeholder"),
    )
    logo_file = st.file_uploader(
        t("sidebar.company_logo_label"),
        type=list(_LOGO_MIME_TYPES.keys()),
        key="company_logo_upload",
    )

    col_cancel, col_save = st.columns(2, gap="small")
    with col_cancel:
        if st.button(t("sidebar.cancel"), key="cancel_settings", use_container_width=True):
            _close_settings_modal()
            st.rerun()
    with col_save:
        if st.button(t("sidebar.save"), key="save_settings", type="primary", use_container_width=True):
            settings.enable_source_selection = enabled
            settings.company_name = company_name.strip()
            settings.ui_language = st.session_state["ui_language_select"]
            if logo_file is not None:
                try:
                    settings.company_logo_path = _save_company_logo(logo_file)
                except Exception as error:  # noqa: BLE001
                    logger.exception("Failed to save company logo")
                    st.error(t("sidebar.company_logo_failed", error=error))
                    return
            save_app_settings(settings)
            if not enabled:
                st.session_state[SELECTED_SOURCES_KEY] = set()
            st.session_state[UI_LANGUAGE_KEY] = st.session_state["ui_language_select"]
            _close_settings_modal()
            st.rerun()


_LOGO_MIME_TYPES = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "svg": "image/svg+xml"}
_LOGO_ASSETS_DIR = Path("./assets")


def _save_company_logo(uploaded_file) -> str:
    """Persist an uploaded logo to disk and return its path for ``AppSettings``.

    Saved under a fixed name per extension (``company_logo.<ext>``) so a
    re-upload simply overwrites the previous file instead of accumulating
    orphaned logo files across saves.
    """
    _LOGO_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    suffix = os.path.splitext(uploaded_file.name)[1].lower()
    destination = _LOGO_ASSETS_DIR / f"company_logo{suffix}"
    destination.write_bytes(uploaded_file.getbuffer())
    return str(destination)


def _render_source_list(repository: DocumentRepository) -> None:
    sources = repository.list_indexed_sources()
    if not sources:
        st.caption(t("sidebar.no_documents"))
        return

    # Locked while a question is streaming so the search scope can't change
    # mid-answer — the retrieval for the in-flight question already used
    # whatever was selected when it started.
    locked = bool(st.session_state.get(GENERATING_KEY))

    selection_enabled = load_app_settings().enable_source_selection
    if selection_enabled:
        _prune_stale_checkbox_state(sources)
        _render_select_all(sources, locked)

    pending: str | None = st.session_state.get(PENDING_DELETE_KEY)

    for index, source in enumerate(sources):
        ext = source.rsplit(".", 1)[-1].lower() if "." in source else ""
        icon = _FILE_ICONS.get(ext, "📎")

        with st.container(key=f"cb_src_row_{index}"):
            if selection_enabled:
                col_check, col_name, col_btn = st.columns(
                    [1, 5, 1], vertical_alignment="center"
                )
                with col_check:
                    st.checkbox(
                        source,
                        key=_source_checkbox_key(source),
                        on_change=_on_source_toggle,
                        args=(sources,),
                        label_visibility="collapsed",
                        disabled=locked,
                    )
            else:
                col_name, col_btn = st.columns([6, 1], vertical_alignment="center")
            with col_name:
                safe_source = html.escape(source, quote=True)
                st.markdown(
                    f'<div class="cb-doc-row"><span class="cb-doc-icon">{icon}</span>'
                    f'<span class="cb-doc-name" title="{safe_source}">{safe_source}</span></div>',
                    unsafe_allow_html=True,
                )
            with col_btn:
                if st.button(
                    "✕", key=f"delete_{source}", help=t("sidebar.remove_source_help", source=source)
                ):
                    st.session_state[PENDING_DELETE_KEY] = source
                    st.rerun()

        if pending == source:
            _render_delete_confirmation(repository, source)

    if selection_enabled:
        _persist_selection(sources)
        if not _selected_from_state(sources):
            st.caption(t("sidebar.no_source_selected"))
    else:
        st.session_state[SELECTED_SOURCES_KEY] = set()


def _render_select_all(sources: list[str], locked: bool = False) -> None:
    """Render the NotebookLM-style master checkbox that drives every row."""
    # The master reflects whether every row is currently checked. Seed the
    # widget state before creating it so ``value=`` is never needed (which
    # Streamlit ignores once a keyed widget owns its state).
    st.session_state["select_all"] = all(
        st.session_state.get(_source_checkbox_key(s), False) for s in sources
    )
    with st.container(key="cb_src_row_select_all"):
        col_check, col_label, _col_spacer = st.columns([1, 5, 1], vertical_alignment="center")
        with col_check:
            st.checkbox(
                t("sidebar.select_all"),
                key="select_all",
                on_change=_on_select_all_toggle,
                args=(sources,),
                label_visibility="collapsed",
                disabled=locked,
            )
        with col_label:
            st.markdown(
                f'<div class="cb-doc-row"><span class="cb-select-all-label">{t("sidebar.select_all")}</span></div>',
                unsafe_allow_html=True,
            )


def _on_select_all_toggle(sources: list[str]) -> None:
    """Master checkbox callback: mirror its value onto every row checkbox."""
    value = st.session_state.get("select_all", False)
    for source in sources:
        st.session_state[_source_checkbox_key(source)] = value


def _on_source_toggle(sources: list[str]) -> None:
    """Row checkbox callback: keep the master checkbox in sync with the rows."""
    st.session_state["select_all"] = all(
        st.session_state.get(_source_checkbox_key(s), False) for s in sources
    )


def _selected_from_state(sources: list[str]) -> list[str]:
    return [s for s in sources if st.session_state.get(_source_checkbox_key(s), False)]


def _persist_selection(sources: list[str]) -> None:
    """Mirror the checkbox state into ``selected_sources`` for the chat layer."""
    st.session_state[SELECTED_SOURCES_KEY] = set(_selected_from_state(sources))


def _prune_stale_checkbox_state(sources: list[str]) -> None:
    """Drop checkbox state for sources that are no longer indexed."""
    valid = set(sources)
    for key in [k for k in st.session_state if k.startswith("select_")]:
        source = key[len("select_") :]
        if source and source not in valid and key != "select_all":
            del st.session_state[key]


def _render_delete_confirmation(repository: DocumentRepository, source: str) -> None:
    st.warning(t("sidebar.remove_confirm", source=source))
    col_confirm, col_cancel = st.columns(2, gap="small")
    with col_confirm:
        if st.button(t("sidebar.remove_button"), type="primary", key="confirm_delete", use_container_width=True):
            try:
                repository.delete_by_source(source)
                st.session_state.pop(PENDING_DELETE_KEY, None)
                st.session_state.get(PROCESSED_FILES_KEY, set()).discard(source)
                st.session_state.get(SELECTED_SOURCES_KEY, set()).discard(source)
                st.session_state.pop(f"select_{source}", None)
                st.success(t("sidebar.remove_success", source=source))
            except Exception as error:  # noqa: BLE001
                logger.exception("Failed to delete source '%s'", source)
                st.error(t("sidebar.remove_failed", source=source, error=error))
            st.rerun()
    with col_cancel:
        if st.button(t("sidebar.cancel"), key="cancel_delete", use_container_width=True):
            st.session_state.pop(PENDING_DELETE_KEY, None)
            st.rerun()


def _ingest_new_files(uploaded_files, ingest_use_case: IngestDocument) -> None:
    """Process a batch of newly uploaded files.

    The upload box is reset (its widget key bumped) and the page rerun right
    after this returns — see ``render_sidebar`` — so per-file status shown
    here via ``st.status`` is only visible for the brief moment before that
    rerun. Errors are additionally persisted to ``UPLOAD_ERRORS_KEY`` so they
    remain visible as a message under the (now-empty) upload box across the
    rerun, instead of disappearing with the widget reset.
    """
    processed: set[str] = st.session_state.setdefault(PROCESSED_FILES_KEY, set())
    errors: list[str] = st.session_state.setdefault(UPLOAD_ERRORS_KEY, [])
    for uploaded_file in uploaded_files:
        if uploaded_file.name in processed:
            continue

        with st.status(
            t("sidebar.status_loading", name=uploaded_file.name), expanded=False
        ) as status:
            try:
                chunk_count = _ingest_single_file(uploaded_file, ingest_use_case, status)
            except EmptyDocumentError:
                message = t("sidebar.empty_document_warning", name=uploaded_file.name)
                status.update(label=message, state="error")
                errors.append(message)
                # Not added to ``processed``: the file stays selectable for
                # re-upload once fixed, and is never marked as indexed.
                continue
            except LLMCallError as error:
                logger.exception("Failed to ingest %s", uploaded_file.name)
                message = format_llm_call_error(error)
                status.update(label=message, state="error")
                errors.append(f"{uploaded_file.name}: {message}")
                continue
            except Exception as error:  # noqa: BLE001
                logger.exception("Failed to ingest %s", uploaded_file.name)
                message = t("sidebar.upload_failed", name=uploaded_file.name, error=error)
                status.update(label=message, state="error")
                errors.append(message)
                continue

            status.update(
                label=t("sidebar.status_done", name=uploaded_file.name, count=chunk_count),
                state="complete",
            )

        processed.add(uploaded_file.name)
        st.toast(t("sidebar.upload_toast", name=uploaded_file.name), icon="✅")


def _ingest_single_file(uploaded_file, ingest_use_case: IngestDocument, status) -> int:
    suffix = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        temp_path = tmp.name
    try:
        # ``IngestDocument.execute`` performs chunking and indexing as a
        # single internal step (no callback hook for progress in between),
        # so this is the most granular status the UI can honestly show.
        status.update(label=t("sidebar.status_chunking"))
        return ingest_use_case.execute(file_path=temp_path, file_name=uploaded_file.name)
    finally:
        os.unlink(temp_path)
