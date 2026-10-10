from database.connection import get_db
from src.logger import get_logger
logger = get_logger()

MCP_NAME = "mcp_admin_01"
MCP_DESCRIPTION = "Allow authorized admins to view patient information."
MCP_ROLE = "admin"
MCP_PERMISSION = "patient.admin.read"


def get_patient_for_admin(patient_id: int):
    """
    Get patient information for an authorized admin.

    Sensitive authentication fields such as password_hash
    are never selected.
    """

    if not patient_id or patient_id <= 0:
        logger.warning(
            "Invalid patient ID supplied to admin MCP",
            extra={
                "event": "ADMIN_MCP_INVALID_PATIENT_ID",
                "mcp_name": MCP_NAME,
            },
        )

        return {
            "success": False,
            "message": "Invalid patient.",
        }

    with get_db() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    phone,
                    email,
                    dob,
                    gender,
                    address,
                    role,
                    created_at,
                    updated_at
                FROM patients
                WHERE id = %s
                LIMIT 1
                """,
                (patient_id,),
            )

            patient = cursor.fetchone()

    if not patient:
        return {
            "success": False,
            "message": "Patient not found.",
        }

    return {
        "success": True,
        "data": patient,
    }


def search_patients(search: str | None = None):
    """
    Search patients by name, phone or email.

    If no search value is provided, active patient records
    are returned with a reasonable limit.
    """

    with get_db() as connection:
        with connection.cursor() as cursor:

            if search:
                search_value = f"%{search.strip()}%"

                cursor.execute(
                    """
                    SELECT
                        id,
                        name,
                        phone,
                        email,
                        dob,
                        gender,
                        role,
                        created_at
                    FROM patients
                    WHERE name LIKE %s
                       OR phone LIKE %s
                       OR email LIKE %s
                    ORDER BY name
                    LIMIT 100
                    """,
                    (
                        search_value,
                        search_value,
                        search_value,
                    ),
                )

            else:
                cursor.execute(
                    """
                    SELECT
                        id,
                        name,
                        phone,
                        email,
                        dob,
                        gender,
                        role,
                        created_at
                    FROM patients
                    ORDER BY name
                    LIMIT 100
                    """
                )

            patients = cursor.fetchall()

    logger.info(
        "Admin patient search completed",
        extra={
            "event": "ADMIN_PATIENT_SEARCH",
            "mcp_name": MCP_NAME,
            "result_count": len(patients),
        },
    )

    return {
        "success": True,
        "data": patients,
    }