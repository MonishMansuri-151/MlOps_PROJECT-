from services.report_service import (
    get_patient_medical_images,
    get_medical_image,
    get_secure_image_path,
    delete_medical_image,
)
from src.logger import get_logger
logger = get_logger(__name__)

MCP_NAME = "mcp_user_05"
MCP_DESCRIPTION = "Access the authenticated patient's medical reports and images."
MCP_ROLE = "user"
MCP_PERMISSION = "medical_report.read"


def get_my_medical_reports(patient_id: int):
    """
    Get medical report/image metadata belonging to the patient.
    """

    if not patient_id or patient_id <= 0:
        logger.warning(
            "Invalid patient ID supplied to medical report MCP",
            extra={
                "event": "MCP_MEDICAL_REPORT_INVALID_PATIENT",
                "mcp_name": MCP_NAME,
            },
        )

        return {
            "success": False,
            "message": "Invalid patient.",
        }

    reports = get_patient_medical_images(
        patient_id=patient_id,
    )

    return {
        "success": True,
        "data": reports,
    }


def get_my_medical_report(
    patient_id: int,
    image_id: int,
):
    """
    Get one medical report belonging to the authenticated patient.

    The file path is intentionally not returned to the caller.
    """

    if not patient_id or patient_id <= 0:
        return {
            "success": False,
            "message": "Invalid patient.",
        }

    if not image_id or image_id <= 0:
        return {
            "success": False,
            "message": "Invalid medical report.",
        }

    image = get_medical_image(
        patient_id=patient_id,
        image_id=image_id,
    )

    if not image:
        return {
            "success": False,
            "message": "Medical report not found.",
        }

    return {
        "success": True,
        "data": {
            "id": image["id"],
            "chat_session_id": image["chat_session_id"],
            "uploaded_at": image["uploaded_at"],
        },
    }


def get_my_medical_report_path(
    patient_id: int,
    image_id: int,
):
    """
    Get a validated internal file path for a patient's report.

    This should only be used by trusted internal application
    components that need to process the file.

    It should NOT be directly exposed to the LLM or frontend.
    """

    if not patient_id or patient_id <= 0:
        return {
            "success": False,
            "message": "Invalid patient.",
        }

    if not image_id or image_id <= 0:
        return {
            "success": False,
            "message": "Invalid medical report.",
        }

    safe_path = get_secure_image_path(
        patient_id=patient_id,
        image_id=image_id,
    )

    if not safe_path:
        return {
            "success": False,
            "message": "Medical report file is unavailable.",
        }

    return {
        "success": True,
        "path": str(safe_path),
    }


def delete_my_medical_report(
    patient_id: int,
    image_id: int,
):
    """
    Delete a medical report belonging to the authenticated patient.

    Authorization must be checked before executing this MCP.
    """

    if not patient_id or patient_id <= 0:
        return {
            "success": False,
            "message": "Invalid patient.",
        }

    if not image_id or image_id <= 0:
        return {
            "success": False,
            "message": "Invalid medical report.",
        }

    return delete_medical_image(
        patient_id=patient_id,
        image_id=image_id,
    )