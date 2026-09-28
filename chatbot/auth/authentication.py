import bcrypt


from chatbot.database.queries import (
    get_patient_by_phone,
    get_patient_by_email,
    get_admin_by_email,
)
import sys
from src.logger import get_logger
from src.exception import CustomException
logger = get_logger(__name__)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )
    except Exception as e:
        logger.error(f"Password verification failed: {e}")
        raise CustomException(e,sys)


def authenticate_patient(identifier: str, password: str):
    try:
        patient = get_patient_by_phone(identifier)

        if patient is None:
            patient = get_patient_by_email(identifier)

        if patient is None:
            logger.warning("Patient authentication failed: patient not found")
            return None

        if not verify_password(password, patient["password_hash"]):
            logger.warning(
                f"Patient authentication failed for patient_id={patient['id']}"
            )
            return None

        logger.info(
            f"Patient authenticated successfully: patient_id={patient['id']}"
        )

        return patient

    except Exception as e:
        logger.error(f"Patient authentication error: {e}")
        raise CustomException(e,sys)
    
    
def authenticate_admin(email: str, password: str):
    try:
        admin = get_admin_by_email(email)

        if admin is None:
            logger.warning(
                "Admin authentication failed: admin not found"
            )
            return None

        if not verify_password(
            password,
            admin["password"]
        ):
            logger.warning(
                f"Admin authentication failed for admin_id={admin['id']}"
            )
            return None

        if admin["role"] not in {"admin", "super_admin"}:
            logger.warning(
                f"Invalid admin role for admin_id={admin['id']}"
            )
            return None

        logger.info(
            f"Admin authenticated successfully: "
            f"admin_id={admin['id']}, role={admin['role']}"
        )

        return admin

    except Exception as e:
        logger.error(
            f"Admin authentication error: {e}"
        )
        raise CustomException(e, sys)