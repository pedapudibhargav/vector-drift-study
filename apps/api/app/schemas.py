from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    top_k: int = Field(default=3, ge=1, le=20)
    use_metadata_filter: bool = False
    metadata_filter: dict[str, str] | None = None
    corpus_size: int | None = Field(default=None, description="Active corpus milestone N for scaling metrics")


class HealthStatus(BaseModel):
    status: str
    openai: str
    vector_db: str
    postgres: str
    version: str
