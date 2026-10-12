from database.connection import get_db
from src.logger import get_logger

logger = get_logger(__name__)


def check_database_connection():
    """
    Check whether the application can successfully
    communicate with the MySQL database.
    """
    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 AS status")
            result = cursor.fetchone()
    return result


def create_chat_session(patient_id: int) -> int:
    """
    Create a new chat session in the database for a patient.
    """
    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO chat_sessions (patient_id) VALUES (%s)",
                (patient_id,)
            )
            session_id = cursor.lastrowid
    logger.info("Chat session created", extra={"event": "CHAT_SESSION_CREATED", "patient_id": patient_id, "session_id": session_id})
    return session_id


def get_or_create_active_session(patient_id: int) -> int:
    """
    Retrieve the most recent active chat session for a patient, or create a new one.
    """
    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id FROM chat_sessions
                WHERE patient_id = %s AND ended_at IS NULL
                ORDER BY started_at DESC, id DESC
                LIMIT 1
                """,
                (patient_id,)
            )
            row = cursor.fetchone()
            if row and row.get("id"):
                return row["id"]

    return create_chat_session(patient_id)


def add_chat_message(session_id: int, role: str, message: str) -> bool:
    """
    Save a chat message to MySQL chat_messages table.
    """
    if role not in ("user", "assistant", "system"):
        role = "user"

    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO chat_messages (session_id, role, message)
                VALUES (%s, %s, %s)
                """,
                (session_id, role, message)
            )
    return True


def get_chat_history(session_id: int, limit: int = 20) -> list:
    """
    Retrieve recent messages for a given chat session, in chronological order.
    """
    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT role, message AS content, created_at
                FROM chat_messages
                WHERE session_id = %s
                ORDER BY id ASC
                LIMIT %s
                """,
                (session_id, limit)
            )
            return cursor.fetchall()