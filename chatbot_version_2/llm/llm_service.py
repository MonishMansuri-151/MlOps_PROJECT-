
import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

from src.logger import get_logger

# load_dotenv()
# logger = get_logger(__name__)
MCP_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(MCP_ENV_FILE, override=True)

logger = get_logger(__name__)

_client = None


def get_llm_client():
    """Create the Groq client when first required."""
    global _client

    if _client is not None:
        return _client

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    _client = Groq(api_key=api_key)
    return _client


def generate_response(
    message: str,
    system_prompt: str | None = None,
) -> str:
    """Generate a healthcare assistant response using Groq."""

    if not isinstance(message, str) or not message.strip():
        raise ValueError("Message cannot be empty.")

    if len(message) > 8000:
        raise ValueError("Message is too long.")

    prompt = system_prompt or (
        "You are Sanjivni, a helpful healthcare information assistant. "
        "Give clear, cautious general health information. "
        "Do not claim to diagnose diseases or replace a doctor. "
        "For severe or potentially life-threatening symptoms, "
        "advise urgent medical care. "
        "Never invent patient records, appointments, or test results."
    )

    try:
        client = get_llm_client()

        response = client.chat.completions.create(
            model=os.getenv(
                "GROQ_MODEL",
                "openai/gpt-oss-20b",
            ),
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": message.strip()},
            ],
            temperature=0.3,
            max_tokens=600,
        )

        answer = response.choices[0].message.content

        if not answer:
            return "Sorry, I couldn't generate a response. Please try again."

        return answer.strip()

    except Exception:
        logger.exception("Groq response generation failed.")
        raise RuntimeError(
            "The AI service is temporarily unavailable."
        ) from None