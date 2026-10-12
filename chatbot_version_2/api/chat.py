"""
Chat API  (prefix: /api/chat)

GET  /api/chat/me        is there a logged-in session?
POST /api/chat/message   send one message, get the assistant's reply
"""
import uuid
from collections import OrderedDict, deque

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

from auth.authorization import get_authenticated_user
from auth.rate_limit import RateLimiter
from database.queries import (
    add_chat_message,
    get_chat_history,
    get_or_create_active_session,
)
from llm.agent import chat_with_tools
from services.report_service import save_medical_file
from src.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])

# Max 20 messages per minute per user (protects LLM quota and cost).
chat_limiter = RateLimiter(max_events=20, window_seconds=60)

# ---- server-side chat memory --------------------------------------------
# The website widget does not send history, so the server remembers the
# last messages. Keyed by a random id stored in the login session, so it is
# dropped on logout. In-memory: lost on server restart; bounded in size.
MAX_REMEMBERED_MESSAGES = 10
MAX_REMEMBERED_CHATS = 1000
_CHAT_MEMORY: "OrderedDict[str, deque]" = OrderedDict()


def _get_memory(request: Request) -> deque:
    chat_id = request.session.get("chat_id")
    if not chat_id:
        chat_id = uuid.uuid4().hex
        request.session["chat_id"] = chat_id

    memory = _CHAT_MEMORY.get(chat_id)
    if memory is None:
        memory = deque(maxlen=MAX_REMEMBERED_MESSAGES)
        _CHAT_MEMORY[chat_id] = memory
        while len(_CHAT_MEMORY) > MAX_REMEMBERED_CHATS:
            _CHAT_MEMORY.popitem(last=False)
    else:
        _CHAT_MEMORY.move_to_end(chat_id)
    return memory


# ---- schemas --------------------------------------------------------------

class HistoryItem(BaseModel):
    role: str
    content: str = Field(max_length=4000)


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    # Optional: a client may send its own history instead of server memory.
    history: list[HistoryItem] = Field(default_factory=list, max_length=20)


# ---- routes ---------------------------------------------------------------

@router.get("/me")
def chat_status(request: Request):
    user = get_authenticated_user(request)
    session_id = request.session.get("chat_session_id")
    if not session_id and user.get("role") == "user":
        try:
            session_id = get_or_create_active_session(user["id"])
            request.session["chat_session_id"] = session_id
        except Exception:
            logger.exception("Failed to initialize chat session ID.")

    return {
        "authenticated": True,
        "user_id": user["id"],
        "role": user["role"],
        "session_id": session_id,
    }


@router.get("/history")
def get_user_chat_history(request: Request):
    user = get_authenticated_user(request)
    if user.get("role") != "user":
        return {"messages": []}

    try:
        session_id = request.session.get("chat_session_id")
        if not session_id:
            session_id = get_or_create_active_session(user["id"])
            request.session["chat_session_id"] = session_id

        messages = get_chat_history(session_id, limit=30)
        return {"messages": messages, "session_id": session_id}
    except Exception:
        logger.exception("Failed to retrieve chat history.")
        return {"messages": []}


@router.post("/message")
def send_chat_message(data: ChatMessageRequest, request: Request):
    user = get_authenticated_user(request)

    message = data.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    limit_key = f"{user['role']}:{user['id']}"
    if not chat_limiter.check_and_hit(limit_key):
        raise HTTPException(
            status_code=429,
            detail="You are sending messages too fast. Please wait a moment.",
            headers={"Retry-After": str(chat_limiter.retry_after(limit_key))},
        )

    try:
        memory = _get_memory(request)
        history = (
            [item.model_dump() for item in data.history]
            if data.history
            else list(memory)
        )

        answer = chat_with_tools(message=message, user=user, history=history)

        memory.append({"role": "user", "content": message})
        memory.append({"role": "assistant", "content": answer})

        # Persist into MySQL chat_sessions and chat_messages for patients
        if user.get("role") == "user":
            try:
                session_id = request.session.get("chat_session_id")
                if not session_id:
                    session_id = get_or_create_active_session(user["id"])
                    request.session["chat_session_id"] = session_id

                add_chat_message(session_id, "user", message)
                add_chat_message(session_id, "assistant", answer)
            except Exception:
                logger.exception("Failed to persist message to MySQL database.")

        return {"success": True, "reply": answer}

    except Exception as exc:
        # Full error + traceback goes to the terminal / logs/app.log.
        logger.exception(
            "Chat generation failed for authenticated user: %s",
            type(exc).__name__,
        )

        # Rate limit from the LLM provider (common on free plans).
        if type(exc).__name__ == "RateLimitError":
            raise HTTPException(
                status_code=429,
                detail=(
                    "The assistant is busy right now. "
                    "Please wait a few seconds and try again."
                ),
            ) from None

        raise HTTPException(
            status_code=503,
            detail="Chat service is temporarily unavailable.",
        ) from None


@router.post("/upload")
async def upload_chat_document(request: Request, file: UploadFile = File(...)):
    user = get_authenticated_user(request)
    if user.get("role") != "user":
        raise HTTPException(
            status_code=403,
            detail="Medical document uploads are currently available for patients.",
        )

    try:
        content = await file.read()
        session_id = request.session.get("chat_session_id")
        if not session_id:
            session_id = get_or_create_active_session(user["id"])
            request.session["chat_session_id"] = session_id

        result = save_medical_file(
            patient_id=user["id"],
            original_filename=file.filename,
            file_content=content,
            chat_session_id=session_id,
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "Upload failed."))

        # Add message note in database chat session
        sys_note = f"[Medical Report Uploaded: {file.filename}]"
        add_chat_message(session_id, "user", sys_note)
        reply_note = f"Received your medical document: **{file.filename}**. It has been securely attached to your patient profile and consultation record. How can I help you regarding this report?"
        add_chat_message(session_id, "assistant", reply_note)

        memory = _get_memory(request)
        memory.append({"role": "user", "content": sys_note})
        memory.append({"role": "assistant", "content": reply_note})

        return {
            "success": True,
            "message": result["message"],
            "filename": file.filename,
            "image_id": result.get("image_id"),
            "reply": reply_note,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Upload processing failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to process medical document.")

