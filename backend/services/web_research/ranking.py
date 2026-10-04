from dataclasses import dataclass, field

from .models import WebSearchResult


@dataclass
class ResearchPlan:
    query: str
    needs_web: bool = True
    preferred_source_types: list[str] = field(default_factory=list)
    max_results: int = 8


@dataclass
class RankedWebResult:
    result: WebSearchResult
    score: float
    reason: str = ""


SOURCE_TYPE_PRIORITY = {
    "official": 1.00,
    "research_paper": 0.95,
    "wikipedia": 0.80,
    "general_web": 0.50,
}


def rank_results(
    results: list[WebSearchResult],
    preferred_source_types: list[str] | None = None,
) -> list[RankedWebResult]:
    preferred_source_types = preferred_source_types or []

    ranked = []

    for result in results:
        base_score = SOURCE_TYPE_PRIORITY.get(
            result.source_type,
            0.40,
        )

        if result.source_type in preferred_source_types:
            base_score += 0.20

        ranked.append(
            RankedWebResult(
                result=result,
                score=base_score,
                reason=f"source_type={result.source_type}",
            )
        )

    ranked.sort(
        key=lambda item: item.score,
        reverse=True,
    )

    return ranked
