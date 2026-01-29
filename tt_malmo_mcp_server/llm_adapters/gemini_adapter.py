"""
Gemini Adapter - Google AI API integration.

Supports Gemini 2.5 Flash Lite (free tier), Gemini 2.5 Pro, and other Gemini models.
"""

from typing import Optional
import google.generativeai as genai
from .base_adapter import BaseLLMAdapter


class GeminiAdapter(BaseLLMAdapter):
    """
    Adapter for Google's Gemini models.

    Uses the official Google Generative AI Python SDK.
    """

    def __init__(self, api_key: str,
                 model: str = "models/gemini-2.5-flash-lite",
                 max_tokens: int = 1024):
        """
        Initialize Gemini adapter.

        Args:
            api_key: Google AI API key
            model: Gemini model identifier (default: models/gemini-2.5-flash-lite)
            max_tokens: Maximum tokens to generate
        """
        super().__init__(api_key, model, max_tokens)

        # Configure Gemini
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model_name=model)

        # Generation config
        self.generation_config = {
            "max_output_tokens": max_tokens,
            "temperature": 0.7,
            "top_p": 0.95,
        }

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text using Gemini.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt (prepended to user prompt)

        Returns:
            Generated text
        """
        try:
            # Gemini doesn't have separate system prompt,
            # so we prepend it to the user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            response = self.client.generate_content(
                full_prompt,
                generation_config=self.generation_config
            )

            return response.text

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                print(f"Gemini rate limit reached. Consider using multiple providers.")
            else:
                print(f"Error calling Gemini API: {e}")
            return f"[ERROR: Rate limited or API error]"

    async def generate_streaming(self, prompt: str, system_prompt: Optional[str] = None):
        """
        Generate text with streaming using Gemini.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt (prepended to user prompt)

        Yields:
            Text chunks as they are generated
        """
        try:
            # Gemini doesn't have separate system prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            response = self.client.generate_content(
                full_prompt,
                generation_config=self.generation_config,
                stream=True
            )

            for chunk in response:
                if hasattr(chunk, 'text'):
                    yield chunk.text

        except Exception as e:
            print(f"Error in Gemini streaming: {e}")
            yield f"[ERROR: {str(e)}]"

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using Gemini's tokenizer.

        Args:
            text: Text to count tokens for

        Returns:
            Token count
        """
        try:
            response = self.client.count_tokens(text)
            return response.total_tokens
        except Exception as e:
            print(f"Error counting tokens: {e}")
            # Rough estimate: 4 chars per token
            return len(text) // 4
