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
/* Make the sidebar column (header + user content) a full-height flex column so
   the user content fills EXACTLY the space left by the header — no fixed-height
   math. The previous approach forced ``height: calc(100vh + 8px)`` on the
   content (to compensate a -52px negative-margin overlap of the header), which
   left the content box taller than the viewport and produced a second,
   page-level scrollbar. ``:has(> stSidebarUserContent)`` targets the emotion-
   hashed wrapper Streamlit renders between the sidebar and its two children,
   without depending on that generated class name. */
[data-testid="stSidebar"] > div:has(> [data-testid="stSidebarUserContent"]) {{
  display: flex !important;
  flex-direction: column !important;
  height: 100% !important;
}}
/* The native header strip only hosts the "<<" collapse button; compress it to a
   short row so the brand block below it sits near the top instead of under a
   tall empty gap (the "margem em cima" complaint). */
[data-testid="stSidebarHeader"] {{
  flex: 0 0 auto !important;
  height: 2.25rem !important;
  min-height: 2.25rem !important;
  padding-top: 6px !important;
  padding-bottom: 0 !important;
  /* Streamlit ships a 16px bottom margin on this strip — dead space that pushed
     the brand block down (the "margem em cima"). Zero it. */
  margin-bottom: 0 !important;
}}
[data-testid="stSidebarUserContent"] {{
  flex: 1 1 auto !important;
  min-height: 0 !important;
  padding-top: 0 !important;
  /* Streamlit's default ~6rem bottom padding here left the content box ending
     ~96px above the viewport, so the pinned Settings bar floated well short of
     the real bottom (the "margem embaixo"). Zero it so the flex column spans
     the full sidebar height and Settings actually reaches the bottom. */
  padding-bottom: 0 !important;
  display: flex !important;
  flex-direction: column !important;
  /* Contain overflow here so the single intended scroll lives in
     ``cb_sidebar_scroll`` below, never leaking out to a page-level scrollbar. */
  overflow: hidden !important;
}}
/* Force EVERY ancestor div of the Settings bar AND of the scrollable content
   block (however many wrappers Streamlit nests between the user content and
   those blocks) to be a full-height, shrinkable flex column. Streamlit wraps
   every ``st.container`` in its own extra div, and that wrapper defaults to
   ``min-height: auto`` — which makes it size to its content's intrinsic
   height instead of shrinking to the available space, breaking the flex
   chain partway down. ``cb_sidebar_scroll`` and ``cb_settings_bar`` are
   siblings (not ancestor/descendant), so ``:has()`` targeted at the settings
   bar alone never reaches the scroll wrapper — both must be matched
   explicitly so min-height:0 propagates all the way from
   ``stSidebarUserContent`` down to the actual scrolling element. */
[data-testid="stSidebarUserContent"] div:has([class*="st-key-cb_settings_bar"]),
[data-testid="stSidebarUserContent"] div:has(> [class*="st-key-cb_sidebar_scroll"]) {{
  flex: 1 1 auto !important;
  min-height: 0 !important;
  display: flex !important;
  flex-direction: column !important;
}}
/* The broad rule above also matches the Settings bar's OWN wrapper (it contains
   the settings block as a descendant), inflating it to flex:1 so it grew a tall
   empty band above the button. Override just that direct wrapper back to
   hug-content — the scroll wrapper above already takes all the free space, so
   the Settings wrapper naturally lands at the bottom. */
[data-testid="stSidebarUserContent"] [data-testid="stLayoutWrapper"]:has(> [class*="st-key-cb_settings_bar"]) {{
  flex: 0 0 auto !important;
  margin-top: auto !important;
}}

/* ── Sidebar scrollable content (everything above the pinned Settings bar) ── */
[class*="st-key-cb_sidebar_scroll"] {{
  flex: 1 1 auto !important;
  min-height: 0 !important;
  overflow-y: auto !important;
  padding-right: 2px;
}}

/* ── Settings bar, pinned to the bottom of the sidebar ── */
[class*="st-key-cb_settings_bar"] {{
  flex: 0 0 auto !important;
  /* ``margin-top: auto`` pins the bar to the bottom of the flex column even if
     the scrollable area does not fully fill the height. */
  margin-top: auto !important;
  border-top: 1px solid var(--brand-dim);
  padding: 10px 0 4px 0;
}}
[class*="st-key-cb_settings_bar"] button {{
  justify-content: flex-start !important;
  background: transparent !important;
  border: none !important;
  color: inherit !important;
  opacity: 0.75;
  font-size: 0.85rem !important;
}}
[class*="st-key-cb_settings_bar"] button:hover {{
  background: var(--brand-dim) !important;
  opacity: 1;
}}

/* Sidebar header (logo + company name). ~20px of breathing room down to the
   first section ("Add sources") so the brand block doesn't visually collide
   with the section label right below it. */
