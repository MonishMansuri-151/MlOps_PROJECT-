
from typing import Any

from mcp_app.permissions import can_execute_mcp
from mcp_app.registry import get_mcp
from src.logger import get_logger

logger = get_logger(__name__)


def execute_mcp(
    mcp_name: str,
    authenticated_user: dict[str, Any],
    arguments: dict | None = None,
):
    """
    Execute a registered MCP using identity supplied by
    a trusted authentication layer.

    Never pass an LLM-supplied role or permission here.
    """

    if not mcp_name:
        return {
            "success": False,
            "error": "MCP name is required.",
        }

    if not isinstance(authenticated_user, dict):
        return {
            "success": False,
            "error": "Authenticated identity is required.",
        }

    user_id = authenticated_user.get("id")
    role = authenticated_user.get("role")

    if user_id is None or role not in {
        "user",
        "admin",
        "super_admin",
    }:
        return {
            "success": False,
            "error": "Invalid authenticated identity.",
        }

    if arguments is None:
        arguments = {}

    if not isinstance(arguments, dict):
        return {
            "success": False,
            "error": "MCP arguments must be an object.",
        }

    mcp = get_mcp(mcp_name)

    if not mcp:
        logger.warning(
            "Unknown MCP requested: %s",
            mcp_name,
        )
        return {
            "success": False,
            "error": "MCP not found.",
        }

    # Permission must come from trusted server-side registration.
    registered_permission = mcp.get("permission")

    if not registered_permission:
        logger.error(
            "MCP has no registered permission: %s",
            mcp_name,
        )
        return {
            "success": False,
            "error": "MCP permission is not configured.",
        }

    if not can_execute_mcp(
        role=role,
        mcp_name=mcp_name,
        permission=registered_permission,
    ):
        logger.warning(
            "MCP execution denied: name=%s role=%s",
            mcp_name,
            role,
        )
        return {
            "success": False,
            "error": "You are not authorized to use this MCP.",
        }

    handler = mcp.get("handler")

    if not callable(handler):
        logger.error("Invalid MCP handler: %s", mcp_name)
        return {
            "success": False,
            "error": "MCP handler is unavailable.",
        }

    # Do not allow the caller to override trusted identity
    # by injecting identity fields into tool arguments.
    if {"role", "authenticated_user"} & arguments.keys():
        return {
            "success": False,
            "error": "Identity fields cannot be supplied as MCP arguments.",
        }

    logger.info(
        "MCP execution started: name=%s role=%s",
        mcp_name,
        role,
    )

    try:
        result = handler(**arguments)

    except TypeError:
        logger.exception(
            "Invalid arguments for MCP: %s",
            mcp_name,
        )
        return {
            "success": False,
            "error": "Invalid MCP arguments.",
        }

    except Exception:
        logger.exception(
            "MCP execution failed: %s",
            mcp_name,
        )
        return {
            "success": False,
            "error": "MCP execution failed.",
        }

    return {
        "success": True,
        "data": result,
    }


def get_available_mcps(role: str):
    """List MCPs available to a role."""
    if role not in {"user", "admin", "super_admin"}:
        return []

    from mcp_app.registry import get_mcps_by_role

    return get_mcps_by_role(role)
