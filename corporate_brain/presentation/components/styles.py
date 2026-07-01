"""Inject custom CSS respecting the user's light/dark mode preference."""

import streamlit as st


def inject_styles(primary_color: str) -> None:
    st.markdown(
        f"""
<style>
/* ── Brand accent ── */
:root {{
  --brand: {primary_color};
  --brand-dim: {primary_color}22;
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
  border-right: 1px solid var(--brand-dim);
}}

/* Sidebar header (logo + company name) */
.cb-brand-header {{
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 0 20px 0;
  border-bottom: 1px solid var(--brand-dim);
  margin-bottom: 20px;
}}
.cb-brand-header img {{
  width: 36px;
  height: 36px;
  object-fit: contain;
  border-radius: 6px;
}}
.cb-brand-name {{
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}}

/* ── Section labels ── */
.cb-section-label {{
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  opacity: 0.5;
  margin-bottom: 8px;
}}

/* ── Document rows ── */
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:has([class*="st-key-delete_"]) {{
  display: flex !important;
  align-items: center !important;   /* centralize the columns relative to each other */
  border-radius: 8px;
  padding: 4px 6px;
  margin-bottom: 4px;
  transition: background 0.15s;
}}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:has([class*="st-key-delete_"]):hover {{
  background: var(--brand-dim);
}}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:has([class*="st-key-delete_"]) [data-testid="stElementContainer"] {{
  margin: 0 !important;
  padding: 0 !important;
}}
/* stColumn only needs to allow ellipsis to work (min-width:0 overrides the flex
   item default of min-width:auto, which otherwise blocks text from shrinking).
   Vertical centering is handled solely by stHorizontalBlock above — do not set
   align-items here: stColumn's main axis is column, so align-items would only
   affect the horizontal (cross) axis, not vertical position. */
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:has([class*="st-key-delete_"]) [data-testid="stColumn"] {{
  min-width: 0;
}}
.cb-doc-row {{
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  line-height: 1;
}}
.cb-doc-icon {{
  flex-shrink: 0;
  font-size: 1rem;
  line-height: 1;
  display: flex;
  align-items: center;   /* neutralize the emoji glyph's intrinsic vertical space */
}}
.cb-doc-name {{
  flex: 1;
  min-width: 0;
  font-size: 0.85rem;
  line-height: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:has([class*="st-key-delete_"]) p {{
  margin: 0 !important;
}}

/* ── Upload area ── */
[data-testid="stFileUploader"] {{
  border: 1.5px dashed var(--brand-dim) !important;
  border-radius: 10px !important;
  padding: 4px !important;
}}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {{
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 8px;
}}

/* ── Source expander ── */
[data-testid="stExpander"] {{
  border: 1px solid var(--brand-dim) !important;
  border-radius: 8px !important;
}}

/* ── Buttons ── */
[data-testid="stBaseButton-secondary"] {{
  border-color: var(--brand-dim) !important;
}}
[data-testid="stBaseButton-primary"] {{
  background-color: var(--brand) !important;
  border-color: var(--brand) !important;
}}

/* ── Delete (✕) button in source list ── */
[class*="st-key-delete_"] button {{
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 32px !important;
  height: 32px !important;
  min-height: 32px !important;
  padding: 0 !important;
  border: none !important;
  background: transparent !important;
  box-shadow: none !important;
  color: var(--brand) !important;
  border-radius: 6px !important;
}}
/* Zero the inner markdown/paragraph metrics so the ✕ glyph sits dead center. */
[class*="st-key-delete_"] button > div,
[class*="st-key-delete_"] button [data-testid="stMarkdownContainer"] {{
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 100% !important;
  height: 100% !important;
}}
[class*="st-key-delete_"] button p {{
  margin: 0 !important;
  padding: 0 !important;
  line-height: 1 !important;
  font-size: 1rem !important;
}}
[class*="st-key-delete_"] button:hover {{
  background: var(--brand-dim) !important;
}}

/* ── Remove (primary) hover feedback in delete confirmation ── */
.st-key-confirm_delete button:hover {{
  filter: brightness(0.9);
}}

/* ── Cancel button in delete confirmation ── */
.st-key-cancel_delete button {{
  background: rgba(128, 128, 128, 0.25) !important;
  border: none !important;
  color: inherit !important;
}}
.st-key-cancel_delete button:hover {{
  background: rgba(128, 128, 128, 0.4) !important;
}}

/* ── Chat input ── */
[data-testid="stChatInput"] textarea {{
  border-color: var(--brand-dim) !important;
}}
[data-testid="stChatInput"] textarea:focus {{
  border-color: var(--brand) !important;
  box-shadow: 0 0 0 2px var(--brand-dim) !important;
}}

/* ── Scrollbar (webkit) ── */
::-webkit-scrollbar {{ width: 5px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: var(--brand-dim); border-radius: 10px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--brand); }}

/* ── Page title ── */
.cb-page-title {{
  font-size: 1.3rem;
  font-weight: 700;
  margin-bottom: 4px;
}}
.cb-page-subtitle {{
  font-size: 0.85rem;
  opacity: 0.55;
  margin-bottom: 24px;
}}
</style>
""",
        unsafe_allow_html=True,
    )
