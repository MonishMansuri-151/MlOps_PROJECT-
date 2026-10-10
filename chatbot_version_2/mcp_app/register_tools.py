
from functools import wraps

from src.logger import get_logger
from mcp_app.server import mcp_server
from mcp_app.registry import register_mcp
from mcp_app.permissions import can_execute_mcp

from mcp_app.user.mcp_user_01.tool import get_patient_information
from mcp_app.user.mcp_user_02.tool import get_doctors
from mcp_app.user.mcp_user_03.tool import (
    get_available_appointment_slots,
    create_appointment,
    get_my_appointments,
    cancel_my_appointment,
)
from mcp_app.user.mcp_user_04.tool import (
    get_my_medical_history,
    get_my_medical_history_record,
)
from mcp_app.user.mcp_user_05.tool import (
    get_my_medical_reports,
    get_my_medical_report,
)

from mcp_app.admin.mcp_admin_01.tool import (
    get_patient_for_admin,
    search_patients,
)
from mcp_app.admin.mcp_admin_02.tool import (
    get_doctor_for_admin,
    search_doctors,
)
from mcp_app.admin.mcp_admin_03.tool import (
    get_patient_appointments_for_admin,
)

from mcp_app.system.mcp_system_01.tool import (
    check_system_database_health,
)
from mcp_app.system.mcp_system_02.tool import (
    get_system_mcp_summary,
    get_system_mcps_by_role,
)

logger = get_logger(__name__)

TOOLS = [
    # USER TOOLS
    (
        "get_patient_information",
        get_patient_information,
        "Get basic information for a patient.",
        "user",
        "patient.read",
    ),
    (
        "get_doctors",
        get_doctors,
        "Get active doctors, optionally filtered by department.",
        "user",
        "doctor.read",
    ),
    (
        "get_available_appointment_slots",
        get_available_appointment_slots,
        "Find available appointment slots.",
        "user",
        "appointment.manage",
    ),
    (
        "create_appointment",
        create_appointment,
        "Create a patient appointment.",
        "user",
        "appointment.manage",
    ),
    (
        "get_my_appointments",
        get_my_appointments,
        "Get the authenticated patient's appointments.",
        "user",
        "appointment.manage",
    ),
    (
        "cancel_my_appointment",
        cancel_my_appointment,
        "Cancel an eligible patient appointment.",
        "user",
        "appointment.manage",
    ),
    (
        "get_my_medical_history",
        get_my_medical_history,
        "Get a patient's medical history.",
        "user",
        "medical_history.read",
    ),
    (
        "get_my_medical_history_record",
        get_my_medical_history_record,
        "Get a specific medical history record.",
        "user",
        "medical_history.read",
    ),
    (
        "get_my_medical_reports",
        get_my_medical_reports,
        "List a patient's medical reports.",
        "user",
        "medical_report.read",
    ),
    (
        "get_my_medical_report",
        get_my_medical_report,
        "Get details of a specific medical report.",
        "user",
        "medical_report.read",
    ),

    # ADMIN TOOLS
    (
        "get_patient_for_admin",
        get_patient_for_admin,
        "Get patient details for authorized admin use.",
        "admin",
        "patient.admin.read",
    ),
    (
        "search_patients",
        search_patients,
        "Search patient records for authorized admin use.",
        "admin",
        "patient.admin.read",
    ),
    (
        "get_doctor_for_admin",
        get_doctor_for_admin,
        "Get doctor details for authorized admin use.",
        "admin",
        "doctor.admin.read",
    ),
    (
        "search_doctors",
        search_doctors,
        "Search doctors for authorized admin use.",
        "admin",
        "doctor.admin.read",
    ),
    (
        "get_patient_appointments_for_admin",
        get_patient_appointments_for_admin,
        "Get appointments for authorized admin review.",
        "admin",
        "appointment.admin.read",
    ),

    # SYSTEM TOOLS
    (
        "check_system_database_health",
        check_system_database_health,
        "Check database connectivity and health.",
        "super_admin",
        "system.health.read",
    ),
    (
        "get_system_mcp_summary",
        get_system_mcp_summary,
        "Get a summary of registered MCP tools.",
        "super_admin",
        "system.mcp.read",
    ),
    (
        "get_system_mcps_by_role",
        get_system_mcps_by_role,
        "List registered MCP tools for a specified role.",
        "super_admin",
        "system.mcp.read",
    ),
]


def register_all_tools():
    registered_count = 0

    for name, handler, description, role, permission in TOOLS:
        # Keep the original handler and its permission metadata.
        register_mcp(
            name=name,
            handler=handler,
            description=description,
            role=role,
            permission=permission,
        )

        def make_guarded_handler(
            tool_name,
            original_handler,
            required_role,
            required_permission,
        ):
            @wraps(original_handler)
            def guarded_handler(*args, **kwargs):
                # Direct stdio calls have no trusted application identity.
                # Fail closed; do not bypass authorization.
                logger.warning(
                    "Blocked direct MCP call without trusted identity: %s",
                    tool_name,
                )
                raise PermissionError(
                    "Authentication required. Use the authenticated "
                    "application API to execute this tool."
                )

            return guarded_handler

        guarded_handler = make_guarded_handler(
            name,
            handler,
            role,
            permission,
        )

        mcp_server.tool(
            name=name,
            description=description,
        )(guarded_handler)

        registered_count += 1
        logger.info("Registered guarded MCP tool: %s", name)

    return registered_count
