"""Lightweight, pattern-based input screening for obvious prompt-injection attempts.

Implements the ``Guardrail`` port with regex heuristics. Kept swappable: a
future moderation-API-backed implementation only needs to implement the same
port and be wired in at composition time.
"""

import logging
import re

from domain.interfaces.guardrail import Guardrail

logger = logging.getLogger(__name__)

# Each pattern targets a distinct injection intent: overriding prior
# instructions, requesting the system prompt, or reassigning the assistant's
# role/identity. Deliberately narrow and English/Portuguese-only to avoid
# false positives on legitimate questions about company policy wording.
_INJECTION_PATTERNS = [
    re.compile(r"\bignore\s+(all\s+)?(previous|prior|above)\s+instructions?\b", re.IGNORECASE),
    re.compile(r"\bignor[ea]\s+(todas\s+)?as?\s+instru[cç][oõ]es?\s+anteriores\b", re.IGNORECASE),
    re.compile(r"\b(reveal|show|print|repeat)(\s+me)?\s+(your|the)\s+system\s+prompt\b", re.IGNORECASE),
    re.compile(r"\b(mostre|revele|repita)\s+(o\s+)?(seu\s+)?prompt\s+(do\s+)?sistema\b", re.IGNORECASE),
    re.compile(r"\byou\s+are\s+now\s+(a|an)\b", re.IGNORECASE),
    re.compile(r"\bact\s+as\b.{0,40}\b(dan|jailbreak)\b", re.IGNORECASE),
    re.compile(r"\bdisregard\s+(your|the)\s+(guidelines|rules|instructions)\b", re.IGNORECASE),
]


class PatternGuardrail(Guardrail):
    """Flags obvious prompt-injection patterns without calling the LLM."""

    def screen_question(self, question: str) -> bool:
        for pattern in _INJECTION_PATTERNS:
            if pattern.search(question):
                logger.warning(
                    "Guardrail triggered on pattern %r for question: %r",
                    pattern.pattern,
                    question,
                )
                return True
        return False
