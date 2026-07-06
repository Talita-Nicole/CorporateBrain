"""UI string translation table and lookup helper (CB-010).

Independent of the *answer* language (CB-007, which only controls what
language the RAG response is generated in). This module controls the static
chrome: sidebar labels, buttons, tooltips, status and error messages.
"""

import os

import streamlit as st

PORTUGUESE = "pt-BR"
ENGLISH = "en"
DEFAULT_UI_LANGUAGE = ENGLISH
UI_LANGUAGE_KEY = "ui_language"

_UI_LANGUAGE_DISPLAY = {
    ENGLISH: "English",
    PORTUGUESE: "Português (pt-BR)",
}

# Keyed by a stable identifier, not by the English text, so English copy can
# change without silently breaking the Portuguese translation lookup.
_STRINGS: dict[str, dict[str, str]] = {
    # sidebar.py
    "sidebar.add_sources": {ENGLISH: "Add sources", PORTUGUESE: "Adicionar fontes"},
    "sidebar.add_documents_button": {ENGLISH: "➕ Add documents", PORTUGUESE: "➕ Adicionar documentos"},
    "sidebar.upload_title": {ENGLISH: "Add documents", PORTUGUESE: "Adicionar documentos"},
    "sidebar.upload_hint": {
        ENGLISH: "Supported files: PDF, DOCX, TXT, CSV, MD, XLSX.",
        PORTUGUESE: "Arquivos suportados: PDF, DOCX, TXT, CSV, MD, XLSX.",
    },
    "sidebar.upload_label": {ENGLISH: "Upload documents", PORTUGUESE: "Enviar documentos"},
    "sidebar.indexed_sources": {ENGLISH: "Company documents", PORTUGUESE: "Documentos da empresa"},
    "sidebar.no_documents": {ENGLISH: "No documents yet.", PORTUGUESE: "Nenhum documento ainda."},
    "sidebar.select_all": {ENGLISH: "Select all", PORTUGUESE: "Selecionar todos"},
    "sidebar.no_source_selected": {
        ENGLISH: "Nothing selected — searching all company documents.",
        PORTUGUESE: "Nada selecionado — buscando em todos os documentos da empresa.",
    },
    "sidebar.remove_source_help": {ENGLISH: "Remove {source}", PORTUGUESE: "Remover {source}"},
    "sidebar.remove_confirm": {
        ENGLISH: "Remove **{source}**? This action cannot be undone.",
        PORTUGUESE: "Remover **{source}**? Esta ação não pode ser desfeita.",
    },
    "sidebar.remove_button": {ENGLISH: "Remove", PORTUGUESE: "Remover"},
    "sidebar.cancel": {ENGLISH: "Cancel", PORTUGUESE: "Cancelar"},
    "sidebar.remove_success": {ENGLISH: "✓ {source} removed.", PORTUGUESE: "✓ {source} removido."},
    "sidebar.remove_failed": {ENGLISH: "Failed to remove {source}: {error}", PORTUGUESE: "Falha ao remover {source}: {error}"},
    "sidebar.upload_toast": {ENGLISH: "✓ {name} uploaded", PORTUGUESE: "✓ {name} enviado"},
    "sidebar.upload_failed": {ENGLISH: "Couldn't process {name}: {error}", PORTUGUESE: "Não foi possível processar {name}: {error}"},
    "sidebar.dismiss_errors": {ENGLISH: "Dismiss", PORTUGUESE: "Dispensar"},
    "sidebar.status_loading": {ENGLISH: "Reading {name}…", PORTUGUESE: "Lendo {name}…"},
    "sidebar.status_chunking": {ENGLISH: "Processing…", PORTUGUESE: "Processando…"},
    "sidebar.status_done": {ENGLISH: "{name} ready", PORTUGUESE: "{name} pronto"},
    "sidebar.empty_document_warning": {
        ENGLISH: "Couldn't read any text from {name} — is this a scanned document?",
        PORTUGUESE: "Não foi possível ler texto de {name} — é um documento escaneado?",
    },
    "sidebar.settings_button": {ENGLISH: "⚙️ Settings", PORTUGUESE: "⚙️ Configurações"},
    "sidebar.settings_title": {ENGLISH: "Settings", PORTUGUESE: "Configurações"},
    "sidebar.select_docs_checkbox": {
        ENGLISH: "Select documents to search",
        PORTUGUESE: "Selecionar documentos para busca",
    },
    "sidebar.select_docs_help": {
        ENGLISH: "When enabled, you can choose which documents to search.",
        PORTUGUESE: "Quando ativado, você pode escolher quais documentos pesquisar.",
    },
    "sidebar.ui_language_label": {ENGLISH: "Interface language", PORTUGUESE: "Idioma da interface"},
    "sidebar.branding_label": {ENGLISH: "Branding", PORTUGUESE: "Identidade visual"},
    "sidebar.company_name_label": {ENGLISH: "Company name", PORTUGUESE: "Nome da empresa"},
    "sidebar.company_name_placeholder": {ENGLISH: "e.g. Acme Inc.", PORTUGUESE: "ex: Acme Ltda."},
    "sidebar.company_logo_label": {ENGLISH: "Company logo", PORTUGUESE: "Logo da empresa"},
    "sidebar.company_logo_failed": {
        ENGLISH: "Couldn't save the logo: {error}",
        PORTUGUESE: "Não foi possível salvar a logo: {error}",
    },
    "sidebar.save": {ENGLISH: "Save", PORTUGUESE: "Salvar"},

    # chat.py
    "chat.title": {ENGLISH: "Ask {company_name}", PORTUGUESE: "Pergunte à {company_name}"},
    "chat.subtitle": {
        ENGLISH: "Ask questions about company documents.",
        PORTUGUESE: "Faça perguntas sobre os documentos da empresa.",
    },
    "chat.new_chat_button": {ENGLISH: "New Chat", PORTUGUESE: "Nova Conversa"},
    "chat.new_chat_help": {
        ENGLISH: "Starts a new conversation. This one is already saved under Saved conversations.",
        PORTUGUESE: "Inicia uma nova conversa. Esta já está salva em Conversas salvas.",
    },
    "chat.input_placeholder": {
        ENGLISH: "Ask a question about company documents…",
        PORTUGUESE: "Faça uma pergunta sobre os documentos da empresa…",
    },
    "chat.thinking": {ENGLISH: "Thinking…", PORTUGUESE: "Pensando…"},
    "chat.preparing_suggestions": {ENGLISH: "Preparing suggestions…", PORTUGUESE: "Preparando sugestões…"},
    "chat.answer_failed": {
        ENGLISH: "Failed to generate an answer: {error}",
        PORTUGUESE: "Falha ao gerar uma resposta: {error}",
    },
    "chat.sources_expander": {ENGLISH: "📎 {count} source(s)", PORTUGUESE: "📎 {count} fonte(s)"},
    "chat.suggested_questions": {ENGLISH: "Suggested questions", PORTUGUESE: "Perguntas sugeridas"},
    "chat.token_usage": {
        ENGLISH: "{total} tokens ({input} in, {output} out)",
        PORTUGUESE: "{total} tokens ({input} entrada, {output} saída)",
    },
    "chat.debug_expander": {ENGLISH: "🐞 Debug panel", PORTUGUESE: "🐞 Painel de depuração"},
    "chat.debug_config": {
        ENGLISH: "**Retrieval:** top-k={top_k}, max distance={max_distance} · **Chunking:** size={chunk_size}, overlap={chunk_overlap}",
        PORTUGUESE: "**Busca:** top-k={top_k}, distância máx.={max_distance} · **Divisão:** tamanho={chunk_size}, sobreposição={chunk_overlap}",
    },
    "chat.debug_models": {
        ENGLISH: "**Embedding model:** {embedding_model} · **Chat model:** {chat_model}",
        PORTUGUESE: "**Modelo de embedding:** {embedding_model} · **Modelo de chat:** {chat_model}",
    },

    # sessions.py
    "sessions.saved_conversations": {ENGLISH: "Saved conversations", PORTUGUESE: "Conversas salvas"},
    "sessions.no_saved": {ENGLISH: "No saved conversations yet.", PORTUGUESE: "Nenhuma conversa salva ainda."},
    "sessions.delete_help": {ENGLISH: "Delete this conversation", PORTUGUESE: "Excluir esta conversa"},
    "sessions.delete_confirm": {
        ENGLISH: "Delete this saved conversation? This action cannot be undone.",
        PORTUGUESE: "Excluir esta conversa salva? Esta ação não pode ser desfeita.",
    },
    "sessions.delete_button": {ENGLISH: "Delete", PORTUGUESE: "Excluir"},
    "sessions.delete_success": {ENGLISH: "✓ Conversation deleted.", PORTUGUESE: "✓ Conversa excluída."},
    "sessions.delete_failed": {
        ENGLISH: "Failed to delete conversation: {error}",
        PORTUGUESE: "Falha ao excluir conversa: {error}",
    },
    "sessions.untitled": {ENGLISH: "Untitled conversation", PORTUGUESE: "Conversa sem título"},
}


def t(key: str, **kwargs: str) -> str:
    """Look up ``key`` in the current UI language and format it with ``kwargs``.

    Falls back to English if the key or language is missing, so a translation
    gap never crashes the UI. Reads the language from
    ``st.session_state["ui_language"]``, defaulting to ``DEFAULT_UI_LANGUAGE``
    (or the ``DEFAULT_UI_LANGUAGE`` env var, read once at import time).
    """
    language = st.session_state.get(UI_LANGUAGE_KEY, _env_default_language())
    entry = _STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(language) or entry.get(ENGLISH) or key
    return text.format(**kwargs) if kwargs else text


def ui_language_options() -> list[str]:
    return [ENGLISH, PORTUGUESE]


def ui_language_display(code: str) -> str:
    return _UI_LANGUAGE_DISPLAY.get(code, code)


def _env_default_language() -> str:
    value = os.getenv("DEFAULT_UI_LANGUAGE", DEFAULT_UI_LANGUAGE).strip()
    return value if value in (ENGLISH, PORTUGUESE) else DEFAULT_UI_LANGUAGE
