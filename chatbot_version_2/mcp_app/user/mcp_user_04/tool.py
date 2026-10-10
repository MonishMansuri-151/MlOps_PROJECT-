from services.report_service import (
    get_patient_medical_history,
    get_medical_history_by_id,
)
from src.logger import get_logger
logger = get_logger(__name__)

MCP_NAME = "mcp_user_04"
MCP_DESCRIPTION = "Access the authenticated patient's medical history."
MCP_ROLE = "user"
MCP_PERMISSION = "medical_history.read"


def get_my_medical_history(patient_id: int):
    """
    Get medical history of the authenticated patient.

    The patient_id must come from the authenticated user context.
    It should not be trusted from an arbitrary LLM-generated value.
    """

    if not patient_id or patient_id <= 0:
        logger.warning(
            "Invalid patient ID supplied to medical history MCP",
            extra={
                "event": "MCP_MEDICAL_HISTORY_INVALID_PATIENT",
                "mcp_name": MCP_NAME,
            },
        )

        return {
            "success": False,
            "message": "Invalid patient.",
        }

    history = get_patient_medical_history(
        patient_id=patient_id,
    )

    return {
        "success": True,
        "data": history,
    }


def get_my_medical_history_record(
    patient_id: int,
    history_id: int,
):
    """
    Get one medical history record belonging to the authenticated patient.
    """

    if not patient_id or patient_id <= 0:
        return {
            "success": False,
            "message": "Invalid patient.",
        }

    if not history_id or history_id <= 0:
        return {
            "success": False,
            "message": "Invalid medical history record.",
        }

    history = get_medical_history_by_id(
        patient_id=patient_id,
        history_id=history_id,
    )

    if not history:
        return {
            "success": False,
            "message": "Medical history record not found.",
        }

    return {
        "success": True,
        "data": history,
    }