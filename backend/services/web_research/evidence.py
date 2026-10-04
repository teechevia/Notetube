from .fetch import fetch_webpage
from .models import WebEvidence


MAX_EVIDENCE_CHARS = 12000


def fetch_evidence(result):
    try:
        page = fetch_webpage(result.url)

        content = page.get("content", "").strip()

        if not content:
            return None

        return WebEvidence(
            title=page.get("title") or result.title,
            url=page.get("url") or result.url,
            domain=page.get("domain") or result.domain,
            content=content[:MAX_EVIDENCE_CHARS],
            snippet=result.snippet,
            source_type=result.source_type,
            authority=result.source_type,
            metadata={
                "search_score": result.score,
            },
        )

    except Exception:
        return None


def fetch_ranked_evidence(ranked_results):
    evidence = []

    for ranked in ranked_results:
        item = fetch_evidence(ranked.result)

        if item is not None:
            evidence.append(item)

    return evidence
