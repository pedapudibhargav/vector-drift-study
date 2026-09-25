from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_here = Path(__file__).resolve()
_env_candidates: list[Path] = [Path("/app/.env")]
for _depth in (3, 2, 1):
    try:
        _env_candidates.append(_here.parents[_depth] / ".env")
    except IndexError:
        break
_env_file = next((p for p in _env_candidates if p.exists()), _env_candidates[-1] if _env_candidates else Path(".env"))
PROJECT_ROOT = _env_file.parent


def resolve_openai_api_key() -> str:
    """Prefer a real key from mounted .env when container env still has placeholders."""
    key = settings.openai_api_key.strip()
    if key and not key.startswith("sk-your"):
        return key
    for path in _env_candidates:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.startswith("OPENAI_API_KEY="):
                continue
            candidate = line.split("=", 1)[1].strip().strip('"').strip("'")
            if candidate and not candidate.startswith("sk-your"):
                return candidate
    return key


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        **({"env_file": str(_env_file)} if _env_file.exists() else {}),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    pinecone_api_key: str = ""
    pinecone_index_name: str = "vector-drift-research"
    pinecone_environment: str = "us-east-1-aws"
    # Serverless index data-plane host (preferred over list_indexes lookup)
    pinecone_host_url: str = Field(default="", validation_alias="PINECONE_HOST_URL")
    pinecone_host: str = Field(default="", validation_alias="PINECONE_HOST")

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    database_url: str = "postgresql+asyncpg://postgres:postgres@vector-drift-postgres:5432/vector_drift_db"
    crawl_requests_per_second: float = Field(default=4.0, validation_alias="CRAWL_REQUESTS_PER_SECOND")

    @property
    def pinecone_data_host(self) -> str:
        return (self.pinecone_host_url or self.pinecone_host).strip().rstrip("/")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