.cb-brand-header {{
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 0 10px 0;
  border-bottom: 1px solid var(--brand-dim);
  margin-bottom: 10px;
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
/* Spacing above the flat "Saved conversations" label so it separates from the
   Company documents section above it. */
.cb-section-label-spaced {{
  margin-top: 20px;
}}

/* ── Sidebar section expander (Company documents only) ──
   Streamlit's default expander is a heavy bordered card; strip it to a flat
   collapsible section that reads exactly like the other section labels: no
   border, no background box, the SAME colour as the sidebar, and the chevron
   pushed to the RIGHT edge. Scoped to the sidebar so the chat's own bordered
   "sources" expander is untouched. */
[data-testid="stSidebar"] [data-testid="stExpander"] {{
  margin-bottom: 6px;
}}
[data-testid="stSidebar"] [data-testid="stExpander"] details {{
  border: none !important;
  background: transparent !important;
}}
/* No background change on hover/expand — the header must stay the same colour as
   the sidebar (per feedback), so only the chevron/label read as interactive. */
[data-testid="stSidebar"] [data-testid="stExpander"] summary {{
  padding: 6px 0 !important;
  background: transparent !important;
}}
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {{
  background: transparent !important;
}}
/* Match the uppercase section-label styling on the expander's own header text. */
[data-testid="stSidebar"] [data-testid="stExpander"] summary p {{
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  opacity: 0.6;
}}
/* Push the chevron icon to the far RIGHT of the header (Streamlit renders it on
   the left, inside a shrink-to-fit ``<span>``). Make that span full-width first,
   then ``order`` + ``margin-left: auto`` sends the chevron to the right edge
   while the label stays on the left. */
[data-testid="stSidebar"] [data-testid="stExpander"] summary > span {{
  width: 100% !important;
  display: flex !important;
  align-items: center !important;
}}
[data-testid="stSidebar"] [data-testid="stExpander"] summary [data-testid="stIconMaterial"] {{
  margin-left: auto !important;
  order: 2;
}}
/* Drop the expander body's default left padding so rows align with the header. */
[data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
  padding: 4px 0 0 0 !important;
}}

/* ── Document rows (Select all + each indexed source) ──
   Both the master "Select all" row and every source row are wrapped in a
   keyed container whose class starts with ``st-key-cb_src_row_``. Styling the
   shared wrapper (rather than only rows that :has() a delete button) keeps the
   checkboxes on a single X axis and the labels/names starting at the same
   offset — the two used to diverge because only file rows were padded. */
[data-testid="stSidebar"] [class*="st-key-cb_src_row_"] {{
  border-radius: 8px;
  padding: 4px 6px;
  /* The sidebar content column places a 16px flex ``gap`` between every child,
     which leaves the source list looking loose. Pull each row up so the visible
     row-to-row gap is a compact, uniform ~8px. */
  margin-top: -8px;
  margin-bottom: 0;
  transition: background 0.15s;
}}
/* The master row is the first child after the "Indexed sources" label; use a
   smaller pull so it keeps a little breathing room under the header (~6px)
   instead of colliding with it. */
[data-testid="stSidebar"] [class*="st-key-cb_src_row_select_all"] {{
  margin-top: -2px;
}}
[data-testid="stSidebar"] [class*="st-key-cb_src_row_"]:hover {{
  background: var(--brand-dim);
}}
[data-testid="stSidebar"] [class*="st-key-cb_src_row_"] [data-testid="stHorizontalBlock"] {{
  display: flex !important;
  align-items: center !important;   /* centralize the columns relative to each other */
}}
[data-testid="stSidebar"] [class*="st-key-cb_src_row_"] [data-testid="stElementContainer"] {{
  margin: 0 !important;
  padding: 0 !important;
}}
/* stColumn only needs to allow ellipsis to work (min-width:0 overrides the flex
   item default of min-width:auto, which otherwise blocks text from shrinking).
   Vertical centering is handled solely by stHorizontalBlock above — do not set
   align-items here: stColumn's main axis is column, so align-items would only
   affect the horizontal (cross) axis, not vertical position. */
[data-testid="stSidebar"] [class*="st-key-cb_src_row_"] [data-testid="stColumn"] {{
  min-width: 0;
}}
/* Streamlit gives the last markdown container a ``margin-bottom: -16px`` that
   collapses the name column to zero height, leaving the file name anchored to
   the column's centre line and hanging ~8px below the checkbox/icon/✕. Zero it
   so the column keeps its real height and stHorizontalBlock's align-items:center
   can line all four elements up on one horizontal axis. */
[data-testid="stSidebar"] [class*="st-key-cb_src_row_"] [data-testid="stMarkdownContainer"] {{
  margin-bottom: 0 !important;
}}
/* BaseWeb top-aligns the checkbox glyph inside its label; centre it so it shares
   the row's vertical axis with the name and ✕ button. */
[data-testid="stSidebar"] [class*="st-key-cb_src_row_"] [data-testid="stCheckbox"] label {{
  align-items: center !important;
}}
/* Source selection checkboxes disabled while a question is streaming (see
   sidebar.py's GENERATING_KEY lock) — dim the row and show a "no" cursor so
   it reads as locked, not just a rendering glitch. */
[data-testid="stSidebar"] [class*="st-key-cb_src_row_"] [data-testid="stCheckbox"]:has(input:disabled) {{
  opacity: 0.45;
  cursor: not-allowed;
}}
[data-testid="stSidebar"] [class*="st-key-cb_src_row_"] [data-testid="stCheckbox"]:has(input:disabled) label {{
  cursor: not-allowed;
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
  width: 1.15rem;        /* fixed box so varied emoji glyph widths don't shift the name */
  font-size: 1rem;
  line-height: 1;
  display: flex;
  align-items: center;   /* neutralize the emoji glyph's intrinsic vertical space */
  justify-content: center;
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
.cb-select-all-label {{
  font-size: 0.8rem;
  font-weight: 600;
  opacity: 0.7;
  line-height: 1;
}}
[data-testid="stSidebar"] [class*="st-key-cb_src_row_"] p {{
  margin: 0 !important;
}}

/* ── Saved conversation rows ──
   Each row is a keyed container (``st-key-cb_session_row_<id>``) holding the
   title as a full-width button (the whole row is the click target, ChatGPT/
   Claude-style — no separate reload icon) plus a small delete button. Match
   the same padding/hover rhythm as the document rows above for visual
   consistency between the two collapsible sections. */
[data-testid="stSidebar"] [class*="st-key-cb_session_row_"] {{
  border-radius: 8px;
  padding: 2px 6px;
  margin-top: -8px;
  margin-bottom: 0;
  transition: background 0.15s;
}}
[data-testid="stSidebar"] [class*="st-key-cb_session_row_"] [class*="st-key-load_session_"] button {{
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  justify-content: flex-start !important;
  text-align: left !important;
  padding: 6px 4px !important;
  font-size: 0.85rem !important;
  font-weight: 400 !important;
  color: inherit !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}}
/* The button's inner wrapper div (BaseWeb) centers its content by default
   (``justify-content: center``), which overrides the button-level
   flex-start above and re-centers the title text. Un-center it so the
   conversation name reads as a left-aligned list item, not a pill button. */
[data-testid="stSidebar"] [class*="st-key-cb_session_row_"] [class*="st-key-load_session_"] button > div {{
  justify-content: flex-start !important;
  width: 100%;
  overflow: hidden;
}}
[data-testid="stSidebar"] [class*="st-key-cb_session_row_"] [class*="st-key-load_session_"] button [data-testid="stMarkdownContainer"] {{
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}}
[data-testid="stSidebar"] [class*="st-key-cb_session_row_"] [class*="st-key-load_session_"] button p {{
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin: 0 !important;
}}
/* The WHOLE row highlights on hover (full width, including the ✕ column) so the
   delete button is never left sitting on an un-highlighted strip — this is what
   made the session hover look "separado" versus the document rows. The load
   button itself stays transparent; the row container owns the highlight, exactly
   like the document rows above. */
[data-testid="stSidebar"] [class*="st-key-cb_session_row_"]:hover {{
  background: var(--brand-dim);
}}
/* The active conversation's load button is rendered ``disabled`` — highlight the
   whole row (via ``:has``) and mark the title, instead of the default greyed-out
   disabled look. The button's own background stays transparent so the row
   container is the single source of the highlight. */
[data-testid="stSidebar"] [class*="st-key-cb_session_row_"]:has(button:disabled) {{
  background: var(--brand-dim);
}}
[data-testid="stSidebar"] [class*="st-key-cb_session_row_"] [class*="st-key-load_session_"] button:disabled {{
  background: transparent !important;
  color: var(--brand) !important;
  font-weight: 600 !important;
  opacity: 1 !important;
  cursor: default !important;
}}
/* Delete (✕) button stays hidden until the row is hovered — ChatGPT/Claude
   style — so the list reads as clean titles, not a column of ✕ glyphs. Kept
   focus-visible so keyboard users can still reach it. */
[data-testid="stSidebar"] [class*="st-key-cb_session_row_"] [class*="st-key-delete_session_"] button {{
  opacity: 0;
  transition: opacity 0.12s ease;
}}
[data-testid="stSidebar"] [class*="st-key-cb_session_row_"]:hover [class*="st-key-delete_session_"] button,
[data-testid="stSidebar"] [class*="st-key-cb_session_row_"] [class*="st-key-delete_session_"] button:focus-visible {{
  opacity: 1;
}}
/* Same hover-reveal for the document rows' ✕, so both sections behave
   identically (the previous always-on ✕ on documents was the visible mismatch
   against the sessions' hover-only ✕). */
[data-testid="stSidebar"] [class*="st-key-cb_src_row_"] [class*="st-key-delete_"] button {{
  opacity: 0;
  transition: opacity 0.12s ease;
}}
[data-testid="stSidebar"] [class*="st-key-cb_src_row_"]:hover [class*="st-key-delete_"] button,
[data-testid="stSidebar"] [class*="st-key-cb_src_row_"] [class*="st-key-delete_"] button:focus-visible {{
  opacity: 1;
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

/* ── Source expander (chat answers only) ──
   Scoped to the main area so it keeps its bordered card look, WITHOUT re-adding
   a border to the flat sidebar section expanders styled above. */
[data-testid="stMain"] [data-testid="stExpander"] {{
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

/* ── Settings modal buttons (Save / Cancel) ── */
.st-key-save_settings button {{
  cursor: pointer;
  transition: background-color 0.15s ease, filter 0.15s ease;
}}
/* Save is a primary button (brand background); darken it ~12% on hover. */
.st-key-save_settings button:hover {{
  filter: brightness(0.88);
}}
.st-key-cancel_settings button {{
  background: rgba(128, 128, 128, 0.25) !important;
  border: none !important;
  color: inherit !important;
  cursor: pointer;
  transition: background-color 0.15s ease;
}}
.st-key-cancel_settings button:hover {{
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

/* ── Main content area ── */
/* Streamlit's top toolbar (``stHeader``) is a fixed 60px opaque bar that masks
   scrolled content, and the main column (``stMainBlockContainer``) carries a
   6rem top padding to clear it. Both left the title floating far from the top.
   Shrink the toolbar to 44px (still tall enough for the Deploy/menu controls and
   still opaque, so it keeps masking scroll) and trim the column padding so the
   title sits just below it. NB: the old ``> .main .block-container`` selector no
   longer matches modern Streamlit, and the header's 60px is a ``min-height`` (so
   ``height`` alone is ignored) — both are overridden here. */
[data-testid="stHeader"] {{
  height: 44px !important;
  min-height: 44px !important;
}}
[data-testid="stToolbar"] {{
  min-height: 44px !important;
  height: 44px !important;
}}
[data-testid="stMainBlockContainer"] {{
  padding-top: 1.75rem !important;
}}

/* ── Sticky "New Chat" header ──
   The scrolling ancestor of the chat transcript is ``section[data-testid=
   "stMain"]`` (overflow-y:auto). The old rules targeted
   ``stAppScrollToBottomContainer``, a testid that no longer exists in this
   Streamlit version, so they matched NOTHING: the header never pinned ("New
   Chat" scrolled away on long conversations) and never got an opaque
   background (the subtitle/title showed through and overlapped scrolled
   messages).

   Opaque background is done theme-agnostically with ``background-color:
   inherit``. The nearest painted ancestor is ``stAppViewContainer`` (and its
   direct child div), which carry the real active theme color; bridging every
   element from there down to the header with ``inherit`` propagates that exact
   color, so it tracks the in-app Light/Dark/System choice instead of a
   hardcoded value. ``inherit`` only bridges ONE generation, so each link in
   the chain must be listed explicitly. The chain is: stAppViewContainer
   (opaque) → its child div → section.stMain → stMainBlockContainer → the
   unlabelled stVerticalBlock → the header's stLayoutWrapper → the keyed header
   block.
   IMPORTANT: never use a blanket ``stMain *`` selector — that would wipe the
   chat-message avatars' own background-color and make them invisible. Only the
   exact wrapper chain feeding the sticky header is targeted. */
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > div,
section[data-testid="stMain"],
section[data-testid="stMain"] > [data-testid="stMainBlockContainer"],
section[data-testid="stMain"] > [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"],
section[data-testid="stMain"] [data-testid="stLayoutWrapper"]:has(> [class*="st-key-cb_chat_header"]),
section[data-testid="stMain"] [class*="st-key-cb_chat_header"] {{
  background-color: inherit;
}}
/* The ``st.container(key=...)`` is wrapped in an extra ``stLayoutWrapper`` div,
   and it's THAT wrapper (not the keyed block) that must carry ``position:
   sticky`` for the pin to actually take, relative to the stMain scroller. */
section[data-testid="stMain"] [data-testid="stLayoutWrapper"]:has(> [class*="st-key-cb_chat_header"]) {{
  position: sticky !important;
  top: 0 !important;
  z-index: 5 !important;
}}
section[data-testid="stMain"] [class*="st-key-cb_chat_header"] {{
  padding-bottom: 8px;
}}

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
