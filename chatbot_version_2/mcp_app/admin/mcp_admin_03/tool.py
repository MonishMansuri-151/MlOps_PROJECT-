from services.appointment_service import get_patient_appointments
from src.logger import get_logger 
logger = get_logger(__name__)

MCP_NAME = "mcp_admin_03"
MCP_DESCRIPTION = "Retrieve appointment records for authorized clinic administration."
MCP_ROLE = "admin"
MCP_PERMISSION = "appointment.admin.read"


def get_patient_appointments_for_admin(patient_id: int):
    """
    Retrieve appointments for a specific patient.

    This function should only be called after the admin's
    identity and appointment-read permission are verified.
    """

    if not patient_id or patient_id <= 0:
        logger.warning(
            "Invalid patient ID supplied to admin appointment MCP",
            extra={
                "event": "ADMIN_MCP_INVALID_PATIENT_ID",
                "mcp_name": MCP_NAME,
            },
        )

        return {
            "success": False,
            "message": "Invalid patient ID.",
        }

    appointments = get_patient_appointments(patient_id=patient_id)

    logger.info(
        "Admin appointment lookup completed",
        extra={
            "event": "ADMIN_APPOINTMENT_LOOKUP",
            "mcp_name": MCP_NAME,
            "patient_id": patient_id,
            "result_count": len(appointments),
        },
    )

    return {
        "success": True,
        "data": appointments,
    }