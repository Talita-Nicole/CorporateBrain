"""Sidebar section: save, list, load, rename and delete chat sessions (CB-013)."""

import logging
import uuid

import streamlit as st

from domain.entities.message import Message
from domain.interfaces.session_repository import SessionRepository
from presentation.i18n import t

logger = logging.getLogger(__name__)

# Shared session_state keys — kept in sync with chat.py's own constants
# (identical string values), since sessions.py must not import from chat.py
# (chat.py already imports from sessions.py; a cycle would result).
HISTORY_KEY = "chat_history"
CURRENT_SESSION_ID_KEY = "current_session_id"
CURRENT_SESSION_NAME_KEY = "current_session_name"
PENDING_DELETE_SESSION_KEY = "pending_delete_session_id"
SUGGESTIONS_KEY = "follow_up_suggestions"
GENERATING_KEY = "generating_question"
STARTERS_DONE_KEY = "starters_generated"

MAX_AUTO_NAME_LENGTH = 60


def render_sessions(repository: SessionRepository | None) -> None:
    """Render the saved-sessions list. No-op when persistence is unavailable.

    Callers own the section chrome (label/expander) — this only renders the
    list itself, so it can be nested inside sidebar.py's collapsible
    ``st.expander`` without a duplicated title.
    """
    if repository is None:
        return

    sessions = repository.list_sessions()
    if not sessions:
        st.caption(t("sessions.no_saved"))
        return

    pending_delete = st.session_state.get(PENDING_DELETE_SESSION_KEY)
    current_id = st.session_state.get(CURRENT_SESSION_ID_KEY)

    for session in sessions:
        is_active = session.id == current_id
        with st.container(key=f"cb_session_row_{session.id}"):
            col_name, col_del = st.columns([6, 1], vertical_alignment="center")
            with col_name:
                # The whole row is the click target — clicking the title loads
                # the conversation directly, matching the common chat-app
                # pattern (ChatGPT/Claude) instead of requiring a separate
                # reload icon. Disabled while already active so re-clicking
                # the open conversation is a no-op rather than a wasted reload.
                if st.button(
                    session.name,
                    key=f"load_session_{session.id}",
                    use_container_width=True,
                    disabled=is_active,
                ):
                    _load_session(repository, session.id)
                    st.rerun()
            with col_del:
                if st.button("✕", key=f"delete_session_{session.id}", help=t("sessions.delete_help")):
                    st.session_state[PENDING_DELETE_SESSION_KEY] = session.id
                    st.rerun()

        if pending_delete == session.id:
            _render_delete_confirmation(repository, session.id)


def autosave_conversation(repository: SessionRepository | None, history: list[Message]) -> None:
    """Upsert the current conversation after a completed question+answer turn.

    Called once per turn from ``chat.py``, right after a streamed answer is
    appended to history — no manual "Save" action needed. The session id is
    created on the first turn and reused on every subsequent turn so this
    always updates the same row instead of inserting a new one. Silently
    no-ops when persistence is unavailable (``repository is None``) or when
    ``history`` is empty (a conversation is only created once it actually
    has content — never an empty placeholder entry).

    Failures are logged, not surfaced to the user: autosave running in the
    background should not interrupt the chat experience with an error toast
    on every turn if Postgres has a transient hiccup.
    """
    if repository is None or not history:
        return

    session_id = st.session_state.get(CURRENT_SESSION_ID_KEY) or str(uuid.uuid4())
    name = st.session_state.get(CURRENT_SESSION_NAME_KEY) or _auto_name(history)
    try:
        saved = repository.save(session_id, name, history)
    except Exception:  # noqa: BLE001
        logger.exception("Autosave failed for session '%s'", session_id)
        return
    st.session_state[CURRENT_SESSION_ID_KEY] = saved.id
    st.session_state[CURRENT_SESSION_NAME_KEY] = saved.name


def _render_delete_confirmation(repository: SessionRepository, session_id: str) -> None:
    st.warning(t("sessions.delete_confirm"))
    col_confirm, col_cancel = st.columns(2, gap="small")
    with col_confirm:
        if st.button(t("sessions.delete_button"), type="primary", key="confirm_delete_session", use_container_width=True):
            try:
                repository.delete(session_id)
                if st.session_state.get(CURRENT_SESSION_ID_KEY) == session_id:
                    # The conversation just deleted is the one currently shown
                    # in the chat panel — it no longer exists anywhere, so
                    # reset the chat to the same empty "New Chat" state used
                    # by the New Chat button, instead of leaving its stale
                    # transcript on screen pointing at a deleted row.
                    st.session_state[HISTORY_KEY] = []
                    st.session_state.pop(SUGGESTIONS_KEY, None)
                    st.session_state.pop(GENERATING_KEY, None)
                    st.session_state.pop(STARTERS_DONE_KEY, None)
                    st.session_state.pop(CURRENT_SESSION_ID_KEY, None)
                    st.session_state.pop(CURRENT_SESSION_NAME_KEY, None)
                st.session_state.pop(PENDING_DELETE_SESSION_KEY, None)
                st.success(t("sessions.delete_success"))
            except Exception as error:  # noqa: BLE001
                logger.exception("Failed to delete session '%s'", session_id)
                st.error(t("sessions.delete_failed", error=error))
            st.rerun()
    with col_cancel:
        if st.button(t("sidebar.cancel"), key="cancel_delete_session", use_container_width=True):
            st.session_state.pop(PENDING_DELETE_SESSION_KEY, None)
            st.rerun()


def _load_session(repository: SessionRepository, session_id: str) -> None:
    session = repository.load(session_id)
    if session is None:
        return
    st.session_state[HISTORY_KEY] = list(session.messages)
    st.session_state[CURRENT_SESSION_ID_KEY] = session.id
    st.session_state[CURRENT_SESSION_NAME_KEY] = session.name
    st.session_state.pop(SUGGESTIONS_KEY, None)
    st.session_state.pop(GENERATING_KEY, None)
    st.session_state[STARTERS_DONE_KEY] = True


def _auto_name(history: list[Message]) -> str:
    """Suggest a session name from the first user question, editable by the user."""
    first_question = next((m.content for m in history if m.role == "user"), t("sessions.untitled"))
    if len(first_question) > MAX_AUTO_NAME_LENGTH:
        return first_question[:MAX_AUTO_NAME_LENGTH].rstrip() + "…"
    return first_question
