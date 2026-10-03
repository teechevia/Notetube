from abc import ABC, abstractmethod
from typing import Optional


class AIProvider(ABC):
    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        """
        Generate text using the provider.

        Args:
            prompt: User/task prompt.
            system_instruction: Optional system instruction.
            model: Optional model identifier. If not provided,
                   the provider may use its default model.
        """
        pass