
import bcrypt

from database.connection import get_db
from src.logger import get_logger

logger = get_logger(__name__)


# Bcrypt hash of a random string. Used so a login for an unknown user costs
# the same time as a wrong password (prevents user enumeration by timing).
_DUMMY_HASH = bcrypt.hashpw(b"not-a-real-password", bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its stored bcrypt hash."""
    if not plain_password or not hashed_password:
        return False

    try:
        password_bytes = plain_password.encode("utf-8")
        hash_bytes = hashed_password.encode("utf-8")

        return bcrypt.checkpw(password_bytes, hash_bytes)

    except (ValueError, TypeError, UnicodeError):
        logger.warning("Password hash verification failed.")
        return False


def authenticate_patient(identifier: str, password: str):
    """
    Authenticate a patient using phone number or email.

    Returns safe user information on success, otherwise None.
    """
    if not identifier or not password:
        return None

    try:
        with get_db() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, name, phone, email, password_hash, role
                    FROM patients
                    WHERE phone = %s OR email = %s
                    LIMIT 1
                    """,
                    (identifier, identifier),
                )
                patient = cursor.fetchone()

        if not patient:
            verify_password(password, _DUMMY_HASH)
            return None

        if not verify_password(password, patient["password_hash"]):
            return None

        return {
            "id": patient["id"],
            "name": patient["name"],
            "phone": patient["phone"],
            "email": patient["email"],
            # A patient account is ALWAYS role "user". Never trust the
            # patients.role column here, otherwise a changed DB value
            # (or a bug) would silently make a patient an admin.
            "role": "user",
        }

    except Exception:
        logger.exception("Patient authentication failed.")
        raise


def authenticate_admin(email: str, password: str):
    """
    Authenticate an admin or super_admin account.
    """
    if not email or not password:
        return None

    try:
        with get_db() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, name, email, password, role
                    FROM admin_users
                    WHERE email = %s
                    LIMIT 1
                    """,
                    (email,),
                )
                admin = cursor.fetchone()

        if not admin:
            verify_password(password, _DUMMY_HASH)
            return None

        if not verify_password(password, admin["password"]):
            return None

        role = admin["role"]

        if role not in {"admin", "super_admin"}:
            return None

        return {
            "id": admin["id"],
            "name": admin["name"],
            "email": admin["email"],
            "role": role,
        }

    except Exception:
        logger.exception("Admin authentication failed.")
        raise
