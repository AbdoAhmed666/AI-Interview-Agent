"""Interview-related backend module.

This file contains the question-generation logic for the interview flow.
"""

from .llm_provider import BaseLLMProvider, get_provider
from .prompts import build_interview_question_prompt


provider: BaseLLMProvider = get_provider()


def generate_question(role: str) -> str:
    """Return a mocked interview question for the selected role."""
    prompt = build_interview_question_prompt(role)
    return provider.generate_question(prompt)
