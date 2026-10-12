"""Groq LLM client (shared by the chat agent)."""
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from src.logger import get_logger

# override=False: real environment variables win over the .env file.
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

logger = get_logger(__name__)

_client = None


def get_model_name() -> str:
    return os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


def get_llm_client() -> Groq:
    """Create the Groq client the first time it is needed."""
    global _client

    if _client is not None:
        return _client

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    _client = Groq(
        api_key=api_key,
        timeout=float(os.getenv("GROQ_TIMEOUT", "30")),
        max_retries=1,
    )
    return _client
