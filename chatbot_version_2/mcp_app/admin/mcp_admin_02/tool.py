from services.doctor_service import (
    get_doctor_by_id,
    get_active_doctors,
    get_doctors_by_department,
)
from src.logger import get_logger
logger = get_logger(__name__)

MCP_NAME = "mcp_admin_02"
MCP_DESCRIPTION = "Allow authorized admins to view and filter doctor information."
MCP_ROLE = "admin"
MCP_PERMISSION = "doctor.admin.read"


def get_doctor_for_admin(doctor_id: int):
    """
    Retrieve a doctor's information for an authorized admin.
    """

    if not doctor_id or doctor_id <= 0:
        logger.warning(
            "Invalid doctor ID supplied to admin MCP",
            extra={
                "event": "ADMIN_MCP_INVALID_DOCTOR_ID",
                "mcp_name": MCP_NAME,
            },
        )

        return {
            "success": False,
            "message": "Invalid doctor ID.",
        }

    doctor = get_doctor_by_id(doctor_id)

    if not doctor:
        return {
            "success": False,
            "message": "Doctor not found.",
        }

    return {
        "success": True,
        "data": doctor,
    }


def search_doctors(department_id: int | None = None):
    """
    Retrieve doctors, optionally filtered by department.

    When a department ID is supplied, only active doctors
    from that department are returned.
    """

    if department_id is not None:
        if department_id <= 0:
            logger.warning(
                "Invalid department ID supplied to admin MCP",
                extra={
                    "event": "ADMIN_MCP_INVALID_DEPARTMENT_ID",
                    "mcp_name": MCP_NAME,
                },
            )

            return {
                "success": False,
                "message": "Invalid department ID.",
            }

        doctors = get_doctors_by_department(department_id)

    else:
        doctors = get_active_doctors()

    logger.info(
        "Admin doctor search completed",
        extra={
            "event": "ADMIN_DOCTOR_SEARCH",
            "mcp_name": MCP_NAME,
            "result_count": len(doctors),
        },
    )

    return {
        "success": True,
        "data": doctors,
    }