import sys

from chatbot.database.queries import (
    create_chat_session,
    add_chat_message,
    get_chat_sessions,
    get_chat_messages,
    delete_chat_session,
)

from src.logger import get_logger
from src.exception import CustomException


logger = get_logger(__name__)


def create_session(patient_id: int) -> int:
    """
    Create a new chatbot conversation session.
    """
    try:
        if not patient_id:
            raise ValueError("Patient ID is required.")

        session_id = create_chat_session(patient_id)

        logger.info(
            f"Chat history session created: "
            f"patient_id={patient_id}, "
            f"session_id={session_id}"
        )

        return session_id

    except Exception as e:
        logger.error(
            f"Failed to create chat history session: {e}"
        )
        raise CustomException(e, sys)


def save_message(
    session_id: int,
    role: str,
    message: str
) -> bool:
    """
    Save one chatbot message.
    """

    try:
        if not session_id:
            raise ValueError("Session ID is required.")

        if role not in (
            "user",
            "assistant",
            "system"
        ):
            raise ValueError(
                "Invalid chat message role."
            )

        if not message or not message.strip():
            raise ValueError(
                "Chat message cannot be empty."
            )

        result = add_chat_message(
            session_id=session_id,
            role=role,
            message=message.strip()
        )

        return result

    except Exception as e:
        logger.error(
            f"Failed to save chat message: {e}"
        )
        raise CustomException(e, sys)


def get_patient_chat_sessions(
    patient_id: int
) -> list:
    """
    Return all chatbot sessions belonging
    to the authenticated patient.
    """

    try:
        if not patient_id:
            raise ValueError(
                "Patient ID is required."
            )

        sessions = get_chat_sessions(
            patient_id
        )

        return sessions

    except Exception as e:
        logger.error(
            f"Failed to fetch patient chat sessions: {e}"
        )
        raise CustomException(e, sys)


def get_session_messages(
    patient_id: int,
    session_id: int
) -> list:
    """
    Return messages only when the session
    belongs to the authenticated patient.
    """

    try:
        if not patient_id:
            raise ValueError(
                "Patient ID is required."
            )

        if not session_id:
            raise ValueError(
                "Session ID is required."
            )

        messages = get_chat_messages(
            session_id=session_id,
            patient_id=patient_id
        )

        return messages

    except Exception as e:
        logger.error(
            f"Failed to fetch session messages: {e}"
        )
        raise CustomException(e, sys)


def delete_session(
    patient_id: int,
    session_id: int
) -> bool:
    """
    Delete a chatbot conversation only if
    it belongs to the authenticated patient.
    """

    try:
        if not patient_id:
            raise ValueError(
                "Patient ID is required."
            )

        if not session_id:
            raise ValueError(
                "Session ID is required."
            )

        deleted = delete_chat_session(
            session_id=session_id,
            patient_id=patient_id
        )

        if deleted:
            logger.info(
                f"Chat conversation deleted: "
                f"patient_id={patient_id}, "
                f"session_id={session_id}"
            )
        else:
            logger.warning(
                f"Chat conversation not found or "
                f"unauthorized delete attempt: "
                f"patient_id={patient_id}, "
                f"session_id={session_id}"
            )

        return deleted

    except Exception as e:
        logger.error(
            f"Failed to delete chat session: {e}"
        )
        raise CustomException(e, sys)