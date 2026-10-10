from typing import Any, Callable
from src.logger import get_logger
logger = get_logger(__name__)

MCP_REGISTRY: dict[str, dict[str, Any]] = {}


def register_mcp(
    name: str,
    handler: Callable,
    description: str,
    role: str,
    permission: str,
):
    """
    Register one MCP tool.

    Parameters:
        name:
            Unique MCP tool name.

        handler:
            Function that executes the actual operation.

        description:
            Human-readable description of the tool.

        role:
            Minimum role allowed to use this MCP.

        permission:
            Fine-grained permission required to execute it.
    """

    if not name:
        raise ValueError("MCP name is required.")

    if not callable(handler):
        raise ValueError("MCP handler must be callable.")

    if not description:
        raise ValueError("MCP description is required.")

    if not role:
        raise ValueError("MCP role is required.")

    if not permission:
        raise ValueError("MCP permission is required.")

    if name in MCP_REGISTRY:
        raise ValueError(f"MCP already registered: {name}")

    MCP_REGISTRY[name] = {
        "name": name,
        "handler": handler,
        "description": description,
        "role": role,
        "permission": permission,
    }

    logger.info(
        "MCP registered successfully",
        extra={
            "event": "MCP_REGISTERED",
            "mcp_name": name,
            "role": role,
            "permission": permission,
        },
    )


def get_mcp(name: str):
    """
    Get one registered MCP by name.
    """

    if not name:
        return None

    return MCP_REGISTRY.get(name)


def get_all_mcps():
    """
    Get all registered MCP definitions.

    Handler functions are removed from the returned data so
    that callers cannot accidentally expose internal functions.
    """

    mcps = []

    for mcp in MCP_REGISTRY.values():
        mcps.append(
            {
                "name": mcp["name"],
                "description": mcp["description"],
                "role": mcp["role"],
                "permission": mcp["permission"],
            }
        )

    return mcps


def get_mcps_by_role(role: str):
    """
    Get MCPs available for a specific role.
    """

    if not role:
        return []

    mcps = []

    for mcp in MCP_REGISTRY.values():
        if mcp["role"] == role:
            mcps.append(
                {
                    "name": mcp["name"],
                    "description": mcp["description"],
                    "role": mcp["role"],
                    "permission": mcp["permission"],
                }
            )

    return mcps


def mcp_exists(name: str) -> bool:
    """
    Check whether an MCP is registered.
    """

    if not name:
        return False

    return name in MCP_REGISTRY


def remove_mcp(name: str) -> bool:
    """
    Remove an MCP from the registry.

    Returns True if removed, otherwise False.
    """

    if not name or name not in MCP_REGISTRY:
        return False

    del MCP_REGISTRY[name]

    logger.info(
        "MCP removed successfully",
        extra={
            "event": "MCP_REMOVED",
            "mcp_name": name,
        },
    )

    return True


def clear_registry():
    """
    Clear the complete MCP registry.

    Intended mainly for application reset/testing.
    """

    MCP_REGISTRY.clear()

    logger.info(
        "MCP registry cleared",
        extra={
            "event": "MCP_REGISTRY_CLEARED",
        },
    )