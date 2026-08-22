from pydantic import BaseModel

class VideoRequest(BaseModel):
    url: str

class TranscriptRequest(BaseModel):
    transcript: str

class TextRequest(BaseModel):
    text: str