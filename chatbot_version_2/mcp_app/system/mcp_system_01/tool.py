from database.queries import check_database_connection
from src.logger import get_logger
logger = get_logger(__name__)

MCP_NAME = "mcp_system_01"
MCP_DESCRIPTION = "Check application database connectivity."
MCP_ROLE = "super_admin"
MCP_PERMISSION = "system.health.read"


def check_system_database_health():
    """
    Check whether the application's database is reachable.

    Intended for authorized system monitoring.
    """

    try:
        result = check_database_connection()

        if result and result.get("status") == 1:
            logger.info(
                "System database health check succeeded",
                extra={
                    "event": "SYSTEM_DATABASE_HEALTH_OK",
                    "mcp_name": MCP_NAME,
                },
            )

            return {
                "success": True,
                "data": {
                    "database": "connected",
                    "status": "healthy",
                },
            }

        logger.warning(
            "System database health check returned an unexpected result",
            extra={
                "event": "SYSTEM_DATABASE_HEALTH_UNEXPECTED",
                "mcp_name": MCP_NAME,
            },
        )

        return {
            "success": False,
            "message": "Database health check failed.",
        }

    except Exception:
        logger.exception(
            "System database health check failed",
            extra={
                "event": "SYSTEM_DATABASE_HEALTH_FAILED",
                "mcp_name": MCP_NAME,
            },
        )

        return {
            "success": False,
            "message": "Database is unavailable.",
        }