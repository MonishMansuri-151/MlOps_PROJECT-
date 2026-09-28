from typing import Optional
import sys
from fastapi import Request

from src.logger import get_logger
from src.exception import CustomException
logger = get_logger(__name__)


SESSION_USER_KEY = "user"


def set_user_session(request: Request, user_data: dict) -> None:
    try:
        request.session[SESSION_USER_KEY] = {
            "id": user_data["id"],
            "name": user_data["name"],
            "phone": user_data["phone"],
            "email": user_data.get("email"),
        }

        logger.info(
            f"User session created: user_id={user_data['id']}"
        )

    except Exception as e:
        logger.error(f"Failed to create user session: {e}")
        raise CustomException(e,sys)


def get_current_user(request: Request) -> Optional[dict]:
    try:
        return request.session.get(SESSION_USER_KEY)

    except Exception as e:
        logger.error(f"Failed to get current user session: {e}")
        raise CustomException(e,sys)


def clear_user_session(request: Request) -> None:
    try:
        request.session.clear()

        logger.info("User session cleared")

    except Exception as e:
        logger.error(f"Failed to clear user session: {e}")
        raise CustomException(e,sys)