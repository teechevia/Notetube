from .planner import build_research_plan
from .google_search import search_web
from .classify import classify_results
from .ranking import rank_results
from .evidence import fetch_ranked_evidence


def research_web(query: str):
    plan = build_research_plan(query)

    if not plan.needs_web:
        return {
            "query": query,
            "plan": plan,
            "results": [],
            "evidence": [],
        }

    _, results = search_web(query)

    results = classify_results(results)

    ranked = rank_results(
        results,
        preferred_source_types=plan.preferred_source_types,
    )

    ranked = ranked[:plan.max_results]

    evidence = fetch_ranked_evidence(ranked)

    return {
        "query": query,
        "plan": plan,
        "results": ranked,
        "evidence": evidence,
    }
