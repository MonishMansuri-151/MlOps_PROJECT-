
from mcp_app.registry import (
    get_all_mcps,
    get_mcps_by_role,
)
from src.logger import get_logger 
logger = get_logger(__name__)

MCP_NAME = "mcp_system_02"
MCP_DESCRIPTION = "Monitor registered MCP tools and their role assignments."
MCP_ROLE = "super_admin"
MCP_PERMISSION = "system.mcp.read"


def get_system_mcp_summary():
    """
    Return a summary of MCPs registered in the registry.
    """

    try:
        mcps = get_all_mcps()

        role_counts = {}

        for mcp in mcps:
            role = mcp.get("role", "unknown")
            role_counts[role] = role_counts.get(role, 0) + 1

        logger.info(
            "System MCP summary retrieved",
            extra={
                "event": "SYSTEM_MCP_SUMMARY",
                "mcp_name": MCP_NAME,
                "total_mcps": len(mcps),
            },
        )

        return {
            "success": True,
            "data": {
                "total_mcps": len(mcps),
                "role_counts": role_counts,
                "mcps": mcps,
            },
        }

    except Exception:
        logger.exception(
            "Failed to retrieve system MCP summary",
            extra={
                "event": "SYSTEM_MCP_SUMMARY_FAILED",
                "mcp_name": MCP_NAME,
            },
        )

        return {
            "success": False,
            "message": "Unable to retrieve MCP summary.",
        }


def get_system_mcps_by_role(role: str):
    """
    Return registered MCPs assigned to a specified role.
    """

    if not role or not role.strip():
        return {
            "success": False,
            "message": "A valid role is required.",
        }

    allowed_roles = {
        "user",
        "admin",
        "super_admin",
    }

    normalized_role = role.strip().lower()

    if normalized_role not in allowed_roles:
        return {
            "success": False,
            "message": "Invalid role.",
        }

    mcps = get_mcps_by_role(normalized_role)

    return {
        "success": True,
        "data": {
            "role": normalized_role,
            "total_mcps": len(mcps),
            "mcps": mcps,
        },
    }