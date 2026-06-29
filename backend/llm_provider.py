"""LLM provider abstraction for the AI Interview Agent backend.

This module defines a provider interface and a mock implementation for now.
Future providers such as OpenAI, Gemini, or Groq can implement the same API.
"""

import logging
from abc import ABC, abstractmethod

from .config import settings

logger = logging.getLogger(__name__)

FALLBACK_QUESTION = "What is the difference between Random Forest and XGBoost?"


class BaseLLMProvider(ABC):
    """Abstract interface for all LLM providers."""

    @abstractmethod
    def generate_question(self, prompt: str) -> str:
        """Generate a single interview question."""
        raise NotImplementedError

    @abstractmethod
    def evaluate_answer(self, prompt: str) -> str:
        """Evaluate a candidate answer."""
        raise NotImplementedError

    @abstractmethod
    def summarize_session(self, prompt: str) -> str:
        """Generate a final session summary."""
        raise NotImplementedError


class MockLLMProvider(BaseLLMProvider):
    """Mock provider used during development and testing."""

    def generate_question(self, prompt: str) -> str:
        """Return a realistic mock interview question."""
        return "What is the difference between Random Forest and XGBoost?"

    def evaluate_answer(self, prompt: str) -> str:
        """Return realistic mock evaluation JSON."""
        return (
            '{"score": 7, "strengths": ["Clear structure", "Relevant examples"], '
            '"weaknesses": ["Could be more specific about trade-offs"], '
            '"feedback": "Good answer with room for deeper technical detail.", '
            '"follow_up_question": "How would you optimize this approach for large-scale data?"}'
        )

    def summarize_session(self, prompt: str) -> str:
        """Return realistic mock session summary JSON."""
        return (
            '{"overall_score": 8, "overall_strengths": ["Strong fundamentals", "Clear communication"], '
            '"overall_weaknesses": ["Needs deeper trade-off discussion"], '
            '"hiring_recommendation": "Recommend moving forward to next round."}'
        )


class GeminiProvider(BaseLLMProvider):
    """Gemini-backed provider with validation, timeout, logging, and fallback."""

    def __init__(self) -> None:
        logger.info("GeminiProvider initialized")
        logger.info("Gemini model name: %s", settings.model_name)

    def generate_question(self, prompt: str) -> str:
        return self._generate_text(prompt)
        # try:
        #     return self._generate_text(prompt)
        # except Exception:
        #     logger.warning("Using fallback interview question")
        #     return FALLBACK_QUESTION

    def evaluate_answer(self, prompt: str) -> str:
        return self._generate_text(prompt)
        # try:
        #     return self._generate_text(prompt)
        # except Exception:
        #     logger.warning("Using mock evaluation fallback")
        #     return MockLLMProvider().evaluate_answer(prompt)

    def summarize_session(self, prompt: str) -> str:
        return self._generate_text(prompt)
        # try:
        #     return self._generate_text(prompt)
        # except Exception:
        #     logger.warning("Using mock summary fallback")
        #     return MockLLMProvider().summarize_session(prompt)

    def _generate_text(self, prompt: str) -> str:
        """Internal Gemini text-generation path kept unchanged."""
        logger.info("Gemini request start for prompt=%r", prompt)
        logger.info("Gemini model name: %s", settings.model_name)

        if not settings.gemini_api_key:
            logger.warning("Missing GEMINI_API_KEY; using fallback question")
            return FALLBACK_QUESTION

        if not settings.model_name:
            logger.warning("Missing MODEL_NAME; using fallback question")
            return FALLBACK_QUESTION

        try:
            from google import genai

            client = genai.Client(api_key=settings.gemini_api_key)
            response = client.models.generate_content(
                model=settings.model_name,
                contents=prompt,
            )
            text = getattr(response, "text", None)

            if text:
                logger.info("Gemini request succeeded")
                return text.strip()

            logger.warning("Gemini returned an empty response; using fallback question")
            return FALLBACK_QUESTION
        except TimeoutError as exc:
            logger.exception("Gemini request timed out")
            raise exc

        except Exception as exc:
            logger.exception("Gemini request failed")
            raise exc


class GroqProvider(BaseLLMProvider):

    def _generate_text(self, prompt: str):

        from groq import Groq

        client = Groq(
            api_key=settings.groq_api_key
        )

        response = client.chat.completions.create(

            model=settings.groq_model,

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]

        )

        return response.choices[0].message.content

    def generate_question(self, prompt: str):
        return self._generate_text(prompt)

    def evaluate_answer(self, prompt: str):
        return self._generate_text(prompt)

    def summarize_session(self, prompt: str):
        return self._generate_text(prompt)


class RouterProvider(BaseLLMProvider):

    def generate_question(self, prompt: str) -> str:

        try:
            logger.info("Trying Gemini")

            return GeminiProvider().generate_question(
                prompt
            )

        except Exception as e:

            logger.warning(
                "Gemini failed switching to Groq: %s",
                e
            )

            try:

                logger.info("Trying Groq")

                return GroqProvider().generate_question(
                    prompt
                )

            except Exception as e:

                logger.warning(
                    "Groq failed switching to Mock: %s",
                    e
                )

                return MockLLMProvider().generate_question(
                    prompt
                )

    def evaluate_answer(self, prompt: str) -> str:

        try:
            logger.info("Trying Gemini")

            return GeminiProvider().evaluate_answer(
                prompt
            )

        except Exception as e:

            logger.warning(
                "Gemini failed switching to Groq: %s",
                e
            )

            try:

                logger.info("Trying Groq")

                return GroqProvider().evaluate_answer(
                    prompt
                )

            except Exception as e:

                logger.warning(
                    "Groq failed switching to Mock: %s",
                    e
                )

                return MockLLMProvider().evaluate_answer(
                    prompt
                )

    def summarize_session(self, prompt: str) -> str:

        try:
            logger.info("Trying Gemini")

            return GeminiProvider().summarize_session(
                prompt
            )

        except Exception as e:

            logger.warning(
                "Gemini failed switching to Groq: %s",
                e
            )

            try:

                logger.info("Trying Groq")

                return GroqProvider().summarize_session(
                    prompt
                )

            except Exception as e:

                logger.warning(
                    "Groq failed switching to Mock: %s",
                    e
                )

                return MockLLMProvider().summarize_session(
                    prompt
                )


def get_provider() -> BaseLLMProvider:

    provider_name = settings.llm_provider

    if provider_name == "gemini":
        return GeminiProvider()

    if provider_name == "groq":
        return GroqProvider()

    if provider_name == "router":
        return RouterProvider()

    return MockLLMProvider()
