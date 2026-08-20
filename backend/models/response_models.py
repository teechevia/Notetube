from pydantic import BaseModel

class Definition(BaseModel):
    term: str
    meaning: str

class KnowledgeResponse(BaseModel):
    summary: str
    topics: list[str]
    definitions: list[Definition]
    keywords: list[str]
    main_points: list[str]