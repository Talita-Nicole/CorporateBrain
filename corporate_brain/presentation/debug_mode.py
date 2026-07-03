"""Developer-only debug mode, gated by an environment variable (not a user setting).

Token usage always renders inline under each answer (see ``chat.py``). The
detailed retrieval panel (chunks, distances, top-k, chunk size/overlap,
model names) is reserved for local development and only appears when
``DEBUG_MODE=true`` is set — there is no UI toggle for it.
"""

import os


def is_debug_mode_enabled() -> bool:
    return os.getenv("DEBUG_MODE", "false").strip().lower() in ("1", "true", "yes")
