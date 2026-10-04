from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WebSearchResult:
    title: str
    url: str
    snippet: str = ""
    domain: str = ""
    source_type: str = "web"
    score: float = 0.0


@dataclass
class WebEvidence:
    title: str
    url: str
    domain: str
    content: str
    snippet: str = ""
    source_type: str = "web"
    authority: str = "general"
    metadata: dict = field(default_factory=dict)
