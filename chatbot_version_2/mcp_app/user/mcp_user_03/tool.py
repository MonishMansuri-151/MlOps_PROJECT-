from datetime import date, time
from src.logger import get_logger
logger = get_logger(__name__)
from services.appointment_service import (
    get_available_slots,
    book_appointment,
    get_patient_appointments,
    cancel_appointment,
)


MCP_NAME = "mcp_user_03"
MCP_DESCRIPTION = "Manage patient appointment operations."
MCP_ROLE = "user"
MCP_PERMISSION = "appointment.manage"


def get_available_appointment_slots(
    doctor_id: int,
    appointment_date: date,
):
    """
    Get available appointment slots for a doctor.
    """

    if not doctor_id or doctor_id <= 0:
        return {
            "success": False,
            "message": "Invalid doctor.",
        }

    if not appointment_date:
        return {
            "success": False,
            "message": "Appointment date is required.",
        }

    slots = get_available_slots(
        doctor_id=doctor_id,
        appointment_date=appointment_date,
    )

    return {
        "success": True,
        "data": slots,
    }


def create_appointment(
    patient_id: int,
    doctor_id: int,
    department_id: int,
    appointment_date: date,
    start_time: time,
    end_time: time,
    reason: str | None = None,
):
    """
    Create an appointment for a patient.

    Authorization must be performed before this MCP is executed.
    """

    if not patient_id or patient_id <= 0:
        return {
            "success": False,
            "message": "Invalid patient.",
        }

    if not doctor_id or doctor_id <= 0:
        return {
            "success": False,
            "message": "Invalid doctor.",
        }

    if not department_id or department_id <= 0:
        return {
            "success": False,
            "message": "Invalid department.",
        }

    return book_appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        department_id=department_id,
        appointment_date=appointment_date,
        start_time=start_time,
        end_time=end_time,
        reason=reason,
    )


def get_my_appointments(patient_id: int):
    """
    Get appointments belonging to the authenticated patient.
    """

    if not patient_id or patient_id <= 0:
        return {
            "success": False,
            "message": "Invalid patient.",
        }

    appointments = get_patient_appointments(
        patient_id=patient_id,
    )

    return {
        "success": True,
        "data": appointments,
    }


def cancel_my_appointment(
    patient_id: int,
    appointment_id: int,
):
    """
    Cancel an appointment belonging to the patient.
    """

    if not patient_id or patient_id <= 0:
        return {
            "success": False,
            "message": "Invalid patient.",
        }

    if not appointment_id or appointment_id <= 0:
        return {
            "success": False,
            "message": "Invalid appointment.",
        }

    return cancel_appointment(
        patient_id=patient_id,
        appointment_id=appointment_id,
    )