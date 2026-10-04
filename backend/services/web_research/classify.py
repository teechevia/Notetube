from urllib.parse import urlparse

from .models import WebSearchResult


WIKIPEDIA_DOMAINS = {
    "wikipedia.org",
}

RESEARCH_DOMAINS = {
    "arxiv.org",
    "pubmed.ncbi.nlm.nih.gov",
    "doi.org",
    "nature.com",
    "science.org",
    "sciencedirect.com",
    "springer.com",
    "link.springer.com",
    "ieee.org",
    "acm.org",
}

OFFICIAL_DOMAIN_SUFFIXES = (
    ".gov",
    ".gov.in",
    ".edu",
    ".edu.in",
)


def _normalize_domain(domain: str) -> str:
    return domain.lower().strip().removeprefix("www.")


def _domain_from_url(url: str) -> str:
    try:
        return _normalize_domain(urlparse(url).netloc)
    except Exception:
        return ""


def _domain_from_title(title: str) -> str:
    value = title.lower().strip()

    if value.startswith("www."):
        value = value[4:]

    for suffix in (".com", ".org", ".net", ".gov", ".edu"):
        if value.endswith(suffix):
            return value

    return ""


def classify_source(result: WebSearchResult) -> str:
    domain = _domain_from_url(result.url)

    # Google grounding URLs use a redirect domain.
    if domain == "vertexaisearch.cloud.google.com":
        domain = _domain_from_title(result.title)

    # Wikipedia includes language subdomains such as
    # en.wikipedia.org, hi.wikipedia.org, etc.
    if (
        domain in WIKIPEDIA_DOMAINS
        or domain.endswith(".wikipedia.org")
    ):
        return "wikipedia"

    # Research domains may also use subdomains.
    if (
        domain in RESEARCH_DOMAINS
        or any(domain.endswith("." + item) for item in RESEARCH_DOMAINS)
    ):
        return "research_paper"

    if domain.endswith(OFFICIAL_DOMAIN_SUFFIXES):
        return "official"

    if domain in {
        "python.org",
        "docs.python.org",
        "developer.mozilla.org",
        "github.com",
        "docs.github.com",
        "openai.com",
        "developers.google.com",
        "cloud.google.com",
    }:
        return "official"

    return "general_web"


def classify_results(
    results: list[WebSearchResult],
) -> list[WebSearchResult]:
    classified = []

    for result in results:
        result.source_type = classify_source(result)
        classified.append(result)

    return classified
