
from src.logger import get_logger

logger = get_logger(__name__)


# Roles available in Sanjivni
VALID_ROLES = {
    "user",
    "admin",
    "super_admin",
}


# Permissions assigned to each role
ROLE_PERMISSIONS = {
    "user": {
        "patient.read",
        "doctor.read",
        "appointment.manage",
        "medical_history.read",
        "medical_report.read",
    },
    "admin": {
        "patient.admin.read",
        "doctor.admin.read",
        "appointment.admin.read",
    },
    "super_admin": {
        "system.health.read",
        "system.mcp.read",
    },
}


def is_valid_role(role: str) -> bool:
    """Check whether the supplied role is recognized."""
    return role in VALID_ROLES


def has_permission(role: str, permission: str) -> bool:
    """Check whether a role has a particular permission."""
    if not is_valid_role(role):
        logger.warning("RBAC rejected an unknown role.")
        return False

    allowed = permission in ROLE_PERMISSIONS.get(role, set())

    if not allowed:
        logger.warning(
            "Permission denied for role=%s, permission=%s",
            role,
            permission,
        )

    return allowed


def get_role_permissions(role: str) -> set[str]:
    """Return a copy of the permissions assigned to a valid role."""
    if not is_valid_role(role):
        return set()

    return set(ROLE_PERMISSIONS[role])