from services.ai import ask_ai
from services.providers.base import AIProvider


class GeminiProvider(AIProvider):
    def generate_text(
        self,
        prompt: str,
        system_instruction: str = None,
    ) -> str:
        return ask_ai(prompt, system_instruction)
