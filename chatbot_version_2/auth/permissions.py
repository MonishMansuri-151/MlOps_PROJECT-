
from enum import Enum


class Permission(str, Enum):
    # Patient permissions
    PATIENT_READ = "patient.read"
    PATIENT_ADMIN_READ = "patient.admin.read"

    # Doctor permissions
    DOCTOR_READ = "doctor.read"
    DOCTOR_ADMIN_READ = "doctor.admin.read"

    # Appointment permissions
    APPOINTMENT_MANAGE = "appointment.manage"
    APPOINTMENT_ADMIN_READ = "appointment.admin.read"

    # Medical record permissions
    MEDICAL_HISTORY_READ = "medical_history.read"
    MEDICAL_REPORT_READ = "medical_report.read"

    # System permissions
    SYSTEM_HEALTH_READ = "system.health.read"
    SYSTEM_MCP_READ = "system.mcp.read"
