
from mcp_app.registry import get_mcp
from src.logger import get_logger

logger = get_logger(__name__)

VALID_ROLES = {
    "user",
    "admin",
    "super_admin",
}


def check_mcp_permission(
    role: str,
    permission: str,
    mcp_name: str,
) -> bool:
    """Verify role and permission against registered MCP metadata."""

    if role not in VALID_ROLES:
        return False

    if not permission or not mcp_name:
        return False

    mcp = get_mcp(mcp_name)

    if not mcp:
        return False

    registered_role = mcp.get("role")
    registered_permission = mcp.get("permission")

    allowed = (
        role == registered_role
        and permission == registered_permission
    )

    if not allowed:
        logger.warning(
            "MCP permission denied: name=%s role=%s",
            mcp_name,
            role,
        )

    return allowed


def can_execute_mcp(
    role: str,
    mcp_name: str,
    permission: str,
) -> bool:
    """Return whether the role can execute the requested MCP."""

    return check_mcp_permission(
        role=role,
        permission=permission,
        mcp_name=mcp_name,
    )


def get_mcp_permission(mcp_name: str):
    """Return the registered permission, if the MCP exists."""

    mcp = get_mcp(mcp_name)
    return mcp.get("permission") if mcp else None


def get_mcp_role(mcp_name: str):
    """Return the registered role, if the MCP exists."""

    mcp = get_mcp(mcp_name)
    return mcp.get("role") if mcp else None


def is_mcp_available_for_role(role: str, mcp_name: str) -> bool:
    """Check whether an MCP is registered for this exact role."""

    if role not in VALID_ROLES:
        return False

    mcp = get_mcp(mcp_name)

    return bool(mcp and mcp.get("role") == role)