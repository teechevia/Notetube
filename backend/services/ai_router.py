from services.ai_config import Task, AI_ROUTING_CONFIG
from services.ai import ask_ai

def generate_text(task: Task, prompt: str, system_instruction: str = None) -> str:
    """
    Routes text generation requests to the appropriate AI provider based on task.
    Currently, all tasks route to the existing Gemini implementation.
    """
    config = AI_ROUTING_CONFIG.get(task)
    if not config:
        raise ValueError(f"No routing configuration found for task: {task}")
    
    provider = config.get("provider")
    
    if provider == "gemini":
        if system_instruction:
            return ask_ai(prompt, system_instruction)
        return ask_ai(prompt)
    else:
        raise NotImplementedError(f"Provider '{provider}' is not implemented yet.")
