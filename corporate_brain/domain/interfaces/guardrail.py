"""Contract for screening user input before it reaches the language model."""

from abc import ABC, abstractmethod


class Guardrail(ABC):
    """Screens a question for known misuse patterns before any LLM call."""

    @abstractmethod
    def screen_question(self, question: str) -> bool:
        """Return ``True`` when ``question`` should be refused without calling the LLM."""
