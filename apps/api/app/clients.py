from openai import AsyncOpenAI

from app import ssl_bundle
from app.config import settings, resolve_openai_api_key

_openai_client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        ssl_bundle.apply_corporate_ssl_bundle()
        _openai_client = AsyncOpenAI(api_key=resolve_openai_api_key())
    return _openai_client


def reset_clients() -> None:
    global _openai_client
    _openai_client = None
