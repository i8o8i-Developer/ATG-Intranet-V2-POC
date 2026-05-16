"""
Unified LLM client — supports Anthropic (claude-haiku-4-5) and OpenAI (gpt-4o-mini).
Switch via LLM_PROVIDER env var. Model names are configurable per provider.
"""

from typing import Optional
from iris.config import settings


class LLMClient:
    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or settings.llm_provider).lower()
        self._anthropic_client = None
        self._openai_client = None

    @property
    def model_name(self) -> str:
        if self.provider == "anthropic":
            return settings.anthropic_model
        return settings.openai_model

    def _get_anthropic(self):
        if self._anthropic_client is None:
            import anthropic
            self._anthropic_client = anthropic.Anthropic(
                api_key=settings.anthropic_api_key
            )
        return self._anthropic_client

    def _get_openai(self):
        if self._openai_client is None:
            from openai import OpenAI
            self._openai_client = OpenAI(api_key=settings.openai_api_key)
        return self._openai_client

    def complete(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> str:
        """
        Send a completion request. Returns raw text response.
        Temperature is kept low (0.1) for consistent structured extraction.
        """
        if self.provider == "anthropic":
            return self._complete_anthropic(system_prompt, user_message, max_tokens, temperature)
        elif self.provider == "openai":
            return self._complete_openai(system_prompt, user_message, max_tokens, temperature)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}. Use 'anthropic' or 'openai'.")

    def _complete_anthropic(
        self, system_prompt: str, user_message: str, max_tokens: int, temperature: float
    ) -> str:
        client = self._get_anthropic()
        response = client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    def _complete_openai(
        self, system_prompt: str, user_message: str, max_tokens: int, temperature: float
    ) -> str:
        client = self._get_openai()
        response = client.chat.completions.create(
            model=self.model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content

    def info(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model_name,
        }


# Singleton — shared across the app
llm_client = LLMClient()
