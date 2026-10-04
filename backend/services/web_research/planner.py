from .models import WebSearchResult
from .ranking import ResearchPlan


RESEARCH_KEYWORDS = {
    "research_paper": (
        "study",
        "research",
        "paper",
        "experiment",
        "evidence",
        "clinical",
        "scientific",
        "academic",
    ),
    "official": (
        "official",
        "documentation",
        "docs",
        "specification",
        "release",
        "version",
        "policy",
        "law",
        "government",
    ),
    "wikipedia": (
        "what is",
        "who is",
        "history of",
        "definition",
        "overview",
        "meaning",
    ),
}


def build_research_plan(query: str) -> ResearchPlan:
    normalized = query.lower().strip()

    preferred = []

    for source_type, keywords in RESEARCH_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            preferred.append(source_type)

    if not preferred:
        preferred = [
            "official",
            "research_paper",
            "wikipedia",
            "general_web",
        ]

    return ResearchPlan(
        query=query,
        needs_web=True,
        preferred_source_types=preferred,
        max_results=8,
    )
