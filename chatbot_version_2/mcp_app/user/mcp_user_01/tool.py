from services.patient_service import get_patient_by_id
from src.logger import get_logger 
logger = get_logger(__name__)
MCP_NAME = "mcp_user_01"
MCP_DESCRIPTION = "Retrieve basic information of the authenticated patient."
MCP_ROLE = "user"
MCP_PERMISSION = "patient.read"


def get_patient_information(patient_id: int):
    """
    Retrieve basic information of a patient.

    The service layer handles the actual database access.
    This MCP only coordinates the operation.
    """

    if not patient_id or patient_id <= 0:
        logger.warning(
            "Invalid patient ID supplied to patient MCP",
            extra={
                "event": "MCP_PATIENT_INVALID_ID",
                "mcp_name": MCP_NAME,
            },
        )

        return {
            "success": False,
            "message": "Invalid patient.",
        }

    patient = get_patient_by_id(patient_id)

    if not patient:
        return {
            "success": False,
            "message": "Patient information not found.",
        }

    return {
        "success": True,
        "data": patient,
    }