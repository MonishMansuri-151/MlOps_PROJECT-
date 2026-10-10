from services.doctor_service import (
    get_active_doctors,
    get_doctors_by_department,
)
from src.logger import get_logger
logger = get_logger(__name__)

MCP_NAME = "mcp_user_02"
MCP_DESCRIPTION = "Find active doctors and filter doctors by department."
MCP_ROLE = "user"
MCP_PERMISSION = "doctor.read"


def get_doctors(department_id: int | None = None):
    """
    Get active doctors.

    If department_id is provided, only doctors from that
    department are returned.
    """

    if department_id is not None:
        if department_id <= 0:
            logger.warning(
                "Invalid department ID supplied to doctor MCP",
                extra={
                    "event": "MCP_DOCTOR_INVALID_DEPARTMENT",
                    "mcp_name": MCP_NAME,
                    "department_id": department_id,
                },
            )

            return {
                "success": False,
                "message": "Invalid department.",
            }

        doctors = get_doctors_by_department(department_id)

    else:
        doctors = get_active_doctors()

    return {
        "success": True,
        "data": doctors,
    }