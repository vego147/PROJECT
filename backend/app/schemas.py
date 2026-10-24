from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class GenerateRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=300)
    platform: str = Field(default="Instagram", max_length=40)
    tone: str = Field(default="Professional", max_length=40)

class Source(BaseModel):
    title: str
    url: str
    published_date: str | None = None
    snippet: str
    credibility: str = "Unverified"
    extracted_content: str = ""
    extraction_status: str = "not fetched"
    http_status: int | None = None

class Verification(BaseModel):
    summary: str
    warnings: list[str] = []
    confidence: str = "Basic"

class PostResponse(BaseModel):
    article_title: str = ""
    article: str = ""
    stages: list[dict] = []
    id: int | None = None
    topic: str
    platform: str
    tone: str
    title: str
    caption: str
    hashtags: list[str]
    call_to_action: str
    image_prompt: str
    image_data: str
    sources: list[Source]
    verification: Verification
    mode: str
    created_at: datetime | None = None

class HistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    topic: str
    title: str
    caption: str
    hashtags: str
    call_to_action: str
    image_prompt: str
    image_data: str
    sources_json: str
    mode: str
    created_at: datetime
