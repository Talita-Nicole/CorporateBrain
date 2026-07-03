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
/* Streamlit ships a fixed 60px sidebar header (``stSidebarHeader``) that also
   hosts the collapse ("<<") button, then renders app content below it in
   ``stSidebarUserContent``. That stacks the brand header under a tall empty
   strip. Collapse the header to a compact 44px row and pull the content up to
   overlap it, so the brand header (logo + name) lands on the SAME axis as the
   "<<" button — a single compact header, Claude-style.
   ``position/z-index`` keep the header (and its button) painted above the
   pulled-up content; without this the content covers the button and the
   collapse control stops responding to clicks. The 13px top padding centres the
   button on the logo's row; -52px is tuned so the logo top clears the viewport
   edge (~8px) while leaving ~14px down to the first section. */
[data-testid="stSidebarHeader"] {{
  height: 44px !important;
  min-height: 44px !important;
  padding-top: 13px !important;
  padding-bottom: 0 !important;
  position: relative !important;
  z-index: 10 !important;
}}
[data-testid="stSidebarUserContent"] {{
  margin-top: -52px !important;
  padding-top: 0 !important;
  /* The -52px pull lifts this box's top to ~-8px (44px header − 52px). To reach
     the real viewport bottom the height must span that gap too: 100vh − (−8px)
     = 100vh + 8px. The old ``100vh − 44px`` stopped ~52px short, leaving the
     empty strip below the pinned Settings bar. */
  height: calc(100vh + 8px) !important;
  display: flex !important;
  flex-direction: column !important;
  /* Without this, overflow inside the flex column (e.g. a long document/
     conversation list) is NOT contained by the inner ``cb_sidebar_scroll``
     box — it leaks past this container's own fixed height and forces a
     second, outer scrollbar on the page/body, on top of the intended single
     scroll inside cb_sidebar_scroll. Hidden here pushes all overflow handling
     down to the one scrollable child that actually wants it. */
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
[data-testid="stSidebar"] [class*="st-key-cb_session_row_"] [class*="st-key-load_session_"] button:hover:not(:disabled) {{
  background: var(--brand-dim) !important;
}}
/* The active conversation's button is rendered ``disabled`` — style that
   state as a highlighted "currently open" row instead of the default greyed-
   out disabled look, and swap the cursor back to default (not "not-allowed"),
   since disabling it here means "already open", not "unavailable". */
[data-testid="stSidebar"] [class*="st-key-cb_session_row_"] [class*="st-key-load_session_"] button:disabled {{
  background: var(--brand-dim) !important;
  color: var(--brand) !important;
  font-weight: 600 !important;
  opacity: 1 !important;
  cursor: default !important;
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
   [data-testid="stAppScrollToBottomContainer"] (class stMain) is the actual
   scrolling ancestor of the chat transcript — stMainBlockContainer itself
   does not scroll. Pinning the header there keeps "New Chat" reachable
   without scrolling back to the top of a long conversation.
   Every ancestor between this header and ``.stApp`` has a transparent
   background in Streamlit's DOM (only ``.stApp`` itself is painted with the
   real active theme color). A hardcoded ``light-dark(#ffffff, #0e1117)``
   used to paper over that, but ``light-dark()`` resolves from the BROWSER/OS
   color-scheme preference, not from the theme the user picked inside the
   app's own Light/Dark/System menu — switching the in-app theme while the OS
   stayed in the other mode left this one element painted in the stale
   color, a visible dark/light patch over an otherwise-retheme'd page.
   Fixed by making the whole ancestor chain ``background-color: inherit``
   too, so the real color painted on ``.stApp`` — whatever the user actually
   chose — propagates all the way down through ``inherit`` instead of being
   guessed from a media-query-like signal that can disagree with it. */
/* Every ancestor between the header and ``stAppViewContainer`` (the nearest
   opaque one — it, and everything above it up to ``.stApp``, is already
   painted with the real theme color) must carry ``background-color:
   inherit`` for that color to actually propagate down to the header —
   ``inherit`` only bridges ONE generation at a time, so a single
   transparent link anywhere breaks it for every descendant below. The chain
   here is: stAppViewContainer (opaque) → one unlabelled wrapper div →
   stAppScrollToBottomContainer → stMainBlockContainer → an unlabelled
   stVerticalBlock → stLayoutWrapper → the header's own stVerticalBlock.
   Missing any ONE of these (as happened while narrowing this rule down)
   silently breaks the whole chain below it. */
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > div,
[data-testid="stAppScrollToBottomContainer"],
[data-testid="stAppScrollToBottomContainer"] [data-testid="stMainBlockContainer"],
[data-testid="stAppScrollToBottomContainer"] [data-testid="stMainBlockContainer"] * {{
  background-color: inherit;
}}
/* Streamlit wraps every ``st.container(key=...)`` in an extra
   ``stLayoutWrapper`` div, and it's THAT wrapper — not the ``stVerticalBlock``
   the key actually lands on — that needs ``position: sticky``. Applying
   sticky to the inner ``st-key-cb_chat_header`` block alone computes as
   "sticky" (DevTools confirms it) but never visually pins: verified by
   injecting a bare sticky ``<div>`` as a direct child of the scroller, which
   pins correctly, versus one one level deeper (mirroring the wrapper/block
   nesting Streamlit produces here), which does not — the extra flex-layout
   level in between defeats it. Targeting the wrapper via ``:has()`` reaches
   the level that actually holds the scroll-relative containing block. */
[data-testid="stAppScrollToBottomContainer"] div:has(> [class*="st-key-cb_chat_header"]) {{
  position: sticky !important;
  top: 0 !important;
  z-index: 5 !important;
}}
[data-testid="stAppScrollToBottomContainer"] [class*="st-key-cb_chat_header"] {{
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
