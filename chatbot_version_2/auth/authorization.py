
from typing import Any

from fastapi import HTTPException, Request, status

from src.logger import get_logger
from auth.rbac import has_permission, is_valid_role

logger = get_logger(__name__)


def get_authenticated_user(request: Request) -> dict[str, Any]:
    """
    Read the authenticated user from the server-side session.

    This function expects login code to store the user under
    request.session["user"].
    """
    user = request.session.get("user")

    if not isinstance(user, dict):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    user_id = user.get("id")
    role = user.get("role", "user")

    if user_id is None or not is_valid_role(role):
        logger.warning("Rejected invalid session identity or role.")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authenticated session.",
        )

    return {
        "id": user_id,
        "role": role,
    }


def require_permission(
    user: dict[str, Any],
    permission: str,
) -> dict[str, Any]:
    """
    Verify that an authenticated user's role has the requested permission.
    """
    role = user.get("role")

    if not is_valid_role(role) or not has_permission(role, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action.",
        )

    return user


def require_patient_ownership(
    user: dict[str, Any],
    patient_id: int,
) -> int:
    """
    Ensure a patient can access only their own patient record.
    Admin access must use a separate, explicitly authorized path.
    """
    if user.get("role") != "user" or user.get("id") != patient_id:
        logger.warning("Patient ownership check denied access.")

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access another patient's information.",
        )

    return patient_id
