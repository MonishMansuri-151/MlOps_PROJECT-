
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from auth.authorization import get_authenticated_user
from llm.llm_service import generate_response
from llm.prompts import HEALTHCARE_SYSTEM_PROMPT
from src.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


@router.get("/me")
def chat_status(request: Request):
    """Check whether the user has an authenticated session."""
    user = get_authenticated_user(request)

    return {
        "authenticated": True,
        "user_id": user["id"],
        "role": user["role"],
    }


@router.post("/message")
def send_chat_message(
    data: ChatMessageRequest,
    request: Request,
):
    """Send a message to the healthcare LLM."""
    user = get_authenticated_user(request)

    message = data.message.strip()
    if not message:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    try:
        answer = generate_response(
            message=message,
            system_prompt=HEALTHCARE_SYSTEM_PROMPT,
        )

        return {
            "success": True,
            "reply": answer,
        }

    except RuntimeError:
        logger.exception(
            "Chat generation failed for authenticated user."
        )
        raise HTTPException(
            status_code=503,
            detail="Chat service is temporarily unavailable.",
        ) from None
