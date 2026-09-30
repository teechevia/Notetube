from enum import Enum

class Task(Enum):
    CHAT = "CHAT"
    HUMAN_NOTES = "HUMAN_NOTES"
    BRIEFING = "BRIEFING"
    FLASHCARDS = "FLASHCARDS"
    QUIZ = "QUIZ"
    FAQ = "FAQ"
    PODCAST = "PODCAST"

# Minimal configuration: Phase 1 routes all tasks to the existing Gemini implementation
AI_ROUTING_CONFIG = {
    Task.CHAT: {"provider": "gemini"},
    Task.HUMAN_NOTES: {"provider": "gemini"},
    Task.BRIEFING: {"provider": "gemini"},
    Task.FLASHCARDS: {"provider": "gemini"},
    Task.QUIZ: {"provider": "gemini"},
    Task.FAQ: {"provider": "gemini"},
    Task.PODCAST: {"provider": "gemini"},
}
